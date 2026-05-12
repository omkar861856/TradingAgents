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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from bson import ObjectId
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
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/tradingagents")
# Check if running inside Docker (simple check)
if os.path.exists("/.dockerenv") or os.getenv("DOCKER_CONTAINER"):
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
                    "user_id": "system_admin",
                    "agent_status": [
                        {"team": "Analyst Team", "agents": ["Market Analyst", "Social Analyst"]},
                        {"team": "Trading Team", "agents": ["Trader"]}
                    ]
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
    data_source: Optional[str] = "yfinance"

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
async def analyze(request: Request, data: AnalysisRequest, background_tasks: BackgroundTasks):
    ticker = data.ticker.strip().upper()
    if not ticker.isalnum() or len(ticker) > 10:
        raise HTTPException(status_code=400, detail="Invalid ticker")
    
    task_id = f"task_{datetime.now().strftime('%H%M%S%f')}"
    _tasks[task_id] = {
        "status": "pending",
        "ticker": data.ticker,
        "logs": ["Initializing research agents..."],
        "result": None
    }
    
    data.llm_provider = "openai"
    data.deep_think_llm = "gpt-4o"
    data.quick_think_llm = "gpt-4o"
    
    if not data.api_key:
        data.api_key = os.getenv("OPENAI_API_KEY")

    background_tasks.add_task(run_analysis_task, task_id, data)
    background_tasks.add_task(log_activity, data, task_id)
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
        if request.data_source:
            config_overrides["data_vendors"] = {
                "core_stock_apis": request.data_source,
                "technical_indicators": request.data_source,
                "fundamental_data": request.data_source,
                "news_data": request.data_source,
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
        logger.error(f"Task {task_id} failed with exception: {str(e)}", exc_info=True)
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

@app.get("/api/blog-data/{blog_id}")
async def get_blog_data(blog_id: str):
    try:
        doc = await blogs_collection.find_one({"_id": ObjectId(blog_id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Blog not found")
        doc["_id"] = str(doc["_id"])
        doc["timestamp"] = doc["timestamp"].isoformat()
        return doc
    except Exception as e:
        logger.error(f"Failed to fetch blog data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    return HTMLResponse(content=html_content)

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
    return HTMLResponse(content=html_content)

@app.get("/robots.txt")
async def get_robots():
    content = "User-agent: *\nDisallow: /admin\nSitemap: https://ecotron.co.in/sitemap.xml"
    return Response(content=content, media_type="text/plain")

@app.get("/sitemap.xml")
async def get_sitemap():
    # Exclude admin and internal paths
    urls = [
        "<url><loc>https://ecotron.co.in/</loc><lastmod>2026-05-10</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"
    ]
    cursor = blogs_collection.find({}, {"_id": 1, "timestamp": 1})
    async for blog in cursor:
        lastmod = blog["timestamp"].strftime("%Y-%m-%d")
        urls.append(f"<url><loc>https://ecotron.co.in/blog/{blog['_id']}</loc><lastmod>{lastmod}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>")
    
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{"".join(urls)}</urlset>'
    return Response(content=xml, media_type="application/xml")

@app.get("/{path:path}")
async def catch_all(request: Request, path: str):
    if path.startswith("api/") or path.startswith("static/") or "." in path:
        return Response(status_code=404)
    
    index_path = os.path.join("frontend", "dist", "index.html")
    if not os.path.exists(index_path):
        index_path = os.path.join("static", "index.html")
        
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())
    
    return HTMLResponse(content="<h1>Ecotron Trading Platform</h1><p>Frontend not built. Please run npm run build.</p>")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
