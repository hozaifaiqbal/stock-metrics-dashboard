import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

sys.path.insert(0, str(SRC_PATH))

import plotly.express as px
import streamlit as st

import pandas as pd
import os

def load_uploaded_file(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        transactions = pd.read_csv(uploaded_file)
        stock_master = pd.DataFrame()
        return transactions, stock_master

    if uploaded_file.name.endswith((".xlsx", ".xls")):
        excel_file = pd.ExcelFile(uploaded_file)

        transactions = pd.read_excel(excel_file, sheet_name="1_TRANSACTIONS")

        if "2_STOCK_MASTER" in excel_file.sheet_names:
            stock_master = pd.read_excel(excel_file, sheet_name="2_STOCK_MASTER")
        else:
            stock_master = pd.DataFrame()

        return transactions, stock_master

    raise ValueError("Please upload a CSV or Excel file.")

from google_sheets import load_all_sheets
from data_cleaning import clean_transactions
from portfolio_engine import (
    calculate_positions,
    add_market_values,
    calculate_portfolio_summary,
)
from benchmark import calculate_benchmark_comparison, get_performance_message
from stock_metadata import enrich_positions_with_metadata
from template_generator import create_excel_template
from risk_metrics import calculate_risk_metrics




st.set_page_config(
    page_title="Stock Metrics Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("Stock Metrics Dashboard")

template_file = create_excel_template()

st.download_button(
    label="Download Template & Fill Data",
    data=template_file,
    file_name="stock_dashboard_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
st.caption(
    "Your data stays private. Download the template, fill it locally, and upload it here to generate your dashboard."
)

st.sidebar.header("Data Source")

show_google_sheet_mode = (
    os.getenv("SHOW_GOOGLE_SHEET_MODE", "false").lower() == "true"
)

data_source_options = ["Upload CSV/Excel"]

if show_google_sheet_mode:
    data_source_options.append("Google Sheet")

data_source = st.sidebar.radio(
    "Choose input method",
    data_source_options,
)

uploaded_file = None

if data_source == "Upload CSV/Excel":
    st.sidebar.caption(
        "Download the template, fill your data locally, then upload it here."
    )

    uploaded_file = st.sidebar.file_uploader(
        "Upload portfolio file",
        type=["csv", "xlsx", "xls"],
    )

with st.spinner("Loading portfolio data..."):
    if data_source == "Google Sheet":
        data = load_all_sheets()
        raw_transactions = data["transactions"]
        stock_master = data.get("stock_master", pd.DataFrame())

    else:
        if uploaded_file is None:
            st.info("Upload a CSV or Excel file to generate your dashboard.")
            st.stop()

        raw_transactions, stock_master = load_uploaded_file(uploaded_file)

    transactions = clean_transactions(raw_transactions)
    positions = calculate_positions(transactions)
    positions = add_market_values(positions)

    if not stock_master.empty:
        try:
            positions = enrich_positions_with_metadata(positions, stock_master)
        except Exception:
            pass

    summary = calculate_portfolio_summary(positions)
    benchmark = calculate_benchmark_comparison(transactions, summary)
    risk_metrics = calculate_risk_metrics(positions)
    messages = get_performance_message(benchmark)



st.subheader("Portfolio Summary")

row1 = st.columns(4)
row1[0].metric("Lifetime Capital Deployed", f"₹{summary['lifetime_capital_deployed']:,.0f}")
row1[1].metric("Open Capital", f"₹{summary['open_capital']:,.0f}")
row1[2].metric("Current Open Value", f"₹{summary['current_value']:,.0f}")
row1[3].metric("Open Positions", summary["open_positions_count"])

row2 = st.columns(4)
row2[0].metric("Realized P&L", f"₹{summary['realized_pnl']:,.0f}")
row2[1].metric("Unrealized P&L", f"₹{summary['unrealized_pnl']:,.0f}")
row2[2].metric("Total P&L", f"₹{summary['total_pnl']:,.0f}")
row2[3].metric("Lifetime Return", f"{summary['lifetime_return_pct']}%")

row3 = st.columns(4)
row3[0].metric("Lifetime CAGR", f"{summary['lifetime_cagr_pct']}%")
row3[1].metric("Open Return", f"{summary['open_return_pct']}%")
row3[2].metric("Open CAGR", f"{summary['open_cagr_pct']}%")
row3[3].metric("Worst by Amount", summary["worst_by_amount"])

row4 = st.columns(4)
row4[0].metric("Best by Amount", summary["best_by_amount"])
row4[1].metric("Best by %", summary["best_by_pct"])
row4[2].metric("Worst by %", summary["worst_by_pct"])

st.subheader("Benchmark Comparison")

bench_cols = st.columns(4)

bench_cols[0].metric("Nifty 50 Return", f"{benchmark['nifty_return_pct']}%")
bench_cols[1].metric("Your Alpha vs Nifty", f"{benchmark['nifty_alpha_pct']}%")
bench_cols[2].metric("USD-INR Change", f"{benchmark['usd_inr_return_pct']}%")
bench_cols[3].metric("FD CAGR Alpha", f"{benchmark['fd_alpha_pct']}%")

st.info(messages["nifty_message"])
st.info(messages["fd_message"])


st.divider()

st.subheader("Risk Metrics")

risk_cols = st.columns(4)

risk_cols[0].metric("Beta", risk_metrics["portfolio_beta"])
risk_cols[1].metric("Alpha", f"{risk_metrics['portfolio_alpha_pct']}%")
risk_cols[2].metric("Volatility", f"{risk_metrics['annual_volatility_pct']}%")
risk_cols[3].metric("Sharpe Ratio", risk_metrics["sharpe_ratio"])

risk_cols_2 = st.columns(4)

risk_cols_2[0].metric("Sortino Ratio", risk_metrics["sortino_ratio"])
risk_cols_2[1].metric("Max Drawdown", f"{risk_metrics['max_drawdown_pct']}%")
risk_cols_2[2].metric("Correlation vs Nifty", risk_metrics["correlation_with_benchmark"])


st.divider()


display_columns = [
    "ticker",
    "company_name",
    "sector",
    "open_quantity",
    "average_buy_price",
    "current_price",
    "remaining_cost",
    "current_value",
    "realized_pnl",
    "unrealized_pnl",
    "total_pnl",
    "total_return_pct",
    "open_cagr_pct",
    "allocation_pct",
    "holding_days",
]


st.subheader("Live Positions")
st.dataframe(
    positions[display_columns],
    use_container_width=True,
    hide_index=True,
)

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Stock Allocation")
    fig_allocation = px.pie(
        positions,
        names="ticker",
        values="current_value",
        hole=0.35,
    )
    st.plotly_chart(fig_allocation, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Sector Allocation")
    sector_df = (
        positions.groupby("final_sector", as_index=False)
        .agg(current_value=("current_value", "sum"))
    )
    fig_sector = px.pie(
        sector_df,
        names="final_sector",
        values="current_value",
        hole=0.35,
    )
    st.plotly_chart(fig_sector, use_container_width=True)

with right:
    st.subheader("Industry Allocation")
    industry_df = (
        positions.groupby("final_industry", as_index=False)
        .agg(current_value=("current_value", "sum"))
    )
    fig_industry = px.pie(
        industry_df,
        names="final_industry",
        values="current_value",
        hole=0.35,
    )
    st.plotly_chart(fig_industry, use_container_width=True)


st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Total P&L by Stock")
    fig_pnl = px.bar(
        positions.sort_values("total_pnl"),
        x="ticker",
        y="total_pnl",
        color="total_pnl",
        text="total_pnl",
    )
    st.plotly_chart(fig_pnl, use_container_width=True)

with right:
    st.subheader("Return % by Stock")
    fig_return = px.bar(
        positions.sort_values("total_return_pct"),
        x="ticker",
        y="total_return_pct",
        color="total_return_pct",
        text="total_return_pct",
    )
    st.plotly_chart(fig_return, use_container_width=True)
