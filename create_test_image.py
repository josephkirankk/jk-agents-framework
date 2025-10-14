#!/usr/bin/env python3
"""
Create a test image for multimodal processing
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

# Create a new image with white background
def create_test_image(output_path="test_image.png"):
    # Create a 400x300 image with white background
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw geometric shapes
    draw.rectangle([50, 50, 150, 100], fill='blue', outline='black', width=2)
    draw.ellipse([160, 35, 240, 115], fill='red', outline='black', width=2)
    draw.polygon([(300, 50), (350, 100), (250, 100)], fill='green', outline='black', width=2)
    
    # Add text
    try:
        # Use a default font
        font = ImageFont.load_default()
        draw.text((50, 150), "Test Image Analysis", fill='black', font=font)
        draw.text((50, 180), "Blue Rectangle", fill='blue', font=font)
        draw.text((50, 210), "Red Circle", fill='red', font=font)
        draw.text((50, 240), "Green Triangle", fill='green', font=font)
    except Exception as e:
        print(f"Warning: Font issue: {e}")
        # Fallback without font specification
        draw.text((50, 150), "Test Image Analysis", fill='black')
        draw.text((50, 180), "Blue Rectangle", fill='blue')
        draw.text((50, 210), "Red Circle", fill='red')
        draw.text((50, 240), "Green Triangle", fill='green')
    
    # Save the image
    img.save(output_path)
    print(f"✅ Test image created at: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

if __name__ == "__main__":
    create_test_image()
