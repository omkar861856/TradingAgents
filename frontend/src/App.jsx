import React, { useState, useEffect } from 'react';
import { TrendingUp, Zap, BrainCircuit, CheckCircle, X, Share2, Twitter, Facebook, MessageSquare } from 'lucide-react';
import { marked } from 'marked';

const App = () => {
  const [ticker, setTicker] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [blogs, setBlogs] = useState([]);
  const [activeTaskId, setActiveTaskId] = useState(localStorage.getItem('active_task_id'));
  const [userId] = useState(() => {
    let id = localStorage.getItem('trading_user_id');
    if (!id) {
      id = 'u_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('trading_user_id', id);
    }
    return id;
  });

  useEffect(() => {
    fetchBlogs();
    if (activeTaskId) startPolling(activeTaskId);
  }, []);

  const fetchBlogs = async () => {
    try {
      const res = await fetch('/blogs');
      const data = await res.json();
      setBlogs(data);
    } catch (e) { console.error('Failed to fetch blogs', e); }
  };

  const startPolling = (taskId) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/status/${taskId}`);
        const data = await res.json();
        
        if (data.status === 'completed') {
          clearInterval(interval);
          localStorage.removeItem('active_task_id');
          setActiveTaskId(null);
          setIsProcessing(false);
          fetchBlogs();
        } else if (data.status === 'failed') {
          clearInterval(interval);
          localStorage.removeItem('active_task_id');
          setActiveTaskId(null);
          setIsProcessing(false);
          alert("Analysis failed.");
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 5000);
  };

  const handleAnalyze = async () => {
    if (!ticker) return;
    setIsProcessing(true);
    try {
      const response = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: ticker.toUpperCase(), user_id: userId })
      });
      const { task_id } = await response.json();
      setActiveTaskId(task_id);
      localStorage.setItem('active_task_id', task_id);
      localStorage.setItem('active_task_ticker', ticker.toUpperCase());
      startPolling(task_id);
    } catch (e) { setIsProcessing(false); }
  };

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="w-full glass sticky top-0 z-[100] px-10 py-6 border-b border-white/5">
        <div className="max-w-[1800px] mx-auto flex justify-between items-center">
          <div className="flex items-center gap-5">
            <div className="w-12 h-12 bg-sky-500 rounded-2xl flex items-center justify-center shadow-[0_0_40px_rgba(14,165,233,0.3)]">
              <TrendingUp className="text-black w-7 h-7" />
            </div>
            <h1 className="text-3xl font-black tracking-tighter uppercase cursor-pointer">
              ECOTRON <span className="text-sky-500 text-glow-sky">TRADING</span>
            </h1>
          </div>
          {(isProcessing || activeTaskId) && (
            <div className="flex items-center gap-4 px-6 py-3 bg-sky-500/10 rounded-2xl border border-sky-500/20 animate-pulse">
              <div className="w-2.5 h-2.5 bg-sky-500 rounded-full"></div>
              <span className="text-[11px] font-black uppercase text-sky-500 tracking-[0.2em]">Neural Nodes Active</span>
            </div>
          )}
        </div>
      </header>

      <div className="app-container mt-10 pb-20">
        {/* Left Sidebar */}
        <aside className="ad-left hidden xl:block space-y-8">
          <AdContainer height="600px" label="Neural Network Sponsor" adKey="419b347d315cd1215c1db06b7db000a5" width="160" />
          <AdContainer height="250px" label="Partner Intelligence" adKey="d9b9196cf2814e58242076df2f21e5dc" width="160" />
        </aside>

        <main className="main-content">
          <AdContainer height="60px" width="468" label="Network Protocol Ad" adKey="d9b9196cf2814e58242076df2f21e5dc" className="mx-auto mb-12" />

          {/* Search Section */}
          <div className="glass-card relative overflow-hidden group">
            <div className={`relative z-10 space-y-10 ${isProcessing ? 'opacity-0' : 'opacity-100'} transition-opacity duration-500`}>
              <div className="text-center">
                <h2 className="text-5xl font-black uppercase tracking-tighter mb-3">Neural Market <span className="text-sky-500 text-glow-sky">Search</span></h2>
                <p className="text-slate-500 text-[11px] font-black uppercase tracking-[0.4em]">Deploy multi-agent expert systems for any ticker</p>
              </div>
              <div className="flex flex-col md:flex-row gap-5 max-w-4xl mx-auto">
                <input 
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value)}
                  type="text" 
                  placeholder="ENTER TICKER (E.G. NVDA, BTC, AAPL)" 
                  className="input-neural flex-grow text-xl font-black uppercase tracking-widest py-6"
                />
                <button onClick={handleAnalyze} className="btn-primary flex items-center justify-center gap-3">
                  <span>Initiate Neural Scan</span>
                  <Zap className="w-4 h-4" />
                </button>
              </div>
            </div>

            {isProcessing && (
              <div className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center p-12 bg-black/20 backdrop-blur-md">
                <div className="relative mb-8">
                  <div className="absolute inset-0 bg-sky-500/20 blur-3xl rounded-full animate-pulse"></div>
                  <BrainCircuit className="w-24 h-24 text-sky-500 relative z-10" />
                </div>
                <h3 className="text-3xl font-black uppercase tracking-tighter mb-4 text-glow-sky">Neural Synthesis in Progress</h3>
                <p className="text-slate-400 text-sm max-w-lg mx-auto leading-relaxed font-medium">
                  Our multi-agent network is debating technicals, sentiment, and fundamentals. 
                  <span className="text-sky-400 font-bold block mt-2">Research reports finalize in 60-90 seconds.</span>
                </p>
              </div>
            )}
          </div>

          {/* Feed Section */}
          <div className="pt-10">
            <div className="flex justify-between items-end mb-10">
              <h2 className="text-3xl font-black uppercase tracking-tighter">Global Intelligence <span className="text-sky-500 text-glow-sky">Feed</span></h2>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-ping"></div>
                <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Real-time Research Node</span>
              </div>
            </div>
            <div className="feed-grid">
              {blogs.map(blog => (
                <BlogCard key={blog._id} blog={blog} />
              ))}
            </div>
          </div>
        </main>

        {/* Right Sidebar */}
        <aside className="ad-right hidden lg:block space-y-8">
          <AdContainer height="250px" width="300" label="Neural Protocol Insight" adKey="eca2cd8a7fd561c8d9ddc9b4e1302ac9" />
          <AdContainer height="600px" width="300" label="Strategic Partner" adKey="419b347d315cd1215c1db06b7db000a5" />
        </aside>
      </div>

      <Footer />
    </div>
  );
};

const AdContainer = ({ height, width, label, adKey, className = "" }) => {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = `https://developdomicile.com/${adKey}/invoke.js`;
    script.async = true;
    const atOptions = {
      'key': adKey,
      'format': 'iframe',
      'height': parseInt(height),
      'width': parseInt(width),
      'params': {}
    };
    // Note: Social ads like these often rely on global variables. 
    // In a real React app, you'd use a safer integration, but for this MVP we'll inject.
    window.atOptions = atOptions;
    document.body.appendChild(script);
    return () => { document.body.removeChild(script); };
  }, [adKey, height, width]);

  return (
    <div className={`ad-native-container ${className}`} style={{ height, width: width + 'px' }}>
      <span className="ad-label">{label}</span>
      <div id={`ad-${adKey}`}></div>
    </div>
  );
};

const BlogCard = ({ blog }) => {
  const decision = blog.decision.toUpperCase();
  let color = 'sky';
  if (decision.includes('BUY')) color = 'emerald';
  else if (decision.includes('HOLD')) color = 'amber';
  else if (decision.includes('SELL')) color = 'rose';

  return (
    <div className="blog-card glass-card group cursor-pointer" onClick={() => window.location.href = `/blog/${blog._id}`}>
      <div className="flex justify-between items-center mb-6">
        <span className="px-3 py-1 bg-sky-500/10 rounded-lg text-[10px] font-black text-sky-500 uppercase tracking-widest border border-sky-500/20">{blog.ticker}</span>
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter opacity-60">
          {new Date(blog.timestamp).toLocaleDateString()}
        </span>
      </div>
      <h3 className="text-xl font-black leading-tight mb-5 group-hover:text-sky-400 transition-colors uppercase tracking-tight line-clamp-2 h-[3.5rem]">
        {blog.title}
      </h3>
      <div className="text-xs text-slate-400 mb-6 leading-relaxed opacity-80 line-clamp-4" dangerouslySetInnerHTML={{ __html: marked.parse(blog.summary) }} />
      <div className="flex items-center justify-between pt-6 border-t border-white/5">
        <div className="flex gap-3">
          <ShareBtn icon={<Twitter className="w-4 h-4" />} />
          <ShareBtn icon={<Facebook className="w-4 h-4" />} />
          <ShareBtn icon={<MessageSquare className="w-4 h-4" />} />
        </div>
        <span className={`text-[10px] font-black uppercase text-${color}-400 px-3 py-1.5 bg-${color}-500/10 rounded-lg border border-${color}-500/20 tracking-[0.1em]`}>
          {blog.decision}
        </span>
      </div>
    </div>
  );
};

const ShareBtn = ({ icon }) => (
  <button className="w-8 h-8 flex items-center justify-center rounded-lg bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white transition-all">
    {icon}
  </button>
);

const Footer = () => (
  <footer className="w-full glass py-24 mt-20 border-t border-white/5 flex flex-col items-center gap-16 text-center px-10 relative overflow-hidden">
    <div className="absolute inset-0 bg-sky-500/[0.02] blur-3xl rounded-full translate-y-1/2"></div>
    <AdContainer height="90px" width="728" label="Neural Grid Sponsor" adKey="c25ecd0c0fe9d93f6cf66f0016cbd198" />
    <div className="max-w-4xl w-full space-y-8">
      <p className="text-slate-700 text-[10px] font-black uppercase tracking-[0.3em]">Neural Architecture v4.0</p>
      <p className="text-slate-500 text-xs font-medium max-w-2xl mx-auto">&copy; 2026 Ecotron Advanced Trading Systems. All rights reserved. Quantitative multi-agent frameworks are for informational purposes only.</p>
    </div>
  </footer>
);

export default App;
