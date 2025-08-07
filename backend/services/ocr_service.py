import os
import asyncio
import json
from typing import Optional, Dict, Any, Union, List
from pathlib import Path
import logging

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoProcessor
    from qwen_vl_utils import process_vision_info
    DOTS_OCR_AVAILABLE = True
except ImportError:
    DOTS_OCR_AVAILABLE = False

from config import settings

logger = logging.getLogger(__name__)

class DotsOCRService:
    """Service for document OCR using dots.ocr model"""
    
    def __init__(self):
        self.model_name = settings.dots_ocr_model
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
    def is_available(self) -> bool:
        """Check if dots.ocr dependencies are available and compatible"""
        if not DOTS_OCR_AVAILABLE:
            return False
        
        # Check if we're on Mac (flash_attn doesn't work on Mac)
        import platform
        if platform.system() == "Darwin":
            logger.info("Running on macOS - dots.ocr not available (flash_attn not supported)")
            return False
        
        return True
        
    async def initialize(self):
        """Initialize the dots.ocr model"""
        if not self.is_available():
            logger.warning("Dots.OCR dependencies are not available. Install with: pip install transformers torch qwen-vl-utils accelerate")
            raise RuntimeError("Dots.OCR dependencies are not available")
            
        try:
            logger.info(f"Initializing {self.model_name} model on {self.device}...")
            
            # Import torch at the top level
            import torch
            
            # Check available memory if using CUDA
            if self.device == "cuda":
                try:
                    if torch.cuda.is_available():
                        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                        logger.info(f"GPU memory available: {gpu_memory:.1f} GB")
                        if gpu_memory < 8:
                            logger.warning("Low GPU memory detected. Consider using CPU or a smaller model.")
                except Exception as e:
                    logger.warning(f"Could not check GPU memory: {e}")
            
            # Try to load the model
            try:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.bfloat16,
                    device_map="auto",
                    trust_remote_code=True
                )
                logger.info("Model loaded successfully")
                
            except Exception as e:
                logger.error(f"Failed to load dots.ocr model: {e}")
                logger.warning("Dots.OCR model requires flash_attn. Consider installing it or using Tesseract fallback.")
                raise RuntimeError(f"Dots.OCR model requires flash_attn: {e}")
            
            # Load the processor
            self.processor = AutoProcessor.from_pretrained(
                self.model_name, 
                trust_remote_code=True
            )
            
            logger.info("Dots OCR model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize dots.ocr model: {e}")
            raise
    
    def _create_prompt(self, task_type: str = "full") -> str:
        """Create appropriate prompt based on task type"""
        if task_type == "layout_only":
            return """Please output the layout information from the PDF image, including each layout element's bbox and its category.

1. Bbox format: [x1, y1, x2, y2]
2. Layout Categories: The possible categories are ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title'].
3. Constraints: All layout elements must be sorted according to human reading order.
4. Final Output: The entire output must be a single JSON object."""
        
        elif task_type == "ocr_only":
            return """Please extract all text content from the image, excluding Page-header and Page-footer elements.

1. Extract text from all text elements, titles, captions, footnotes, and list items.
2. For tables, format the text as HTML.
3. For formulas, format the text as LaTeX.
4. The output text must be the original text from the image, with no translation.
5. Final Output: Return the extracted text in a clean, readable format."""
        
        else:  # full parsing
            return """Please output the layout information from the PDF image, including each layout element's bbox, its category, and the corresponding text content within the bbox.

1. Bbox format: [x1, y1, x2, y2]
2. Layout Categories: The possible categories are ['Caption', 'Footnote', 'Formula', 'List-item', 'Page-footer', 'Page-header', 'Picture', 'Section-header', 'Table', 'Text', 'Title'].
3. Text Extraction & Formatting Rules:
   - Picture: For the 'Picture' category, the text field should be omitted.
   - Formula: Format its text as LaTeX.
   - Table: Format its text as HTML.
   - All Others (Text, Title, etc.): Format their text as Markdown.
4. Constraints:
   - The output text must be the original text from the image, with no translation.
   - All layout elements must be sorted according to human reading order.
5. Final Output: The entire output must be a single JSON object."""
    
    async def extract_text_from_image(
        self, 
        image_path: Union[str, Path], 
        task_type: str = "full"
    ) -> Dict[str, Any]:
        """Extract text from image using dots.ocr"""
        if not self.model or not self.processor:
            raise RuntimeError("Dots.OCR model not initialized")
            
        try:
            logger.info(f"Processing image with dots.ocr: {image_path}")
            
            # Create prompt based on task type
            prompt = self._create_prompt(task_type)
            
            # Prepare messages for the model
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": str(image_path)},
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
            
            # Prepare inputs for inference
            text = self.processor.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            )
            
            # Move inputs to device
            inputs = inputs.to(self.device)
            
            # Generate output
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs, 
                    max_new_tokens=24000,
                    do_sample=False
                )
            
            # Decode the generated text
            generated_ids_trimmed = [
                out_ids[len(in_ids):] 
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            
            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]
            
            # Parse JSON if it's a structured output
            try:
                if task_type == "full" or task_type == "layout_only":
                    parsed_output = json.loads(output_text)
                    return {
                        "text": output_text,
                        "parsed": parsed_output,
                        "task_type": task_type,
                        "success": True
                    }
                else:
                    return {
                        "text": output_text,
                        "parsed": None,
                        "task_type": task_type,
                        "success": True
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                return {
                    "text": output_text,
                    "parsed": None,
                    "task_type": task_type,
                    "success": True
                }
                
        except Exception as e:
            logger.error(f"Dots OCR failed for {image_path}: {e}")
            raise
    
    async def extract_text_from_pdf(
        self, 
        pdf_path: Union[str, Path], 
        task_type: str = "full",
        num_threads: int = 4,
        dpi: int = 200
    ) -> Dict[str, Any]:
        """Extract text from PDF using dots.ocr with optimized processing"""
        if not self.model or not self.processor:
            raise RuntimeError("Dots.OCR model not initialized")
            
        try:
            logger.info(f"Processing PDF with dots.ocr: {pdf_path}")
            
            # Check if PyMuPDF is available
            try:
                import fitz  # PyMuPDF
            except ImportError:
                raise RuntimeError("PyMuPDF (fitz) is required for PDF processing. Install with: pip install PyMuPDF")
            
            doc = fitz.open(str(pdf_path))
            all_results = []
            total_pages = len(doc)
            
            logger.info(f"Processing {total_pages} pages with DPI {dpi}")
            
            # Process pages with progress tracking
            for page_num in range(total_pages):
                try:
                    page = doc.load_page(page_num)
                    
                    # Convert page to image with optimal DPI for dots.ocr
                    # Dots.ocr works best with DPI 200-300
                    mat = fitz.Matrix(dpi/72, dpi/72)  # Convert DPI to zoom factor
                    pix = page.get_pixmap(matrix=mat)
                    
                    # Save temporary image with better naming
                    temp_image_path = f"/tmp/dots_ocr_pdf_{page_num}_{hash(str(pdf_path))}.png"
                    pix.save(temp_image_path)
                    
                    logger.debug(f"Processing page {page_num + 1}/{total_pages}")
                    
                    # Process the page image with dots.ocr
                    page_result = await self.extract_text_from_image(temp_image_path, task_type)
                    page_result["page_num"] = page_num + 1
                    page_result["page_total"] = total_pages
                    all_results.append(page_result)
                    
                    # Clean up temporary file immediately
                    try:
                        os.remove(temp_image_path)
                    except Exception as e:
                        logger.warning(f"Failed to remove temp file {temp_image_path}: {e}")
                    
                    # Memory cleanup after each page
                    del pix
                    del page
                    
                except Exception as e:
                    logger.error(f"Failed to process page {page_num + 1}: {e}")
                    # Add error result for this page
                    all_results.append({
                        "page_num": page_num + 1,
                        "page_total": total_pages,
                        "success": False,
                        "error": str(e),
                        "text": "",
                        "parsed": None
                    })
            
            doc.close()
            
            # Combine results from all pages with better formatting
            combined_text = ""
            successful_pages = 0
            
            for i, result in enumerate(all_results):
                if result.get("success", False):
                    successful_pages += 1
                    page_text = result.get("text", "")
                    if page_text.strip():
                        combined_text += f"\n\n--- עמוד {result['page_num']} ---\n\n{page_text}"
                else:
                    combined_text += f"\n\n--- עמוד {result['page_num']} (שגיאה) ---\n\n"
            
            logger.info(f"PDF processing completed: {successful_pages}/{total_pages} pages successful")
            
            return {
                "text": combined_text.strip(),
                "pages": all_results,
                "task_type": task_type,
                "success": successful_pages > 0,
                "total_pages": total_pages,
                "successful_pages": successful_pages,
                "dpi_used": dpi
            }
            
        except Exception as e:
            logger.error(f"Dots OCR failed for PDF {pdf_path}: {e}")
            raise
    
    async def cleanup_memory(self):
        """Clean up model memory and GPU cache"""
        try:
            if self.model:
                # Move model to CPU to free GPU memory
                if hasattr(self.model, 'to'):
                    self.model.to('cpu')
                
                # Delete model references
                del self.model
                self.model = None
                
            if self.processor:
                del self.processor
                self.processor = None
            
            # Clear GPU cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("GPU memory cache cleared")
            
            logger.info("Dots.OCR memory cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information"""
        try:
            memory_info = {
                "model_loaded": self.model is not None,
                "processor_loaded": self.processor is not None,
                "device": self.device
            }
            
            if torch.cuda.is_available():
                memory_info.update({
                    "gpu_memory_allocated": f"{torch.cuda.memory_allocated() / 1024**3:.2f} GB",
                    "gpu_memory_reserved": f"{torch.cuda.memory_reserved() / 1024**3:.2f} GB",
                    "gpu_memory_total": f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
                })
            
            return memory_info
            
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {"error": str(e)}
    
    async def reload_model(self):
        """Reload the model (useful after memory cleanup)"""
        try:
            await self.cleanup_memory()
            await self.initialize()
            logger.info("Model reloaded successfully")
        except Exception as e:
            logger.error(f"Error reloading model: {e}")
            raise

class TesseractOCRService:
    """Fallback OCR service using Tesseract"""
    
    def __init__(self):
        self.lang = settings.tesseract_lang
        
    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        return TESSERACT_AVAILABLE
    
    async def extract_text_from_image(self, image_path: Union[str, Path]) -> str:
        """Extract text from image using Tesseract OCR"""
        if not self.is_available():
            raise RuntimeError("Tesseract OCR is not available")
        
        try:
            image = Image.open(image_path)
            # Configure Tesseract for Hebrew + English
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(
                image, 
                lang=self.lang,
                config=custom_config
            )
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR failed for {image_path}: {e}")
            raise

class OCRService:
    """Main OCR service that coordinates different OCR methods"""
    
    def __init__(self):
        self.dots_ocr = DotsOCRService()
        self.tesseract_ocr = TesseractOCRService()
        self.initialized = False
    
    async def initialize(self):
        """Initialize OCR services"""
        if not self.initialized:
            try:
                await self.dots_ocr.initialize()
                logger.info("OCR Service initialized successfully")
                self.initialized = True
            except Exception as e:
                logger.warning(f"Failed to initialize dots.ocr, will use fallback: {e}")
                self.initialized = True
    
    async def extract_text_from_image(
        self, 
        image_path: Union[str, Path],
        use_fallback: bool = True,
        task_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Extract text from image using primary or fallback OCR
        
        Args:
            image_path: Path to the image file
            use_fallback: Whether to use Tesseract as fallback
            task_type: Type of OCR task ("full", "layout_only", "ocr_only")
        
        Returns:
            Dict with extracted text and metadata
        """
        if not self.initialized:
            await self.initialize()
        
        result = {
            "text": "",
            "method": "",
            "success": False,
            "error": None,
            "parsed": None,
            "task_type": task_type
        }
        
        # Try dots.ocr first if available
        if self.dots_ocr.is_available():
            try:
                dots_result = await self.dots_ocr.extract_text_from_image(image_path, task_type)
                result.update({
                    "text": dots_result["text"],
                    "method": "dots.ocr",
                    "success": True,
                    "parsed": dots_result.get("parsed"),
                    "task_type": dots_result.get("task_type", task_type)
                })
                return result
            except Exception as e:
                logger.warning(f"Dots OCR failed: {e}")
                result["error"] = str(e)
        
        # Fallback to Tesseract if enabled
        if use_fallback and self.tesseract_ocr.is_available():
            try:
                text = await self.tesseract_ocr.extract_text_from_image(image_path)
                result.update({
                    "text": text,
                    "method": "tesseract",
                    "success": True,
                    "error": None
                })
                return result
            except Exception as e:
                logger.error(f"Tesseract OCR also failed: {e}")
                result["error"] = f"Both OCR methods failed. Dots: {result['error']}, Tesseract: {str(e)}"
        
        return result
    
    async def extract_text_from_pdf(
        self, 
        pdf_path: Union[str, Path],
        use_fallback: bool = True,
        task_type: str = "full"
    ) -> Dict[str, Any]:
        """
        Extract text from PDF using primary or fallback OCR
        
        Args:
            pdf_path: Path to the PDF file
            use_fallback: Whether to use Tesseract as fallback
            task_type: Type of OCR task ("full", "layout_only", "ocr_only")
        
        Returns:
            Dict with extracted text and metadata
        """
        if not self.initialized:
            await self.initialize()
        
        result = {
            "text": "",
            "method": "",
            "success": False,
            "error": None,
            "parsed": None,
            "task_type": task_type,
            "total_pages": 0
        }
        
        # Try dots.ocr first if available
        if self.dots_ocr.is_available():
            try:
                dots_result = await self.dots_ocr.extract_text_from_pdf(pdf_path, task_type)
                result.update({
                    "text": dots_result["text"],
                    "method": "dots.ocr",
                    "success": True,
                    "parsed": dots_result.get("parsed"),
                    "task_type": dots_result.get("task_type", task_type),
                    "total_pages": dots_result.get("total_pages", 0),
                    "pages": dots_result.get("pages", [])
                })
                return result
            except Exception as e:
                logger.warning(f"Dots OCR failed for PDF: {e}")
                result["error"] = str(e)
        
        # For PDF fallback, we'd need to implement PDF to image conversion
        # and then use Tesseract on each page
        if use_fallback:
            logger.warning("PDF fallback to Tesseract not implemented yet")
            result["error"] = "PDF processing fallback not available"
        
        return result

# Global OCR service instance
ocr_service = OCRService()