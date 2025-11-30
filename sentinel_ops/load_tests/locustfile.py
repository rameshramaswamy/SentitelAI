import time
import json
import uuid
from locust import User, task, between, events

class WebSocketUser(User):
    wait_time = between(1, 3)

    def on_start(self):
        """Simulate connection setup"""
        self.session_id = str(uuid.uuid4())
        # In real test, use websocket-client to connect to Gateway URL
        # For simplicity, we just print here, but you'd implement the socket handshake
        print(f"User {self.session_id} connected.")

    @task
    def stream_audio(self):
        """Simulate streaming audio for 30 seconds"""
        start_time = time.time()
        
        # Send chunks for 10 seconds
        while time.time() - start_time < 10:
            # Simulate 64ms audio chunk payload
            payload = b'\x00' * 2048 
            
            # Send to Gateway (Placeholder logic)
            # self.client.send(payload) 
            
            # Sleep 64ms to simulate real-time
            time.sleep(0.064)
            
    def on_stop(self):
        print(f"User {self.session_id} disconnected.")