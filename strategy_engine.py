import pandas as pd
import numpy as np
from supertrend import calculate_supertrend
from zerodha_api import get_intraday_data
from zerodha_api import TIMEFRAME_MAP
def analyze_stock(kite,symbol):
    """
    Analyze a single stock for volume spike and trend.
    Returns dict of key metrics or None if error.
    """
    # Fetch live data
    df,timeframe_data = get_intraday_data(kite,symbol)
    # Only proceed if we have at least 5M data
    if timeframe_data["5M"]['price'] == '-' or timeframe_data["5M"]['volume'] == '-':
        return None

    # --- Optional: Generate Signal Based on Trend Consistency ---
    strong_up = all(tf['vol_spike'] != "-" and float(tf['vol_spike'].strip("%")) > 50 for tf in timeframe_data.values())
    signal = "✅ Strong Buy" if strong_up else "⚠️ Mixed"

    # --- Build final dict for DataFrame ---
    result = {
        'Symbol': symbol,
        'Signal': signal
    }

    # Add each timeframe's data as separate columns
    for tf in TIMEFRAME_MAP.keys():
        result[f"{tf}_Price"] = timeframe_data[tf]['price']
        result[f"{tf}_Volume"] = timeframe_data[tf]['volume']
        result[f"{tf}_VolSpike"] = timeframe_data[tf]['vol_spike']

    return result

    