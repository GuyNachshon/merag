#!/usr/bin/env python3
"""
Comprehensive Verification Test
Tests that the enhanced features are actually working correctly
"""

import asyncio
import logging
from pathlib import Path
from services import ocr_service, document_processor
from config.settings import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ocr_verification():
    """Verify OCR is actually working"""
    print("\n🔍 OCR Verification Test")
    print("=" * 50)
    
    # Create a test image with Hebrew text
    test_image_path = Path("test_hebrew_image.png")
    
    if not test_image_path.exists():
        print("❌ No test image found. Create 'test_hebrew_image.png' with Hebrew text")
        return False
    
    try:
        # Test Tesseract OCR
        print("Testing Tesseract OCR...")
        result = await ocr_service.extract_text_from_image(test_image_path)
        
        if result["success"]:
            text = result["text"]
            print(f"✅ OCR Success! Extracted {len(text)} characters")
            print(f"📝 First 100 chars: {text[:100]}...")
            
            # Check if Hebrew characters are present
            hebrew_chars = sum(1 for c in text if '\u0590' <= c <= '\u05FF')
            print(f"🇮🇱 Hebrew characters found: {hebrew_chars}")
            
            return hebrew_chars > 0
        else:
            print(f"❌ OCR failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ OCR test failed: {e}")
        return False

async def test_memory_management_verification():
    """Verify memory management is actually working"""
    print("\n🧠 Memory Management Verification")
    print("=" * 50)
    
    try:
        import psutil
        process = psutil.Process()
        
        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"📊 Initial memory usage: {initial_memory:.1f} MB")
        
        # Process multiple documents to test memory cleanup
        test_files = []
        for i in range(5):
            test_file = Path(f"test_doc_{i}.txt")
            test_file.write_text(f"זהו מסמך בדיקה מספר {i} בעברית")
            test_files.append(test_file)
        
        # Process documents
        print("📄 Processing 5 test documents...")
        result = await document_processor.process_multiple_documents(test_files)
        
        # Get memory after processing
        after_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"📊 Memory after processing: {after_memory:.1f} MB")
        
        # Clean up test files
        for test_file in test_files:
            test_file.unlink()
        
        # Check memory difference
        memory_diff = after_memory - initial_memory
        print(f"📊 Memory difference: {memory_diff:+.1f} MB")
        
        # Success if memory didn't grow too much (indicating cleanup worked)
        success = memory_diff < 100  # Less than 100MB growth
        print(f"{'✅' if success else '❌'} Memory management: {'Good' if success else 'Poor'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        return False

async def test_configuration_verification():
    """Verify configuration validation is comprehensive"""
    print("\n⚙️ Configuration Verification")
    print("=" * 50)
    
    try:
        validation = await settings.validate_configuration()
        
        print(f"📊 Overall Status: {validation['overall_status']}")
        print(f"📊 Errors: {len(validation['errors'])}")
        print(f"📊 Warnings: {len(validation['warnings'])}")
        print(f"📊 Info: {len(validation['info'])}")
        
        # Check specific validations
        env_info = validation['environment_info']
        
        checks = [
            ("Python Version", env_info.get('python_version')),
            ("CUDA Available", env_info.get('cuda_available')),
            ("System Memory", env_info.get('system_memory_gb')),
            ("Torch Available", env_info.get('torch_available')),
            ("Transformers Available", env_info.get('transformers_available')),
            ("FastEmbed Available", env_info.get('fastembed_available')),
            ("Qdrant Client Available", env_info.get('qdrant_client_available')),
            ("PyMuPDF Available", env_info.get('fitz_available')),
            ("Tesseract Available", env_info.get('pytesseract_available')),
        ]
        
        passed_checks = 0
        for name, value in checks:
            status = "✅" if value else "❌"
            print(f"{status} {name}: {value}")
            if value:
                passed_checks += 1
        
        print(f"\n📊 Configuration checks passed: {passed_checks}/{len(checks)}")
        
        return passed_checks >= 7  # At least 7 out of 9 checks should pass
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def test_batch_processing_verification():
    """Verify batch processing is actually working"""
    print("\n📦 Batch Processing Verification")
    print("=" * 50)
    
    try:
        # Create test documents with different content
        test_files = []
        test_contents = [
            "זהו מסמך ראשון בעברית עם תוכן מעניין",
            "מסמך שני עם מידע נוסף ופרטים חשובים",
            "המסמך השלישי מכיל נתונים סטטיסטיים וטבלאות"
        ]
        
        for i, content in enumerate(test_contents):
            test_file = Path(f"batch_test_{i}.txt")
            test_file.write_text(content)
            test_files.append(test_file)
        
        # Process in batch
        print("📄 Processing batch of 3 documents...")
        result = await document_processor.process_multiple_documents(test_files)
        
        print(f"📊 Total documents: {result['total_documents']}")
        print(f"📊 Total chunks: {result['total_chunks']}")
        print(f"📊 Failed: {len(result['failed'])}")
        
        # Clean up
        for test_file in test_files:
            test_file.unlink()
        
        # Verify results
        success = (
            result['total_documents'] == 3 and
            result['total_chunks'] >= 3 and
            len(result['failed']) == 0
        )
        
        print(f"{'✅' if success else '❌'} Batch processing: {'Success' if success else 'Failed'}")
        
        return success
        
    except Exception as e:
        print(f"❌ Batch processing test failed: {e}")
        return False

async def test_audio_processing_verification():
    """Verify audio processing is actually working"""
    print("\n🎵 Audio Processing Verification")
    print("=" * 50)
    
    test_audio_path = Path("backend/test_files/test_audio.wav")
    
    if not test_audio_path.exists():
        print("ℹ️ No test audio found. Skipping audio verification.")
        return True
    
    try:
        # Process audio
        print("🎵 Processing test audio file...")
        result = await document_processor.process_document(test_audio_path)
        
        if result["success"]:
            documents = result.get("documents", [])
            if documents:
                text = documents[0].page_content
                print(f"✅ Audio transcription successful!")
                print(f"📝 Transcribed text length: {len(text)} characters")
                print(f"🇮🇱 Hebrew characters in transcription: {sum(1 for c in text if '\u0590' <= c <= '\u05FF')}")
                print("\n" + "="*50)
                print("🎵 FULL TRANSCRIPTION:")
                print("="*50)
                print(text)
                print("="*50)
                
                return len(text) > 50  # Should have substantial transcription
            else:
                print("❌ No documents created from audio")
                return False
        else:
            print(f"❌ Audio processing failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False

async def main():
    """Run comprehensive verification tests"""
    print("🔬 Comprehensive Feature Verification")
    print("=" * 60)
    
    tests = [
        ("OCR Verification", test_ocr_verification),
        ("Memory Management Verification", test_memory_management_verification),
        ("Configuration Verification", test_configuration_verification),
        ("Batch Processing Verification", test_batch_processing_verification),
        ("Audio Processing Verification", test_audio_processing_verification)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = await test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Verification Results Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} verifications passed")
    
    if passed == total:
        print("🎉 All features are working correctly!")
    else:
        print("⚠️ Some features need attention")

if __name__ == "__main__":
    asyncio.run(main()) 