# blog_engine.py — v1.0 (Supabase Blog Publisher)
import re
import uuid
import datetime
import json
from pathlib import Path

def generate_slug(title: str) -> str:
    """Menghasilkan slug URL yang bersih dari judul artikel."""
    s = title.lower()
    s = re.sub(r'[^a-z0-9\s-]', '', s)
    s = re.sub(r'[\s-]+', '-', s).strip('-')
    return s

def calculate_read_time(content: str) -> int:
    """Menghitung perkiraan waktu baca berdasarkan jumlah kata."""
    words = len(content.split())
    minutes = max(1, round(words / 200))
    return minutes

def publish_to_supabase(partner_id: str, title: str, excerpt: str, content: str,
                        category: str, image_url: str, author: str, tags: list) -> dict:
    """Menerbitkan artikel blog langsung ke Supabase mitra yang bersangkutan."""
    from core.database import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, supabase_url, supabase_key FROM partners WHERE id = ?", (partner_id,))
    partner = cursor.fetchone()
    conn.close()
    
    if not partner:
        return {"status": "error", "message": f"Partner '{partner_id}' tidak ditemukan di database."}
        
    partner_name = partner["name"]
    sb_url = partner["supabase_url"]
    sb_key = partner["supabase_key"]
    
    # Jika kredensial kosong atau default dummy, simpan draf lokal
    if not sb_url or not sb_key or sb_url.startswith("https://xxxx"):
        drafts_dir = Path(__file__).parent.parent / "data" / "blog_drafts" / partner_id
        drafts_dir.mkdir(parents=True, exist_ok=True)
        
        slug = generate_slug(title)
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        published_at = datetime.date.today().isoformat()
        read_time = calculate_read_time(content)
        
        draft_data = {
            "id": art_id,
            "slug": slug,
            "title": title,
            "excerpt": excerpt,
            "content": content,
            "category": category,
            "imageUrl": image_url,
            "author": author,
            "publishedAt": published_at,
            "readTime": read_time,
            "tags": tags
        }
        
        draft_path = drafts_dir / f"{slug}.json"
        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(draft_data, f, indent=2, ensure_ascii=False)
            
        print(f"[BLOG] Partner '{partner_id}' Supabase belum terkonfigurasi. Menyimpan draf lokal ke {draft_path.name}")
        return {
            "status": "success",
            "mode": "local_draft",
            "message": f"Supabase belum dikonfigurasi. Draf disimpan lokal ke {draft_path.name}",
            "data": draft_data
        }
        
    try:
        from supabase import create_client
        supabase_client = create_client(sb_url, sb_key)
        
        slug = generate_slug(title)
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        published_at = datetime.date.today().isoformat()
        read_time = calculate_read_time(content)
        
        article_payload = {
            "id": art_id,
            "slug": slug,
            "title": title,
            "excerpt": excerpt,
            "content": content,
            "category": category,
            "image_url": image_url,
            "author": author,
            "published_at": published_at,
            "read_time": read_time,
            "tags": tags
        }
        
        # Simpan ke tabel 'articles' di Supabase menggunakan upsert
        res = supabase_client.table("articles").upsert([article_payload]).execute()
        
        print(f"[BLOG] Berhasil mempublikasikan artikel '{title}' ke Supabase {partner_name}!")
        return {
            "status": "success",
            "mode": "supabase",
            "message": f"Berhasil mempublikasikan ke Supabase {partner_name}",
            "data": article_payload
        }
    except Exception as e:
        print(f"[BLOG] Error menerbitkan ke Supabase: {e}")
        
        # Fallback sekunder ke draf lokal
        drafts_dir = Path(__file__).parent.parent / "data" / "blog_drafts" / partner_id
        drafts_dir.mkdir(parents=True, exist_ok=True)
        slug = generate_slug(title)
        art_id = f"art-{uuid.uuid4().hex[:8]}"
        published_at = datetime.date.today().isoformat()
        read_time = calculate_read_time(content)
        
        draft_data = {
            "id": art_id,
            "slug": slug,
            "title": title,
            "excerpt": excerpt,
            "content": content,
            "category": category,
            "imageUrl": image_url,
            "author": author,
            "publishedAt": published_at,
            "readTime": read_time,
            "tags": tags
        }
        
        draft_path = drafts_dir / f"{slug}.json"
        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(draft_data, f, indent=2, ensure_ascii=False)
            
        return {
            "status": "success",
            "mode": "local_draft_fallback",
            "message": f"Supabase error ({e}). Draf disimpan secara lokal.",
            "data": draft_data
        }

if __name__ == "__main__":
    # Test publishing draft lokal
    res = publish_to_supabase(
        partner_id="duagaris",
        title="5 Rahasia Menjaga Kebersihan Rumput Gajah Mini",
        excerpt="Tips merawat rumput gajah mini agar tahan lama, hijau tebal, dan bebas dari gulma liar.",
        content="## Perawatan Rumput Gajah Mini\n\nRumput gajah mini sangat populer karena perawatannya mudah. Namun, ada beberapa rahasia untuk menjaganya tetap premium...",
        category="Panduan Perawatan",
        image_url="https://placehold.co/1200x630/4A7A4D/FFFFFF/png?text=Rumput+Gajah+Mini+Premium",
        author="Tim Dua Garis",
        tags=["rumput", "taman", "tips", "gajah mini"]
    )
    print("Test Result:", res)
