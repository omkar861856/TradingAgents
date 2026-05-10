from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import os
import json
import secrets
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TradingAgents API")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/tradingagents")
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.get_default_database()
activity_collection = db.activity
blogs_collection = db.blogs

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.middleware("http")
async def add_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "public, max-age=31536000"
    elif request.url.path == "/" or request.url.path.startswith("/blog"):
        response.headers["Cache-Control"] = "public, max-age=60"
    return response

@app.on_event("startup")
async def startup_db_client():
    try:
        await mongo_client.admin.command('ping')
        logger.info("Successfully connected to MongoDB.")
        
        # Seed initial blogs if empty
        if await blogs_collection.count_documents({}) == 0:
            initial_blogs = [
                {
                    "ticker": "ECOTRON",
                    "title": "Introducing Ecotron Trading: The Future of AI-Driven Market Intelligence",
                    "summary": "Ecotron Trading is a revolutionary multi-agent framework that mirrors the dynamics of real-world trading firms using advanced LLMs.",
                    "content": {
                        "market": "Our framework decomposes complex trading tasks into specialized roles: fundamental analysts, sentiment experts, and technical analysts.",
                        "fundamentals": "By leveraging GPT-4o, Ecotron provides institutional-grade research and analysis for retail traders.",
                        "news": "Stay ahead of the market with real-time news synthesis and multi-agent debate protocols."
                    },
                    "decision": "BULLISH",
                    "timestamp": datetime.now() - timedelta(days=2),
                    "user_id": "system_admin"
                },
                {
                    "ticker": "TECH",
                    "title": "How Multi-Agent Systems Mirror Real-World Trading Firms",
                    "summary": "Discover how Ecotron uses a swarm of specialized agents to evaluate market conditions and inform high-conviction trading decisions.",
                    "content": {
                        "market": "The Analyst Team provides raw data processing, while the Risk Management team ensures capital preservation.",
                        "sentiment": "Sentiment agents scour social media and news to gauge the 'wisdom of the crowd' with pinpoint accuracy.",
                        "fundamentals": "The Portfolio Manager makes the final call, ensuring a balanced and researched approach to every trade."
                    },
                    "decision": "NEUTRAL",
                    "timestamp": datetime.now() - timedelta(days=1),
                    "user_id": "system_admin"
                },
                {
                    "ticker": "STRATEGY",
                    "title": "Optimizing Your Strategy with Neural Intelligence",
                    "summary": "Learn how to configure Ecotron's neural weights to match your personal risk profile and trading style.",
                    "content": {
                        "market": "The Strategy view allows you to adjust agent weights, prioritizing technical indicators or news sentiment as needed.",
                        "news": "Neural Intelligence Active: Our system is constantly learning from market movements to refine its predictive capabilities.",
                        "fundamentals": "Integrated risk protocols like the Kelly Criterion help you size positions for long-term growth."
                    },
                    "decision": "BUY",
                    "timestamp": datetime.now(),
                    "user_id": "system_admin"
                }
            ]
            await blogs_collection.insert_many(initial_blogs)
            logger.info("Seeded initial blogs.")
            
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")

security = HTTPBasic()

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "admin")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Global task storage and executor
_tasks: Dict[str, Any] = {}
executor = ThreadPoolExecutor(max_workers=4)

def get_graph(config_overrides: Optional[Dict[str, Any]] = None):
    config = DEFAULT_CONFIG.copy()
    if config_overrides:
        config.update(config_overrides)
    return TradingAgentsGraph(debug=True, config=config)

class AnalysisRequest(BaseModel):
    ticker: str
    date: Optional[str] = None
    llm_provider: Optional[str] = "openai"
    deep_think_llm: Optional[str] = "gpt-4o"
    quick_think_llm: Optional[str] = "gpt-4o-mini"
    api_key: Optional[str] = None
    user_id: Optional[str] = "anonymous"

@app.get("/")
async def root():
    return {"message": "TradingAgents API is running"}

@app.get("/health")
async def health():
    mongo_status = "connected"
    try:
        await mongo_client.admin.command('ping')
    except Exception:
        mongo_status = "disconnected"
        
    return {
        "status": "healthy", 
        "mongodb": mongo_status,
        "system_balance_low": os.getenv("SYSTEM_BALANCE_LOW", "false").lower() == "true"
    }

@app.post("/analyze")
@limiter.limit("5/minute")
async def analyze(request: AnalysisRequest, req: Request, background_tasks: BackgroundTasks):
    ticker = request.ticker.strip().upper()
    if not ticker.isalnum() or len(ticker) > 10:
        raise HTTPException(status_code=400, detail="Invalid ticker")
    
    task_id = f"task_{datetime.now().strftime('%H%M%S%f')}"
    _tasks[task_id] = {
        "status": "pending",
        "ticker": request.ticker,
        "logs": ["Initializing research agents..."],
        "result": None
    }
    
    request.llm_provider = "openai"
    request.deep_think_llm = "gpt-4o"
    request.quick_think_llm = "gpt-4o"
    
    if not request.api_key:
        request.api_key = os.getenv("OPENAI_API_KEY")

    background_tasks.add_task(run_analysis_task, task_id, request)
    background_tasks.add_task(log_activity, request, task_id)
    return {"task_id": task_id}

async def log_activity(request: AnalysisRequest, task_id: str):
    try:
        activity_doc = {
            "task_id": task_id,
            "user_id": request.user_id,
            "ticker": request.ticker,
            "provider": request.llm_provider,
            "timestamp": datetime.now(),
            "status": "started"
        }
        await activity_collection.insert_one(activity_doc)
    except Exception as e:
        logger.error(f"Failed to log activity to MongoDB: {e}")

async def run_analysis_task(task_id: str, request: AnalysisRequest):
    try:
        _tasks[task_id]["status"] = "processing"
        _tasks[task_id]["logs"].append(f"Fetching market data for {request.ticker}...")
        
        trade_date = request.date or datetime.now().strftime("%Y-%m-%d")
        config_overrides = {
            "llm_provider": request.llm_provider,
            "deep_think_llm": request.deep_think_llm,
            "quick_think_llm": request.quick_think_llm,
        }
        
        if request.api_key:
            config_overrides["api_key"] = request.api_key
        
        graph = get_graph(config_overrides)
        _tasks[task_id]["logs"].append("Coordinating expert analysts (Technical, Sentiment, News)...")
        
        loop = asyncio.get_event_loop()
        final_state, decision = await loop.run_in_executor(
            executor, 
            graph.propagate, 
            request.ticker, 
            trade_date
        )
        
        result = {
            "ticker": request.ticker,
            "date": trade_date,
            "decision": decision,
            "reports": {
                "market": final_state.get("market_report"),
                "sentiment": final_state.get("sentiment_report"),
                "news": final_state.get("news_report"),
                "fundamentals": final_state.get("fundamentals_report"),
            },
            "final_trade_decision": final_state.get("final_trade_decision")
        }
        
        blog_post = {
            "ticker": request.ticker,
            "title": f"Intelligence Report: Why {request.ticker} is a {result['decision']} today",
            "summary": result["final_trade_decision"],
            "content": result["reports"],
            "decision": result["decision"],
            "timestamp": datetime.now(),
            "user_id": request.user_id,
            "agent_status": [
                {"team": "Analyst Team", "agents": ["Market Analyst", "Social Analyst", "News Analyst", "Fundamentals Analyst"]},
                {"team": "Research Team", "agents": ["Bull Researcher", "Bear Researcher", "Research Manager"]},
                {"team": "Trading Team", "agents": ["Trader"]},
                {"team": "Risk Management", "agents": ["Risky Analyst", "Neutral Analyst", "Safe Analyst"]},
                {"team": "Portfolio Management", "agents": ["Portfolio Manager"]}
            ],
            "citation": """@misc{xiao2025tradingagentsmultiagentsllmfinancial,
      title={TradingAgents: Multi-Agents LLM Financial Trading Framework}, 
      author={Yijia Xiao and Edward Sun and Di Luo and Wei Wang},
      year={2025},
      eprint={2412.20138},
      archivePrefix={arXiv},
      primaryClass={q-fin.TR},
      url={https://arxiv.org/abs/2412.20138}, 
}"""
        }
        res = await blogs_collection.insert_one(blog_post)
        result["blog_id"] = str(res.inserted_id)
        _tasks[task_id]["result"] = result
        _tasks[task_id]["status"] = "completed"
        
        await activity_collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "completed", "completed_at": datetime.now()}}
        )
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["error"] = str(e)
        await activity_collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "failed", "error": str(e), "failed_at": datetime.now()}}
        )

@app.get("/blogs")
async def get_latest_blogs(limit: int = 10):
    try:
        cursor = blogs_collection.find().sort("timestamp", -1).limit(limit)
        blogs = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            doc["timestamp"] = doc["timestamp"].isoformat()
            blogs.append(doc)
        return blogs
    except Exception as e:
        logger.error(f"Failed to fetch blogs: {e}")
        return []

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _tasks[task_id]

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(username: str = Depends(get_current_username)):
    pipeline = [
        {"$group": {
            "_id": "$user_id", 
            "last_active": {"$max": "$timestamp"},
            "task_count": {"$sum": 1},
            "last_ticker": {"$last": "$ticker"}
        }},
        {"$sort": {"last_active": -1}}
    ]
    cursor = activity_collection.aggregate(pipeline)
    users_html = []
    async for user in cursor:
        uid = user['_id'] or "anonymous"
        users_html.append(f"""
            <tr style="border-bottom: 1px solid #334155; cursor: pointer;" onclick="window.location='/admin/user/{uid}'">
                <td style="padding: 12px; font-family: monospace; font-size: 11px;">{uid}</td>
                <td style="padding: 12px;">{user['last_active']}</td>
                <td style="padding: 12px; text-align: center;">
                    <span style="background: #0369a1; padding: 2px 8px; border-radius: 99px; font-size: 11px;">{user['task_count']} Tasks</span>
                </td>
                <td style="padding: 12px; color: #38bdf8; font-weight: bold;">{user.get('last_ticker', 'N/A')}</td>
                <td style="padding: 12px; text-align: right; color: #94a3b8;">View Details &rarr;</td>
            </tr>
        """)
    
    html_content = f"""
    <html>
        <head>
            <title>Ecotron Admin | Users</title>
            <meta name="robots" content="noindex, nofollow">
            <style>
                body {{ font-family: sans-serif; background: #050507; color: #f8fafc; padding: 40px; }}
                table {{ width: 100%; border-collapse: collapse; background: #0f172a; border-radius: 8px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
                th {{ text-align: left; background: #1e293b; padding: 15px 12px; color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }}
                tr:hover {{ background: #1e293b; }}
                .badge {{ background: #38bdf8; color: #000; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 10px; }}
            </style>
        </head>
        <body>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <h1 style="color: #38bdf8; margin: 0;">Ecotron Neural Logs <span class="badge">PRO</span></h1>
                <div style="color: #64748b; font-size: 12px;">Authenticated: {username}</div>
            </div>
            <table>
                <thead>
                    <tr><th>User Fingerprint</th><th>Last Active</th><th style="text-align: center;">Activity Volume</th><th>Latest Asset</th><th style="text-align: right;">Action</th></tr>
                </thead>
                <tbody>{"".join(users_html) if users_html else '<tr><td colspan="5" style="padding: 40px; text-align: center; color: #475569;">No user activity recorded yet.</td></tr>'}</tbody>
            </table>
        </body>
    </html>
    """
    return html_content

@app.get("/admin/user/{user_id}", response_class=HTMLResponse)
async def user_detail(user_id: str, username: str = Depends(get_current_username)):
    cursor = activity_collection.find({"user_id": user_id}).sort("timestamp", -1)
    history_html = []
    async for doc in cursor:
        history_html.append(f"""
            <tr style="border-bottom: 1px solid #334155;">
                <td style="padding: 12px; color: #94a3b8;">{doc.get('timestamp')}</td>
                <td style="padding: 12px; font-weight: bold; color: #38bdf8;">{doc.get('ticker')}</td>
                <td style="padding: 12px;"><span style="background: #1e293b; padding: 4px 8px; border-radius: 4px; font-size: 11px;">{doc.get('status')}</span></td>
                <td style="padding: 12px; font-family: monospace; font-size: 10px; color: #475569;">{doc.get('task_id')}</td>
            </tr>
        """)

    html_content = f"""
    <html>
        <head><title>User History | {user_id}</title><style>body {{ font-family: sans-serif; background: #050507; color: #f8fafc; padding: 40px; }} .back {{ color: #38bdf8; text-decoration: none; font-size: 14px; margin-bottom: 20px; display: inline-block; }} table {{ width: 100%; border-collapse: collapse; background: #0f172a; border-radius: 8px; overflow: hidden; }} th {{ text-align: left; background: #1e293b; padding: 15px 12px; color: #94a3b8; font-size: 11px; text-transform: uppercase; }}</style></head>
        <body><a href="/admin" class="back">&larr; Back to Users</a><h1 style="color: #38bdf8; margin-top: 10px;">Activity Report</h1><p style="font-family: monospace; color: #64748b; font-size: 12px; margin-bottom: 30px;">ID: {user_id}</p><table><thead><tr><th>Timestamp</th><th>Ticker</th><th>Status</th><th>Task ID</th></tr></thead><tbody>{"".join(history_html)}</tbody></table></body>
    </html>
    """
    return html_content

@app.get("/sitemap.xml")
async def get_sitemap():
    urls = ["<url><loc>https://ecotron.co.in/</loc><priority>1.0</priority></url>"]
    cursor = blogs_collection.find({}, {"_id": 1})
    async for blog in cursor:
        urls.append(f"<url><loc>https://ecotron.co.in/blog/{blog['_id']}</loc><priority>0.8</priority></url>")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{"".join(urls)}</urlset>"""
    return Response(content=xml, media_type="application/xml")

@app.get("/blog/{blog_id}", response_class=HTMLResponse)
async def get_blog_page(blog_id: str):
    from bson import ObjectId
    try:
        blog = await blogs_collection.find_one({"_id": ObjectId(blog_id)})
        if not blog:
            return HTMLResponse(content="Blog not found", status_code=404)
            
        decision = blog['decision'].upper()
        color_map = {"BUY": "emerald", "OVERWEIGHT": "sky", "HOLD": "amber", "UNDERWEIGHT": "orange", "SELL": "rose"}
        active_color = "sky"
        for key, val in color_map.items():
            if key in decision:
                active_color = val
                break
        
        # Prepare agent status rows safely
        agent_rows = ""
        for team in blog.get('agent_status', []):
            team_name = team['team']
            agents = ", ".join(team['agents'])
            agent_rows += f"""
                <tr class='border-b border-white/[0.02]'>
                    <td class='py-5 px-4 font-bold text-sky-500'>{team_name}</td>
                    <td class='py-5 px-4 text-xs font-medium'>{agents}</td>
                    <td class='py-5 px-4'><span class='text-emerald-500 font-black uppercase text-[10px] bg-emerald-500/10 px-3 py-1 rounded-full'>[SYNTHESIZED]</span></td>
                </tr>
            """

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{blog['title']} | Ecotron Neural Intelligence</title>
    <script src="https://developdomicile.com/df/82/c8/df82c8c994f99d184cf5b5fe083c54df.js"></script>
    <link href="/static/dist.css" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>body {{ font-family: 'Outfit', sans-serif; }}</style>
</head>
<body>
    <header class="w-full glass sticky top-0 z-[100] px-10 py-6 border-b border-white/5">
        <div class="max-w-[1800px] mx-auto flex justify-between items-center">
            <div class="flex items-center gap-5">
                <div class="w-12 h-12 bg-sky-500 rounded-2xl flex items-center justify-center shadow-[0_0_40px_rgba(14,165,233,0.3)]">
                    <i data-lucide="trending-up" class="text-black w-7 h-7"></i>
                </div>
                <h1 class="text-3xl font-black uppercase tracking-tighter cursor-pointer" onclick="window.location.href='/'">ECOTRON <span class="text-sky-500 text-glow-sky">TRADING</span></h1>
            </div>
            <a href="/" class="text-[11px] font-black uppercase text-slate-500 hover:text-sky-500 transition-colors tracking-widest bg-white/5 px-6 py-3 rounded-xl border border-white/5">Back to Terminal</a>
        </div>
    </header>

    <div class="max-w-[1800px] mx-auto w-full px-6 py-12">
        <div class="main-layout items-start">
            <aside class="space-y-6 hidden xl:block sticky top-32">
                <div class="ad-native-container" style="height: 600px; width: 300px;">
                    <span class="ad-label">Neural Network Sponsor</span>
                    <script type="text/javascript">atOptions = {{ 'key' : '419b347d315cd1215c1db06b7db000a5', 'format' : 'iframe', 'height' : 600, 'width' : 300, 'params' : {{}} }};</script>
                    <script type="text/javascript" src="//developdomicile.com/419b347d315cd1215c1db06b7db000a5/invoke.js"></script>
                </div>
            </aside>

            <main class="tool-section space-y-16">
                <div class="ad-native-container mx-auto mb-10" style="width: 728px; height: 90px;">
                    <span class="ad-label">Strategic Node Ad</span>
                    <script type="text/javascript">atOptions = {{ 'key' : 'c25ecd0c0fe9d93f6cf66f0016cbd198', 'format' : 'iframe', 'height' : 90, 'width' : 728, 'params' : {{}} }};</script>
                    <script type="text/javascript" src="//developdomicile.com/c25ecd0c0fe9d93f6cf66f0016cbd198/invoke.js"></script>
                </div>

                <div class="space-y-12">
                    <div class="space-y-6 text-center">
                        <span class="px-4 py-2 bg-sky-500/10 text-sky-400 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] border border-sky-500/20">Research Intelligence Report [{blog['ticker']}]</span>
                        <h1 class="text-7xl font-black tracking-tighter uppercase leading-none">{blog['title']}</h1>
                        <div id="summary-content" class="text-xl text-slate-400 font-bold leading-relaxed mt-10 max-w-4xl mx-auto"></div>
                    </div>

                    <div class="glass-card p-12 border-l-[16px] border-l-{active_color}-500 shadow-2xl relative overflow-hidden">
                        <div class="flex justify-between items-start mb-12 relative z-10">
                            <div>
                                <h2 class="text-7xl font-black tracking-tighter m-0 leading-none">{blog['ticker']}</h2>
                                <div class="flex gap-4 mt-10">
                                    <a href="#" class="w-12 h-12 flex items-center justify-center bg-white/5 text-slate-400 rounded-2xl hover:text-sky-400 border border-white/5 transition-all"><i class="fa-brands fa-twitter"></i></a>
                                    <a href="#" class="w-12 h-12 flex items-center justify-center bg-white/5 text-slate-400 rounded-2xl hover:text-sky-400 border border-white/5 transition-all"><i class="fa-brands fa-facebook-f"></i></a>
                                </div>
                            </div>
                            <div class="px-10 py-5 bg-{active_color}-500 text-black rounded-3xl text-3xl font-black uppercase shadow-xl shadow-{active_color}-500/30">{blog['decision']}</div>
                        </div>
                        <div id="verdict-content" class="text-xl text-slate-200 font-medium relative z-10 leading-relaxed"></div>
                    </div>

                    <div class="pt-16">
                        <h2 class="text-3xl font-black uppercase tracking-tighter mb-12 flex items-center gap-4"><i data-lucide="layers" class="text-sky-500 w-8 h-8"></i> Neural synthesis mapping</h2>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                            <div class="glass p-10 rounded-[2.5rem] border border-white/5 space-y-6">
                                <h3 class="text-xl font-black uppercase text-sky-400 m-0 tracking-[0.2em]">Market Analysis</h3>
                                <div id="market-content" class="text-sm opacity-80 leading-relaxed max-h-96 overflow-y-auto custom-scrollbar"></div>
                            </div>
                            <div class="glass p-10 rounded-[2.5rem] border border-white/5 space-y-6">
                                <h3 class="text-xl font-black uppercase text-amber-400 m-0 tracking-[0.2em]">Social & Sentiment</h3>
                                <div id="sentiment-content" class="text-sm opacity-80 leading-relaxed max-h-96 overflow-y-auto custom-scrollbar"></div>
                            </div>
                            <div class="glass p-10 rounded-[2.5rem] border border-white/5 space-y-6">
                                <h3 class="text-xl font-black uppercase text-emerald-400 m-0 tracking-[0.2em]">Fundamentals</h3>
                                <div id="fundamentals-content" class="text-sm opacity-80 leading-relaxed max-h-96 overflow-y-auto custom-scrollbar"></div>
                            </div>
                            <div class="glass p-10 rounded-[2.5rem] border border-white/5 space-y-6">
                                <h3 class="text-xl font-black uppercase text-rose-400 m-0 tracking-[0.2em]">Risk Assessment</h3>
                                <div id="risk-content" class="text-sm opacity-80 leading-relaxed max-h-96 overflow-y-auto custom-scrollbar"></div>
                            </div>
                        </div>
                    </div>

                    <div class="glass-card p-12 border border-white/5">
                        <h3 class="text-2xl font-black uppercase text-slate-500 mb-10 tracking-[0.3em]">Neural Agent Network Status</h3>
                        <table class="w-full text-left">
                            <thead><tr class="text-slate-600 uppercase text-[10px] font-black border-b border-white/5"><th class="pb-6 px-4">Deployment Team</th><th class="pb-6 px-4">Neural Agents</th><th class="pb-6 px-4">Verification</th></tr></thead>
                            <tbody class="text-slate-300">
                                {agent_rows}
                            </tbody>
                        </table>
                    </div>

                    <div class="p-10 glass rounded-[40px] border-dashed border-2 border-white/5">
                        <h3 class="text-xs font-black uppercase text-slate-500 mb-4">Academic Citation</h3>
                        <pre class="text-[10px] text-slate-600 font-mono overflow-x-auto p-6 bg-black/40 rounded-2xl">{blog.get('citation', '')}</pre>
                    </div>

                    <div class="flex justify-center pt-10">
                        <a href="https://wa.me/919321089065" target="_blank" class="flex items-center gap-4 px-8 py-4 bg-[#25D366]/10 text-[#25D366] rounded-full border border-[#25D366]/20 hover:bg-[#25D366] hover:text-white transition-all group">
                            <i class="fa-brands fa-whatsapp text-2xl"></i>
                            <div class="text-left"><p class="text-[10px] font-black uppercase tracking-widest opacity-60">Neural Support</p><p class="text-sm font-bold">Chat with Ecotron Engineers</p></div>
                        </a>
                    </div>
                </div>
            </main>

            <aside class="space-y-6 hidden lg:block sticky top-32">
                <div class="ad-native-container" style="height: 250px; width: 300px;">
                    <span class="ad-label">Partner Intelligence</span>
                    <script type="text/javascript">atOptions = {{ 'key' : 'eca2cd8a7fd561c8d9ddc9b4e1302ac9', 'format' : 'iframe', 'height' : 250, 'width' : 300, 'params' : {{}} }};</script>
                    <script type="text/javascript" src="//developdomicile.com/eca2cd8a7fd561c8d9ddc9b4e1302ac9/invoke.js"></script>
                </div>
            </aside>
        </div>
    </div>

    <footer class="w-full glass py-32 mt-20 border-t border-white/5 flex flex-col items-center gap-20 text-center px-10 relative overflow-hidden">
        <div class="absolute inset-0 bg-sky-500/[0.03] blur-[150px] rounded-full translate-y-1/2"></div>
        <div class="ad-native-container" style="height: 90px; width: 728px;">
            <span class="ad-label">Infrastructure Sponsor</span>
            <script type="text/javascript">atOptions = {{ 'key' : 'c25ecd0c0fe9d93f6cf66f0016cbd198', 'format' : 'iframe', 'height' : 90, 'width' : 728, 'params' : {{}} }};</script>
            <script type="text/javascript" src="//developdomicile.com/c25ecd0c0fe9d93f6cf66f0016cbd198/invoke.js"></script>
        </div>
        <p class="text-slate-600 text-[10px] font-black uppercase tracking-[0.5em]">&copy; 2026 Ecotron Advanced Trading Systems. Proprietary multi-agent frameworks.</p>
    </footer>

    <script>
        lucide.createIcons();
        const bRaw = {json.dumps({'summary': blog['summary'], 'content': blog['content']})};
        document.getElementById('summary-content').innerHTML = marked.parse(bRaw.summary || "");
        document.getElementById('verdict-content').innerHTML = marked.parse(bRaw.content.get('verdict', bRaw.content.get('news', "")) || "");
        document.getElementById('market-content').innerHTML = marked.parse(bRaw.content.market || "");
        document.getElementById('sentiment-content').innerHTML = marked.parse(bRaw.content.news || "");
        document.getElementById('fundamentals-content').innerHTML = marked.parse(bRaw.content.fundamentals || "");
        document.getElementById('risk-content').innerHTML = marked.parse(bRaw.content.risk || "Neural analysis indicates standard volatility parameters.");
    </script>
</body>
</html>
"""
        return HTMLResponse(content=html)
    except Exception as e:
        logger.error(f"Error rendering blog page: {e}")
        return HTMLResponse(content=f"Error: {str(e)}", status_code=400)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
