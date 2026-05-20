# 📋 AUTOGRAM — Briefing Proyek & Roadmap Strategis

> **Dokumen Briefing Internal**
> Terakhir Diperbarui: 20 Mei 2026
> Disusun untuk: Tim Pengembang (Solo Developer + AI Co-Pilot)
> Status: **Fase 8 Selesai — Menuju Fase 9 (Migrasi Arsitektur SaaS)**

---

## 🔭 VISI

Menjadi **platform otomasi konten Instagram #1 di Indonesia** yang mampu menjalankan seluruh siklus hidup konten — dari riset tren, penulisan AI, pembuatan visual, hingga posting otomatis — secara **100% otonom, multi-klien, dan tanpa biaya operasional** (free-tier cloud services).

**Visi Jangka Panjang:**
> Autogram bukan sekadar bot Instagram. Autogram adalah **Agensi Digital AI** yang bisa mengelola puluhan akun Instagram sekaligus, dengan kualitas konten setara copywriter profesional, visual designer, dan social media manager — semuanya berjalan 24/7 tanpa campur tangan manusia.

---

## 🎯 GOAL (Tujuan Strategis)

### Goal Jangka Pendek (Q2 2026)
1. **Operasional Penuh**: Pipeline berjalan otonom 1x posting/hari untuk minimal 2 akun klien
2. **Deployment Cloud**: Aplikasi ter-deploy di Vercel (frontend) + Supabase (database & auth)
3. **Zero Hardcode**: Seluruh konfigurasi klien dikelola lewat antarmuka web, bukan file `.env`
4. **Keamanan Produksi**: Sistem login berbasis sesi, role-based access (Admin vs Customer)

### Goal Jangka Menengah (Q3-Q4 2026)
1. **5 Klien Aktif**: Onboard minimal 5 akun Instagram bisnis lokal
2. **Self-Service Portal**: Pelanggan bisa login, melihat statistik, dan mengkonfigurasi niche mereka sendiri
3. **Monetisasi**: Model langganan bulanan (Rp 150k - 500k/akun/bulan)
4. **Blog Engine**: Auto-publish artikel SEO ke website klien (Supabase + Vercel)

### Goal Jangka Panjang (2027)
1. **50+ Klien**: Skalabilitas multi-tenant penuh
2. **AI Generasi Ke-2**: Model fine-tuned khusus niche Indonesia
3. **Ekspansi Platform**: TikTok, Facebook, LinkedIn auto-posting
4. **White-Label**: Klien enterprise bisa branding dashboard sendiri

---

## 📐 ARSITEKTUR SAAT INI (Fase 1-8 — Selesai)

```
┌─────────────────────────────────────────────┐
│              AUTOGRAM v1.0                  │
│         (Monolith — Python Flask)           │
├─────────────────────────────────────────────┤
│                                             │
│  [Scheduler] ──► [Trend Engine]             │
│       │              │                      │
│       ▼              ▼                      │
│  [Content Engine] ◄── Groq LLM (Free)      │
│       │                                     │
│       ▼                                     │
│  [Visual Engine] ◄── Pollinations.ai (Free) │
│       │                                     │
│       ▼                                     │
│  [QA Engine] ──► [Post Engine]              │
│       │              │                      │
│       ▼              ▼                      │
│  [SQLite DB]    [Instagram API]             │
│                                             │
│  [Flask Dashboard] ◄── Basic Auth           │
│       │                                     │
│       ▼                                     │
│  localhost:5000                              │
└─────────────────────────────────────────────┘
```

### Keterbatasan Arsitektur Lama:
- ❌ SQLite = tidak bisa multi-instance, tidak bisa di-host serverless
- ❌ Flask monolith = tidak cocok untuk Vercel (serverless)
- ❌ Basic Auth = tidak mendukung multi-user / multi-role
- ❌ Tidak ada landing page publik
- ❌ Tidak ada pemisahan Admin vs Customer

---

## 🏗️ ARSITEKTUR TARGET (Fase 9 — SaaS Migration)

```
┌──────────────────────────────────────────────────────────┐
│                    AUTOGRAM v2.0                         │
│              (SaaS — Vercel + Supabase)                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────┐         │
│  │           VERCEL (Frontend + API)            │         │
│  │                                              │         │
│  │  [Landing Page]  ──  Publik, SEO-optimized   │         │
│  │  [Login Page]    ──  Supabase Auth (Email)   │         │
│  │  [Admin Panel]   ──  Role: admin             │         │
│  │  [Customer Page] ──  Role: customer          │         │
│  │  [API Routes]    ──  Serverless Functions     │         │
│  └──────────────────────┬───────────────────────┘         │
│                         │                                 │
│  ┌──────────────────────▼───────────────────────┐         │
│  │            SUPABASE (Backend)                 │         │
│  │                                               │         │
│  │  [Auth]     ── Email/Password, Session-based  │         │
│  │  [Database] ── PostgreSQL (partners, posts,   │         │
│  │                 users, pipeline_logs, etc.)    │         │
│  │  [Storage]  ── Gambar slide (opsional)         │         │
│  │  [Edge Fn]  ── Cron trigger pipeline           │         │
│  └──────────────────────┬───────────────────────┘         │
│                         │                                 │
│  ┌──────────────────────▼───────────────────────┐         │
│  │         AI ENGINE LAYER (Serverless)           │         │
│  │                                               │         │
│  │  [Groq API]          ── Content + QA          │         │
│  │  [Pollinations.ai]   ── Image Generation      │         │
│  │  [Google Trends]     ── Trend Research        │         │
│  │  [Instagram API]     ── Auto-posting          │         │
│  └───────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────┘
```

---

## 📄 HALAMAN-HALAMAN APLIKASI

### 1. 🏠 Landing Page (`/`)
- Hero section dengan tagline "Autopilot Instagram Anda"
- Fitur highlights (AI Content, Auto Post, Multi-Account)
- Pricing cards (Basic / Pro / Enterprise)
- Testimonial placeholder
- CTA → "Mulai Gratis" → Redirect ke `/login`
- **Akses**: Publik (tanpa login)

### 2. 🔐 Login Page (`/login`)
- Form email + password
- Supabase Auth integration
- "Lupa Password" flow
- "Daftar Akun Baru" link → `/register`
- **Akses**: Publik

### 3. 📝 Register Page (`/register`)
- Form pendaftaran (Nama, Email, Password)
- Auto-assign role `customer`
- Redirect ke `/dashboard` setelah berhasil
- **Akses**: Publik

### 4. 👤 Customer Dashboard (`/dashboard`)
- Statistik akun Instagram sendiri (followers, engagement)
- Riwayat postingan yang sudah di-publish AI
- Konfigurasi niche/topik yang diinginkan
- Preview konten mendatang
- **Akses**: Role `customer` (hanya melihat data sendiri)

### 5. 🛡️ Admin Panel (`/admin`)
- Seluruh fitur dashboard yang ada sekarang
- Manajemen semua partner/customer
- Kontrol pipeline manual (trigger, skip, retry)
- Log sistem & monitoring
- Konfigurasi scheduler
- Blog engine & SEO tools
- **Akses**: Role `admin` saja

---

## 🗄️ SKEMA DATABASE (Supabase PostgreSQL)

### Tabel `users` (Baru — Supabase Auth)
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | UUID (PK) | Dari Supabase Auth |
| email | TEXT | Email login |
| role | TEXT | `admin` atau `customer` |
| partner_id | TEXT (FK) | Relasi ke tabel partners |
| created_at | TIMESTAMP | - |

### Tabel `partners` (Evolusi)
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | TEXT (PK) | Slug unik (cth: `duagaris`) |
| name | TEXT | Nama brand |
| website_url | TEXT | - |
| niche_list | JSONB | Array niche/topik |
| ig_username | TEXT | Username IG |
| ig_password | TEXT | Password IG (encrypted) |
| theme_accent | TEXT | Warna tema 1 |
| theme_accent2 | TEXT | Warna tema 2 |
| theme_bg | TEXT | Warna background |
| supabase_url | TEXT | - |
| supabase_key | TEXT | - |
| telegram_token | TEXT | Notifikasi |
| telegram_chat_id | TEXT | - |
| is_active | BOOLEAN | Status aktif |
| created_at | TIMESTAMP | - |

### Tabel `posts` (Tetap)
| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | SERIAL (PK) | Auto-increment |
| partner_id | TEXT (FK) | Relasi ke partners |
| niche | TEXT | - |
| topic | TEXT | - |
| caption | TEXT | - |
| hashtags | JSONB | Array hashtag |
| image_path | TEXT | URL gambar |
| image_prompt | TEXT | Prompt AI |
| post_format | TEXT | single/carousel/thematic |
| series_id | TEXT | ID kampanye bertema |
| series_index | INT | Urutan dalam seri |
| qa_score | REAL | Skor QA 0-10 |
| status | TEXT | pending/posted/failed/skipped |
| ig_post_id | TEXT | ID post di Instagram |
| scheduled_at | TIMESTAMP | Jadwal posting |
| posted_at | TIMESTAMP | Waktu aktual posting |
| created_at | TIMESTAMP | - |

---

## 🛤️ DEPLOYMENT PIPELINE

```
Developer Push ──► GitHub (main branch)
                      │
                      ▼
              Vercel Auto-Deploy
                      │
              ┌───────┴────────┐
              │                │
         Frontend          API Routes
     (Next.js SSR)     (Serverless Fn)
              │                │
              └───────┬────────┘
                      │
                      ▼
               Supabase Cloud
          (PostgreSQL + Auth + Storage)
```

### Tech Stack Migrasi:
| Komponen | Lama | Baru |
|----------|------|------|
| Frontend | Flask + Jinja2 | Next.js (React) |
| Styling | Vanilla CSS | Vanilla CSS (migrasi) |
| Backend API | Flask routes | Next.js API Routes |
| Database | SQLite | Supabase PostgreSQL |
| Auth | Basic Auth | Supabase Auth (Session) |
| Hosting | localhost:5000 | Vercel (auto-deploy) |
| File Storage | Local disk | Supabase Storage |
| Cron/Scheduler | APScheduler | Supabase Edge Functions / Vercel Cron |

---

## ✅ RENCANA EKSEKUSI (Task Breakdown)

### Fase 9A: Fondasi Next.js + Supabase
- [ ] Inisialisasi proyek Next.js di direktori baru atau migrasi
- [ ] Setup Supabase project (database + auth)
- [ ] Migrasi skema SQLite → Supabase PostgreSQL
- [ ] Implementasi Supabase Auth (email/password)
- [ ] Setup environment variables (`.env.local`)

### Fase 9B: Halaman Publik
- [ ] Desain & implementasi Landing Page (`/`)
- [ ] Desain & implementasi Login Page (`/login`)
- [ ] Desain & implementasi Register Page (`/register`)
- [ ] Responsive design untuk mobile

### Fase 9C: Dashboard & Role-Based Access
- [ ] Implementasi middleware auth (protected routes)
- [ ] Admin Panel (`/admin`) — migrasi fitur dashboard Flask
- [ ] Customer Dashboard (`/dashboard`) — tampilan terbatas per-partner
- [ ] Role-based navigation & sidebar

### Fase 9D: Migrasi Engine ke Serverless
- [ ] Port `content_engine.py` → Next.js API Route (atau Python serverless)
- [ ] Port `visual_engine.py` → API Route
- [ ] Port `post_engine.py` → API Route
- [ ] Port `pipeline.py` → Vercel Cron atau Supabase Edge Function
- [ ] Port `qa_engine.py` → API Route

### Fase 9E: Deployment & Testing
- [ ] Push ke GitHub → Vercel auto-deploy
- [ ] Testing end-to-end (register → login → config → auto-post)
- [ ] Domain custom (opsional)
- [ ] Monitoring & logging di production

---

## 💰 MODEL BISNIS (Draft)

| Paket | Harga/Bulan | Fitur |
|-------|-------------|-------|
| **Starter** | Gratis | 1 akun IG, 3 post/minggu, watermark |
| **Pro** | Rp 150.000 | 1 akun IG, 1 post/hari, tanpa watermark, carousel |
| **Business** | Rp 350.000 | 3 akun IG, 1 post/hari, thematic campaign, blog SEO |
| **Enterprise** | Rp 500.000+ | Unlimited akun, custom branding, priority support |

---

## ⚠️ RISIKO & MITIGASI

| Risiko | Dampak | Mitigasi |
|--------|--------|----------|
| Instagram API rate limit / ban | Pipeline berhenti | Session rotation, delay acak, proxy (future) |
| Groq free tier habis | Konten gagal generate | Fallback ke model lain (Mistral, dll) |
| Vercel serverless timeout | Pipeline gagal | Pecah pipeline jadi beberapa step kecil |
| Supabase free tier limit | Database penuh | Monitoring usage, arsip data lama |
| Kualitas konten AI rendah | Engagement drop | QA Engine threshold ketat, human review option |

---

## 📊 METRIK KEBERHASILAN

| Metrik | Target Q2 2026 | Target Q4 2026 |
|--------|----------------|----------------|
| Uptime pipeline | 95% | 99% |
| Rata-rata QA Score | > 7.0 | > 8.0 |
| Jumlah klien aktif | 2 | 10 |
| Posting sukses/bulan | 60 | 300 |
| Revenue bulanan | Rp 0 (beta) | Rp 1.500.000 |

---

## 🔑 KEPUTUSAN ARSITEKTUR KUNCI

1. **Mengapa Next.js?** — Native Vercel support, SSR untuk landing page SEO, API routes menggantikan Flask, React ecosystem yang kaya.

2. **Mengapa Supabase?** — Free tier PostgreSQL yang generous (500MB), built-in Auth, realtime subscriptions, Edge Functions untuk cron, dan SDK yang mudah.

3. **Mengapa bukan tetap Flask?** — Flask membutuhkan server always-on (VPS), tidak cocok untuk serverless Vercel, dan tidak memiliki built-in auth/session management yang modern.

4. **Mengapa Python engines dipertahankan?** — Library `instagrapi`, `Pillow`, dan `groq` SDK hanya tersedia di Python. Kita akan menjalankannya sebagai API terpisah atau Vercel Python serverless functions.

---

> **Catatan Penutup:**
> Dokumen ini adalah *living document*. Akan terus diperbarui seiring perkembangan proyek. Setiap fase yang selesai akan di-commit ke GitHub sebagai checkpoint.
>
> *"Satu langkah kecil untuk kode, satu lompatan besar untuk bisnis."*
>
> — Tim Autogram, Mei 2026
