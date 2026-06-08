import pandas as pd
import yfinance as yf


def fetch_stock_metadata(tickers):
    rows = []

    for ticker in sorted(set(tickers)):
        try:
            info = yf.Ticker(ticker).info

            rows.append({
                "ticker": ticker,
                "internet_company_name": info.get("longName") or info.get("shortName"),
                "internet_sector": info.get("sector"),
                "internet_industry": info.get("industry"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
            })

        except Exception as error:
            rows.append({
                "ticker": ticker,
                "internet_company_name": None,
                "internet_sector": None,
                "internet_industry": None,
                "market_cap": None,
                "currency": None,
                "metadata_error": str(error),
            })

    return pd.DataFrame(rows)


def enrich_positions_with_metadata(positions, stock_master):
    positions = positions.copy()
    stock_master = stock_master.copy()

    tickers = positions["ticker"].tolist()
    internet_metadata = fetch_stock_metadata(tickers)

    positions = positions.merge(internet_metadata, on="ticker", how="left")

    fallback_columns = [
        "ticker",
        "sector",
        "industry",
        "market_cap_category",
        "currency",
    ]

    available_fallback_columns = [
        column for column in fallback_columns if column in stock_master.columns
    ]

    stock_master_small = stock_master[available_fallback_columns].copy()

    positions = positions.merge(
        stock_master_small,
        on="ticker",
        how="left",
        suffixes=("", "_manual"),
    )

    positions["final_sector"] = (
        positions["internet_sector"]
        .fillna(positions.get("sector_manual"))
        .fillna(positions.get("sector"))
        .fillna("Unknown")
    )

    positions["final_industry"] = (
        positions["internet_industry"]
        .fillna(positions.get("industry"))
        .fillna("Unknown")
    )

    positions["final_currency"] = (
        positions["currency"]
        .fillna(positions.get("currency_manual"))
        .fillna("INR")
    )

    return positions


if __name__ == "__main__":
    from google_sheets import load_all_sheets
    from data_cleaning import clean_transactions
    from portfolio_engine import calculate_positions, add_market_values

    data = load_all_sheets()
    transactions = clean_transactions(data["transactions"])

    positions = calculate_positions(transactions)
    positions = add_market_values(positions)

    enriched = enrich_positions_with_metadata(
        positions,
        data["stock_master"],
    )

    print(enriched[[
        "ticker",
        "company_name",
        "final_sector",
        "final_industry",
        "market_cap",
        "final_currency",
    ]].to_string(index=False))
