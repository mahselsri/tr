import os
from kiteconnect import KiteConnect
import streamlit as st
SESSION_FILE = "zerodha_app_session.txt"
API_KEY = "f1t0xfioknkg0v64"
API_SECRET = "2y0071w25pm3mj49pxvzqdtnk3g4ocvg"

def load_access_token():
    """Load access token from file"""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_access_token(token):
    """Save access token to file"""
    with open(SESSION_FILE, "w") as f:
        f.write(token)

def get_kite():
    """
    Returns authenticated Kite instance.
    Uses st.session_state to preserve state across reruns.
    """
    if 'kite' in st.session_state:
        return st.session_state['kite']

    kite = KiteConnect(api_key=API_KEY)

    # Try loading saved token
    access_token = load_access_token()
    if access_token:
        try:
            kite.set_access_token(access_token)
            kite.profile()  # Quick test to see if token is valid
            st.session_state['kite'] = kite
            return kite
        except Exception as e:
            print("⚠️ Saved token invalid:", e)

    # If no valid token found
    st.session_state['kite'] = None
    return None