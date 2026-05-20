import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AutoGram v2 — Centaur Dashboard',
  description: 'AI-driven social media automation and quality control workspace.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&family=Fira+Code:wght@400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body>
        {children}
      </body>
    </html>
  );
}
