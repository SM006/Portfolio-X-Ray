import streamlit as st
import pandas as pd

from analytics.portfolio import build_portfolio
from analytics.data_loader import fetch_price_data

from analytics.risk_analysis import (
    compute_asset_returns,
    compute_portfolio_returns,
    identify_stress_periods,
    compute_correlation_matrices,
    stress_loss_attribution
)

st.title("Portfolio X-Ray")
st.subheader("Enter your portfolio")

asset_types = ["Stock", "ETF", "Index", "Bond ETF", "Gold"]   # Define asset types

# Initialize session state
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

with st.form("portfolio_form"):
    ticker = st.text_input("Ticker (e.g. RELIANCE.NS)")
    amount = st.number_input("Amount Invested", min_value=0.0, step=1000.0)
    asset_type = st.selectbox("Asset Type", asset_types)

    add_asset = st.form_submit_button("Add Asset")

if add_asset:
    if ticker and amount > 0:
        st.session_state.portfolio.append({
            "ticker": ticker.strip(),
            "amount": amount,
            "asset_type": asset_type
        })

# Show portfolio
if st.session_state.portfolio:
    st.subheader("Current Portfolio")

    portfolio_df = pd.DataFrame(st.session_state.portfolio)

    edited_df = st.data_editor(
        portfolio_df,
        num_rows="dynamic",
        use_container_width=True,
        key="portfolio_editor"
    )
    
    # Clean the edited DataFrame: remove rows with missing ticker or amount <= 0
    edited_df = edited_df.dropna(subset=["ticker", "amount"])
    edited_df = edited_df[edited_df["ticker"].str.strip() != ""]
    edited_df = edited_df[edited_df["amount"] > 0]
    
    st.session_state.portfolio = edited_df.to_dict("records")

    # Sync edited data back to session state
    if st.session_state.portfolio:
        try:
            portfolio_df = build_portfolio(st.session_state.portfolio)
            
            st.subheader("Current Portfolio Distribution")
            st.dataframe(portfolio_df)
            
            if st.button("Run Portfolio X-Ray"):
                try:
                    tickers = portfolio_df["ticker"].tolist()
                    weights = portfolio_df.set_index("ticker")["allocation_pct"]

                    prices = fetch_price_data(tickers)

                    asset_returns = compute_asset_returns(prices)
                    portfolio_returns = compute_portfolio_returns(asset_returns, weights)
                    
                    stress_dates=identify_stress_periods(portfolio_returns)
                    normal_corr, stress_corr=compute_correlation_matrices(asset_returns, stress_dates)

                    st.subheader("Asset Returns (Preview)")
                    st.dataframe(asset_returns.head())

                    st.subheader("Portfolio Returns (Preview)")
                    st.dataframe(portfolio_returns.head())

                    st.success("Returns computed successfully")
                    
                    st.subheader("Correlation Matrix (Normal Periods)")
                    st.dataframe(normal_corr)

                    st.subheader("Correlation Matrix (Stress Periods)")
                    st.dataframe(stress_corr)
                    
                    stress_contribution = stress_loss_attribution(
                        asset_returns,
                        weights,
                        stress_dates
                    )

                    st.subheader("Stress Loss Attribution")
                    st.dataframe(stress_contribution.rename("Total Stress Contribution"))

                except Exception as e:
                    st.error(str(e))

                
        except ValueError as e:
            st.error(f"Error in portfolio data: {e}")
            