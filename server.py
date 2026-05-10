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
        "mongodb": mongo_status
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
            "title": f"Deep Dive: Why {request.ticker} is a {result['decision']} Today",
            "summary": result["final_trade_decision"][:300] + "...",
            "content": result["reports"],
            "decision": result["decision"],
            "timestamp": datetime.now(),
            "user_id": request.user_id
        }
        await blogs_collection.insert_one(blog_post)
        
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
    cursor = activity_collection.find().sort("timestamp", -1).limit(100)
    activities = []
    async for doc in cursor:
        activities.append(f"""
            <tr style="border-bottom: 1px solid #334155;">
                <td style="padding: 12px;">{doc.get('timestamp')}</td>
                <td style="padding: 12px;">{doc.get('user_id')}</td>
                <td style="padding: 12px; font-weight: bold; color: #38bdf8;">{doc.get('ticker')}</td>
                <td style="padding: 12px;">{doc.get('provider')}</td>
                <td style="padding: 12px;"><span style="background: #1e293b; padding: 4px 8px; border-radius: 4px;">{doc.get('status')}</span></td>
            </tr>
        """)
    
    html_content = f"""
    <html>
        <head>
            <title>Ecotron Admin</title>
            <style>
                body {{ font-family: sans-serif; background: #050507; color: #f8fafc; padding: 40px; }}
                table {{ width: 100%; border-collapse: collapse; background: #0f172a; border-radius: 8px; overflow: hidden; }}
                th {{ text-align: left; background: #1e293b; padding: 12px; color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
            </style>
        </head>
        <body>
            <h1 style="color: #38bdf8;">Ecotron Neural Logs (MongoDB)</h1>
            <p>Authenticated as: {{username}}</p>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>User Fingerprint</th>
                        <th>Ticker</th>
                        <th>Provider</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(activities)}
                </tbody>
            </table>
        </body>
    </html>
    """
    return html_content

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
