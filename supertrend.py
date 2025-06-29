import numpy as np
np.NaN = np.nan  # Monkey patch NaN for compatibility with pandas_ta
import pandas as pd
import pandas_ta as ta

def calculate_supertrend(df, base_period=10, multiplier=2):
    df = df.copy()

    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[required_columns].apply(pd.to_numeric, errors='coerce').dropna()
    if df.empty:
        df['InUptrend'] = np.nan
        return df

    num_candles = len(df)

    if num_candles < 3:
        df['InUptrend'] = np.nan
        return df

    adjusted_period = min(base_period, max(3, int(num_candles / 2)))

    try:
        df.ta.supertrend(period=adjusted_period, multiplier=multiplier, append=True)
    except Exception as e:
        print(f"⚠️ Supertrend failed: {e}")
        df['InUptrend'] = np.nan
        return df

    supertrend_col = [col for col in df.columns if 'SUPERT_' in col]
    if not supertrend_col:
        df['InUptrend'] = np.nan
        return df

    df['Supertrend'] = df[supertrend_col[0]]
    df['InUptrend'] = df['Close'] > df['Supertrend']

    return df
    
def calculate_supertrend1(df, period=10, multiplier=2):
    """
    Calculates Supertrend and trend direction.
    
    Args:
        df (pd.DataFrame): DataFrame with 'Open', 'High', 'Low', 'Close', 'Volume'
        period (int): ATR Period
        multiplier (float): ATR Multiplier

    Returns:
        pd.DataFrame: Original df with Supertrend and InUptrend signal
    """
    # Avoid modifying original df
    df = df.copy()

    # --- Step 1: Ensure valid index ---
    if isinstance(df.index, pd.MultiIndex):
        df.reset_index(level=0, drop=True, inplace=True)

    try:
        df.index = pd.to_datetime(df.index)
    except Exception:
        df.reset_index(inplace=True)
        df['datetime'] = pd.to_datetime(df.iloc[:, 0])
        df.set_index('datetime', inplace=True)

    # --- Step 2: Select only required columns and clean them ---
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[required_columns]

    # Coerce all to numeric
    for col in required_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with missing OHLC
    df.dropna(subset=['Open', 'High', 'Low', 'Close'], inplace=True)

    # --- Step 3: Ensure enough data for calculation ---
    if len(df) < 20:
        print("🚫 Not enough data to calculate indicators.")
        df['Supertrend'] = np.nan
        df['InUptrend'] = np.nan
        return df

    # --- Step 4: Calculate Supertrend safely ---
    try:
        df.ta.supertrend(period=period, multiplier=multiplier, append=True)
    except Exception as e:
        print(f"⚠️ Supertrend calculation failed: {e}")
        df['Supertrend'] = np.nan
        df['InUptrend'] = np.nan
        return df

    # --- Step 5: Try to find the correct Supertrend column ---
    supertrend_col = f"SUPERT_{period}_{multiplier}"

    # If exact match not found, look for any column with SUPERT in name
    if supertrend_col not in df.columns:
        possible_cols = [col for col in df.columns if 'SUPERT' in str(col)]
        if possible_cols:
            supertrend_col = possible_cols[0]
            print(f"✅ Using alternative column: {supertrend_col}")
        else:
            print(f"❌ No Supertrend column found in output")
            df['Supertrend'] = np.nan
            df['InUptrend'] = np.nan
            return df

    # --- Step 6: Add readable signals ---
    df['Supertrend'] = df[supertrend_col]
    df['InUptrend'] = df['Close'] > df['Supertrend']

    return df