import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any
from datetime import datetime
import yfinance as yf
import time

from src.strategies.base import BaseStrategy
from src.strategies.classic import (
    SMACrossover, RSIReversion, BollingerBands,
    MACDSignalCross, VolumeBreakout, BuyAndHold,
)

STRATEGY_MAP: dict[str, type[BaseStrategy]] = {
    "SMACrossover": SMACrossover,
    "RSIReversion": RSIReversion,
    "BollingerBands": BollingerBands,
    "MACDSignalCross": MACDSignalCross,
    "VolumeBreakout": VolumeBreakout,
    "BuyAndHold": BuyAndHold,
}

DATA_DIR = Path("./data/processed")
TRANSACTION_COST = 0.001  # 0.1% per trade
TRADING_DAYS_PER_YEAR = 252


def _download_market_data(
    asset: str, start_date: str | datetime, end_date: str | datetime
) -> pd.DataFrame:
    """
    Download OHLCV data from yfinance and cache to CSV.
    Returns DataFrame with index=Date, columns=[Open, High, Low, Close, Volume].
    """
    # Ensure dates are strings for yfinance
    start_str = str(start_date)[:10] if not isinstance(start_date, str) else start_date
    end_str = str(end_date)[:10] if not isinstance(end_date, str) else end_date
    
    # Download from Yahoo Finance
    df = yf.download(asset, start=start_str, end=end_str, progress=False)
    
    if df.empty:
        raise ValueError(f"No data found for {asset} from {start_str} to {end_str}")
    
    # Flatten MultiIndex columns if yfinance returns them (happens with certain tickers)
    if isinstance(df.columns, pd.MultiIndex):
        # Take the first level (the OHLCV names) and drop the ticker level
        df.columns = df.columns.get_level_values(0)
    
    # Normalize: ensure UTC timezone, reset to naive (no tz info)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    
    # Standardize column names to Title Case (Open, High, Low, Close, Volume, Adj Close)
    df.columns = df.columns.str.title()
    df = df.sort_index()
    
    # Cache to CSV
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / f"{asset}.csv"
    df.to_csv(csv_path, index=True, index_label="Date")
    
    return df


def _load_csv(asset: str, start_date: str | datetime | None = None, end_date: str | datetime | None = None) -> pd.DataFrame:
    """Load market data from cached CSV, or download if not available."""
    csv_path = DATA_DIR / f"{asset}.csv"
    
    # If CSV doesn't exist or dates span beyond cached file, download fresh
    if not csv_path.exists():
        if start_date is None or end_date is None:
            raise FileNotFoundError(f"No cached data for {asset}. Provide start_date and end_date to download.")
        return _download_market_data(asset, start_date, end_date)
    
    # Load existing CSV
    df = pd.read_csv(csv_path, parse_dates=["Date"], index_col="Date")
    df.sort_index(inplace=True)
    
    # Ensure column names are Title Case (for consistency with strategy code)
    df.columns = df.columns.str.title()
    
    # If date range is specified, check if we have coverage or need to re-download
    if start_date is not None and end_date is not None:
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date)
        cached_start = df.index[0]
        cached_end = df.index[-1]
        
        # Re-download if requested range extends beyond cache
        if start_dt < cached_start or end_dt > cached_end:
            return _download_market_data(asset, start_date, end_date)
    
    return df


def _apply_transaction_costs(df: pd.DataFrame) -> pd.Series:
    """Subtract 0.1% cost on every day the signal changes (a trade occurs)."""
    signal_changes = df["Signal"].diff().abs() > 0
    cost = signal_changes.astype(float) * TRANSACTION_COST
    return df["Strategy_Returns"] - cost


def _compute_kpis(
    strategy_returns: pd.Series,
    market_returns: pd.Series,
) -> dict[str, float]:
    # Cumulative return
    cumulative_return = float((1 + strategy_returns).prod() - 1)

    # Annualized return
    n_days = len(strategy_returns)
    annualized_return = float((1 + cumulative_return) ** (TRADING_DAYS_PER_YEAR / n_days) - 1)

    # Annualized volatility
    annualized_volatility = float(strategy_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR))

    # Sharpe ratio (risk-free rate assumed 0)
    sharpe_ratio = float(annualized_return / annualized_volatility) if annualized_volatility != 0 else 0.0

    # Maximum drawdown
    equity = (1 + strategy_returns).cumprod()
    rolling_max = equity.cummax()
    drawdown = (equity - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min())

    # Win rate
    win_rate = float((strategy_returns > 0).mean())

    # Beta & Alpha vs market
    cov_matrix = np.cov(strategy_returns.dropna(), market_returns.dropna())
    beta = float(cov_matrix[0, 1] / cov_matrix[1, 1]) if cov_matrix[1, 1] != 0 else 0.0
    market_ann_return = float((1 + market_returns).prod() ** (TRADING_DAYS_PER_YEAR / n_days) - 1)
    alpha = float(annualized_return - beta * market_ann_return)

    return {
        "cumulativeReturn": round(cumulative_return, 6),
        "annualizedReturn": round(annualized_return, 6),
        "annualizedVolatility": round(annualized_volatility, 6),
        "sharpeRatio": round(sharpe_ratio, 6),
        "maxDrawdown": round(max_drawdown, 6),
        "winRate": round(win_rate, 6),
        "beta": round(beta, 6),
        "alpha": round(alpha, 6),
    }


def _build_equity_curve(returns: pd.Series, initial_value: float = 10_000.0) -> list[dict[str, Any]]:
    equity = initial_value * (1 + returns).cumprod()
    return [
        {"time": str(ts.date()), "value": round(v, 4)}
        for ts, v in equity.items()
    ]


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


def run_backtest(
    strategy_name: str,
    asset: str,
    parameters: dict[str, Any],
    start_date: str | datetime | None = None,
    end_date: str | datetime | None = None,
    initial_capital: float = 10_000.0,
) -> dict[str, Any]:
    if strategy_name not in STRATEGY_MAP:
        raise ValueError(f"Unknown strategy '{strategy_name}'. Available: {list(STRATEGY_MAP)}")

    # Load market data, downloading if necessary
    df = _load_csv(asset, start_date, end_date)
    
    # Filter to requested date range if specified
    if start_date is not None or end_date is not None:
        start_dt = pd.Timestamp(start_date) if start_date else df.index[0]
        end_dt = pd.Timestamp(end_date) if end_date else df.index[-1]
        df = df.loc[start_dt:end_dt]

    # TODO: add validation for invalid parameters -- return meaningful error

    _t0 = time.perf_counter()

    # Run chosen strategy
    strategy: BaseStrategy = STRATEGY_MAP[strategy_name](**parameters)
    result = strategy.execute(df)
    result["Strategy_Returns"] = _apply_transaction_costs(result)

    # Run benchmark (Buy and Hold) on same data
    benchmark_result = BuyAndHold().execute(df)

    # Drop NaN rows introduced by rolling windows
    result.dropna(subset=["Strategy_Returns", "Market_Returns"], inplace=True)
    benchmark_result.dropna(subset=["Strategy_Returns", "Market_Returns"], inplace=True)

    kpis = _compute_kpis(result["Strategy_Returns"], result["Market_Returns"])
    
    # Calculate final portfolio value
    final_value = initial_capital * (1 + result["Strategy_Returns"]).prod()
    kpis["finalPortfolioValue"] = round(final_value, 2)

    execution_time_ms = round((time.perf_counter() - _t0) * 1000, 1)

    return {
        "meta": {
            "strategy": strategy_name,
            "asset": asset,
            "start_date": str(df.index[0].date()) if len(df) > 0 else str(start_date),
            "end_date": str(df.index[-1].date()) if len(df) > 0 else str(end_date),
            "data_source": "yfinance",
            "initial_capital": initial_capital,
            "executionTimeMs": execution_time_ms,
        },
        "metrics": kpis,
        "charts": {
            "strategy": _build_equity_curve(result["Strategy_Returns"], initial_capital),
            "benchmark": _build_equity_curve(benchmark_result["Strategy_Returns"], initial_capital),
        },
        "trades": _extract_trades(result, asset),
    }
