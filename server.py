from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import os
import json
import secrets
from datetime import datetime, timedelta
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TradingAgents API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/tradingagents")
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.get_default_database()
activity_collection = db.activity
blogs_collection = db.blogs

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

# Global task storage
_tasks: Dict[str, Any] = {}
_graph = None

def get_graph(config_overrides: Optional[Dict[str, Any]] = None):
    global _graph
    config = DEFAULT_CONFIG.copy()
    if config_overrides:
        config.update(config_overrides)
    
    # Ensure local ollama is used if provider is ollama
    if config.get("llm_provider") == "ollama":
        # Check for OLLAMA_HOST env var, default to http://ollama:11434 in docker
        ollama_host = os.getenv("OLLAMA_HOST", "http://ollama:11434")
        if not ollama_host.endswith("/v1"):
            ollama_host = ollama_host.rstrip("/") + "/v1"
        config["backend_url"] = ollama_host

    return TradingAgentsGraph(debug=True, config=config)

class AnalysisRequest(BaseModel):
    ticker: str
    date: Optional[str] = None
    llm_provider: Optional[str] = "ollama"
    deep_think_llm: Optional[str] = "llama3.1:8b"
    quick_think_llm: Optional[str] = "llama3.1:8b"
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
        "ollama": os.getenv("OLLAMA_HOST"),
        "mongodb": mongo_status,
        "system_balance_low": os.getenv("SYSTEM_BALANCE_LOW", "false").lower() == "true"
    }

@app.post("/analyze")
async def analyze(request: AnalysisRequest, background_tasks: BackgroundTasks):
    task_id = f"task_{datetime.now().strftime('%H%M%S%f')}"
    _tasks[task_id] = {
        "status": "pending",
        "ticker": request.ticker,
        "logs": ["Initializing research agents..."],
        "result": None
    }
    
    # Default to OpenAI as requested
    request.llm_provider = "openai"
    request.deep_think_llm = "gpt-4o"
    request.quick_think_llm = "gpt-4o"
    
    # Use environment key if not provided in request (though request field will be hidden in UI)
    if not request.api_key:
        request.api_key = os.getenv("OPENAI_API_KEY")

    background_tasks.add_task(run_analysis_task, task_id, request)
    
    # Log activity to MongoDB
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
            # Pass api_key to both llms if provided
            config_overrides["api_key"] = request.api_key
        
        graph = get_graph(config_overrides)
        
        _tasks[task_id]["logs"].append("Coordinating expert analysts (Technical, Sentiment, News)...")
        # In a more complex setup, we'd hook into the graph to get real-time node logs.
        # For now, we simulate the sequence to keep the UI alive.
        
        final_state, decision = graph.propagate(request.ticker, trade_date)
        
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
        _tasks[task_id]["result"] = result

        # Generate Dynamic Blog
        blog_post = {
            "ticker": request.ticker,
            "title": f"Intelligence Report: Why {request.ticker} is a {result['decision']} today",
            "summary": result["final_trade_decision"],
            "content": result["reports"],
            "decision": result["decision"],
            "timestamp": datetime.now(),
            "user_id": request.user_id,
            "metrics": {
                "alpha": 85 + (len(result["reports"]["market"]) % 15),
                "sentiment": 60 + (len(result["reports"]["sentiment"]) % 30),
                "fundamental": 50 + (len(result["reports"]["fundamentals"]) % 40)
            }
        }
        res = await blogs_collection.insert_one(blog_post)
        result["blog_id"] = str(res.inserted_id)
        
        # Update Task Result with Blog Info
        result["blog_id"] = str(blog_post["_id"])
        _tasks[task_id]["result"] = result
        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["logs"].append("Blog generated and published to Neural Feed.")
        
        # Update MongoDB activity
        await activity_collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "completed", "completed_at": datetime.now()}}
        )
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        _tasks[task_id]["status"] = "failed"
        _tasks[task_id]["error"] = str(e)
        
        # Update MongoDB activity with failure
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
            <p style="color: #94a3b8; margin-bottom: 30px;">Unique analysts identified by browser fingerprinting.</p>
            <table>
                <thead>
                    <tr>
                        <th>User Fingerprint</th>
                        <th>Last Active</th>
                        <th style="text-align: center;">Activity Volume</th>
                        <th>Latest Asset</th>
                        <th style="text-align: right;">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(users_html) if users_html else '<tr><td colspan="5" style="padding: 40px; text-align: center; color: #475569;">No user activity recorded yet.</td></tr>'}
                </tbody>
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
        <head>
            <title>User History | {user_id}</title>
            <style>
                body {{ font-family: sans-serif; background: #050507; color: #f8fafc; padding: 40px; }}
                .back {{ color: #38bdf8; text-decoration: none; font-size: 14px; margin-bottom: 20px; display: inline-block; }}
                table {{ width: 100%; border-collapse: collapse; background: #0f172a; border-radius: 8px; overflow: hidden; }}
                th {{ text-align: left; background: #1e293b; padding: 15px 12px; color: #94a3b8; font-size: 11px; text-transform: uppercase; }}
            </style>
        </head>
        <body>
            <a href="/admin" class="back">&larr; Back to Users</a>
            <h1 style="color: #38bdf8; margin-top: 10px;">Activity Report</h1>
            <p style="font-family: monospace; color: #64748b; font-size: 12px; margin-bottom: 30px;">ID: {user_id}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Ticker</th>
                        <th>Status</th>
                        <th>Task ID</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(history_html)}
                </tbody>
            </table>
        </body>
    </html>
    """
    return html_content

@app.get("/sitemap.xml")
async def get_sitemap():
    urls = [
        "<url><loc>https://ecotron.co.in/</loc><priority>1.0</priority></url>",
        "<url><loc>https://ecotron.co.in/admin</loc><priority>0.1</priority></url>"
    ]
    
    cursor = blogs_collection.find({}, {"_id": 1})
    async for blog in cursor:
        urls.append(f"<url><loc>https://ecotron.co.in/blog/{blog['_id']}</loc><priority>0.8</priority></url>")
        
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    {"".join(urls)}
</urlset>"""
    return Response(content=xml, media_type="application/xml")

@app.get("/blog/{blog_id}", response_class=HTMLResponse)
async def get_blog_page(blog_id: str):
    from bson import ObjectId
    try:
        blog = await blogs_collection.find_one({"_id": ObjectId(blog_id)})
        if not blog:
            return "Blog not found", 404
            
        # Rich SSR for indexing and standalone viewing
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{blog['title']} | Ecotron Neural Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://developdomicile.com/df/82/c8/df82c8c994f99d184cf5b5fe083c54df.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #020203; color: #f8fafc; overflow-x: hidden; }}
        .glass {{ background: rgba(15, 23, 42, 0.7); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.05); }}
        .ad-box {{ position: relative; border-radius: 12px; overflow: hidden; background: rgba(0,0,0,0.4); margin-bottom: 24px; border: 1px solid rgba(255,255,255,0.03); }}
        .ad-tag {{ position: absolute; top: 4px; left: 6px; font-size: 8px; color: #475569; z-index: 10; font-weight: 800; letter-spacing: 0.1em; }}
        .prose-custom h1 {{ font-size: 3rem; font-weight: 900; margin-bottom: 1.5rem; color: #fff; letter-spacing: -0.05em; }}
        .prose-custom h2 {{ font-size: 1.8rem; font-weight: 800; margin-top: 2rem; margin-bottom: 1rem; color: #38bdf8; }}
        .prose-custom p {{ margin-bottom: 1rem; line-height: 1.7; color: #cbd5e1; font-size: 0.95rem; }}
        .prose-custom table {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; background: rgba(255,255,255,0.02); }}
        .prose-custom th {{ background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 12px; text-align: left; }}
        .prose-custom td {{ padding: 12px; border-top: 1px solid rgba(255,255,255,0.05); }}
    </style>
</head>
<body>
    <header class="w-full glass px-8 py-5 border-b border-white/5">
        <div class="max-w-[1400px] mx-auto flex justify-between items-center">
            <div class="flex items-center gap-4">
                <div class="w-10 h-10 bg-sky-500 rounded-xl flex items-center justify-center"><i data-lucide="trending-up" class="text-black"></i></div>
                <h1 class="text-2xl font-black uppercase" onclick="window.location.href='/'" style="cursor:pointer">ECOTRON <span class="text-sky-500">TRADING</span></h1>
            </div>
            <a href="/" class="text-xs font-black uppercase text-slate-500 hover:text-white">Back to Terminal</a>
        </div>
    </header>

    <div class="max-w-[1400px] mx-auto flex gap-10 px-6 mt-10 pb-20">
        <aside style="width:160px; flex-shrink:0;">
            <div class="ad-box" style="width: 160px; height: 600px;">
                <span class="ad-tag">ADVERTISEMENT</span>
                <script>atOptions = {{ 'key' : '419b347d315cd1215c1db06b7db000a5', 'format' : 'iframe', 'height' : 600, 'width' : 160, 'params' : {{}} }};</script>
                <script src="https://developdomicile.com/419b347d315cd1215c1db06b7db000a5/invoke.js"></script>
            </div>
        </aside>

        <main style="flex-grow:1; min-width:0; max-width:1100px;">
            <div class="ad-box mx-auto" style="width: 468px; height: 60px;">
                <span class="ad-tag">SPONSORED</span>
                <script>atOptions = {{ 'key' : 'd9b9196cf2814e58242076df2f21e5dc', 'format' : 'iframe', 'height' : 60, 'width' : 468, 'params' : {{}} }};</script>
                <script src="https://developdomicile.com/d9b9196cf2814e58242076df2f21e5dc/invoke.js"></script>
            </div>

            <div class="space-y-12 prose-custom">
                <div>
                    <span class="px-4 py-2 bg-sky-500/10 text-sky-400 rounded-xl text-xs font-black uppercase">Intelligence Report [{blog['ticker']}]</span>
                    <h1 class="text-7xl font-black tracking-tighter uppercase mt-6">{blog['title']}</h1>
                    <div id="summary-content" class="text-2xl text-slate-400 font-bold leading-tight"></div>
                </div>

                <div class="glass p-10 rounded-[40px] border-l-[16px] border-l-{ 'emerald' if 'BUY' in blog['decision'] or 'BULL' in blog['decision'] else 'rose' if 'SELL' in blog['decision'] or 'BEAR' in blog['decision'] else 'sky' }-500">
                    <div class="flex justify-between items-start mb-10">
                        <div>
                            <h2 class="text-6xl font-black tracking-tighter m-0">{blog['ticker']}</h2>
                            <div class="flex gap-4 mt-6">
                                <a href="https://twitter.com/intent/tweet?text={blog['title']}&url=https://ecotron.co.in/blog/{blog_id}" target="_blank" class="w-12 h-12 flex items-center justify-center bg-[#1DA1F2]/10 text-[#1DA1F2] rounded-xl hover:bg-[#1DA1F2] hover:text-white transition-all shadow-lg"><i data-lucide="twitter"></i></a>
                                <a href="https://www.facebook.com/sharer/sharer.php?u=https://ecotron.co.in/blog/{blog_id}" target="_blank" class="w-12 h-12 flex items-center justify-center bg-[#4267B2]/10 text-[#4267B2] rounded-xl hover:bg-[#4267B2] hover:text-white transition-all shadow-lg"><i data-lucide="facebook"></i></a>
                                <a href="https://api.whatsapp.com/send?text={blog['title']}%20https://ecotron.co.in/blog/{blog_id}" target="_blank" class="w-12 h-12 flex items-center justify-center bg-[#25D366]/10 text-[#25D366] rounded-xl hover:bg-[#25D366] hover:text-white transition-all shadow-lg"><i data-lucide="message-circle"></i></a>
                            </div>
                        </div>
                        <div class="px-10 py-5 bg-white text-black rounded-3xl text-3xl font-black uppercase">{blog['decision']}</div>
                    </div>
                    <div id="verdict-content" class="text-xl text-slate-100 font-bold"></div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                    <div class="glass p-10 rounded-[40px] border-t-8 border-t-sky-500/50">
                        <h3 class="text-2xl font-black uppercase text-sky-400">Market Dynamics</h3>
                        <div id="market-content"></div>
                    </div>
                    <div class="glass p-10 rounded-[40px] border-t-8 border-t-amber-500/50">
                        <h3 class="text-2xl font-black uppercase text-amber-400">Sentiment Intelligence</h3>
                        <div id="sentiment-content"></div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <script>
        lucide.createIcons();
        document.getElementById('summary-content').innerHTML = marked.parse({repr(blog['summary'])});
        document.getElementById('verdict-content').innerHTML = marked.parse({repr(blog['summary'])});
        document.getElementById('market-content').innerHTML = marked.parse({repr(blog['content'].get('market', ''))});
        document.getElementById('sentiment-content').innerHTML = marked.parse({repr(blog['content'].get('sentiment', blog['content'].get('news', '')))});
    </script>
</body>
</html>
        """
        return html
    except Exception as e:
        return f"Error: {{str(e)}}", 400

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
