import React, { useState, useEffect, useRef } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useParams, Link } from 'react-router-dom';
import { TrendingUp, Zap, BrainCircuit, CheckCircle, X, Share2, Send, MessageSquare, Search, Command, ArrowRight, Layers, Layout, ChevronLeft, ChevronDown } from 'lucide-react';
import { marked } from 'marked';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'sonner';

// --- Shared Layout Components ---

const TRANSHUMAN_ICONS = [
  "Astro.svg", "Bueno.svg", "Chaotic Good.svg", "Chillin.svg", "Chilly.svg", "Coffee.svg", 
  "Consumer.svg", "Cube Leg.svg", "Ecto Plasma.svg", "Entertainment.svg", "Experiments.svg", 
  "Feliz.svg", "Fling.svg", "Gamestation.svg", "Groceries.svg", "Growth.svg", "Jumping.svg", 
  "Kiddo.svg", "Late for Class.svg", "Looking Ahead.svg", "Mask.svg", "Mechanical Love.svg", 
  "Meela Pantalones.svg", "New Beginnings.svg", "Pacheco.svg", "Pilot.svg", "Plants.svg", 
  "Polka Pup.svg", "Pondering.svg", "Puppy.svg", "Reflecting.svg", "Roboto.svg", "Rogue.svg", 
  "Runner.svg", "Waiting.svg", "Walking Contradiction.svg", "Whoa.svg", "Wont Stop.svg"
];

const Navigation = ({ isProcessing, activeTaskId }) => (
  <nav className="w-full glass sticky top-0 z-[100] px-8 py-5 border-b-4 border-black">
    <div className="max-w-[1800px] mx-auto flex justify-between items-center">
      <Link to="/" className="flex items-center gap-6 group">
        <div className="w-14 h-14 bg-white p-1 flex items-center justify-center shadow-[4px_4px_0px_#000000] group-hover:translate-x-1 group-hover:translate-y-1 group-hover:shadow-none transition-all border-2 border-black">
          <img src="/transhumans art/SVG/Pilot.svg" alt="Ecotron Logo" className="w-12 h-12" />
        </div>
        <h1 className="text-3xl font-black tracking-tighter uppercase text-black">
          ECOTRON <span className="text-black">TRADING</span>
        </h1>
      </Link>
      

      <AnimatePresence>
        {(isProcessing || activeTaskId) && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="flex items-center gap-4 px-5 py-2.5 bg-black/5 rounded-xl border border-black/10"
          >
            <div className="w-2 h-2 bg-black rounded-full animate-pulse"></div>
            <span className="text-[10px] font-black uppercase text-black tracking-widest">Synthesis Active</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  </nav>
);

const NavLink = ({ label, to }) => (
  <Link to={to} className="group relative py-2 text-[12px] font-black uppercase tracking-[0.3em] transition-all text-white/60 hover:text-white">
    {label}
    <div className="absolute -bottom-1 left-0 h-1 bg-white w-0 group-hover:w-full transition-all duration-200"></div>
  </Link>
);

const SidebarAd = ({ height, width, label, adKey, isNative }) => {
  const iframeRef = useRef(null);

  useEffect(() => {
    if (iframeRef.current && !isNative) {
      const doc = iframeRef.current.contentDocument || iframeRef.current.contentWindow.document;
      doc.open();
      doc.write(`
        <html>
          <body style="margin:0; padding:0; overflow:hidden; background:transparent;">
            <script type="text/javascript">
              atOptions = { 'key' : '${adKey}', 'format' : 'iframe', 'height' : ${height.replace('px', '')}, 'width' : ${width}, 'params' : {} };
            </script>
            <script type="text/javascript" src="//developdomicile.com/${adKey}/invoke.js"></script>
          </body>
        </html>
      `);
      doc.close();
    }
  }, [adKey, height, width, isNative]);

  if (isNative) {
    return (
      <div className="ad-native-container w-full min-h-[150px] p-6 flex flex-col items-center gap-4">
        <span className="ad-label">{label}</span>
        <div id={`container-${adKey}`} className="w-full">
           <script async="async" data-cfasync="false" src={`https://developdomicile.com/${adKey}/invoke.js`}></script>
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      className="ad-native-container sticky top-32 flex-shrink-0 mx-auto" 
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

const PageLayout = ({ children, isProcessing, activeTaskId }) => (
  <div className="page-wrapper min-h-screen selection:bg-white selection:text-black">
    <Navigation isProcessing={isProcessing} activeTaskId={activeTaskId} />
    
    <div className="max-w-[1800px] mx-auto w-full px-6 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-[180px_1fr_180px] gap-12 items-start">
        {/* Left Sidebar - Sticky Stack */}
        <aside className="hidden lg:flex flex-col gap-12 sticky top-32">
          <SidebarAd height="600px" width="160" label="GRID_UPLINK" adKey="419b347d315cd1215c1db06b7db000a5" />
          <SidebarAd isNative adKey="bc5972dfd55ab0a5e10b6ee43572241a" label="NEURAL_SPONSOR" />
        </aside>

        {/* Center Content */}
        <main className="w-full min-w-0">
          {children}
        </main>

        {/* Right Sidebar - Sticky Stack */}
        <aside className="hidden lg:flex flex-col gap-12 sticky top-32">
          <SidebarAd height="600px" width="160" label="INSTITUTIONAL_ADS" adKey="419b347d315cd1215c1db06b7db000a5" />
        </aside>
      </div>
    </div>

    <Footer />
  </div>
);

const Footer = () => (
  <footer className="mt-40 border-t-8 border-black py-24 flex flex-col items-center gap-10">
     <div className="max-w-2xl text-center px-10">
        <p className="text-[10px] font-black uppercase tracking-[0.3em] text-black/30 leading-relaxed">
          Research derived from "TradingAgents: Multi-Agents LLM Financial Trading Framework" (arXiv:2412.20138). 
          USC & Google DeepMind.
        </p>
     </div>
     <div className="flex items-center gap-5 grayscale hover:grayscale-0 transition-all cursor-pointer">
        <img src="/transhumans art/SVG/Pilot.svg" className="w-14 h-14" alt="Ecotron" />
        <span className="text-xl font-black uppercase tracking-[0.8em] text-black">ECOTRON.CO.IN</span>
     </div>
  </footer>
);

// --- Pages ---

const Dashboard = ({ 
  ticker, setTicker, isProcessing, setIsProcessing, blogs, fetchBlogs, userId, setActiveTaskId, startPolling 
}) => {
  const [filterTicker, setFilterTicker] = useState('');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [currentIconIdx, setCurrentIconIdx] = useState(0);
  const [dataSource, setDataSource] = useState('yfinance');

  useEffect(() => {
    let interval;
    if (isProcessing) {
      interval = setInterval(() => {
        setCurrentIconIdx(prev => (prev + 1) % TRANSHUMAN_ICONS.length);
      }, 400);
    } else {
      setCurrentIconIdx(0);
    }
    return () => clearInterval(interval);
  }, [isProcessing]);

  const uniqueTickers = Array.from(new Set(blogs.map(b => b.ticker))).sort();

  const filteredBlogs = blogs.filter(b => {
    const matchesTicker = !filterTicker || b.ticker === filterTicker;
    const blogDate = new Date(b.timestamp);
    const afterStart = !dateRange.start || blogDate >= new Date(dateRange.start);
    const beforeEnd = !dateRange.end || blogDate <= new Date(dateRange.end);
    return matchesTicker && afterStart && beforeEnd;
  });

  const handleAnalyze = async () => {
    if (!ticker) return;
    setIsProcessing(true);
    setTicker(''); // Clear input immediately
    toast.promise(
      fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker: ticker.toUpperCase(), user_id: userId, data_source: dataSource })
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
    <div className="space-y-24">
      {/* Search Terminal */}
      <div className="glass-card relative overflow-hidden group min-h-[500px] flex items-center justify-center p-1 border-black">
        <div className="absolute inset-0 bg-[radial-gradient(#00000011_1px,transparent_1px)] [background-size:20px_20px] opacity-10"></div>
        <AnimatePresence mode="wait">
          {!isProcessing ? (
            <motion.div 
              key="input"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="relative z-10 w-full space-y-16 px-12"
            >
              <div className="text-center space-y-8">
                <div className="inline-flex items-center gap-3 px-6 py-3 bg-white text-black border-2 border-black mb-6">
                  <span className="text-[14px] font-black uppercase tracking-[0.4em]">Neural Terminal v4.0</span>
                </div>
                <h2 className="text-8xl font-black uppercase tracking-tighter leading-none text-black">
                  NEURAL <span className="text-black">SEARCH</span>
                </h2>
                <p className="text-black/40 text-[12px] font-black uppercase tracking-[0.8em]">Deploy multi-agent expert systems for institutional research</p>
              </div>
              <div className="flex flex-col gap-8 max-w-3xl mx-auto">
                <div className="relative group/input">
                  <div className="absolute -inset-2 bg-black/5 blur opacity-0 group-focus-within/input:opacity-100 transition duration-500"></div>
                  <div className="relative bg-white border-4 border-black group-focus-within/input:translate-x-1 group-focus-within/input:translate-y-1 transition-all">
                    <input 
                      value={ticker}
                      onChange={(e) => setTicker(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                      type="text" 
                      placeholder="ENTER TICKER..." 
                      className="w-full bg-transparent text-4xl font-black uppercase tracking-[0.3em] py-12 px-14 outline-none placeholder:text-black/10 text-black"
                    />
                    <div className="absolute right-10 top-1/2 -translate-y-1/2 flex items-center gap-6">
                      <div className="relative group/source hidden md:block">
                        <select 
                          value={dataSource}
                          onChange={(e) => setDataSource(e.target.value)}
                          className="bg-black text-white text-[10px] font-black uppercase px-4 py-2 outline-none appearance-none cursor-pointer border-2 border-black pr-8"
                        >
                          <option value="yfinance">Yahoo Finance</option>
                          <option value="alpha_vantage">Alpha Vantage</option>
                        </select>
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-white"><ChevronDown className="w-3 h-3" /></div>
                      </div>
                      <div className="text-black/30 text-[14px] font-black tracking-widest hidden sm:block">PRESS ENTER ↵</div>
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
              className="absolute inset-0 z-20 flex flex-col items-center justify-center text-center p-12 bg-white"
            >
              <div className="relative mb-20 flex items-center justify-center">
                   <motion.img 
                      key={currentIconIdx}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      src={`/transhumans_art/SVG/${TRANSHUMAN_ICONS[currentIconIdx]}`} 
                      alt="Synthesis Node" 
                      className="w-48 h-48" 
                    />
              </div>
              <h3 className="text-6xl font-black uppercase tracking-tighter mb-12 text-black">SYNTHESIZING...</h3>
              <div className="space-y-6 max-w-xl w-full">
                <LoadingStep text={`NODE: ${TRANSHUMAN_ICONS[currentIconIdx].replace('.svg', '').toUpperCase()}`} delay={0} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Global Intelligence Feed Filters */}
      <div className="space-y-12">
        <div className="flex flex-col md:flex-row gap-8 items-end justify-between border-b-4 border-black pb-12">
          <div className="space-y-4">
            <h2 className="text-5xl font-black uppercase tracking-tighter text-black">Global Intelligence Feed</h2>
          </div>
          <div className="flex flex-wrap gap-4">
             <div className="space-y-2 relative">
                <label className="text-[10px] font-black uppercase text-black/40 tracking-widest">Filter Ticker</label>
                <div className="relative group/select">
                  <select 
                    value={filterTicker}
                    onChange={(e) => setFilterTicker(e.target.value)}
                    className="bg-white border-4 border-black px-8 py-4 text-sm font-black uppercase outline-none hover:bg-black hover:text-white transition-all appearance-none cursor-pointer min-w-[200px] text-black shadow-[6px_6px_0px_#000]"
                  >
                    <option value="">ALL_TICKERS</option>
                    {uniqueTickers.map(t => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                  <div className="absolute right-4 top-1/2 translate-y-1 pointer-events-none group-hover/select:text-white text-black">
                    <ChevronDown className="w-5 h-5" />
                  </div>
                </div>
             </div>
             <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-black/40 tracking-widest">From</label>
                <input 
                  type="date" 
                  value={dateRange.start}
                  onChange={(e) => setDateRange(prev => ({...prev, start: e.target.value}))}
                  className="bg-white border-2 border-black px-4 py-3 text-sm font-black uppercase outline-none"
                />
             </div>
             <div className="space-y-2">
                <label className="text-[10px] font-black uppercase text-black/40 tracking-widest">To</label>
                <input 
                  type="date" 
                  value={dateRange.end}
                  onChange={(e) => setDateRange(prev => ({...prev, end: e.target.value}))}
                  className="bg-white border-2 border-black px-4 py-3 text-sm font-black uppercase outline-none"
                />
             </div>
          </div>
        </div>

        <div className="feed-grid">
          {filteredBlogs.map((blog, idx) => (
            <BlogCard key={blog._id} blog={blog} index={idx} />
          ))}
        </div>
      </div>
    </div>
  );
};

const BlogDetail = () => {
  const { id } = useParams();
  const [blog, setBlog] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBlog = async () => {
      try {
        const res = await fetch(`/api/blog-data/${id}`);
        if (!res.ok) throw new Error('Not found');
        const data = await res.json();
        setBlog(data);
      } catch (e) {
        toast.error("Research report not found.");
        navigate('/');
      } finally {
        setLoading(false);
      }
    };
    fetchBlog();
  }, [id]);

  if (loading) return (
    <div className="flex flex-col items-center justify-center py-40 gap-8">
      <div className="w-16 h-16 border-4 border-sky-500/20 border-t-sky-500 rounded-full animate-spin"></div>
      <p className="text-[10px] font-black uppercase tracking-[0.5em] text-slate-500">Accessing Neural Archive...</p>
    </div>
  );

  if (!blog) return null;

  const decision = blog.decision.toUpperCase();
  const isPositive = decision.includes('BUY') || decision.includes('OVERWEIGHT');

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-16">
      <div className="relative flex flex-col md:flex-row justify-between items-start gap-12 border-b-8 border-black pb-16">
        <div className="space-y-8 flex-grow">
          <button onClick={() => navigate(-1)} className="flex items-center gap-3 text-[12px] font-black uppercase text-black/40 hover:text-black transition-colors mb-8">
            <ChevronLeft className="w-5 h-5" /> BACK_TO_TERMINAL
          </button>
          <div className="space-y-6">
             <h1 className="text-6xl font-black tracking-tighter m-0 leading-[1.1] text-black max-w-4xl">{blog.title}</h1>
             <h2 className="text-9xl font-black tracking-tighter m-0 leading-none text-black/10 absolute top-20 right-0 -z-10 select-none">{blog.ticker}</h2>
             <div className="flex flex-wrap gap-4 mt-8">
               <SocialBtn platform="Twitter" ticker={blog.ticker} title={blog.title} />
               <SocialBtn platform="Facebook" />
               <SocialBtn platform="WhatsApp" title={blog.title} />
               <SocialBtn platform="Copy" />
            </div>
          </div>
        </div>
        <div className={`flex items-center justify-center px-8 py-6 ${isPositive ? 'bg-black text-white' : 'border-8 border-black text-black'} text-4xl lg:text-5xl font-black uppercase shadow-[12px_12px_0px_#000000] min-w-[280px] text-center`}>
          {blog.decision}
        </div>
      </div>

      <div className="text-2xl text-slate-700 font-medium leading-relaxed prose max-w-none border-l-8 border-black/5 pl-12 py-8" dangerouslySetInnerHTML={{ __html: marked.parse(blog.summary) }} />
      
      {blog.agent_status && blog.agent_status.length > 0 && (
        <div className="border-4 border-black p-10 bg-white">
          <h3 className="text-3xl font-black uppercase tracking-tighter mb-8 border-b-4 border-black pb-4 text-black">Neural Expert Teams Deployed</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {blog.agent_status.map((team, idx) => (
              <div key={idx} className="space-y-4">
                <h4 className="text-xl font-black uppercase text-black/40">{team.team}</h4>
                <div className="flex flex-wrap gap-2">
                  {team.agents.map((agent, aIdx) => (
                    <span key={aIdx} className="px-3 py-1 border-2 border-black text-[12px] font-black uppercase text-black bg-black/5">{agent}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-12">
        {Object.entries(blog.content || {}).map(([key, content], idx) => {
          if (!content) return null;
          const titles = {
            market: "Market Analysis",
            sentiment: "Sentiment Analysis",
            news: "Social & Sentiment",
            fundamentals: "Fundamentals"
          };
          const icons = ["Chillin.svg", "Pacheco.svg", "Roboto.svg", "Waiting.svg", "Consumer.svg", "Growth.svg"];
          const title = titles[key] || key.toUpperCase();
          const icon = icons[idx % icons.length];
          return <ReportSection key={key} title={title} content={content} icon={icon} />;
        })}
      </div>


    </motion.div>
  );
};

const ReportSection = ({ title, content, icon }) => (
  <div className="glass-card p-12 lg:p-20 border-4 border-black space-y-16 bg-white shadow-none">
    <div className="flex flex-col md:flex-row items-center gap-10 border-b-8 border-black pb-10">
      <div className="agent-icon-container">
        <img src={`/transhumans_art/SVG/${icon}`} alt={title} className="w-32 h-32 object-contain" />
        <div className="agent-status-tick">✓</div>
      </div>
      <h3 className="text-5xl lg:text-7xl font-black uppercase m-0 tracking-tighter text-black">{title}</h3>
    </div>
    <div className="space-y-10">
      <div className="text-2xl lg:text-3xl text-black/80 leading-relaxed prose font-medium max-w-none" dangerouslySetInnerHTML={{ __html: marked.parse(content || "") }} />
    </div>
  </div>
);

const MainContainer = () => {
  const [ticker, setTicker] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [blogs, setBlogs] = useState([]);
  const [activeTaskId, setActiveTaskId] = useState(localStorage.getItem('active_task_id'));
  const navigate = useNavigate();
  const [userId] = useState(() => {
    let id = localStorage.getItem('trading_user_id');
    if (!id) {
      id = 'u_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('trading_user_id', id);
    }
    return id;
  });

  const fetchBlogs = async () => {
    try {
      const res = await fetch('/blogs');
      if (!res.ok) throw new Error('Server Error');
      const data = await res.json();
      setBlogs(data);
    } catch (e) { toast.error("Failed to sync with neural nodes."); }
  };

  useEffect(() => {
    fetchBlogs();
    if (activeTaskId) startPolling(activeTaskId);

    const CURRENT_VERSION = 'v2.1';
    const storedVersion = localStorage.getItem('app_version');
    if (storedVersion !== CURRENT_VERSION) {
      const performHardRefresh = async () => {
        const userId = localStorage.getItem('trading_user_id');
        localStorage.clear();
        sessionStorage.clear();
        if (userId) localStorage.setItem('trading_user_id', userId);
        localStorage.setItem('app_version', CURRENT_VERSION);
        
        if ('caches' in window) {
          try {
            const cacheNames = await caches.keys();
            await Promise.all(cacheNames.map(name => caches.delete(name)));
          } catch (e) {}
        }
        window.location.reload(true);
      };
      performHardRefresh();
    }
  }, []);

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
          toast.success("Intelligence Report Synthesized!");
          fetchBlogs();
          if (data.result && data.result.blog_id) {
            navigate(`/blog/${data.result.blog_id}`);
          }
        } else if (data.status === 'failed') {
          clearInterval(interval);
          localStorage.removeItem('active_task_id');
          setActiveTaskId(null);
          setIsProcessing(false);
          toast.error("Analysis Protocol Failed");
        }
      } catch (e) { clearInterval(interval); }
    }, 5000);
  };

  return (
    <PageLayout isProcessing={isProcessing} activeTaskId={activeTaskId}>
      <Routes>
        <Route path="/" element={
          <Dashboard 
            ticker={ticker} setTicker={setTicker} 
            isProcessing={isProcessing} setIsProcessing={setIsProcessing}
            blogs={blogs} fetchBlogs={fetchBlogs}
            userId={userId} setActiveTaskId={setActiveTaskId}
            startPolling={startPolling}
          />
        } />
        <Route path="/blog/:id" element={<BlogDetail />} />
      </Routes>

      <footer className="mt-40 border-t-8 border-black py-24 flex flex-col items-center gap-10">
         <div className="max-w-2xl text-center px-10">
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-black/30 leading-relaxed">
              Research derived from "TradingAgents: Multi-Agents LLM Financial Trading Framework" (arXiv:2412.20138). 
              USC & Google DeepMind.
            </p>
         </div>
         <div className="flex items-center gap-5 grayscale hover:grayscale-0 transition-all cursor-pointer">
            <img src="/transhumans_art/SVG/Pilot.svg" className="w-14 h-14" alt="Ecotron" />
            <span className="text-xl font-black uppercase tracking-[0.8em] text-black">ECOTRON.CO.IN</span>
         </div>
      </footer>
    </PageLayout>
  );
};

const App = () => {
  return (
    <BrowserRouter>
      <Toaster position="top-right" theme="light" richColors closeButton />
      <MainContainer />
    </BrowserRouter>
  );
};

export default App;

// --- Sub-components ---

const LoadingStep = ({ text, delay }) => (
  <motion.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay }} className="flex items-center justify-center gap-4 text-black/40 text-[12px] font-black uppercase tracking-[0.4em]">
    <div className="w-2 h-2 bg-black animate-pulse"></div>
    <span>{text}...</span>
  </motion.div>
);

const BlogCard = ({ blog, index }) => {
  const navigate = useNavigate();
  const decision = blog.decision.toUpperCase();
  const isPositive = decision.includes('BUY') || decision.includes('OVERWEIGHT');

  return (
    <motion.div 
      layout initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.05 }}
      whileHover={{ y: -8 }} className="blog-card glass-card group cursor-pointer flex flex-col hover:border-black bg-white" 
      onClick={() => navigate(`/blog/${blog._id}`)}
    >
      <div className="flex justify-between items-center mb-8">
        <span className="px-5 py-2 bg-black text-white text-[12px] font-black uppercase tracking-widest border-2 border-black">{blog.ticker}</span>
        <span className="text-[12px] text-black/40 font-black uppercase tracking-widest">{new Date(blog.timestamp).toLocaleDateString()}</span>
      </div>
      <h3 className="text-4xl font-black leading-[1.1] mb-8 transition-colors uppercase tracking-tighter h-[3.2rem] overflow-hidden text-slate-900">
        {(() => {
          const t = `${blog.ticker} INTELLIGENCE: ${blog.title}`;
          return t.length > 25 ? t.substring(0, 25) + "..." : t;
        })()}
      </h3>
      <div className="text-lg text-slate-500 mb-10 leading-relaxed line-clamp-3 flex-grow prose font-bold" dangerouslySetInnerHTML={{ __html: marked.parse(blog.summary) }} />
      <div className="flex items-center justify-between pt-10 border-t-4 border-black">
        <div className="flex gap-2">
          <SocialBtn platform="Twitter" small ticker={blog.ticker} title={blog.title} />
          <SocialBtn platform="Facebook" small />
          <SocialBtn platform="WhatsApp" small title={blog.title} />
          <SocialBtn platform="Copy" small />
        </div>
        <span className={`text-[12px] font-black uppercase px-6 py-3 tracking-[0.3em] ${isPositive ? 'bg-black text-white' : 'border-4 border-black text-black'}`}>{blog.decision}</span>
      </div>
    </motion.div>
  );
};

const SocialBtn = ({ platform, small, ticker, title }) => {
  const [copied, setCopied] = useState(false);
  const shareUrl = window.location.href;

  const handleShare = (e) => {
    e.stopPropagation();
    if (platform === 'Copy') {
      navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("Link copied to clipboard");
      return;
    }
    
    let url = "";
    if (platform === 'Twitter') url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(`${title || ticker} Research Synthesized by Ecotron Intelligence`)}&url=${encodeURIComponent(shareUrl)}`;
    if (platform === 'Facebook') url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`;
    if (platform === 'WhatsApp') url = `https://api.whatsapp.com/send?text=${encodeURIComponent(`${title || ticker} Research: ${shareUrl}`)}`;
    
    window.open(url, '_blank');
  };

  const Icon = {
    Twitter: TrendingUp,
    Facebook: Layout,
    WhatsApp: Send,
    Copy: copied ? CheckCircle : Share2
  }[platform];

  return (
    <button 
      onClick={handleShare}
      className={`${small ? 'w-10 h-10' : 'h-14 px-6'} flex items-center justify-center gap-3 bg-white text-black border-2 border-black hover:bg-black hover:text-white transition-all font-black uppercase text-[10px] tracking-widest`}
    >
      <Icon className={small ? 'w-4 h-4' : 'w-5 h-5'} />
      {!small && platform}
    </button>
  );
};
