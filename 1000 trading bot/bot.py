"""Paper-only daily swing trading prototype. Educational; not investment advice."""
import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed

load_dotenv()
if os.getenv('ALPACA_PAPER', '').lower() != 'true':
    raise SystemExit('Safety lock: this prototype only runs with ALPACA_PAPER=true')
KEY, SECRET = os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY')
if not KEY or not SECRET:
    raise SystemExit('Add paper API keys to .env')
trading = TradingClient(KEY, SECRET, paper=True)
data = StockHistoricalDataClient(KEY, SECRET)
WATCHLIST = ['SPY', 'QQQ', 'IWM']  # Examples, not recommendations
MAX_POSITION = 200.0
MAX_POSITIONS = 3
MIN_CASH = 400.0
DAILY_LOSS_LIMIT = 20.0
STOP_PCT = .03
TARGET_PCT = .05

def bars(symbol):
    end = datetime.now(timezone.utc)
    req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Day,
                           start=end-timedelta(days=150), end=end, feed=DataFeed.IEX)
    frame = data.get_stock_bars(req).df
    if frame.empty:
        return None
    if isinstance(frame.index, pd.MultiIndex):
        frame = frame.xs(symbol, level='symbol')
    # Ignore the current, potentially incomplete trading session.
    today_ny = datetime.now(ZoneInfo('America/New_York')).date()
    frame = frame[frame.index.tz_convert('America/New_York').date < today_ny]
    return frame if len(frame) >= 55 else None

def signal(frame):
    close = frame['close']
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1]
    return float(close.iloc[-1]) > sma20 > sma50

def run():
    now = datetime.now(ZoneInfo('America/New_York'))
    clock = trading.get_clock()
    if not clock.is_open or now.hour < 10 or now.hour >= 15:
        print('Run only during regular market hours, 10am–3pm New York time')
        return
    account = trading.get_account()
    equity = float(account.equity)
    prior = float(account.last_equity)
    loss_cutoff_reached = equity - prior <= -DAILY_LOSS_LIMIT
    if loss_cutoff_reached:
        print('Daily loss cutoff reached; exits still checked, new entries disabled')
    positions = {p.symbol: p for p in trading.get_all_positions()}
    open_orders = trading.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN))
    pending = {o.symbol for o in open_orders}
    cash = float(account.cash)
    # Exits first; no new entries for a symbol being exited.
    for symbol, p in positions.items():
        if symbol not in WATCHLIST or symbol in pending:
            continue
        entry = float(p.avg_entry_price)
        current = float(p.current_price)
        history = bars(symbol)
        trend_broken = history is not None and not signal(history)
        if current <= entry*(1-STOP_PCT) or current >= entry*(1+TARGET_PCT) or trend_broken:
            print(f'PAPER SELL {symbol}: risk/target/trend rule')
            trading.submit_order(MarketOrderRequest(symbol=symbol, qty=abs(float(p.qty)),
                                                    side=OrderSide.SELL, time_in_force=TimeInForce.DAY))
            pending.add(symbol)
    if loss_cutoff_reached:
        return
    occupied = len(positions) + len([s for s in pending if s not in positions])
    for symbol in WATCHLIST:
        if occupied >= MAX_POSITIONS or cash-MIN_CASH < 10:
            break
        if symbol in positions or symbol in pending:
            continue
        history = bars(symbol)
        if history is None or not signal(history):
            continue
        budget = round(min(MAX_POSITION, cash-MIN_CASH), 2)
        if budget < 10:
            continue
        print(f'PAPER BUY {symbol}: ${budget}')
        trading.submit_order(MarketOrderRequest(symbol=symbol, notional=budget,
                                                side=OrderSide.BUY, time_in_force=TimeInForce.DAY))
        cash -= budget
        occupied += 1

if __name__ == '__main__':
    run()
