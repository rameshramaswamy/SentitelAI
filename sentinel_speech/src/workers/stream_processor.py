# Main Event Loop (Audio -> Text -> NLP -> Event)# sentinel_speech/src/workers/stream_processor.py
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoRespondersError

from src.core.config import settings
from src.core.audio_buffer import AudioBuffer
from src.core.vad import VADEngine
from src.core.transcriber import Transcriber
from src.core.nlp_router import NLPRouter
from src.adapters.state import StateManager
from sentinel_shared.schemas.events import OverlayTriggerPayload, EventType, OverlayContent

logger = logging.getLogger("worker.speech")

class StreamProcessor:
    def __init__(self):
        # 1. Initialize Engines (Heavy Loading)
        self.vad = VADEngine()
        self.transcriber = Transcriber()
        self.nlp = NLPRouter()
        self.state_db = StateManager()
        
        # 2. Session State: Dict[session_id, AudioBuffer]
        self.sessions: Dict[str, AudioBuffer] = {}
        
        # 3. Thread Pool for blocking GPU/CPU tasks
        self.executor = ThreadPoolExecutor(max_workers=4) 
        
        self.nc = None

    async def start(self):
        """Connects to NATS and starts the subscriber loop."""
        self.nc = await nats.connect(settings.NATS_URL if hasattr(settings, 'NATS_URL') else "nats://localhost:4222")
        logger.info("Connected to NATS.")

        # Subscribe to all audio streams
        # Queue Group "speech_workers" ensures load balancing if we scale replicas
        await self.nc.subscribe("audio.raw.>", queue="speech_workers", cb=self.message_handler)
        
        # Keep alive
        while True:
            await asyncio.sleep(1)

    async def message_handler(self, msg):
        subject = msg.subject
        session_id = subject.split(".")[-1]
        data = msg.data

        if session_id not in self.sessions:
            self.sessions[session_id] = AudioBuffer()
        
        buffer = self.sessions[session_id]
        
        # OPTIMIZATION: Pre-Filter using VAD on the raw chunk (approx 30-60ms)
        # We need to quickly convert just this chunk to float for VAD
        # Note: We do this in the main loop because VAD is very lightweight (0.5ms)
        # compared to the overhead of thread switching.
        chunk_float = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Check if this specific chunk has speech
        is_speech = self.vad.has_speech(chunk_float)
        
        if is_speech:
            buffer.add_bytes(data) # Only add if speech exists
        else:
            # Optional: Add a counter here to detect "End of Sentence" logic
            pass

        # Check if we have enough "Valid Speech" to transcribe
        if buffer.is_ready(min_seconds=settings.MIN_AUDIO_DURATION):
            audio_chunk = buffer.get_audio().copy()
            buffer.clear()
            asyncio.create_task(self.process_audio_chunk(session_id, audio_chunk))

    async def process_audio_chunk(self, session_id: str, audio_data):
        loop = asyncio.get_running_loop()
        previous_text = self.sessions[session_id].last_transcript_segment

         # Step B: Transcribe (Heavy GPU operation)
        # Transcribe with context
        text = await loop.run_in_executor(
            self.executor, 
            lambda: self.transcriber.model.transcribe(
                audio_data, 
                initial_prompt=previous_text, # <--- The Fix
                beam_size=1
            )
        )

        if not text:
            return

        logger.info(f"[{session_id}] Transcript: {text}")

        # Step C: Persist to Redis (Async)
        await self.state_db.append_transcript(session_id, text)

        # Step D: NLP Routing (Find Intelligence)
        trigger = self.nlp.process(text)
        
        if trigger:
            logger.info(f"[{session_id}] Trigger Match: {trigger['title']}")
            
            # Step E: Construct Payload using Shared Schema
            payload = OverlayTriggerPayload(
                content=OverlayContent(
                    title=trigger["title"],
                    message=trigger["message"],
                    color_hex=trigger["color_hex"]
                )
            )
            
            # Step F: Publish to UI Command Topic
            # Subject: ui.commands.{session_id} -> Gateway listens to this
            await self.nc.publish(
                f"ui.commands.{session_id}", 
                payload.model_dump_json().encode()
            )

    async def shutdown(self):
        logger.info("Shutting down worker...")
        if self.nc:
            await self.nc.close()
        await self.state_db.close()
        self.executor.shutdown()