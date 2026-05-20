import os
import yaml
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from core.database import get_connection, init_db
from core.notifier import notify_success, notify_fail, notify_skip
from engines.trend_engine import research_trends
from engines.content_engine import run_content_engine
from engines.visual_engine import generate_image
from engines.post_engine import upload_post
from engines.qa_engine import run_qa

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def log_pipeline(post_id: int, stage: str, status: str, duration: float = 0, message: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO pipeline_logs (post_id, stage, status, duration_s, message)
        VALUES (?, ?, ?, ?, ?)
    """, (post_id, stage, status, duration, message))
    conn.commit()
    conn.close()

def sync_to_supabase(post_id: int):
    """Sync a post row from local SQLite to Supabase PostgreSQL."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("⚠️  Supabase not configured (SUPABASE_URL / SUPABASE_SERVICE_KEY), skipping sync.")
        return

    import requests
    conn = get_connection()
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()

    if not row:
        return

    data = dict(row)
    
    # Map fields to match Supabase schema (exclude 'id' to let Supabase auto-increment it uniquely)
    payload = {
        "niche": data.get("niche"),
        "topic": data.get("topic"),
        "trend_score": data.get("trend_score"),
        "caption": data.get("caption"),
        "image_path": data.get("image_path"),
        "image_prompt": data.get("image_prompt"),
        "qa_score": data.get("qa_score"),
        "ig_post_id": data.get("ig_post_id"),
        "status": data.get("status"),
        "error_msg": data.get("error_msg"),
    }
    
    # Convert hashtags string back to array if it is JSON string
    hashtags_str = data.get("hashtags", "[]")
    try:
        payload["hashtags"] = json.loads(hashtags_str)
    except Exception:
        payload["hashtags"] = []

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

    try:
        endpoint = f"{url.rstrip('/')}/rest/v1/posts"
        res = requests.post(endpoint, headers=headers, json=payload)
        if res.status_code in [200, 201, 204]:
            print("✅ Successfully synced run data to Supabase PostgreSQL.")
        else:
            print(f"⚠️  Failed to sync to Supabase: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"⚠️  Supabase request failed: {e}")

def save_post_draft(data: dict) -> int:
    conn = get_connection()
    image_path = data.get("image_path", "")
    if isinstance(image_path, list):
        image_path = json.dumps(image_path)

    cursor = conn.execute("""
        INSERT INTO posts (partner_id, niche, topic, trend_score, caption, hashtags,
                          image_path, image_prompt, status, post_format, series_id, series_index, scheduled_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?, ?, ?)
    """, (
        data.get("partner_id", "duagaris"), data["niche"], data["topic"], data.get("trend_score", 0),
        data["caption"], json.dumps(data.get("hashtags", [])),
        image_path, data.get("image_prompt", ""),
        data.get("post_format", "single"), data.get("series_id"), data.get("series_index"), data.get("scheduled_at")
    ))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id

def update_post_status(post_id: int, status: str, qa_score: float = None, ig_post_id: str = None, error_msg: str = None):
    conn = get_connection()
    now = datetime.now()
    if status == "posted":
        conn.execute("""
            UPDATE posts SET status=?, qa_score=?, ig_post_id=?, posted_at=?
            WHERE id=?
        """, (status, qa_score, ig_post_id, now, post_id))
    else:
        conn.execute("""
            UPDATE posts SET status=?, qa_score=?, error_msg=?
            WHERE id=?
        """, (status, qa_score, error_msg, post_id))
    conn.commit()
    conn.close()

def process_upload(post_id: int, image_paths: list, caption: str, hashtags: list, qa_score: float, dry_run: bool, niche: str, topic: str, ig_username: str, ig_password: str):
    print(f"\n📍 STEP 5: Upload ke Instagram (Post ID {post_id}) sebagai {ig_username}")
    start_time = datetime.now()
    t = datetime.now()
    
    post_result = upload_post(image_paths, caption, hashtags, ig_username=ig_username, ig_password=ig_password, dry_run=dry_run)
    duration = (datetime.now() - t).total_seconds()

    if post_result["success"]:
        update_post_status(post_id, "posted", qa_score=qa_score, ig_post_id=post_result.get("post_id"))
        log_pipeline(post_id, "post", "success", duration)
        
        print(f"\n{'='*55}")
        print(f"✅ PIPELINE UPLOAD SELESAI — {duration:.0f} detik")
        print(f"   Post ID  : {post_result.get('post_id')}")
        print(f"   QA Score : {qa_score:.1f}/10")
        if not dry_run:
            print(f"   URL      : {post_result.get('post_url')}")
        print(f"{'='*55}")

        notify_success(niche=niche, topic=topic, qa_score=qa_score, post_url=post_result.get("post_url") if not dry_run else None)
        return {"success": True, "post_id": post_id, "result": post_result}
    else:
        update_post_status(post_id, "failed", error_msg=post_result.get("message"))
        log_pipeline(post_id, "post", "fail", duration, post_result.get("message"))
        msg = post_result.get("message", "unknown error")
        print(f"\n❌ Upload gagal: {msg}")
        notify_fail(reason=msg, stage="upload")
        return {"success": False, "reason": "upload_failed", "post_id": post_id}

def run_pipeline(dry_run: bool = False) -> dict:
    init_db()
    config = load_config()
    max_retries = config["content"]["max_retries"]
    start_time = datetime.now()
    niche_override = os.getenv("NICHE_OVERRIDE", "").strip()

    print("\n" + "="*55)
    print("🚀 AUTOGRAM PIPELINE DIMULAI")
    print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"   Waktu: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*55)

    try:
        # CEK ANTREAN (PENDING POSTS)
        conn = get_connection()
        cursor = conn.execute("""
            SELECT p.id, p.image_path, p.caption, p.hashtags, p.niche, p.topic, p.qa_score, 
                   pt.ig_username, pt.ig_password 
            FROM posts p
            LEFT JOIN partners pt ON p.partner_id = pt.id
            WHERE p.status = 'pending' AND (p.scheduled_at IS NULL OR p.scheduled_at <= ?) 
            ORDER BY p.scheduled_at ASC, p.id ASC LIMIT 1
        """, (datetime.now(),))
        pending = cursor.fetchone()
        
        if pending:
            conn.close()
            print(f"\n📍 Memproses post tertunda dari antrean (ID: {pending['id']})")
            post_id = pending['id']
            try:
                image_paths = json.loads(pending['image_path'])
            except:
                image_paths = [pending['image_path']]
            
            try:
                hashtags = json.loads(pending['hashtags'])
            except:
                hashtags = pending['hashtags'].split() if pending['hashtags'] else []
                
            return process_upload(
                post_id, image_paths, pending['caption'], hashtags, pending['qa_score'] or 10.0, 
                dry_run, pending['niche'], pending['topic'], 
                pending['ig_username'], pending['ig_password']
            )

        # FETCH ACTIVE PARTNER FOR NEW DRAFT
        cursor = conn.execute("SELECT id, ig_username, ig_password FROM partners LIMIT 1")
        active_partner = cursor.fetchone()
        conn.close()

        if not active_partner:
            raise ValueError("Tidak ada partner terkonfigurasi di database.")
        
        partner_id = active_partner['id']
        ig_username = active_partner['ig_username']
        ig_password = active_partner['ig_password']

        # JIKA TIDAK ADA ANTREAN -> BUAT KONTEN BARU
        print("\n📍 STEP 1: Trend Research")
        t = datetime.now()
        trend = research_trends()
        if niche_override:
            trend["niche"] = niche_override
        duration = (datetime.now() - t).total_seconds()
        print(f"   ✅ Selesai ({duration:.1f}s)")

        print("\n📍 STEP 2: Content Generation")
        t = datetime.now()
        content = run_content_engine(trend["niche"], trend["topic"])
        duration = (datetime.now() - t).total_seconds()
        print(f"   ✅ Selesai ({duration:.1f}s)")

        post_format = content["post_format"]
        posts_data = content["posts_data"]
        
        series_id = str(uuid.uuid4())[:8] if post_format == "thematic" else None
        
        first_post_id = None
        first_post_data = None

        print(f"\n📍 STEP 3: Visual Generation & Drafting ({len(posts_data)} part)")
        for idx, p_data in enumerate(posts_data):
            print(f"   Generating Part {idx+1}...")
            p_data["partner_id"] = partner_id
            p_data["niche"] = trend["niche"]
            p_data["topic"] = trend["topic"]
            p_data["trend_score"] = trend["score"]
            p_data["post_format"] = post_format
            p_data["series_id"] = series_id
            p_data["series_index"] = idx + 1
            
            # Jadwalkan untuk esok hari dan lusa jika thematic
            if idx > 0:
                p_data["scheduled_at"] = datetime.now() + timedelta(days=idx)
            else:
                p_data["scheduled_at"] = datetime.now()

            # Generate Image (Cloud)
            slide_count = p_data.get("slide_count", 1)
            image_paths = generate_image(p_data.get("image_prompt", ""), p_data["niche"], p_data["topic"], slide_count=slide_count)
            p_data["image_path"] = image_paths

            # QA Check (Optional in batch, we can assume 10.0 or run QA here)
            qa_image = image_paths[0] if isinstance(image_paths, list) else image_paths
            qa_result = run_qa(p_data["niche"], p_data["topic"], p_data["caption"], p_data.get("hashtags", []), p_data.get("image_prompt", ""), qa_image)
            p_data["qa_score"] = qa_result["overall"]

            post_id = save_post_draft(p_data)
            print(f"   💾 Draft Part {idx+1} disimpan (ID: {post_id}) dengan QA Score: {qa_result['overall']}")
            
            if idx == 0:
                first_post_id = post_id
                first_post_data = p_data
                first_qa_result = qa_result

        # Langsung post part pertama!
        if first_qa_result and first_qa_result["passed"]:
            return process_upload(
                first_post_id, 
                first_post_data["image_path"], 
                first_post_data["caption"], 
                first_post_data.get("hashtags", []), 
                first_qa_result["overall"], 
                dry_run, 
                first_post_data["niche"], 
                first_post_data["topic"],
                ig_username, ig_password
            )
        else:
            reason = f"QA gagal (score: {first_qa_result['overall']:.1f}/10)"
            update_post_status(first_post_id, "skipped", first_qa_result["overall"], error_msg=reason)
            print(f"\n⚠️  Pipeline dihentikan — {reason}")
            notify_skip(reason)
            return {"success": False, "reason": "qa_failed", "post_id": first_post_id}

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        notify_fail(reason=str(e), stage="pipeline")
        return {"success": False, "reason": str(e)}
    finally:
        if post_id:
            try:
                sync_to_supabase(post_id)
            except Exception as se:
                print(f"⚠️  Supabase sync failed: {se}")

if __name__ == "__main__":
    result = run_pipeline(dry_run=False)
    print(f"\n🎯 Final result: {result}")