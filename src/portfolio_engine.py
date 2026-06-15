import pandas as pd
from datetime import datetime

from data_cleaning import clean_transactions
from google_sheets import load_all_sheets
from market_data import get_current_prices


def calculate_positions(transactions):
    transactions = transactions.copy()

    buys = transactions[transactions["transaction_type"] == "BUY"]
    sells = transactions[transactions["transaction_type"] == "SELL"]

    buy_summary = (
    buys.groupby("ticker", as_index=False)
    .agg(
        company_name=("company_name", "first"),
        sector=("sector", "first"),
        total_buy_quantity=("quantity", "sum"),
        total_buy_amount=("net_amount", "sum"),
    )
)

    sell_summary = (
        sells.groupby(["ticker"], as_index=False)
        .agg(
            total_sell_quantity=("quantity", "sum"),
            total_sell_amount=("net_amount", "sum"),
        )
    )

    positions = buy_summary.merge(sell_summary, on="ticker", how="left")

    positions["total_sell_quantity"] = positions["total_sell_quantity"].fillna(0)
    positions["total_sell_amount"] = positions["total_sell_amount"].fillna(0)

    positions["open_quantity"] = (
        positions["total_buy_quantity"] - positions["total_sell_quantity"]
    )
    positions["calculated_position_tag"] = "ACTIVE"

    positions.loc[
        positions["open_quantity"] == 0,
        "calculated_position_tag"
    ] = "CLOSED"

    positions.loc[
        (positions["open_quantity"] > 0) & (positions["total_sell_quantity"] > 0),
        "calculated_position_tag"
    ] = "PARTIAL_EXIT"
    positions["average_buy_price"] = (
        positions["total_buy_amount"] / positions["total_buy_quantity"]
    )

    positions["remaining_cost"] = (
        positions["open_quantity"] * positions["average_buy_price"]
    )

    positions["realized_pnl"] = (
        positions["total_sell_amount"]
        - (positions["total_sell_quantity"] * positions["average_buy_price"])
    )
    #no:of days held
    date_summary = (
    transactions.groupby("ticker", as_index=False)
    .agg(
        first_buy_date=("transaction_date", "min"),
        last_transaction_date=("transaction_date", "max"),
    )
    )

    positions = positions.merge(date_summary, on="ticker", how="left")

    today = pd.Timestamp(datetime.today().date())

    positions["holding_end_date"] = positions["last_transaction_date"]

    positions.loc[
    positions["open_quantity"] > 0,
    "holding_end_date"
    ] = today

    positions["holding_days"] = (
    positions["holding_end_date"] - positions["first_buy_date"]
    ).dt.days


    #CAGR calculation
    positions["realized_return_pct"] = (
    positions["realized_pnl"]
    / (positions["total_sell_quantity"] * positions["average_buy_price"])
    ) * 100

    positions["realized_return_pct"] = positions["realized_return_pct"].fillna(0)
    #realized %
    positions["realized_return_pct"] = (
    positions["realized_pnl"]
    / (positions["total_sell_quantity"] * positions["average_buy_price"])
    ) * 100

    positions["realized_return_pct"] = positions["realized_return_pct"].fillna(0)

    #CAGR on realized positions
    positions["realized_cagr_pct"] = (
    ((1 + positions["realized_return_pct"] / 100) ** (365 / positions["holding_days"])) - 1
    ) * 100

    positions.loc[positions["holding_days"] <= 0, "realized_cagr_pct"] = 0
    positions["realized_cagr_pct"] = positions["realized_cagr_pct"].fillna(0)

    return positions

def add_market_values(positions):
    positions = positions.copy()

    tickers = positions["ticker"].tolist()
    prices = get_current_prices(tickers)

    positions = positions.merge(prices, on="ticker", how="left")

    positions["current_value"] = (
        positions["open_quantity"] * positions["current_price"]
    )

    positions["unrealized_pnl"] = (
        positions["current_value"] - positions["remaining_cost"]
    )

    positions["unrealized_return_pct"] = (
        positions["unrealized_pnl"] / positions["remaining_cost"]
    ) * 100

    positions["open_cagr_pct"] = (
    ((positions["current_value"] / positions["remaining_cost"]) ** (365 / positions["holding_days"])) - 1
    ) * 100

    positions.loc[
        (positions["remaining_cost"] <= 0) | (positions["holding_days"] <= 0),
        "open_cagr_pct"
    ] = 0

    positions["open_cagr_pct"] = positions["open_cagr_pct"].fillna(0)

    positions.loc[positions["remaining_cost"] == 0, "unrealized_return_pct"] = 0
    positions["unrealized_return_pct"] = positions["unrealized_return_pct"].fillna(0)

    positions["total_pnl"] = (
        positions["realized_pnl"] + positions["unrealized_pnl"]
    )

    positions["total_return_pct"] = (
        positions["total_pnl"] / positions["total_buy_amount"]
    ) * 100

    positions["total_return_pct"] = positions["total_return_pct"].fillna(0)

    total_current_value = positions["current_value"].sum()

    if total_current_value > 0:
        positions["allocation_pct"] = (
            positions["current_value"] / total_current_value
        ) * 100
    else:
        positions["allocation_pct"] = 0

    money_columns = [
        "open_cagr_pct",
        "average_buy_price",
        "remaining_cost",
        "current_price",
        "current_value",
        "realized_pnl",
        "unrealized_pnl",
        "total_pnl",
        "realized_return_pct",
        "realized_cagr_pct",
        "unrealized_return_pct",
        "total_return_pct",
        "allocation_pct",
    ]

    for column in money_columns:
        if column in positions.columns:
            positions[column] = positions[column].round(2)

    return positions

def calculate_xirr(cashflows):
    cashflows = [
        (pd.Timestamp(date), float(amount))
        for date, amount in cashflows
        if pd.notna(date) and amount != 0
    ]

    if not cashflows:
        return 0.0

    has_positive = any(amount > 0 for _, amount in cashflows)
    has_negative = any(amount < 0 for _, amount in cashflows)

    if not has_positive or not has_negative:
        return 0.0

    cashflows = sorted(cashflows, key=lambda item: item[0])
    start_date = cashflows[0][0]

    def npv(rate):
        total = 0.0

        for date, amount in cashflows:
            years = (date - start_date).days / 365.25
            total += amount / ((1 + rate) ** years)

        return total

    low = -0.9999
    high = 10.0
    mid = 0.0

    for _ in range(100):
        mid = (low + high) / 2.0
        value = npv(mid)

        if abs(value) < 0.0001:
            return round(mid * 100, 2)

        if value > 0:
            low = mid
        else:
            high = mid

    return round(mid * 100, 2)

def calculate_portfolio_xirr(transactions, positions):
    cashflows = []

    for _, row in transactions.iterrows():
        if row["transaction_type"] == "BUY":
            cashflows.append((row["transaction_date"], -row["net_amount"]))

        elif row["transaction_type"] == "SELL":
            cashflows.append((row["transaction_date"], row["net_amount"]))

    current_open_value = positions.loc[
        positions["open_quantity"] > 0,
        "current_value"
    ].sum()

    if current_open_value > 0:
        today = pd.Timestamp(datetime.today().date())
        cashflows.append((today, current_open_value))

    return round(calculate_xirr(cashflows), 2)

def calculate_portfolio_summary(positions, transactions=None):
    lifetime_capital_deployed = positions["total_buy_amount"].sum()

    open_positions = positions[positions["open_quantity"] > 0].copy()

    open_capital = open_positions["remaining_cost"].sum()
    current_value = open_positions["current_value"].sum()

    realized_pnl = positions["realized_pnl"].sum()
    unrealized_pnl = open_positions["unrealized_pnl"].sum()
    total_pnl = realized_pnl + unrealized_pnl

    lifetime_return_pct = 0
    if lifetime_capital_deployed > 0:
        lifetime_return_pct = (total_pnl / lifetime_capital_deployed) * 100

    open_return_pct = 0
    if open_capital > 0:
        open_return_pct = (unrealized_pnl / open_capital) * 100

    first_buy_date = positions["first_buy_date"].min()
    today = pd.Timestamp(datetime.today().date())
    lifetime_days = (today - first_buy_date).days

    lifetime_cagr_pct = 0
    if lifetime_days > 0 and lifetime_return_pct > -100:
        lifetime_cagr_pct = (
            ((1 + lifetime_return_pct / 100) ** (365 / lifetime_days)) - 1
        ) * 100

    open_cagr_pct = 0
    if current_value > 0:
        open_cagr_pct = (
            (open_positions["open_cagr_pct"] * open_positions["current_value"]).sum()
            / current_value
        )

    best_by_pct = positions.sort_values("total_return_pct", ascending=False).iloc[0]
    worst_by_pct = positions.sort_values("total_return_pct", ascending=True).iloc[0]

    best_by_amount = positions.sort_values("total_pnl", ascending=False).iloc[0]
    worst_by_amount = positions.sort_values("total_pnl", ascending=True).iloc[0]

    portfolio_xirr_pct = 0

    if transactions is not None:
        portfolio_xirr_pct = calculate_portfolio_xirr(transactions, positions)
        
    return {
        "lifetime_capital_deployed": round(lifetime_capital_deployed, 2),
        "open_capital": round(open_capital, 2),
        "current_value": round(current_value, 2),
        "realized_pnl": round(realized_pnl, 2),
        "unrealized_pnl": round(unrealized_pnl, 2),
        "total_pnl": round(total_pnl, 2),
        "lifetime_return_pct": round(lifetime_return_pct, 2),
        "open_return_pct": round(open_return_pct, 2),
        "lifetime_cagr_pct": round(lifetime_cagr_pct, 2),
        "open_cagr_pct": round(open_cagr_pct, 2),
        "open_positions_count": len(open_positions),
        "best_by_pct": best_by_pct["ticker"],
        "worst_by_pct": worst_by_pct["ticker"],
        "best_by_amount": best_by_amount["ticker"],
        "worst_by_amount": worst_by_amount["ticker"],
        "portfolio_xirr_pct": portfolio_xirr_pct,
    }



if __name__ == "__main__":
    data = load_all_sheets()
    transactions = clean_transactions(data["transactions"])

    positions = calculate_positions(transactions)
    positions = add_market_values(positions)

    display_columns = [
        "ticker",
        "company_name",
        "open_quantity",
        "average_buy_price",
        "current_price",
        "remaining_cost",
        "current_value",
        "realized_pnl",
        "unrealized_pnl",
        "total_pnl",
        "total_return_pct",
        "allocation_pct",
        "holding_days",
    ]

    print("Portfolio positions with live market data:")
    print(positions[display_columns].to_string(index=False))

    summary = calculate_portfolio_summary(positions)

    print("\nPortfolio summary:")
    for key, value in summary.items():
        print(f"{key}: {value}")
