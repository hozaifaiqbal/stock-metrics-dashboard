import yfinance as yf
import pandas as pd


def get_current_prices(tickers):
    tickers = list(set(tickers))

    data = yf.download(
        tickers,
        period="5d",
        auto_adjust=True,
        progress=False,
    )

    if data is None or data.empty:
        raise ValueError("No price data received from Yahoo Finance.")

    if "Close" not in data:
        raise ValueError("Close price column missing from Yahoo Finance data.")

    close_prices = data["Close"]


    if isinstance(close_prices, pd.Series):
        return pd.DataFrame(
            {
                "ticker": [tickers[0]],
                "current_price": [close_prices.dropna().iloc[-1]],
            }
        )

    latest_prices = close_prices.ffill().iloc[-1]

    price_df = latest_prices.reset_index()
    price_df.columns = ["ticker", "current_price"]

    return price_df


if __name__ == "__main__":
    sample_tickers = ["COALINDIA.NS", "ASIANPAINT.NS", "COLPAL.NS"]
    prices = get_current_prices(sample_tickers)
    print(prices.to_string(index=False))
