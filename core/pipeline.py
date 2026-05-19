import os
import yaml
import json
from pathlib import Path
from datetime import datetime
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

def log_pipeline(post_id: int, stage: str, status: str,
                 duration: float = 0, message: str = ""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO pipeline_logs (post_id, stage, status, duration_s, message)
        VALUES (?, ?, ?, ?, ?)
    """, (post_id, stage, status, duration, message))
    conn.commit()
    conn.close()

def save_post_draft(data: dict) -> int:
    conn = get_connection()
    # image_path: simpan sebagai JSON list jika carousel
    image_path = data.get("image_path", "")
    if isinstance(image_path, list):
        image_path = json.dumps(image_path)

    cursor = conn.execute("""
        INSERT INTO posts (niche, topic, trend_score, caption, hashtags,
                          image_path, image_prompt, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
    """, (
        data["niche"], data["topic"], data.get("trend_score", 0),
        data["caption"], json.dumps(data["hashtags"]),
        image_path, data.get("image_prompt", "")
    ))
    conn.commit()
    post_id = cursor.lastrowid
    conn.close()
    return post_id

def update_post_status(post_id: int, status: str,
                       qa_score: float = None, ig_post_id: str = None,
                       error_msg: str = None):
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
    if niche_override:
        print(f"   Niche: {niche_override} (dari Telegram)")
    print("="*55)

    post_id = None

    try:
        # ── STEP 1: TREND RESEARCH ──
        print("\n📍 STEP 1: Trend Research")
        t = datetime.now()
        trend = research_trends()
        if niche_override:
            trend["niche"] = niche_override
            print(f"   ⚡ Niche override: {niche_override}")
        duration = (datetime.now() - t).total_seconds()
        print(f"   ✅ Selesai ({duration:.1f}s)")

        # ── STEP 2: CONTENT GENERATION ──
        print("\n📍 STEP 2: Content Generation")
        t = datetime.now()
        content = run_content_engine(trend["niche"], trend["topic"])
        content["trend_score"] = trend["score"]
        duration = (datetime.now() - t).total_seconds()
        print(f"   ✅ Selesai ({duration:.1f}s)")

        post_id = save_post_draft(content)
        print(f"   💾 Draft disimpan (ID: {post_id})")
        log_pipeline(post_id, "content", "success", duration)

        # ── STEP 3: IMAGE GENERATION (carousel) ──
        print("\n📍 STEP 3: Carousel Generation")
        t = datetime.now()
        image_paths = generate_image(
            content["image_prompt"],
            content["niche"],
            content["topic"],
            brief=content.get("brief", ""),
            caption=content.get("caption", "")
        )
        # image_paths adalah list[str]
        content["image_path"] = image_paths
        duration = (datetime.now() - t).total_seconds()
        slide_count = len(image_paths) if isinstance(image_paths, list) else 1
        print(f"   ✅ Selesai — {slide_count} slide ({duration:.1f}s)")
        log_pipeline(post_id, "visual", "success", duration,
                     f"slides={slide_count}")

        # Untuk QA, gunakan slide pertama (cover)
        qa_image = image_paths[0] if isinstance(image_paths, list) else image_paths

        # ── STEP 4: QA ENGINE ──
        print("\n📍 STEP 4: QA Check")
        qa_result = None
        for attempt in range(1, max_retries + 1):
            print(f"   Attempt {attempt}/{max_retries}...")
            t = datetime.now()
            qa_result = run_qa(
                content["niche"], content["topic"],
                content["caption"], content["hashtags"],
                content["image_prompt"], qa_image
            )
            duration = (datetime.now() - t).total_seconds()

            if qa_result["passed"]:
                print(f"   ✅ QA PASS (score: {qa_result['overall']:.1f})")
                log_pipeline(post_id, "qa", "pass", duration,
                             f"score={qa_result['overall']}")
                break
            else:
                print(f"   ❌ QA FAIL (score: {qa_result['overall']:.1f})")
                log_pipeline(post_id, "qa", "fail", duration,
                             f"score={qa_result['overall']}")
                if attempt < max_retries:
                    print(f"   🔄 Regenerate konten...")
                    content = run_content_engine(trend["niche"], trend["topic"])
                    content["trend_score"] = trend["score"]
                    content["image_path"] = image_paths

        if not qa_result or not qa_result["passed"]:
            update_post_status(post_id, "skipped", qa_result["overall"],
                               error_msg="QA gagal 3x")
            reason = f"QA gagal {max_retries}x (score terakhir: {qa_result['overall']:.1f}/10)"
            print(f"\n⚠️  Pipeline dihentikan — {reason}")
            notify_skip(reason)
            return {"success": False, "reason": "qa_failed", "post_id": post_id}

        # ── STEP 5: POSTING (carousel) ──
        print(f"\n📍 STEP 5: Upload Carousel ke Instagram")
        t = datetime.now()
        post_result = upload_post(
            image_paths,           # list[str]
            content["caption"],
            content["hashtags"],
            dry_run=dry_run
        )
        duration = (datetime.now() - t).total_seconds()

        if post_result["success"]:
            update_post_status(
                post_id, "posted",
                qa_score=qa_result["overall"],
                ig_post_id=post_result.get("post_id")
            )
            log_pipeline(post_id, "post", "success", duration)
            total = (datetime.now() - start_time).total_seconds()
            print(f"\n{'='*55}")
            print(f"✅ PIPELINE SELESAI — {total:.0f} detik")
            print(f"   Post ID  : {post_result.get('post_id')}")
            print(f"   Slides   : {post_result.get('slide_count')}")
            print(f"   QA Score : {qa_result['overall']:.1f}/10")
            if not dry_run:
                print(f"   URL      : {post_result.get('post_url')}")
            print(f"{'='*55}")

            notify_success(
                niche=content["niche"],
                topic=content["topic"],
                qa_score=qa_result["overall"],
                post_url=post_result.get("post_url") if not dry_run else None
            )
            return {"success": True, "post_id": post_id, "result": post_result}

        else:
            update_post_status(post_id, "failed",
                               error_msg=post_result.get("message"))
            log_pipeline(post_id, "post", "fail", duration,
                         post_result.get("message"))
            msg = post_result.get("message", "unknown error")
            print(f"\n❌ Upload gagal: {msg}")
            notify_fail(reason=msg, stage="upload")
            return {"success": False, "reason": "upload_failed", "post_id": post_id}

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        if post_id:
            update_post_status(post_id, "failed", error_msg=str(e))
        notify_fail(reason=str(e), stage="pipeline")
        return {"success": False, "reason": str(e)}

if __name__ == "__main__":
    result = run_pipeline(dry_run=False)
    print(f"\n🎯 Final result: {result}")