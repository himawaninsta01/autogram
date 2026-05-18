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

    prompt = f"""Kamu adalah social media strategist profesional yang spesialis konten tips & trik AI tools.

Buat content brief untuk postingan Instagram yang SANGAT SPESIFIK tentang:
- Niche: {niche}
- Topik: {topic}

PENTING: Konten harus berupa tips/trik KONKRET dan ACTIONABLE, bukan penjelasan umum.
Contoh yang BAIK: "3 prompt Claude yang bikin ringkasan meeting jadi 10x lebih cepat"
Contoh yang BURUK: "Manfaat AI untuk produktivitas"

{lang_instruction}

Output dalam format:
ANGLE: [sudut pandang spesifik — harus berupa tips/trik/hack konkret]
TONE: [conversational, helpful, insider knowledge]
KEY_MESSAGE: [1 tips konkret yang bisa langsung dicoba]
TARGET: [target audiens spesifik]
CTA: [ajakan untuk coba tips tersebut]
JUDUL_GAMBAR: [judul singkat max 5 kata untuk ditampilkan di gambar, huruf kapital]
POIN_GAMBAR: [3-5 poin singkat untuk ditampilkan sebagai list di gambar]"""

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

    prompt = f"""Kamu adalah copywriter Instagram profesional yang ahli konten tips AI tools.

Buat caption Instagram berdasarkan brief ini:
{brief}

Topik: {topic}
Niche: {niche}

{lang_instruction}

ATURAN:
- Hook baris pertama harus SPESIFIK dan mengejutkan, contoh:
  "Kamu buang 2 jam/hari karena salah pakai Claude 😬"
  "Ekstensi ini bikin ChatGPT-mu 3x lebih pintar (gratis)"
  "Prompt ini yang dipakai programmer senior di Silicon Valley"
- Body berisi 3-4 tips konkret yang bisa langsung dicoba
- Gunakan angka dan data spesifik bila memungkinkan
- Akhiri dengan CTA yang mendorong action nyata
- Maksimal {max_chars} karakter
- Emoji secukupnya (3-5), jangan berlebihan
- Jangan sertakan hashtag

Tulis HANYA caption-nya saja."""

    print(f"✍️  Generating caption...")
    return _chat(client, model, prompt)

def generate_hashtags(niche: str, topic: str, config: dict, client: Groq) -> list:
    """Generate hashtag yang relevan."""
    model = config["content"]["llm_model"]
    count = config["content"]["hashtag_count"]

    prompt = f"""Buat {count} hashtag Instagram untuk konten tips & trik tentang:
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
    """Generate prompt untuk infografis via Pollinations.ai."""
    model = config["content"]["llm_model"]

    # Ekstrak JUDUL dan POIN dari brief
    judul = ""
    poin = ""
    for line in brief.splitlines():
        if line.startswith("JUDUL_GAMBAR:"):
            judul = line.replace("JUDUL_GAMBAR:", "").strip()
        if line.startswith("POIN_GAMBAR:"):
            poin = line.replace("POIN_GAMBAR:", "").strip()

    prompt = f"""Buat image prompt untuk AI image generator yang menghasilkan INFOGRAFIS Instagram.

Topik: {topic}
Judul untuk gambar: {judul if judul else topic.upper()}
Poin konten: {poin if poin else "tips konkret, actionable"}

Buat prompt untuk gambar infografis yang:
- Berbentuk kartu info / cheat sheet bergaya modern
- Ada judul besar di bagian atas
- Ada 3-5 poin teks di badan gambar
- Warna gelap elegan (dark navy, dark purple, atau dark teal) dengan aksen neon
- Ada ikon atau elemen visual yang relevan
- Typography yang bersih dan mudah dibaca
- Gaya: modern UI design, infographic card, clean layout
- Square format 1:1 untuk Instagram

Tulis HANYA prompt bahasa Inggris-nya saja, maksimal 120 kata."""

    print(f"🎨 Generating image prompt (infografis)...")
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
    result = run_content_engine("AI", "tips claude ai")
    print("\n" + "="*50)
    print("✅ Content Engine selesai!")
    print(f"Caption length: {len(result['caption'])} karakter")
    print(f"Hashtags: {len(result['hashtags'])} tag")