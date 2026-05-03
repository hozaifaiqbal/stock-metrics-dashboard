import numpy as np
import pandas as pd
import yfinance as yf


TRADING_DAYS = 252


def get_close_prices(tickers, period="3y"):
    data = yf.download(
        tickers,
        period=period,
        auto_adjust=True,
        progress=False,
    )

    if data is None or data.empty:
        raise ValueError("No historical price data received.")

    close = data["Close"]

    if isinstance(close, pd.Series):
        close = close.to_frame(name=tickers[0])

    close = close.dropna(how="all")
    return close


def calculate_max_drawdown(portfolio_returns):
    cumulative = (1 + portfolio_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative / running_max) - 1
    return drawdown.min() * 100


def calculate_risk_metrics(positions, benchmark_ticker="^NSEI", period="3y", risk_free_rate=0.07):
    open_positions = positions[positions["open_quantity"] > 0].copy()

    if open_positions.empty:
        return {
            "portfolio_beta": 0,
            "portfolio_alpha_pct": 0,
            "annual_volatility_pct": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "max_drawdown_pct": 0,
            "correlation_with_benchmark": 0,
        }

    tickers = open_positions["ticker"].tolist()
    all_tickers = tickers + [benchmark_ticker]

    close = get_close_prices(all_tickers, period=period)
    returns = close.pct_change().dropna()

    available_tickers = [ticker for ticker in tickers if ticker in returns.columns]

    if not available_tickers or benchmark_ticker not in returns.columns:
        raise ValueError("Not enough price data to calculate risk metrics.")

    open_positions = open_positions[open_positions["ticker"].isin(available_tickers)]

    weights = open_positions.set_index("ticker")["current_value"]
    weights = weights / weights.sum()

    portfolio_returns = returns[available_tickers].mul(weights, axis=1).sum(axis=1)
    benchmark_returns = returns[benchmark_ticker]

    aligned = pd.concat(
        [portfolio_returns.rename("portfolio"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()

    portfolio_returns = aligned["portfolio"]
    benchmark_returns = aligned["benchmark"]

    portfolio_annual_return = portfolio_returns.mean() * TRADING_DAYS
    benchmark_annual_return = benchmark_returns.mean() * TRADING_DAYS

    annual_volatility = portfolio_returns.std() * np.sqrt(TRADING_DAYS)

    benchmark_variance = benchmark_returns.var()
    beta = 0
    if benchmark_variance != 0:
        beta = portfolio_returns.cov(benchmark_returns) / benchmark_variance

    alpha = (
        portfolio_annual_return
        - risk_free_rate
        - beta * (benchmark_annual_return - risk_free_rate)
    )

    sharpe_ratio = 0
    if annual_volatility != 0:
        sharpe_ratio = (portfolio_annual_return - risk_free_rate) / annual_volatility

    downside_returns = portfolio_returns[portfolio_returns < 0]
    downside_deviation = downside_returns.std() * np.sqrt(TRADING_DAYS)

    sortino_ratio = 0
    if downside_deviation != 0 and not np.isnan(downside_deviation):
        sortino_ratio = (portfolio_annual_return - risk_free_rate) / downside_deviation

    max_drawdown = calculate_max_drawdown(portfolio_returns)
    correlation = portfolio_returns.corr(benchmark_returns)

    return {
        "portfolio_beta": round(beta, 2),
        "portfolio_alpha_pct": round(alpha * 100, 2),
        "annual_volatility_pct": round(annual_volatility * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sortino_ratio": round(sortino_ratio, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "correlation_with_benchmark": round(correlation, 2),
    }


if __name__ == "__main__":
    from google_sheets import load_all_sheets
    from data_cleaning import clean_transactions
    from portfolio_engine import calculate_positions, add_market_values

    data = load_all_sheets()
    transactions = clean_transactions(data["transactions"])

    positions = calculate_positions(transactions)
    positions = add_market_values(positions)

    metrics = calculate_risk_metrics(positions)

    print("Risk metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")
