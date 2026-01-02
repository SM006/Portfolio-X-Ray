# Portfolio X-Ray: Stress-Aware Investment Risk Analytics

## 1. Project Overview
"Portfolio X-Ray" is a quantitative analytics tool designed to evaluate the true risk profile of an investment portfolio using historical market data.

Traditional portfolio trackers often rely on simple metrics like average annual returns or sector diversification diagrams. These metrics fail to capture **tail risk**—the behavior of assets during market crashes—and often underestimate the danger of correlation breakdowns during stress periods.

This project ingests a real-world portfolio (based on invested amounts, not just percentages) and subjects it to rigorous historical stress testing. It reconstructs the portfolio's historical performance, analyzes its behavior during the worst market days, and provides an honest assessment of downside risk across different time horizons.

## 2. Key Objectives
The primary goals of this analytics system are:
*   **Reveal Hidden Downside Risk**: Go beyond standard deviation to measure "Stress Beta" and performance during tail events.
*   **Analyze Correlation Breakdown**: Identify assets that normally appear uncorrelated but move together (couple) during market crashes.
*   **Quantify Time-Horizon Risk**: Calculate the probability of loss for various holding periods (e.g., 1 year vs. 5 years) to discourage short-termism.
*   **Attribute Stress Losses**: Pinpoint exactly which assets contribute the most to portfolio drag during downturns.
*   **Provide Transparent Analytics**: Focus on explainable, arithmetic-based insights rather than black-box machine learning predictions.

## 3. Data Sources
*   **Market Data**: Historical pricing data is fetched via the **Yahoo Finance API**.
*   **Price Type**: We utilize **Adjusted Close** prices to account for dividends and stock splits, ensuring an accurate reflection of total return.
*   **Inception Handling**: The system dynamically handles assets with different inception dates. The portfolio history is truncated to the start date of the youngest asset to ensure a valid, common timeframe for correlation and covariance calculations.

## 4. Methodology
The core of this project relies on rigorous mathematical definitions of risk and return.

### Asset Returns
We calculate daily simple returns for each asset. Log returns are not used to preserve the linear additivity required for portfolio weights.

$$
R_{i,t} = \frac{P_{i,t} - P_{i,t-1}}{P_{i,t-1}}
$$

Where $R_{i,t}$ is the return of asset $i$ at time $t$, and $P$ is the Adjusted Close price.

### Portfolio Weights
Weights are derived from the current invested amounts provided by the user.

$$
w_i = \frac{A_i}{\sum_{j=1}^{N} A_j}
$$

Where $w_i$ is the weight of asset $i$, and $A_i$ is the dollar amount invested.

### Portfolio Returns
The daily return of the total portfolio is the weighted sum of individual asset returns.

$$
R_{p,t} = \sum_{i=1}^{N} w_i \cdot R_{i,t}
$$

This assumes daily rebalancing to fixed weights for the purpose of historical analysis, a standard approximation in risk modeling.

### Correlation (Pearson)
Measures the linear relationship between two assets.

$$
\rho_{i,j} = \frac{\text{Cov}(R_i, R_j)}{\sigma_i \cdot \sigma_j}
$$

Where $\text{Cov}$ is covariance and $\sigma$ is standard deviation. High correlation implies assets move together.

### Stress Scenario Definition
We define "Stress Days" as the trading days falling in the bottom $q$-th percentile (e.g., bottom 5%) of the portfolio's historical return distribution.

$$
t \in S \iff R_{p,t} \le Q_q(R_p)
$$

Where $S$ is the set of stress days and $Q_q$ is the quantile function.

### Stress Correlation
This is the Pearson correlation coefficient $\rho_{i,j}$ computed **only** using data points $t \in S$.
Why: Assets often become more correlated during crashes (contagion), negating diversification benefits. Comparing Normal vs. Stress correlation reveals this risk.

### Stress Loss Attribution
Calculates how much each asset contributed to the total portfolio decline during stress periods.

$$
C_{i,t} = w_i \cdot R_{i,t}
$$

$$
\text{StressLoss}_i = \sum_{t \in S} C_{i,t}
$$

This identifies the specific drivers of drawdown, regardless of the asset's volatility.

### Rolling Holding-Period Returns
We simulate purchasing the portfolio on every possible day in history and holding it for $H$ days.

$$
R_{p,t}(H) = \left( \prod_{k=0}^{H-1} (1 + R_{p,t-k}) \right) - 1
$$

This generates a distribution of realized returns for a specific investment horizon.

### Probability of Loss
The likelihood of losing money if the portfolio is held for $H$ days, based on historical frequency.

$$
P(\text{loss}) = \frac{\text{count}(R(H) < 0)}{\text{total observations}}
$$

Showcases how risk diminishes as the investment horizon lengthens.

### Worst-Case Return
The absolute minimum return observed for a given holding period $H$.

$$
\text{Worst}(H) = \min(R(H))
$$

Represents the "historical maximum drawdown" for a fixed time window.

## 5. Visualizations
The application utilizes **Plotly** for interactive, financial-grade charts:

1.  **Portfolio Allocation (Donut Chart)**:
    *   Visualizes the current weight distribution $w_i$ of the portfolio.
2.  **Correlation Heatmaps (Comparison)**:
    *   Displays two side-by-side matrices: one for full-history correlation and one for **Stress Correlation**.
    *   Highlights "breakdowns" where separate assets suddenly lockstep during crashes.
3.  **Stress Loss Attribution (Bar Chart)**:
    *   Quantifies exactly how much money each asset theoretically cost the portfolio during defined stress events.
    *   Distinguishes between "safe havens" (positive bars) and "drag" contributors (negative bars).
4.  **Time-Horizon Risk Analysis (Multi-Line Chart)**:
    *   Plots "Probability of Loss" and "Worst Case Return" against holding periods (1 month to 10 years).
    *   Graphically demonstrates the "time diversification" effect.

## 6. Key Insights Generated
*   **Diversification Quality**: Is the portfolio actually diverse, or just a collection of different tickers that move identically?
*   **Concentration Risk**: Does a single asset dominate the downside risk, even if its weight implies otherwise?
*   **Time-Dependent Risk**: How long must an investor hold this specific mix of assets to statistically minimize the chance of a negative return?
*   **Regime Sensitivity**: How does the portfolio behave specifically during market shocks (Left-Tail events)?

## 7. Tech Stack
*   **Language**: Python 3.10+
*   **Data Processing**: Pandas, NumPy
*   **Visualization**: Plotly Graph Objects
*   **Data Sourcing**: Yahoo Finance (`yfinance`)
*   **Web Framework**: Streamlit

## 8. Project Scope & Limitations
To ensure clarity on valid use-cases:
*   **No Prediction**: This tool does **not** forecast future prices. It assumes historical distributions are a useful (though imperfect) proxy for future risk.
*   **No Machine Learning**: There are no "AI" black boxes. All metrics are transparent, arithmetic derivations from realized price history.
*   **No Optimization**: It does not suggest "better" weights (e.g., Efficient Frontier). It analyzes the portfolio *as provided*.
*   **Currency Risk**: The current version assumes all assets are denominated in USD or does not account for FX volatility.

## 9. How to Run the Project

### Prerequisites
*   Python 3.8 or higher installed.

### Installation
1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/portfolio-xray.git
    cd portfolio-xray
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    streamlit run app.py
    ```

4.  Input your portfolio tickers and amounts in the sidebar to generate the analysis.

## 10. Conclusion
Portfolio X-Ray bridges the gap between basic trackers and institutional-grade risk management systems. By rigorously analyzing historical stress behavior and correlation dynamics, it empowers self-directed investors to understand *what in their portfolio actually hurts them* during a crash. It champions interpretability and financial robustness over speculative prediction.
