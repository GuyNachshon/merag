#!/bin/bash

echo "Installing Hebrew Transcription Service dependencies..."

# Install system dependencies for audio processing
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo apt-get update
    sudo apt-get install -y ffmpeg libsndfile1
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew install ffmpeg libsndfile
else
    echo "Please install ffmpeg and libsndfile manually for your system"
fi

# Install Python dependencies
pip install transformers torch librosa soundfile numpy

echo "Transcription service dependencies installed successfully!"
echo ""
echo "The Hebrew Whisper model (ivrit-ai/whisper-large-v3) will be downloaded"
echo "automatically when the service starts for the first time."
echo ""
echo "Model size: ~1.54B parameters"
echo "Supported audio formats: WAV, MP3, OGG, FLAC, AAC, WEBM, M4A"
echo ""
echo "To start the service, run: python main.py" 