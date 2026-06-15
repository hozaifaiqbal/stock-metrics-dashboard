from datetime import datetime

import pandas as pd
import yfinance as yf

from portfolio_engine import calculate_xirr

def get_first_buy_date(transactions):
    buy_transactions = transactions[transactions["transaction_type"] == "BUY"]

    if buy_transactions.empty:
        raise ValueError("No BUY transactions found.")

    return buy_transactions["transaction_date"].min()


def get_close_series(ticker, start_date, end_date):
    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        auto_adjust=True,
        progress=False,
    )

    if data is None or data.empty:
        raise ValueError(f"No benchmark data found for {ticker}")

    close = data["Close"].squeeze()

    if not isinstance(close, pd.Series):
        raise ValueError(f"Unexpected close price format for {ticker}")

    close = close.dropna()


    if close.empty:
        raise ValueError(f"No close price data found for {ticker}")

    return close


def get_benchmark_return(ticker, start_date, end_date=None):
    if end_date is None:
        end_date = datetime.today().date()

    close = get_close_series(ticker, start_date, end_date)

    start_price = float(close.iloc[0])
    end_price = float(close.iloc[-1])

    absolute_return_pct = ((end_price / start_price) - 1) * 100

    days = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days

    cagr_pct = 0
    if days > 0:
        cagr_pct = (((end_price / start_price) ** (365 / days)) - 1) * 100

    return {
        "ticker": ticker,
        "start_price": round(start_price, 2),
        "end_price": round(end_price, 2),
        "absolute_return_pct": round(absolute_return_pct, 2),
        "cagr_pct": round(cagr_pct, 2),
        "days": days,
    }


def calculate_benchmark_comparison(transactions, portfolio_summary):
    start_date = get_first_buy_date(transactions)

    nifty = get_benchmark_return("^NSEI", start_date)
    usd_inr = get_benchmark_return("INR=X", start_date)

    portfolio_return = portfolio_summary["lifetime_return_pct"]
    portfolio_cagr = portfolio_summary["lifetime_cagr_pct"]

    cashflow_matched_nifty = calculate_cashflow_matched_benchmark(transactions)
    portfolio_xirr = portfolio_summary.get("portfolio_xirr_pct", portfolio_cagr)

    return {
        "start_date": start_date.date(),
        "portfolio_return_pct": round(portfolio_return, 2),
        "portfolio_cagr_pct": round(portfolio_cagr, 2),
        "nifty_return_pct": nifty["absolute_return_pct"],
        "nifty_cagr_pct": nifty["cagr_pct"],
        "nifty_alpha_pct": round(portfolio_return - nifty["absolute_return_pct"], 2),
        "nifty_cagr_alpha_pct": round(portfolio_cagr - nifty["cagr_pct"], 2),
        "usd_inr_return_pct": usd_inr["absolute_return_pct"],
        "usd_inr_cagr_pct": usd_inr["cagr_pct"],
        "usd_inr_alpha_pct": round(portfolio_return - usd_inr["absolute_return_pct"], 2),
        "fd_assumed_cagr_pct": 7.0,
        "fd_alpha_pct": round(portfolio_cagr - 7.0, 2),
        "portfolio_xirr_pct": portfolio_xirr,
        "nifty_cashflow_xirr_pct": cashflow_matched_nifty["benchmark_xirr_pct"],
        "xirr_alpha_vs_nifty_pct": round(
            portfolio_xirr - cashflow_matched_nifty["benchmark_xirr_pct"], 2
        ),
        "nifty_cashflow_current_value": cashflow_matched_nifty["benchmark_current_value"],
    }


def get_performance_message(benchmark):
    if benchmark["nifty_alpha_pct"] > 0:
        nifty_message = f"You are beating Nifty 50 by {benchmark['nifty_alpha_pct']}% since your first recorded buy."
    else:
        nifty_message = f"You are behind Nifty 50 by {abs(benchmark['nifty_alpha_pct'])}% since your first recorded buy."

    if benchmark["fd_alpha_pct"] > 0:
        fd_message = f"Your CAGR is ahead of a 7% FD assumption by {benchmark['fd_alpha_pct']}%."
    else:
        fd_message = f"Your CAGR is behind a 7% FD assumption by {abs(benchmark['fd_alpha_pct'])}%."

    return {
        "nifty_message": nifty_message,
        "fd_message": fd_message,
    }

def calculate_cashflow_matched_benchmark(transactions, benchmark_ticker="^NSEI"):
    transactions = transactions.sort_values("transaction_date").copy()

    start_date = transactions["transaction_date"].min()
    end_date = pd.Timestamp(datetime.today().date()) + pd.Timedelta(days=1)

    close = get_close_series(benchmark_ticker, start_date, end_date)

    benchmark_units = 0
    cashflows = []

    for _, row in transactions.iterrows():
        trade_date = pd.Timestamp(row["transaction_date"])
        available_prices = close[close.index >= trade_date]

        if available_prices.empty:
            continue

        benchmark_price = float(available_prices.iloc[0])
        amount = float(row["net_amount"])

        if row["transaction_type"] == "BUY":
            benchmark_units += amount / benchmark_price
            cashflows.append((trade_date, -amount))

        elif row["transaction_type"] == "SELL":
            benchmark_units -= amount / benchmark_price
            cashflows.append((trade_date, amount))

    benchmark_current_value = benchmark_units * float(close.iloc[-1])

    if benchmark_current_value > 0:
        cashflows.append((pd.Timestamp(end_date), benchmark_current_value))

    benchmark_xirr = calculate_xirr(cashflows)

    return {
        "benchmark_current_value": round(benchmark_current_value, 2),
        "benchmark_xirr_pct": round(benchmark_xirr, 2),
    }