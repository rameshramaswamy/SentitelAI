import numpy as np
import tritonclient.http as httpclient
import time

def test_inference():
    client = httpclient.InferenceServerClient(url="localhost:8000")
    
    # Create dummy audio (1 sec silence)
    audio = np.zeros(16000, dtype=np.float32)
    
    # Prepare Input
    inputs = [
        httpclient.InferInput("AUDIO_DATA", audio.shape, "FP32")
    ]
    inputs[0].set_data_from_numpy(audio)
    
    # Prepare Output
    outputs = [
        httpclient.InferRequestedOutput("TRANSCRIPT")
    ]
    
    print("Sending Request to Triton...")
    start = time.time()
    results = client.infer(model_name="whisper", inputs=inputs, outputs=outputs)
    end = time.time()
    
    response = results.as_numpy("TRANSCRIPT")[0].decode('utf-8')
    print(f"Response: '{response}'")
    print(f"Latency: {(end-start)*1000:.2f}ms")

if __name__ == "__main__":
    test_inference()