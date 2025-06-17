from data_fetcher import get_intraday_data
from supertrend import calculate_supertrend
import pandas as pd
def analyze_stock(symbol):
    df = get_intraday_data(symbol)
    if df is None or len(df) < 30:
        return None

    try:
        # Clean DataFrame before processing
        print(f"\nProcessing {symbol} | Index Type: {type(df.index)}")
        print("Columns:", df.columns.tolist())
        print("Sample Data:\n", df.tail(2))
        print("Data Types:\n", df.dtypes)

        df = calculate_supertrend(df)

        if df.empty:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # --- Generate Signal ---
        signal = None

        # Extract trend values
        prev_trend = prev['InUptrend']
        curr_trend = latest['InUptrend']

        # Safely handle NaNs and ensure boolean logic
        if pd.notna(prev_trend) and pd.notna(curr_trend):
            prev_trend = bool(prev_trend)
            curr_trend = bool(curr_trend)

            if not prev_trend and curr_trend:
                signal = "Buy Call (1 ITM)"
            elif prev_trend and not curr_trend:
                signal = "Buy Put (1 ITM)"
            else:
                signal = "Hold / No Signal"
        else:
            signal = "Hold / No Signal (Invalid Trend Data)"

        volume = latest['Volume']
        avg_volume = df['Volume'].rolling(window=10).mean().iloc[-1]
        volume_spike = round(volume / avg_volume, 2)

        return {
            'Symbol': symbol,
            'Signal': signal,
            'Volume Spike': volume_spike,
            'Current Price': round(latest['Close'], 2),
            'InUptrend': latest['InUptrend'],
            'Timestamp': str(df.index[-1])
        }
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None