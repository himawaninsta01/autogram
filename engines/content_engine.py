# content_engine.py — v3.0 (Prompt Breakdown + Real Result)
# Konten fokus: tampilkan prompt nyata + breakdown per bagian + output AI

import os
import yaml
import random
from pathlib import Path
from groq import Groq

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

# Rotasi AI tools — bergantian tiap post
AI_TOOLS = [
    {"name": "Claude",      "maker": "Anthropic",  "emoji": "🟠", "url": "claude.ai"},
    {"name": "ChatGPT",     "maker": "OpenAI",     "emoji": "🟢", "url": "chatgpt.com"},
    {"name": "Gemini",      "maker": "Google",     "emoji": "🔵", "url": "gemini.google.com"},
    {"name": "Perplexity",  "maker": "Perplexity", "emoji": "🟣", "url": "perplexity.ai"},
    {"name": "Copilot",     "maker": "Microsoft",  "emoji": "⚪", "url": "copilot.microsoft.com"},
]

# Kategori use case konkret
USE_CASES = [
    "meringkas dokumen panjang",
    "menulis email profesional",
    "debugging kode",
    "riset topik cepat",
    "membuat konten media sosial",
    "analisis data bisnis",
    "menulis proposal",
    "brainstorming ide",
    "menerjemahkan dokumen teknis",
    "membuat presentasi",
    "review dan perbaikan tulisan",
    "membuat rencana proyek",
]

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan di environment.")
    return Groq(api_key=api_key)

def _chat(client: Groq, model: str, prompt: str, max_tokens: int = 1500) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()

def pick_ai_tool(topic: str) -> dict:
    """Pilih AI tool secara semi-random berdasarkan hash topik (konsisten per topik)."""
    idx = hash(topic) % len(AI_TOOLS)
    return AI_TOOLS[idx]

def pick_use_case(topic: str) -> str:
    """Pilih use case berdasarkan topik."""
    idx = hash(topic + "uc") % len(USE_CASES)
    return USE_CASES[idx]

def generate_prompt_breakdown(niche: str, topic: str, ai_tool: dict,
                               use_case: str, config: dict, client: Groq) -> dict:
    """
    Generate konten utama: prompt nyata + output + breakdown per bagian.
    Return dict dengan semua komponen.
    """
    model = config["content"]["llm_model"]

    prompt = f"""Kamu adalah expert prompt engineer yang membuat konten edukasi Instagram.

Buat konten tentang cara menggunakan {ai_tool['name']} untuk: {use_case}
Topik spesifik: {topic}

Generate dalam format JSON berikut (HANYA JSON, tanpa penjelasan, tanpa markdown):

{{
  "judul": "judul hook menarik max 8 kata, pakai angka/fakta spesifik",
  "hook": "kalimat pembuka caption yang mengejutkan, max 120 karakter",
  "ai_tool": "{ai_tool['name']}",
  "use_case": "{use_case}",
  "prompt_lengkap": "prompt nyata yang bisa langsung dicopy-paste ke {ai_tool['name']}, 50-120 kata, dalam Bahasa Indonesia, sangat spesifik dan actionable",
  "output_preview": "contoh output singkat dari {ai_tool['name']} jika prompt di atas dijalankan, 3-5 kalimat, terkesan nyata dan berguna",
  "breakdown": [
    {{
      "bagian": "kutipan singkat bagian pertama dari prompt (max 6 kata)",
      "penjelasan": "kenapa bagian ini penting dan efeknya ke output, 1-2 kalimat"
    }},
    {{
      "bagian": "kutipan singkat bagian kedua dari prompt (max 6 kata)",
      "penjelasan": "kenapa bagian ini penting dan efeknya ke output, 1-2 kalimat"
    }},
    {{
      "bagian": "kutipan singkat bagian ketiga dari prompt (max 6 kata)",
      "penjelasan": "kenapa bagian ini penting dan efeknya ke output, 1-2 kalimat"
    }}
  ],
  "caption_body": "body caption Instagram 3-4 baris, informatif, dalam Bahasa Indonesia",
  "cta": "call to action spesifik yang mendorong save/coba, max 80 karakter",
  "judul_gambar": "judul singkat max 5 kata untuk slide cover, HURUF KAPITAL",
  "poin_gambar": ["poin 1 singkat", "poin 2 singkat", "poin 3 singkat"]
}}

PENTING: Output HANYA JSON valid, tidak ada teks lain."""

    print(f"🧠 Generating prompt breakdown untuk {ai_tool['name']}...")
    raw = _chat(client, model, prompt, max_tokens=2000)

    # Parse JSON
    import json, re
    # Bersihkan jika ada markdown fence
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'\s*```$', '', raw.strip())

    try:
        data = json.loads(raw)
        return data
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON parse error: {e}, pakai fallback...")
        return {
            "judul": f"Prompt {ai_tool['name']} untuk {use_case}",
            "hook": f"Prompt ini mengubah cara kamu {use_case} dengan {ai_tool['name']} 🔥",
            "ai_tool": ai_tool["name"],
            "use_case": use_case,
            "prompt_lengkap": f"Tolong bantu saya {use_case} tentang {topic}. Berikan hasil yang terstruktur, konkret, dan langsung bisa digunakan.",
            "output_preview": f"Berikut hasil {ai_tool['name']} untuk {use_case}...",
            "breakdown": [
                {"bagian": "Tolong bantu saya", "penjelasan": "Instruksi langsung membuat AI lebih fokus."},
                {"bagian": "terstruktur dan konkret", "penjelasan": "Kata kunci kualitas output yang diinginkan."},
                {"bagian": "langsung bisa digunakan", "penjelasan": "Menghindari output yang terlalu teoritis."},
            ],
            "caption_body": f"Gunakan prompt ini untuk {use_case} dengan {ai_tool['name']}.",
            "cta": "Save prompt ini sebelum lupa! 💾",
            "judul_gambar": f"PROMPT {ai_tool['name'].upper()}",
            "poin_gambar": [use_case, "Copy-paste ready", "Hasil terbukti"],
        }

def generate_hashtags(niche: str, topic: str, ai_tool: str,
                      config: dict, client: Groq) -> list:
    model = config["content"]["llm_model"]
    count = config["content"]["hashtag_count"]

    prompt = f"""Buat {count} hashtag Instagram untuk konten tips prompt {ai_tool} tentang {topic}.
Target: Indonesia. Campurkan populer, medium, dan niche.
Format: hanya hashtag dipisah spasi, dimulai #. Tulis HANYA hashtag."""

    raw = _chat(client, model, prompt, max_tokens=300)
    hashtags = [t.strip() for t in raw.split() if t.startswith("#")]
    return hashtags[:count]

def run_content_engine(niche: str, topic: str) -> dict:
    """Jalankan full content generation pipeline v3."""
    config  = load_config()
    client  = get_client()
    model   = config["content"]["llm_model"]

    ai_tool  = pick_ai_tool(topic)
    use_case = pick_use_case(topic)

    print(f"\n🚀 Content Engine v3 (Prompt Breakdown)")
    print(f"   Niche   : {niche}")
    print(f"   Topik   : {topic}")
    print(f"   AI Tool : {ai_tool['name']} {ai_tool['emoji']}")
    print(f"   Use Case: {use_case}")
    print(f"   Model   : {model}\n")

    # Generate konten utama
    data = generate_prompt_breakdown(niche, topic, ai_tool, use_case, config, client)

    # Generate hashtags
    hashtags = generate_hashtags(niche, topic, ai_tool["name"], config, client)

    # Susun caption lengkap
    caption = (
        f"{data['hook']}\n\n"
        f"{data['caption_body']}\n\n"
        f"🔧 Tool: {ai_tool['emoji']} {ai_tool['name']} ({ai_tool['url']})\n\n"
        f"{data['cta']}"
    )

    # Susun brief untuk visual engine
    brief = (
        f"JUDUL_GAMBAR: {data['judul_gambar']}\n"
        f"POIN_GAMBAR: {', '.join(data['poin_gambar'])}\n"
        f"AI_TOOL: {ai_tool['name']}\n"
        f"PROMPT: {data['prompt_lengkap']}\n"
        f"OUTPUT: {data['output_preview']}\n"
        f"BREAKDOWN_1: {data['breakdown'][0]['bagian']} | {data['breakdown'][0]['penjelasan']}\n"
        f"BREAKDOWN_2: {data['breakdown'][1]['bagian']} | {data['breakdown'][1]['penjelasan']}\n"
        f"BREAKDOWN_3: {data['breakdown'][2]['bagian']} | {data['breakdown'][2]['penjelasan']}\n"
    )

    print(f"✅ Content generated!")
    print(f"   Judul   : {data['judul']}")
    print(f"   Prompt  : {data['prompt_lengkap'][:60]}...")

    return {
        "niche":        niche,
        "topic":        topic,
        "brief":        brief,
        "caption":      caption,
        "hashtags":     hashtags,
        "image_prompt": f"dark tech background, {ai_tool['name']} AI interface, {niche} aesthetic, abstract glow",
        "ai_tool":      ai_tool,
        "use_case":     use_case,
        "prompt_data":  data,
        "trend_score":  0,
    }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    result = run_content_engine("AI", "menulis email profesional")
    print("\n" + "="*50)
    print("✅ Content Engine v3 selesai!")
    print(f"Caption:\n{result['caption']}")
    print(f"\nBrief:\n{result['brief']}")