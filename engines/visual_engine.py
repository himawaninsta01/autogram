# visual_engine.py — v2 (Pollinations.ai)
# Refactor: ComfyUI API → Pollinations.ai HTTP GET
# Tidak butuh API key, tidak butuh GPU, tidak butuh model download.
# URL: https://image.pollinations.ai/prompt/{prompt}?width=1080&height=1080&nologo=true

import time
import random
import requests
import yaml
from pathlib import Path
from datetime import datetime
from PIL import Image
import io
import urllib.parse

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
OUTPUT_DIR  = Path(__file__).parent.parent / "data" / "images"

# Base URL Pollinations
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def generate_image(image_prompt: str, niche: str, topic: str) -> str | None:
    """
    Generate gambar via Pollinations.ai.
    Return: path file gambar, atau None jika gagal.

    Pollinations.ai:
    - Gratis, tanpa API key
    - Resolusi hingga 1920x1920
    - Model default: FLUX (kualitas tinggi)
    - Kadang lambat (10-30 detik), sesekali timeout
    """
    config = load_config()
    width  = config["image"].get("width", 1080)
    height = config["image"].get("height", 1080)

    # Tambah suffix kualitas agar hasil lebih baik
    full_prompt = (
        image_prompt.strip()
        + ", high quality, detailed, instagram worthy, professional photography"
    )

    print(f"🎨 Memulai image generation via Pollinations.ai...")
    print(f"   Prompt: {image_prompt[:80]}...")

    encoded_prompt = urllib.parse.quote(full_prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&nologo=true"
        f"&seed={random.randint(1, 999999)}"
    )

    # Retry 3x (Pollinations kadang timeout di request pertama)
    for attempt in range(1, 4):
        try:
            print(f"   Attempt {attempt}/3 — requesting...", end=" ", flush=True)
            response = requests.get(url, timeout=60)

            if response.status_code == 200 and response.headers.get(
                "content-type", ""
            ).startswith("image"):
                print("✅")
                return save_image(response.content, niche, topic)
            else:
                print(f"❌ status {response.status_code}")

        except requests.Timeout:
            print(f"⏱ timeout")
        except Exception as e:
            print(f"❌ {e}")

        if attempt < 3:
            wait = attempt * 5
            print(f"   Retry dalam {wait}s...")
            time.sleep(wait)

    # Semua retry gagal → fallback
    print(f"⚠️  Semua attempt gagal, pakai fallback image")
    return generate_fallback_image(niche, topic)

def save_image(img_data: bytes, niche: str, topic: str) -> str:
    """Simpan image ke folder output, validasi dulu."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        img = Image.open(io.BytesIO(img_data))
        # Pastikan 1080x1080
        if img.size != (1080, 1080):
            img = img.resize((1080, 1080), Image.LANCZOS)
        # Pastikan RGB (bukan RGBA)
        if img.mode != "RGB":
            img = img.convert("RGB")
    except Exception as e:
        print(f"⚠️  Gagal proses gambar: {e} — pakai fallback")
        return generate_fallback_image(niche, topic)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"{timestamp}_{niche.replace(' ', '_')}.jpg"
    filepath  = OUTPUT_DIR / filename

    img.save(filepath, "JPEG", quality=92)
    print(f"✅ Image disimpan: {filename} ({img.size[0]}x{img.size[1]})")
    return str(filepath)

def generate_fallback_image(niche: str, topic: str) -> str:
    """
    Buat placeholder image saat Pollinations tidak tersedia.
    Berguna untuk testing pipeline tanpa internet.
    """
    from PIL import ImageDraw

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    colors = {
        "AI":                 ("#1a1a2e", "#e94560"),
        "teknologi":          ("#0f3460", "#16213e"),
        "desain":             ("#2d6a4f", "#40916c"),
        "bisnis online":      ("#f77f00", "#d62828"),
        "tips produktivitas": ("#3a0ca3", "#7209b7"),
    }
    bg_color, accent = colors.get(niche, ("#1a1a2e", "#e94560"))

    img  = Image.new("RGB", (1080, 1080), bg_color)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, 1080, 8],    fill=accent)
    draw.rectangle([0, 1072, 1080, 1080], fill=accent)
    draw.text((540, 460), f"[{niche.upper()}]", fill=accent,   anchor="mm")
    draw.text((540, 540), topic[:40],            fill="white",  anchor="mm")
    draw.text((540, 620), "AutoGram v2",         fill="#666666", anchor="mm")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"{timestamp}_{niche.replace(' ', '_')}_fallback.jpg"
    filepath  = OUTPUT_DIR / filename
    img.save(filepath, "JPEG", quality=85)

    print(f"✅ Fallback image disimpan: {filename}")
    return str(filepath)

if __name__ == "__main__":
    test_prompt = (
        "neural network visualization, futuristic lab, "
        "glowing circuits, tech aesthetic, soft lighting"
    )
    result = generate_image(test_prompt, "AI", "gemini ai")
    print(f"\n🎯 Output: {result}")