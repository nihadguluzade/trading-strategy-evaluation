import pandas as pd
import numpy as np
from pathlib import Path
from typing import Any

from src.strategies.base import BaseStrategy
from src.strategies.classic import (
    SMACrossover, RSIReversion, BollingerBands,
    MACDSignalCross, VolumeBreakout, BuyAndHold,
)

STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    "SMACrossover": SMACrossover,
    "RSIReversion": RSIReversion,
    "BollingerBands": BollingerBands,
    "MACDSignalCross": MACDSignalCross,
    "VolumeBreakout": VolumeBreakout,
    "BuyAndHold": BuyAndHold,
}

DATA_DIR = Path("/app/data/processed")
TRANSACTION_COST = 0.001  # 0.1% per trade
TRADING_DAYS_PER_YEAR = 252


def _load_csv(asset: str) -> pd.DataFrame:
    path = DATA_DIR / f"{asset}.csv"
    df = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
    df.sort_index(inplace=True)
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


def run_backtest(strategy_name: str, asset: str, parameters: dict[str, Any]) -> dict[str, Any]:
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(f"Unknown strategy '{strategy_name}'. Available: {list(STRATEGY_REGISTRY)}")

    df = _load_csv(asset)

    # Run chosen strategy
    strategy: BaseStrategy = STRATEGY_REGISTRY[strategy_name](**parameters)
    result = strategy.execute(df)
    result["Strategy_Returns"] = _apply_transaction_costs(result)

    # Run benchmark (Buy and Hold) on same data
    benchmark_result = BuyAndHold().execute(df)

    # Drop NaN rows introduced by rolling windows
    result.dropna(subset=["Strategy_Returns", "Market_Returns"], inplace=True)
    benchmark_result.dropna(subset=["Strategy_Returns", "Market_Returns"], inplace=True)

    kpis = _compute_kpis(result["Strategy_Returns"], result["Market_Returns"])

    return {
        "metrics": kpis,
        "charts": {
            "strategy": _build_equity_curve(result["Strategy_Returns"]),
            "benchmark": _build_equity_curve(benchmark_result["Strategy_Returns"]),
        },
    }
