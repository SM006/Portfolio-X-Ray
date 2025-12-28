import numpy as np

def portfolio_overview_insight(portfolio_df):
    equity_types = ["Stock", "ETF", "Index"]
    equity_pct = portfolio_df.loc[
        portfolio_df["asset_type"].isin(equity_types),
        "allocation_pct"
    ].sum()

    if equity_pct > 70:
        return "This portfolio is equity-heavy, making it sensitive to market fluctuations."
    elif equity_pct > 40:
        return "This portfolio has a balanced mix of growth and defensive assets."
    else:
        return "This portfolio is defensively positioned with lower exposure to equities."



def correlation_insight(normal_corr, stress_corr):
    def avg_off_diag(corr):
        mask = ~np.eye(corr.shape[0], dtype=bool)
        return corr.values[mask].mean()

    normal_avg = avg_off_diag(normal_corr)
    stress_avg = avg_off_diag(stress_corr)

    if stress_avg > normal_avg + 0.15:
        return "Asset correlations increase during stress, reducing diversification when it is most needed."
    elif stress_avg < normal_avg - 0.1:
        return "Assets become less correlated during stress, improving diversification in difficult periods."
    else:
        return "Asset relationships remain relatively stable during stress periods."

def stress_loss_insight(stress_contribution):
    total_loss = stress_contribution.sum()
    top_asset = stress_contribution.idxmin()
    top_share = abs(stress_contribution.min() / total_loss) * 100

    if top_share > 60:
        return (
            f"Most stress losses are driven by {top_asset}, "
            "indicating concentration risk in this asset."
        )
    else:
        return (
            "Stress losses are distributed across assets, "
            "indicating limited concentration risk."
        )

def horizon_risk_insight(horizon_df):
    short_loss_prob = horizon_df.loc[
        horizon_df["Horizon"] == "6 Months",
        "Probability of Loss"
    ].values[0]

    long_loss_prob = horizon_df.loc[
        horizon_df["Horizon"] == "3 Years",
        "Probability of Loss"
    ].values[0]

    if long_loss_prob < short_loss_prob * 0.5:
        return (
            "The probability of loss decreases significantly over longer holding periods, "
            "highlighting the benefits of staying invested."
        )
    else:
        return (
            "Loss risk remains persistent even over longer holding periods, "
            "indicating structural portfolio risk."
        )

def final_xray_summary(
    portfolio_insight,
    stress_insight,
    horizon_insight
):
    return (
        f"{portfolio_insight} "
        f"{stress_insight} "
        f"{horizon_insight}"
    )
