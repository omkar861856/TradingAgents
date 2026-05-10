import React, { useState, useEffect } from 'react';
import { TrendingUp, Zap, BrainCircuit, CheckCircle, X, Share2, Send, MessageSquare } from 'lucide-react';
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
    <div className="page-wrapper min-h-screen">
      {/* Navigation */}
      <nav className="w-full glass sticky top-0 z-[100] px-8 py-5 border-b border-white/5">
        <div className="max-w-[1800px] mx-auto flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 bg-sky-500 rounded-xl flex items-center justify-center shadow-[0_0_30px_rgba(14,165,233,0.3)]">
              <TrendingUp className="text-black w-6 h-6" />
            </div>
            <h1 className="text-2xl font-black tracking-tighter uppercase cursor-pointer">
              ECOTRON <span className="text-sky-500 text-glow-sky">TRADING</span>
            </h1>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <NavLink label="Neural Terminal" active />
            <NavLink label="Market Swarm" />
            <NavLink label="Research Node" />
          </div>
          {(isProcessing || activeTaskId) && (
            <div className="flex items-center gap-4 px-5 py-2.5 bg-sky-500/10 rounded-xl border border-sky-500/20 animate-pulse">
              <div className="w-2 h-2 bg-sky-500 rounded-full"></div>
              <span className="text-[10px] font-black uppercase text-sky-500 tracking-widest">Synthesis Active</span>
            </div>
          )}
        </div>
      </nav>

      {/* Main Container */}
      <div className="max-w-[1800px] mx-auto w-full px-6 py-12 space-y-20">
        
        {/* Top Section: Ads | Tool | Ads */}
        <div className="main-layout items-start">
          {/* Left Ads */}
          <aside className="space-y-6 hidden xl:block sticky top-32">
            <AdContainer height="600px" width="300" label="Neural System Intelligence" adKey="419b347d315cd1215c1db06b7db000a5" />
            <AdContainer height="250px" width="300" label="Partner Protocol" adKey="d9b9196cf2814e58242076df2f21e5dc" />
          </aside>

          {/* Center: The Tool */}
          <main className="tool-section space-y-12">
            <AdContainer height="90px" width="728" label="Network Sponsor" adKey="c25ecd0c0fe9d93f6cf66f0016cbd198" className="mx-auto" />
            
            <div className="glass-card relative overflow-hidden group min-h-[400px] flex items-center justify-center">
              <div className={`relative z-10 w-full space-y-10 px-8 ${isProcessing ? 'opacity-0 scale-95' : 'opacity-100 scale-100'} transition-all duration-700`}>
                <div className="text-center space-y-4">
                  <h2 className="text-5xl font-black uppercase tracking-tighter">Neural Market <span className="text-sky-500 text-glow-sky">Search</span></h2>
                  <p className="text-slate-500 text-[11px] font-black uppercase tracking-[0.5em]">Deploy multi-agent expert systems for institutional research</p>
                </div>
                <div className="flex flex-col gap-4 max-w-3xl mx-auto">
                  <div className="relative group/input">
                    <input 
                      value={ticker}
                      onChange={(e) => setTicker(e.target.value)}
                      type="text" 
                      placeholder="ENTER TICKER SYMBOL..." 
                      className="input-neural text-2xl font-black uppercase tracking-widest py-8"
                    />
                    <div className="absolute right-4 top-1/2 -translate-y-1/2 opacity-20 group-focus-within/input:opacity-100 transition-opacity">
                      <BrainCircuit className="w-8 h-8 text-sky-500" />
                    </div>
                  </div>
                  <button onClick={handleAnalyze} className="btn-primary w-full flex items-center justify-center gap-4 group">
                    <span className="text-sm">Initiate Neural Synthesis</span>
                    <Zap className="w-5 h-5 group-hover:scale-125 transition-transform" />
                  </button>
                </div>
              </div>

              {isProcessing && (
                <div className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center p-12 bg-black/40 backdrop-blur-xl">
                  <div className="relative mb-10">
                    <div className="absolute inset-0 bg-sky-500/30 blur-[100px] rounded-full animate-pulse"></div>
                    <div className="w-32 h-32 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin"></div>
                    <BrainCircuit className="w-16 h-16 text-sky-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <h3 className="text-4xl font-black uppercase tracking-tighter mb-6 text-glow-sky">Synthesizing Intel</h3>
                  <div className="flex flex-col gap-2 text-slate-400 text-xs font-black uppercase tracking-widest">
                    <span>Gathering fundamental consensus...</span>
                    <span>Analyzing technical divergence...</span>
                    <span>Mapping sentiment velocity...</span>
                  </div>
                </div>
              )}
            </div>
          </main>

          {/* Right Ads */}
          <aside className="space-y-6 hidden lg:block sticky top-32">
            <AdContainer height="250px" width="300" label="Strategic Analytics" adKey="eca2cd8a7fd561c8d9ddc9b4e1302ac9" />
            <AdContainer height="600px" width="300" label="Global Neural Feed" adKey="419b347d315cd1215c1db06b7db000a5" />
          </aside>
        </div>

        {/* Bottom Section: Blogs (Full Width) */}
        <div className="space-y-12 pt-10">
          <div className="flex justify-between items-end border-b border-white/5 pb-8">
            <div className="space-y-2">
              <h2 className="text-4xl font-black uppercase tracking-tighter">Global Intelligence <span className="text-sky-500 text-glow-sky">Feed</span></h2>
              <p className="text-slate-500 text-[10px] font-black uppercase tracking-[0.4em]">Real-time research node throughput</p>
            </div>
            <div className="flex items-center gap-4 px-4 py-2 glass rounded-full">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-ping"></div>
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Active Stream</span>
            </div>
          </div>
          
          <div className="feed-grid">
            {blogs.map(blog => (
              <BlogCard key={blog._id} blog={blog} />
            ))}
          </div>
        </div>

      </div>

      <Footer />
    </div>
  );
};

const NavLink = ({ label, active }) => (
  <a href="#" className={`text-[11px] font-black uppercase tracking-[0.2em] transition-all hover:text-sky-400 ${active ? 'text-sky-500 text-glow-sky' : 'text-slate-500'}`}>
    {label}
  </a>
);

const AdContainer = ({ height, width, label, adKey, className = "" }) => {
  const iframeRef = React.useRef(null);

  useEffect(() => {
    if (iframeRef.current) {
      const doc = iframeRef.current.contentDocument || iframeRef.current.contentWindow.document;
      doc.open();
      doc.write(`
        <html>
          <body style="margin:0; padding:0; overflow:hidden; background:transparent;">
            <script type="text/javascript">
              atOptions = {
                'key' : '${adKey}',
                'format' : 'iframe',
                'height' : ${height.replace('px', '')},
                'width' : ${width},
                'params' : {}
              };
            </script>
            <script type="text/javascript" src="//developdomicile.com/${adKey}/invoke.js"></script>
          </body>
        </html>
      `);
      doc.close();
    }
  }, [adKey, height, width]);

  return (
    <div className={`ad-native-container ${className}`} style={{ height, width: width + 'px' }}>
      <span className="ad-label">{label}</span>
      <iframe
        ref={iframeRef}
        title={`ad-${adKey}`}
        width={width}
        height={height.replace('px', '')}
        frameBorder="0"
        scrolling="no"
        style={{ border: 'none', overflow: 'hidden', background: 'transparent' }}
      ></iframe>
    </div>
  );
};

const BlogCard = ({ blog }) => {
  const decision = blog.decision.toUpperCase();
  let colorClass = 'text-sky-400 bg-sky-500/10 border-sky-500/20';
  if (decision.includes('BUY')) colorClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  else if (decision.includes('HOLD')) colorClass = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
  else if (decision.includes('SELL')) colorClass = 'text-rose-400 bg-rose-500/10 border-rose-500/20';

  return (
    <div className="blog-card glass-card group cursor-pointer flex flex-col" onClick={() => window.location.href = `/blog/${blog._id}`}>
      <div className="flex justify-between items-center mb-6">
        <span className="px-3 py-1 bg-sky-500/10 rounded-lg text-[10px] font-black text-sky-500 uppercase tracking-widest border border-sky-500/20">{blog.ticker}</span>
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter opacity-60">
          {new Date(blog.timestamp).toLocaleDateString()}
        </span>
      </div>
      <h3 className="text-2xl font-black leading-tight mb-5 group-hover:text-sky-400 transition-colors uppercase tracking-tighter line-clamp-2 h-[4rem]">
        {blog.title}
      </h3>
      <div className="text-sm text-slate-400 mb-8 leading-relaxed opacity-80 line-clamp-4 flex-grow" dangerouslySetInnerHTML={{ __html: marked.parse(blog.summary) }} />
      <div className="flex items-center justify-between pt-6 border-t border-white/5">
        <div className="flex gap-2">
          <ShareBtn icon={<Send className="w-4 h-4" />} />
          <ShareBtn icon={<Share2 className="w-4 h-4" />} />
          <ShareBtn icon={<MessageSquare className="w-4 h-4" />} />
        </div>
        <span className={`text-[10px] font-black uppercase px-4 py-2 rounded-xl border tracking-[0.15em] ${colorClass}`}>
          {blog.decision}
        </span>
      </div>
    </div>
  );
};

const ShareBtn = ({ icon }) => (
  <button className="w-9 h-9 flex items-center justify-center rounded-xl bg-white/5 text-slate-400 hover:bg-white/10 hover:text-sky-400 hover:border-sky-500/30 border border-transparent transition-all">
    {icon}
  </button>
);

const Footer = () => (
  <footer className="w-full glass py-32 mt-20 border-t border-white/5 flex flex-col items-center gap-20 text-center px-10 relative overflow-hidden">
    <div className="absolute inset-0 bg-sky-500/[0.03] blur-[150px] rounded-full translate-y-1/2"></div>
    <AdContainer height="90px" width="728" label="Infrastructure Sponsor" adKey="c25ecd0c0fe9d93f6cf66f0016cbd198" />
    <div className="max-w-4xl w-full space-y-10">
      <div className="flex items-center justify-center gap-6 opacity-30 grayscale hover:grayscale-0 transition-all">
        <TrendingUp className="w-8 h-8" />
        <BrainCircuit className="w-8 h-8" />
        <Zap className="w-8 h-8" />
      </div>
      <p className="text-slate-600 text-[10px] font-black uppercase tracking-[0.5em]">Neural Grid Protocol v4.2.0</p>
      <p className="text-slate-500 text-xs font-medium max-w-2xl mx-auto leading-relaxed">
        &copy; 2026 Ecotron Advanced Trading Systems. Proprietary multi-agent quantitative frameworks. 
        Market analysis provided for institutional research synthesis only.
      </p>
    </div>
  </footer>
);

export default App;
