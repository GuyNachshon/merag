#!/usr/bin/env python3
"""
Simple Audio Transcription Test
Shows the full transcription of an audio file
"""

import asyncio
import logging
from pathlib import Path
from services import transcription_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_transcription():
    """Test audio transcription and show full results"""
    print("🎵 Audio Transcription Test")
    print("=" * 50)
    
    test_audio_path = Path("backend/test_files/test_audio.wav")
    
    if not test_audio_path.exists():
        print(f"❌ Audio file not found: {test_audio_path}")
        print("Please create a test audio file at that location")
        return
    
    try:
        print(f"📁 Processing audio file: {test_audio_path}")
        print(f"📊 File size: {test_audio_path.stat().st_size / 1024:.1f} KB")
        
        # Initialize transcription service
        if not transcription_service.initialized:
            print("🔄 Initializing transcription service...")
            await transcription_service.initialize()
        
        # Transcribe audio
        print("🎤 Transcribing audio...")
        result = await transcription_service.transcribe_audio_file(str(test_audio_path))
        
        if result["success"]:
            text = result["text"]
            print("\n" + "="*60)
            print("🎵 TRANSCRIPTION RESULT:")
            print("="*60)
            print(text)
            print("="*60)
            
            # Statistics
            print(f"\n📊 Statistics:")
            print(f"  • Total characters: {len(text)}")
            hebrew_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
            print(f"  • Hebrew characters: {hebrew_chars}")
            print(f"  • Words (estimated): {len(text.split())}")
            print(f"  • Model used: {result.get('model', 'Unknown')}")
            
            # Check for Hebrew content
            hebrew_ratio = hebrew_chars / len(text) if text else 0
            print(f"  • Hebrew content ratio: {hebrew_ratio:.1%}")
            
        else:
            print(f"❌ Transcription failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_transcription()) 