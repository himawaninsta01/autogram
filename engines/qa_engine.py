# qa_engine.py — v2 (Groq API)
# Refactor: ollama.chat() → groq.chat.completions.create()
# Model: qwen2.5-coder:14b → mixtral-8x7b-32768

import os
import json
import yaml
from pathlib import Path
from PIL import Image
from groq import Groq

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY tidak ditemukan di environment.")
    return Groq(api_key=api_key)

BANNED_WORDS = [
    "judi", "slot", "togel", "porno", "bokep", "viagra",
    "hack", "crack", "illegal", "narkoba", "weapons"
]

def check_banned_words(text: str) -> list:
    found = []
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            found.append(word)
    return found

def check_image(image_path: str) -> dict:
    """Cek kualitas gambar dasar."""
    try:
        img = Image.open(image_path)
        width, height = img.size
        size_ok  = width >= 1000 and height >= 1000
        ratio    = width / height
        ratio_ok = 0.9 <= ratio <= 1.1
        return {
            "ok": size_ok and ratio_ok,
            "size": f"{width}x{height}",
            "ratio": f"{ratio:.2f}",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def score_content(
    niche: str, topic: str, caption: str,
    hashtags: list, image_prompt: str,
    config: dict, client: Groq
) -> dict:
    """AI scoring konten via Groq (mixtral-8x7b-32768)."""

    # QA pakai model yang lebih kuat dari content engine
    model     = config["content"].get("qa_model", "mixtral-8x7b-32768")
    threshold = config["content"]["qa_threshold"]

    prompt = f"""Kamu adalah quality checker konten Instagram profesional.
Evaluasi konten berikut dan beri skor 0-10 untuk setiap aspek:

NICHE: {niche}
TOPIK: {topic}

CAPTION:
{caption}

HASHTAGS ({len(hashtags)} tag):
{' '.join(hashtags[:10])}

IMAGE PROMPT:
{image_prompt[:200]}

Berikan evaluasi dalam format PERSIS ini (ganti angka dengan skor 0-10):
RELEVANCE: [skor] | Relevansi caption dengan topik
QUALITY: [skor] | Kualitas penulisan caption
HASHTAG: [skor] | Relevansi dan variasi hashtag
VISUAL: [skor] | Kesesuaian image prompt dengan konten
OVERALL: [skor] | Skor keseluruhan
VERDICT: PASS atau FAIL
REASON: [alasan singkat dalam 1 kalimat]"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,   # rendah agar konsisten
        max_tokens=512,
    )
    raw = response.choices[0].message.content.strip()

    # Parse hasil
    scores = {}
    for line in raw.split("\n"):
        for key in ["RELEVANCE", "QUALITY", "HASHTAG", "VISUAL", "OVERALL"]:
            if line.startswith(key):
                try:
                    val = line.split(":")[1].split("|")[0].strip()
                    scores[key.lower()] = float(val)
                except:
                    scores[key.lower()] = 0.0
        if line.startswith("VERDICT"):
            scores["verdict"] = "PASS" if "PASS" in line.upper() else "FAIL"
        if line.startswith("REASON"):
            scores["reason"] = line.split(":", 1)[1].strip() if ":" in line else ""

    overall = scores.get("overall", 0.0)
    passed  = overall >= threshold and scores.get("verdict") == "PASS"

    return {
        "scores": scores,
        "overall": overall,
        "passed": passed,
        "threshold": threshold,
        "raw_response": raw,
    }

def run_qa(
    niche: str, topic: str, caption: str,
    hashtags: list, image_prompt: str, image_path: str
) -> dict:
    """Jalankan full QA check."""
    config = load_config()
    client = get_client()

    print(f"\n🔍 QA Engine dimulai (Groq · mixtral-8x7b-32768)...")

    # 1. Banned words
    banned = check_banned_words(caption)
    if banned:
        print(f"❌ Banned words ditemukan: {banned}")
        return {"passed": False, "reason": f"Banned words: {banned}", "overall": 0}
    print(f"✅ Banned words: bersih")

    # 2. Image check
    img_check = check_image(image_path)
    if not img_check.get("ok"):
        print(f"⚠️  Image check: {img_check}")
    else:
        print(f"✅ Image check: {img_check['size']} ratio {img_check['ratio']}")

    # 3. AI scoring
    print(f"🤖 AI scoring konten...")
    result = score_content(niche, topic, caption, hashtags, image_prompt, config, client)

    scores = result["scores"]
    print(f"\n📊 Hasil QA:")
    print(f"   Relevance : {scores.get('relevance', 0):.1f}/10")
    print(f"   Quality   : {scores.get('quality', 0):.1f}/10")
    print(f"   Hashtag   : {scores.get('hashtag', 0):.1f}/10")
    print(f"   Visual    : {scores.get('visual', 0):.1f}/10")
    print(f"   ─────────────────")
    print(f"   Overall   : {result['overall']:.1f}/10  (threshold: {result['threshold']})")
    print(f"   Verdict   : {'✅ PASS' if result['passed'] else '❌ FAIL'}")
    print(f"   Reason    : {scores.get('reason', '-')}")

    return result

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    test_caption = """Gemini AI hadir mengubah cara kita bekerja! 🚀

Model AI terbaru dari Google ini mampu memahami teks, gambar, dan kode sekaligus.
Produktivitas kamu bisa naik 3x lipat dengan tools yang tepat.

Coba sekarang dan rasakan perbedaannya!"""

    test_hashtags = ["#AI", "#GeminiAI", "#TeknologiIndonesia",
                     "#MachineLearning", "#Produktivitas"]
    test_prompt = "neural network visualization, futuristic lab, glowing circuits"
    test_image  = "data/images/test.png"

    result = run_qa("AI", "gemini ai", test_caption,
                    test_hashtags, test_prompt, test_image)
    print(f"\n🎯 QA {'LOLOS' if result['passed'] else 'GAGAL'}")