# content_engine.py — v4.0 (Cloud & Format Rotation)
import os
import yaml
import json
import random
from pathlib import Path
from groq import Groq

sys_path = Path(__file__).parent.parent
CONFIG_PATH = sys_path / "config.yaml"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan di environment.")
    return Groq(api_key=api_key)

def _chat(client: Groq, model: str, prompt: str, max_tokens: int = 3000) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()

def get_recent_topics(limit=30) -> list:
    """Mengambil memori topik agar AI tidak mengulang pembahasan."""
    try:
        from core.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT topic FROM posts WHERE status != 'failed' ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [row["topic"] for row in rows]
    except Exception as e:
        print(f"Warning: Could not fetch recent topics: {e}")
        return []

def run_content_engine(niche: str, topic: str) -> dict:
    """Jalankan content generation pipeline v4."""
    config = load_config()
    client = get_client()
    model = config["content"]["llm_model"]

    # 1. Topic Memory (Anti-Repetition)
    recent_topics = get_recent_topics()
    memory_prompt = ""
    if recent_topics:
        memory_prompt = "\nPENTING: HINDARI membahas secara persis topik-topik berikut yang sudah pernah diposting:\n- " + "\n- ".join(recent_topics) + "\nCari sudut pandang/angle baru yang belum pernah dibahas."

    # 2. Format Rotation
    # 50% Single, 30% Carousel, 20% Thematic
    rand = random.random()
    if rand < 0.5:
        post_format = "single"
        format_desc = "Single Post (1 Post, 1 Gambar Utama)"
    elif rand < 0.8:
        post_format = "carousel"
        format_desc = "Carousel Post (1 Post, 3-5 Slide Gambar swipe-able yang mendalam)"
    else:
        post_format = "thematic"
        format_desc = "Thematic Campaign (3 Postingan terpisah yang bersambung, untuk diposting selama 3 hari berturut-turut. Part 1, Part 2, dan Part 3)"

    print(f"\n🚀 Content Engine v4 (Cloud & Format Rotation)")
    print(f"   Niche   : {niche}")
    print(f"   Topik   : {topic}")
    print(f"   Format  : {post_format.upper()}")
    print(f"   Memori  : {len(recent_topics)} topik dihindari")

    prompt = f"""Kamu adalah Social Media Manager dan Expert Copywriter. Buat konten Instagram berkualitas tinggi untuk niche '{niche}' dengan topik: '{topic}'.
{memory_prompt}

FORMAT KONTEN: {format_desc}

Tugas Anda adalah menghasilkan JSON berisi data postingan.
PENTING: Output HANYA JSON array of objects murni, tanpa backticks, tanpa penjelasan tambahan.

Bentuk JSON-nya harus berupa array of objects (meskipun hanya 1 post jika format Single/Carousel):
[
  {{
    "caption": "Caption Instagram yang memikat, gunakan newline, emoji, bahasa profesional tapi asik, dan pancing interaksi. Max 3-4 paragraf. Jika format thematic, pastikan ada 'Bersambung ke part...' atau 'Lanjutan dari part...'",
    "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"],
    "image_prompt": "Prompt gambar dalam Bahasa Inggris untuk AI Image Generator. Harus sangat deskriptif, sinematik, aesthetic, menyebutkan elemen utama.",
    "slide_count": {"1 jika single/thematic, 4 jika carousel"},
    "campaign_part": {"1, 2, atau 3 jika thematic. 1 jika bukan thematic"}
  }}
]
"""
    print("🧠 Generating content via LLM...")
    raw = _chat(client, model, prompt)
    
    # Parse JSON
    import re
    raw = re.sub(r'^```[a-z]*\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())

    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            data = [data]
    except Exception as e:
        print(f"⚠️ JSON parse error: {e}. Fallback ke single post sederhana.")
        data = [{
            "caption": f"Membahas {topic} untuk {niche}. Simak tips terbarunya! ✨\n\n#tips #info",
            "hashtags": ["#info", "#tips", "#terbaru"],
            "image_prompt": f"High quality aesthetic photo about {topic}, {niche} style, cinematic lighting",
            "slide_count": 1,
            "campaign_part": 1
        }]

    print(f"✅ Content generated! ({len(data)} post data)")
    return {
        "niche": niche,
        "topic": topic,
        "post_format": post_format,
        "posts_data": data
    }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = run_content_engine("AI", "menulis email profesional")
    print(json.dumps(result, indent=2))