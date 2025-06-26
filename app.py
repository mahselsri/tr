import streamlit as st
import pandas as pd
from data_fetcher import fetch_nifty_50_stocks
from strategy_engine import analyze_stock
from getaccesstoken import get_kite, save_access_token
import os
from kiteconnect import KiteConnect
st.set_page_config(layout="wide")
st.title("📈 Live Nifty 50 (Top 10) Volume & Trend Screener")
# Initialize kite object
kite = get_kite()

if kite is None:
    st.warning("🔑 Zerodha API Not Authenticated")
    
    request_token = st.text_input("Enter request_token from URL after login:")
    if st.button("Generate Session"):
        if request_token.strip():
            kite = KiteConnect(api_key="f1t0xfioknkg0v64")
            try:
                session_data = kite.generate_session(request_token, api_secret="2y0071w25pm3mj49pxvzqdtnk3g4ocvg")
                access_token = session_data["access_token"]
                save_access_token(access_token)
                kite.set_access_token(access_token)
                st.session_state['kite'] = kite
                st.success("✅ Session generated! Refreshing...")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to generate session: {e}")
else:
    if st.button("Fetch Live Picks"):
        symbols = fetch_nifty_50_stocks()
        results = []

        with st.spinner("Scanning stocks..."):
            for symbol in symbols:
                result = analyze_stock(kite, symbol)
                if result:
                    results.append(result)

        if results:
            df_results = pd.DataFrame(results)
            df_results = df_results.sort_values(by='Volume Spike', ascending=False).head(10)
            df_results['Signal'] = df_results.apply(
                lambda row: "🟢 Buy Call (1 ITM)" if row['InUptrend'] else "🔴 Buy Put (1 ITM)",
                axis=1
            )
            st.dataframe(df_results)
        else:
            st.warning("No valid signals found.")