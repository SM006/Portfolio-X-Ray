import pandas as pd

#Portfolio math lives here

def build_portfolio(portfolio_records: list) -> pd.DataFrame:
    
    """
        Takes raw portfolio records (ticker, amount, asset_type)
        and returns a normalized portfolio DataFrame with weights.
    """
    
    if not portfolio_records:
        raise ValueError("Portfolio records list is empty.")    
    
    df=pd.DataFrame(portfolio_records)
    
    #Basic Validation
    
    if(df["amount"] <= 0).any():
        raise ValueError("Amount Invested need to be positive.")
    
    total_value = df["amount"].sum()
    df["allocation_pct"] = df["amount"] / total_value *100  # Weight in percentage
    
    return df