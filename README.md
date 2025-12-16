# Trading_Strategy_Backtester

A comprehensive backtesting engine for long/short/fractional trading strategies with support for compounding returns and detailed performance analytics.

## Features

✅ **Flexible Position Management**
- Long positions (signal = 1)
- Short positions (signal = -1)
- Fractional positions (signal = 0.5 for half capital, etc.)
- Seamless position transitions (long→short, short→long, etc.)

✅ **Realistic Transaction Costs**
- Configurable per-side transaction costs (default: 0.03% per side)
- Separate entry and exit costs tracked

✅ **Compounding Returns**
- Capital compounds over time
- Continuous position tracking across days
- No daily resets

✅ **Comprehensive Metrics**
- Returns: Total PnL, CAGR, Annualized Returns
- Risk: Sharpe Ratio, Calmar Ratio, Maximum Drawdown
- Trade Analytics: Win rate, Average win/loss, Hold periods
- Daily Analytics: Winning/losing days, Best/worst day PnL

## Installation

No special installation required. Just ensure you have:

```bash
pip install pandas numpy
```

Optional for visualization:
```bash
pip install matplotlib
```

## Quick Start

### 1. Prepare Your Data

Your CSV should have the following columns:

| Column | Format | Description |
|--------|--------|-------------|
| datetime | DD-MM-YYYY HH:MM | Timestamp for each bar |
| close | float | Closing price |
| signal | float | Trading signal (1=long, -1=short, 0.5=half, etc.) |

Example CSV:
```csv
datetime,close,signal
01-01-2024 09:15,21500.50,1
01-01-2024 09:16,21505.25,1
01-01-2024 09:17,21510.00,0
01-01-2024 09:18,21508.75,-1
```

### 2. Run the Backtester

```python
from backtester import Backtester

# Load your data
df = pd.read_csv('your_data.csv')

# Initialize backtester
backtester = Backtester(
    initial_capital=10000,      # Starting capital
    transaction_cost_pct=0.0003 # 0.03% per side
)

# Run backtest
results = backtester.run_backtest(
    data=df,
    price_col='close',
    signal_col='signal',
    datetime_col='datetime'
)

# Print summary
backtester.print_summary(results)
```

## Signal Logic

The backtester handles signal transitions intelligently:

### Signal Values
- **1.0**: Full long position (100% of capital)
- **0.5**: Half long position (50% of capital)
- **0.0**: No position (flat)
- **-0.5**: Half short position (50% of capital)
- **-1.0**: Full short position (100% of capital)

### Position Transitions

| Current Position | New Signal | Action |
|-----------------|------------|---------|
| 0 (Flat) | 1 (Long) | Enter long with full capital |
| 1 (Long) | 1 (Long) | Hold position |
| 1 (Long) | 0 (Flat) | Close long, go flat |
| 1 (Long) | -1 (Short) | Close long, open short (2 transactions) |
| 1 (Long) | 0.5 (Half) | Close long, open half long |
| -1 (Short) | 1 (Long) | Close short, open long (2 transactions) |

### Transaction Costs

Transaction costs are applied on BOTH entry and exit:
- **Entry**: Cost = Position Value × 0.03%
- **Exit**: Cost = Position Value × 0.03%
- **Total**: 0.06% round-trip

For position changes (e.g., long→short):
- Exit cost charged for closing old position
- Entry cost charged for opening new position

## Output Metrics

### Capital Metrics
- **Initial Capital**: Starting capital
- **Final Capital**: Ending capital after all trades
- **Total PnL**: Net profit/loss
- **Total Transaction Cost**: Sum of all transaction costs
- **Final Returns**: Percentage return on initial capital

### Performance Metrics
- **CAGR**: Compound Annual Growth Rate
- **Annualized Returns**: Simple annualized return
- **Sharpe Ratio**: Risk-adjusted returns (annualized)
- **Calmar Ratio**: CAGR / Maximum Drawdown
- **Maximum Drawdown**: Largest peak-to-trough decline

### Trade Statistics
- **Total Trades**: Number of completed trades
- **Winning/Losing Trades**: Count and win rate
- **Average Winning/Losing Trade**: Mean P&L
- **Best/Worst Trade**: Largest profit/loss
- **Average Hold Period**: Mean time in position

### Daily Statistics
- **Number of Days**: Calendar days in backtest
- **Winning/Losing Days**: Days with positive/negative P&L
- **Best/Worst Day PnL**: Largest daily profit/loss

## Advanced Usage

### Access Detailed Results

```python
# Run backtest
results = backtester.run_backtest(df)

# Get trades DataFrame
trades_df = results['trades_df']
print(trades_df.columns)
# ['entry_time', 'exit_time', 'entry_price', 'exit_price', 
#  'position_type', 'position_size', 'pnl', 'transaction_cost', 'net_pnl']

# Get equity curve
equity_curve = results['equity_curve']
print(equity_curve.columns)
# ['datetime', 'equity', 'price', 'signal', 'position', 'drawdown']

# Export to CSV
trades_df.to_csv('my_trades.csv', index=False)
equity_curve.to_csv('my_equity_curve.csv', index=False)
```

### Plot Results

```python
import matplotlib.pyplot as plt

equity_curve = results['equity_curve']

plt.figure(figsize=(14, 7))

# Plot equity
plt.subplot(2, 1, 1)
plt.plot(equity_curve['datetime'], equity_curve['equity'])
plt.title('Equity Curve')
plt.ylabel('Capital')
plt.grid(True)

# Plot drawdown
plt.subplot(2, 1, 2)
plt.plot(equity_curve['datetime'], equity_curve['drawdown'], color='red')
plt.title('Drawdown')
plt.ylabel('Drawdown %')
plt.grid(True)

plt.tight_layout()
plt.savefig('backtest_results.png')
```

### Custom Analysis

```python
results = backtester.run_backtest(df)

# Analyze trades
trades = results['trades_df']

# Long vs Short performance
long_trades = trades[trades['position_type'] == 'LONG']
short_trades = trades[trades['position_type'] == 'SHORT']

print(f"Long trades: {len(long_trades)}, Avg PnL: {long_trades['net_pnl'].mean():.2f}")
print(f"Short trades: {len(short_trades)}, Avg PnL: {short_trades['net_pnl'].mean():.2f}")

# Win rate by position type
long_win_rate = (long_trades['net_pnl'] > 0).sum() / len(long_trades) * 100
short_win_rate = (short_trades['net_pnl'] > 0).sum() / len(short_trades) * 100

print(f"Long win rate: {long_win_rate:.2f}%")
print(f"Short win rate: {short_win_rate:.2f}%")

# Monthly returns
equity_curve = results['equity_curve']
equity_curve['month'] = equity_curve['datetime'].dt.to_period('M')
monthly_returns = equity_curve.groupby('month')['equity'].last().pct_change() * 100
print("\nMonthly Returns:")
print(monthly_returns)
```

## Important Notes

### Position Sizing
- Signals represent the **fraction of capital** to deploy
- Signal = 1 means 100% of current capital
- Capital compounds, so position sizes grow/shrink with P&L

### Transaction Costs
- Applied on EVERY position change
- Costs reduce capital before opening new positions
- Realistic modeling of slippage + brokerage

### Overnight Positions
- Positions are carried forward across days
- No daily capital resets
- True compounding behavior

### Data Requirements
- Minimum 1 bar required
- Datetime must be in DD-MM-YYYY HH:MM format
- Missing signals are treated as 0 (no position)

## Troubleshooting

### Issue: Poor performance compared to expectations
**Check:**
- Are transaction costs too high? Reduce `transaction_cost_pct`
- Are signals generating too many trades? Filter signals
- Is the strategy profitable before costs?

### Issue: Wrong number of trades
**Check:**
- Signal changes trigger trades
- Even small signal changes (1→0.9) create trades
- Verify signal generation logic

### Issue: Dates not parsing
**Solution:**
```python
# Ensure datetime column is in correct format
df['datetime'] = pd.to_datetime(df['datetime'], format='%d-%m-%Y %H:%M')
```

## Example Output

```
==================================================
=== Backtest Summary ===
Initial Capital               : 100.00
Final Capital                 : 139.68
Total PnL                     : 39.68
Total Transaction Cost         : 11.27
Penalty Counts                : 0
Final Returns                 : 39.68%
CAGR                          : 18.7513%
Annualized Returns            : 20.4062%
Sharpe Ratio                  : 2.4812
Calmar Ratio                  : 5.3156
Maximum Drawdown              : -3.8390%
No. of Days                   : 490
Winning Days                  : 85
Losing Days                   : 57
Best Day                      : 67
Worst Day                     : 33
Best Day PnL                  : 12.49
Worst Day PnL                 : -1.56
Total Trades                  : 637
Winning Trades                : 328
Losing Trades                 : 309
Win Rate (%)                  : 51.49%
Average Winning Trade         : 0.5211
Average Losing Trade          : -0.2349
Average Hold Period (seconds) : 6,139.46
Average Hold Period (minutes) : 102.32
==================================================
```

## Files Included

- **backtester.py**: Main backtester class
- **example_usage.py**: Example script with your data
- **test_backtester.py**: Test script with sample data
- **README.md**: This documentation

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example scripts
3. Verify your data format matches requirements

## License

Free to use and modify for your trading strategies.
