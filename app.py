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
from risk_metrics import calculate_risk_metrics
from template_generator import (
    create_excel_template,
    create_sample_transactions,
    create_stock_master_template,
)
from report_generator import generate_dashboard_pdf_report



st.set_page_config(
    page_title="Stock Metrics Dashboard",
    page_icon="📈",
    layout="wide",
)

st.markdown(
    """
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 24px 30px;
        border-radius: 8px;
        border-bottom: 4px solid #3b82f6;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    ">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h1 style="
                    color: #ffffff;
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    margin: 0;
                    font-size: 32px;
                    font-weight: 800;
                    letter-spacing: -0.5px;
                ">
                    📈 Stock Metrics Dashboard
                </h1>
                <p style="
                    color: #94a3b8;
                    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                    margin: 5px 0 0 0;
                    font-size: 14px;
                    font-weight: 400;
                ">
                    Institutional-Grade Portfolio Analytics & Quantitative Risk Tool
                </p>
            </div>
            <div style="
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.2);
                padding: 6px 14px;
                border-radius: 20px;
            ">
                <span style="
                    color: #60a5fa;
                    font-size: 12px;
                    font-weight: 600;
                    font-family: monospace;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                ">
                    ● Live Engine Connected
                </span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

template_file = create_excel_template()

st.download_button(
    label="Download Template & Fill Data",
    data=template_file,
    file_name="stock_dashboard_template.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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

if data_source == "Upload CSV/Excel":
    st.caption(
        "Your data stays private. Download the template, fill it locally, and upload it here to generate your dashboard."
    )

    if uploaded_file is None:
        st.info("Showing demo dashboard. Upload your filled template to view your own portfolio.")
        st.caption(
            "Demo dashboard assumes Rs 1,00,000 invested equally in Reliance, TCS, UltraTech Cement, and Asian Paints on 2020-01-01. UltraTech Cement is shown as sold, while the other three remain open holdings."
        )

elif data_source == "Google Sheet":
    st.markdown(
        """
        <p style="
            color: #1e3a8a; 
            font-family: 'Georgia', serif; 
            font-size: 15px; 
            font-style: italic; 
            background-color: #eff6ff; 
            padding: 14px; 
            border-radius: 8px; 
            border: 1px dashed #3b82f6;
        ">
           Personal Google Sheet mode: calculations are based on my recorded trades and current positions from the date of 15 June 2026.As i am tracking this portfolio for myself and i am measuring my performance from this specific date.
        </p>
        """,
        unsafe_allow_html=True
    )

with st.spinner("Loading portfolio data..."):
    if data_source == "Google Sheet":
        data = load_all_sheets()
        raw_transactions = data["transactions"]
        stock_master = data.get("stock_master", pd.DataFrame())

    else:
        if uploaded_file is None:
            raw_transactions = create_sample_transactions()
            stock_master = create_stock_master_template()
        else:
            raw_transactions, stock_master = load_uploaded_file(uploaded_file)

    transactions = clean_transactions(raw_transactions)
    broker_options = ["All"] + sorted(transactions["broker"].dropna().unique().tolist())

    selected_broker = st.sidebar.selectbox(
    "Broker / Demat account",
    broker_options,
    )

    if selected_broker != "All":
        transactions = transactions[transactions["broker"] == selected_broker]
   
    account_options = ["All"] + sorted(
    transactions["account_name"].dropna().astype(str).unique().tolist()
    )

    selected_account = st.sidebar.selectbox(
    "Account",
    account_options,
    )

    if selected_account != "All":
        transactions = transactions[transactions["account_name"] == selected_account]
    
    positions = calculate_positions(transactions)
    positions = add_market_values(positions)

    try:
        positions = enrich_positions_with_metadata(positions, stock_master)
    except Exception:
        positions["final_sector"] = positions.get("sector", "Unknown")
        positions["final_industry"] = "Unknown"

    summary = calculate_portfolio_summary(positions, transactions)
    benchmark = calculate_benchmark_comparison(transactions, summary)
    risk_metrics = calculate_risk_metrics(positions)
    messages = get_performance_message(benchmark)



st.subheader("Portfolio Summary")
st.divider()

if st.button("Prepare PDF Report"):
    with st.spinner("Creating PDF report..."):
        pdf_path = generate_dashboard_pdf_report(
            positions=positions,
            summary=summary,
            benchmark=benchmark,
            messages=messages,
            risk_metrics=risk_metrics,
        )

        st.session_state["dashboard_pdf_bytes"] = Path(pdf_path).read_bytes()
        st.session_state["dashboard_pdf_name"] = Path(pdf_path).name

if "dashboard_pdf_bytes" in st.session_state:
    st.download_button(
        label="Download PDF Report",
        data=st.session_state["dashboard_pdf_bytes"],
        file_name=st.session_state["dashboard_pdf_name"],
        mime="application/pdf",
    )


st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #f0f4f8 0%, #ffffff 100%);
        padding: 10px 15px;
        border-left: 6px solid #1e3a8a;
        border-radius: 4px;
        margin-top: 20px;
        margin-bottom: 20px;
    ">
        <h2 style="
            color: #1e3a8a;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 0.5px;
        ">
            📊 Major Ratios of My Portfolio
        </h2>
    </div>
    """,
    unsafe_allow_html=True
)

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

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #f0f4f8 0%, #ffffff 100%);
        padding: 10px 15px;
        border-left: 6px solid #1e3a8a;
        border-radius: 4px;
        margin-top: 20px;
        margin-bottom: 20px;
    ">
        <h2 style="
            color: #1e3a8a;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 0.5px;
        ">
            Benchmark Comparison and Performance Analysis
        </h2>
    </div>
    """,
    unsafe_allow_html=True
)

bench_cols = st.columns(4)

bench_cols[0].metric("Nifty 50 Return", f"{benchmark['nifty_return_pct']}%")
bench_cols[1].metric("Your Alpha vs Nifty", f"{benchmark['nifty_alpha_pct']}%")
bench_cols[2].metric("USD-INR Change", f"{benchmark['usd_inr_return_pct']}%")
bench_cols[3].metric("FD CAGR Alpha", f"{benchmark['fd_alpha_pct']}%")

xirr_cols = st.columns(4)

xirr_cols[0].metric("Portfolio XIRR", f"{benchmark['portfolio_xirr_pct']}%")
xirr_cols[1].metric("Nifty Cashflow XIRR", f"{benchmark['nifty_cashflow_xirr_pct']}%")
xirr_cols[2].metric("XIRR Alpha vs Nifty", f"{benchmark['xirr_alpha_vs_nifty_pct']}%")

st.info(messages["nifty_message"])
st.info(messages["fd_message"])


st.divider()

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #f0f4f8 0%, #ffffff 100%);
        padding: 10px 15px;
        border-left: 6px solid #1e3a8a;
        border-radius: 4px;
        margin-top: 20px;
        margin-bottom: 20px;
    ">
        <h2 style="
            color: #1e3a8a;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            letter-spacing: 0.5px;
        ">
           Risk Metrics
        </h2>
    </div>
    """,
    unsafe_allow_html=True
)

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
