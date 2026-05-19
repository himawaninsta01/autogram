# visual_engine.py — v4.0 (Prompt Breakdown Carousel)
# Slide: Cover → Prompt → Output → Breakdown x3 → CTA

import time, random, requests, yaml, re, textwrap, json
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io, urllib.parse

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
]
FONT_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]
FONT_MONO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_font(size, bold=False, mono=False):
    paths = FONT_MONO if mono else (FONT_BOLD if bold else FONT_REG)
    for p in paths:
        try: return ImageFont.truetype(p, size)
        except: continue
    return ImageFont.load_default()

def parse_brief(brief: str, topic: str) -> dict:
    """Parse semua field dari brief string."""
    data = {
        "judul": topic.upper(),
        "poin": [],
        "ai_tool": "AI",
        "prompt": "",
        "output": "",
        "breakdown": [],
    }
    for line in brief.splitlines():
        line = line.strip()
        if line.startswith("JUDUL_GAMBAR:"):
            data["judul"] = line.replace("JUDUL_GAMBAR:", "").strip().upper()
        elif line.startswith("POIN_GAMBAR:"):
            raw = line.replace("POIN_GAMBAR:", "").strip()
            data["poin"] = [p.strip() for p in raw.split(",") if p.strip()][:5]
        elif line.startswith("AI_TOOL:"):
            data["ai_tool"] = line.replace("AI_TOOL:", "").strip()
        elif line.startswith("PROMPT:"):
            data["prompt"] = line.replace("PROMPT:", "").strip()
        elif line.startswith("OUTPUT:"):
            data["output"] = line.replace("OUTPUT:", "").strip()
        elif line.startswith("BREAKDOWN_"):
            parts = line.split(":", 1)[1].strip().split("|", 1)
            if len(parts) == 2:
                data["breakdown"].append({
                    "bagian": parts[0].strip(),
                    "penjelasan": parts[1].strip()
                })
    return data

def fetch_background(prompt: str, W: int, H: int):
    bg_prompt = "abstract dark tech background, " + prompt[:80] + ", no text, bokeh, soft neon glow"
    encoded = urllib.parse.quote(bg_prompt)
    url = (f"https://image.pollinations.ai/prompt/{encoded}"
           f"?width={W}&height={H}&nologo=true&seed={random.randint(1,999999)}")
    for attempt in range(1, 4):
        try:
            print(f"   BG {attempt}/3...", end=" ", flush=True)
            r = requests.get(url, timeout=55)
            if r.status_code == 200 and r.headers.get("content-type","").startswith("image"):
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                if img.size != (W, H):
                    img = img.resize((W, H), Image.LANCZOS)
                print("✅")
                return img
            print(f"❌{r.status_code}")
        except requests.Timeout: print("⏱")
        except Exception as e: print(f"❌{e}")
        if attempt < 3: time.sleep(attempt * 4)
    return None

def base_canvas(bg, bg_col, accent, W, H):
    if bg:
        canvas = bg.copy().convert("RGBA")
        dark = Image.new("RGBA", (W, H), (*bg_col, 205))
        canvas = Image.alpha_composite(canvas, dark)
    else:
        canvas = Image.new("RGBA", (W, H), (*bg_col, 255))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, 7, H], fill=(*accent, 255))
    for x in range(80, W, 70):
        for y in range(80, H, 70):
            draw.ellipse([x-1,y-1,x+1,y+1], fill=(*accent, 15))
    return canvas, draw

def draw_slide_indicator(draw, W, H, current, total, accent):
    dot_r, gap = 5, 18
    tw = total*(dot_r*2) + (total-1)*gap
    sx = (W - tw)//2
    for i in range(total):
        cx = sx + i*(dot_r*2+gap) + dot_r
        cy = H - 42
        fill = (*accent, 255) if i == current else (*accent, 55)
        draw.ellipse([cx-dot_r,cy-dot_r,cx+dot_r,cy+dot_r], fill=fill)

def draw_watermark(draw, W, H, accent):
    font = get_font(24)
    draw.rectangle([0, H-80, W, H-78], fill=(*accent, 70))
    draw.text((W-40, H-42), "@superchronos.ai", font=font,
              fill=(120,135,160), anchor="rm")

# ══════════════════════════════════════════════
# SLIDE 1: COVER
# ══════════════════════════════════════════════
def slide_cover(bg, data, niche, caption_hook, theme, total, W=1080, H=1080):
    accent, accent2, bg_col = theme["accent"], theme["accent2"], theme["bg"]
    canvas, draw = base_canvas(bg, bg_col, accent, W, H)

    # Badge AI tool
    font_badge = get_font(28, bold=True)
    badge = f"  {data['ai_tool'].upper()}  "
    bb = draw.textbbox((0,0), badge, font=font_badge)
    bw, bh = bb[2]-bb[0]+20, bb[3]-bb[1]+14
    bx, by = 50, 75
    draw.rounded_rectangle([bx,by,bx+bw,by+bh], radius=8,
                            fill=(*accent,35), outline=(*accent,200), width=2)
    draw.text((bx+10,by+7), badge.strip(), font=font_badge, fill=(*accent,255))

    # Label use case
    font_uc = get_font(30)
    uc_text = f"untuk: {data.get('use_case', niche)}"
    draw.text((50, by+bh+16), uc_text, font=font_uc, fill=(*accent2, 180))

    # Judul besar
    font_judul = get_font(70, bold=True)
    jy = by + bh + 70
    for line in textwrap.wrap(data["judul"], width=20)[:3]:
        draw.text((50, jy), line, font=font_judul, fill=(240,245,255))
        jy += 82

    # Garis aksen
    draw.rectangle([50, jy+10, min(50+len(data["judul"])*22, W-50), jy+14],
                   fill=(*accent2, 200))

    # Hook
    font_hook = get_font(34)
    hy = jy + 52
    for line in textwrap.wrap(caption_hook, width=36)[:3]:
        draw.text((50, hy), line, font=font_hook, fill=(170,185,212))
        hy += 46

    # Swipe
    font_sw = get_font(30, bold=True)
    draw.text((W-50, H//2+100), "swipe →", font=font_sw,
              fill=(*accent, 180), anchor="rm")

    draw_slide_indicator(draw, W, H, 0, total, accent)
    draw_watermark(draw, W, H, accent)
    return canvas.convert("RGB")

# ══════════════════════════════════════════════
# SLIDE 2: PROMPT (tampilan kode)
# ══════════════════════════════════════════════
def slide_prompt(bg, data, theme, total, W=1080, H=1080):
    accent, accent2, bg_col = theme["accent"], theme["accent2"], theme["bg"]
    canvas, draw = base_canvas(bg, bg_col, accent, W, H)

    # Header
    font_h = get_font(32, bold=True)
    draw.text((50, 55), f"📋 PROMPT {data['ai_tool'].upper()}", font=font_h,
              fill=(*accent, 255))
    draw.rectangle([50, 95, W-50, 98], fill=(*accent, 120))

    # Kotak kode
    box_x, box_y = 40, 115
    box_w, box_h = W - 80, H - 200
    draw.rounded_rectangle([box_x, box_y, box_x+box_w, box_y+box_h],
                            radius=16, fill=(15, 20, 40, 230),
                            outline=(*accent, 100), width=2)

    # Dot dekoratif (terminal style)
    dot_colors = [(255,90,90), (255,200,50), (50,210,100)]
    for i, dc in enumerate(dot_colors):
        cx = box_x + 22 + i*20
        draw.ellipse([cx-6,box_y+16,cx+6,box_y+28], fill=dc)

    # Label
    font_label = get_font(22)
    draw.text((box_x + box_w - 16, box_y + 16), f"copy → {data['ai_tool']}",
              font=font_label, fill=(*accent, 120), anchor="rm")

    # Teks prompt (monospace)
    font_code = get_font(30, mono=True)
    prompt_text = data.get("prompt", "")
    py = box_y + 52
    for line in textwrap.wrap(prompt_text, width=38)[:14]:
        if py > box_y + box_h - 40: break
        draw.text((box_x + 24, py), line, font=font_code, fill=(200, 215, 235))
        py += 42

    draw_slide_indicator(draw, W, H, 1, total, accent)
    draw_watermark(draw, W, H, accent)
    return canvas.convert("RGB")

# ══════════════════════════════════════════════
# SLIDE 3: OUTPUT (chat bubble style)
# ══════════════════════════════════════════════
def slide_output(bg, data, theme, total, W=1080, H=1080):
    accent, accent2, bg_col = theme["accent"], theme["accent2"], theme["bg"]
    canvas, draw = base_canvas(bg, bg_col, accent, W, H)

    # Header
    font_h = get_font(32, bold=True)
    draw.text((50, 55), f"✨ HASIL DARI {data['ai_tool'].upper()}", font=font_h,
              fill=(*accent, 255))
    draw.rectangle([50, 95, W-50, 98], fill=(*accent, 120))

    # Bubble output
    bub_x, bub_y = 40, 115
    bub_w, bub_h = W - 80, H - 195
    draw.rounded_rectangle([bub_x, bub_y, bub_x+bub_w, bub_y+bub_h],
                            radius=20, fill=(20, 30, 55, 235),
                            outline=(*accent2, 80), width=2)

    # Avatar AI
    av_r = 28
    av_cx, av_cy = bub_x + 40, bub_y + 45
    draw.ellipse([av_cx-av_r, av_cy-av_r, av_cx+av_r, av_cy+av_r],
                 fill=(*accent2, 60), outline=(*accent2, 200), width=2)
    font_av = get_font(24, bold=True)
    draw.text((av_cx, av_cy), data["ai_tool"][0], font=font_av,
              fill=(*accent2, 255), anchor="mm")

    # Nama AI
    font_name = get_font(26, bold=True)
    draw.text((av_cx + av_r + 14, av_cy - 8), data["ai_tool"],
              font=font_name, fill=(*accent2, 230))
    font_sub = get_font(22)
    draw.text((av_cx + av_r + 14, av_cy + 16), "AI Assistant",
              font=font_sub, fill=(120,135,165))

    # Teks output
    font_out = get_font(32)
    output_text = data.get("output", "")
    oy = bub_y + 96
    for line in textwrap.wrap(output_text, width=34)[:12]:
        if oy > bub_y + bub_h - 40: break
        draw.text((bub_x + 24, oy), line, font=font_out, fill=(210,222,242))
        oy += 46

    draw_slide_indicator(draw, W, H, 2, total, accent)
    draw_watermark(draw, W, H, accent)
    return canvas.convert("RGB")

# ══════════════════════════════════════════════
# SLIDE 4-6: BREAKDOWN (per bagian prompt)
# ══════════════════════════════════════════════
def slide_breakdown(bg, item: dict, idx: int, total_bd: int,
                    theme, slide_num, total_slides, W=1080, H=1080):
    accent, accent2, bg_col = theme["accent"], theme["accent2"], theme["bg"]
    canvas, draw = base_canvas(bg, bg_col, accent, W, H)

    # Header
    font_h = get_font(30, bold=True)
    draw.text((50, 55), f"🔍 BREAKDOWN PROMPT — BAGIAN {idx+1}/{total_bd}",
              font=font_h, fill=(*accent, 220))
    draw.rectangle([50, 93, W-50, 96], fill=(*accent, 100))

    # Nomor besar dekoratif
    font_num_bg = get_font(280, bold=True)
    draw.text((W-20, H//2+80), str(idx+1), font=font_num_bg,
              fill=(*accent, 10), anchor="rm")

    # Kotak highlight bagian prompt
    hbox_y = 130
    draw.rounded_rectangle([40, hbox_y, W-40, hbox_y+110], radius=14,
                            fill=(*accent, 20), outline=(*accent, 150), width=2)
    font_quote = get_font(36, mono=True)
    draw.text((W//2, hbox_y+55), f'"{item["bagian"]}"',
              font=font_quote, fill=(*accent, 255), anchor="mm")

    # Label
    font_lbl = get_font(24)
    draw.text((W//2, hbox_y+90), "↑ bagian ini penting karena...",
              font=font_lbl, fill=(*accent, 120), anchor="mm")

    # Penjelasan
    font_penj = get_font(38)
    py = hbox_y + 155
    for line in textwrap.wrap(item["penjelasan"], width=30)[:6]:
        draw.text((50, py), line, font=font_penj, fill=(215,228,248))
        py += 54

    # Efek visual — panah ke bawah
    font_arr = get_font(44, bold=True)
    draw.text((W//2, py+30), "↓", font=font_arr, fill=(*accent2, 150), anchor="mm")

    # Sub-label "efeknya ke output"
    font_eff = get_font(30)
    draw.text((W//2, py+82), "efeknya ke output AI",
              font=font_eff, fill=(*accent2, 120), anchor="mm")

    draw_slide_indicator(draw, W, H, slide_num, total_slides, accent)
    draw_watermark(draw, W, H, accent)
    return canvas.convert("RGB")

# ══════════════════════════════════════════════
# SLIDE TERAKHIR: CTA
# ══════════════════════════════════════════════
def slide_cta(bg, data, niche, theme, total, W=1080, H=1080):
    accent, accent2, bg_col = theme["accent"], theme["accent2"], theme["bg"]
    canvas, draw = base_canvas(bg, bg_col, accent, W, H)

    cx, cy = W//2, H//2 - 40

    # Lingkaran dekoratif
    for r, a in [(220, 15), (170, 25), (120, 40)]:
        draw.ellipse([cx-r,cy-r,cx+r,cy+r], outline=(*accent, a), width=2)

    # Teks utama
    font_main = get_font(70, bold=True)
    draw.text((cx, cy-70), "SAVE", font=font_main, fill=(*accent,255), anchor="mm")
    draw.text((cx, cy+10), "prompt ini!", font=font_main,
              fill=(240,245,255), anchor="mm")

    # Sub
    font_sub = get_font(32)
    draw.text((cx, cy+90), "Bagikan ke teman yang butuh 👇",
              font=font_sub, fill=(160,175,200), anchor="mm")

    draw.rectangle([80, cy+138, W-80, cy+141], fill=(*accent,70))

    # Username
    font_usr = get_font(46, bold=True)
    draw.text((cx, cy+180), "@superchronos.ai",
              font=font_usr, fill=(*accent,255), anchor="mm")

    # Tool tag
    font_tag = get_font(28)
    draw.text((cx, cy+236), f"#{data['ai_tool']} #PromptEngineering #TipsAI",
              font=font_tag, fill=(*accent2,150), anchor="mm")

    draw_slide_indicator(draw, W, H, total-1, total, accent)
    draw_watermark(draw, W, H, accent)
    return canvas.convert("RGB")

# ══════════════════════════════════════════════
# MAIN FUNCTION
# ══════════════════════════════════════════════
def generate_carousel(image_prompt: str, niche: str, topic: str,
                      brief: str = "", caption: str = "") -> list:
    config = load_config()
    W = config["image"].get("width", 1080)
    H = config["image"].get("height", 1080)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    theme  = THEMES.get(niche, DEFAULT_THEME)
    accent = theme["accent"]
    data   = parse_brief(brief, topic)
    hook   = caption.split("\n")[0][:120] if caption else data["judul"]

    # Hitung total slide: cover + prompt + output + breakdown*N + cta
    n_breakdown  = len(data["breakdown"]) if data["breakdown"] else 3
    total_slides = 1 + 1 + 1 + n_breakdown + 1

    print(f"🎨 Generating carousel {total_slides} slide (Prompt Breakdown)...")
    print(f"   Tool : {data['ai_tool']}")
    print(f"   Judul: {data['judul']}")

    # Fetch background sekali, dipakai semua slide
    bg = fetch_background(image_prompt, W, H)

    paths = []
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    niche_slug = niche.replace(" ", "_")

    def save(img, label):
        p = OUTPUT_DIR / f"{ts}_{niche_slug}_{label}.jpg"
        img.save(str(p), "JPEG", quality=92)
        paths.append(str(p))
        print(f"   ✅ {label}")
        return str(p)

    save(slide_cover(bg, data, niche, hook, theme, total_slides, W, H), "s00_cover")
    save(slide_prompt(bg, data, theme, total_slides, W, H), "s01_prompt")
    save(slide_output(bg, data, theme, total_slides, W, H), "s02_output")

    for i, item in enumerate(data["breakdown"][:3]):
        save(slide_breakdown(bg, item, i, min(3, len(data["breakdown"])),
                             theme, 3+i, total_slides, W, H),
             f"s{3+i:02d}_breakdown{i+1}")

    save(slide_cta(bg, data, niche, theme, total_slides, W, H),
         f"s{total_slides-1:02d}_cta")

    print(f"✅ Carousel selesai: {len(paths)} slide")
    return paths

def generate_image(image_prompt: str, niche: str, topic: str,
                   brief: str = "", caption: str = "") -> list:
    """Alias untuk backward compat."""
    return generate_carousel(image_prompt, niche, topic, brief, caption)

if __name__ == "__main__":
    test_brief = """JUDUL_GAMBAR: PROMPT EMAIL PROFESIONAL
AI_TOOL: Claude
PROMPT: Kamu adalah asisten profesional. Tolong tulis email kepada klien yang menjelaskan keterlambatan pengiriman proyek. Gunakan nada yang profesional namun tetap empati. Sertakan: alasan keterlambatan, solusi yang ditawarkan, dan timeline baru yang realistis. Maksimal 150 kata.
OUTPUT: Yth. Bapak/Ibu [Nama Klien], Kami ingin menyampaikan permohonan maaf atas keterlambatan pengiriman proyek. Hal ini disebabkan oleh kendala teknis yang tidak terduga. Sebagai solusi, kami telah menambah tim dan menjadwalkan penyelesaian pada 25 Mei 2026.
BREAKDOWN_1: Kamu adalah asisten profesional | Menetapkan persona membuat output lebih konsisten dan terfokus.
BREAKDOWN_2: nada yang profesional namun empati | Dua kata kunci ini mengontrol tone seluruh output.
BREAKDOWN_3: Maksimal 150 kata | Batasan panjang mencegah output yang terlalu bertele-tele."""

    paths = generate_carousel(
        "dark professional email interface glow",
        "AI", "email profesional dengan Claude",
        brief=test_brief,
        caption="Email profesional dalam 30 detik? Claude bisa. 🔥"
    )
    print(f"\n🎯 {len(paths)} slide generated")
    for p in paths: print(f"   {p}")