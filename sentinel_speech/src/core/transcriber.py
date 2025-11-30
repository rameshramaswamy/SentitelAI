import numpy as np
import tritonclient.grpc as grpcclient
from src.core.config import settings
import logging

logger = logging.getLogger("speech.transcriber")

class Transcriber:
    def __init__(self):
        # Configuration for Triton
        # In K8s, this URL will be the Service DNS: "sentinel-triton:8001"
        self.triton_url = settings.TRITON_URL if hasattr(settings, 'TRITON_URL') else "localhost:8001"
        
        logger.info(f"Connecting to Triton Inference Server at {self.triton_url}...")
        self.client = grpcclient.InferenceServerClient(url=self.triton_url)
        
        # Check server status
        if not self.client.is_server_live():
            logger.warning("Triton Server is NOT live.")

    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Sends audio to Triton via gRPC.
        """
        if len(audio_data) == 0:
            return ""

        try:
            # Prepare Input
            # Triton expects shape [batch_size, samples] or [samples] depending on config
            # Our config expects 1D array for simplicity, Triton handles batching
            inputs = [
                grpcclient.InferInput("AUDIO_DATA", audio_data.shape, "FP32")
            ]
            inputs[0].set_data_from_numpy(audio_data)

            # Prepare Output
            outputs = [
                grpcclient.InferRequestedOutput("TRANSCRIPT")
            ]

            # Inference Call
            result = self.client.infer(
                model_name="whisper",
                inputs=inputs,
                outputs=outputs
            )

            # Parse Output
            # Result comes back as bytes array
            transcript_bytes = result.as_numpy("TRANSCRIPT")[0]
            return transcript_bytes.decode("utf-8")

        except Exception as e:
            logger.error(f"Triton Inference Failed: {e}")
            return ""