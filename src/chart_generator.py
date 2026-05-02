from pathlib import Path

import plotly.express as px


def create_weekly_report_charts(positions, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    allocation_path = output_dir / "stock_allocation.png"
    pnl_path = output_dir / "pnl_by_stock.png"
    return_path = output_dir / "return_by_stock.png"

    fig_allocation = px.pie(
        positions,
        names="ticker",
        values="current_value",
        hole=0.35,
        title="Stock Allocation",
    )
    fig_allocation.write_image(str(allocation_path), width=900, height=500)

    fig_pnl = px.bar(
        positions.sort_values("total_pnl"),
        x="ticker",
        y="total_pnl",
        color="total_pnl",
        text="total_pnl",
        title="Total P&L by Stock",
    )
    fig_pnl.write_image(str(pnl_path), width=900, height=500)

    fig_return = px.bar(
        positions.sort_values("total_return_pct"),
        x="ticker",
        y="total_return_pct",
        color="total_return_pct",
        text="total_return_pct",
        title="Return % by Stock",
    )
    fig_return.write_image(str(return_path), width=900, height=500)

    return {
        "allocation_chart": allocation_path,
        "pnl_chart": pnl_path,
        "return_chart": return_path,
    }
