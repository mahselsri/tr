import pandas as pd
import numpy as np

def calculate_score(df):
    """
    Calculates swing score based on:
    - RSI (Relative Strength Index)
    - Volume Spike
    - MACD Crossover
    - Price above 20 SMA
    - Bollinger Band Position

    Returns:
        score (int): Final swing score (0–100)
        df (pd.DataFrame): Original df with added indicators
    """

    if len(df) < 30:
        print("Not enough data to calculate indicators.")
        return 0, df

    try:
        # --- Simple Moving Averages ---
        df['SMA20'] = df['Close'].rolling(window=20).mean()
        df['SMA50'] = df['Close'].rolling(window=50).mean()

        # --- Distance from SMA20 (for trend strength) ---
        df['DistanceFromSMA20'] = (df['Close'] - df['SMA20']) / df['SMA20']

        # --- RSI Calculation ---
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))

        # --- MACD Calculation ---
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

        # --- Volume Analysis ---
        df['AvgVolume'] = df['Volume'].rolling(window=10).mean()
        df['VolumeRatio'] = df['Volume'] / df['AvgVolume']

        # --- Bollinger Bands ---
        df['BB_Middle'] = df['Close'].rolling(20).mean()
        bb_std = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)

        # --- Latest Values for Scoring ---
        rsi = df['RSI'].iloc[-1]
        volume_ratio = df['VolumeRatio'].iloc[-1]
        price_above_sma20 = df['Close'].iloc[-1] > df['SMA20'].iloc[-1]
        price_in_bb_range = df['Close'].iloc[-1] > df['BB_Lower'].iloc[-1] and df['Close'].iloc[-1] < df['BB_Upper'].iloc[-1]
        sma20_above_sma50 = df['SMA20'].iloc[-1] > df['SMA50'].iloc[-1]

        # --- Score Logic ---
        score = 0

        if not pd.isna(rsi):
            if rsi < 40:
                score += 20  # Oversold
            elif rsi > 60:
                score += 10  # Overbought may indicate strength

        if not pd.isna(volume_ratio) and volume_ratio > 2:
            score += 20

        if not pd.isna(df['MACD'].iloc[-1]) and not pd.isna(df['Signal'].iloc[-1]):
            if df['MACD'].iloc[-1] > df['Signal'].iloc[-1]:
                score += 15

        if price_above_sma20:
            score += 10

        if price_in_bb_range:
            score += 10

        if sma20_above_sma50:
            score += 15

        return min(score, 100), df  # <-- Now returning modified df

    except Exception as e:
        print(f"Error calculating score: {e}")
        return 0, df