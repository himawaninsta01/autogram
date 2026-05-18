# visual_engine.py — v4.0 (Carousel Multi-Slide)
# Generate multiple slide PIL untuk carousel Instagram.
# Slide 1: Cover, Slide 2-N: 1 poin/slide, Slide terakhir: CTA

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
    """Ambil 1 background dari Pollinations, dipakai semua slide."""
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

def base_canvas(bg, bg_col, accent, W, H) -> tuple:
    """Buat canvas dasar dengan background + overlay gelap."""
    if bg:
        canvas = bg.copy().convert("RGBA")
        dark = Image.new("RGBA", (W, H), (*bg_col, 200))
        canvas = Image.alpha_composite(canvas, dark)
    else:
        canvas = Image.new("RGBA", (W, H), (*bg_col, 255))
    draw = ImageDraw.Draw(canvas)
    # Garis kiri
    draw.rectangle([0, 0, 7, H], fill=(*accent, 255))
    # Dot grid
    for x in range(80, W, 70):
        for y in range(80, H, 70):
            draw.ellipse([x-1, y-1, x+1, y+1], fill=(*accent, 18))
    return canvas, draw

def draw_footer(draw, canvas, accent, W, H, slide_num, total_slides):
    """Footer standar semua slide: watermark + indikator slide."""
    fy = H - 88
    draw.rectangle([0, fy, W, fy+2], fill=(*accent, 90))

    font_wm = get_font(26)
    draw.text((W - 44, H - 44), "@superchronos.ai",
              font=font_wm, fill=(125, 140, 165), anchor="rm")

    # Indikator slide (dot)
    dot_total = total_slides
    dot_r = 6
    dot_gap = 20
    total_w = dot_total * (dot_r*2) + (dot_total-1) * dot_gap
    start_x = (W - total_w) // 2
    for i in range(dot_total):
        cx = start_x + i * (dot_r*2 + dot_gap) + dot_r
        cy = H - 44
        if i == slide_num:
            draw.ellipse([cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r],
                         fill=(*accent, 255))
        else:
            draw.ellipse([cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r],
                         fill=(*accent, 60))

def build_cover_slide(bg, judul, niche, caption_hook, theme, W=1080, H=1080) -> Image.Image:
    """
    Slide 1 — Cover:
    Badge niche | Judul besar | Hook 1 kalimat | "Swipe →"
    """
    accent  = theme["accent"]
    accent2 = theme["accent2"]
    bg_col  = theme["bg"]

    canvas, draw = base_canvas(bg, bg_col, accent, W, H)

    # Badge niche
    font_badge = get_font(28, bold=True)
    badge_txt  = f"  {niche.upper()}  "
    bb = draw.textbbox((0,0), badge_txt, font=font_badge)
    bw = bb[2]-bb[0]+20; bh = bb[3]-bb[1]+14
    bx, by = 50, 80
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=8,
                            fill=(*accent, 35), outline=(*accent, 200), width=2)
    draw.text((bx+10, by+7), badge_txt.strip(), font=font_badge, fill=(*accent, 255))

    # Judul besar
    font_judul = get_font(72, bold=True)
    jy = by + bh + 40
    for line in textwrap.wrap(judul, width=20)[:3]:
        draw.text((50, jy), line, font=font_judul, fill=(240, 245, 255))
        jy += 84

    # Garis aksen
    draw.rectangle([50, jy+10, 420, jy+14], fill=(*accent2, 220))

    # Hook singkat
    font_hook = get_font(36)
    hook_short = textwrap.wrap(caption_hook, width=38)[:3]
    hy = jy + 50
    for line in hook_short:
        draw.text((50, hy), line, font=font_hook, fill=(180, 195, 215))
        hy += 46

    # Swipe indicator
    font_swipe = get_font(32, bold=True)
    draw.text((W - 50, H//2), "swipe →", font=font_swipe,
              fill=(*accent, 200), anchor="rm")

    draw_footer(draw, canvas, accent, W, H, 0, 1)  # placeholder, diupdate nanti

    return canvas.convert("RGB")

def build_point_slide(bg, poin: str, num: int, total: int,
                      niche: str, theme: dict, W=1080, H=1080) -> Image.Image:
    """
    Slide poin — 1 tips per slide:
    Nomor besar | Judul poin | Penjelasan detail
    """
    accent  = theme["accent"]
    accent2 = theme["accent2"]
    bg_col  = theme["bg"]

    canvas, draw = base_canvas(bg, bg_col, accent, W, H)

    # Nomor besar di background (dekoratif)
    font_num_bg = get_font(320, bold=True)
    draw.text((W - 30, H//2 + 60), str(num),
              font=font_num_bg, fill=(*accent, 12), anchor="rm")

    # Label "TIP #N"
    font_label = get_font(30, bold=True)
    label = f"TIP #{num} dari {total}"
    draw.text((50, 70), label, font=font_label, fill=(*accent, 200))
    draw.rectangle([50, 108, 50 + len(label)*18, 112], fill=(*accent, 100))

    # Judul poin (besar)
    font_poin_title = get_font(60, bold=True)
    py = 140
    for line in textwrap.wrap(poin, width=22)[:2]:
        draw.text((50, py), line, font=font_poin_title, fill=(235, 242, 255))
        py += 72

    # Garis pemisah
    draw.rectangle([50, py+16, W-50, py+20], fill=(*accent2, 150))

    # Penjelasan — diambil dari poin itu sendiri (diperluas)
    # Karena poin sudah cukup deskriptif, kita tampilkan ulang lebih besar
    font_detail = get_font(38)
    detail_lines = textwrap.wrap(poin, width=30)
    dy = py + 60
    for line in detail_lines[:4]:
        draw.text((50, dy), line, font=font_detail, fill=(170, 185, 210))
        dy += 52

    # Swipe hint (bukan slide terakhir)
    font_swipe = get_font(28, bold=True)
    draw.text((W - 50, H - 110), "→ next",
              font=font_swipe, fill=(*accent, 150), anchor="rm")

    draw_footer(draw, canvas, accent, W, H, num, 1)  # placeholder

    return canvas.convert("RGB")

def build_cta_slide(bg, niche: str, judul: str, theme: dict,
                    W=1080, H=1080) -> Image.Image:
    """
    Slide terakhir — CTA:
    Ajakan save/share/follow + username
    """
    accent  = theme["accent"]
    accent2 = theme["accent2"]
    bg_col  = theme["bg"]

    canvas, draw = base_canvas(bg, bg_col, accent, W, H)

    # Lingkaran dekoratif besar di tengah
    cx, cy, cr = W//2, H//2 - 60, 200
    draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr],
                 fill=(*accent, 15), outline=(*accent, 60), width=3)

    # Teks CTA utama
    font_cta = get_font(64, bold=True)
    draw.text((W//2, cy - 60), "SIMPAN", font=font_cta,
              fill=(*accent, 255), anchor="mm")
    draw.text((W//2, cy + 10), "konten ini!", font=font_cta,
              fill=(240, 245, 255), anchor="mm")

    # Sub teks
    font_sub = get_font(34)
    draw.text((W//2, cy + 100), "Bagikan ke teman yang butuh tips ini 👇",
              font=font_sub, fill=(160, 175, 200), anchor="mm")

    # Garis pemisah
    draw.rectangle([100, cy+155, W-100, cy+158], fill=(*accent, 80))

    # Username
    font_user = get_font(44, bold=True)
    draw.text((W//2, cy + 210), "@superchronos.ai",
              font=font_user, fill=(*accent, 255), anchor="mm")

    # Topik tag
    font_tag = get_font(28)
    draw.text((W//2, cy + 268), f"#{niche.replace(' ', '')} #TipsAI #TeknologiIndonesia",
              font=font_tag, fill=(*accent2, 160), anchor="mm")

    draw_footer(draw, canvas, accent, W, H, 0, 1)  # placeholder

    return canvas.convert("RGB")

def add_slide_dots(img: Image.Image, slide_idx: int, total: int,
                   accent, W: int, H: int) -> Image.Image:
    """Tambahkan dot indikator slide yang benar."""
    canvas = img.convert("RGBA")
    draw   = ImageDraw.Draw(canvas)
    dot_r  = 6
    dot_gap = 20
    total_w = total * (dot_r*2) + (total-1) * dot_gap
    sx = (W - total_w) // 2
    for i in range(total):
        cx = sx + i * (dot_r*2 + dot_gap) + dot_r
        cy = H - 44
        fill = (*accent, 255) if i == slide_idx else (*accent, 55)
        draw.ellipse([cx-dot_r, cy-dot_r, cx+dot_r, cy+dot_r], fill=fill)
    return canvas.convert("RGB")

def generate_carousel(image_prompt: str, niche: str, topic: str,
                      brief: str = "", caption: str = "") -> list[str]:
    """
    Generate semua slide carousel.
    Return: list path file gambar (cover + poin slides + cta).
    """
    config = load_config()
    W = config["image"].get("width", 1080)
    H = config["image"].get("height", 1080)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    theme   = THEMES.get(niche, DEFAULT_THEME)
    accent  = theme["accent"]

    judul, poin_list = parse_brief(brief, topic)
    if not poin_list:
        poin_list = [
            f"Gunakan {topic} untuk produktivitas harian",
            f"Optimalkan workflow dengan {topic}",
            f"Tips terbaik menggunakan {topic}",
        ]

    total_slides = 1 + len(poin_list) + 1  # cover + poin + cta
    hook = caption.split("\n")[0][:120] if caption else judul

    print(f"🎨 Generating carousel {total_slides} slide...")
    print(f"   Judul : {judul}")
    print(f"   Poin  : {len(poin_list)} item")

    # Fetch 1 background, dipakai semua slide
    print(f"🖼️  Fetching background...")
    bg = fetch_background(image_prompt, W, H)
    if not bg:
        print("⚠️  Background gagal, pakai solid color")

    paths = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Slide 1: Cover ──
    cover = build_cover_slide(bg, judul, niche, hook, theme, W, H)
    cover = add_slide_dots(cover, 0, total_slides, accent, W, H)
    p = OUTPUT_DIR / f"{timestamp}_{niche.replace(' ','_')}_s00_cover.jpg"
    cover.save(str(p), "JPEG", quality=92)
    paths.append(str(p))
    print(f"   ✅ Slide 1/{ total_slides}: Cover")

    # ── Slide 2..N: Poin ──
    for i, poin in enumerate(poin_list):
        slide = build_point_slide(bg, poin, i+1, len(poin_list), niche, theme, W, H)
        slide = add_slide_dots(slide, i+1, total_slides, accent, W, H)
        p = OUTPUT_DIR / f"{timestamp}_{niche.replace(' ','_')}_s{i+1:02d}_poin.jpg"
        slide.save(str(p), "JPEG", quality=92)
        paths.append(str(p))
        print(f"   ✅ Slide {i+2}/{total_slides}: Poin {i+1}")

    # ── Slide terakhir: CTA ──
    cta = build_cta_slide(bg, niche, judul, theme, W, H)
    cta = add_slide_dots(cta, total_slides-1, total_slides, accent, W, H)
    p = OUTPUT_DIR / f"{timestamp}_{niche.replace(' ','_')}_s{total_slides-1:02d}_cta.jpg"
    cta.save(str(p), "JPEG", quality=92)
    paths.append(str(p))
    print(f"   ✅ Slide {total_slides}/{total_slides}: CTA")

    print(f"✅ Carousel selesai: {len(paths)} slide")
    return paths

# Backward compat — single image (tidak dipakai lagi tapi jaga-jaga)
def generate_image(image_prompt: str, niche: str, topic: str,
                   brief: str = "", caption: str = "") -> list[str]:
    return generate_carousel(image_prompt, niche, topic, brief, caption)

if __name__ == "__main__":
    test_brief = """JUDUL_GAMBAR: 5 PROMPT CLAUDE TERBAIK
POIN_GAMBAR: Ringkas meeting jadi 5 menit, Buat email profesional sekali klik, Debug kode lebih cepat, Riset topik apapun dalam 30 detik, Buat konten viral dengan mudah"""
    test_caption = "Kamu buang 2 jam/hari karena salah pakai Claude 😬 Ini 5 prompt yang mengubah segalanya."

    paths = generate_carousel(
        "futuristic AI neural network glow blue green",
        "AI", "tips prompt claude",
        brief=test_brief, caption=test_caption
    )
    print(f"\n🎯 Output: {len(paths)} slide")
    for p in paths:
        print(f"   {p}")