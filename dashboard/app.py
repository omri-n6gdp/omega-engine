"""Streamlit dashboard for the Omega Engine."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager
from config import DB_PATH

st.set_page_config(page_title="Omega Strategy Engine", layout="wide")

db = DatabaseManager(DB_PATH)

st.title("🔥 Omega Strategy Engine")
st.caption("Research-grade backtesting platform. Educational use only.")

# Sidebar filters
st.sidebar.header("Filters")
is_oos = st.sidebar.checkbox("Out-of-Sample Only", value=True)
min_sharpe = st.sidebar.slider("Min Sharpe", -2.0, 3.0, 0.0, 0.1)
timeframe = st.sidebar.selectbox("Timeframe", ["All", "1d", "1wk", "1mo"])
ticker = st.sidebar.text_input("Ticker (blank for all)", "")

page = st.sidebar.radio("Page", ["🏆 Leaderboard", "🔬 Strategy Autopsy", "⚠️ Overfitting Report", "📊 Data Health"])

tf_filter = None if timeframe == "All" else timeframe
ticker_filter = ticker.upper() if ticker else None

if page == "🏆 Leaderboard":
    st.header("Strategy Leaderboard")
    results = db.get_results(
        is_oos=is_oos,
        min_sharpe=min_sharpe,
        ticker=ticker_filter,
        timeframe=tf_filter,
        limit=200
    )
    if results.empty:
        st.warning("No results found. Run backtests first: `python main.py backtest`")
    else:
        results["params_short"] = results["params"].str[:60]
        display = results[["strategy_name", "ticker", "timeframe", "params_short", 
                           "sharpe_ratio", "total_return", "max_drawdown", "num_trades", "calmar_ratio"]]
        st.dataframe(display, use_container_width=True)

        st.subheader("Sharpe Distribution")
        fig = go.Figure(data=[go.Histogram(x=results["sharpe_ratio"], nbinsx=50)])
        fig.add_vline(x=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)

elif page == "🔬 Strategy Autopsy":
    st.header("Strategy Deep Dive")
    results = db.get_results(is_oos=is_oos, ticker=ticker_filter, timeframe=tf_filter, limit=500)
    if results.empty:
        st.warning("No results.")
    else:
        # Select strategy
        options = [f"{r.strategy_name} | {r.ticker} | {r.timeframe} | Sharpe={r.sharpe_ratio:.2f}" 
                   for _, r in results.iterrows()]
        selected = st.selectbox("Select Strategy", options)
        if selected:
            idx = options.index(selected)
            row = results.iloc[idx]

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Sharpe", f"{row.sharpe_ratio:.2f}")
            col2.metric("Return", f"{row.total_return:.1%}")
            col3.metric("Max DD", f"{row.max_drawdown:.1%}")
            col4.metric("Trades", f"{row.num_trades}")

            st.json(row.params)

            # Equity curve
            try:
                equity = pd.read_json(row.equity_curve, typ="series")
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=equity.index, y=equity.values, mode="lines", name="Equity"))
                fig.update_layout(title="Equity Curve", height=400)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.info("Equity curve not available.")

elif page == "⚠️ Overfitting Report":
    st.header("In-Sample vs Out-of-Sample")
    is_results = db.get_results(is_oos=False, ticker=ticker_filter, timeframe=tf_filter, limit=500)
    oos_results = db.get_results(is_oos=True, ticker=ticker_filter, timeframe=tf_filter, limit=500)

    if is_results.empty or oos_results.empty:
        st.warning("Need both IS and OOS results. Run with walk-forward enabled.")
    else:
        merged = pd.merge(
            is_results[["strategy_name", "ticker", "timeframe", "params", "sharpe_ratio"]].rename(columns={"sharpe_ratio": "is_sharpe"}),
            oos_results[["strategy_name", "ticker", "timeframe", "params", "sharpe_ratio"]].rename(columns={"sharpe_ratio": "oos_sharpe"}),
            on=["strategy_name", "ticker", "timeframe", "params"],
            how="inner"
        )
        fig = go.Figure(data=[
            go.Scatter(x=merged["is_sharpe"], y=merged["oos_sharpe"], mode="markers", 
                       marker=dict(size=8, opacity=0.6))
        ])
        fig.add_shape(type="line", x0=-2, y0=-2, x1=3, y1=3, line=dict(dash="dash", color="red"))
        fig.update_layout(xaxis_title="In-Sample Sharpe", yaxis_title="OOS Sharpe", height=600)
        st.plotly_chart(fig, use_container_width=True)

        survivors = merged[(merged["is_sharpe"] > 0.5) & (merged["oos_sharpe"] > 0.5)]
        st.write(f"**Survivors** (IS > 0.5 AND OOS > 0.5): {len(survivors)} / {len(merged)}")
        st.dataframe(survivors, use_container_width=True)

elif page == "📊 Data Health":
    st.header("Data Health")
    status = db.get_data_status()
    if status.empty:
        st.warning("No data cached. Run `python main.py fetch`")
    else:
        st.dataframe(status, use_container_width=True)
        st.bar_chart(status.set_index("ticker")["bars_count"])
