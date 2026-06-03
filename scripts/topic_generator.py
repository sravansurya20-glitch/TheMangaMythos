import os
import json
import datetime
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Each entry is: (hook_title, search_keyword, anime_series_id)
VIRAL_HOOKS = [
    # One Piece
    ("What if Shanks is secretly working for the World Government?", "shanks gorosei theory", "one_piece"),
    ("Why Zoro's closed eye has a demonic secret.", "zoro ashura sharingan", "one_piece"),
    ("Luffy's Gear 5 is NOT what you think it is.", "gear 5 joy boy nika", "one_piece"),
    ("Is Blackbeard actually three people in one body?", "blackbeard three souls", "one_piece"),
    ("The real reason Gol D. Roger laughed at Laugh Tale.", "roger laughed one piece", "one_piece"),
    ("Why Imu is actually Luffy's mother.", "imu luffy mother", "one_piece"),
    ("Is Joy Boy actually a giant in One Piece?", "joy boy giant skull", "one_piece"),
    ("Why Akainu is secretly plotting to overthrow the Gorosei.", "akainu fleet admiral anger", "one_piece"),
    ("The connection between Sun God Nika and the Ancient Weapons.", "nika ancient weapons poseidon", "one_piece"),
    
    # Solo Leveling
    ("How Sung Jinwoo actually became the Shadow Monarch.", "sung jinwoo ashborn monarch", "solo_leveling"),
    ("What if the Monarch of Destruction won?", "monarch destruction dragonant", "solo_leveling"),
    ("The dark origin of the System in Solo Leveling.", "architect system jinwoo", "solo_leveling"),
    ("Why Sung Jinwoo's dad had to die.", "sung il hwan death shadow", "solo_leveling"),
    ("The secret of the Double Dungeon in Solo Leveling.", "double dungeon stone statue", "solo_leveling"),
    ("What if Sung Jinwoo lost his shadow powers?", "jinwoo weak hunter E-rank", "solo_leveling"),
    ("Why the Rulers are actually the bad guys in Solo Leveling.", "rulers absolute being fragment", "solo_leveling"),
    
    # Bleach
    ("What if Ichigo's Zanpakuto was actually Yhwach all along?", "old man zangetsu yhwach", "bleach"),
    ("Why Aizen's Bankai was never shown in Bleach.", "aizen bankai kyoka suigetsu", "bleach"),
    ("Is Kisuke Urahara the true final villain of Bleach?", "kisuke urahara shady look", "bleach"),
    ("Why Ichigo is the most overpowered anime protagonist.", "ichigo hollow quincy shinigami", "bleach"),
    ("The secret connection between Ichigo and the Soul King.", "ichigo soul king replacement", "bleach"),
    ("What if Aizen planned Ichigo's entire life?", "aizen glasses smirk mastermind", "bleach"),
    ("Why Yhwach's Almighty is the most broken anime ability.", "yhwach almighty eyes pupils", "bleach"),
]

def generate_topic_and_script(niche: str) -> dict:
    today = datetime.date.today().strftime("%B %d, %Y")
    day_number = datetime.date.today().toordinal()
    
    # Select hook based on the day of the year
    hook, keyword, anime_series = VIRAL_HOOKS[day_number % len(VIRAL_HOOKS)]

    prompt = f"""You are the world's leading Anime Theory content creator, famous for wild, mind-bending, and controversial theories that spark massive debates in the comments.
Your goal is to write a viral YouTube Short script.

Today: {today}
Topic: {hook}
Anime Series Focus: {anime_series.upper()} (Make sure the script is entirely focused on this specific anime!)

STORY REQUIREMENTS:
1. Start with the HOOK exactly.
2. Structure: 
   - Hook (immediate attention-grabbing statement, say it with complete conviction!)
   - The "Meat" (Explain the wild theory. Make it sound incredibly logical even if it's completely fake/insane! Build up fake evidence or clues.)
   - The Twist/Insight (Why this changes everything we know about the series. "If this is true, then...")
   - Call to Action / Engagement Prompt (Prompt viewers to debate in the comments. E.g. "But what do you think? Did Shanks betray Luffy, or is he playing the long game? Let me know in the comments and subscribe for more wild anime theories! 🔔")
3. TONE: High energy, fast-paced, theatrical, debate-provoking.
4. LENGTH: 70-85 words (Perfect for a 30-40 second Short).
5. EMOJIS: Generously include relevant, high-impact emojis throughout the script (e.g., 🏴‍☠️, 🦊, ⚔️, 👿, 🤯, 💀, 👁️) to make captions visually pop!

SCRIPT STYLE:
- Use second person ("You", "Did you know...", "What if...")
- Short, punchy sentences (maximum 12 words per sentence).
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
