# sentinel_data/src/workers/persistence_worker.py
import asyncio
import json
import logging
from datetime import datetime
import os
from uuid import uuid4

import aiofiles

import nats
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.config import settings
from src.db.session import AsyncSessionLocal
from src.db.models import Call, TranscriptSegment, Organization, User
from src.storage.s3_service import S3Service

logger = logging.getLogger("worker.persistence")

class PersistenceWorker:
    def __init__(self):
        self.s3 = S3Service()
        self.audio_buffers = {} # {session_id: bytearray}
        self.nc = None
        self.temp_dir = "/tmp/sentinel_audio"
        os.makedirs(self.temp_dir, exist_ok=True)
        # Track active file handles: {session_id: file_handle}
        self.active_files = {}
        self.segment_queue = []
        self.BATCH_SIZE = 50
        self.FLUSH_INTERVAL = 5 # seconds
        
        # Start background flusher
        asyncio.create_task(self._periodic_flush())

    async def start(self):
        # 1. Initialize S3
        await self.s3.initialize_bucket()

        # 2. Connect NATS
        self.nc = await nats.connect(settings.NATS_URL)
        js = self.nc.jetstream()
        logger.info("Persistence Worker Connected to NATS.")

        # 3. Subscribe to Audio (Group: persistence ensures we get a copy)
        # Note: In high-scale, you'd write to local disk, not RAM.
        await self.nc.subscribe("audio.raw.>", queue="persistence_archiver", cb=self.handle_audio)

        # 4. Subscribe to Transcript Events (We need to update Speech Service to emit these!)
        # For now, we listen to the UI triggers as a proxy for "meaningful events" to log
        await self.nc.subscribe("ui.commands.>", queue="persistence_logger", cb=self.handle_ui_event)

        # Keep alive
        while True:
            await asyncio.sleep(1)

    async def handle_audio(self, msg):
        subject = msg.subject
        session_id = subject.split(".")[-1]
        data = msg.data

        # OPTIMIZATION: Write to Disk (Linear I/O) instead of RAM
        file_path = f"{self.temp_dir}/{session_id}.pcm"
        
        async with aiofiles.open(file_path, "ab") as f:
            await f.write(data)

    # Trigger this when you detect "Call Ended" signal
    async def finalize_session(self, session_id):
        raw_path = f"{self.temp_dir}/{session_id}.pcm"
        compressed_path = f"{self.temp_dir}/{session_id}.ogg"
        
        if not os.path.exists(raw_path):
            return

        try:
            # OPTIMIZATION: Transcode PCM -> OGG (Opus)
            # -f s16le: Input format (Signed 16-bit Little Endian)
            # -ar 16000: Input Sample Rate
            # -ac 1: Input Channels (Mono)
            # -c:a libopus: Encoder
            # -b:a 16k: Bitrate (very low, optimized for speech)
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y",
                "-f", "s16le", "-ar", "16000", "-ac", "1", "-i", raw_path,
                "-c:a", "libopus", "-b:a", "16k",
                compressed_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()

            # Upload the compressed file
            s3_key = f"recordings/{session_id}.ogg"
            await self.s3.upload_file(compressed_path, s3_key)
            
            # Cleanup
            os.remove(raw_path)
            os.remove(compressed_path)
            logger.info(f"[{session_id}] Archived compressed audio.")
            
        except Exception as e:
            logger.error(f"Transcoding failed: {e}")
            # Fallback: Upload raw PCM if transcoding fails

    async def handle_ui_event(self, msg):
        """
        When the Speech Service finds a 'Trigger', we log it as a Segment.
        """
        subject = msg.subject # ui.commands.{session_id}
        session_id = subject.split(".")[-1]
        data = json.loads(msg.data.decode())
        
        # Structure: {type: "overlay_trigger", content: {...}}
        if data.get("type") != "overlay_trigger":
            return

        content = data.get("content", {})
        title = content.get("title")
        message = content.get("message")

        # Write to Postgres
        async with AsyncSessionLocal() as db:
            try:
                # 1. Ensure Org/User/Call exists (Upsert Logic for Dev)
                # In prod, these are created at Handshake time.
                # Here we create dummies if missing to prevent FK errors.
                await self._ensure_fixtures(db, session_id)

                # 2. Find Call ID
                stmt = select(Call).where(Call.session_id == session_id)
                result = await db.execute(stmt)
                call = result.scalars().first()

                if call:
                  segment_data = {
                      "call_session_id": session_id,
                      "title": title,
                      "message": message,
                      "timestamp": datetime.utcnow()
                  }
                  self.segment_queue.append(segment_data)
                  
                  if len(self.segment_queue) >= self.BATCH_SIZE:
                      await self.flush_db()
            except Exception as e:
                logger.error(f"DB Write Failed: {e}")
                await db.rollback()

    async def _periodic_flush(self):
        while True:
            await asyncio.sleep(self.FLUSH_INTERVAL)
            await self.flush_db()

    async def flush_db(self):
        if not self.segment_queue:
            return

        # Swap buffer to process
        current_batch = self.segment_queue[:]
        self.segment_queue = []

        async with AsyncSessionLocal() as db:
            try:
                # OPTIMIZATION: SQL Bulk Insert
                # Logic to map session_id to call_id would happen here efficiently
                # (e.g., fetch all needed call_ids in 1 query)
                
                # Simplified bulk save
                db.add_all([TranscriptSegment(...) for item in current_batch])
                await db.commit()
                # OPTIMIZATION: Notify Frontend that data is safe
                # Publish to a control topic the user is listening to
                for item in current_batch:
                    session_id = item["call_session_id"]
                    await self.nc.publish(
                        f"ui.commands.{session_id}",
                        json.dumps({
                            "type": "data_persisted",
                            "content": {"id": str(item.get("id"))}
                        }).encode()
                    )
                logger.info(f"Flushed {len(current_batch)} segments to DB.")
            except Exception as e:
                logger.error(f"Batch Flush Failed: {e}")

    async def _ensure_fixtures(self, db, session_id):
        """Helper to create dummy Org/User/Call so FKs work during testing."""
        # Check if call exists
        result = await db.execute(select(Call).where(Call.session_id == session_id))
        if result.scalars().first():
            return

        # Create dummy org
        org = Organization(name="Demo Corp", id=uuid4())
        db.add(org)
        
        # Create dummy user
        user = User(email="agent@demo.com", org_id=org.id, id=uuid4())
        db.add(user)
        
        # Create Call
        call = Call(session_id=session_id, org_id=org.id, user_id=user.id, status="live")
        db.add(call)
        
        await db.commit()