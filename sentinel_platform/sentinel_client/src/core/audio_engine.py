# sentinel_client/src/core/audio_engine.py
import sounddevice as sd
import queue
import numpy as np
from sentinel_shared.utils.logger import setup_logger
import numpy as np

logger = setup_logger("client.audio")

class AudioEngine:
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.stream = None
        self.is_running = False
        self.silence_threshold = 200

    def _callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Audio status: {status}")
        
        # OPTIMIZATION: Calculate Volume (RMS) quickly using NumPy
        # Convert bytes back to numpy array for calculation (Zero-Copy view)
        audio_data = np.frombuffer(indata, dtype=np.int16)
        
        # Calculate amplitude
        volume = np.sqrt(np.mean(audio_data**2))
        
        # Only queue if volume exceeds threshold
        if volume > self.silence_threshold:
            self.audio_queue.put(bytes(indata))
        else:
            # Optional: Log silence or send heartbeat counter
            pass

    def start(self):
        logger.info("Starting Audio Stream...")
        self.stream = sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=1024,
            device=None, # Uses default mic
            channels=self.channels,
            dtype='int16',
            callback=self._callback
        )
        self.stream.start()
        self.is_running = True

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
        self.is_running = False

    def get_chunk(self):
        """Non-blocking retrieval."""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None