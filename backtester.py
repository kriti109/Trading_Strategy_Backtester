import pandas as pd
import numpy as np
from datetime import datetime

class Backtester:
    def __init__(self, initial_capital=10000, transaction_cost_pct=0.0003):
        """
        Initialize the backtester
        
        Parameters:
        -----------
        initial_capital : float
            Starting capital amount
        transaction_cost_pct : float
            Transaction cost per side (default 0.03% = 0.0003)
        """
        self.initial_capital = initial_capital
        self.transaction_cost_pct = transaction_cost_pct
        
    def run_backtest(self, data, price_col='close', signal_col='signal', datetime_col='datetime'):
        """
        Run backtest on the provided data
        
        Parameters:
        -----------
        data : pd.DataFrame
            DataFrame containing price and signal data
        price_col : str
            Name of the price column
        signal_col : str
            Name of the signal column (1=long, -1=short, 0.5=half long, etc.)
        datetime_col : str
            Name of the datetime column
            
        Returns:
        --------
        dict : Backtest results and statistics
        """
        df = data.copy()
        
        # Ensure datetime column is datetime type
        if datetime_col in df.columns:
            df[datetime_col] = pd.to_datetime(df[datetime_col], format='%d-%m-%Y %H:%M', errors='coerce')
            df = df.sort_values(datetime_col).reset_index(drop=True)
        
        # Initialize tracking variables
        capital = self.initial_capital
        position = 0  # Current position: 1=full long, -1=full short, 0.5=half long, etc.
        entry_price = 0
        position_value = 0
        
        # Lists to track performance
        trades = []
        daily_pnl = {}
        equity_curve = []
        transaction_costs = []
        
        for i in range(len(df)):
            current_price = df.loc[i, price_col]
            current_signal = df.loc[i, signal_col]
            current_time = df.loc[i, datetime_col] if datetime_col in df.columns else i
            current_date = current_time.date() if isinstance(current_time, datetime) else None
            
            # Calculate current position P&L if we have an open position
            if position != 0:
                if position > 0:  # Long position
                    unrealized_pnl = position_value * (current_price / entry_price - 1)
                else:  # Short position
                    unrealized_pnl = position_value * (1 - current_price / entry_price)
                
                current_equity = capital + unrealized_pnl
            else:
                current_equity = capital
            
            equity_curve.append({
                'datetime': current_time,
                'equity': current_equity,
                'price': current_price,
                'signal': current_signal,
                'position': position
            })
            
            # Check if we need to change position
            if i == 0:
                # First bar - enter position based on signal
                new_position = current_signal
            else:
                new_position = current_signal
            
            # Execute trade if position changes
            if new_position != position:
                # Close existing position if any
                if position != 0:
                    if position > 0:  # Closing long
                        pnl = position_value * (current_price / entry_price - 1)
                    else:  # Closing short
                        pnl = position_value * (1 - current_price / entry_price)
                    
                    # Calculate transaction cost for closing
                    exit_cost = abs(position_value) * self.transaction_cost_pct
                    transaction_costs.append(exit_cost)
                    
                    # Update capital
                    capital += pnl - exit_cost
                    
                    # Record trade
                    trades.append({
                        'entry_time': entry_time,
                        'exit_time': current_time,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'position_type': 'LONG' if position > 0 else 'SHORT',
                        'position_size': abs(position),
                        'pnl': pnl,
                        'transaction_cost': exit_cost,
                        'net_pnl': pnl - exit_cost
                    })
                    
                    # Track daily P&L
                    if current_date:
                        if current_date not in daily_pnl:
                            daily_pnl[current_date] = 0
                        daily_pnl[current_date] += pnl - exit_cost
                    
                    # Reset position
                    position = 0
                    position_value = 0
                
                # Open new position if signal is not 0
                if new_position != 0:
                    position = new_position
                    position_value = capital * abs(new_position)
                    entry_price = current_price
                    entry_time = current_time
                    
                    # Calculate transaction cost for opening
                    entry_cost = position_value * self.transaction_cost_pct
                    transaction_costs.append(entry_cost)
                    capital -= entry_cost
        
        # Close any remaining position at the end
        if position != 0:
            final_price = df.loc[len(df)-1, price_col]
            final_time = df.loc[len(df)-1, datetime_col] if datetime_col in df.columns else len(df)-1
            final_date = final_time.date() if isinstance(final_time, datetime) else None
            
            if position > 0:  # Closing long
                pnl = position_value * (final_price / entry_price - 1)
            else:  # Closing short
                pnl = position_value * (1 - final_price / entry_price)
            
            exit_cost = abs(position_value) * self.transaction_cost_pct
            transaction_costs.append(exit_cost)
            capital += pnl - exit_cost
            
            trades.append({
                'entry_time': entry_time,
                'exit_time': final_time,
                'entry_price': entry_price,
                'exit_price': final_price,
                'position_type': 'LONG' if position > 0 else 'SHORT',
                'position_size': abs(position),
                'pnl': pnl,
                'transaction_cost': exit_cost,
                'net_pnl': pnl - exit_cost
            })
            
            if final_date:
                if final_date not in daily_pnl:
                    daily_pnl[final_date] = 0
                daily_pnl[final_date] += pnl - exit_cost
        
        # Calculate statistics
        results = self._calculate_statistics(
            capital, 
            trades, 
            daily_pnl, 
            equity_curve, 
            transaction_costs,
            df[datetime_col].min() if datetime_col in df.columns else None,
            df[datetime_col].max() if datetime_col in df.columns else None
        )
        
        return results
    
    def _calculate_statistics(self, final_capital, trades, daily_pnl, equity_curve, transaction_costs, start_date, end_date):
        """Calculate backtest statistics"""
        
        total_pnl = final_capital - self.initial_capital
        total_transaction_cost = sum(transaction_costs)
        
        # Trade statistics
        trades_df = pd.DataFrame(trades)
        n_trades = len(trades)
        
        if n_trades > 0:
            winning_trades = trades_df[trades_df['net_pnl'] > 0]
            losing_trades = trades_df[trades_df['net_pnl'] < 0]
            
            n_winning = len(winning_trades)
            n_losing = len(losing_trades)
            win_rate = (n_winning / n_trades * 100) if n_trades > 0 else 0
            
            avg_win = winning_trades['net_pnl'].mean() if n_winning > 0 else 0
            avg_loss = losing_trades['net_pnl'].mean() if n_losing > 0 else 0
            
            best_trade = trades_df['net_pnl'].max() if n_trades > 0 else 0
            worst_trade = trades_df['net_pnl'].min() if n_trades > 0 else 0
            
            # Calculate average hold period
            if 'entry_time' in trades_df.columns and 'exit_time' in trades_df.columns:
                trades_df['hold_period'] = (trades_df['exit_time'] - trades_df['entry_time']).dt.total_seconds()
                avg_hold_seconds = trades_df['hold_period'].mean()
                avg_hold_minutes = avg_hold_seconds / 60
            else:
                avg_hold_seconds = 0
                avg_hold_minutes = 0
        else:
            n_winning = 0
            n_losing = 0
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            best_trade = 0
            worst_trade = 0
            avg_hold_seconds = 0
            avg_hold_minutes = 0
        
        # Daily statistics
        daily_pnl_values = list(daily_pnl.values())
        n_days = len(daily_pnl_values)
        
        if n_days > 0:
            winning_days = sum(1 for pnl in daily_pnl_values if pnl > 0)
            losing_days = sum(1 for pnl in daily_pnl_values if pnl < 0)
            best_day_pnl = max(daily_pnl_values)
            worst_day_pnl = min(daily_pnl_values)
        else:
            winning_days = 0
            losing_days = 0
            best_day_pnl = 0
            worst_day_pnl = 0
        
        # Calculate returns metrics
        final_returns = (final_capital - self.initial_capital) / self.initial_capital * 100
        
        # Calculate number of days
        if start_date and end_date:
            n_calendar_days = (end_date - start_date).days + 1
        else:
            n_calendar_days = n_days
        
        # CAGR calculation
        years = n_calendar_days / 365.25
        if years > 0:
            cagr = (pow(final_capital / self.initial_capital, 1/years) - 1) * 100
        else:
            cagr = 0
        
        # Annualized returns
        if years > 0:
            annualized_returns = (final_capital / self.initial_capital - 1) / years * 100
        else:
            annualized_returns = 0
        
        # Sharpe Ratio (using daily returns)
        equity_df = pd.DataFrame(equity_curve)
        equity_df['returns'] = equity_df['equity'].pct_change()
        daily_returns = equity_df['returns'].dropna()
        
        if len(daily_returns) > 0 and daily_returns.std() != 0:
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Maximum Drawdown
        equity_df['cummax'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = (equity_df['equity'] - equity_df['cummax']) / equity_df['cummax'] * 100
        max_drawdown = equity_df['drawdown'].min()
        
        # Calmar Ratio
        if max_drawdown < 0:
            calmar_ratio = abs(cagr / max_drawdown)
        else:
            calmar_ratio = 0
        
        # Compile results
        results = {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_pnl': total_pnl,
            'total_transaction_cost': total_transaction_cost,
            'penalty_counts': 0,
            'final_returns': final_returns,
            'cagr': cagr,
            'annualized_returns': annualized_returns,
            'sharpe_ratio': sharpe_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'n_days': n_calendar_days,
            'winning_days': winning_days,
            'losing_days': losing_days,
            'best_day': winning_days,
            'worst_day': losing_days,
            'best_day_pnl': best_day_pnl,
            'worst_day_pnl': worst_day_pnl,
            'total_trades': n_trades,
            'winning_trades': n_winning,
            'losing_trades': n_losing,
            'win_rate': win_rate,
            'avg_winning_trade': avg_win,
            'avg_losing_trade': avg_loss,
            'avg_hold_seconds': avg_hold_seconds,
            'avg_hold_minutes': avg_hold_minutes,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'trades_df': trades_df,
            'equity_curve': equity_df
        }
        
        return results
    
    def print_summary(self, results):
        """Print backtest summary in the specified format"""
        print("=" * 50)
        print("=== Backtest Summary ===")
        print(f"Initial Capital               : {results['initial_capital']:.2f}")
        print(f"Final Capital                 : {results['final_capital']:.2f}")
        print(f"Total PnL                     : {results['total_pnl']:.2f}")
        print(f"Total Transaction Cost         : {results['total_transaction_cost']:.2f}")
        print(f"Penalty Counts                : {results['penalty_counts']}")
        print(f"Final Returns                 : {results['final_returns']:.2f}%")
        print(f"CAGR                          : {results['cagr']:.4f}%")
        print(f"Annualized Returns            : {results['annualized_returns']:.4f}%")
        print(f"Sharpe Ratio                  : {results['sharpe_ratio']:.4f}")
        print(f"Calmar Ratio                  : {results['calmar_ratio']:.4f}")
        print(f"Maximum Drawdown              : {results['max_drawdown']:.4f}%")
        print(f"No. of Days                   : {results['n_days']}")
        print(f"Winning Days                  : {results['winning_days']}")
        print(f"Losing Days                   : {results['losing_days']}")
        print(f"Best Day                      : {results['best_day']}")
        print(f"Worst Day                     : {results['worst_day']}")
        print(f"Best Day PnL                  : {results['best_day_pnl']:.2f}")
        print(f"Worst Day PnL                 : {results['worst_day_pnl']:.2f}")
        print(f"Total Trades                  : {results['total_trades']}")
        print(f"Winning Trades                : {results['winning_trades']}")
        print(f"Losing Trades                 : {results['losing_trades']}")
        print(f"Win Rate (%)                  : {results['win_rate']:.2f}%")
        print(f"Average Winning Trade         : {results['avg_winning_trade']:.4f}")
        print(f"Average Losing Trade          : {results['avg_losing_trade']:.4f}")
        print(f"Average Hold Period (seconds) : {results['avg_hold_seconds']:.2f}")
        print(f"Average Hold Period (minutes) : {results['avg_hold_minutes']:.2f}")
        print("=" * 50)


# Example usage
if __name__ == "__main__":
    # Load your data
    # df = pd.read_csv('your_data.csv')
    # Expected columns: 'datetime' (DD-MM-YYYY HH-MM format), 'close' (price), 'signal' (1, -1, 0.5, etc.)
    
    # Initialize backtester
    backtester = Backtester(initial_capital=10000, transaction_cost_pct=0.0003)
    
    # Run backtest
    # results = backtester.run_backtest(df, price_col='close', signal_col='signal', datetime_col='datetime')
    
    # Print summary
    # backtester.print_summary(results)
    
    # Access detailed results
    # trades_df = results['trades_df']  # DataFrame with all trades
    # equity_curve = results['equity_curve']  # DataFrame with equity curve
    
    print("Backtester initialized successfully!")
    print("To use:")
    print("1. Load your CSV with columns: 'datetime', 'close', 'signal'")
    print("2. backtester = Backtester(initial_capital=10000, transaction_cost_pct=0.0003)")
    print("3. results = backtester.run_backtest(df)")
    print("4. backtester.print_summary(results)")
