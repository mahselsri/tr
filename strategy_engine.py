import pandas as pd
import numpy as np
from supertrend import calculate_supertrend
from zerodha_api import get_intraday_data




def analyze_stock1(kite, symbol):
    """
    Analyzes early volume spike between 9:16 AM and 9:21 AM
    Uses live quotes instead of full historical data
    """
    try:
        # Get live quote
        instrument_token = get_instrument_token(kite, symbol)
        if not instrument_token:
            print(f"⚠️ Instrument token not found for {symbol}")
            return None

        quote = kite.quote(instrument_token)
        if not quote:
            return None

        # Extract relevant quote data
        last_price = quote[str(instrument_token)]['last_price']
        volume = quote[str(instrument_token)]['volume']

        # Fallback to daily OHLC if available
        ohlc = quote[str(instrument_token)].get('ohlc', {})
        open_price = ohlc.get('open', None)

        if open_price is None:
            print(f"🚫 No open price for {symbol}")
            return None

        # Simple volume check
        if volume and volume > 1000:  # Set a baseline (you can adjust dynamically)
            change_percent = ((last_price - open_price) / open_price) * 100
            signal = "Buy Call (1 ITM)" if change_percent > 0.1 else "Buy Put (1 ITM)"
            
            return {
                'Symbol': symbol,
                'Signal': signal,
                'Price': round(last_price, 2),
                'Volume': volume,
                'Open Price': round(open_price, 2),
                'Change (%)': round(change_percent, 2)
            }
        else:
            return None

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

def analyze_stock(kite,symbol):
    """
    Analyze a single stock for volume spike and trend.
    Returns dict of key metrics or None if error.
    """
    # Fetch live data
    df = get_intraday_data(kite,symbol)
    
    
    if df is None or len(df) < 2:
        return None
    print(df.tail())
    try:
        # Clean OHLC data
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df = df.apply(pd.to_numeric, errors='coerce').dropna()

        # Calculate Supertrend
        df = calculate_supertrend(df)

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # --- Trend Signal ---
        current_trend = latest['InUptrend']
        previous_trend = prev['InUptrend']

        signal = "Hold / No Signal"
        if signal == "Hold / No Signal":
            if len(df) >= 2:
                prev_price = df['Close'].iloc[-2]
                curr_price = df['Close'].iloc[-1]
                change_percent = round((curr_price - prev_price) / prev_price * 100, 2)

                if change_percent > 0.3:
                    signal = "Buy Call (1 ITM) [Fallback]"
                elif change_percent < -0.3:
                    signal = "Buy Put (1 ITM) [Fallback]"
        
        
        # --- Volume Spike (vs Avg of last 5 candles) ---
        avg_volume = df['Volume'].tail(5).mean()
        latest_volume = latest['Volume']

        if avg_volume > 0:
            volume_spike = round(latest_volume / avg_volume, 2)
        else:
            volume_spike = 0

        return {
            'Symbol': symbol,
            'Signal': signal,
            'Price': round(latest['Close'], 2),
            'Volume': latest_volume,
            'Avg Volume (5)': round(avg_volume, 2),
            'Volume Spike': volume_spike,
            'InUptrend': current_trend,
            'Timestamp': df.index[-1].strftime("%Y-%m-%d %H:%M:%S (IST)")
        }

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None