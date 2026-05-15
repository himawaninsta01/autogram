import random
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.date import DateTrigger
from core.pipeline import run_pipeline

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_next_post_time() -> datetime:
    """Hitung waktu posting berikutnya secara random."""
    config = load_config()
    sched = config["scheduler"]

    # Random interval 44-52 jam dari sekarang
    hours = random.uniform(
        sched["interval_hours_min"],
        sched["interval_hours_max"]
    )
    base_time = datetime.now() + timedelta(hours=hours)

    # Sesuaikan ke engagement window terdekat
    windows = sched["engagement_windows"]
    best_time = None
    min_diff = float("inf")

    for window in windows:
        start_h, end_h = window
        candidate = base_time.replace(
            hour=random.randint(start_h, end_h - 1),
            minute=random.randint(0, 59),
            second=random.randint(0, 59)
        )
        # Jika candidate sudah lewat, tambah 1 hari
        if candidate < datetime.now():
            candidate += timedelta(days=1)

        diff = abs((candidate - base_time).total_seconds())
        if diff < min_diff:
            min_diff = diff
            best_time = candidate

    return best_time

def job_run_pipeline():
    """Job yang dijalankan scheduler — pipeline + jadwal berikutnya."""
    print(f"\n⏰ Scheduler trigger: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Jalankan pipeline (live, bukan dry run)
    result = run_pipeline(dry_run=False)
    
    if result["success"]:
        print(f"✅ Pipeline berhasil — post ID: {result['post_id']}")
    else:
        print(f"⚠️  Pipeline gagal: {result.get('reason')}")

    # Jadwalkan run berikutnya
    schedule_next()

def schedule_next():
    """Tambahkan job berikutnya ke scheduler."""
    next_time = get_next_post_time()
    scheduler.add_job(
        job_run_pipeline,
        trigger=DateTrigger(run_date=next_time),
        id="next_pipeline",
        replace_existing=True
    )
    print(f"\n📅 Post berikutnya dijadwalkan:")
    print(f"   {next_time.strftime('%A, %d %B %Y pukul %H:%M:%S WIB')}")
    hours_from_now = (next_time - datetime.now()).total_seconds() / 3600
    print(f"   ({hours_from_now:.1f} jam dari sekarang)")

scheduler = BlockingScheduler(timezone="Asia/Jakarta")

if __name__ == "__main__":
    print("="*55)
    print("🤖 AUTOGRAM SCHEDULER DIMULAI")
    print("="*55)

    # Jadwalkan run pertama
    schedule_next()

    print("\n✅ Scheduler aktif — tekan Ctrl+C untuk berhenti")
    print("   Pipeline akan berjalan otomatis sesuai jadwal\n")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n⛔ Scheduler dihentikan")
        scheduler.shutdown()