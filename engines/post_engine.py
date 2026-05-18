import os
import time
import json
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired

load_dotenv()

SESSION_FILE = Path(__file__).parent.parent / "data" / "ig_session.json"

def get_client() -> Client:
    """Login ke Instagram, prioritaskan IG_SESSION dari environment (GitHub Secrets)."""
    cl = Client()
    cl.delay_range = [2, 5]

    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")

    if not username or not password:
        raise ValueError("IG_USERNAME atau IG_PASSWORD tidak ditemukan di .env")

    # ── PRIORITAS 1: IG_SESSION dari GitHub Secrets (environment variable) ──
    session_str = os.getenv("IG_SESSION")
    if session_str:
        try:
            cl.set_settings(json.loads(session_str))
            cl.login(username, password)
            cl.get_timeline_feed()  # Test apakah session masih valid
            print("✅ Session dari GitHub Secrets berhasil digunakan")
            return cl
        except LoginRequired:
            print("⚠️  Session dari Secrets expired, coba login fresh...")
        except Exception as e:
            print(f"⚠️  Session dari Secrets error: {e}, coba login fresh...")

    # ── PRIORITAS 2: Session file lokal (untuk development) ──
    if SESSION_FILE.exists():
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            cl.get_timeline_feed()
            print("✅ Session file lokal berhasil digunakan")
            return cl
        except LoginRequired:
            print("⚠️  Session file lokal expired, login ulang...")
            SESSION_FILE.unlink(missing_ok=True)
        except Exception as e:
            print(f"⚠️  Session file lokal error: {e}, login ulang...")
            SESSION_FILE.unlink(missing_ok=True)

    # ── PRIORITAS 3: Login fresh ──
    try:
        print(f"🔐 Login fresh sebagai {username}...")
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        print("✅ Login berhasil, session disimpan ke file lokal")
        return cl
    except ChallengeRequired:
        print("❌ Instagram minta verifikasi (challenge)")
        print("   Buka Instagram di HP dan selesaikan verifikasi dulu")
        raise
    except Exception as e:
        print(f"❌ Login gagal: {e}")
        raise

def get_random_post_delay() -> int:
    """Hitung random delay dalam detik sebelum posting."""
    delay = random.uniform(30, 120)
    print(f"⏱️  Delay {delay:.0f} detik sebelum upload...")
    return int(delay)

def upload_post(image_path: str, caption: str, hashtags: list,
                dry_run: bool = False) -> dict:
    """
    Upload foto ke Instagram.
    dry_run=True: simulasi tanpa benar-benar posting.
    """
    full_caption = caption + "\n\n" + " ".join(hashtags)

    print(f"\n📤 Mempersiapkan upload...")
    print(f"   Image : {Path(image_path).name}")
    print(f"   Caption: {caption[:60]}...")
    print(f"   Hashtags: {len(hashtags)} tag")
    print(f"   Total caption: {len(full_caption)} karakter")

    if dry_run:
        print(f"\n🧪 DRY RUN MODE — tidak benar-benar posting")
        print(f"   Caption preview:\n{full_caption[:200]}...")
        return {
            "success": True,
            "dry_run": True,
            "post_id": "dry_run_000",
            "timestamp": datetime.now().isoformat()
        }

    # Delay natural sebelum upload
    time.sleep(get_random_post_delay())

    try:
        cl = get_client()

        print(f"📸 Mengupload ke Instagram...")
        media = cl.photo_upload(
            path=image_path,
            caption=full_caption
        )

        result = {
            "success": True,
            "dry_run": False,
            "post_id": str(media.pk),
            "post_url": f"https://instagram.com/p/{media.code}/",
            "timestamp": datetime.now().isoformat()
        }

        print(f"✅ Upload berhasil!")
        print(f"   Post ID : {result['post_id']}")
        print(f"   URL     : {result['post_url']}")
        return result

    except ChallengeRequired:
        return {
            "success": False,
            "error": "challenge_required",
            "message": "Instagram minta verifikasi — selesaikan di HP dulu"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(type(e).__name__),
            "message": str(e)
        }

if __name__ == "__main__":
    from pathlib import Path

    test_image = str(next(Path("data/images").glob("*.png")))
    test_caption = "Gemini AI hadir mengubah cara kita bekerja! 🚀\n\nCoba sekarang!"
    test_hashtags = ["#AI", "#GeminiAI", "#TeknologiIndonesia"]

    print("=== TEST POST ENGINE (DRY RUN) ===\n")
    result = upload_post(test_image, test_caption, test_hashtags, dry_run=True)
    print(f"\n🎯 Result: {result}")