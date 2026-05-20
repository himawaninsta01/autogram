import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { niche, topic } = body;

    const token = process.env.GH_TOKEN;
    const owner = process.env.GH_OWNER;
    const repo = process.env.GH_REPO;

    if (!token || !owner || !repo) {
      return NextResponse.json(
        { error: 'GitHub configuration missing on server.' },
        { status: 500 }
      );
    }

    const url = `https://api.github.com/repos/${owner}/${repo}/dispatches`;
    
    // Set up client payload for GitHub repository_dispatch
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'autogram-dashboard-api',
      },
      body: JSON.stringify({
        event_type: 'manual_run',
        client_payload: {
          niche: niche || '',
          topic: topic || ''
        }
      }),
    });

    if (response.status === 204) {
      return NextResponse.json({ success: true, message: 'Pipeline successfully triggered on GitHub Actions.' });
    } else {
      const errorText = await response.text();
      return NextResponse.json(
        { error: `GitHub API error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
