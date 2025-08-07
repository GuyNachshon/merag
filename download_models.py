#!/usr/bin/env python3
"""
Download and cache ML models for airgapped deployment
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """Setup environment variables for model caching"""
    os.environ['HF_HOME'] = '/app/models'
    os.environ['TRANSFORMERS_CACHE'] = '/app/models/transformers'
    os.environ['FASTEMBED_CACHE_DIR'] = '/app/models/fastembed'
    
    # Create model directories
    model_dirs = [
        '/app/models/fastembed',
        '/app/models/whisper', 
        '/app/models/dots-ocr',
        '/app/models/transformers'
    ]
    
    for dir_path in model_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def download_fastembed():
    """Download FastEmbed model"""
    try:
        print("📥 Downloading FastEmbed model...")
        from fastembed import TextEmbedding
        embedding = TextEmbedding('intfloat/multilingual-e5-large', cache_dir='/app/models/fastembed')
        print("✅ FastEmbed model downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ FastEmbed download failed: {e}")
        return False

def download_whisper():
    """Download Whisper model"""
    try:
        print("📥 Downloading Whisper model...")
        from transformers import WhisperProcessor, WhisperForConditionalGeneration
        processor = WhisperProcessor.from_pretrained('ivrit-ai/whisper-large-v3', cache_dir='/app/models/whisper')
        model = WhisperForConditionalGeneration.from_pretrained('ivrit-ai/whisper-large-v3', cache_dir='/app/models/whisper')
        print("✅ Whisper model downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Whisper download failed: {e}")
        return False

def download_dots_ocr():
    """Download Dots.OCR model"""
    try:
        print("📥 Downloading Dots.OCR model...")
        from transformers import AutoModelForCausalLM, AutoProcessor
        
        # Download dots.ocr model
        dots_model = AutoModelForCausalLM.from_pretrained(
            'rednote-hilab/dots.ocr',
            torch_dtype='auto',
            device_map='auto',
            trust_remote_code=True,
            cache_dir='/app/models/dots-ocr'
        )
        
        dots_processor = AutoProcessor.from_pretrained(
            'rednote-hilab/dots.ocr',
            trust_remote_code=True,
            cache_dir='/app/models/dots-ocr'
        )
        
        print("✅ Dots.OCR model downloaded successfully")
        return True
    except Exception as e:
        print(f"⚠️  Dots.OCR model download failed: {e}")
        print("⚠️  Will use Tesseract fallback for OCR")
        return False

def verify_models():
    """Verify that models were downloaded successfully"""
    print("\n🔍 Verifying model downloads...")
    
    models_to_check = [
        ('FastEmbed', '/app/models/fastembed'),
        ('Whisper', '/app/models/whisper'),
        ('Dots.OCR', '/app/models/dots-ocr')
    ]
    
    all_verified = True
    
    for model_name, cache_path in models_to_check:
        if os.path.exists(cache_path) and len(os.listdir(cache_path)) > 0:
            print(f"✅ {model_name} model verified")
        else:
            print(f"❌ {model_name} model not found")
            all_verified = False
    
    return all_verified

def main():
    """Main download function"""
    print("🚀 Starting ML model download process...")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Download models
    results = []
    results.append(download_fastembed())
    results.append(download_whisper())
    results.append(download_dots_ocr())
    
    # Verify downloads
    verification_passed = verify_models()
    
    print("\n" + "=" * 50)
    print("📦 Model download summary:")
    print(f"  • FastEmbed: {'✅' if results[0] else '❌'}")
    print(f"  • Whisper: {'✅' if results[1] else '❌'}")
    print(f"  • Dots.OCR: {'✅' if results[2] else '❌'}")
    print(f"  • Verification: {'✅' if verification_passed else '❌'}")
    
    if all(results):
        print("\n🎉 All models downloaded successfully!")
        return 0
    else:
        print("\n⚠️  Some models failed to download, but system will still work with fallbacks")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 