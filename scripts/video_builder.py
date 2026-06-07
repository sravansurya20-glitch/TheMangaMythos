import os
import re
import json
import tempfile
import subprocess
import datetime
import random
import requests
from pathlib import Path
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTH, HEIGHT = 1080, 1920

def get_audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())

EMOJI_MAP = {
    r"\bLUFFY\b": "LUFFY 👒",
    r"\bSHANKS\b": "SHANKS 🏴‍☠️",
    r"\bZORO\b": "ZORO ⚔️",
    r"\bGEAR 5\b": "GEAR 5 ⚡",
    r"\bONE PIECE\b": "ONE PIECE 🏴‍☠️",
    r"\bIMU\b": "IMU 👑",
    r"\bBLACKBEARD\b": "BLACKBEARD 👿",
    r"\bJINWOO\b": "JINWOO 👑",
    r"\bSUNG\b": "SUNG 👑",
    r"\bSHADOW\b": "SHADOW 👿",
    r"\bMONARCH\b": "MONARCH 👑",
    r"\bSYSTEM\b": "SYSTEM ⚙️",
    r"\bICHIGO\b": "ICHIGO ⚔️",
    r"\bAIZEN\b": "AIZEN 🤓",
    r"\bBANKAI\b": "BANKAI 卍",
    r"\bHOLLOW\b": "HOLLOW 👺",
    r"\bQUINCY\b": "QUINCY 🏹",
    r"\bSOUL KING\b": "SOUL KING 👑",
    r"\bNARUTO\b": "NARUTO 🦊",
    r"\bSASUKE\b": "SASUKE 👁️",
    r"\bITACHI\b": "ITACHI 🐦",
    r"\bMADARA\b": "MADARA ☄️",
    r"\bUCHIHA\b": "UCHIHA 👁️",
    r"\bSHARINGAN\b": "SHARINGAN 👁️",
    r"\bAKATSUKI\b": "AKATSUKI ☁️",
    r"\bSECRET\b": "SECRET 🤫",
    r"\bTHEORY\b": "THEORY 🧠",
    r"\bDEATH\b": "DEATH 💀",
    r"\bDIED\b": "DIED 💀",
    r"\bCRAZY\b": "CRAZY 🤯",
    r"\bTRUTH\b": "TRUTH 💯",
    r"\bVILLAIN\b": "VILLAIN 🦹‍♂️",
}

def inject_emojis(text: str) -> str:
    for pattern, replacement in EMOJI_MAP.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def fmt_ass_time(s: float) -> str:
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"

def generate_whisper_ass(audio_path: str) -> str | None:
    """Use OpenAI Whisper for perfectly synced captions with active word pop/highlighting"""
    try:
        import whisper
        print("  Running Whisper for perfect Hormozi-style ASS caption sync...")
        model = whisper.load_model("tiny")
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            language="en"
        )

        all_words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                all_words.append({
                    "word": word_info["word"].strip().upper(),
                    "start": word_info["start"],
                    "end": word_info["end"]
                })

        if not all_words:
            return None

        # Group words into lines of 3 words
        words_per_line = 3
        events = []
        
        # Keywords to highlight in bright Green
        highlight_keywords = {
            "JINWOO", "SUNG", "ASHBORN", "MONARCH", "SHADOW", "SYSTEM", "THRONE", "STEAL", "STOLE", "PROVEN", "PROOF",
            "LUFFY", "SHANKS", "ZORO", "GEAR", "NIKA", "BLACKBEARD", "IMU", "ROGER",
            "ICHIGO", "AIZEN", "BANKAI", "HOLLOW", "QUINCY", "SOUL", "KING", "YHWACH"
        }

        for i in range(0, len(all_words), words_per_line):
            line_chunk = all_words[i:i + words_per_line]
            if not line_chunk:
                continue
            
            # Create a separate Dialogue event for each active word spoke
            for active_idx, active_word_info in enumerate(line_chunk):
                start_time_str = fmt_ass_time(active_word_info["start"])
                end_time_str = fmt_ass_time(active_word_info["end"])
                
                text_parts = []
                for idx, w_info in enumerate(line_chunk):
                    word_clean = w_info["word"]
                    word_clean_nopunct = re.sub(r'[^\w\s]', '', word_clean)
                    
                    is_active = (idx == active_idx)
                    is_keyword = (word_clean_nopunct in highlight_keywords)
                    
                    if is_active:
                        # Highlight active word (Green if keyword, Yellow if normal)
                        color = "&H00FF00&" if is_keyword else "&H00FFFF&"
                        part = f"{{\\c{color}}}{{\\fscx115\\fscy115}}{word_clean}{{\\fscx100\\fscy100}}"
                    else:
                        # Inactive word is white
                        part = f"{{\\c&HFFFFFF&}}{word_clean}"
                    text_parts.append(part)
                
                event_text = " ".join(text_parts)
                event_text = inject_emojis(event_text)
                
                events.append(f"Dialogue: 0,{start_time_str},{end_time_str},Default,,0,0,0,,{event_text}")

        ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&HFFFFFF,&HFFFFFF,&H000000,&H000000,1,0,0,0,100,100,0,0,1,5,0,2,10,10,650,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        ass_content = ass_header + "\n".join(events) + "\n"
        
        tmp = tempfile.NamedTemporaryFile(
            delete=False, suffix=".ass",
            mode='w', encoding='utf-8'
        )
        tmp.write(ass_content)
        tmp.close()
        print("  Hormozi-style Whisper ASS captions generated!")
        return tmp.name

    except Exception as e:
        print(f"  Whisper ASS generation failed: {e}")
        return None

def generate_estimated_ass(script: str, duration: float) -> str:
    """Fallback: estimated timing based on word count with active word pop/highlighting"""
    script = re.sub(r'\s+', ' ', script).strip()
    words = script.split()
    total = len(words)
    if total == 0:
        words = ["..."]
        total = 1

    time_per_word = duration / total
    words_per_line = 3
    events = []

    for i in range(0, total, words_per_line):
        line_chunk = words[i:i + words_per_line]
        line_start = i * time_per_word
        line_end = min((i + words_per_line) * time_per_word, duration)
        
        w_dur = (line_end - line_start) / len(line_chunk)
        
        for active_idx, active_word in enumerate(line_chunk):
            w_start = line_start + active_idx * w_dur
            w_end = w_start + w_dur
            
            start_time_str = fmt_ass_time(w_start)
            end_time_str = fmt_ass_time(w_end)
            
            text_parts = []
            for idx, word in enumerate(line_chunk):
                is_active = (idx == active_idx)
                if is_active:
                    part = f"{{\\c&H00FFFF&}}{{\\fscx115\\fscy115}}{word.upper()}{{\\fscx100\\fscy100}}"
                else:
                    part = f"{{\\c&HFFFFFF&}}{word.upper()}"
                text_parts.append(part)
                
            event_text = " ".join(text_parts)
            event_text = inject_emojis(event_text)
            events.append(f"Dialogue: 0,{start_time_str},{end_time_str},Default,,0,0,0,,{event_text}")

    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,72,&HFFFFFF,&HFFFFFF,&H000000,&H000000,1,0,0,0,100,100,0,0,1,5,0,2,10,10,650,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass_content = ass_header + "\n".join(events) + "\n"
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".ass",
        mode='w', encoding='utf-8'
    )
    tmp.write(ass_content)
    tmp.close()
    return tmp.name

def safe_text(text: str) -> str:
    text = re.sub(r"['\"\[\]{}|\\]", "", text)
    text = text.replace(":", "\\:").replace(",", "\\,")
    text = text.replace("?", "\\?").replace("!", "\\!")
    return text[:55]

def get_images_for_series(series_id: str) -> list:
    search_dirs = [
        r"C:\Users\srava\.gemini\antigravity\scratch\anime-theory-youtube\extracted_images",
        r"C:\Users\srava\OneDrive\Desktop\Anime Theory"
    ]
    
    # Resolve relative repo root fallback for extracted_images if needed
    repo_extracted = os.path.join(REPO_ROOT, "extracted_images")
    if repo_extracted not in search_dirs:
        search_dirs.append(repo_extracted)
        
    matching_folders = []
    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue
        try:
            subfolders = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
            for folder in subfolders:
                folder_name = os.path.basename(folder).lower()
                if series_id == "one_piece" and "one piece" in folder_name:
                    matching_folders.append(folder)
                elif series_id == "solo_leveling" and ("solo leveling" in folder_name or "capitolo" in folder_name):
                    matching_folders.append(folder)
                elif series_id == "bleach" and "bleach" in folder_name:
                    matching_folders.append(folder)
                elif series_id == "naruto" and "naruto" in folder_name:
                    matching_folders.append(folder)
                elif series_id == "black_clover" and "black clover" in folder_name:
                    matching_folders.append(folder)
        except Exception as e:
            print(f"  Warning: Error scanning {base_dir}: {e}")

    # Deduplicate matching folders list
    matching_folders = list(set(matching_folders))
    
    images = []
    for folder in matching_folders:
        for root, _, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    images.append(os.path.join(root, f))
                    
    # Fallback to any folder in extracted_images or Desktop if no images found
    if not images:
        print(f"  Warning: No matching folder/images for series '{series_id}'. Scanning fallbacks...")
        for base_dir in search_dirs:
            if not os.path.exists(base_dir):
                continue
            try:
                subfolders = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
                for folder in subfolders:
                    for root, _, files in os.walk(folder):
                        for f in files:
                            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                                images.append(os.path.join(root, f))
            except Exception as e:
                pass

    random.shuffle(images)
    print(f"  Found {len(images)} total images for series '{series_id}' in folders: {[os.path.basename(f) for f in matching_folders]}")
    return images


def make_panning_clip(image_path: str, duration: float, output_path: str) -> bool:
    """Creates a 30fps vertical video clip with a smooth panning/scrolling effect based on image aspect ratio"""
    try:
        with Image.open(image_path) as img:
            iw, ih = img.size
    except Exception as e:
        print(f"  Error reading image {image_path}: {e}")
        return False
        
    ratio = iw / ih
    
    # Generate the filtergraph for panning/scrolling
    if ratio < 0.45:
        # 1. Tall vertical image (e.g. Solo Leveling webtoon page) -> Scroll top-to-bottom or bottom-to-top
        direction = random.choice(["down", "up"])
        # Scale to 1080 width, maintaining aspect ratio. If it's too short, scale to at least 2100 height.
        if direction == "down":
            vf = f"scale=1080:'max(2100,ih*1080/iw)':flags=lanczos,crop=1080:1920:0:'(in_h-1920)*t/{duration}'"
        else:
            vf = f"scale=1080:'max(2100,ih*1080/iw)':flags=lanczos,crop=1080:1920:0:'(in_h-1920)*(1-t/{duration})'"
    elif ratio > 1.2:
        # 2. Wide horizontal panel -> Scroll left-to-right or right-to-left
        direction = random.choice(["right", "left"])
        if direction == "right":
            vf = f"scale='max(1200,iw*1920/ih)':1920:flags=lanczos,crop=1080:1920:'(in_w-1080)*t/{duration}':0"
        else:
            vf = f"scale='max(1200,iw*1920/ih)':1920:flags=lanczos,crop=1080:1920:'(in_w-1080)*(1-t/{duration})':0"
    else:
        # 3. Square/Standard page -> Diagonal slow pan
        direction = random.choice(["diagonal_down", "diagonal_up", "zoom_center"])
        if direction == "diagonal_down":
            vf = f"scale='max(1296,iw*2304/ih)':'max(2304,ih*1296/iw)':flags=lanczos,crop=1080:1920:'(in_w-1080)*t/{duration}':'(in_h-1920)*t/{duration}'"
        elif direction == "diagonal_up":
            vf = f"scale='max(1296,iw*2304/ih)':'max(2304,ih*1296/iw)':flags=lanczos,crop=1080:1920:'(in_w-1080)*(1-t/{duration})':'(in_h-1920)*(1-t/{duration})'"
        else:
            vf = f"scale='max(1296,iw*2304/ih)':'max(2304,ih*1296/iw)':flags=lanczos,crop=1080:1920:'(in_w-1080)*t/{duration}':'(in_h-1920)/2'"
            
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-vf", vf,
        "-c:v", "libx264",
        "-t", f"{duration:.3f}",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [FFmpeg Error in make_panning_clip] Command failed: {' '.join(cmd)}")
        print(f"  Stderr: {result.stderr}")
    return result.returncode == 0

def build_video(audio_path: str, title: str, script: str = "", anime_series: str = "one_piece") -> str:
    duration = get_audio_duration(audio_path)
    print(f"  Audio duration: {duration:.1f}s")
    
    # 1. Fetch images for this series
    images = get_images_for_series(anime_series)
    if not images:
        raise RuntimeError(f"No extracted manga images found for '{anime_series}'. Please make sure pdf_extractor has run successfully.")
        
    # We will use 5 images for a standard Short, meaning ~10s per image
    num_clips = 5
    if len(images) < num_clips:
        images = images * (num_clips // len(images) + 1)
    selected_images = images[:num_clips]
    
    clip_dur = duration / num_clips
    print(f"  Creating {num_clips} image clips with duration {clip_dur:.2f}s each...")
    
    # 2. Build temporary panning clips
    temp_clips = []
    temp_dir = tempfile.gettempdir()
    
    for i, img_path in enumerate(selected_images):
        clip_path = os.path.join(temp_dir, f"temp_clip_{i}_{datetime.datetime.now().strftime('%M%S%f')}.mp4")
        success = make_panning_clip(img_path, clip_dur, clip_path)
        if success:
            temp_clips.append(clip_path)
        else:
            print(f"  Error: Failed to create panning clip for {img_path}")
            
    if not temp_clips:
        raise RuntimeError("Failed to create any panning image clips.")
        
    # 3. Concatenate the clips
    concat_txt_path = os.path.join(temp_dir, f"concat_list_{datetime.datetime.now().strftime('%M%S%f')}.txt")
    with open(concat_txt_path, 'w', encoding='utf-8') as f:
        for c in temp_clips:
            # Escape single quotes and backslashes for FFmpeg concat demuxer
            safe_c = c.replace("'", "'\\''").replace("\\", "/")
            f.write(f"file '{safe_c}'\n")
            
    merged_video_path = os.path.join(temp_dir, f"merged_slideshow_{datetime.datetime.now().strftime('%M%S%f')}.mp4")
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt_path,
        "-c", "copy",
        merged_video_path
    ]
    
    print("  Concatenating image clips...")
    res = subprocess.run(concat_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg concatenation failed:\n{res.stderr}")
        
    # Clean up temporary individual clips and list file
    try:
        os.remove(concat_txt_path)
        for c in temp_clips:
            os.remove(c)
    except:
        pass
        
    # 4. Generate subtitles
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output.close()
    
    ass_path = generate_whisper_ass(audio_path)
    if not ass_path:
        caption_text = script if script.strip() else title
        ass_path = generate_estimated_ass(caption_text, duration)
        
    # 5. Check background music
    music_file = os.path.join(REPO_ROOT, "music", "background_music.ogg")
    has_music = os.path.exists(music_file)
    
    escaped_ass = ass_path.replace('\\', '/').replace(':', '\\:')
    vf = f"subtitles='{escaped_ass}'"
    
    PRESET = "medium"
    CRF = "18"
    
    if has_music:
        print(f"  Mixing background music under narration...")
        cmd = [
            "ffmpeg", "-y",
            "-i", merged_video_path,
            "-i", audio_path,
            "-stream_loop", "-1", "-i", music_file,
            "-filter_complex", "[1:a]volume=1.2[v1];[2:a]volume=0.18[v2];[v1][v2]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-vf", vf,
            "-c:v", "libx264", "-preset", PRESET, "-crf", CRF,
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "[a]",
            "-t", f"{duration:.3f}",
            output.name
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", merged_video_path,
            "-i", audio_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", PRESET, "-crf", CRF,
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-t", f"{duration:.3f}",
            output.name
        ]
        
    print("  Rendering final video with audio mix and burned-in captions...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Clean up merged video file
    try:
        os.remove(merged_video_path)
    except:
        pass
        
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg rendering failed:\n{result.stderr}")
        
    size_mb = Path(output.name).stat().st_size / (1024 * 1024)
    print(f"  Video built successfully: {size_mb:.1f} MB")
    return output.name
