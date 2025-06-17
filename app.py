import streamlit as st
import pandas as pd
from data_fetcher import fetch_nifty_50_stocks
from strategy_engine import analyze_stock

st.set_page_config(layout="wide")
st.title("📈 Nifty 50 Options Strategy Dashboard")

if st.button("Fetch Live Picks"):
    symbols = fetch_nifty_50_stocks()
    results = []

    with st.spinner("Analyzing stocks..."):
        for symbol in symbols:
            result = analyze_stock(symbol)
            if result:
                results.append(result)

    if not results:
        st.warning("No signals found.")
    else:
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values(by='Volume Spike', ascending=False).head(10)

        st.subheader("🔥 Top 10 High Volume Stocks")
        st.dataframe(df_results.style.applymap(
            lambda x: 'background-color: lightgreen' if x == True else ('background-color: red' if x == False else '')
        ))

        st.download_button(
            label="📥 Download Signals",
            data=df_results.to_csv(index=False),
            file_name="nifty_options_signals.csv",
            mime="text/csv"
        )