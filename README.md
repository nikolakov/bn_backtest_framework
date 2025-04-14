# BN Backtest Framework

A simple yet powerful Python backtesting framework designed to simulate and evaluate trading strategies using OHLCV data. Built for clarity and extensibility

## Features
- ✅ Event-driven backtesting loop
- ✅ Strategy interface via `on_candle()` callback
- ✅ Long and short position support
- ✅ Support for multiple positions per symbol
- ✅ Set position size either as quantity of assets or a fixed value
- ✅ Realistic fills at next interval's open
- ✅ Vectorized PnL calculation using Pandas
- ✅ Automatically closes all positions at the end
- ✅ Modular design: strategy, position, trade action, and engine separated

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
└── README.md                     # Project overview
```

## How It Works

1. The Backtester is initialized with:
    - Historical OHLCV Pandas DataFrame
    - A strategy class implementing the Strategy interface

2. The backtest runs one time interval at a time:
    - Strategy's on_candle method is called on every candle with full historical data up to the current interval and a list of all open positions
    - Strategy's on_candle method returns a list of TradeActions to be executed
    - Fills occur at the next bar's open

3. Positions can be long or short:
    - An enter action with a positive quantity opens a long
    - An enter action with a negative quantity opens a short
    - An exit action closes a specific open position
    - No need to specify direction — PnL is handled automatically via signed quantities

4. At the end of the backtest the framework calculates:
    - Position-level exposure, value, and PnL for every interval
    - Total portfolio PnL per interval
    - Equity curve via cumulative PnL
    - Performance metrics
        - Max Drawdown
        - Sharpe ratio
        - Win rate
        - Average win/loss

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
- One PnL column per position

You can use it to:
- Plot equity curves
- Evaluate performance metrics

## Next Steps / Ideas
- Add portfolio value and exposure
- Add market orders and limit orders
- Add more performance metrics
- Add slippage/commission model
- Add short position interest model
- Visualization of trade markers and equity curve

## Why This Project?
- This is an intentionally minimalist backtester to:
- Show clean code and architecture in interviews
- Be easy to extend for more complex modeling
- Provide a real-world example of quant dev skills