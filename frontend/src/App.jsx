import React, { useState, useEffect } from 'react';
import { TrendingUp, Zap, BrainCircuit, CheckCircle, X, Share2, Send, MessageSquare, Search, Command, ArrowRight } from 'lucide-react';
import { marked } from 'marked';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'sonner';

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
      if (!res.ok) throw new Error('Server Error');
      const data = await res.json();
      setBlogs(data);
    } catch (e) { 
      console.error('Failed to fetch blogs', e);
      toast.error("Failed to sync with neural nodes.");
    }
  };

  const startPolling = (taskId) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/status/${taskId}`);
        if (!res.ok) return;
        const data = await res.json();
        
        if (data.status === 'completed') {
          clearInterval(interval);
          localStorage.removeItem('active_task_id');
          setActiveTaskId(null);
          setIsProcessing(false);
          toast.success("Intelligence Report Synthesized!", {
             description: `Report for ${localStorage.getItem('active_task_ticker')} is now live.`
          });
          fetchBlogs();
        } else if (data.status === 'failed') {
          clearInterval(interval);
          localStorage.removeItem('active_task_id');
          setActiveTaskId(null);
          setIsProcessing(false);
          toast.error("Analysis Protocol Failed", {
            description: data.error || "Neural synthesis interrupted."
          });
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 5000);
  };

  const handleAnalyze = async () => {
    if (!ticker) return;
    setIsProcessing(true);
    toast.promise(
      fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: ticker.toUpperCase(), user_id: userId })
      }).then(async res => {
        if (!res.ok) throw new Error('API Rejection');
        const data = await res.json();
        setActiveTaskId(data.task_id);
        localStorage.setItem('active_task_id', data.task_id);
        localStorage.setItem('active_task_ticker', ticker.toUpperCase());
        startPolling(data.task_id);
        return data;
      }),
      {
        loading: 'Initiating Neural Synthesis...',
        success: (data) => `Protocol Active: ${ticker.toUpperCase()}`,
        error: 'Synthesis Request Denied.',
      }
    );
  };

  return (
    <div className="page-wrapper min-h-screen selection:bg-sky-500/30">
      <Toaster position="top-right" theme="dark" richColors closeButton />
      
      {/* Navigation */}
      <nav className="w-full glass sticky top-0 z-[100] px-8 py-5 border-b border-white/5">
        <div className="max-w-[1800px] mx-auto flex justify-between items-center">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-4"
          >
            <div className="w-11 h-11 bg-sky-500 rounded-xl flex items-center justify-center shadow-[0_0_30px_rgba(14,165,233,0.3)]">
              <TrendingUp className="text-black w-6 h-6" />
            </div>
            <h1 className="text-2xl font-black tracking-tighter uppercase cursor-pointer" onClick={() => window.location.reload()}>
              ECOTRON <span className="text-sky-500 text-glow-sky">TRADING</span>
            </h1>
          </motion.div>
          
          <div className="hidden md:flex items-center gap-8">
            <NavLink label="Neural Terminal" active />
            <NavLink label="Market Swarm" />
            <NavLink label="Research Node" />
          </div>

          <AnimatePresence>
            {(isProcessing || activeTaskId) && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-4 px-5 py-2.5 bg-sky-500/10 rounded-xl border border-sky-500/20"
              >
                <div className="w-2 h-2 bg-sky-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(14,165,233,0.8)]"></div>
                <span className="text-[10px] font-black uppercase text-sky-500 tracking-widest">Synthesis Active</span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </nav>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-[1800px] mx-auto w-full px-6 py-12 space-y-24"
      >
        
        {/* Top Section: Ads | Tool | Ads */}
        <div className="main-layout items-start gap-12">
          {/* Left Ads */}
          <aside className="space-y-6 hidden xl:block sticky top-32 w-[300px]">
            <AdContainer height="600px" width="300" label="Neural System Intelligence" adKey="419b347d315cd1215c1db06b7db000a5" />
            <AdContainer height="250px" width="300" label="Partner Protocol" adKey="d9b9196cf2814e58242076df2f21e5dc" />
          </aside>

          {/* Center: The Tool */}
          <main className="tool-section space-y-12 flex-grow max-w-[900px] mx-auto">
            <AdContainer height="90px" width="728" label="Network Sponsor" adKey="c25ecd0c0fe9d93f6cf66f0016cbd198" className="mx-auto" />
            
            <div className="glass-card relative overflow-hidden group min-h-[450px] flex items-center justify-center p-1 border-white/10">
              <div className="absolute inset-0 bg-gradient-to-br from-sky-500/5 to-transparent"></div>
              
              <AnimatePresence mode="wait">
                {!isProcessing ? (
                  <motion.div 
                    key="input"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 1.05 }}
                    className="relative z-10 w-full space-y-12 px-12"
                  >
                    <div className="text-center space-y-6">
                      <div className="inline-flex items-center gap-2 px-4 py-2 bg-sky-500/10 rounded-full border border-sky-500/20 mb-4">
                        <Command className="w-3 h-3 text-sky-500" />
                        <span className="text-[10px] font-black uppercase text-sky-400 tracking-[0.2em]">Deployment Terminal v4.2</span>
                      </div>
                      <h2 className="text-6xl font-black uppercase tracking-tighter leading-none">Neural Market <span className="text-sky-500 text-glow-sky">Search</span></h2>
                      <p className="text-slate-500 text-[11px] font-black uppercase tracking-[0.6em]">Deploy multi-agent expert systems for institutional research</p>
                    </div>

                    <div className="flex flex-col gap-6 max-w-2xl mx-auto">
                      <div className="relative group/input">
                        <div className="absolute -inset-1 bg-gradient-to-r from-sky-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-focus-within/input:opacity-100 transition duration-500"></div>
                        <div className="relative bg-black/60 rounded-2xl border border-white/5 group-focus-within/input:border-sky-500/50 transition-all">
                          <input 
                            value={ticker}
                            onChange={(e) => setTicker(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                            type="text" 
                            placeholder="ENTER ASSET TICKER..." 
                            className="w-full bg-transparent text-3xl font-black uppercase tracking-[0.2em] py-10 px-12 outline-none placeholder:text-slate-700"
                          />
                          <div className="absolute right-8 top-1/2 -translate-y-1/2 flex items-center gap-4">
                            <div className="text-slate-600 text-[10px] font-black tracking-widest hidden sm:block">PRESS ENTER ↵</div>
                            <BrainCircuit className="w-8 h-8 text-sky-500/40 group-focus-within/input:text-sky-500 group-focus-within/input:animate-pulse transition-all" />
                          </div>
                        </div>
                      </div>
                      <button 
                        onClick={handleAnalyze} 
                        disabled={!ticker}
                        className="btn-primary w-full flex items-center justify-center gap-4 group py-6 text-lg disabled:opacity-50 disabled:grayscale"
                      >
                        <span className="font-black uppercase tracking-widest">Initiate Neural Synthesis</span>
                        <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
                      </button>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div 
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center p-12 bg-black/40 backdrop-blur-2xl"
                  >
                    <div className="relative mb-12">
                      <motion.div 
                        animate={{ rotate: 360 }}
                        transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
                        className="absolute -inset-8 border-2 border-dashed border-sky-500/20 rounded-full"
                      ></motion.div>
                      <div className="absolute inset-0 bg-sky-500/40 blur-[120px] rounded-full animate-pulse"></div>
                      <div className="w-40 h-40 border-4 border-sky-500/10 border-t-sky-500 rounded-full animate-spin"></div>
                      <BrainCircuit className="w-20 h-20 text-sky-500 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
                    </div>
                    <h3 className="text-5xl font-black uppercase tracking-tighter mb-8 text-glow-sky">Synthesizing Intel</h3>
                    <div className="space-y-3">
                      <LoadingStep text="Gathering fundamental consensus" delay={0} />
                      <LoadingStep text="Analyzing technical divergence" delay={2} />
                      <LoadingStep text="Mapping sentiment velocity" delay={4} />
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </main>

          {/* Right Ads */}
          <aside className="space-y-6 hidden lg:block sticky top-32 w-[300px]">
            <AdContainer height="250px" width="300" label="Strategic Analytics" adKey="eca2cd8a7fd561c8d9ddc9b4e1302ac9" />
            <AdContainer height="600px" width="300" label="Global Neural Feed" adKey="419b347d315cd1215c1db06b7db000a5" />
          </aside>
        </div>

        {/* Bottom Section: Blogs (Full Width) */}
        <div className="space-y-16 pt-10">
          <div className="flex justify-between items-end border-b border-white/5 pb-10">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-1.5 h-6 bg-sky-500 rounded-full"></div>
                <h2 className="text-5xl font-black uppercase tracking-tighter">Global Intelligence <span className="text-sky-500 text-glow-sky">Feed</span></h2>
              </div>
              <p className="text-slate-500 text-[11px] font-black uppercase tracking-[0.5em] ml-5">Real-time research node throughput & historical synthesis</p>
            </div>
            <div className="flex flex-col items-end gap-3">
               <div className="flex items-center gap-4 px-6 py-3 bg-emerald-500/5 rounded-full border border-emerald-500/10">
                <div className="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-ping"></div>
                <span className="text-[11px] font-black text-emerald-500 uppercase tracking-widest">Nodes Synchronized</span>
              </div>
              <div className="relative group w-64">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input type="text" placeholder="FILTER FEED..." className="w-full bg-white/5 border border-white/5 rounded-xl py-3 pl-12 pr-4 text-[10px] font-black tracking-widest outline-none focus:border-sky-500/50 transition-all" />
              </div>
            </div>
          </div>
          
          <div className="feed-grid">
            <AnimatePresence>
              {blogs.map((blog, index) => (
                <BlogCard key={blog._id} blog={blog} index={index} />
              ))}
            </AnimatePresence>
          </div>
        </div>

      </motion.div>

      <Footer />
    </div>
  );
};

const LoadingStep = ({ text, delay }) => (
  <motion.div 
    initial={{ opacity: 0, x: -10 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay }}
    className="flex items-center justify-center gap-3 text-slate-400 text-[10px] font-black uppercase tracking-[0.3em]"
  >
    <div className="w-1 h-1 bg-sky-500 rounded-full animate-pulse"></div>
    <span>{text}...</span>
  </motion.div>
);

const NavLink = ({ label, active }) => (
  <a href="#" className={`group relative py-2 text-[11px] font-black uppercase tracking-[0.2em] transition-all hover:text-sky-400 ${active ? 'text-sky-500 text-glow-sky' : 'text-slate-500'}`}>
    {label}
    <div className={`absolute bottom-0 left-0 h-0.5 bg-sky-500 transition-all duration-300 ${active ? 'w-full' : 'w-0 group-hover:w-1/2'}`}></div>
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
    <motion.div 
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      className={`ad-native-container ${className}`} 
      style={{ height, width: width + 'px' }}
    >
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
    </motion.div>
  );
};

const BlogCard = ({ blog, index }) => {
  const decision = blog.decision.toUpperCase();
  let colorClass = 'text-sky-400 bg-sky-500/10 border-sky-500/20';
  let glowColor = 'rgba(14,165,233,0.3)';
  
  if (decision.includes('BUY')) {
    colorClass = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    glowColor = 'rgba(16,185,129,0.3)';
  }
  else if (decision.includes('HOLD')) {
    colorClass = 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    glowColor = 'rgba(245,158,11,0.3)';
  }
  else if (decision.includes('SELL')) {
    colorClass = 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    glowColor = 'rgba(244,63,94,0.3)';
  }

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ y: -8, transition: { duration: 0.2 } }}
      className="blog-card glass-card group cursor-pointer flex flex-col hover:border-sky-500/40 transition-all duration-300" 
      onClick={() => window.location.href = `/blog/${blog._id}`}
    >
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-3">
          <span className="px-4 py-1.5 bg-sky-500/10 rounded-xl text-[11px] font-black text-sky-500 uppercase tracking-widest border border-sky-500/20 shadow-[0_0_15px_rgba(14,165,233,0.1)]">{blog.ticker}</span>
          <div className="w-1 h-1 bg-slate-700 rounded-full"></div>
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Research ID: {blog._id.slice(-6)}</span>
        </div>
        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-tighter opacity-60">
          {new Date(blog.timestamp).toLocaleDateString()}
        </span>
      </div>
      <h3 className="text-3xl font-black leading-none mb-6 group-hover:text-sky-400 transition-colors uppercase tracking-tighter line-clamp-2 h-[4.5rem]">
        {blog.title}
      </h3>
      <div className="text-sm text-slate-400 mb-10 leading-relaxed opacity-70 line-clamp-4 flex-grow prose prose-invert prose-sm" dangerouslySetInnerHTML={{ __html: marked.parse(blog.summary) }} />
      <div className="flex items-center justify-between pt-8 border-t border-white/5">
        <div className="flex gap-3">
          <ShareBtn icon={<Send className="w-4 h-4" />} />
          <ShareBtn icon={<Share2 className="w-4 h-4" />} />
          <ShareBtn icon={<MessageSquare className="w-4 h-4" />} />
        </div>
        <motion.span 
          whileHover={{ scale: 1.05 }}
          className={`text-[11px] font-black uppercase px-6 py-3 rounded-2xl border tracking-[0.2em] shadow-lg ${colorClass}`}
          style={{ boxShadow: `0 0 20px ${glowColor}` }}
        >
          {blog.decision}
        </motion.span>
      </div>
    </motion.div>
  );
};

const ShareBtn = ({ icon }) => (
  <button className="w-10 h-10 flex items-center justify-center rounded-2xl bg-white/5 text-slate-400 hover:bg-sky-500/20 hover:text-sky-400 hover:border-sky-500/30 border border-transparent transition-all">
    {icon}
  </button>
);

const Footer = () => (
  <footer className="w-full glass py-32 mt-20 border-t border-white/5 flex flex-col items-center gap-20 text-center px-10 relative overflow-hidden">
    <div className="absolute inset-0 bg-sky-500/[0.03] blur-[150px] rounded-full translate-y-1/2"></div>
    <AdContainer height="90px" width="728" label="Infrastructure Sponsor" adKey="c25ecd0c0fe9d93f6cf66f0016cbd198" />
    <div className="max-w-4xl w-full space-y-12">
      <div className="flex items-center justify-center gap-8 opacity-20 grayscale hover:grayscale-0 transition-all duration-700">
        <TrendingUp className="w-10 h-10" />
        <BrainCircuit className="w-10 h-10" />
        <Zap className="w-10 h-10" />
      </div>
      <p className="text-slate-600 text-[11px] font-black uppercase tracking-[0.6em]">Neural Grid Protocol v4.2.0 • Established 2024</p>
      <p className="text-slate-500 text-xs font-medium max-w-2xl mx-auto leading-relaxed opacity-60">
        &copy; 2026 Ecotron Advanced Trading Systems. Proprietary multi-agent quantitative frameworks. 
        Market analysis provided for institutional research synthesis only. All intelligence generated by decentralized neural nodes.
      </p>
    </div>
  </footer>
);

export default App;
