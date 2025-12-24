import pandas as pd


def compute_asset_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute daily returns for each asset.
    """
    if prices.empty:
        raise ValueError("Price data is empty")

    returns = prices.pct_change().dropna()

    if returns.empty:
        raise ValueError("Returns data is empty")

    return returns


def compute_portfolio_returns(
    asset_returns: pd.DataFrame,
    weights: pd.Series
) -> pd.Series:
    """
    Compute daily portfolio returns using asset weights.
    """
    # Ensure alignment
    weights = weights.reindex(asset_returns.columns)

    portfolio_returns = asset_returns.dot(weights / 100)  # return * weight

    return portfolio_returns
