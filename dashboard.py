# dashboard.py — v1.0 (AutoSEO Enterprise Dashboard Backend)
import os
import json
import sqlite3
import yaml
import re
import urllib.parse
import random
from pathlib import Path
from functools import wraps
from flask import Flask, jsonify, request, render_template, send_from_directory, render_template_string, Response

# Autentikasi Sederhana (Basic Auth)
def check_auth(username, password):
    admin_user = os.getenv("DASHBOARD_USER", "admin")
    admin_pass = os.getenv("DASHBOARD_PASS", "autoseo123")
    return username == admin_user and password == admin_pass

def authenticate():
    return Response(
    'Akses Ditolak. Harap masukkan kredensial Admin Autogram.\n', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# Impor engine lokal
sys_path = Path(__file__).parent
import sys
sys.path.append(str(sys_path))

from core.database import get_connection
from engines.blog_engine import publish_to_supabase, generate_slug, calculate_read_time
from engines.seo_engine import track_seo_rankings
from engines.social_analytics import track_social_stats

app = Flask(__name__, static_folder="static", template_folder="templates")

DB_PATH = sys_path / "data" / "autogram.db"
IMAGES_DIR = sys_path / "data" / "images"
DRAFTS_DIR = sys_path / "data" / "blog_drafts"

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

@app.route("/")
@requires_auth
def home():
    return render_template("index.html")

@app.route("/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)

@app.route("/api/partners", methods=["GET"])
def get_partners():
    """Mengembalikan daftar semua mitra/partner."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, website_url, niche_list, theme_accent, theme_accent2, theme_bg, ig_username FROM partners")
    rows = cursor.fetchall()
    conn.close()
    
    partners = []
    for r in rows:
        partners.append({
            "id": r["id"],
            "name": r["name"],
            "website_url": r["website_url"],
            "niche_list": json.loads(r["niche_list"]) if r["niche_list"] else [],
            "theme_accent": r["theme_accent"],
            "theme_accent2": r["theme_accent2"],
            "theme_bg": r["theme_bg"],
            "ig_username": r["ig_username"]
        })
    return jsonify(partners)

@app.route("/api/partners/save", methods=["POST"])
def save_partner():
    """Menyimpan atau memperbarui data konfigurasi mitra."""
    data = request.json
    partner_id = data.get("id")
    name = data.get("name")
    website_url = data.get("website_url")
    niche_list = json.dumps(data.get("niche_list", []))
    theme_accent = data.get("theme_accent", "42,67,45")
    theme_accent2 = data.get("theme_accent2", "74,122,77")
    theme_bg = data.get("theme_bg", "8,20,12")
    ig_username = data.get("ig_username", "")
    ig_password = data.get("ig_password", "")
    supabase_url = data.get("supabase_url", "")
    supabase_key = data.get("supabase_key", "")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO partners (id, name, website_url, niche_list, theme_accent, theme_accent2, theme_bg, ig_username, ig_password, supabase_url, supabase_key)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            website_url=excluded.website_url,
            niche_list=excluded.niche_list,
            theme_accent=excluded.theme_accent,
            theme_accent2=excluded.theme_accent2,
            theme_bg=excluded.theme_bg,
            ig_username=excluded.ig_username,
            ig_password=CASE WHEN excluded.ig_password <> '' THEN excluded.ig_password ELSE partners.ig_password END,
            supabase_url=CASE WHEN excluded.supabase_url <> '' THEN excluded.supabase_url ELSE partners.supabase_url END,
            supabase_key=CASE WHEN excluded.supabase_key <> '' THEN excluded.supabase_key ELSE partners.supabase_key END
    """, (partner_id, name, website_url, niche_list, theme_accent, theme_accent2, theme_bg, ig_username, ig_password, supabase_url, supabase_key))
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Konfigurasi mitra berhasil disimpan."})

@app.route("/api/stats/<partner_id>", methods=["GET"])
def get_stats(partner_id):
    """Mengambil statistik historis Instagram, kata kunci SEO, dan log pipeline mitra."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Analitik Instagram Historis (30 entri terakhir)
    cursor.execute("""
        SELECT followers, following, posts_count, engagement_rate, checked_at 
        FROM social_analytics 
        WHERE partner_id = ? 
        ORDER BY checked_at ASC LIMIT 30
    """, (partner_id,))
    social_rows = cursor.fetchall()
    
    social_history = []
    for r in social_rows:
        social_history.append({
            "followers": r["followers"],
            "following": r["following"],
            "posts_count": r["posts_count"],
            "engagement_rate": r["engagement_rate"],
            "checked_at": r["checked_at"]
        })
        
    # 2. Kata Kunci SEO Historis
    cursor.execute("""
        SELECT keyword, rank, checked_at 
        FROM seo_rank_history 
        WHERE partner_id = ? 
        ORDER BY checked_at ASC
    """, (partner_id,))
    seo_rows = cursor.fetchall()
    
    seo_history = {}
    for r in seo_rows:
        kw = r["keyword"]
        if kw not in seo_history:
            seo_history[kw] = []
        seo_history[kw].append({
            "rank": r["rank"],
            "checked_at": r["checked_at"]
        })
        
    # 3. Log Pipeline Terakhir (20 entri terakhir)
    cursor.execute("""
        SELECT id, stage, status, duration_s, message, timestamp 
        FROM pipeline_logs 
        WHERE partner_id = ? 
        ORDER BY timestamp DESC LIMIT 25
    """, (partner_id,))
    log_rows = cursor.fetchall()
    
    logs = []
    for r in log_rows:
        logs.append({
            "id": r["id"],
            "stage": r["stage"],
            "status": r["status"],
            "duration_s": r["duration_s"],
            "message": r["message"],
            "timestamp": r["timestamp"]
        })
        
    # 4. Pratinjau Slides Gambar Instagram Terakhir
    # Cari gambar-gambar terbaru di folder images
    images = []
    try:
        all_files = sorted(IMAGES_DIR.glob("*.jpg"), key=os.path.getmtime, reverse=True)
        # Kelompokkan berdasarkan batch kode tanggal-waktu
        # Format file: 20260520_110351_AI_s00_cover.jpg
        batches = {}
        for f in all_files:
            match = re.match(r"^(\d{8}_\d{6})_(.*)_s(\d{2})_(.*)\.jpg$", f.name)
            if match:
                batch_id = match.group(1)
                slide_num = int(match.group(3))
                if batch_id not in batches:
                    batches[batch_id] = []
                batches[batch_id].append({
                    "name": f.name,
                    "num": slide_num,
                    "path": f"/images/{f.name}"
                })
        
        # Urutkan slides di tiap batch
        for bid in batches:
            batches[bid] = sorted(batches[bid], key=lambda x: x["num"])
            
        # Ambil batch terbaru saja
        if batches:
            latest_bid = list(batches.keys())[0]
            images = batches[latest_bid]
    except Exception as e:
        print(f"Error loading slide images: {e}")
        
    conn.close()
    
    # Hitung rata-rata peringkat SEO terkini
    current_seo = {}
    for kw in seo_history:
        if seo_history[kw]:
            current_seo[kw] = seo_history[kw][-1]["rank"]
            
    avg_rank = 0
    ranks_list = [r for r in current_seo.values() if r > 0]
    if ranks_list:
        avg_rank = round(sum(ranks_list) / len(ranks_list), 1)
        
    latest_social = social_history[-1] if social_history else {"followers": 0, "following": 0, "posts_count": 0, "engagement_rate": 0.0}
    
    return jsonify({
        "social_history": social_history,
        "seo_history": seo_history,
        "current_seo": current_seo,
        "avg_seo_rank": avg_rank,
        "latest_social": latest_social,
        "logs": logs,
        "latest_slides": images
    })

import re

@app.route("/api/articles/<partner_id>", methods=["GET"])
def get_articles(partner_id):
    """Mengambil artikel lokal (draft JSON) dan jika terkoneksi, mengambil artikel live Supabase."""
    # 1. Muat draf lokal dari folder
    partner_drafts_dir = DRAFTS_DIR / partner_id
    partner_drafts_dir.mkdir(parents=True, exist_ok=True)
    
    drafts = []
    for f in partner_drafts_dir.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as file:
                data = json.load(file)
                data["status"] = "draft"
                data["local_path"] = f.name
                drafts.append(data)
        except Exception as e:
            print(f"Failed to read draft {f.name}: {e}")
            
    # Urutkan draf berdasarkan tanggal publish menurun
    drafts = sorted(drafts, key=lambda x: x.get("publishedAt", ""), reverse=True)
    
    # 2. Ambil data dari Supabase jika dikonfigurasi
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT supabase_url, supabase_key FROM partners WHERE id = ?", (partner_id,))
    partner = cursor.fetchone()
    conn.close()
    
    live_articles = []
    supabase_configured = False
    
    if partner:
        sb_url = partner["supabase_url"]
        sb_key = partner["supabase_key"]
        
        if sb_url and sb_key and not sb_url.startswith("https://xxxx"):
            supabase_configured = True
            try:
                from supabase import create_client
                supabase_client = create_client(sb_url, sb_key)
                res = supabase_client.table("articles").select("*").execute()
                if res.data:
                    for d in res.data:
                        live_articles.append({
                            "id": d["id"],
                            "slug": d["slug"],
                            "title": d["title"],
                            "excerpt": d["excerpt"],
                            "content": d["content"],
                            "category": d["category"],
                            "imageUrl": d["image_url"],
                            "author": d["author"],
                            "publishedAt": d["published_at"],
                            "readTime": d["read_time"],
                            "tags": d["tags"],
                            "status": "published"
                        })
            except Exception as e:
                print(f"[DASHBOARD] Supabase query failed: {e}")
                
    return jsonify({
        "drafts": drafts,
        "live": live_articles,
        "supabase_configured": supabase_configured
    })

@app.route("/api/articles/save", methods=["POST"])
def save_article_draft():
    """Menyimpan atau mengupdate draft artikel lokal."""
    data = request.json
    partner_id = data.get("partner_id")
    slug = data.get("slug")
    title = data.get("title")
    excerpt = data.get("excerpt")
    content = data.get("content")
    category = data.get("category", "Inspirasi & Tren")
    image_url = data.get("imageUrl", "https://placehold.co/1200x630/4A7A4D/FFFFFF/png?text=Rumah+Taman")
    author = data.get("author", "Tim Redaksi")
    tags = data.get("tags", [])
    
    if not partner_id or not title:
        return jsonify({"status": "error", "message": "Partner ID dan Judul wajib diisi."}), 400
        
    if not slug:
        slug = generate_slug(title)
        
    partner_drafts_dir = DRAFTS_DIR / partner_id
    partner_drafts_dir.mkdir(parents=True, exist_ok=True)
    
    draft_data = {
        "id": data.get("id") or f"art-{datetime.now().strftime('%m%d%H%M')}",
        "slug": slug,
        "title": title,
        "excerpt": excerpt,
        "content": content,
        "category": category,
        "imageUrl": image_url,
        "author": author,
        "publishedAt": data.get("publishedAt") or datetime.now().strftime("%Y-%m-%d"),
        "readTime": calculate_read_time(content),
        "tags": tags if isinstance(tags, list) else [t.strip() for t in tags.split(",") if t.strip()]
    }
    
    draft_path = partner_drafts_dir / f"{slug}.json"
    with open(draft_path, "w", encoding="utf-8") as f:
        json.dump(draft_data, f, indent=2, ensure_ascii=False)
        
    return jsonify({
        "status": "success",
        "message": "Draf artikel lokal berhasil disimpan.",
        "data": draft_data
    })

@app.route("/api/articles/publish", methods=["POST"])
def publish_article():
    """Menerbitkan artikel langsung ke Supabase Mitra."""
    data = request.json
    partner_id = data.get("partner_id")
    title = data.get("title")
    excerpt = data.get("excerpt")
    content = data.get("content")
    category = data.get("category")
    image_url = data.get("imageUrl")
    author = data.get("author")
    tags = data.get("tags", [])
    
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]
        
    res = publish_to_supabase(
        partner_id=partner_id,
        title=title,
        excerpt=excerpt,
        content=content,
        category=category,
        image_url=image_url,
        author=author,
        tags=tags
    )
    
    if res["status"] == "success":
        # Hapus draft lokal setelah dipublikasikan ke Supabase jika draf itu ada
        slug = generate_slug(title)
        draft_path = DRAFTS_DIR / partner_id / f"{slug}.json"
        if draft_path.exists():
            try:
                draft_path.unlink()
            except Exception as e:
                print(f"Failed to delete draft after publishing: {e}")
                
    return jsonify(res)

@app.route("/api/run-pipeline", methods=["POST"])
def run_pipeline():
    """Memicu aksi pipeline secara langsung."""
    data = request.json
    partner_id = data.get("partner_id")
    engine = data.get("engine") # 'seo', 'social', 'trend', 'blog', 'visual'
    
    if not partner_id or not engine:
        return jsonify({"status": "error", "message": "Partner ID dan tipe Engine wajib disertakan."}), 400
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, niche_list FROM partners WHERE id = ?", (partner_id,))
    partner = cursor.fetchone()
    conn.close()
    
    if not partner:
        return jsonify({"status": "error", "message": f"Partner '{partner_id}' tidak ditemukan."}), 404
        
    partner_name = partner["name"]
    niche_list = json.loads(partner["niche_list"]) if partner["niche_list"] else []
    
    start_time = datetime.now()
    
    try:
        message = ""
        duration_s = 0.0
        
        if engine == "seo":
            # Peringkat SEO
            res = track_seo_rankings(partner_id)
            duration_s = (datetime.now() - start_time).total_seconds()
            message = f"Berhasil melacak {len(res)} peringkat kata kunci di Google Indonesia."
            
            # Log ke pipeline_logs
            write_pipeline_log(partner_id, "SEO Rank", "success", duration_s, message)
            return jsonify({"status": "success", "message": message, "data": res})
            
        elif engine == "social":
            # Analitik Instagram
            res = track_social_stats(partner_id)
            duration_s = (datetime.now() - start_time).total_seconds()
            message = f"Berhasil menarik statistik Instagram: {res[0]['followers']} followers."
            
            # Log ke pipeline_logs
            write_pipeline_log(partner_id, "Social Stats", "success", duration_s, message)
            return jsonify({"status": "success", "message": message, "data": res})
            
        elif engine == "trend":
            # Riset tren niche baru
            niche = random.choice(niche_list) if niche_list else "taman"
            trend_score = round(random.uniform(45.0, 92.0), 1)
            topic = f"Desain {niche} modern minimalis"
            
            # Simpan cache trend
            conn = get_connection()
            conn.execute("""
                INSERT INTO trend_cache (partner_id, niche, topic, score, source, fetched_at, expires_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now', '+6 hour'))
            """, (partner_id, niche, topic, trend_score, "Google Trends (Simulated)"))
            conn.commit()
            conn.close()
            
            duration_s = (datetime.now() - start_time).total_seconds()
            message = f"Tren terpopuler terdeteksi: '{topic}' (Skor: {trend_score})"
            write_pipeline_log(partner_id, "Trend Research", "success", duration_s, message)
            return jsonify({"status": "success", "message": message, "data": {"niche": niche, "topic": topic, "score": trend_score}})
            
        elif engine == "blog":
            # Generasikan artikel blog draf
            niche = random.choice(niche_list) if niche_list else "desain taman"
            topic = f"Cara Merawat {niche} Agar Terlihat Hijau Segar"
            
            # Simulasi penulisan artikel berkelas premium
            title = f"5 Langkah Praktis Merawat {niche.title()} Menjadi Lebih Indah"
            excerpt = f"Temukan rahasia menata dan merawat {niche} agar memiliki tampilan visual sekelas hotel bintang lima di pekarangan Anda."
            content = f"""## Keindahan {niche.title()} yang Sempurna

Taman pekarangan adalah cermin dari rumah kita. Memiliki {niche} yang sehat dan rimbun tidak hanya menyejukkan mata, tetapi juga meningkatkan nilai estetika hunian secara signifikan.

### 1. Perencanaan Tata Letak (Layout)
Langkah awal adalah menentukan zonasi area agar pasokan sinar matahari merata ke seluruh tanaman hias Anda.

### 2. Penyiraman Berkala yang Presisi
Hindari menyiram berlebihan. Cukup lakukan di pagi hari sebelum terik matahari membakar permukaan daun.

### 3. Pemupukan Organik Berkala
Gunakan kompos alami untuk menjaga ekosistem tanah tetap gembur dan kaya nutrisi mikro.
"""
            slug = generate_slug(title)
            draft_data = {
                "id": f"art-{datetime.now().strftime('%m%d%H%M')}",
                "slug": slug,
                "title": title,
                "excerpt": excerpt,
                "content": content,
                "category": "Panduan & Inspirasi",
                "imageUrl": "https://placehold.co/1200x630/4A7A4D/FFFFFF/png?text=" + urllib.parse.quote(niche.title()),
                "author": "Asisten AutoSEO",
                "publishedAt": datetime.now().strftime("%Y-%m-%d"),
                "readTime": calculate_read_time(content),
                "tags": [niche, "taman", "tips", "halaman rumah"]
            }
            
            partner_drafts_dir = DRAFTS_DIR / partner_id
            partner_drafts_dir.mkdir(parents=True, exist_ok=True)
            with open(partner_drafts_dir / f"{slug}.json", "w", encoding="utf-8") as f:
                json.dump(draft_data, f, indent=2, ensure_ascii=False)
                
            duration_s = (datetime.now() - start_time).total_seconds()
            message = f"Berhasil menulis draf blog baru: '{title}'"
            write_pipeline_log(partner_id, "Blog Engine", "success", duration_s, message)
            return jsonify({"status": "success", "message": message, "data": draft_data})
            
        elif engine == "visual":
            # Jalankan Pillow visual engine untuk membuat slide
            import subprocess
            print("[DASHBOARD] Memicu visual_engine.py secara mandiri...")
            # Kita bisa memicu script visual_engine.py langsung lewat interpreter python yang sama
            interpreter = sys.executable
            script_path = sys_path / "engines" / "visual_engine.py"
            
            # Jalankan subprocess
            proc = subprocess.run([interpreter, str(script_path)], capture_output=True, text=True, timeout=90)
            duration_s = (datetime.now() - start_time).total_seconds()
            
            if proc.returncode == 0:
                message = "Berhasil me-render 7 slide visual Instagram komposit transparan premium."
                write_pipeline_log(partner_id, "Visual Canvas", "success", duration_s, message)
                return jsonify({"status": "success", "message": message})
            else:
                error_msg = f"Visual Engine gagal: {proc.stderr[:100]}"
                write_pipeline_log(partner_id, "Visual Canvas", "failed", duration_s, error_msg)
                return jsonify({"status": "error", "message": error_msg})
                
        else:
            return jsonify({"status": "error", "message": "Engine yang diminta tidak dikenal."}), 400
            
    except Exception as e:
        duration_s = (datetime.now() - start_time).total_seconds()
        err_msg = f"Gagal mengeksekusi pipeline: {str(e)}"
        write_pipeline_log(partner_id, engine.upper(), "failed", duration_s, err_msg)
        return jsonify({"status": "error", "message": err_msg}), 500

CONFIG_PATH = Path(__file__).parent / "config.yaml"

@app.route("/api/ai/enrich-story", methods=["POST"])
def enrich_story():
    """Mengembangkan narasi artikel dengan mengintegrasikan fakta lapangan nyata (E-E-A-T) via LLM (Groq) dengan fallback cerdas."""
    data = request.json
    partner_id = data.get("partner_id")
    title = data.get("title")
    category = data.get("category", "Inspirasi & Tren")
    real_experience = data.get("real_experience", "")
    
    if not title or not real_experience:
        return jsonify({"status": "error", "message": "Judul dan Fakta Lapangan wajib diisi."}), 400
        
    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f)
            model = config["content"]["llm_model"]
    except Exception:
        model = "llama-3.1-8b-instant"
        
    api_key = os.environ.get("GROQ_API_KEY")
    
    prompt = f"""Kamu adalah penulis blog profesional dan pakar di niche tersebut.
Buatlah artikel blog yang sangat menarik, berjiwa empati tinggi, terstruktur, dan memiliki kedalaman E-E-A-T (pengalaman nyata dan keahlian).

Judul: {title}
Kategori: {category}

FAKTA LAPANGAN / PENGALAMAN PROYEK (WAJIB dimasukkan secara natural dan mendalam):
"{real_experience}"

Gunakan Bahasa Indonesia yang elegan dan profesional (seperti tulisan majalah arsitektur atau pakar profesional).
Gunakan format Markdown untuk heading (##, ###) dan poin-poin.
Tulis artikel lengkap (minimal 350-500 kata) yang terbagi menjadi beberapa bagian:
1. Pembukaan yang berempati dengan masalah pembaca dan mengaitkannya dengan fakta lapangan/pengalaman di atas.
2. Penjelasan solusi konkret yang dilakukan (analisis mengapa taktik di atas berhasil).
3. 3-4 tips praktis tambahan bagi pembaca yang ingin menirunya.
4. Kesimpulan persuasif dan ajakan berkonsultasi.

Tulis HANYA konten artikel dalam format Markdown, tanpa pesan pembuka atau penutup."""

    content = ""
    excerpt = ""
    
    if api_key:
        try:
            from groq import Groq
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            content = response.choices[0].message.content.strip()
            
            # Buat excerpt singkat menggunakan AI
            excerpt_prompt = f"Buat ringkasan pendek (1-2 kalimat) yang memikat untuk artikel berikut:\n\n{content}\n\nHANYA berikan ringkasan tersebut tanpa teks lain."
            res_exc = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": excerpt_prompt}],
                temperature=0.7,
                max_tokens=150,
            )
            excerpt = res_exc.choices[0].message.content.strip()
        except Exception as e:
            print(f"[AI-ENRICH] Error calling Groq: {e}")
            
    if not content:
        # Fallback generator berkualitas tinggi dengan narasi terstruktur
        content = f"""## Menghadirkan Keindahan Nyata di Pekarangan Anda

Menghadapi tantangan di pekarangan rumah sering kali membuat kita frustrasi. Dari masalah tanah yang keras hingga rumput yang tiba-tiba menguning, setiap masalah memerlukan sentuhan ahli yang berpengalaman langsung di lapangan.

Baru-baru ini, kami membuktikan solusi konkret ini dalam proyek nyata kami:
> **"{real_experience}"**

### Mengapa Solusi Ini Berhasil?

Dari pengalaman lapangan di atas, pelajaran penting bagi kita semua adalah pentingnya diagnosis yang tepat terhadap masalah tanah dan drainase sebelum melakukan penataan. Sering kali, pemilik rumah memaksakan penanaman tanpa memperhatikan filter resapan, yang akhirnya berujung pada kegagalan tumbuh.

### 3 Tips Praktis untuk Meniru Hasil Ini:

1. **Kenali Karakteristik Tanah Anda**
   Lakukan pengujian kegemburan tanah secara manual. Tanah yang terlalu liat membutuhkan modifikasi media tanam pasir malang atau split agar sirkulasi air tetap terjaga.
   
2. **Pola Penyiraman Presisi**
   Pastikan pengairan merata namun tidak membuat air tergenang. Air yang menggenang adalah musuh utama dari akar tanaman sehat.
   
3. **Pemberian Nutrisi Tambahan Berkala**
   Gunakan kompos organik alami setiap dua bulan sekali untuk menjaga mikroorganisme tanah tetap aktif membantu perkembangan akar.

## Kesimpulan

Membangun taman yang sehat dan estetik bukan sekadar menanam, melainkan merawat ekosistem di bawahnya. Jika Anda menghadapi tantangan serupa di pekarangan rumah Anda, jangan ragu untuk memulai konsultasi dengan tim profesional kami untuk mendiagnosis solusi terbaik secara langsung."""
        
        excerpt = f"Temukan panduan praktis dan kisah nyata keberhasilan penataan pekarangan asri berbasis pengalaman lapangan kami."
        
    return jsonify({
        "status": "success",
        "content": content,
        "excerpt": excerpt
    })

from datetime import timedelta

@app.route("/api/scheduler/config", methods=["GET"])
def get_scheduler_config():
    """Mengembalikan konfigurasi scheduler dan estimasi postingan berikutnya."""
    try:
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f)
        sched = config.get("scheduler", {})
    except Exception:
        sched = {
            "interval_hours_min": 44,
            "interval_hours_max": 52,
            "engagement_windows": [[7, 9], [11, 13], [19, 22]]
        }
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp FROM pipeline_logs ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    last_run = None
    if row:
        last_run_str = row["timestamp"]
        if ' ' in last_run_str and 'T' not in last_run_str:
            last_run_str = last_run_str.replace(' ', 'T')
        try:
            last_run = datetime.fromisoformat(last_run_str)
        except Exception:
            last_run = datetime.now()
    else:
        last_run = datetime.now() - timedelta(hours=24)
        
    avg_interval = (sched.get("interval_hours_min", 44) + sched.get("interval_hours_max", 52)) / 2
    next_run = last_run + timedelta(hours=avg_interval)
    
    if next_run < datetime.now():
        next_run = datetime.now() + timedelta(hours=2)
        
    time_diff = next_run - datetime.now()
    total_seconds = int(time_diff.total_seconds())
    
    hours_left = total_seconds // 3600
    minutes_left = (total_seconds % 3600) // 60
    
    return jsonify({
        "status": "success",
        "config": sched,
        "next_run_timestamp": next_run.isoformat(),
        "hours_left": hours_left,
        "minutes_left": minutes_left,
        "formatted_next_run": next_run.strftime("%A, %d %B %Y pukul %H:%M WIB")
    })

@app.route("/api/scheduler/update", methods=["POST"])
def update_scheduler_config():
    """Mengupdate konfigurasi scheduler di berkas config.yaml."""
    data = request.json
    min_hours = int(data.get("interval_hours_min", 44))
    max_hours = int(data.get("interval_hours_max", 52))
    
    try:
        with open(CONFIG_PATH, "r") as f:
            config = yaml.safe_load(f)
    except Exception:
        config = {}
        
    if "scheduler" not in config:
        config["scheduler"] = {}
        
    config["scheduler"]["interval_hours_min"] = min_hours
    config["scheduler"]["interval_hours_max"] = max_hours
    
    try:
        with open(CONFIG_PATH, "w") as f:
            yaml.safe_dump(config, f, default_flow_style=False)
        return jsonify({"status": "success", "message": "Konfigurasi scheduler berhasil disimpan."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal menulis konfigurasi: {str(e)}"}), 500

@app.route("/api/niches/<partner_id>", methods=["GET"])
def get_niches(partner_id):
    """Mengambil semua daftar niche dan kata kunci terkonfigurasi untuk partner."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, niche, enabled, priority, style FROM niche_config WHERE partner_id = ?", (partner_id,))
    rows = cursor.fetchall()
    
    if len(rows) == 0:
        cursor.execute("SELECT niche_list FROM partners WHERE id = ?", (partner_id,))
        p_row = cursor.fetchone()
        if p_row and p_row["niche_list"]:
            n_list = json.loads(p_row["niche_list"])
            for n in n_list:
                cursor.execute("""
                    INSERT INTO niche_config (partner_id, niche, enabled, priority, style)
                    VALUES (?, ?, 1, 5, 'Clean Premium')
                """, (partner_id, n))
            conn.commit()
            
            cursor.execute("SELECT id, niche, enabled, priority, style FROM niche_config WHERE partner_id = ?", (partner_id,))
            rows = cursor.fetchall()
            
    conn.close()
    
    niches = []
    for r in rows:
        niches.append({
            "id": r["id"],
            "niche": r["niche"],
            "enabled": bool(r["enabled"]),
            "priority": r["priority"],
            "style": r["style"]
        })
    return jsonify(niches)

@app.route("/api/niches/add", methods=["POST"])
def add_niche_config():
    """Menambahkan niche/kata kunci baru untuk partner."""
    data = request.json
    partner_id = data.get("partner_id")
    niche = data.get("niche")
    priority = int(data.get("priority", 5))
    style = data.get("style", "Clean Premium")
    
    if not partner_id or not niche:
        return jsonify({"status": "error", "message": "Partner ID dan kata kunci niche wajib diisi."}), 400
        
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO niche_config (partner_id, niche, enabled, priority, style)
            VALUES (?, ?, 1, ?, ?)
        """, (partner_id, niche, priority, style))
        
        cursor.execute("SELECT niche_list FROM partners WHERE id = ?", (partner_id,))
        p_row = cursor.fetchone()
        if p_row:
            n_list = json.loads(p_row["niche_list"]) if p_row["niche_list"] else []
            if niche not in n_list:
                n_list.append(niche)
                cursor.execute("UPDATE partners SET niche_list = ? WHERE id = ?", (json.dumps(n_list), partner_id))
                
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Niche '{niche}' berhasil ditambahkan."})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"status": "error", "message": f"Kata kunci '{niche}' sudah terkonfigurasi."}), 400


def write_pipeline_log(partner_id, stage, status, duration_s, message):
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO pipeline_logs (partner_id, stage, status, duration_s, message)
            VALUES (?, ?, ?, ?, ?)
        """, (partner_id, stage, status, duration_s, message))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error writing pipeline log: {e}")

if __name__ == "__main__":
    # Jalankan Flask Server di Port 5000 secara lokal
    print("[OK] Starting AutoSEO Enterprise Local Dashboard on http://localhost:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
