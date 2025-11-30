import numpy as np

class AudioBuffer:
    def __init__(self, sample_rate=16000, max_duration=30):
        self.sample_rate = sample_rate
        self.capacity = sample_rate * max_duration
        # OPTIMIZATION: Pre-allocate memory once. No dynamic resizing.
        self.buffer = np.zeros(self.capacity, dtype=np.float32)
        self.write_ptr = 0
        self.count = 0

    def add_bytes(self, chunk: bytes):
        # Zero-copy conversion where possible
        float32_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
        length = len(float32_data)

        # Ring buffer logic (simplified for Phase 2: Just reset if full)
        if self.write_ptr + length > self.capacity:
            # In a real ring buffer, we'd wrap around. 
            # For speech chunks, shifting is safer to keep context.
            # Shift buffer left by length
            self.buffer[:-length] = self.buffer[length:]
            self.write_ptr -= length
        
        self.buffer[self.write_ptr : self.write_ptr + length] = float32_data
        self.write_ptr += length

    def get_audio(self) -> np.ndarray:
        # Return a view, not a copy
        return self.buffer[:self.write_ptr]
    
    def clear(self):
        # Soft reset (instant)
        self.write_ptr = 0