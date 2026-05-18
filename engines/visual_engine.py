# visual_engine.py — v3.0 (Full PIL Infografis)
# Background dari Pollinations (dekoratif), teks 100% PIL — selalu terbaca.

import time
import random
import requests
import yaml
import re
import textwrap
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import urllib.parse

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
OUTPUT_DIR  = Path(__file__).parent.parent / "data" / "images"

THEMES = {
    "AI":                 {"bg": (8, 8, 24),    "accent": (0, 229, 160),  "accent2": (0, 180, 255)},
    "teknologi":          {"bg": (8, 16, 40),   "accent": (0, 180, 255),  "accent2": (0, 229, 200)},
    "desain":             {"bg": (8, 32, 24),   "accent": (0, 220, 120),  "accent2": (100, 255, 180)},
    "bisnis online":      {"bg": (32, 16, 8),   "accent": (255, 180, 0),  "accent2": (255, 120, 50)},
    "tips produktivitas": {"bg": (24, 8, 48),   "accent": (180, 100, 255),"accent2": (255, 100, 200)},
}
DEFAULT_THEME = {"bg": (8, 8, 24), "accent": (0, 229, 160), "accent2": (0, 180, 255)}

FONT_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
FONT_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    paths = FONT_BOLD if bold else FONT_REG
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

def parse_brief(brief: str, topic: str) -> tuple:
    """Ekstrak JUDUL_GAMBAR dan POIN_GAMBAR dari brief."""
    judul = topic.upper()
    poin_list = []
    for line in brief.splitlines():
        line = line.strip()
        if line.startswith("JUDUL_GAMBAR:"):
            judul = line.replace("JUDUL_GAMBAR:", "").strip().upper()
        if line.startswith("POIN_GAMBAR:"):
            raw = line.replace("POIN_GAMBAR:", "").strip()
            parts = re.split(r',\s*(?=\d+\.)|,\s*(?=-)|[\n;]|,', raw)
            poin_list = [
                re.sub(r'^[\d\-\.\)\u2022\*]\s*', '', p.strip())
                for p in parts if p.strip()
            ][:5]
    return judul, poin_list

def fetch_background(prompt: str, W: int, H: int):
    """Ambil background abstract dari Pollinations (tanpa teks)."""
    bg_prompt = (
        "abstract dark background, " + prompt[:80]
        + ", no text, no letters, dark moody, bokeh, soft glow, cinematic"
    )
    encoded = urllib.parse.quote(bg_prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={W}&height={H}&nologo=true&seed={random.randint(1, 999999)}"
    )
    for attempt in range(1, 4):
        try:
            print(f"   BG attempt {attempt}/3...", end=" ", flush=True)
            r = requests.get(url, timeout=55)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                if img.size != (W, H):
                    img = img.resize((W, H), Image.LANCZOS)
                print("✅")
                return img
            print(f"❌ {r.status_code}")
        except requests.Timeout:
            print("⏱ timeout")
        except Exception as e:
            print(f"❌ {e}")
        if attempt < 3:
            time.sleep(attempt * 4)
    return None

def build_infographic(bg, judul, poin_list, niche, topic, W=1080, H=1080):
    """Render infografis lengkap di atas background."""
    theme   = THEMES.get(niche, DEFAULT_THEME)
    bg_col  = theme["bg"]
    accent  = theme["accent"]
    accent2 = theme["accent2"]

    # Base canvas
    if bg:
        canvas = bg.copy().convert("RGBA")
        dark   = Image.new("RGBA", (W, H), (*bg_col, 195))
        canvas = Image.alpha_composite(canvas, dark)
    else:
        canvas = Image.new("RGBA", (W, H), (*bg_col, 255))

    draw = ImageDraw.Draw(canvas)

    # Garis vertikal kiri
    draw.rectangle([0, 0, 7, H], fill=(*accent, 255))

    # Dot grid subtle
    for x in range(80, W, 70):
        for y in range(80, H, 70):
            draw.ellipse([x-1, y-1, x+1, y+1], fill=(*accent, 20))

    # ── HEADER ──
    header_h = 230
    hdr = Image.new("RGBA", (W, header_h), (*bg_col, 245))
    canvas.paste(hdr, (0, 0), hdr)
    draw.rectangle([0, header_h - 4, W, header_h], fill=(*accent, 255))

    # Badge niche
    font_badge = get_font(26, bold=True)
    badge_txt  = niche.upper()
    bb = draw.textbbox((0, 0), badge_txt, font=font_badge)
    bw = bb[2] - bb[0] + 28
    bh = bb[3] - bb[1] + 14
    bx, by = 50, 32
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=7,
                            fill=(*accent, 35), outline=(*accent, 190), width=2)
    draw.text((bx + 14, by + 7), badge_txt, font=font_badge, fill=(*accent, 255))

    # Judul
    font_judul = get_font(62, bold=True)
    lines = textwrap.wrap(judul, width=24)[:2]
    jy = by + bh + 16
    for line in lines:
        draw.text((50, jy), line, font=font_judul, fill=(240, 245, 255))
        jy += 72

    # Garis aksen bawah judul
    draw.rectangle([50, jy + 6, 380, jy + 10], fill=(*accent2, 200))

    # ── BODY: poin-poin ──
    body_top = header_h + 36
    body_bot = H - 100
    n        = max(len(poin_list), 1)
    slot_h   = (body_bot - body_top) // n

    font_num  = get_font(42, bold=True)
    font_main = get_font(36, bold=False)
    font_sub  = get_font(28, bold=False)

    for i, poin in enumerate(poin_list):
        cy = body_top + i * slot_h + slot_h // 2

        # Lingkaran nomor
        nx, r = 80, 32
        draw.ellipse([nx-r, cy-r, nx+r, cy+r],
                     fill=(*accent, 28), outline=(*accent, 200), width=2)
        draw.text((nx, cy), str(i+1), font=font_num,
                  fill=(*accent, 255), anchor="mm")

        # Teks poin
        px = nx + r + 22
        wrapped = textwrap.wrap(poin, width=36)[:2]
        if len(wrapped) == 1:
            draw.text((px, cy), wrapped[0], font=font_main,
                      fill=(220, 232, 248), anchor="lm")
        else:
            draw.text((px, cy - 20), wrapped[0], font=font_main,
                      fill=(220, 232, 248), anchor="lm")
            draw.text((px, cy + 20), wrapped[1], font=font_sub,
                      fill=(155, 170, 200), anchor="lm")

        # Garis separator
        if i < n - 1:
            sy = body_top + (i+1) * slot_h - 1
            draw.rectangle([50, sy, W-50, sy+1], fill=(*accent, 28))

    # ── FOOTER ──
    fy = H - 88
    draw.rectangle([0, fy, W, fy+2], fill=(*accent, 90))
    font_wm = get_font(26, bold=False)
    draw.text((W - 44, H - 44), "@superchronos.ai",
              font=font_wm, fill=(125, 140, 165), anchor="rm")
    font_icon = get_font(26, bold=True)
    draw.text((44, H - 44), "✦ superchronos.ai",
              font=font_icon, fill=(*accent, 100), anchor="lm")

    return canvas.convert("RGB")

def generate_image(image_prompt: str, niche: str, topic: str,
                   brief: str = "") -> str | None:
    """Generate infografis PIL dengan background dari Pollinations."""
    config = load_config()
    W = config["image"].get("width", 1080)
    H = config["image"].get("height", 1080)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    judul, poin_list = parse_brief(brief, topic)

    if not poin_list:
        poin_list = [f"Tips {topic} #{i+1}" for i in range(3)]

    print(f"🎨 Generating infografis PIL v3...")
    print(f"   Judul : {judul}")
    print(f"   Poin  : {len(poin_list)} item")

    print(f"🖼️  Fetching background dari Pollinations...")
    bg = fetch_background(image_prompt, W, H)
    if not bg:
        print("⚠️  Background gagal, pakai solid color")

    img = build_infographic(bg, judul, poin_list, niche, topic, W, H)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = f"{timestamp}_{niche.replace(' ', '_')}.jpg"
    filepath  = OUTPUT_DIR / filename
    img.save(str(filepath), "JPEG", quality=92)
    print(f"✅ Infografis disimpan: {filename}")
    return str(filepath)

if __name__ == "__main__":
    test_brief = """JUDUL_GAMBAR: 5 PROMPT CLAUDE TERBAIK
POIN_GAMBAR: Ringkas meeting jadi 5 menit, Buat email profesional sekali klik, Debug kode lebih cepat, Riset topik apapun dalam 30 detik, Buat konten viral dengan mudah"""

    result = generate_image(
        "futuristic AI neural network glow blue green",
        "AI",
        "tips prompt claude",
        brief=test_brief
    )
    print(f"\n🎯 Output: {result}")