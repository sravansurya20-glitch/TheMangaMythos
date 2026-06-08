import os
import json
import datetime
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Each entry is: (hook_title, search_keyword, anime_series_id)
VIRAL_HOOKS = [
    # Black Clover (TEST)
    ("Asta's demon Liebe is actually the child of a god.", "asta liebe devil theory", "black_clover"),
]

import random

HISTORY_FILE = r"C:\Users\srava\.gemini\antigravity\scratch\anime_used_hooks.json"

def generate_topic_and_script(niche: str) -> dict:
    today = datetime.date.today().strftime("%B %d, %Y")
    
    # Load recently used hooks from persistent file
    used_hooks = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                used_hooks = json.load(f)
        except:
            pass
            
    # Filter out recently used hooks
    available = [h for h in VIRAL_HOOKS if h[0] not in used_hooks]
    if not available:
        available = VIRAL_HOOKS
        used_hooks = []
        
    selected = random.choice(available)
    hook, keyword, anime_series = selected
    
    # Save selection to history (keep last 10 to prevent short-term repeats)
    used_hooks.append(hook)
    if len(used_hooks) > 10:
        used_hooks = used_hooks[-10:]
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(used_hooks, f)
    except:
        pass

    prompt = f"""You are the world's leading Anime Theory content creator, famous for wild, mind-bending, and controversial theories. Your videos feel authentic, personal, and conversational—never robotic or AI-generated.
Your goal is to write a viral YouTube Short script.

Today: {today}
Topic: {hook}
Anime Series Focus: {anime_series.upper()} (Make sure the script is entirely focused on this specific anime!)

STORY REQUIREMENTS:
1. Start with a SCROLL-STOPPING HOOK: A controversial, high-energy statement or shocking question that makes it impossible to swipe away.
2. Structure: 
   - Refined Hook (1-2 sentences. Speak with extreme conviction!)
   - The Proof (Build up specific, logical evidence or clues from the manga/lore. Explain it simply but passionately.)
   - The Big Twist (Why this changes everything: "If this is true, then...")
   - Theory Score & CTA: Grade the theory out of 10 and prompt a comment debate. (E.g. "I give this theory a solid 9 out of 10. What's your score? Let me know in the comments and subscribe for more wild anime theories! 🔔")
3. TONE: High energy, fast-paced, personal, debate-provoking, authentic.
4. LENGTH: 70-85 words (Perfect for a 30-40 second Short).
5. EMOJIS: Generously include relevant, high-impact emojis throughout the script (e.g., 🏴‍☠️, 🦊, ⚔️, 👿, 🤯, 💀, 👁️) to make captions visually pop!

SCRIPT STYLE (TO AVOID "AI" FEEL):
- Never use generic intros like "Welcome back", "In this video", or "Have you ever wondered".
- Speak like a real passionate fan talking to their friend: use conversational fillers like "Wait...", "Think about it...", "Let that sink in...", "Here's the crazy part..."
- Short, punchy sentences (maximum 10 words per sentence).
- NO stage directions or [Music] tags.
- Focus on "Hyped Narrator" style storytelling.

Return ONLY valid JSON:
{{
  "title": "{hook[:45]}...",
  "keyword": "{keyword}",
  "anime_series": "{anime_series}",
  "script": "70-85 word high-energy viral script with rich, relevant emojis included in the text",
  "description": "{hook} 🤯🔥 #AnimeTheory #Anime #Manga #Shorts #Trending #{anime_series.replace('_', '')}",
  "tags": ["anime", "manga", "anime theory", "shorts", "trending", "{anime_series.replace('_', '')}", "what if", "theory"]
}}"""

    # Models to try in order
    models_to_try = [
        "claude-opus-4-7", # The custom/proxy model name that is active in this account
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            print(f"  Attempting script generation with {model_name}...")
            message = client.messages.create(
                model=model_name,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = message.content[0].text.strip()
            
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()

            data = json.loads(raw)
            # Ensure the anime_series is saved
            data["anime_series"] = anime_series
            print(f"  Success with {model_name}!")
            
            word_count = len(data["script"].split())
            print(f"  Script word count: {word_count}")
            print(f"  Topic: {hook}")
            return data
            
        except Exception as e:
            last_error = e
            if "404" in str(e):
                continue
            else:
                break
    
    raise last_error
