import logging
import torch
from pathlib import Path
from typing import Dict, Any, Optional
import tempfile
import os
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import librosa
import numpy as np

logger = logging.getLogger(__name__)

class HebrewTranscriptionService:
    """Hebrew Speech-to-Text service using ivrit-ai/whisper-large-v3"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = "ivrit-ai/whisper-large-v3"
        self.initialized = False
        
    async def initialize(self):
        """Initialize the Whisper model and processor"""
        try:
            logger.info(f"Initializing Hebrew Whisper model: {self.model_name}")
            logger.info(f"Using device: {self.device}")
            
            # Load processor and model
            self.processor = WhisperProcessor.from_pretrained(self.model_name)
            self.model = WhisperForConditionalGeneration.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            if self.device == "cpu":
                self.model = self.model.to(self.device)
            
            self.initialized = True
            logger.info("Hebrew Whisper model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Hebrew Whisper model: {e}")
            raise
    
    def _load_audio(self, audio_path: str, target_sr: int = 16000) -> np.ndarray:
        """Load and preprocess audio file"""
        try:
            # Load audio with librosa
            audio, sr = librosa.load(audio_path, sr=target_sr)
            
            # Ensure audio is mono
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            return audio
            
        except Exception as e:
            logger.error(f"Failed to load audio file {audio_path}: {e}")
            raise
    
    async def transcribe_audio(
        self, 
        audio_path: str,
        language: str = "he",
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """Transcribe audio file to text"""
        if not self.initialized:
            raise RuntimeError("Transcription service not initialized")
            
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Load and preprocess audio
            audio = self._load_audio(audio_path)
            
            # Process audio with Whisper
            inputs = self.processor(
                audio, 
                sampling_rate=16000, 
                return_tensors="pt"
            ).input_features
            
            # Move to device
            inputs = inputs.to(self.device)
            
            # Generate transcription
            with torch.no_grad():
                predicted_ids = self.model.generate(
                    inputs,
                    language=language,
                    task=task,
                    do_sample=False
                )
            
            # Decode transcription
            transcription = self.processor.batch_decode(
                predicted_ids, 
                skip_special_tokens=True
            )[0]
            
            logger.info(f"Transcription completed: {len(transcription)} characters")
            
            return {
                "success": True,
                "text": transcription,
                "language": language,
                "task": task,
                "model": self.model_name
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": "",
                "language": language,
                "task": task,
                "model": self.model_name
            }
    
    async def transcribe_audio_file(
        self,
        audio_file_path: str,
        output_format: str = "text"
    ) -> Dict[str, Any]:
        """Transcribe audio file with optional output formatting"""
        result = await self.transcribe_audio(audio_file_path)
        
        if result["success"] and output_format == "json":
            # Add metadata for JSON output
            result["metadata"] = {
                "file_path": audio_file_path,
                "file_size": os.path.getsize(audio_file_path) if os.path.exists(audio_file_path) else 0,
                "duration": self._get_audio_duration(audio_file_path)
            }
        
        return result
    
    def _get_audio_duration(self, audio_path: str) -> Optional[float]:
        """Get audio duration in seconds"""
        try:
            duration = librosa.get_duration(path=audio_path)
            return duration
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            return None
    
    async def close(self):
        """Clean up resources"""
        if self.model:
            del self.model
        if self.processor:
            del self.processor
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

# Global instance
transcription_service = HebrewTranscriptionService() 