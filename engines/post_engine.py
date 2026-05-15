import os
import time
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired

load_dotenv()

SESSION_FILE = Path(__file__).parent.parent / "data" / "ig_session.json"

def get_client() -> Client:
    """Login ke Instagram, pakai session tersimpan jika ada."""
    cl = Client()
    cl.delay_range = [2, 5]  # Random delay antar request

    username = os.getenv("IG_USERNAME")
    password = os.getenv("IG_PASSWORD")

    if not username or not password:
        raise ValueError("IG_USERNAME atau IG_PASSWORD tidak ditemukan di .env")

    # Coba load session tersimpan
    if SESSION_FILE.exists():
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            cl.get_timeline_feed()  # Test apakah session masih valid
            print("✅ Session tersimpan berhasil digunakan")
            return cl
        except LoginRequired:
            print("⚠️  Session expired, login ulang...")
            SESSION_FILE.unlink(missing_ok=True)
        except Exception as e:
            print(f"⚠️  Session error: {e}, login ulang...")
            SESSION_FILE.unlink(missing_ok=True)

    # Login fresh
    try:
        print(f"🔐 Login sebagai {username}...")
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        print("✅ Login berhasil, session disimpan")
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
    # Test dry run dulu — tidak posting ke Instagram
    from pathlib import Path

    test_image = str(next(Path("data/images").glob("*.png")))
    test_caption = "Gemini AI hadir mengubah cara kita bekerja! 🚀\n\nCoba sekarang!"
    test_hashtags = ["#AI", "#GeminiAI", "#TeknologiIndonesia"]

    print("=== TEST POST ENGINE (DRY RUN) ===\n")
    result = upload_post(test_image, test_caption, test_hashtags, dry_run=True)
    print(f"\n🎯 Result: {result}")