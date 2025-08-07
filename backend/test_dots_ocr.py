#!/usr/bin/env python3
"""
Test script for dots.ocr integration
"""

import asyncio
import logging
from pathlib import Path
from services.ocr_service import ocr_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_dots_ocr():
    """Test the dots.ocr integration"""
    
    print("Testing dots.ocr integration...")
    
    # Check if dots.ocr is available
    if not ocr_service.dots_ocr.is_available():
        print("❌ Dots.OCR dependencies are not available")
        print("Please install the required dependencies:")
        print("pip install transformers torch qwen-vl-utils accelerate")
        return
    
    print("✅ Dots.OCR dependencies are available")
    
    # Initialize the OCR service
    try:
        await ocr_service.initialize()
        print("✅ OCR service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize OCR service: {e}")
        return
    
    # Test with a sample image (if available)
    test_image_path = Path("test_image.png")
    if test_image_path.exists():
        print(f"Testing with image: {test_image_path}")
        
        try:
            result = await ocr_service.extract_text_from_image(
                test_image_path, 
                task_type="full"
            )
            
            if result["success"]:
                print("✅ Image OCR successful")
                print(f"Method: {result['method']}")
                print(f"Text length: {len(result['text'])} characters")
                if result.get("parsed"):
                    print(f"Parsed layout elements: {len(result['parsed'])}")
            else:
                print(f"❌ Image OCR failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Image OCR error: {e}")
    else:
        print("ℹ️  No test image found. Create a 'test_image.png' file to test image OCR")
    
    # Test with a sample PDF (if available)
    test_pdf_path = Path("test_document.pdf")
    if test_pdf_path.exists():
        print(f"Testing with PDF: {test_pdf_path}")
        
        try:
            result = await ocr_service.extract_text_from_pdf(
                test_pdf_path, 
                task_type="full"
            )
            
            if result["success"]:
                print("✅ PDF OCR successful")
                print(f"Method: {result['method']}")
                print(f"Total pages: {result.get('total_pages', 0)}")
                print(f"Text length: {len(result['text'])} characters")
            else:
                print(f"❌ PDF OCR failed: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ PDF OCR error: {e}")
    else:
        print("ℹ️  No test PDF found. Create a 'test_document.pdf' file to test PDF OCR")
    
    print("\nOCR Service Status:")
    print(f"Dots.OCR available: {ocr_service.dots_ocr.is_available()}")
    print(f"Tesseract available: {ocr_service.tesseract_ocr.is_available()}")
    print(f"Service initialized: {ocr_service.initialized}")

if __name__ == "__main__":
    asyncio.run(test_dots_ocr()) 