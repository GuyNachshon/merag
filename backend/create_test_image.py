#!/usr/bin/env python3
"""
Create a test image with Hebrew text for OCR verification
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_hebrew_test_image():
    """Create a test image with Hebrew text"""
    
    # Create a white image
    width, height = 800, 400
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    
    # Hebrew text to test
    hebrew_text = """שלום עולם!
זהו טקסט בעברית לבדיקת OCR
המערכת צריכה לזהות את הטקסט הזה
ולהמיר אותו לטקסט דיגיטלי
"""
    
    try:
        # Try to use a Hebrew font if available
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
    except:
        try:
            # Fallback to default font
            font = ImageFont.load_default()
        except:
            # Last resort - use default
            font = None
    
    # Draw text
    text_bbox = draw.textbbox((0, 0), hebrew_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # Center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), hebrew_text, fill='black', font=font)
    
    # Save the image
    output_path = "test_hebrew_image.png"
    image.save(output_path)
    
    print(f"✅ Created test image: {output_path}")
    print(f"📝 Image contains Hebrew text for OCR testing")
    
    return output_path

if __name__ == "__main__":
    create_hebrew_test_image() 