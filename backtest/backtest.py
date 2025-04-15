from strategy import Strategy
from position import Position
from trade_action import TradeAction
from typing import List, Type
import pandas as pd
import numpy as np


class Backtest:
    def __init__(
        self,
        data: pd.DataFrame,
        strategy: Type[Strategy],
        equity: float = float("inf"),
    ):
        """
        Initialize the Backtester with data, strategy and starting equity.

        :param data: DataFrame containing OHLCV data.
        :param strategy: Strategy class to be used for backtesting.
        :param equity: Starting cash or equity (default: infinite for unrestricted backtests)
        """
        self.data = data
        self.strategy = strategy()
        self.starting_equity = equity
        self.cash_balance = equity
        self.positions: List[Position] = []

    def run(self):
        # Run the backtest form the first interval to the second to last last interval. Data from the last interval cannot be used to open new positions.
        # Positions are opened and closed with the open price of the next interval.
        # All remaining positions on the last interval are closed with the open price.
        for i in range(len(self.data) - 1):
            # Get the data until that interval, included (historical data)
            historical_data = self.data.iloc[: i + 1]
            # Get the next interval data (next_data)
            next_data = self.data.iloc[i + 1]

            # Throw an error if the buying power becomes negative. Possibly handle position liquidation later;
            buying_power = self._calculate_buying_power(next_data)
            if buying_power < 0:
                raise ValueError(
                    f"Buying power is negative: {buying_power}. The strategy was liquidated at open on {next_data.name}."
                )

            # Call the strategy's on_candle method
            trade_actions = self.strategy.on_candle(historical_data, self.positions)

            # Update positions based on trade actions
            self._update_positions(trade_actions, next_data)

        self._calculate_pnl()

    def _update_positions(
        self, trade_actions: List[TradeAction], next_interval_data: pd.Series
    ):
        """
        Update the open positions based on the trade actions.

        :param tradeActions: List of trade actions to be executed.
        :return: Updated list of open positions.
        """

        # process exit actions first to
        # 1. avoid chance of closing a position that was just opened
        # 2. free up buying power for new positions
        trade_actions = sorted(
            trade_actions, key=lambda action: 0 if action.action == "exit" else 1
        )

        for action in trade_actions:
            # Validations
            if action.action == "enter" and (action.quantity is None) == (
                action.value is None
            ):
                raise ValueError(
                    "Provide exactly one of 'quantity' or 'value' in TradeAction"
                )
            if action.action not in ["enter", "exit"]:
                raise ValueError("Invalid action. Must be 'enter' or 'exit'.")
            if action.action == "exit" and action.position_id is None:
                raise ValueError("Position ID must be provided for exit action.")

            if action.action == "exit":
                # Close an existing position
                for pos in self._get_open_positions():
                    if pos.id == action.position_id:
                        pos.exit_time = next_interval_data.name

                        # Update available cash
                        self.cash_balance += pos.quantity * next_interval_data["Open"]

                        break
            elif action.action == "enter":
                # Convert value to quantity if needed
                if action.value is not None:
                    # Calculate quantity from value
                    action.quantity = action.value / next_interval_data["Open"]

                # Check if there is enough cash to enter the position
                entry_cost = action.quantity * next_interval_data["Open"]
                if self._calculate_buying_power(next_interval_data) < entry_cost:
                    raise ValueError(
                        f"Insufficient buying power to enter position {action} on {next_interval_data.name}. Buying power: {self._calculate_buying_power(next_interval_data)}, entry cost: {entry_cost}."
                    )

                new_position = Position(
                    id=f"{len(self.positions) + 1}",
                    entry_time=next_interval_data.name,
                    exit_time=None,
                    quantity=action.quantity,
                )
                self.positions.append(new_position)

                # Update available cash
                self.cash_balance -= entry_cost

    def _calculate_pnl(self):
        """
        Calculate the pnl for every position for every interval.
        """
        pnl_df = self.data.copy()
        value_cols = {}
        cash_balance = pd.Series(self.starting_equity, index=pnl_df.index)

        # Add position exposure for each position
        for position in self.positions:
            # Get the initial value of the position (value at entry time)
            entry_value = pnl_df.loc[position.entry_time, "Open"] * position.quantity

            # Get the exit time of the position (last interval if not closed)
            last_quantity_int_idx = (
                pnl_df.index.get_loc(position.exit_time) - 1
                if position.exit_time is not None
                else -1
            )
            last_quantity_idx = pnl_df.index[last_quantity_int_idx]

            # Subtract position entry value from the cash value
            cash_balance.loc[position.entry_time :] -= entry_value
            # Add back the exit value to the cash value
            if position.exit_time is not None:
                exit_value = pnl_df.loc[position.exit_time, "Open"] * position.quantity
                cash_balance.loc[position.exit_time :] += exit_value

            # Calculate position value for each interval
            qty_series = pd.Series(0.0, index=pnl_df.index)
            qty_series.loc[position.entry_time : last_quantity_idx] = position.quantity
            value_series = qty_series * pnl_df["Close"]

            value_cols[f"pos-{position.id}-value"] = value_series

        # Add the cash balance to the DataFrame
        pnl_df["cash_balance"] = cash_balance

        pos_value_df = pd.DataFrame(value_cols)

        # Calculate the equity
        pnl_df["equity"] = pnl_df["cash_balance"] + pos_value_df.sum(axis=1)
        # Calculate the pnl
        pnl_df["total_pnl"] = pnl_df["equity"] - self.starting_equity
        # Add the position values to the DataFrame
        pnl_df = pd.concat([pnl_df, pos_value_df], axis=1)

        self.pnl_df = pnl_df

    def stats(self):
        """
        Calculate the statistics of the backtest.
        """
        stats = {}

        stats["start"] = self.pnl_df.index[0]
        stats["end"] = self.pnl_df.index[-1]
        stats["duration"] = self.pnl_df.index[-1] - self.pnl_df.index[0]
        stats["starting_equity"] = self.starting_equity
        stats["peak_equity"] = self.pnl_df["equity"].max()
        stats["final_equity"] = self.pnl_df["equity"].iloc[-1]

        # Total return
        stats["total_return"] = self.pnl_df["total_pnl"].iloc[-1]
        stats["total_return_pct"] = (
            self.pnl_df["total_pnl"].iloc[-1] / self.starting_equity
        ) * 100

        # Buy and hold return
        if self.starting_equity != float("inf"):
            asset_change = (
                self.pnl_df["Close"].iloc[-1] / self.pnl_df["Open"].iloc[0] - 1
            )
            stats["buy_and_hold_return"] = asset_change * self.starting_equity
            stats["buy_and_hold_return_pct"] = asset_change * 100

        # Exposure time
        total_exposure_series = (
            self.pnl_df[[f"pos-{pos.id}-value" for pos in self.positions]]
            .abs()
            .sum(axis=1)
        )
        stats["exposure_time"] = (total_exposure_series != 0).sum()
        stats["exposure_time_pct"] = (stats["exposure_time"] / len(self.pnl_df)) * 100

        # Max drawdown
        cumulative_max_series = self.pnl_df["total_pnl"].cummax()
        drawdown_series = self.pnl_df["total_pnl"] - cumulative_max_series
        stats["max_drawdown"] = drawdown_series.min()
        if self.starting_equity != float("inf"):
            stats["max_drawdown_pct"] = (
                drawdown_series.min()
                / (cumulative_max_series.iloc[-1] + self.starting_equity)
            ) * 100

        # Sharpe ratio
        if self.starting_equity != float("inf"):
            returns = self.pnl_df["equity"].pct_change().fillna(0)
            mean_return = returns.mean()
            std_return = returns.std()
            stats["sharpe_ratio"] = (
                mean_return / std_return if std_return != 0 else np.nan
            )

        # Win rate, average win, and average loss
        wins = []
        losses = []

        for pos in self.positions:
            entry_price = self.pnl_df.loc[pos.entry_time, "Open"]
            exit_price = (
                self.pnl_df.loc[pos.exit_time, "Open"]
                if pos.exit_time is not None
                else self.pnl_df["Close"].iloc[-1]
            )
            pnl = (exit_price - entry_price) * pos.quantity

            if pnl > 0:
                wins.append(pnl)
            elif pnl < 0:
                losses.append(pnl)

        total_trades = len(self.positions)
        win_trades = len(wins)

        stats["num_trades"] = total_trades
        stats["win_rate"] = win_trades / total_trades if total_trades else np.nan
        stats["avg_win"] = np.mean(wins) if wins else 0.0
        stats["avg_loss"] = np.mean(losses) if losses else 0.0
        stats["best_trade"] = max([*wins, *losses], default=0.0)
        stats["worst_trade"] = min([*wins, *losses], default=0.0)

        # Profit factor
        stats["profit_factor"] = (
            sum(wins) / abs(sum(losses)) if sum(losses) != 0 else np.nan
        )

        # Expectancy
        stats["expectancy"] = (
            stats["win_rate"] * stats["avg_win"]
            + (1 - stats["win_rate"]) * stats["avg_loss"]
        )

        # Position duration
        position_times = [
            [pos.entry_time, pos.exit_time or self.pnl_df.index[-1]]
            for pos in self.positions
        ]
        durations = [exit_time - entry_time for entry_time, exit_time in position_times]
        stats["max_position_duration"] = max(durations) if durations else 0
        stats["avg_position_duration"] = np.mean(durations) if durations else 0

        print("Backtest Statistics:")
        for key, value in stats.items():
            print(f"{key}: {value}")

        return stats

    def _get_open_positions(self) -> List[Position]:
        """
        Get the list of open positions.

        :return: List of open positions.
        """
        return [pos for pos in self.positions if pos.exit_time is None]

    def _calculate_buying_power(self, next_interval_data) -> float:
        """
        Calculate the buying power of the portfolio.

        :return: Buying power of the portfolio.
        """
        open_short_positions = [
            pos for pos in self._get_open_positions() if pos.quantity < 0
        ]

        short_exposure = np.sum(
            [
                next_interval_data["Open"] * abs(pos.quantity)
                for pos in open_short_positions
            ]
        )
        return self.cash_balance - short_exposure
