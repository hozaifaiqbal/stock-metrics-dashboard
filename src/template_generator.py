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
                "broker": "demo",
                "account_name": "demo_user",
                "ticker": "RELIANCE.NS",
                "company_name": "Reliance Industries",
                "exchange": "NSE",
                "sector": "Energy",
                "transaction_type": "BUY",
                "transaction_date": "2020-01-01",
                "quantity": 31,
                "price": 806.45,
                "gross_amount": 25000,
                "charges": 20,
                "net_amount": 25020,
                "trade_label": "initial_buy",
                "notes": "Demo: Rs 25,000 invested on 2020-01-01",
                "status": "COMPLETED",
                "position_tag": "ACTIVE",
            },
            {
                "transaction_id": "txn_002",
                "broker": "demo",
                "account_name": "demo_user",
                "ticker": "TCS.NS",
                "company_name": "Tata Consultancy Services",
                "exchange": "NSE",
                "sector": "IT",
                "transaction_type": "BUY",
                "transaction_date": "2020-01-01",
                "quantity": 12,
                "price": 2083.33,
                "gross_amount": 25000,
                "charges": 20,
                "net_amount": 25020,
                "trade_label": "initial_buy",
                "notes": "Demo: Rs 25,000 invested on 2020-01-01",
                "status": "COMPLETED",
                "position_tag": "ACTIVE",
            },
            {
                "transaction_id": "txn_003",
                "broker": "demo",
                "account_name": "demo_user",
                "ticker": "ULTRACEMCO.NS",
                "company_name": "UltraTech Cement",
                "exchange": "NSE",
                "sector": "Cement",
                "transaction_type": "BUY",
                "transaction_date": "2020-01-01",
                "quantity": 6,
                "price": 4166.67,
                "gross_amount": 25000,
                "charges": 20,
                "net_amount": 25020,
                "trade_label": "initial_buy",
                "notes": "Demo: Rs 25,000 invested on 2020-01-01",
                "status": "COMPLETED",
                "position_tag": "PROFIT_BOOKED",
            },
            {
                "transaction_id": "txn_004",
                "broker": "demo",
                "account_name": "demo_user",
                "ticker": "ULTRACEMCO.NS",
                "company_name": "UltraTech Cement",
                "exchange": "NSE",
                "sector": "Cement",
                "transaction_type": "SELL",
                "transaction_date": "2025-01-01",
                "quantity": 6,
                "price": 11500,
                "gross_amount": 69000,
                "charges": 50,
                "net_amount": 68950,
                "trade_label": "full_exit",
                "notes": "Demo: UltraTech Cement sold after five years",
                "status": "COMPLETED",
                "position_tag": "PROFIT_BOOKED",
            },
            {
                "transaction_id": "txn_005",
                "broker": "demo",
                "account_name": "demo_user",
                "ticker": "ASIANPAINT.NS",
                "company_name": "Asian Paints",
                "exchange": "NSE",
                "sector": "Paints",
                "transaction_type": "BUY",
                "transaction_date": "2020-01-01",
                "quantity": 15,
                "price": 1666.67,
                "gross_amount": 25000,
                "charges": 20,
                "net_amount": 25020,
                "trade_label": "initial_buy",
                "notes": "Demo: Rs 25,000 invested on 2020-01-01",
                "status": "COMPLETED",
                "position_tag": "ACTIVE",
            },
        ]
    )



def create_stock_master_template():
    return pd.DataFrame(
        [
            {
                "ticker": "RELIANCE.NS",
                "company_name": "Reliance Industries",
                "exchange": "NSE",
                "sector": "Energy",
                "industry": "Oil & Gas Refining and Marketing",
                "market_cap_category": "Large Cap",
                "is_active": "YES",
                "benchmark": "NIFTY50",
                "currency": "INR",
                "notes": "Demo holding",
            },
            {
                "ticker": "TCS.NS",
                "company_name": "Tata Consultancy Services",
                "exchange": "NSE",
                "sector": "IT",
                "industry": "Information Technology Services",
                "market_cap_category": "Large Cap",
                "is_active": "YES",
                "benchmark": "NIFTY50",
                "currency": "INR",
                "notes": "Demo holding",
            },
            {
                "ticker": "ULTRACEMCO.NS",
                "company_name": "UltraTech Cement",
                "exchange": "NSE",
                "sector": "Cement",
                "industry": "Cement and Construction Materials",
                "market_cap_category": "Large Cap",
                "is_active": "NO",
                "benchmark": "NIFTY50",
                "currency": "INR",
                "notes": "Demo exited position",
            },
            {
                "ticker": "ASIANPAINT.NS",
                "company_name": "Asian Paints",
                "exchange": "NSE",
                "sector": "Paints",
                "industry": "Paints and Coatings",
                "market_cap_category": "Large Cap",
                "is_active": "YES",
                "benchmark": "NIFTY50",
                "currency": "INR",
                "notes": "Demo holding",
            },
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
