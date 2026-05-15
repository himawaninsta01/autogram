# content_engine.py — v2 (Groq API)
# Refactor: ollama.chat() → groq.chat.completions.create()

import os
import yaml
from pathlib import Path
from groq import Groq

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_client() -> Groq:
    """Inisialisasi Groq client dari env variable."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan di environment. Cek file .env")
    return Groq(api_key=api_key)

def _chat(client: Groq, model: str, prompt: str) -> str:
    """Helper: kirim satu prompt, return text response."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1024,
    )
    return response.choices[0].message.content.strip()

def generate_content_brief(niche: str, topic: str, config: dict, client: Groq) -> str:
    """Buat content brief dari niche dan topik terpilih."""
    model = config["content"]["llm_model"]
    lang = config["content"]["language"]
    lang_instruction = (
        "Gunakan Bahasa Indonesia yang natural dan engaging."
        if lang == "id" else
        "Use natural and engaging English."
    )

    prompt = f"""Kamu adalah social media strategist profesional.
Buat content brief singkat untuk postingan Instagram tentang:
- Niche: {niche}
- Topik spesifik: {topic}

{lang_instruction}

Output dalam format:
ANGLE: [sudut pandang konten]
TONE: [tone of voice]
KEY_MESSAGE: [pesan utama dalam 1 kalimat]
TARGET: [target audiens]
CTA: [call to action]

Singkat dan langsung ke poin."""

    print(f"📝 Membuat content brief untuk '{topic}'...")
    return _chat(client, model, prompt)

def generate_caption(brief: str, niche: str, topic: str, config: dict, client: Groq) -> str:
    """Generate caption Instagram dari content brief."""
    model = config["content"]["llm_model"]
    max_chars = config["content"]["caption_max_chars"]
    lang = config["content"]["language"]
    lang_instruction = (
        "Tulis dalam Bahasa Indonesia yang natural, bukan terjemahan kaku."
        if lang == "id" else
        "Write in natural English."
    )

    prompt = f"""Kamu adalah copywriter Instagram profesional.
Buat caption Instagram berdasarkan brief ini:

{brief}

Topik: {topic}
Niche: {niche}

{lang_instruction}

ATURAN:
- Baris pertama harus berupa hook yang menarik perhatian (maksimal 125 karakter)
- Body 3-4 baris yang informatif atau menghibur
- Akhiri dengan CTA yang jelas
- Maksimal {max_chars} karakter total
- Jangan gunakan emoji berlebihan (maksimal 5)
- Jangan sertakan hashtag (akan ditambahkan terpisah)

Tulis HANYA caption-nya saja, tanpa penjelasan tambahan."""

    print(f"✍️  Generating caption...")
    return _chat(client, model, prompt)

def generate_hashtags(niche: str, topic: str, config: dict, client: Groq) -> list:
    """Generate hashtag yang relevan."""
    model = config["content"]["llm_model"]
    count = config["content"]["hashtag_count"]

    prompt = f"""Buat {count} hashtag Instagram untuk konten tentang:
- Niche: {niche}
- Topik: {topic}
- Target: Indonesia

Campurkan:
- 5 hashtag sangat populer (jutaan post)
- 10 hashtag medium (ratusan ribu post)
- 5 hashtag niche spesifik (puluhan ribu post)

Format output: hanya daftar hashtag dipisah spasi, dimulai dengan #
Contoh: #ai #teknologi #belajar ...

Tulis HANYA hashtag-nya saja."""

    print(f"#️⃣  Generating hashtags...")
    raw = _chat(client, model, prompt)
    hashtags = [tag.strip() for tag in raw.split() if tag.startswith("#")]
    return hashtags[:count]

def generate_image_prompt(niche: str, topic: str, brief: str, config: dict, client: Groq) -> str:
    """Generate prompt untuk image generation (Pollinations.ai)."""
    model = config["content"]["llm_model"]
    style = config["image"]["style_map"].get(niche, "digital art, clean aesthetic")

    prompt = f"""Buat image prompt untuk AI image generator berdasarkan:
- Topik: {topic}
- Style: {style}
- Brief: {brief}

ATURAN prompt:
- Bahasa Inggris
- Deskriptif dan visual
- Sertakan style, lighting, composition
- Cocok untuk Instagram square (1:1)
- Tidak ada teks atau tulisan dalam gambar
- Maksimal 100 kata

Tulis HANYA prompt-nya saja."""

    print(f"🎨 Generating image prompt...")
    return _chat(client, model, prompt)

def run_content_engine(niche: str, topic: str) -> dict:
    """Jalankan full content generation pipeline."""
    config = load_config()
    client = get_client()

    print(f"\n🚀 Content Engine dimulai (Groq API)")
    print(f"   Niche: {niche} | Topik: {topic}")
    print(f"   Model: {config['content']['llm_model']}\n")

    brief        = generate_content_brief(niche, topic, config, client)
    print(f"\n📋 Brief:\n{brief}\n")

    caption      = generate_caption(brief, niche, topic, config, client)
    print(f"\n📱 Caption:\n{caption}\n")

    hashtags     = generate_hashtags(niche, topic, config, client)
    print(f"\n🏷️  Hashtags ({len(hashtags)}): {' '.join(hashtags[:5])}...")

    image_prompt = generate_image_prompt(niche, topic, brief, config, client)
    print(f"\n🖼️  Image Prompt:\n{image_prompt}\n")

    return {
        "niche": niche,
        "topic": topic,
        "brief": brief,
        "caption": caption,
        "hashtags": hashtags,
        "image_prompt": image_prompt,
    }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = run_content_engine("AI", "gemini ai")
    print("\n" + "="*50)
    print("✅ Content Engine selesai!")
    print(f"Caption length: {len(result['caption'])} karakter")
    print(f"Hashtags: {len(result['hashtags'])} tag")