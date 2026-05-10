from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import os
import json
from datetime import datetime
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
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/tradingagents")
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client.get_default_database()
activity_collection = db.activity

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
    return {"status": "healthy"}

@app.post("/analyze")
async def analyze(request: AnalysisRequest, background_tasks: BackgroundTasks):
    task_id = f"task_{datetime.now().strftime('%H%M%S%f')}"
    _tasks[task_id] = {
        "status": "pending",
        "ticker": request.ticker,
        "logs": ["Initializing research agents..."],
        "result": None
    }
    
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
        
        _tasks[task_id]["result"] = {
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
        _tasks[task_id]["status"] = "completed"
        _tasks[task_id]["logs"].append("Analysis finalized. Generating signal...")
        
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

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _tasks[task_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
