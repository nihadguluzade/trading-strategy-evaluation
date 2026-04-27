from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.engine.core import run_backtest, STRATEGY_REGISTRY
import pandas as pd
import numpy as np
import sys, os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from src.strategies.classic import (
    SMACrossover,
    RSIReversion,
    BollingerBands,
    MACDSignalCross,
    VolumeBreakout,
    BuyAndHold,
)

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

STRATEGY_MAP = {
    "SMA Crossover": SMACrossover,
    "RSI Reversion": RSIReversion,
    "Bollinger Bands": BollingerBands,
    "MACD Signal Cross": MACDSignalCross,
    "Volume Breakout": VolumeBreakout,
    "Buy and Hold": BuyAndHold,
}


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
    return {"strategies": list(STRATEGY_REGISTRY.keys())}


@app.get("/strategies")
def list_strategies():
    return {
        "strategies": [
            {"name": "SMA Crossover", "params": ["short_window", "long_window"]},
            {
                "name": "RSI Reversion",
                "params": ["window", "lower_bound", "upper_bound"],
            },
            {"name": "Bollinger Bands", "params": ["window", "num_std"]},
            {"name": "MACD Signal Cross", "params": ["fast", "slow", "signal"]},
            {
                "name": "Volume Breakout",
                "params": ["volume_window", "volume_multiplier"],
            },
            {"name": "Buy and Hold", "params": []},
        ]
    }


def _generate_synthetic_ohlcv(asset: str, start: str, end: str) -> pd.DataFrame:
    seed = sum(ord(c) for c in asset)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start=start, end=end)
    n = len(dates)
    mu, sigma = 0.0003, 0.012
    returns = rng.normal(mu, sigma, n)
    price = 150.0 * np.exp(np.cumsum(returns))
    volume = rng.integers(5_000_000, 30_000_000, n).astype(float)
    high = price * (1 + rng.uniform(0, 0.015, n))
    low = price * (1 - rng.uniform(0, 0.015, n))
    return pd.DataFrame(
        {"Open": price, "High": high, "Low": low, "Close": price, "Volume": volume},
        index=dates,
    )


def _fetch_data(asset: str, start: str, end: str) -> pd.DataFrame:
    try:
        import yfinance as yf

        df = yf.download(asset, start=start, end=end, progress=False, auto_adjust=True)
        if df.empty:
            raise ValueError("empty")
        df.index = pd.to_datetime(df.index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    except Exception:
        return _generate_synthetic_ohlcv(asset, start, end)


def _compute_metrics(df: pd.DataFrame, initial_capital: float):
    strat_r = df["Strategy_Returns"].dropna()
    market_r = df["Market_Returns"].dropna()

    strat_equity = initial_capital * (1 + strat_r).cumprod()
    bench_equity = initial_capital * (1 + market_r).cumprod()

    total_return = (strat_equity.iloc[-1] / initial_capital) - 1
    n_years = len(strat_r) / 252
    ann_return = (1 + total_return) ** (1 / max(n_years, 0.01)) - 1
    ann_vol = strat_r.std() * np.sqrt(252)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    roll_max = strat_equity.cummax()
    drawdown = (strat_equity - roll_max) / roll_max
    max_dd = drawdown.min()

    win_rate = (strat_r > 0).sum() / len(strat_r) if len(strat_r) > 0 else 0.0

    cov_matrix = np.cov(strat_r.values, market_r.values)
    beta = cov_matrix[0, 1] / cov_matrix[1, 1] if cov_matrix[1, 1] > 0 else 1.0
    bench_ann = (bench_equity.iloc[-1] / initial_capital) ** (
        1 / max(n_years, 0.01)
    ) - 1
    alpha = ann_return - beta * bench_ann

    neg = strat_r[strat_r < 0]
    sortino = (
        ann_return / (neg.std() * np.sqrt(252))
        if len(neg) > 0 and neg.std() > 0
        else 0.0
    )

    return {
        "metrics": {
            "cumulativeReturn": round(total_return, 4),
            "annualizedReturn": round(ann_return, 4),
            "annualizedVolatility": round(ann_vol, 4),
            "sharpeRatio": round(sharpe, 4),
            "sortinoRatio": round(sortino, 4),
            "maxDrawdown": round(max_dd, 4),
            "winRate": round(win_rate, 4),
            "beta": round(beta, 4),
            "alpha": round(alpha, 4),
            "finalPortfolioValue": round(float(strat_equity.iloc[-1]), 2),
        },
        "charts": {
            "strategy": [
                {"time": t.strftime("%Y-%m-%d"), "value": round(float(v), 2)}
                for t, v in strat_equity.items()
            ],
            "benchmark": [
                {"time": t.strftime("%Y-%m-%d"), "value": round(float(v), 2)}
                for t, v in bench_equity.items()
            ],
        },
    }


def _extract_trades(df: pd.DataFrame, asset: str):
    trades = []
    sig = df["Signal"].dropna()
    price = df["Close"]
    prev_sig = 0
    entry_date = entry_price = None

    for date, s in sig.items():
        s_int = int(s)
        if s_int != prev_sig:
            if prev_sig != 0 and entry_date is not None:
                exit_price = float(price.loc[date])
                ep = float(entry_price)
                ret = (exit_price - ep) / ep * prev_sig
                trades.append(
                    {
                        "entryDate": entry_date.strftime("%Y-%m-%d"),
                        "exitDate": date.strftime("%Y-%m-%d"),
                        "entryPrice": round(ep, 2),
                        "exitPrice": round(exit_price, 2),
                        "action": "long" if prev_sig == 1 else "short",
                        "symbol": asset,
                        "return": round(ret, 4),
                        "days": (date - entry_date).days,
                        "pnl": round((exit_price - ep) * prev_sig, 2),
                    }
                )
            if s_int != 0:
                entry_date = date
                entry_price = price.loc[date]
        prev_sig = s_int

    return sorted(trades, key=lambda t: t["exitDate"], reverse=True)[:20]


@app.post("/run")
def run_strategy(req: StrategyRequest):
    strategy_cls = STRATEGY_MAP.get(req.strategy)
    if strategy_cls is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy '{req.strategy}'. Available: {list(STRATEGY_MAP.keys())}",
        )

    df = _fetch_data(req.asset, req.start_date, req.end_date)
    if df.empty:
        raise HTTPException(status_code=422, detail="No price data available.")

    valid_params = strategy_cls.__init__.__code__.co_varnames
    try:
        strat = strategy_cls(
            **{k: v for k, v in req.parameters.items() if k in valid_params}
        )
    except TypeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {e}")

    result_df = strat.execute(df)
    output = _compute_metrics(result_df, req.initial_capital)
    output["trades"] = _extract_trades(result_df, req.asset)
    output["meta"] = {
        "strategy": req.strategy,
        "asset": req.asset,
        "start_date": req.start_date,
        "end_date": req.end_date,
        "parameters": req.parameters,
        "data_source": "yfinance" if "yfinance" in sys.modules else "synthetic",
    }
    return output

@app.post("/api/run")
def run_strategy(request: StrategyRequest):
    try:
        result = run_backtest(request.strategy, request.asset, request.parameters)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"No data file found for asset '{request.asset}'.")
