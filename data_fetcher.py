import yfinance as yf
import pandas as pd

def fetch_nifty_50_stocks():
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
        "SBIN.NS", "ICICIBANK.NS", "KOTAKBANK.NS", "AXISBANK.NS", "LT.NS",
        "BAJFINANCE.NS", "ITC.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
        "TATASTEEL.NS", "NESTLEIND.NS", "POWERGRID.NS", "ONGC.NS", "WIPRO.NS",
        "JSWSTEEL.NS", "HCLTECH.NS", "GRASIM.NS", "BAJAJFINSV.NS", "INDUSINDBK.NS",
        "TECHM.NS", "ADANIPORTS.NS", "BPCL.NS", "HEROMOTOCO.NS", "SHREECEM.NS",
        "DRREDDY.NS", "ULTRACEMCO.NS", "TITAN.NS", "NTPC.NS", "BHARTIARTL.NS",
        "DIVISLAB.NS", "CIPLA.NS", "APOLLOHOSP.NS", "BRITANNIA.NS", "BAJAJ-AUTO.NS",
        "EICHERMOT.NS", "HDFCLIFE.NS", "ICICIGI.NS", "SBILIFE.NS", "PIDILITIND.NS",
        "M&M.NS", "COALINDIA.NS", "TATAPOWER.NS", "TVSMOTOR.NS", "ACC.NS"
    ]

def get_intraday_data(symbol):
    """
    Fetches 5-minute interval data for a given symbol.
    Returns clean OHLC DataFrame with flat column names.
    """
    df = yf.download(tickers=symbol, interval="5m", period="1d", auto_adjust=False)

    if df.empty:
        print(f"No data returned for {symbol}")
        return None

    # --- FLATTEN MULTIINDEX COLUMNS ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]

        # Rename to standard OHLC
        df.rename(columns={
            f'Open_{symbol}': 'Open',
            f'High_{symbol}': 'High',
            f'Low_{symbol}': 'Low',
            f'Close_{symbol}': 'Close',
            f'Volume_{symbol}': 'Volume'
        }, inplace=True)

    # --- Ensure proper OHLC structure ---
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required_columns):
        print(f"Missing required OHLC columns for {symbol}")
        return None

    df = df[required_columns]

    # Convert to numeric
    for col in required_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df.dropna(inplace=True)

    return df