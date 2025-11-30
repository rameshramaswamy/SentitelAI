#!/bin/bash

# Create a temporary Dockerfile context
cat <<EOF > Dockerfile.triton
FROM nvcr.io/nvidia/tritonserver:23.10-py3

# Install dependencies for our Python Backend
RUN pip install --no-cache-dir \
    faster-whisper \
    numpy \
    torch \
    torchaudio

# (Optional) Pre-download model to bake it into image
# RUN python3 -c "from faster_whisper import download_model; download_model('base')"

CMD ["tritonserver", "--model-repository=/models"]
EOF

echo "Building Sentinel Triton Image..."
docker build -t sentinel-triton-whisper:latest -f Dockerfile.triton .

# Cleanup
rm Dockerfile.triton
echo "Build Complete. Image: sentinel-triton-whisper:latest"