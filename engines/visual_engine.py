# visual_engine.py — v2.1 (Pollinations.ai + PIL Infografis)
# Upgrade: gambar sekarang berupa infografis dengan teks dari brief

import time
import random
import requests
import yaml
import re
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import urllib.parse

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
OUTPUT_DIR  = Path(__file__).parent.parent / "data" / "images"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def generate_image(image_prompt: str, niche: str, topic: str,
                   brief: str = "") -> str | None:
    """
    Generate gambar infografis via Pollinations.ai + overlay teks PIL.
    Return: path file gambar, atau None jika gagal.
    """
    config = load_config()
    width  = config["image"].get("width", 1080)
    height = config["image"].get("height", 1080)

    full_prompt = (
        image_prompt.strip()
        + ", infographic style, clean typography, high quality, "
          "instagram worthy, professional design, no watermark"
    )

    print(f"🎨 Memulai image generation via Pollinations.ai...")
    print(f"   Prompt: {image_prompt[:80]}...")

    encoded_prompt = urllib.parse.quote(full_prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&nologo=true"
        f"&seed={random.randint(1, 999999)}"
    )

    for attempt in range(1, 4):
        try:
            print(f"   Attempt {attempt}/3 — requesting...", end=" ", flush=True)
            response = requests.get(url, timeout=60)

            if response.status_code == 200 and response.headers.get(
                "content-type", ""
            ).startswith("image"):
                print("✅")
                img_path = save_image(response.content, niche, topic)

                # Overlay teks jika ada brief
                if brief and img_path:
                    img_path = overlay_text(img_path, topic, brief, niche)

                return img_path
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

    print(f"⚠️  Semua attempt gagal, pakai fallback image")
    return generate_fallback_image(niche, topic, brief)

def overlay_text(img_path: str, topic: str, brief: str, niche: str) -> str:
    """
    Overlay teks infografis di atas gambar yang sudah ada.
    Ekstrak JUDUL dan POIN dari brief.
    """
    try:
        img = Image.open(img_path).convert("RGBA")
        W, H = img.size

        # Ekstrak judul dan poin dari brief
        judul = topic.upper()
        poin_list = []

        for line in brief.splitlines():
            if line.startswith("JUDUL_GAMBAR:"):
                judul = line.replace("JUDUL_GAMBAR:", "").strip().upper()
            if line.startswith("POIN_GAMBAR:"):
                raw = line.replace("POIN_GAMBAR:", "").strip()
                # Support format: "1. xxx, 2. xxx" atau "- xxx, - xxx"
                poin_list = [
                    re.sub(r'^[\d\-\.\)\•]\s*', '', p.strip())
                    for p in re.split(r'[,\n]|(?=\d\.)', raw)
                    if p.strip()
                ][:5]

        if not poin_list:
            return img_path  # Tidak ada poin, skip overlay

        # ── Buat overlay panel bawah ──
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        panel_h = int(H * 0.52)
        panel_y = H - panel_h

        # Warna tema per niche
        themes = {
            "AI":                 ((10, 10, 30), (0, 229, 160)),
            "teknologi":          ((10, 20, 50), (0, 180, 255)),
            "desain":             ((10, 40, 30), (0, 229, 120)),
            "bisnis online":      ((40, 20, 10), (255, 180, 0)),
            "tips produktivitas": ((30, 10, 60), (180, 100, 255)),
        }
        bg_rgb, accent_rgb = themes.get(niche, ((10, 10, 30), (0, 229, 160)))

        # Panel semi-transparan
        panel = Image.new("RGBA", (W, panel_h), (*bg_rgb, 220))
        overlay.paste(panel, (0, panel_y))

        # Garis aksen atas panel
        draw.rectangle([0, panel_y, W, panel_y + 5], fill=(*accent_rgb, 255))

        # ── Font (fallback ke default jika tidak ada) ──
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
            font_poin  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
            font_icon  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font_title = ImageFont.load_default()
            font_poin  = font_title
            font_icon  = font_title

        draw_overlay = ImageDraw.Draw(overlay)

        # Judul
        title_y = panel_y + 22
        draw_overlay.text(
            (W // 2, title_y),
            judul[:40],
            font=font_title,
            fill=(*accent_rgb, 255),
            anchor="mt"
        )

        # Garis bawah judul
        draw_overlay.rectangle(
            [60, title_y + 62, W - 60, title_y + 65],
            fill=(*accent_rgb, 120)
        )

        # Poin-poin
        poin_start_y = title_y + 85
        poin_gap = (panel_h - 110) // max(len(poin_list), 1)
        poin_gap = min(poin_gap, 85)

        for i, poin in enumerate(poin_list):
            y = poin_start_y + i * poin_gap
            if y > H - 40:
                break

            # Bullet
            draw_overlay.text(
                (55, y),
                "▸",
                font=font_icon,
                fill=(*accent_rgb, 255),
                anchor="lt"
            )

            # Teks poin (wrap jika terlalu panjang)
            poin_text = poin[:60] + ("…" if len(poin) > 60 else "")
            draw_overlay.text(
                (100, y),
                poin_text,
                font=font_poin,
                fill=(220, 230, 240, 255),
                anchor="lt"
            )

        # Watermark kecil
        try:
            font_wm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except:
            font_wm = font_poin
        draw_overlay.text(
            (W - 20, H - 20),
            "@superchronos.ai",
            font=font_wm,
            fill=(150, 150, 150, 180),
            anchor="rb"
        )

        # Gabungkan overlay dengan gambar asli
        result = Image.alpha_composite(img, overlay).convert("RGB")

        # Simpan (overwrite file yang sama)
        result.save(img_path, "JPEG", quality=92)
        print(f"✅ Teks infografis ditambahkan ke gambar")
        return img_path

    except Exception as e:
        print(f"⚠️  Overlay teks gagal: {e} — pakai gambar tanpa overlay")
        return img_path

def save_image(img_data: bytes, niche: str, topic: str) -> str:
    """Simpan image ke folder output, validasi dulu."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        img = Image.open(io.BytesIO(img_data))
        if img.size != (1080, 1080):
            img = img.resize((1080, 1080), Image.LANCZOS)
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

def generate_fallback_image(niche: str, topic: str, brief: str = "") -> str:
    """Buat placeholder infografis saat Pollinations tidak tersedia."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    themes = {
        "AI":                 ("#0a0a1e", "#00e5a0"),
        "teknologi":          ("#0a1432", "#00b4ff"),
        "desain":             ("#0a2818", "#00e578"),
        "bisnis online":      ("#281408", "#ffb400"),
        "tips produktivitas": ("#1e0a3c", "#b464ff"),
    }
    bg_hex, accent_hex = themes.get(niche, ("#0a0a1e", "#00e5a0"))

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

    bg_rgb     = hex_to_rgb(bg_hex)
    accent_rgb = hex_to_rgb(accent_hex)

    img  = Image.new("RGB", (1080, 1080), bg_rgb)
    draw = ImageDraw.Draw(img)

    # Aksen border
    draw.rectangle([0, 0, 1080, 8],       fill=accent_rgb)
    draw.rectangle([0, 1072, 1080, 1080], fill=accent_rgb)

    # Judul
    judul = topic.upper()
    poin_list = []
    for line in brief.splitlines():
        if line.startswith("JUDUL_GAMBAR:"):
            judul = line.replace("JUDUL_GAMBAR:", "").strip().upper()
        if line.startswith("POIN_GAMBAR:"):
            raw = line.replace("POIN_GAMBAR:", "").strip()
            poin_list = [p.strip() for p in raw.split(",") if p.strip()][:5]

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_poin  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
        font_wm    = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except:
        font_title = ImageFont.load_default()
        font_poin  = font_title
        font_wm    = font_title

    draw.text((540, 200), judul[:35], font=font_title, fill=accent_rgb, anchor="mm")
    draw.rectangle([80, 240, 1000, 245], fill=(*accent_rgb, 100))

    for i, poin in enumerate(poin_list):
        y = 320 + i * 100
        draw.text((80, y), f"▸ {poin[:55]}", font=font_poin, fill=(210, 220, 230), anchor="lm")

    draw.text((1060, 1055), "@superchronos.ai", font=font_wm, fill=(120, 120, 120), anchor="rb")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"{timestamp}_{niche.replace(' ', '_')}_fallback.jpg"
    filepath  = OUTPUT_DIR / filename
    img.save(filepath, "JPEG", quality=85)

    print(f"✅ Fallback infografis disimpan: {filename}")
    return str(filepath)

if __name__ == "__main__":
    test_prompt = (
        "dark navy background, modern infographic card design, "
        "neon green accents, clean typography, AI tools cheat sheet"
    )
    test_brief = """JUDUL_GAMBAR: 5 PROMPT CLAUDE TERBAIK
POIN_GAMBAR: Ringkas meeting jadi 5 menit, Buat email profesional, Debug kode lebih cepat, Riset topik apapun, Buat konten viral"""

    result = generate_image(test_prompt, "AI", "tips claude ai", brief=test_brief)
    print(f"\n🎯 Output: {result}")