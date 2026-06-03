import os
import re
import fitz  # PyMuPDF
import zipfile
import io
from PIL import Image
import sys

# Ensure outputs are written in UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Ad keywords for text-based filtering (primarily for One Piece print-to-pdf pages)
AD_KEYWORDS = [
    "download chapter", "ad will open", "comments", "contact us", "insurance", 
    "cheapest", "menu \u2630", "previous chapter", 
    "next chapter", "share on", "facebook", "twitter", "tumblr", "reddit", 
    "pinterest", "report", "go to top", "ichi the witch", "sakamoto days", 
    "kagurabachi", "my anime twin", "read manga", "join them in the comments",
    "savvy savings online", "check zip codes"
]

def is_ad_text(text):
    text_lower = text.lower()
    for kw in AD_KEYWORDS:
        if kw in text_lower:
            return True
    return False

def is_blank_or_solid(img, threshold=240, max_non_white_ratio=0.03, max_non_black_ratio=0.03):
    """
    Check if the image is mostly white or mostly black (blank/solid page).
    """
    # Resize to 50x50 to speed up calculation
    img_small = img.convert("L").resize((50, 50))
    pixels = list(img_small.getdata())
    n_pixels = len(pixels)
    
    # White check
    white_pixels = sum(1 for p in pixels if p >= threshold)
    if (white_pixels / n_pixels) > (1.0 - max_non_white_ratio):
        return True
        
    # Black check
    black_pixels = sum(1 for p in pixels if p <= (255 - threshold))
    if (black_pixels / n_pixels) > (1.0 - max_non_black_ratio):
        return True
        
    return False

def clean_and_extract_pdf(pdf_path, output_dir):
    filename = os.path.basename(pdf_path)
    chapter_name = os.path.splitext(filename)[0]
    chapter_out_dir = os.path.join(output_dir, chapter_name)
    os.makedirs(chapter_out_dir, exist_ok=True)
    
    print(f"Extracting PDF: {filename}...")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    extracted_count = 0
    
    # Check if this is Solo Leveling or standard vertical manhwa
    is_vertical_manhwa = "solo leveling" in filename.lower() or "vertical" in filename.lower()
    
    for i in range(total_pages):
        page = doc[i]
        rect = page.rect
        width, height = rect.width, rect.height
        
        # 1. Text-based ad filtering
        text = page.get_text()
        if is_ad_text(text):
            print(f"  [Skip] Page {i} contains ad-related text.")
            continue
            
        # 2. Aspect Ratio Filter (for vertical manhwa like Solo Leveling)
        # Webtoon strips are extremely tall, while ads are normal screen aspect ratios
        if is_vertical_manhwa:
            aspect_ratio = width / height
            if aspect_ratio > 0.45:
                print(f"  [Skip] Page {i} aspect ratio ({aspect_ratio:.2f}) indicates an ad/credit banner.")
                continue
            # Also skip the very first and last pages if they are likely credits/covers
            if i == 0 or i == total_pages - 1:
                print(f"  [Skip] Page {i} is first/last page of manhwa (likely cover/credits).")
                continue
                
        # Render page to high-quality image (scale 2.0 = ~150 DPI)
        matrix = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=matrix)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 3. Blank / Solid color check
        if is_blank_or_solid(img):
            print(f"  [Skip] Page {i} is blank or solid color.")
            continue
            
        # 4. Browser Header/Footer Cropping
        # Many downloaded PDFs have browser print headers/footers (URLs, date, page numbers)
        # We crop top 4% and bottom 4% to remove these cleanly
        if not is_vertical_manhwa and ("readonepiece" in text.lower() or "http" in text.lower()):
            crop_h = int(img.height * 0.04)
            img = img.crop((0, crop_h, img.width, img.height - crop_h))
            
        # Save image
        out_filename = f"page_{i:03d}.png"
        img.save(os.path.join(chapter_out_dir, out_filename))
        extracted_count += 1
        
    print(f"Finished PDF {filename}: extracted {extracted_count}/{total_pages} pages.")
    return extracted_count

def clean_and_extract_cbz(cbz_path, output_dir):
    filename = os.path.basename(cbz_path)
    chapter_name = os.path.splitext(filename)[0]
    chapter_out_dir = os.path.join(output_dir, chapter_name)
    os.makedirs(chapter_out_dir, exist_ok=True)
    
    print(f"Extracting CBZ: {filename}...")
    extracted_count = 0
    
    with zipfile.ZipFile(cbz_path, 'r') as z:
        # Get all image files inside the archive
        file_list = [f for f in z.namelist() if not f.endswith('/') and f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        # Sort files to maintain chronological order
        file_list.sort()
        
        total_files = len(file_list)
        
        for idx, file_in_zip in enumerate(file_list):
            base_name = os.path.basename(file_in_zip).lower()
            
            # Skip common credit/ad image names
            if "credit" in base_name or "ad" in base_name or "zzz" in base_name or "banner" in base_name:
                print(f"  [Skip] {file_in_zip} based on filename.")
                continue
                
            # Read image data
            img_data = z.read(file_in_zip)
            img = Image.open(io.BytesIO(img_data))
            
            # Check if blank or solid
            if is_blank_or_solid(img):
                print(f"  [Skip] {file_in_zip} is blank or solid color.")
                continue
                
            # Save the image
            out_filename = f"page_{idx:03d}.png"
            img.save(os.path.join(chapter_out_dir, out_filename))
            extracted_count += 1
            
    print(f"Finished CBZ {filename}: extracted {extracted_count}/{total_files} pages.")
    return extracted_count

def main():
    source_dir = r"C:\Users\srava\OneDrive\Desktop\Anime Theory"
    target_dir = r"C:\Users\srava\.gemini\antigravity\scratch\anime-theory-youtube\extracted_images"
    
    if not os.path.exists(source_dir):
        print(f"Error: Source directory {source_dir} does not exist.")
        return
        
    os.makedirs(target_dir, exist_ok=True)
    
    files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.pdf', '.cbz'))]
    print(f"Found {len(files)} manga files to process.")
    
    for f in files:
        full_path = os.path.join(source_dir, f)
        if f.lower().endswith('.pdf'):
            clean_and_extract_pdf(full_path, target_dir)
        elif f.lower().endswith('.cbz'):
            clean_and_extract_cbz(full_path, target_dir)

if __name__ == "__main__":
    main()
