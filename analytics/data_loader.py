import yfinance as yf
import pandas as pd


def fetch_price_data(
    tickers: list,
    start: str = "2015-01-01",
    end: str | None = None
) -> pd.DataFrame:
    """
    Fetch historical price data from Yahoo Finance.
    Uses Adjusted Close if available, otherwise falls back to Close.
    """

    if not tickers:
        raise ValueError("Ticker list is empty")

    data = yf.download(
        tickers,
        start=start,
        end=end,
        progress=False,
        auto_adjust=False
    )

    if data.empty:
        raise ValueError("No data returned from Yahoo Finance")

    # Case 1: Multiple tickers (MultiIndex columns)
    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" in data.columns.levels[0]:
            prices = data["Adj Close"]
        else:
            raise ValueError("Neither Adjusted Close nor Close available")

    # Case 2: Single ticker (flat columns)
    else:
        if "Adj Close" in data.columns:
            prices = data["Adj Close"].to_frame(name=tickers[0])
        else:
            raise ValueError("Neither Adjusted Close nor Close available")

    prices = prices.ffill().dropna()

    if prices.empty:
        raise ValueError("Price data is empty after cleaning")

    return prices
