import streamlit as st
import pandas as pd
from data_fetcher import fetch_nifty_20_stocks
from strategy_engine import analyze_stock
from getaccesstoken import get_kite, save_access_token
import os
from kiteconnect import KiteConnect
from zerodha_api import TIMEFRAME_MAP
st.set_page_config(layout="wide")
st.title("📈 Live Nifty 50 (Top 10) Volume & Trend Screener")
# Initialize kite object


def get_color_for_spike(val):
    """
    Returns background color based on volume spike percentage
    e.g., 'background-color: lightgreen' or 'background-color: darkgreen'
    """
    if not isinstance(val, str) or "%" not in val:
        return ''

    try:
        spike = float(val.strip("%"))
    except:
        return ''

    if spike > 100:
        return 'background-color: darkgreen; color: white;'
    elif spike > 70:
        return 'background-color: forestgreen; color: white;'
    elif spike > 50:
        return 'background-color: mediumseagreen;'
    elif spike > 30:
        return 'background-color: lightgreen;'
    elif spike > 0:
        return 'background-color: lightyellow;'
    elif spike < 0:
        return 'background-color: lightcoral;'
    else:
        return ''
  
kite = get_kite()
def get_quick_ltp(kite, symbol):
    """Quick volume/price check before full scan"""
    try:
        quote = kite.ltp(f"NSE:{symbol}")
        if not quote:
            return None

        q = quote.get(f"NSE:{symbol}", {})
        return {
            'symbol': symbol,
            'volume': q.get('volume', 0),
            'price': q.get('last_price', None)
        }
    except Exception as e:
        print(f"Error getting LTP for {symbol}: {e}")
        return None

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
        symbols = fetch_nifty_20_stocks()
        results = []
        #ftech top volume symbol first

        
        with st.spinner("Scanning stocks..."):
            

            #st.success(f"📈 Proceeding with {len(ltp_results)} high-volume stocks...")
            for symbol in symbols:
                result = analyze_stock(kite, symbol)
                if result:
                    results.append(result)

        if results:
            print(results)
            df_results = pd.DataFrame(results)
            #df_results = df_results.sort_values(by='Volume Spike', ascending=False).head(10)
            #df_results['Signal'] = df_results.apply(
            #    lambda row: "🟢 Buy Call (1 ITM)" if row['InUptrend'] else "🔴 Buy Put (1 ITM)",
            #    axis=1
            #)
            #st.dataframe(df_results)
            # --- Style Volume Spike Columns ---
            vol_spike_cols = [f"{tf}_VolSpike" for tf in TIMEFRAME_MAP.keys()]

            df_results.sort_values(by=vol_spike_cols, ascending=True).head(20)
            styled_df = df_results.style.applymap(get_color_for_spike, subset=vol_spike_cols)
            
            st.subheader("📊 Multi-Timeframe View – Price + Volume Spike")
            st.dataframe(styled_df)
        else:
            st.warning("No valid signals found.")