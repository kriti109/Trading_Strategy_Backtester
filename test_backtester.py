"""
Test script with sample data to demonstrate the backtester
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backtester import Backtester

# Create sample data similar to your format
print("Creating sample data...")

# Generate sample timestamps (1-minute bars)
start_date = datetime(2024, 1, 1, 9, 15)
n_bars = 1000

dates = []
for i in range(n_bars):
    dates.append(start_date + timedelta(minutes=i))

# Convert to DD-MM-YYYY HH-MM format
datetime_strings = [d.strftime('%d-%m-%Y %H:%M') for d in dates]

# Generate sample price data (simulated Nifty50 movement)
np.random.seed(42)
initial_price = 21500
returns = np.random.randn(n_bars) * 0.001  # 0.1% volatility
prices = initial_price * (1 + returns).cumprod()

# Generate sample signals
# Strategy: Simple moving average crossover simulation
signals = []
for i in range(n_bars):
    if i < 50:
        signals.append(0)  # No position initially
    elif i % 100 < 40:
        signals.append(1)  # Long
    elif i % 100 < 50:
        signals.append(0.5)  # Half long
    elif i % 100 < 70:
        signals.append(0)  # Flat
    else:
        signals.append(-1)  # Short

# Create DataFrame
df = pd.DataFrame({
    'datetime': datetime_strings,
    'close': prices,
    'signal': signals
})

print(f"Generated {len(df)} bars of sample data")
print("\nFirst 10 rows:")
print(df.head(10))

# Save sample data
df.to_csv('sample_data.csv', index=False)
print("\nSaved sample data to: sample_data.csv")

# Run backtest
print("\n" + "="*50)
print("Running Backtest...")
print("="*50)

backtester = Backtester(
    initial_capital=10000,
    transaction_cost_pct=0.0003
)

results = backtester.run_backtest(
    data=df,
    price_col='close',
    signal_col='signal',
    datetime_col='datetime'
)

# Print summary
backtester.print_summary(results)

# Show some trades
print("\n" + "="*50)
print("Sample Trades (First 10):")
print("="*50)
trades_df = results['trades_df']
if len(trades_df) > 0:
    print(trades_df.head(10).to_string())
    
    # Save trades
    trades_df.to_csv('sample_trades.csv', index=False)
    print("\nSaved trades to: sample_trades.csv")
else:
    print("No trades executed")

# Save equity curve
equity_curve = results['equity_curve']
equity_curve.to_csv('sample_equity_curve.csv', index=False)
print("Saved equity curve to: sample_equity_curve.csv")

print("\n" + "="*50)
print("Test completed successfully!")
print("="*50)
print("\nYou can now use this backtester with your actual data:")
print("1. Prepare your CSV with columns: datetime, close, signal")
print("2. Use the example_usage.py script as a template")
print("3. Run: python example_usage.py")
