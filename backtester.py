import pandas as pd
import numpy as np
from tqdm import tqdm
from data_fetcher import fetch_nifty_50_stocks, get_stock_data
from scorer import calculate_score

class SwingTradeBacktester:
    def __init__(self, start_date="2024-01-01", end_date="2024-12-31", lookback_days=5):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.lookback_days = lookback_days
        self.trades = []

    def run_backtest(self):
        symbols = fetch_nifty_50_stocks()
        dates = pd.date_range(self.start_date, self.end_date, freq='B')  # Business Days

        for date in tqdm(dates, desc="Backtesting Progress"):
            try:
                df_scores = []

                for symbol in symbols:
                    try:
                        df = get_stock_data(symbol, period="6mo")
                        df = df[df.index <= date]  # Filter up to current date

                        if len(df) < 30:
                            continue

                        score = calculate_score(df)
                        df_scores.append({
                            'Symbol': symbol,
                            'Score': score,
                            'Entry Date': date,
                            'Entry Price': df['Close'].iloc[-1]
                        })
                    except Exception as e:
                        continue

                df_scores = pd.DataFrame(df_scores)
                df_scores = df_scores.sort_values(by='Score', ascending=False).head(1)

                if not df_scores.empty:
                    entry_row = df_scores.iloc[0]
                    symbol = entry_row['Symbol']
                    entry_price = entry_row['Entry Price']
                    entry_date = entry_row['Entry Date']

                    # Get future price
                    future_df = get_stock_data(symbol, period="1y")
                    future_df = future_df[future_df.index > entry_date]

                    if len(future_df) >= self.lookback_days:
                        exit_price = future_df['Close'].iloc[self.lookback_days - 1]
                        exit_date = future_df.index[self.lookback_days - 1]
                        pnl = (exit_price - entry_price) / entry_price * 100
                        win = 1 if pnl > 0 else 0

                        self.trades.append({
                            'Symbol': symbol,
                            'Entry Date': entry_date,
                            'Exit Date': exit_date,
                            'Entry Price': round(entry_price, 2),
                            'Exit Price': round(exit_price, 2),
                            'PnL (%)': round(pnl, 2),
                            'Win': win
                        })

            except Exception as e:
                continue

        self.trades = pd.DataFrame(self.trades)
        return self.generate_report()

    def generate_report(self):
        total_trades = len(self.trades)
        wins = self.trades['Win'].sum()
        win_rate = round(wins / total_trades * 100, 2) if total_trades > 0 else 0
        avg_return = round(self.trades['PnL (%)'].mean(), 2)
        max_drawdown = round(self.trades['PnL (%)'].min(), 2)
        total_return = round(self.trades['PnL (%)'].sum(), 2)

        report = {
            "Total Trades": total_trades,
            "Win Rate (%)": win_rate,
            "Avg Return per Trade (%)": avg_return,
            "Max Drawdown (%)": max_drawdown,
            "Total Return (%)": total_return,
            "Trades": self.trades
        }

        return report