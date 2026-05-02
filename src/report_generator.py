import base64
from chart_generator import create_weekly_report_charts

from datetime import datetime
from pathlib import Path
#from weasyprint import HTML (weasyprint is somewhat laggy so we are not using it)
from playwright.sync_api import sync_playwright


from google_sheets import load_all_sheets
from data_cleaning import clean_transactions
from portfolio_engine import (
    calculate_positions,
    add_market_values,
    calculate_portfolio_summary,
)
from benchmark import calculate_benchmark_comparison, get_performance_message

def image_to_base64(image_path):
    image_path = Path(image_path)
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"


def generate_weekly_html_report():
    data = load_all_sheets()
    transactions = clean_transactions(data["transactions"])

    positions = calculate_positions(transactions)
    positions = add_market_values(positions)

    summary = calculate_portfolio_summary(positions)
    benchmark = calculate_benchmark_comparison(transactions, summary)
    messages = get_performance_message(benchmark)

    chart_dir = Path("reports/weekly/assets")
    charts = create_weekly_report_charts(positions, chart_dir)

    allocation_chart = image_to_base64(charts["allocation_chart"])
    pnl_chart = image_to_base64(charts["pnl_chart"])
    return_chart = image_to_base64(charts["return_chart"])


    today = datetime.today().strftime("%Y-%m-%d")

    report_html = f"""
    <html>
    <head>
        <title>Weekly Portfolio Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                color: #222;
            }}
            h1, h2 {{
                color: #1f2937;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }}
            .card {{
                border: 1px solid #ddd;
                padding: 16px;
                border-radius: 8px;
                background: #f9fafb;
            }}
            .label {{
                font-size: 12px;
                color: #666;
            }}
            .value {{
                font-size: 22px;
                font-weight: bold;
                margin-top: 8px;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-top: 20px;
                font-size: 13px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: right;
            }}
            th {{
                background: #f3f4f6;
            }}
            td:first-child, th:first-child {{
                text-align: left;
            }}
            .message {{
                background: #e8f2ff;
                padding: 14px;
                border-radius: 6px;
                margin: 10px 0;

            
            }}
        .chart-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
        margin-top: 20px;
        }}

        .chart-card {{
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 12px;
        background: #ffffff;
        }}

        .chart-card img {{
            width: 100%;
        }}

        </style>
    </head>
    <body>
        <h1>Weekly Portfolio Report</h1>
        <p>Report Date: {today}</p>

        <h2>Portfolio Summary</h2>
        <div class="grid">
            <div class="card"><div class="label">Open Capital</div><div class="value">Rs {summary["open_capital"]:,.0f}</div></div>
            <div class="card"><div class="label">Current Value</div><div class="value">Rs {summary["current_value"]:,.0f}</div></div>
            <div class="card"><div class="label">Total P&L</div><div class="value">Rs {summary["total_pnl"]:,.0f}</div></div>
            <div class="card"><div class="label">Lifetime CAGR</div><div class="value">{summary["lifetime_cagr_pct"]}%</div></div>
        </div>

        <h2>Benchmark</h2>
        <div class="message">{messages["nifty_message"]}</div>
        <div class="message">{messages["fd_message"]}</div>

        <h2>Charts</h2>

        <div class="chart-grid">
            <div class="chart-card">
                <img src="{allocation_chart}" />
            </div>

            <div class="chart-card">
                <img src="{pnl_chart}" />
            </div>

            <div class="chart-card">
                <img src="{return_chart}" />
            </div>
        </div>


        <h2>Live Positions</h2>
        {positions[[
            "ticker",
            "company_name",
            "open_quantity",
            "current_price",
            "current_value",
            "total_pnl",
            "total_return_pct",
            "open_cagr_pct",
            "allocation_pct",
        ]].to_html(index=False)}
    </body>
    </html>
    """

    output_dir = Path("reports/weekly")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"weekly_report_{today}.html"
    output_path.write_text(report_html, encoding="utf-8")

    return output_path




def convert_html_to_pdf(html_path):
    html_path = Path(html_path).resolve()
    pdf_path = html_path.with_suffix(".pdf")

    if not html_path.exists():
        raise FileNotFoundError(f"HTML report not found: {html_path}")

    # Read the HTML content first
    html_content = html_path.read_text(encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. Manually set the HTML content instead of navigating to a URI
        page.set_content(html_content, wait_until="networkidle")
        
        # 2. Give it a tiny bit more time to render the CSS Grid/Styles
        page.wait_for_timeout(2000) 

        page.pdf(
            path=str(pdf_path),
            format="A4",
            print_background=True, # Critical for your .card background colors!
            margin={
                "top": "12mm",
                "right": "10mm",
                "bottom": "12mm",
                "left": "10mm",
            },
        )
        browser.close()

    return pdf_path


    

if __name__ == "__main__":
    html_path = generate_weekly_html_report()
    pdf_path = convert_html_to_pdf(html_path)

    print(f"Weekly HTML report generated: {html_path}")
    print(f"Weekly PDF report generated: {pdf_path}")
