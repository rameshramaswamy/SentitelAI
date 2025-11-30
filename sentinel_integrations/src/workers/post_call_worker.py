# sentinel_integrations/src/workers/post_call_worker.py
import asyncio
import json
import logging
import nats
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from src.config import settings
from src.db.session import AsyncSessionLocal
from src.db.models import Call, TranscriptSegment, User
from src.llm.engine import LLMEngine
from src.crm import get_crm_adapter

logger = logging.getLogger("worker.post_call")

class PostCallWorker:
    def __init__(self):
        self.nc = None
        self.llm = LLMEngine()
        self.crm = get_crm_adapter()

    async def start(self):
        # 1. Connect to Infrastructure
        await self.crm.connect()
        self.nc = await nats.connect(settings.NATS_URL if hasattr(settings, 'NATS_URL') else "nats://localhost:4222")
        logger.info("Post-Call Worker Connected to NATS.")

        # 2. Subscribe
        # Queue group 'integrations_pipeline' ensures only one worker processes each call
        await self.nc.subscribe("call.ended", queue="integrations_pipeline", cb=self.handle_call_ended)

        # Keep alive
        while True:
            await asyncio.sleep(1)

    async def handle_call_ended(self, msg):
        try:
            data = json.loads(msg.data.decode())
            session_id = data.get("session_id")
            
            if not session_id:
                logger.error("Received call.ended without session_id")
                return

            logger.info(f"[{session_id}] Processing Post-Call Pipeline...")
            await self.process_pipeline(session_id)

        except Exception as e:
            logger.error(f"Error handling message: {e}")

    async def process_pipeline(self, session_id: str):
        async with AsyncSessionLocal() as db:
            # 1. Fetch Call Context (User, Transcript)
            # We assume the Call record was created by sentinel_data during the live session
            stmt = (
                select(Call)
                .options(selectinload(Call.user)) # Eager load User for email
                .where(Call.session_id == session_id)
            )
            result = await db.execute(stmt)
            call = result.scalars().first()

            if not call:
                logger.warning(f"[{session_id}] Call record not found in DB. Skipping.")
                return

            if call.status == "processed":
                logger.info(f"[{session_id}] Already processed. Skipping.")
                return

            # 2. Reconstruct Transcript
            # Fetch all segments ordered by time
            seg_stmt = (
                select(TranscriptSegment)
                .where(TranscriptSegment.call_id == call.id)
                .order_by(TranscriptSegment.start_offset)
            )
            seg_result = await db.execute(seg_stmt)
            segments = seg_result.scalars().all()
            
            if not segments:
                logger.warning(f"[{session_id}] No transcript segments found.")
                return

            full_transcript = "\n".join([f"{s.speaker}: {s.text}" for s in segments])
            logger.info(f"[{session_id}] Reconstructed transcript ({len(full_transcript)} chars).")

            # 3. LLM Analysis
            logger.info(f"[{session_id}] Generating Summary...")
            analysis = await self.llm.generate_summary(full_transcript)
            
            if "error" in analysis:
                logger.error(f"[{session_id}] LLM Error: {analysis['error']}")
                return

            # 4. CRM Sync
            customer_email = call.customer_phone or "unknown@client.com" # Placeholder if not captured
            user_email = call.user.email if call.user else "agent@demo.com"
            
            logger.info(f"[{session_id}] Syncing to CRM...")
            crm_success = await self.crm.log_call_activity(
                user_email=user_email,
                customer_email=customer_email,
                summary_data=analysis
            )

            # 5. Finalize State
            if crm_success:
                call.status = "processed"
                # Optionally save the summary to the DB here if you added a column for it
                # call.ai_summary = json.dumps(analysis) 
                call.sentiment_score = 1.0 if analysis.get("sentiment") == "Positive" else 0.5
                await db.commit()
                logger.info(f"[{session_id}] Pipeline Complete. Status: Processed.")
            else:
                logger.warning(f"[{session_id}] CRM Sync failed, marked as 'review_needed'.")
                call.status = "crm_failed"
                await db.commit()