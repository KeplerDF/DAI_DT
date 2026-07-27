'use client';

import { useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { Loader2, Award, Scale, AlertTriangle, MessageSquare } from 'lucide-react';
import { YoutubeTranscript } from 'youtube-transcript';

// Color palette for charts
const COLORS = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6'];

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');

  // Progress Bar States
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState('');

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setProgress(5);
    setStatusMessage('Extracting YouTube transcript...');

    // Dynamic progress bar updates during request execution
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev < 30) {
          setStatusMessage('Parsing dialogue & timestamps...');
          return prev + 5;
        } else if (prev < 70) {
          setStatusMessage('Running Gemini debate scoring model...');
          return prev + 3;
        } else if (prev < 92) {
          setStatusMessage('Calculating fallacies & net scores...');
          return prev + 1;
        }
        return prev;
      });
    }, 400);

    try {
      // 1. Fetch transcript directly in the browser
      setStatusMessage('Extracting YouTube transcript...');
      const rawTranscript = await YoutubeTranscript.fetchTranscript(url);

      // 2. Format transcript entries with timestamps
      const formattedTranscript = rawTranscript.map(item => {
        const startSec = Math.floor(item.offset / 1000);
        const minutes = Math.floor(startSec / 60);
        const seconds = startSec % 60;
        const timeStr = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        return `[${timeStr}] ${item.text.replace(/\n/g, ' ')}`;
      }).join('\n');

      // 3. Send both URL and transcript_text to your Render backend
      const response = await axios.post('https://dai-dt.onrender.com/analyze-debate', {
        youtube_url: url,
        transcript_text: formattedTranscript
      });

      // Save returned analysis data into state
      setData(response.data);

    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.response?.data?.error || err.message || 'Failed to analyze debate.');
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <div className="max-w-6xl mx-auto space-y-8">

        {/* Header & Input Form */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            Debate Analytics Dashboard
          </h1>
          <p className="text-slate-400">
            Paste a YouTube debate URL to analyze arguments, fallacies, talk times, and integrity ratios.
          </p>

          <form onSubmit={handleAnalyze} className="flex gap-3 max-w-2xl mx-auto">
            <input
              type="text"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-medium px-6 py-3 rounded-lg flex items-center justify-center transition-all min-w-[120px]"
            >
              {loading ? <Loader2 className="animate-spin w-5 h-5" /> : 'Analyze'}
            </button>
          </form>

          {/* Animated Progress Bar */}
          {loading && (
            <div className="max-w-2xl mx-auto mt-6 bg-slate-800 border border-slate-700 rounded-xl p-5 shadow-lg text-left space-y-3">
              <div className="flex justify-between items-center text-sm font-medium">
                <span className="text-blue-400 flex items-center gap-2">
                  <Loader2 className="animate-spin w-4 h-4" />
                  {statusMessage}
                </span>
                <span className="text-slate-400 font-mono">{progress}%</span>
              </div>

              {/* Progress Track */}
              <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-700/50 relative">
                <div
                  className="bg-gradient-to-r from-blue-600 via-indigo-500 to-cyan-400 h-full rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
        </div>

        {/* Dashboard Results Display */}
        {data && (
          <div className="space-y-8">

            {/* Top Grid: Speaker Cards & Talk Time Pie Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* Speaker Stats Cards */}
              <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.speakers.map((speaker: any, index: number) => (
                  <div key={index} className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-semibold text-white">{speaker.speaker_id}</h3>
                        <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">{speaker.affiliation}</span>
                      </div>
                      <span className={`text-2xl font-bold ${speaker.metrics.net_score >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {speaker.metrics.net_score > 0 ? `+${speaker.metrics.net_score}` : speaker.metrics.net_score}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                        <span className="text-slate-400 text-xs block">Integrity Ratio</span>
                        <span className="font-semibold text-blue-400">{speaker.metrics.integrity_ratio.toFixed(1)}%</span>
                      </div>
                      <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                        <span className="text-slate-400 text-xs block">Talk Time</span>
                        <span className="font-semibold text-slate-200">{speaker.talk_time_percentage.toFixed(1)}%</span>
                      </div>
                      <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                        <span className="text-slate-400 text-xs block">Logical Points (L)</span>
                        <span className="font-semibold text-green-400">+{speaker.metrics.logical_points_L}</span>
                      </div>
                      <div className="bg-slate-900/60 p-2 rounded border border-slate-800">
                        <span className="text-slate-400 text-xs block">Fallacies (F)</span>
                        <span className="font-semibold text-red-400">-{speaker.metrics.fallacies_F}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Talk Time Chart */}
              <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 flex flex-col items-center justify-center">
                <h3 className="text-md font-semibold mb-2">Talk Time Distribution</h3>
                <div className="w-full h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={data.speakers}
                        dataKey="talk_time_seconds"
                        nameKey="speaker_id"
                        cx="50%"
                        cy="50%"
                        outerRadius={70}
                      >
                        {data.speakers.map((_: any, idx: number) => (
                          <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#1E293B', borderColor: '#334155', color: '#FFF' }}
                        formatter={(value: any) => [`${Math.round(value as number / 60)} mins`, 'Talk Time']}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Transcript Score Ledger */}
            <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-4">
              <h3 className="text-xl font-bold text-white">Argument Ledger & Timeline</h3>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="text-xs uppercase bg-slate-900/80 text-slate-400 border-b border-slate-700">
                    <tr>
                      <th className="p-3">Time</th>
                      <th className="p-3">Speaker</th>
                      <th className="p-3">Category</th>
                      <th className="p-3">Quote / Impact</th>
                      <th className="p-3 text-right">Points</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-700/50">
                    {data.transcript_ledger.map((item: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-700/30">
                        <td className="p-3 font-mono text-xs text-blue-400">{item.timestamp}</td>
                        <td className="p-3 font-medium text-white">{item.speaker}</td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded text-xs font-semibold ${
                            item.score_change > 0 ? 'bg-green-950 text-green-300 border border-green-800' : 'bg-red-950 text-red-300 border border-red-800'
                          }`}>
                            {item.category}
                          </span>
                        </td>
                        <td className="p-3 max-w-md">
                          <p className="text-slate-200 italic font-serif">"{item.quote}"</p>
                          <p className="text-xs text-slate-400 mt-1">{item.impact_explanation}</p>
                        </td>
                        <td className={`p-3 text-right font-mono font-bold ${item.score_change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {item.score_change > 0 ? `+${item.score_change}` : item.score_change}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

      </div>
    </main>
  );
}