from kiteconnect import KiteConnect
import pandas as pd
import os
import time
# --- Step 1: Paste Your API Key & Secret Here ---

SESSION_FILE = "zerodha_session.txt"


TIMEFRAME_MAP1 = {
    "5M": "5minute",
    "10M": "10minute",
    "15M": "15minute",
    "30M": "30minute",
    "60M": "60minute"
}
TIMEFRAME_MAP = {
    "5M": "5minute",
    "10M": "10minute",
    "15M": "15minute"
    
}
def analyze_timeframe(kite, symbol):
    """
    Returns price + volume info for all timeframes
    """
    timeframe_data = {}
    # Fetch instruments once
    instruments_eq = kite.instruments("NSE")
    instruments_fo = kite.instruments("NSE_FO")
    for tf_key, tf_val in TIMEFRAME_MAP.items():
        df = get_ohlc_data(kite, symbol,instruments_eq, instruments_fo, interval=tf_val, days_back=1)

        if df is None or len(df) < 2:
            timeframe_data[tf_key] = {'price': '-', 'volume': '-', 'vol_spike': '-'}
            continue

        latest = df.iloc[-1]
        prev_volumes = df['Volume'].tail(5).mean()
        vol_spike = round((latest['Volume'] / prev_volumes - 1) * 100, 2) if prev_volumes > 0 else 0

        timeframe_data[tf_key] = {
            'price': round(latest['Close'], 2),
            'volume': latest['Volume'],
            'vol_spike': f"{vol_spike}%"
        }
        #delay between calls
        #time.sleep(1.5) 
    return timeframe_data

def get_intraday_data(kite, symbol):
    # Get trend across timeframes
    timeframe_trends = analyze_timeframe(kite, symbol)

    # Use 5M as primary
    primary_tf = "5M"
    primary_trend = timeframe_trends.get(primary_tf)

    if primary_trend is None:
        return None

    # Generate main signal based on 5M
    signal = None
    if timeframe_trends["5M"] and not timeframe_trends["15M"]:
        signal = "🟢 Buy Call (Mixed)"
    elif timeframe_trends["5M"] and timeframe_trends["10M"] and timeframe_trends["15M"]:
        signal = "✅ Buy Call (Strong)"
    elif not timeframe_trends["5M"]:
        signal = "🛑 Sell Put (Weak)"
    else:
        signal = "⚠️ Mixed Signal"

    return {
        'Symbol': symbol,
        'Signal': signal,
        '5M': timeframe_trends.get("5M"),
        '10M': timeframe_trends.get("10M"),
        '15M': timeframe_trends.get("15M")
    }, timeframe_trends

def get_live_quote_data(kite, symbol):
    """
    Fetches live price and volume using LTP endpoint (minimal permissions needed)
    """

    try:
        #instrument_token = get_instrument_token(kite, symbol)
        exchange = "NSE"
        instrument_token = f"{exchange}:{symbol}"
        if not instrument_token:
            print(f"🚫 Token not found for {symbol}")
            return None
        print(f"One loop{instrument_token}")
        # Get LTP (Last Traded Price) instead of full quote
        ltp_data = kite.ltp(instrument_token)
        print("two loop")
        if not ltp_data or str(instrument_token) not in ltp_data:
            print(f"🚫 LTP data not available for {symbol}")
            return None
        print("after ltp data")
        ltp = ltp_data[str(instrument_token)]
        print(f"backedn after ltp data{ltp}")
        last_price = ltp.get('last_price', None)
        volume = ltp.get('volume', 0)
        timestamp = ltp.get('timestamp', pd.Timestamp.now())

        # We can’t get OHLC/open price from LTP directly
        # So we fallback to "last_price" as both open and current price
        open_price = last_price  # Not perfect but works in early session

        if not last_price:
            return None

        change_percent = 0.0
        if open_price and open_price > 0:
            change_percent = round(((last_price - open_price) / open_price * 100), 2)

        return {
            'symbol': symbol,
            'last_price': last_price,
            'open_price': open_price,
            'change_percent': change_percent,
            'volume': volume,
            'timestamp': timestamp
        }

    except Exception as e:
        print(f"❌ not found fetching live quote for {symbol}: {e}")
        return None
def get_live_quote_data33(kite, symbol):
    """
    Fetches live quote data for a given stock using Zerodha API.
    Returns price, volume, OHLC (open), and timestamp if available.
    """

    try:
        # Get instrument token
        instrument_token = get_instrument_token(kite, symbol)
        if not instrument_token:
            print(f"⚠️ Instrument token not found for {symbol}")
            return None

        # Get live quote
        quote = kite.quote(instrument_token)
        if not quote or str(instrument_token) not in quote:
            print(f"❌ No quote data for {symbol}")
            return None

        quote_data = quote[str(instrument_token)]

        # Extract key values
        last_price = quote_data.get('last_price', None)
        volume = quote_data.get('volume', 0)
        ohlc = quote_data.get('ohlc', {})
        timestamp = quote_data.get('timestamp', pd.Timestamp.now())

        if 'open' not in ohlc:
            print(f"🚫 No OHLC data available for {symbol}")
            return None

        open_price = ohlc['open']

        return {
            'symbol': symbol,
            'last_price': last_price,
            'open_price': open_price,
            'volume': volume,
            'change_percent': round(((last_price - open_price) / open_price * 100, 2)),
            'timestamp': timestamp
        }

    except Exception as e:
        print(f"❌ Error fetching live data for {symbol}: {e}")
        return None
        
def get_ohlc_data(kite, symbol,instruments_eq, instruments_fo, interval, days_back=1):
    """
    Fetches historical OHLC data for given stock from Zerodha API.
    Tries NSE_EQ (cash) first, then NSE_FO (futures & options).
    """
    try:
        print(f"inside get ohlc day")
        # Try segment NSE_EQ (Cash Market)
        #instruments_eq = kite.instruments("NSE")
        #print(f"after get ohlc day{instruments_eq}")
        inst = next((item for item in instruments_eq if item['tradingsymbol'] == symbol), None)
        print(f" NSE Found")
        if not inst:
            # Fallback to NSE_FO (F&O Segment)
            print(f"NO NSE")
            #instruments_fo = kite.instruments("NSE_FO")
            print(f"after NSE_fo{instruments_fo}")
            inst = next((item for item in instruments_fo if item['underlying_symbol'] == symbol or item['tradingsymbol'] == symbol), None)

        if not inst:
            print(f"⚠️ Instrument not found for {symbol} in both NSE_EQ and NSE_FO segments")
            return None

        instrument_token = inst['instrument_token']
        print(f"instrument token:{instrument_token}")
        from_date = (pd.Timestamp.today() - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = pd.Timestamp.today().strftime("%Y-%m-%d")

        data = kite.historical_data(instrument_token, to_date, to_date, interval=interval)
        print(f"history data")
        if not data:
            print(f"❌ No historical data returned for {symbol}")
            return None

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        return df

    except Exception as e:
        print(f"❌ Error fetching OHLC data for {symbol}: {e}")
        return None
def get_instrument_token(kite, symbol):
    """
    Fetches instrument token for a given symbol.
    Tries NSE_EQ (cash market) first, then NSE_FO (F&O)
    """

    try:
        # Try Cash Market (NSE_EQ)
        instruments_eq = kite.instruments("NSE")
        inst = next((item for item in instruments_eq if item['tradingsymbol'] == symbol), None)

        if not inst:
            # Fallback to Futures & Options (NSE_FO)
            instruments_fo = kite.instruments("NSE_FO")
            inst = next((item for item in instruments_fo if item['underlying_symbol'] == symbol or item['tradingsymbol'] == symbol), None)

        if inst:
            return inst['instrument_token']
        else:
            print(f"⚠️ Instrument not found for {symbol} in both NSE_EQ and NSE_FO")
            return None

    except Exception as e:
        print(f"❌ Error getting instrument token for {symbol}: {e}")
        return None
def get_instrument_token1(kite, symbol):
    """Fetches instrument token from Zerodha"""
    try:
        instruments = kite.instruments("NSE")
        inst = next((item for item in instrument if item['tradingsymbol'] == symbol), None)

        if not inst:
            # Fallback to Futures & Options
            instrument = kite.instruments("NSE_FO")
            inst = next((item for item in instrument if item['underlying_symbol'] == symbol), None)

        if not inst:
            print(f"⚠️ Instrument not found for {symbol}")
            return None

        instrument_token = inst['instrument_token']

        from_date = (pd.Timestamp.today() - pd.Timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = pd.Timestamp.today().strftime("%Y-%m-%d")

        data = kite.historical_data(instrument_token, from_date, to_date, interval=interval)
        if not data:
            print(f"❌ No historical data returned for {symbol}")
            return None

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        return df

    except Exception as e:
        print(f"❌ Error fetching OHLC data for {symbol}: {e}")
        return None

def get_trading_symbol(symbol):
    """
    Returns Zerodha symbol in 'exchange:tradingsymbol' format
    e.g., 'NSE:SBIN'
    """
    return f"NSE:{symbol}"