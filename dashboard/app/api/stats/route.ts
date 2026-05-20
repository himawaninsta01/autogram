import { NextResponse } from 'next/server';
import { supabase } from '../../../lib/supabase';

export async function GET() {
  try {
    const { data: posts, error } = await supabase
      .from('posts')
      .select('status, qa_score, niche');

    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }

    const total = posts?.length || 0;
    const posted = posts?.filter(p => p.status === 'posted').length || 0;
    const successRate = total > 0 ? (posted / total) * 100 : 0;

    const qaScores = posts?.filter(p => p.qa_score !== null && p.qa_score !== undefined).map(p => p.qa_score) || [];
    const avgQaScore = qaScores.length > 0 ? qaScores.reduce((a, b) => a + b, 0) / qaScores.length : 0;

    // Distribution by niche
    const niches: Record<string, number> = {};
    posts?.forEach(p => {
      if (p.niche) {
        niches[p.niche] = (niches[p.niche] || 0) + 1;
      }
    });

    return NextResponse.json({
      total,
      posted,
      successRate: parseFloat(successRate.toFixed(1)),
      avgQaScore: parseFloat(avgQaScore.toFixed(1)),
      niches,
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
