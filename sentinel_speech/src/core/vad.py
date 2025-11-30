import onnxruntime
import numpy as np
from src.core.config import settings

class VADEngine:
    def __init__(self):
        print("Loading VAD Model (ONNX)...")
        # Download the ONNX model manually or via script and place in /models
        # For this snippet, we assume the .onnx file exists. 
        # You can fetch 'silero_vad.onnx' from their repo.
        self.session = onnxruntime.InferenceSession("models/silero_vad.onnx")

    def has_speech(self, audio_chunk: np.ndarray) -> bool:
        # ONNX requires specific input shape: [batch, sequence]
        if len(audio_chunk.shape) == 1:
            input_tensor = audio_chunk[np.newaxis, :]
        else:
            input_tensor = audio_chunk

        # Context inputs (h, c) required for Silero ONNX
        # Initialize zeros for stateless check
        batch_size = 1
        h = np.zeros((2, batch_size, 64), dtype=np.float32)
        c = np.zeros((2, batch_size, 64), dtype=np.float32)
        
        ort_inputs = {
            "input": input_tensor, 
            "h": h, 
            "c": c,
            "sr": np.array([16000], dtype=np.int64)
        }
        
        outs = self.session.run(None, ort_inputs)
        speech_prob = outs[0][0][0] # Output shape dependent on model version
        
        return speech_prob > settings.VAD_THRESHOLD