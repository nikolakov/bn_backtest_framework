from strategy import Strategy
from position import Position
from trade_action import TradeAction
from typing import List, Type
import pandas as pd
import numpy as np

class Backtest:
    def __init__(self, data: pd.DataFrame, strategy: Type[Strategy]):
        """
        Initialize the Backtester with data and strategy.

        :param data: DataFrame containing OHLCV data.
        :param strategy: Strategy class to be used for backtesting.
        """
        self.data = data
        self.strategy = strategy()
        self.positions: List[Position] = []

    def run(self):
        # Run the backtest form the first interval to the second to last last interval. Data from the last interval cannot be used to open new positions.
        # Positions are opened and closed with the open price of the next interval.
        # All remaining positions on the last interval are closed with the open price.
        for i in range(len(self.data) - 1):
            # Get the data until that interval, included (historical data)
            historical_data = self.data.iloc[:i + 1]
            # Get the next interval data (next_data)
            next_data = self.data.iloc[i + 1]

            # Call the strategy's on_candle method
            trade_actions = self.strategy.on_candle(historical_data, self.positions)

            # Update positions based on trade actions
            self.positions = self._update_positions(trade_actions, next_data)

        # Close all remaining positions with the open price of the last interval
        last_interval_data = self.data.iloc[-1]
        for pos in self.positions:
            if pos.exit_time is None:
                pos.exit_time = last_interval_data.name
                # Assuming the exit price is the open price of the last interval

        self._calculate_pnl()

    def _update_positions(self, trade_actions: List[TradeAction], next_interval_data: pd.Series):
        """
        Update the open positions based on the trade actions.

        :param tradeActions: List of trade actions to be executed.
        :return: Updated list of open positions.
        """
        updated_positions = self.positions.copy()

        for action in trade_actions:
            # Validations
            if action.action == 'enter' and (action.quantity is None) == (action.value is None):
                raise ValueError("Provide exactly one of 'quantity' or 'value' in TradeAction")
            if action.action not in ['enter', 'exit']:
                raise ValueError("Invalid action. Must be 'enter' or 'exit'.")
            if action.action == 'exit' and action.position_id is None:
                raise ValueError("Position ID must be provided for exit action.")
            
            # Convert value to quantity if needed
            if action.action == 'enter' and action.value is not None:
                # Calculate quantity from value
                action.quantity = action.value / next_interval_data['Open']
            
            if action.action == 'enter':
                # Open a new position
                new_position = Position(
                    id=f"{len(updated_positions) + 1}",
                    entry_time=next_interval_data.name,
                    exit_time=None,
                    quantity=action.quantity
                )
                updated_positions.append(new_position)
            elif action.action == 'exit':
                # Close an existing position
                for pos in updated_positions:
                    if pos.id == action.position_id:
                        pos.exit_time = next_interval_data.name
                        break

        return updated_positions

    def _calculate_pnl(self):
        """
        Calculate the pnl for every position for every interval.
        """
        pnl_df = self.data.copy()
        pnl_cols = {}
        total_pnl = pd.Series(0.0, index=pnl_df.index)

        # Add position exposure for each position
        for position in self.positions:
            # Get the initial value of the position (value at entry time)
            entry_value = pnl_df.loc[position.entry_time, 'Open'] * position.quantity
            exit_value = pnl_df.loc[position.exit_time, 'Open'] * position.quantity

            qty_series = pd.Series(0.0, index=pnl_df.index)
            qty_series.loc[position.entry_time : position.exit_time] = position.quantity

            # Calculate position value for each interval
            value_series = qty_series * pnl_df['Close']

            # Calculate positon pnl for each interval
            pnl_series = pd.Series(0.0, index=pnl_df.index)
            pnl_series.loc[position.entry_time : position.exit_time] = value_series - entry_value

            # Add the realized pnl after the position is closed
            pnl_series.loc[position.exit_time:] = exit_value - entry_value

            # Add the position pnl to the dictionary
            pnl_cols[f"pos-{position.id}-pnl"] = pnl_series
            # Add position pnl to the total
            total_pnl += pnl_series

        # Add the position pnl columns to the dataframe
        pnl_df = pd.concat([pnl_df, pd.DataFrame(pnl_cols)], axis=1)
        # Add the total pnl to the dataframe
        pnl_df['total_pnl'] = total_pnl

        self.pnl_df = pnl_df

    def stats(self):
        """
        Calculate the statistics of the backtest.
        """
        stats = {}

        # Calculate total return
        stats['total_return'] = self.pnl_df['total_pnl'].iloc[-1]

        # Calculate max drawdown
        drawdown_series = self.pnl_df['total_pnl'] - self.pnl_df['total_pnl'].cummax()
        stats['max_drawdown'] = drawdown_series.min()

        # Calculate Sharpe ratio
        returns = self.pnl_df['total_pnl'].diff().fillna(0)
        mean_return = returns.mean()
        std_return = returns.std()
        stats['sharpe_ratio'] = mean_return / std_return if std_return != 0 else np.nan

        # Calculate win rate, average win, and average loss
        wins = []
        losses = []

        for pos in self.positions:
            entry_price = self.pnl_df.loc[pos.entry_time, 'Open']
            exit_price = self.pnl_df.loc[pos.exit_time, 'Open']
            pnl = (exit_price - entry_price) * pos.quantity

            if pnl > 0:
                wins.append(pnl)
            elif pnl < 0:
                losses.append(pnl)

        total_trades = len(self.positions)
        win_trades = len(wins)

        stats['num_trades'] = total_trades
        stats['win_rate'] = win_trades / total_trades if total_trades else np.nan
        stats['avg_win'] = np.mean(wins) if wins else 0.0
        stats['avg_loss'] = np.mean(losses) if losses else 0.0

        print("Backtest Statistics:")
        for key, value in stats.items():
            print(f"{key}: {value}")

        return stats
