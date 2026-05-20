export default function LandingPage() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', overflowX: 'hidden' }}>
      {/* Hero Section */}
      <main style={{ 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column', 
        alignItems: 'center', 
        justifyContent: 'center',
        padding: '4rem 2rem',
        textAlign: 'center',
        position: 'relative'
      }}>
        {/* Glow overlay */}
        <div style={{
          position: 'absolute',
          top: '20%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '500px',
          height: '500px',
          background: 'radial-gradient(circle, rgba(0, 180, 255, 0.08) 0%, transparent 70%)',
          pointerEvents: 'none',
          zIndex: 0
        }} />

        <div style={{ zIndex: 1, maxWidth: '800px', width: '100%' }}>
          <span style={{ 
            fontSize: '0.85rem', 
            fontWeight: 700, 
            letterSpacing: '0.2em', 
            textTransform: 'uppercase',
            color: 'var(--accent)',
            background: 'var(--accent-muted)',
            padding: '0.4rem 1.2rem',
            borderRadius: '50px',
            border: '1px solid rgba(0, 229, 160, 0.2)',
            display: 'inline-block',
            marginBottom: '2rem'
          }}>
            V2 · Centaur AI Edition
          </span>
          
          <h1 style={{ 
            fontSize: '4rem', 
            fontWeight: 800, 
            lineHeight: '1.1',
            fontFamily: 'var(--font-title)',
            letterSpacing: '-0.04em',
            marginBottom: '1.5rem',
            background: 'linear-gradient(to right, #ffffff, #94a3b8)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Auto<span style={{ 
              background: 'linear-gradient(135deg, var(--accent) 0%, var(--accent2) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>Gram</span>
          </h1>

          <p style={{ 
            fontSize: '1.25rem', 
            color: 'var(--text-muted)', 
            lineHeight: '1.6',
            marginBottom: '3rem',
            fontWeight: 400
          }}>
            Social Media Content Pipeline 100% Cloud Serverless.
            Didukung oleh Groq API &amp; Pollinations.ai, dikendalikan melalui Dashboard terintegrasi.
          </p>

          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginBottom: '4rem' }}>
            <a href="/dashboard" className="btn btn-primary" style={{ padding: '0.9rem 2.2rem', fontSize: '1rem' }}>
              Buka Dashboard Kontrol
            </a>
            <a href="#features" className="btn btn-secondary" style={{ padding: '0.9rem 2.2rem', fontSize: '1rem' }}>
              Pelajari Fitur
            </a>
          </div>
        </div>

        {/* Feature Grid Quick View */}
        <section id="features" style={{ 
          maxWidth: '1200px', 
          width: '100%', 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
          gap: '2rem',
          marginTop: '2rem',
          zIndex: 1
        }}>
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', textAlign: 'left' }}>
            <span style={{ fontSize: '2rem' }}>⚡</span>
            <h3 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-title)' }}>Zero Host Costs</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Menjalankan pipeline di GitHub Actions cron scheduling dan Oracle Cloud VM gratis 24/7. PC lokal bebas mati.
            </p>
          </div>

          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', textAlign: 'left' }}>
            <span style={{ fontSize: '2rem' }}>🧠</span>
            <h3 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-title)' }}>Quality Control (QA Engine)</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Setiap draf dievaluasi oleh Llama-3.3-70B untuk menjaga keselarasan konten dan visual sebelum terunggah.
            </p>
          </div>

          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', textAlign: 'left' }}>
            <span style={{ fontSize: '2rem' }}>🎨</span>
            <h3 style={{ fontSize: '1.2rem', fontFamily: 'var(--font-title)' }}>Dynamic Visuals</h3>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
              Integrasi dinamis dengan generator gambar Pollinations.ai 1080×1080px tanpa kebutuhan kunci API eksternal.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer style={{ 
        borderTop: '1px solid var(--border)', 
        padding: '2rem', 
        background: 'rgba(14, 18, 26, 0.4)', 
        color: 'var(--text-muted)', 
        fontSize: '0.85rem',
        textAlign: 'center'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>AutoGram Project v2 — Centaur Edition.</div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <a href="/dashboard" style={{ color: 'var(--accent)' }}>Dashboard</a>
            <span>•</span>
            <a href="https://github.com" target="_blank" rel="noreferrer">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
