import yfinance as yf
import pandas as pd


def fetch_price_data(
    tickers: list,
    start: str = "2015-01-01",
    end: str | None = None
) -> tuple[pd.DataFrame, list[str]]:
    """
    Fetch historical price data from Yahoo Finance with auto-healing.
    
    Returns:
        tuple: (prices_df, dropped_tickers_list)
    """
    if not tickers:
        raise ValueError("Ticker list is empty")

    dropped_tickers = []
    working_tickers = tickers.copy()
    
    # Attempt to fetch data, iteratively removing bad assets if needed
    max_retries = len(tickers)
    for _ in range(max_retries):
        if not working_tickers:
            raise ValueError("All assets were dropped due to data issues")

        try:
            data = yf.download(
                working_tickers,
                start=start,
                end=end,
                progress=False,
                auto_adjust=False,
                group_by="ticker"  # Group by ticker to handle single/multi properly
            )
        except Exception as e:
            # If download fails entirely, we might have a bad ticker
            raise ValueError(f"Download failed: {str(e)}")

        if data.empty:
            raise ValueError("No data returned from Yahoo Finance")
            
        # Extract Adjusted Close
        prices = pd.DataFrame()
        
        # Handle the structure of yfinance result which varies by number of tickers
        if len(working_tickers) == 1:
            ticker = working_tickers[0]
            # When single ticker, columns are flat or just "Adj Close"
            if "Adj Close" in data.columns:
                 prices[ticker] = data["Adj Close"]
            else:
                 # Try fallback
                 prices[ticker] = data["Close"]
        else:
            # Multi-level columns
            for ticker in working_tickers:
                try:
                    # Accessing (Ticker, Adj Close) or just Adj Close depending on structure
                    if (ticker, "Adj Close") in data.columns:
                        prices[ticker] = data[(ticker, "Adj Close")]
                    elif ticker in data.columns and "Adj Close" in data[ticker].columns:
                         prices[ticker] = data[ticker]["Adj Close"]
                    elif "Adj Close" in data.columns and ticker in data["Adj Close"].columns:
                         prices[ticker] = data["Adj Close"][ticker]
                    else:
                        # Fallback to Close
                         if (ticker, "Close") in data.columns:
                            prices[ticker] = data[(ticker, "Close")]
                         elif ticker in data.columns and "Close" in data[ticker].columns:
                             prices[ticker] = data[ticker]["Close"]
                         elif "Close" in data.columns and ticker in data["Close"].columns:
                             prices[ticker] = data["Close"][ticker]
                except KeyError:
                    pass

        # Check for empty columns (tickers that returned no data)
        tickers_to_remove = []
        for ticker in working_tickers:
            if ticker not in prices.columns or prices[ticker].isna().all():
                tickers_to_remove.append(ticker)
        
        for ticker in tickers_to_remove:
            dropped_tickers.append(ticker)
            working_tickers.remove(ticker)
            
        if tickers_to_remove:
             # Loop again to fetch new data set without these bad tickers
             continue

        # Forward fill to handle slight date mismatches
        prices = prices.ffill()
        
        # Now check intersection
        cleaned_prices = prices.dropna()

        if not cleaned_prices.empty:
            # Success!
            return cleaned_prices, dropped_tickers
        
        # If we are here, dropna() killed everything. 
        # Find the limiting factor (the asset that starts the latest)
        valid_start_dates = prices.apply(lambda x: x.first_valid_index())
        latest_start = valid_start_dates.max()
        
        # Find who starts at this latest date (or very close to it)
        # We drop the asset with the LATEST start date because it restricts the history
        problematic_asset = valid_start_dates.idxmax()
        
        dropped_tickers.append(problematic_asset)
        working_tickers.remove(problematic_asset)
        
        # Loop continues to try again without this asset
        
    raise ValueError("Could not find a common date range for any subset of assets")
