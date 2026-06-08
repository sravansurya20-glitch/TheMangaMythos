import os
import sys
import json
import base64
import time
import requests
import argparse
from pathlib import Path

# Force UTF-8 output on Windows
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

API_KEY = os.environ.get("GEMINI_API_KEY")

def get_mime_type(file_path):
    ext = os.path.splitext(file_path.lower())[1]
    if ext in ['.png']:
        return 'image/png'
    elif ext in ['.webp']:
        return 'image/webp'
    return 'image/jpeg'

def scan_image(image_path):
    if not API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)
        
    try:
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        print(f"Error reading {image_path}: {e}")
        return None

    mime_type = get_mime_type(image_path)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    
    prompt = """Analyze this manga panel, comic panel, or anime character illustration. 
1. Identify any specific anime characters present (e.g. "asta", "yuno", "noelle", "yami", "julius", "luffy", "zoro", "shanks", "ichigo", "aizen", "jinwoo", "igris", etc. in lowercase). If none are recognizable, return an empty array.
2. Provide a 1-sentence description of the visual scene.
3. List 5-8 semantic keywords summarizing elements present (e.g. "sword", "fight", "spells", "magic", "fire", "screaming", "smiling", "dark", "cape", "power").
Return the result in valid JSON format matching the schema."""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": image_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "characters": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    },
                    "description": {"type": "STRING"},
                    "keywords": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                },
                "required": ["characters", "description", "keywords"]
            }
        }
    }

    headers = {"Content-Type": "application/json"}
    
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=20)
            if r.status_code == 200:
                res_data = r.json()
                text_response = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return json.loads(text_response)
            elif r.status_code == 429:
                print("  Rate limited (429). Retrying after 10s...")
                time.sleep(10)
            else:
                print(f"  API Error {r.status_code}: {r.text}")
                time.sleep(2)
        except Exception as e:
            print(f"  Attempt {attempt} failed: {e}")
            time.sleep(2)
            
    return None

def process_directory(directory_path, limit=None):
    if not os.path.exists(directory_path):
        print(f"Error: Directory {directory_path} does not exist.")
        return
        
    db_path = os.path.join(directory_path, "image_metadata.json")
    
    # Load database
    db = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                db = json.load(f)
            print(f"Loaded existing database with {len(db)} entries.")
        except Exception as e:
            print(f"Warning: Could not read existing database, starting fresh: {e}")

    # Scan for images
    supported_exts = ('.png', '.jpg', '.jpeg', '.webp')
    all_files = os.listdir(directory_path)
    img_files = [f for f in all_files if f.lower().endswith(supported_exts)]
    
    unprocessed = [f for f in img_files if f not in db]
    print(f"Found {len(img_files)} total images. {len(unprocessed)} need processing.")
    
    if not unprocessed:
        print("All images are already processed.")
        return

    processed_count = 0
    for idx, filename in enumerate(unprocessed):
        if limit and processed_count >= limit:
            print(f"Reached processing limit of {limit} images.")
            break
            
        full_path = os.path.join(directory_path, filename)
        print(f"[{processed_count + 1}/{len(unprocessed)}] Analyzing: {filename}...")
        
        result = scan_image(full_path)
        if result:
            db[filename] = result
            # Save progress immediately
            try:
                with open(db_path, "w", encoding="utf-8") as f:
                    json.dump(db, f, indent=2)
                print(f"  Saved metadata. Characters: {result['characters']}, Keywords: {result['keywords']}")
            except Exception as e:
                print(f"  Failed to save database: {e}")
            processed_count += 1
        else:
            print(f"  Failed to analyze {filename}.")
            
        # Free-tier rate compliance: 15 RPM max -> 4 seconds sleep between requests
        time.sleep(4.5)
        
    print(f"Finished processing! Saved {processed_count} new entries to {db_path}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan and tag manga images using Gemini 1.5 Flash")
    parser.add_argument("directory", help="Path to the directory containing images")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of images to process in this run")
    parser.add_argument("--test", action="store_true", help="Run a test scan on the first image found")
    
    args = parser.parse_args()
    
    # Load env variables from local .env if run directly
    try:
        from dotenv import load_dotenv
        # Look for .env in parent directory of scripts
        load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
        # Also try current directory
        load_dotenv()
    except ImportError:
        pass
        
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        # Fallback check if it's set on system
        print("Warning: GEMINI_API_KEY environment variable not found in system env or .env file.")
        
    if args.test:
        process_directory(args.directory, limit=1)
    else:
        process_directory(args.directory, limit=args.limit)
