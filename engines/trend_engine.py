import yaml
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from pytrends.request import TrendReq
from core.database import get_connection

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

def get_google_trends_score(niche: str, pytrends) -> dict:
    """Ambil trending score dari Google Trends untuk satu niche."""
    try:
        pytrends.build_payload([niche], cat=0, timeframe='now 7-d', geo='ID')
        data = pytrends.interest_over_time()
        if data.empty:
            return {"niche": niche, "score": 0, "topic": niche, "source": "google_trends"}
        score = float(data[niche].mean())
        # Ambil related queries sebagai sub-topik
        related = pytrends.related_queries()
        top_queries = related.get(niche, {}).get("top", None)
        topic = niche
        if top_queries is not None and not top_queries.empty:
            topic = top_queries.iloc[0]["query"]
        return {"niche": niche, "score": score, "topic": topic, "source": "google_trends"}
    except Exception as e:
        print(f"⚠️  Google Trends error untuk '{niche}': {e}")
        return {"niche": niche, "score": 0, "topic": niche, "source": "error"}

def get_cached_trends(niche: str) -> dict | None:
    """Cek apakah ada cache trend yang masih valid (< 6 jam)."""
    conn = get_connection()
    row = conn.execute("""
        SELECT * FROM trend_cache 
        WHERE niche = ? AND expires_at > datetime('now')
        ORDER BY fetched_at DESC LIMIT 1
    """, (niche,)).fetchone()
    conn.close()
    if row:
        return {"niche": row["niche"], "score": row["score"], 
                "topic": row["topic"], "source": row["source"]}
    return None

def save_trend_cache(result: dict):
    """Simpan hasil trend ke cache dengan expiry 6 jam."""
    conn = get_connection()
    now = datetime.now()
    expires = now + timedelta(hours=6)
    conn.execute("""
        INSERT INTO trend_cache (niche, topic, score, source, fetched_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (result["niche"], result["topic"], result["score"], 
          result["source"], now, expires))
    conn.commit()
    conn.close()

def research_trends() -> dict:
    """
    Main function: riset semua niche, pilih yang paling viral.
    Return: dict dengan niche, topic, score terpilih.
    """
    config = load_config()
    niche_list = config["niche"]["list"]
    min_score = config["niche"]["min_trend_score"]
    fallback = config["niche"]["fallback_to_ai"]

    print(f"🔍 Memulai riset trend untuk {len(niche_list)} niche...")
    
    pytrends = TrendReq(hl='id-ID', tz=420)  # WIB = UTC+7 = 420 menit
    results = []

    for niche in niche_list:
        # Cek cache dulu
        cached = get_cached_trends(niche)
        if cached:
            print(f"  📦 Cache hit: '{niche}' → score {cached['score']:.1f}")
            results.append(cached)
            continue

        # Rate limit agar tidak kena block Google
        time.sleep(random.uniform(2, 4))
        
        result = get_google_trends_score(niche, pytrends)
        save_trend_cache(result)
        print(f"  🌐 Google Trends: '{niche}' → score {result['score']:.1f} | topik: {result['topic']}")
        results.append(result)

    # Pilih niche dengan score tertinggi
    results.sort(key=lambda x: x["score"], reverse=True)
    best = results[0]

    print(f"\n📊 Hasil scoring:")
    for r in results:
        bar = "█" * int(r["score"] / 5)
        print(f"  {r['niche']:<25} {bar} {r['score']:.1f}")

    if best["score"] < min_score and fallback:
        print(f"\n⚠️  Semua niche di bawah threshold ({min_score})")
        print(f"🤖 Fallback: pakai niche terbaik yang ada → '{best['niche']}'")

    print(f"\n✅ Niche terpilih: '{best['niche']}' | Topik: '{best['topic']}' | Score: {best['score']:.1f}")
    return best


if __name__ == "__main__":
    result = research_trends()
    print(f"\n🎯 Output: {result}")