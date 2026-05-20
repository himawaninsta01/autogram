'use client';

import { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';

interface Post {
  id: number;
  created_at: string;
  posted_at: string | null;
  niche: string;
  topic: string;
  trend_score: number;
  caption: string;
  hashtags: string;
  image_path: string;
  image_prompt: string;
  qa_score: number | null;
  ig_post_id: string | null;
  status: string;
  error_msg: string | null;
}

interface Stats {
  total: number;
  posted: number;
  successRate: number;
  avgQaScore: number;
  niches: Record<string, number>;
}

export default function DashboardPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [stats, setStats] = useState<Stats>({ total: 0, posted: 0, successRate: 0, avgQaScore: 0, niches: {} });
  const [selectedNiche, setSelectedNiche] = useState<string>('');
  const [customTopic, setCustomTopic] = useState<string>('');
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' | '' }>({ text: '', type: '' });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [expandedPost, setExpandedPost] = useState<number | null>(null);

  const nichesList = ['teknologi', 'AI', 'tips produktivitas', 'desain', 'bisnis online'];

  const fetchDashboardData = async () => {
    try {
      // Fetch posts
      const resPosts = await fetch('/api/posts');
      const dataPosts = await resPosts.json();
      if (dataPosts.posts) setPosts(dataPosts.posts);

      // Fetch stats
      const resStats = await fetch('/api/stats');
      const dataStats = await resStats.json();
      if (dataStats) setStats(dataStats);
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // Subscribe to realtime updates from Supabase for new/updated posts
    const channel = supabase
      .channel('schema-db-changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'posts' },
        () => {
          fetchDashboardData();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const triggerPipeline = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    setMessage({ text: 'Mengirim perintah pipeline ke GitHub Actions...', type: 'success' });

    try {
      const res = await fetch('/api/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          niche: selectedNiche || null,
          topic: customTopic || null
        })
      });

      const data = await res.json();
      if (res.ok && data.success) {
        setMessage({ text: '🚀 Pipeline berhasil dipicu! Silakan pantau beberapa menit ke depan.', type: 'success' });
        setCustomTopic('');
      } else {
        setMessage({ text: `❌ Gagal memicu pipeline: ${data.error || 'Unknown error'}`, type: 'error' });
      }
    } catch (err: any) {
      setMessage({ text: `❌ Terjadi kesalahan: ${err.message}`, type: 'error' });
    } finally {
      setIsRunning(false);
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'posted': return 'badge-success';
      case 'skipped': return 'badge-warning';
      case 'failed': return 'badge-danger';
      default: return 'badge-info';
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Navbar */}
      <header style={{ 
        borderBottom: '1px solid var(--border)', 
        background: 'rgba(14, 18, 26, 0.8)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 10,
        padding: '1rem 2rem'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-title)' }}>
              Auto<span style={{ color: 'var(--accent)' }}>Gram</span>
            </span>
            <span style={{ 
              fontSize: '10px', 
              fontWeight: 700, 
              background: 'var(--accent-muted)', 
              color: 'var(--accent)', 
              border: '1px solid rgba(0, 229, 160, 0.2)',
              padding: '2px 8px',
              borderRadius: '20px'
            }}>CENTAUR EDITION</span>
          </div>
          <nav style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
            <a href="/" style={{ fontSize: '0.9rem', color: 'var(--text-muted)', transition: 'var(--transition)' }} onMouseEnter={e => e.currentTarget.style.color = 'var(--text)'} onMouseLeave={e => e.currentTarget.style.color = 'var(--text-muted)'}>Home</a>
            <span style={{ width: '4px', height: '4px', borderRadius: '50%', background: 'var(--border)' }}></span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span className="pulse-dot"></span>
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>Active Mode</span>
            </div>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '2.5rem 2rem', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
        {/* KPI Cards */}
        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem', marginBottom: '2.5rem' }}>
          <div className="glass-card">
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Total Run</h4>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'var(--font-title)' }}>{isLoading ? '...' : stats.total}</div>
          </div>
          <div className="glass-card">
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Berhasil Post</h4>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'var(--font-title)', color: 'var(--accent)' }}>{isLoading ? '...' : stats.posted}</div>
          </div>
          <div className="glass-card">
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Success Rate</h4>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'var(--font-title)', color: 'var(--accent2)' }}>{isLoading ? '...' : `${stats.successRate}%`}</div>
          </div>
          <div className="glass-card">
            <h4 style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>Avg QA Score</h4>
            <div style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'var(--font-title)', color: 'var(--accent3)' }}>{isLoading ? '...' : `${stats.avgQaScore}/10`}</div>
          </div>
        </section>

        {/* Dashboard Panels Split */}
        <section style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem', alignItems: 'start', marginBottom: '2.5rem' }}>
          
          {/* Left panel: Trigger Pipeline Control */}
          <div className="glass-card" style={{ background: 'rgba(14, 18, 26, 0.4)' }}>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span>🚀</span> Control Center
            </h3>
            <form onSubmit={triggerPipeline} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Pilih Niche</label>
                <select 
                  className="input-field"
                  value={selectedNiche}
                  onChange={(e) => setSelectedNiche(e.target.value)}
                  style={{ cursor: 'pointer' }}
                >
                  <option value="">🎲 AI Auto-Select (Trend-based)</option>
                  {nichesList.map(n => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Topic Override (Opsional)</label>
                <input 
                  type="text" 
                  className="input-field" 
                  placeholder="Contoh: gemini 1.5 flash, tips coding"
                  value={customTopic}
                  onChange={(e) => setCustomTopic(e.target.value)}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginTop: '0.25rem' }}>Mengesampingkan penentuan topik otomatis trend.</span>
              </div>

              {message.text && (
                <div style={{ 
                  padding: '0.75rem 1rem', 
                  borderRadius: '6px', 
                  fontSize: '0.85rem',
                  lineHeight: '1.4',
                  backgroundColor: message.type === 'error' ? 'var(--danger-muted)' : 'var(--accent-muted)',
                  color: message.type === 'error' ? 'var(--danger)' : 'var(--accent)',
                  border: `1px solid ${message.type === 'error' ? 'rgba(255, 95, 126, 0.2)' : 'rgba(0, 229, 160, 0.2)'}`
                }}>
                  {message.text}
                </div>
              )}

              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={isRunning}
                style={{ width: '100%', marginTop: '0.5rem' }}
              >
                {isRunning ? (
                  <>
                    <span className="spinner"></span>
                    <span>Memproses...</span>
                  </>
                ) : (
                  <span>Trigger Pipeline Sekarang</span>
                )}
              </button>
            </form>
          </div>

          {/* Right panel: Active/Recent Post overview */}
          <div className="glass-card" style={{ minHeight: '340px' }}>
            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Sesi Pipa Terkini</h3>
            {isLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '220px' }}>
                <span className="spinner" style={{ width: '32px', height: '32px' }}></span>
              </div>
            ) : posts.length === 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '220px', color: 'var(--text-muted)' }}>
                <p>Belum ada eksekusi pipeline terekam.</p>
                <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>Klik tombol di panel kiri untuk memulai.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                  <div>
                    <span className={`badge ${getStatusBadgeClass(posts[0].status)}`} style={{ marginBottom: '0.5rem' }}>
                      {posts[0].status}
                    </span>
                    <h2 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-title)', fontWeight: 700 }}>
                      {posts[0].topic || 'Menunggu Topik...'}
                    </h2>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Niche: <strong style={{ color: 'var(--text)' }}>{posts[0].niche}</strong> | Trend Score: {posts[0].trend_score}
                    </p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      {new Date(posts[0].created_at).toLocaleString('id-ID')}
                    </span>
                    {posts[0].qa_score && (
                      <div style={{ marginTop: '0.5rem' }}>
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>QA Score: </span>
                        <strong style={{ color: 'var(--accent3)', fontSize: '1.2rem' }}>{posts[0].qa_score}</strong>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Caption Tergenerate:</h4>
                  <div style={{ 
                    background: 'rgba(0, 0, 0, 0.2)', 
                    padding: '1rem', 
                    borderRadius: '8px', 
                    fontSize: '0.9rem', 
                    lineHeight: '1.5',
                    maxHeight: '120px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {posts[0].caption || 'Belum ada caption.'}
                  </div>
                </div>

                {posts[0].image_prompt && (
                  <div>
                    <h4 style={{ fontSize: '0.9rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Prompt Visual:</h4>
                    <p style={{ fontSize: '0.85rem', fontStyle: 'italic', color: 'var(--text)' }}>
                      "{posts[0].image_prompt}"
                    </p>
                  </div>
                )}
                
                {posts[0].error_msg && (
                  <div style={{ 
                    padding: '0.75rem', 
                    background: 'var(--danger-muted)', 
                    border: '1px solid rgba(255, 95, 126, 0.1)',
                    borderRadius: '6px', 
                    color: 'var(--danger)',
                    fontSize: '0.85rem'
                  }}>
                    <strong>Error:</strong> {posts[0].error_msg}
                  </div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* History Section */}
        <section className="glass-card" style={{ marginBottom: '2.5rem' }}>
          <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>Riwayat Aktivitas Pipeline</h3>
          {isLoading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '150px' }}>
              <span className="spinner"></span>
            </div>
          ) : posts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              No history found.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th style={{ padding: '1rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Tanggal</th>
                    <th style={{ padding: '1rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Niche</th>
                    <th style={{ padding: '1rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Topik</th>
                    <th style={{ padding: '1rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Status</th>
                    <th style={{ padding: '1rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>QA Score</th>
                    <th style={{ padding: '1rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'right' }}>Detail</th>
                  </tr>
                </thead>
                <tbody>
                  {posts.map((post) => (
                    <>
                      <tr key={post.id} style={{ 
                        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                        transition: 'var(--transition)',
                      }}
                      onMouseEnter={e => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.02)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <td style={{ padding: '1rem 0.75rem', fontSize: '0.9rem' }}>
                          {new Date(post.created_at).toLocaleDateString('id-ID')}
                        </td>
                        <td style={{ padding: '1rem 0.75rem', fontSize: '0.9rem', fontWeight: 600 }}>{post.niche}</td>
                        <td style={{ padding: '1rem 0.75rem', fontSize: '0.9rem' }}>{post.topic}</td>
                        <td style={{ padding: '1rem 0.75rem' }}>
                          <span className={`badge ${getStatusBadgeClass(post.status)}`}>
                            {post.status}
                          </span>
                        </td>
                        <td style={{ padding: '1rem 0.75rem', fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent3)', textAlign: 'center' }}>
                          {post.qa_score || '-'}
                        </td>
                        <td style={{ padding: '1rem 0.75rem', textAlign: 'right' }}>
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                            onClick={() => setExpandedPost(expandedPost === post.id ? null : post.id)}
                          >
                            {expandedPost === post.id ? 'Tutup' : 'Lihat'}
                          </button>
                        </td>
                      </tr>

                      {expandedPost === post.id && (
                        <tr>
                          <td colSpan={6} style={{ 
                            padding: '1.5rem', 
                            background: 'rgba(0, 0, 0, 0.3)',
                            borderBottom: '1px solid var(--border)'
                          }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                              <div>
                                <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Caption</h4>
                                <pre style={{ 
                                  whiteSpace: 'pre-wrap', 
                                  fontFamily: 'var(--font-sans)', 
                                  fontSize: '0.85rem',
                                  lineHeight: '1.5',
                                  background: 'rgba(0, 0, 0, 0.2)',
                                  padding: '0.75rem',
                                  borderRadius: '6px'
                                }}>{post.caption}</pre>

                                <div style={{ marginTop: '1rem' }}>
                                  <h4 style={{ fontSize: '0.9rem', marginBottom: '0.25rem', color: 'var(--text-muted)' }}>Hashtags</h4>
                                  <span style={{ fontSize: '0.85rem', fontFamily: 'var(--font-mono)', color: 'var(--accent2)' }}>
                                    {(() => {
                                      try {
                                        const tags = JSON.parse(post.hashtags);
                                        return Array.isArray(tags) ? tags.join(', ') : post.hashtags;
                                      } catch {
                                        return post.hashtags;
                                      }
                                    })()}
                                  </span>
                                </div>
                              </div>

                              <div>
                                <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Visual Settings</h4>
                                <div style={{ fontSize: '0.85rem', lineHeight: '1.5', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                  <p><strong>Prompt:</strong> <span style={{ fontStyle: 'italic' }}>"{post.image_prompt}"</span></p>
                                  <p><strong>Local Path:</strong> <code style={{ color: 'var(--accent)' }}>{post.image_path || 'No path'}</code></p>
                                  {post.ig_post_id && (
                                    <p><strong>Instagram Post ID:</strong> <code style={{ color: 'var(--accent2)' }}>{post.ig_post_id}</code></p>
                                  )}
                                  {post.error_msg && (
                                    <p style={{ color: 'var(--danger)' }}><strong>Error:</strong> {post.error_msg}</p>
                                  )}
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border)', padding: '1.5rem 2rem', background: 'rgba(14, 18, 26, 0.4)', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1400px', margin: '0 auto', width: '100%' }}>
          <div>© {new Date().getFullYear()} AutoGram Pipeline Centaur Edition.</div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <span>Oracle Cloud Infrastructure</span>
            <span>•</span>
            <span>Vercel</span>
            <span>•</span>
            <span>Supabase</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
