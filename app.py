import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

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
# Modern UI Configuration
# =============================================================================
st.set_page_config(
    page_title="Portfolio X-Ray",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling with theme support
# =============================================================================
# Helper Functions
# =============================================================================
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# =============================================================================
# Main App
# =============================================================================

# Constants
# =============================================================================
ASSET_TYPES = ["Stock", "ETF", "Index", "Bond ETF", "Gold"]
TIME_HORIZONS = {
    "1 Month": 21,
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
    """Form to add assets to the portfolio with modern styling and validation."""
    with st.form("portfolio_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            ticker = st.text_input(
                "Ticker Symbol",
                placeholder="e.g. RELIANCE.NS, AAPL, SPY",
                help="Enter stock/ETF ticker (Yahoo Finance format)"
            )

        with col2:
            amount = st.number_input(
                "Amount (INR)",
                min_value=100.0,
                step=1000.0,
                help="Investment amount in rupees (minimum ₹100)"
            )

        with col3:
            asset_type = st.selectbox(
                "Type",
                ASSET_TYPES,
                help="Asset category"
            )

        submitted = st.form_submit_button("Add Asset", use_container_width=True)

    if submitted:
        # Validation
        if not ticker.strip():
            st.error("Please enter a ticker symbol")
            return

        if amount <= 0:
            st.error("Please enter a valid investment amount")
            return

        # Check for duplicate tickers
        existing_tickers = [asset["ticker"].upper() for asset in st.session_state.portfolio]
        if ticker.strip().upper() in existing_tickers:
            st.warning(f"{ticker.strip().upper()} is already in your portfolio")
            return

        # Add asset
        st.session_state.portfolio.append({
            "ticker": ticker.strip().upper(),
            "amount": amount,
            "asset_type": asset_type
        })
        st.success(f"Successfully added {ticker.strip().upper()} (INR {amount:,.0f}) to portfolio!")
        st.rerun()

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

def show_analysis_section():
    """Display the analysis section with modern styling and better UX."""
    st.markdown('<div class="section-header">Portfolio Analysis</div>', unsafe_allow_html=True)
    st.markdown("Run comprehensive risk analysis on your portfolio")

    # Check if portfolio is valid for analysis
    if not st.session_state.portfolio:
        st.warning("Add some assets to your portfolio before running analysis")
        return

    # Validate portfolio before analysis
    portfolio_df = pd.DataFrame(st.session_state.portfolio)
    validation_errors = []

    if portfolio_df["ticker"].isna().any() or (portfolio_df["ticker"].str.strip() == "").any():
        validation_errors.append("Missing ticker symbols")

    if (portfolio_df["amount"] <= 0).any():
        validation_errors.append("Invalid investment amounts")

    if len(portfolio_df["ticker"].unique()) != len(portfolio_df):
        validation_errors.append("Duplicate ticker symbols")

    if validation_errors:
        st.error("Please fix the following issues before running analysis:")
        for error in validation_errors:
            st.error(f"- {error}")
        return

    # Show portfolio summary before analysis
    total_value = portfolio_df["amount"].sum()
    num_assets = len(portfolio_df)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Assets to Analyze", num_assets)
    with col2:
        st.metric("Portfolio Value", f"INR {total_value:,.0f}")
    with col3:
        st.metric("Est. Analysis Time", "~30 seconds")

    # Run analysis button with modern styling
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Run Portfolio X-Ray Analysis", type="primary", use_container_width=True):
            with st.spinner("Analyzing your portfolio... This may take a moment."):
                run_portfolio_analysis()
    
    with st.expander("ℹ️ Data Analysis Note"):
        st.markdown("""
        <small>
        To ensure accurate risk metrics, the analysis requires a common historical data range for all assets.
        If an asset has insufficient history (e.g., recent IPO) that would significantly shorten the analysis period for the entire portfolio, 
        it may be <strong>automatically excluded</strong> from the risk calculations.
        </small>
        """, unsafe_allow_html=True)

    # Show tabs only if analysis has been run
    if "analysis_results" in st.session_state:
        st.markdown("---")
        display_analysis_tabs()

def display_analysis_tabs():
    """Display analysis results in modern tabs."""
    tab1, tab2, tab3 = st.tabs([
        "Portfolio Overview",
        "Risk Analysis",
        "Time Horizon Risk"
    ])

    with tab1:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        display_portfolio_overview_tab()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        display_risk_analysis_tab()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="tab-content">', unsafe_allow_html=True)
        display_time_horizon_tab()
        st.markdown('</div>', unsafe_allow_html=True)

def run_portfolio_analysis():
    """Run the full portfolio analysis and store results with better error handling."""
    try:
        portfolio_df = st.session_state.portfolio_df
        tickers = portfolio_df["ticker"].tolist()

        # Progress feedback
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.text("Fetching market data...")
        progress_bar.progress(20)

        # Fetch and compute returns (Auto-Healing)
        try:
            prices, dropped_tickers = fetch_price_data(tickers)
        except ValueError as e:
            # This catches "All assets were dropped" or other fatal errors
            st.error(f"Data Source Error: {str(e)}")
            progress_bar.empty()
            status_text.empty()
            return

        # If any tickers were dropped, alert the user but proceed
        if dropped_tickers:
            msg = f"Excluded the following assets due to insufficient historical data: {', '.join(dropped_tickers)}"
            st.warning(msg)
            
            # We must filter our portfolio_df to ignore these assets heavily
            # Keep only the valid tickers
            valid_tickers = [t for t in tickers if t not in dropped_tickers]
            
            # NOTE: We do NOT re-normalize weights here automatically, because that changes user intent.
            # Instead, we just proceed. The compute_portfolio_returns logic will align weights.
            # Effectively, dropped assets contribute 0 return (like cash with 0% interest).
            
            # Filter the portfolio DF used for subsequent steps
            portfolio_df = portfolio_df[portfolio_df["ticker"].isin(valid_tickers)]
            
            if portfolio_df.empty:
                st.error("No valid assets remaining after data cleaning.")
                return

        progress_bar.progress(40)

        status_text.text("Computing returns...")
        asset_returns = compute_asset_returns(prices)
        portfolio_returns = compute_portfolio_returns(asset_returns, portfolio_df.set_index("ticker")["allocation_pct"])
        progress_bar.progress(60)

        status_text.text("Identifying stress periods...")
        stress_dates = identify_stress_periods(portfolio_returns)
        normal_corr, stress_corr = compute_correlation_matrices(asset_returns, stress_dates)
        progress_bar.progress(80)

        status_text.text("Finalizing analysis...")
        stress_contribution = stress_loss_attribution(asset_returns, portfolio_df.set_index("ticker")["allocation_pct"], stress_dates)
        progress_bar.progress(100)

        # Store results in session state
        st.session_state.analysis_results = {
            "portfolio_df": portfolio_df,
            "asset_returns": asset_returns,
            "portfolio_returns": portfolio_returns,
            "stress_dates": stress_dates,
            "normal_corr": normal_corr,
            "stress_corr": stress_corr,
            "stress_contribution": stress_contribution
        }

        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        st.success("Analysis completed successfully! Explore the results in the tabs below.")

    except ValueError as e:
        status_text.empty()
        progress_bar.empty()
        st.error(f"Data Error: {str(e)}")
        st.info("Troubleshooting Tips:")
        st.info("- Check that all ticker symbols are valid and available on Yahoo Finance")
        st.info("- Ensure tickers follow the correct format (e.g., RELIANCE.NS for Indian stocks)")
        st.info("- Some assets may not have sufficient historical data")

    except Exception as e:
        status_text.empty()
        progress_bar.empty()
        st.error(f"Analysis failed: {str(e)}")
        st.info("If the problem persists, try refreshing the page or contact support")

def display_portfolio_overview_tab():
    """Display portfolio overview in tab."""
    results = st.session_state.analysis_results
    portfolio_df = results["portfolio_df"]

    st.header("Portfolio Overview")
    total_value = portfolio_df["amount"].sum()
    st.metric("Total Portfolio Value", f"INR {total_value:,.0f}")

    st.subheader("Portfolio Distribution")
    st.dataframe(portfolio_df)

    # Add allocation pie chart
    fig_alloc = px.pie(
        portfolio_df,
        names="ticker",
        values="allocation_pct",
        title="Portfolio Allocation",
        hole=0.4
    )
    fig_alloc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig_alloc, use_container_width=True)

    st.info(portfolio_overview_insight(portfolio_df))

def display_risk_analysis_tab():
    """Display risk analysis in tab with modern styling."""
    results = st.session_state.analysis_results

    st.markdown("## Risk Analysis")
    st.markdown("Comprehensive analysis of your portfolio's risk profile")

    # Returns preview section
    st.markdown('<div class="section-header">Returns Analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Asset Returns (Preview)**")
        st.dataframe(results["asset_returns"].head(), use_container_width=True)

    with col2:
        st.markdown("**Portfolio Returns (Preview)**")
        st.dataframe(results["portfolio_returns"].head(), use_container_width=True)

    # Correlation analysis section
    st.markdown('<div class="section-header">Correlation Analysis</div>', unsafe_allow_html=True)
    st.markdown("How assets behave during normal vs. stress periods")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Normal Market Conditions**")
        st.dataframe(results["normal_corr"], use_container_width=True)

    with col2:
        st.markdown("**Stress Market Conditions**")
        st.dataframe(results["stress_corr"], use_container_width=True)

    # Correlation insights
    insight = correlation_insight(results["normal_corr"], results["stress_corr"])
    st.info(f"{insight}")

    # Stress loss attribution section
    st.markdown('<div class="section-header">Stress Loss Attribution</div>', unsafe_allow_html=True)
    st.markdown("Which assets contribute most to losses during market stress")

    st.dataframe(results["stress_contribution"].rename("Total Stress Contribution"), use_container_width=True)

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
    fig_stress.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=None,
        yaxis_title="Loss Contribution"
    )

    st.plotly_chart(fig_stress, use_container_width=True)

    # Stress insights
    stress_text = stress_loss_insight(results["stress_contribution"])
    st.info(f"{stress_text}")

def display_time_horizon_tab():
    """Display time horizon analysis in tab with modern styling."""
    results = st.session_state.analysis_results
    portfolio_returns = results["portfolio_returns"]

    st.markdown("## Time Horizon Risk Analysis")
    st.markdown("Understanding risk across different investment timeframes")

    available_days = len(portfolio_returns)
    filtered_horizons = {k: v for k, v in TIME_HORIZONS.items() if v < available_days}

    if not filtered_horizons:
        st.warning("Not enough historical data for time horizon analysis. Need at least 126 trading days.")
        return

    # Risk metrics table
    st.markdown('<div class="section-header">Risk Metrics by Time Horizon</div>', unsafe_allow_html=True)
    horizon_df = horizon_risk_summary(portfolio_returns, filtered_horizons)
    st.dataframe(horizon_df, use_container_width=True)

    # Create horizon risk chart
    st.markdown('<div class="section-header">Risk Visualization</div>', unsafe_allow_html=True)
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
        title="Risk Across Investment Horizons",
        color_discrete_map={
            "Worst Return": "#ff6b6b",
            "Probability of Loss": "#4ecdc4"
        }
    )
    fig_horizon.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title=None
    )

    st.plotly_chart(fig_horizon, use_container_width=True)

    # Insights
    st.markdown('<div class="section-header">Key Insights</div>', unsafe_allow_html=True)
    horizon_text = horizon_risk_insight(horizon_df)
    st.info(f"{horizon_text}")

    # Final summary
    st.markdown('<div class="section-header">Portfolio X-Ray Summary</div>', unsafe_allow_html=True)
    overview_text = portfolio_overview_insight(results["portfolio_df"])
    stress_text = stress_loss_insight(results["stress_contribution"])
    summary = final_xray_summary(overview_text, stress_text, horizon_text)
    st.success(f"{summary}")

# =============================================================================
# Main App
# =============================================================================
def main():
    # Initialize session state FIRST
    initialize_session_state()

    # Load external CSS
    load_css("style.css")

    # Sidebar for additional features
    with st.sidebar:
        st.markdown('<div class="header">Controls</div>', unsafe_allow_html=True)
        st.markdown("---")

        # Quick stats
        if "portfolio" in st.session_state and st.session_state.portfolio:
            portfolio_df = build_portfolio(st.session_state.portfolio)
            total_value = portfolio_df["amount"].sum()

            st.metric("Portfolio Value", f"INR {total_value:,.0f}")
            st.metric("Assets", len(portfolio_df))

        st.markdown("---")

        # Help section
        with st.expander("How to Use"):
            st.markdown("""
            <div class="sidebar-expander">
            <strong>Getting Started</strong>
            <ul>
                <li>Enter Ticker Symbols (e.g., RELIANCE.NS, TCS.NS, SPY)</li>
                <li>Specify Amounts in INR</li>
                <li>Choose Asset Type</li>
                <li>Click "Add Asset" to include in portfolio</li>
            </ul>

            <strong>Managing Your Portfolio</strong>
            <ul>
                <li>Edit amounts or remove assets using the table editor</li>
                <li>Click "Run Portfolio X-Ray Analysis" for risk assessment</li>
                <li>Explore results in the analysis tabs</li>
            </ul>

            <strong>Pro Tips</strong>
            <ul>
                <li>Use Yahoo Finance format for Indian stocks (add .NS suffix)</li>
                <li>Ensure you have a diverse mix of assets for better analysis</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

        with st.expander("Supported Assets & Tickers"):
            st.markdown("""
            <div class="sidebar-expander">
            <strong>Stock Examples</strong>
            <ul>
                <li><strong>Indian Stocks:</strong> RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS</li>
                <li><strong>US Stocks:</strong> AAPL, MSFT, GOOGL, AMZN, TSLA</li>
                <li><strong>International:</strong> 000001.SS (Shanghai), 0001.HK (Hong Kong)</li>
            </ul>

            <strong>ETF Examples</strong>
            <ul>
                <li><strong>Indian ETFs:</strong> ICICIB22.NS, KOTAKPSUBK.NS</li>
                <li><strong>US ETFs:</strong> SPY, QQQ, VTI, VOO, BND</li>
            </ul>

            <strong>Other Assets</strong>
            <ul>
                <li><strong>Indices:</strong> ^NSEI, ^GSPC, ^FTSE</li>
                <li><strong>Gold/Commodities:</strong> GC=F, SI=F</li>
                <li><strong>Bonds:</strong> AGG, BND, IBND</li>
            </ul>

            <strong>Finding Tickers</strong>
            <ul>
                <li>Search on Yahoo Finance or use the exact symbol from your broker</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

        # Footer
        st.markdown("---")
        st.markdown("Built with Streamlit")

    # Modern header
    st.markdown('<h1 class="main-header">Portfolio X-Ray</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 3rem;">Internal Risk Analytics for Portfolio Management</p>', unsafe_allow_html=True)

    # Welcome message for new users
    if not st.session_state.portfolio:
        st.markdown("""
        <div class="welcome-section">
        <div class="section-header" style="margin-top:0;">Welcome to Portfolio X-Ray</div>

        Get started by adding your first asset to the portfolio. This tool will help you:

        <ul>
            <li><strong>Understand your portfolio composition</strong></li>
            <li><strong>Analyze risk correlations during normal vs. stress periods</strong></li>
            <li><strong>Identify which assets contribute most to losses during downturns</strong></li>
            <li><strong>Assess risk across different investment time horizons</strong></li>
        </ul>

        <p><strong>Ready to begin?</strong> Add your first investment in the section below.</p>
        </div>
        """, unsafe_allow_html=True)

    # Create two main columns for better layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown('<div class="section-header">Portfolio Setup</div>', unsafe_allow_html=True)
        st.markdown("Add your investments and build your portfolio")
        add_portfolio_asset()

    with col2:
        st.markdown('<div class="section-header">Current Holdings</div>', unsafe_allow_html=True)
        display_portfolio_summary()

    # Display and edit portfolio in full width
    if st.session_state.portfolio:
        st.markdown("---")
        display_portfolio_editor()

        # Analysis section
        st.markdown("---")
        show_analysis_section()

def display_portfolio_summary():
    """Show a quick summary of the portfolio with modern cards."""
    if not st.session_state.portfolio:
        st.info("Add assets to your portfolio to get started")
        return

    portfolio_df = build_portfolio(st.session_state.portfolio)
    total_value = portfolio_df["amount"].sum()
    num_assets = len(portfolio_df)
    avg_allocation = portfolio_df["allocation_pct"].mean()

    # Modern metric cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Total Value</h4>
            <h2>INR {total_value:,.0f}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Assets</h4>
            <h2>{num_assets}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Avg Alloc</h4>
            <h2>{avg_allocation:.1f}%</h2>
        </div>
        """, unsafe_allow_html=True)

def display_portfolio_editor():
    """Display portfolio editor with modern styling and validation."""
    st.markdown('<div class="section-header">Edit Portfolio</div>', unsafe_allow_html=True)

    if not st.session_state.portfolio:
        st.info("No assets in portfolio yet. Add some assets above to get started!")
        return

    portfolio_df = pd.DataFrame(st.session_state.portfolio)

    # Show current portfolio summary
    total_value = portfolio_df["amount"].sum()
    st.info(f"**Current Portfolio:** {len(portfolio_df)} assets totaling INR {total_value:,.0f}")

    edited_df = st.data_editor(
        portfolio_df,
        num_rows="dynamic",
        width='stretch',
        key="portfolio_editor",
        column_config={
            "ticker": st.column_config.TextColumn(
                "Ticker",
                help="Stock/ETF symbol",
                required=True
            ),
            "amount": st.column_config.NumberColumn(
                "Amount (INR)",
                help="Investment amount in rupees",
                min_value=100.0,
                format="₹ %.0f",
                required=True
            ),
            "asset_type": st.column_config.SelectboxColumn(
                "Type",
                options=ASSET_TYPES,
                help="Asset category",
                required=True
            )
        }
    )

    # Clean and validate the edited DataFrame
    edited_df = clean_portfolio_data(edited_df)

    # Check for validation issues
    validation_issues = []

    # Check for missing tickers
    if not edited_df.empty:
        missing_tickers = edited_df["ticker"].isna() | (edited_df["ticker"].str.strip() == "")
        if missing_tickers.any():
            validation_issues.append("Some assets are missing ticker symbols")

        # Check for invalid amounts
        invalid_amounts = edited_df["amount"] <= 0
        if invalid_amounts.any():
            validation_issues.append("Some assets have invalid amounts (must be > 0)")

        # Check for duplicate tickers
        duplicate_tickers = edited_df["ticker"].str.upper().duplicated()
        if duplicate_tickers.any():
            validation_issues.append("Duplicate ticker symbols found")

    if validation_issues:
        for issue in validation_issues:
            st.error(issue)
        st.warning("Please fix the validation issues above before proceeding with analysis")
    else:
        # Update session state only if valid
        st.session_state.portfolio = edited_df.to_dict("records")

        # Store portfolio_df for use in tabs
        if st.session_state.portfolio:
            st.session_state.portfolio_df = build_portfolio(st.session_state.portfolio)
            
            # Clear old analysis results since portfolio changed
            if "analysis_results" in st.session_state:
                del st.session_state.analysis_results

            # Show updated summary
            new_total = edited_df["amount"].sum()
            if abs(new_total - total_value) > 0.01:  # Small threshold for floating point
                st.success(f"Portfolio updated! New total: INR {new_total:,.0f}")
                st.rerun() # Rerun to refresh the view immediately
        else:
             # If portfolio became empty (e.g. deleted last item)
             if "analysis_results" in st.session_state:
                del st.session_state.analysis_results
             st.rerun()

if __name__ == "__main__":
    main()
            