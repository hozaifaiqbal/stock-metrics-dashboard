from io import BytesIO

import pandas as pd


TRANSACTION_COLUMNS = [
    "transaction_id",
    "broker",
    "account_name",
    "ticker",
    "company_name",
    "exchange",
    "sector",
    "transaction_type",
    "transaction_date",
    "quantity",
    "price",
    "gross_amount",
    "charges",
    "net_amount",
    "trade_label",
    "notes",
    "status",
    "position_tag",
]


STOCK_MASTER_COLUMNS = [
    "ticker",
    "company_name",
    "exchange",
    "sector",
    "industry",
    "market_cap_category",
    "is_active",
    "benchmark",
    "currency",
    "notes",
]


def create_sample_transactions():
    return pd.DataFrame(
        [
            {
                "transaction_id": "txn_001",
                "broker": "upstox",
                "account_name": "demo_user",
                "ticker": "COALINDIA.NS",
                "company_name": "Coal India",
                "exchange": "NSE",
                "sector": "Energy",
                "transaction_type": "BUY",
                "transaction_date": "2023-04-15",
                "quantity": 100,
                "price": 230,
                "gross_amount": 23000,
                "charges": 20,
                "net_amount": 23020,
                "trade_label": "initial_buy",
                "notes": "Demo buy transaction",
                "status": "COMPLETED",
                "position_tag": "ACTIVE",
            },
            {
                "transaction_id": "txn_002",
                "broker": "upstox",
                "account_name": "demo_user",
                "ticker": "COALINDIA.NS",
                "company_name": "Coal India",
                "exchange": "NSE",
                "sector": "Energy",
                "transaction_type": "SELL",
                "transaction_date": "2024-04-15",
                "quantity": 40,
                "price": 400,
                "gross_amount": 16000,
                "charges": 20,
                "net_amount": 15980,
                "trade_label": "partial_sell",
                "notes": "Demo partial exit",
                "status": "COMPLETED",
                "position_tag": "PARTIAL_PROFIT_BOOKED",
            },
        ]
    )


def create_stock_master_template():
    return pd.DataFrame(
        [
            {
                "ticker": "COALINDIA.NS",
                "company_name": "Coal India",
                "exchange": "NSE",
                "sector": "Energy",
                "industry": "Coal",
                "market_cap_category": "Large Cap",
                "is_active": "YES",
                "benchmark": "NIFTY50",
                "currency": "INR",
                "notes": "Demo stock master row",
            }
        ]
    )


def create_excel_template():
    output = BytesIO()

    transactions = create_sample_transactions()
    stock_master = create_stock_master_template()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        transactions.to_excel(writer, sheet_name="1_TRANSACTIONS", index=False)
        stock_master.to_excel(writer, sheet_name="2_STOCK_MASTER", index=False)

    output.seek(0)
    return output
