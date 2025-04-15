# BN Backtest Framework

A simple yet powerful Python backtesting framework designed to simulate and evaluate trading strategies using OHLCV data. Built for clarity and extensibility

## Features
- ✅ Event-driven backtesting loop
- ✅ Strategy interface via on_candle() callback
- ✅ Long and short position support
- ✅ Multiple simultaneous positions per symbol
- ✅ Set position size by quantity or notional value
- ✅ Realistic fills at next interval's open
- ✅ Vectorized PnL and equity calculation using Pandas
- ✅ Portfolio equity tracking and buying power enforcement
- ✅ Clean modular design: strategy, position, trade action, and engine separated
- ✅ Rich performance stats (Sharpe, drawdown, expectancy, etc.)

## Project Structure
```plaintext
bn_backtest_framework/
├── backtest/                     # Main package
│   ├── __init__.py               # Exposes Backtester, Strategy, etc.
│   ├── backtest.py               # Contains Backtester
│   ├── strategy.py               # Strategy base class
│   ├── trade_action.py           # TradeAction dataclass
│   └── position.py               # Position dataclass
│
├── examples/                     # Example notebooks
│   ├── buy_on_date.ipynb
│   ├── sma_cross.ipynb
│   └── BTCUSDT.csv               # Example OHLCV data
│
├── requirements.txt              # Runtime dependencies
├── environment.yaml              # Conda environment file
└── README.md                     # Project overview
```

## How It Works

1. The Backtester is initialized with:
    - Historical OHLCV Pandas DataFrame
    - A strategy class implementing the Strategy interface
    - An optional starting equity value

2. The backtest runs one time interval at a time:
    - Strategy's on_candle method is called on every candle with full historical data up to the current interval and a list of all open positions
    - Strategy's on_candle method returns a list of TradeActions to be executed
    - Fills occur at the next bar's open
    - TradeActions for exiting positions are executed first, followed by entering new positions
    - Capital availability is enforced for every trade.
    - An error is raised if a trade cannot be filled due to insufficient capital
    - An error is raised if liability exceeds the available buying power

3. Positions can be long or short:
    - An enter action with a positive quantity opens a long
    - An enter action with a negative quantity opens a short
    - An exit action closes a specific open position by id
    - No need to specify direction — PnL is handled automatically via signed quantities

4. At the end of the backtest the framework calculates:
    - Position value and PnL at every interval
    - Total equity curve
    - Total portfolio PnL
    - Equity curve via cumulative PnL

5. Statistics:
    - Start and end dates
    - Duration
    - Starting, final, and peak equity
    - Total PnL (value and percentage, if applicable)
    - Buy and hold PnL (value and percentage), if applicable
    - Exposure time (number of intervals and percentage of time)
    - Max drawdown (value and percentage, if applicable)
    - Sharpe ratio (if applicable)
    - Number of trades, win rate, average win/loss, best/worst trade, expectancy, etc.
    - Max and average position duration

## Getting Started

Dependencies are listed in `/requirements.txt`. Uncomment the optional packages if you want to run the example notebooks.

```bash
pip install -r requirements.txt
jupyter notebook examples/buy_on_date.ipynb
```

A conda environment yaml file is also available. Optional dependencies are included. To create and activate the conda environment, run:

```bash
conda env create -f environment.yaml
conda activate bn_backtest
```

## Example Usage

```python
from backtester import Backtester
from your_strategy import MyStrategy
import pandas as pd

# Load your OHLCV data
# Backtester expects an index called "Date" and columns "Open", "High", "Low", "Close", "Volume"
data = pd.read_csv('data.csv', index_col='Date', parse_dates=True)

bt = Backtester(data=data, strategy=MyStrategy)
bt.run()

# View the resulting pnl DataFrame
print(bt.pnl_df[['total_pnl']])
```

## Jupyter Notebook Examples
- [Buy on date](examples/buy_on_date.ipynb)
- [SMA cross strategy](examples/sma_cross.ipynb)

## Output Example
pnl_df includes:
- total_pnl: total PnL per interval
- equity: portfolio equity per interval
- position_value: value of each open position per interval
- cash_balance: cash balance per interval

You can use it to:
- Plot equity curves
- Evaluate performance metrics

Use `.stats()` to print/get performance metrics

## Next Steps / Ideas
- Add limit order support (fill if price crosses candle bounds)
- Add slippage/commission model
- Add short position interest, leverage, margin requirements models
- Visualization of trade markers and equity curve

## Why This Project?
This is an intentionally minimalist backtester to:
- Show clean code and architecture, good practices and Python proficiency
- Provide a base for building a more advanced backtesting framework
- Provide a real-world example of quant dev skills