FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-dev \
    python3-pip \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install basic Python packages first
RUN pip3 install --no-cache-dir packaging>=21.0 transformers>=4.40.0 torch>=2.0.0 accelerate>=0.20.0

# Try to install flash-attn
RUN pip3 install --no-cache-dir flash-attn --no-build-isolation

# Test if it works
RUN python3 -c "import flash_attn; print('flash_attn imported successfully')" 