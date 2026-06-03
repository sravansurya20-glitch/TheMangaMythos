import os
import tempfile
import requests
import datetime

ELEVENLABS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

VOICES = [
    "vGQNBgLaiM3EdZtxIiuY",  # Alternating Voice A (e.g. Male)
    "JjsQrIrIBD6TZ656NQfi"   # Alternating Voice B (e.g. Female)
]

VOICE_SETTINGS = {
    "stability": 0.35,
    "similarity_boost": 0.85,
    "style": 0.55,
    "use_speaker_boost": True
}

import re

def strip_emojis(text: str) -> str:
    # Match emoji characters in the unicode range
    return re.sub(r'[\U00010000-\U0010ffff]', '', text)

def generate_voiceover(script: str) -> str:
    api_key = os.environ["ELEVENLABS_API_KEY"]
    
    # Alternate daily based on calendar date ordinal
    day_number = datetime.date.today().toordinal()
    voice_id = VOICES[day_number % len(VOICES)]

    clean_script = strip_emojis(script)
    url = ELEVENLABS_URL.format(voice_id=voice_id)

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    payload = {
        "text": clean_script,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": VOICE_SETTINGS
    }

    print(f"  Generating voice with ElevenLabs (Voice ID: {voice_id})...")
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        stream=True,
        timeout=120
    )

    if response.status_code == 200:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                tmp.write(chunk)
        tmp.close()
        print("  Adam voice saved!")
        return tmp.name
    else:
        print(f"  ElevenLabs failed ({response.status_code}), using gTTS...")
        return use_gtts(script)

def use_gtts(script: str) -> str:
    from gtts import gTTS
    clean_script = strip_emojis(script)
    tts = gTTS(text=clean_script, lang='en', slow=False)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    print("  gTTS voice saved")
    return tmp.name
