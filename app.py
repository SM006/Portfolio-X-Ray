import streamlit as st
import pandas as pd
import plotly.express as px

from analytics.portfolio import build_portfolio
from analytics.data_loader import fetch_price_data

from analytics.risk_analysis import (
    compute_asset_returns,
    compute_portfolio_returns,
    identify_stress_periods,
    compute_correlation_matrices,
    stress_loss_attribution,
    horizon_risk_summary
)

from analytics.insights import (
    portfolio_overview_insight,
    correlation_insight,
    stress_loss_insight,
    horizon_risk_insight,
    final_xray_summary
)

# =============================================================================
# Constants
# =============================================================================
ASSET_TYPES = ["Stock", "ETF", "Index", "Bond ETF", "Gold"]
TIME_HORIZONS = {
    "6 Months": 126,
    "1 Year": 252,
    "3 Years": 756
}

# =============================================================================
# Helper Functions
# =============================================================================
def initialize_session_state():
    """Initialize session state variables."""
    if "portfolio" not in st.session_state:
        st.session_state.portfolio = []

def add_portfolio_asset():
    """Form to add assets to the portfolio."""
    with st.form("portfolio_form"):
        ticker = st.text_input("Ticker (e.g. RELIANCE.NS)")
        amount = st.number_input("Amount Invested", min_value=0.0, step=1000.0)
        asset_type = st.selectbox("Asset Type", ASSET_TYPES)

        add_asset = st.form_submit_button("Add Asset")

    if add_asset and ticker and amount > 0:
        st.session_state.portfolio.append({
            "ticker": ticker.strip(),
            "amount": amount,
            "asset_type": asset_type
        })

def display_portfolio():
    """Display current portfolio and allow editing."""
    if not st.session_state.portfolio:
        return

    st.subheader("Current Portfolio")

    portfolio_df = pd.DataFrame(st.session_state.portfolio)

    edited_df = st.data_editor(
        portfolio_df,
        num_rows="dynamic",
        width='stretch',
        key="portfolio_editor"
    )

    # Clean the edited DataFrame
    edited_df = clean_portfolio_data(edited_df)
    st.session_state.portfolio = edited_df.to_dict("records")

    # Store portfolio_df for use in tabs
    if st.session_state.portfolio:
        st.session_state.portfolio_df = build_portfolio(st.session_state.portfolio)
        st.dataframe(st.session_state.portfolio_df)

def clean_portfolio_data(df):
    """Clean portfolio DataFrame by removing invalid entries."""
    df = df.dropna(subset=["ticker", "amount"])
    df = df[df["ticker"].str.strip() != ""]
    df = df[df["amount"] > 0]
    return df

def show_analysis_tabs():
    """Display analysis results in tabs."""
    # Run analysis button
    if st.button("Run Portfolio X-Ray", type="primary"):
        run_portfolio_analysis()

    # Show tabs only if analysis has been run
    if "analysis_results" in st.session_state:
        tab1, tab2, tab3 = st.tabs([
            "📊 Portfolio Overview",
            "🧠 Risk Analysis",
            "⏳ Time Horizon Risk"
        ])

        with tab1:
            display_portfolio_overview_tab()

        with tab2:
            display_risk_analysis_tab()

        with tab3:
            display_time_horizon_tab()

def run_portfolio_analysis():
    """Run the full portfolio analysis and store results."""
    try:
        portfolio_df = st.session_state.portfolio_df
        tickers = portfolio_df["ticker"].tolist()
        weights = portfolio_df.set_index("ticker")["allocation_pct"]

        # Fetch and compute returns
        prices = fetch_price_data(tickers)
        asset_returns = compute_asset_returns(prices)
        portfolio_returns = compute_portfolio_returns(asset_returns, weights)

        # Identify stress periods and compute correlations
        stress_dates = identify_stress_periods(portfolio_returns)
        normal_corr, stress_corr = compute_correlation_matrices(asset_returns, stress_dates)

        # Store results in session state
        st.session_state.analysis_results = {
            "portfolio_df": portfolio_df,
            "asset_returns": asset_returns,
            "portfolio_returns": portfolio_returns,
            "stress_dates": stress_dates,
            "normal_corr": normal_corr,
            "stress_corr": stress_corr,
            "stress_contribution": stress_loss_attribution(asset_returns, weights, stress_dates)
        }

        st.success("Analysis completed successfully!")

    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")

def display_portfolio_overview_tab():
    """Display portfolio overview in tab."""
    results = st.session_state.analysis_results
    portfolio_df = results["portfolio_df"]

    st.header("Portfolio Overview")
    total_value = portfolio_df["amount"].sum()
    st.metric("Total Portfolio Value", f"INR {total_value:,.0f}")

    st.subheader("Portfolio Distribution")
    st.dataframe(portfolio_df)

    
    fig_alloc = px.pie(
        portfolio_df,
        names="ticker",
        values="allocation_pct",
        title="Portfolio Allocation"
    )
    st.plotly_chart(fig_alloc, use_container_width=True)
    
    st.info(portfolio_overview_insight(portfolio_df))

def display_risk_analysis_tab():
    """Display risk analysis in tab."""
    results = st.session_state.analysis_results

    st.header("Risk Analysis")

    # Returns preview
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Asset Returns (Preview)")
        st.dataframe(results["asset_returns"].head())

    with col2:
        st.subheader("Portfolio Returns (Preview)")
        st.dataframe(results["portfolio_returns"].head())

    # Correlation analysis
    st.subheader("Correlation Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Normal Periods**")
        st.dataframe(results["normal_corr"])

    with col2:
        st.write("**Stress Periods**")
        st.dataframe(results["stress_corr"])

    st.info(correlation_insight(results["normal_corr"], results["stress_corr"]))

    # Stress loss attribution
    st.subheader("Stress Loss Attribution")
    st.dataframe(results["stress_contribution"].rename("Total Stress Contribution"))
    
    # Create stress loss chart
    stress_plot_df = results["stress_contribution"].reset_index()
    stress_plot_df.columns = ["Asset", "Stress Contribution"]

    fig_stress = px.bar(
        stress_plot_df,
        x="Asset",
        y="Stress Contribution",
        title="Stress Loss by Asset",
        color="Stress Contribution",
        color_continuous_scale="RdBu"
    )

    st.plotly_chart(fig_stress, width='stretch')
    
    stress_text = stress_loss_insight(results["stress_contribution"])
    st.info(stress_text)

def display_time_horizon_tab():
    """Display time horizon analysis in tab."""
    results = st.session_state.analysis_results
    portfolio_returns = results["portfolio_returns"]

    st.header("Time Horizon Risk Analysis")

    available_days = len(portfolio_returns)
    filtered_horizons = {k: v for k, v in TIME_HORIZONS.items() if v < available_days}

    if not filtered_horizons:
        st.warning("Not enough data for time horizon analysis. Need at least 126 trading days.")
        return

    horizon_df = horizon_risk_summary(portfolio_returns, filtered_horizons)
    st.dataframe(horizon_df)

    # Create horizon risk chart
    horizon_plot_df = horizon_df.melt(
        id_vars="Horizon",
        value_vars=["Worst Return", "Probability of Loss"],
        var_name="Metric",
        value_name="Value"
    )

    fig_horizon = px.bar(
        horizon_plot_df,
        x="Horizon",
        y="Value",
        color="Metric",
        barmode="group",
        title="Risk Across Investment Horizons"
    )

    st.plotly_chart(fig_horizon, width='stretch')

    horizon_text = horizon_risk_insight(horizon_df)
    st.info(horizon_text)

    # Final summary
    st.subheader("Portfolio X-Ray Summary")
    overview_text = portfolio_overview_insight(results["portfolio_df"])
    stress_text = stress_loss_insight(results["stress_contribution"])
    summary = final_xray_summary(overview_text, stress_text, horizon_text)
    st.success(summary)

# =============================================================================
# Main App
# =============================================================================
def main():
    st.title("Portfolio X-Ray")

    # Initialize session state
    initialize_session_state()

    # Portfolio input form (always visible)
    st.subheader("Enter your portfolio")
    add_portfolio_asset()

    # Display and edit portfolio
    display_portfolio()

    # If portfolio exists, show analysis tabs
    if st.session_state.portfolio:
        show_analysis_tabs()

if __name__ == "__main__":
    main()
            