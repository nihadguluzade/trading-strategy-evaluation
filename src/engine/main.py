from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.engine.core import run_backtest, STRATEGY_MAP
import sys, os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

app = FastAPI(
    title="Trading Strategy Evaluation API",
    description="Backend engine for calculating quantitative strategy performance.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class StrategyRequest(BaseModel):
    strategy: str
    asset: str
    parameters: dict
    start_date: Optional[str] = "2018-01-01"
    end_date: Optional[str] = "2024-06-30"
    initial_capital: Optional[float] = 100_000.0


@app.get("/api/health")
def read_health_check():
    return {"status": "online", "message": "Trading Engine API is running."}


@app.get("/api/strategies")
def list_strategies():
    return {"strategies": list(STRATEGY_MAP.keys())}


@app.get("/api/strategies/{strategy_name}/parameters")
def get_strategy_parameters(strategy_name: str):
    if strategy_name not in STRATEGY_MAP:
        raise HTTPException(status_code=404, detail=f"Strategy '{strategy_name}' not found")
    
    strategy_class = STRATEGY_MAP[strategy_name]
    params = strategy_class.get_parameters()
    
    return {"strategy": strategy_name, "parameters": params}


@app.post("/api/run")
def run_strategy(request: StrategyRequest):
    try:
        result = run_backtest(
            request.strategy,
            request.asset,
            request.parameters,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest error: {str(e)}")
