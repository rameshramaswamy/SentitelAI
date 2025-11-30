import asyncio
import json
import nats
import uuid

async def trigger_test():
    # 1. Connect
    nc = await nats.connect("nats://localhost:4222")
    
    # 2. Use a session_id that actually exists in your DB 
    # (From Phase 3 testing, or create a dummy one)
    # If you followed Phase 3, PersistenceWorker created a dummy call.
    # Check your logs or DB for a valid session_id, or we rely on the 
    # worker handling "Call not found" gracefully.
    
    # For this test, we'll assume we need to trigger a session known to the system.
    # Replace this with a real ID from your 'calls' table if you want full success.
    target_session_id = "session_1.0.0" 

    payload = {
        "session_id": target_session_id,
        "reason": "user_disconnect",
        "timestamp": 1698412345
    }

    print(f"Triggering Pipeline for {target_session_id}...")
    await nc.publish("call.ended", json.dumps(payload).encode())
    
    await nc.flush()
    await nc.close()
    print("Event sent.")

if __name__ == "__main__":
    asyncio.run(trigger_test())