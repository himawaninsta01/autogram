import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

def send_notification(message: str):
    """Kirim notifikasi ke Telegram."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("⚠️  Telegram tidak dikonfigurasi, skip notifikasi")
        return False

    async def _send():
        bot = Bot(token=token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

    try:
        asyncio.run(_send())
        return True
    except Exception as e:
        print(f"⚠️  Telegram error: {e}")
        return False

def notify_success(niche: str, topic: str, qa_score: float,
                   post_url: str = None):
    msg = (
        f"✅ <b>AutoGram Post Berhasil!</b>\n\n"
        f"📌 Niche: {niche}\n"
        f"📝 Topik: {topic}\n"
        f"⭐ QA Score: {qa_score:.1f}/10\n"
    )
    if post_url:
        msg += f"🔗 <a href='{post_url}'>Lihat Post</a>"
    send_notification(msg)

def notify_fail(reason: str, stage: str):
    msg = (
        f"❌ <b>AutoGram Pipeline Gagal</b>\n\n"
        f"📍 Stage: {stage}\n"
        f"💬 Alasan: {reason}"
    )
    send_notification(msg)

def notify_skip(reason: str):
    msg = (
        f"⚠️ <b>AutoGram Skip Posting</b>\n\n"
        f"💬 Alasan: {reason}"
    )
    send_notification(msg)

def notify_next_schedule(next_time: str):
    msg = (
        f"📅 <b>Jadwal Posting Berikutnya</b>\n\n"
        f"🕐 {next_time}"
    )
    send_notification(msg)

if __name__ == "__main__":
    print("🧪 Test Telegram notifikasi...")
    result = send_notification(
        "🤖 <b>AutoGram aktif!</b>\n\nSistem notifikasi berjalan dengan baik."
    )
    if result:
        print("✅ Notifikasi terkirim — cek Telegram kamu!")
    else:
        print("❌ Gagal kirim notifikasi")