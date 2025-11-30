import json
import triton_python_backend_utils as pb_utils
import numpy as np
from faster_whisper import WhisperModel
import logging

class TritonPythonModel:
    def initialize(self, args):
        """
        Called when the model is loaded.
        """
        self.model_config = json.loads(args['model_config'])
        
        # Get parameters from config.pbtxt
        params = self.model_config.get('parameters', {})
        model_size = params.get('model_size', {}).get('string_value', 'base')
        device = params.get('device', {}).get('string_value', 'cpu')
        
        # Determine compute type based on device
        compute_type = "float16" if device == "cuda" else "int8"

        logging.info(f"Loading Faster-Whisper ({model_size}) on {device}...")
        
        # Load Model
        self.model = WhisperModel(
            model_size, 
            device=device, 
            compute_type=compute_type
        )
        logging.info("Model Loaded Successfully.")

    def execute(self, requests):
        """
        Receives a list of requests (a batch).
        Returns a list of responses.
        """
        responses = []

        # Iterate over the batch
        for request in requests:
            # 1. Get Input Tensor
            input_tensor = pb_utils.get_input_tensor_by_name(request, "AUDIO_DATA")
            
            # Convert to numpy (Float32)
            # Input shape is [length], but batching might make it [1, length] inside the request object
            audio_data = input_tensor.as_numpy()
            
            # Flatten if necessary
            if len(audio_data.shape) > 1:
                audio_data = audio_data.flatten()

            # 2. Inference
            # Note: faster-whisper is optimized for single-stream processing.
            # Running a loop here inside 'execute' is sequential within this batch.
            # However, because we used 'instance_group count: 2', we have parallelism at the process level.
            try:
                segments, info = self.model.transcribe(
                    audio_data,
                    beam_size=1,
                    temperature=0.0,
                    condition_on_previous_text=False
                )
                
                text = " ".join([segment.text for segment in segments]).strip()
            except Exception as e:
                logging.error(f"Inference failed: {e}")
                text = ""

            # 3. Create Output Tensor
            # String output must be numpy object array
            output_np = np.array([text.encode('utf-8')], dtype=object)
            
            output_tensor = pb_utils.Tensor("TRANSCRIPT", output_np)
            
            # 4. Append Response
            responses.append(pb_utils.InferenceResponse(output_tensors=[output_tensor]))

        return responses

    def finalize(self):
        """Cleanup"""
        print('Cleaning up Whisper Model...')