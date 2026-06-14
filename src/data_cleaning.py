import pandas as pd

REQUIRED_TRANSACTION_COLUMNS = [
    "ticker",
    "transaction_type",
    "transaction_date",
    "quantity",
    "price",
]

OPTIONAL_TRANSACTION_COLUMNS = {
    "transaction_id": "",
    "broker": "unknown",
    "account_name": "default",
    "company_name": "",
    "exchange": "NSE",
    "sector": "Unknown",
    "gross_amount": None,
    "charges": 0,
    "net_amount": None,
    "trade_label": "",
    "notes": "",
    "status": "COMPLETED",
    "position_tag": "",
}


def validate_columns(df, required_columns):
    missing_columns = []

    for column in required_columns:
        if column not in df.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")


def clean_transactions(df):
    df = df.copy()

    df = df.dropna(how="all")

    validate_columns(df, REQUIRED_TRANSACTION_COLUMNS)

    for column, default_value in OPTIONAL_TRANSACTION_COLUMNS.items():
        if column not in df.columns:
            df[column] = default_value

    validate_columns(df, REQUIRED_TRANSACTION_COLUMNS)

    text_columns = [
        "transaction_id",
        "broker",
        "account_name",
        "ticker",
        "company_name",
        "exchange",
        "sector",
        "transaction_type",
        "trade_label",
        "status",
        "position_tag",
    ]

    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    df["ticker"] = df["ticker"].str.upper()
    df["exchange"] = df["exchange"].str.upper()
    df["transaction_type"] = df["transaction_type"].str.upper()
    df["status"] = df["status"].str.upper()
    df["position_tag"] = df["position_tag"].str.upper()

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")

    numeric_columns = [
        "quantity",
        "price",
        "gross_amount",
        "charges",
        "net_amount",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    if df["transaction_date"].isna().any():
        bad_rows = df[df["transaction_date"].isna()]["transaction_id"].tolist()
        raise ValueError(f"Invalid transaction_date in rows: {bad_rows}")

    core_numeric_columns = ["quantity", "price"]

    if df[core_numeric_columns].isna().any().any():
        raise ValueError("Quantity and price are required for every transaction.")

    df["charges"] = df["charges"].fillna(0)

    df["gross_amount"] = df["gross_amount"].fillna(
        df["quantity"] * df["price"]
    )

    buy_mask = df["transaction_type"] == "BUY"
    sell_mask = df["transaction_type"] == "SELL"

    df.loc[buy_mask, "net_amount"] = df.loc[buy_mask, "net_amount"].fillna(
        df.loc[buy_mask, "gross_amount"] + df.loc[buy_mask, "charges"]
    )

    df.loc[sell_mask, "net_amount"] = df.loc[sell_mask, "net_amount"].fillna(
        df.loc[sell_mask, "gross_amount"] - df.loc[sell_mask, "charges"]
    )    
    return df


if __name__ == "__main__":
    from google_sheets import load_all_sheets

    data = load_all_sheets()
    transactions = clean_transactions(data["transactions"])

    print("Cleaned transactions:")
    print(transactions.head())
    print(transactions.dtypes)
