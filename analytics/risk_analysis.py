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


def identify_stress_periods(
    portfolio_returns: pd.Series,
    quantile: float = 0.10
)->pd.Index:
    
    """
    Identify stress periods based on portfolio returns quantile.
    """
   
    if portfolio_returns.empty:
        raise ValueError("Portfolio returns data is empty")
    
    threshold=portfolio_returns.quantile(quantile)
    stress_dates=portfolio_returns[portfolio_returns <= threshold].index
    
    return stress_dates


def compute_correlation_matrices(
    asset_returns: pd.DataFrame,
    stress_dates: pd.Index
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute correlation matrices for normal and stress periods.
    """
    
    normal_corr=asset_returns.corr()

    stress_returns=asset_returns.loc[stress_dates]

    if stress_returns.empty:
        raise ValueError("No returns data for stress period")
    
    stress_corr=stress_returns.corr()
    
    return normal_corr, stress_corr

def stress_loss_attribution(
    asset_returns: pd.DataFrame,
    weights: pd.Series,
    stress_dates: pd.Index
) -> pd.Series:
    """
    Compute each asset's contribution to portfolio losses during stress periods.
    """
    stress_returns = asset_returns.loc[stress_dates]

    # Align weights
    weights = weights.reindex(stress_returns.columns)

    # Contribution per asset per day
    contributions = stress_returns.mul(weights, axis=1)

    # Sum over stress period
    stress_loss = contributions.sum()

    return stress_loss.sort_values()
