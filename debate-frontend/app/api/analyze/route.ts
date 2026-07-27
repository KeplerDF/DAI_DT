import { NextResponse } from 'next/server';
import { YoutubeTranscript } from 'youtube-transcript';
import axios from 'axios';

export async function POST(req: Request) {
  try {
    const { url } = await req.json();

    if (!url) {
      return NextResponse.json({ error: 'YouTube URL is required' }, { status: 400 });
    }

    // 1. Fetch transcript on Node server (bypasses browser CORS)
    const rawTranscript = await YoutubeTranscript.fetchTranscript(url);

    // 2. Format entries with timestamps
    const formattedTranscript = rawTranscript
      .map((item) => {
        const startSec = Math.floor(item.offset / 1000);
        const minutes = Math.floor(startSec / 60);
        const seconds = startSec % 60;
        const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        return `[${timeStr}] ${item.text.replace(/\n/g, ' ')}`;
      })
      .join('\n');

    // 3. Forward to Render backend
    const renderResponse = await axios.post('https://dai-dt.onrender.com/analyze-debate', {
      youtube_url: url,
      transcript_text: formattedTranscript,
    });

    return NextResponse.json(renderResponse.data);
  } catch (error: any) {
    console.error('API Error:', error);
    return NextResponse.json(
      { error: error?.response?.data?.detail || error.message || 'Failed to fetch transcript' },
      { status: 500 }
    );
  }
}