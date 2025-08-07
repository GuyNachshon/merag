#!/usr/bin/env python3
"""
Test script for layout-aware OCR processing
"""

import asyncio
import logging
from pathlib import Path
from services.ocr_service import ocr_service
from services.document_processor import document_processor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_layout_aware_processing():
    """Test the layout-aware OCR processing"""
    
    print("Testing layout-aware OCR processing...")
    
    # Initialize services
    await ocr_service.initialize()
    await document_processor.initialize()
    
    # Test with a sample image (if available)
    test_image_path = Path("test_image.png")
    if test_image_path.exists():
        print(f"Testing with image: {test_image_path}")
        
        try:
            # Test direct OCR
            ocr_result = await ocr_service.extract_text_from_image(
                test_image_path, 
                task_type="full"
            )
            
            print("✅ Direct OCR successful")
            print(f"Method: {ocr_result['method']}")
            print(f"Has layout info: {ocr_result.get('parsed') is not None}")
            
            if ocr_result.get("parsed"):
                layout_data = ocr_result["parsed"]
                elements = layout_data.get("elements", [])
                print(f"Layout elements: {len(elements)}")
                
                # Count element types
                element_types = {}
                for element in elements:
                    element_type = element.get("category", "Unknown")
                    element_types[element_type] = element_types.get(element_type, 0) + 1
                
                print("Element types found:")
                for element_type, count in element_types.items():
                    print(f"  - {element_type}: {count}")
            
            # Test document processing
            doc_result = await document_processor.process_document(test_image_path)
            
            if doc_result["success"]:
                print("✅ Document processing successful")
                print(f"Documents created: {len(doc_result['documents'])}")
                
                # Check metadata
                metadata = doc_result["metadata"]
                print(f"Layout aware: {metadata.get('layout_aware', False)}")
                print(f"OCR enhanced: {metadata.get('ocr_enhanced', False)}")
                
                if metadata.get("has_tables"):
                    print("✅ Tables detected")
                if metadata.get("has_formulas"):
                    print("✅ Formulas detected")
                if metadata.get("has_text_blocks"):
                    print("✅ Text blocks detected")
                
                # Show sample content
                if doc_result["documents"]:
                    sample_doc = doc_result["documents"][0]
                    print(f"\nSample content preview:")
                    print(f"Content length: {len(sample_doc.page_content)} characters")
                    print(f"Content preview: {sample_doc.page_content[:200]}...")
                    
                    # Show metadata
                    print(f"\nDocument metadata:")
                    for key, value in sample_doc.metadata.items():
                        if key != "layout_data":  # Skip large layout data
                            print(f"  {key}: {value}")
            else:
                print(f"❌ Document processing failed: {doc_result.get('error')}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")
    else:
        print("ℹ️  No test image found. Create a 'test_image.png' file to test layout-aware processing")
    
    # Test with a sample PDF (if available)
    test_pdf_path = Path("test_document.pdf")
    if test_pdf_path.exists():
        print(f"\nTesting with PDF: {test_pdf_path}")
        
        try:
            doc_result = await document_processor.process_document(test_pdf_path)
            
            if doc_result["success"]:
                print("✅ PDF processing successful")
                print(f"Documents created: {len(doc_result['documents'])}")
                
                metadata = doc_result["metadata"]
                print(f"Layout aware: {metadata.get('layout_aware', False)}")
                print(f"OCR enhanced: {metadata.get('ocr_enhanced', False)}")
            else:
                print(f"❌ PDF processing failed: {doc_result.get('error')}")
                
        except Exception as e:
            print(f"❌ PDF test error: {e}")
    else:
        print("ℹ️  No test PDF found. Create a 'test_document.pdf' file to test PDF processing")
    
    print("\nLayout-Aware Processing Status:")
    print(f"Dots.OCR available: {ocr_service.dots_ocr.is_available()}")
    print(f"Document processor initialized: {document_processor is not None}")

if __name__ == "__main__":
    asyncio.run(test_layout_aware_processing()) 