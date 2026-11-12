"""Read-only by default, paper-only Alpaca Streamlit dashboard."""
import os
import hmac
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title='Swing Bot | Paper Trading', page_icon='📈', layout='wide')
# Require a password before requesting any brokerage account data.
# For a public deployment, also use a platform-level access restriction.
def setting(name):
    try:
        return str(st.secrets[name])
    except (KeyError, FileNotFoundError):
        return os.getenv(name, '')

password = setting('DASHBOARD_PASSWORD')
if not password or len(password) < 16:
    st.error('Dashboard locked: configure a strong DASHBOARD_PASSWORD (16+ characters).')
    st.stop()
if not st.session_state.get('authenticated', False):
    with st.form('login'):
        entered = st.text_input('Dashboard password', type='password')
        submitted = st.form_submit_button('Unlock dashboard')
    if submitted and hmac.compare_digest(entered, password):
        st.session_state['authenticated'] = True
        st.rerun()
    if submitted:
        st.error('Incorrect password.')
    st.stop()
if st.sidebar.button('Lock dashboard'):
    st.session_state['authenticated'] = False
    st.rerun()

# SDK reads these environment variables; credentials remain server-side.
for name in ('ALPACA_PAPER', 'ALPACA_API_KEY', 'ALPACA_SECRET_KEY'):
    value = setting(name)
    if value:
        os.environ[name] = value

st.title('📈 Swing Bot')
st.caption('Alpaca PAPER account • $1,000 starting target • No live trading')

st.sidebar.header('Trading controls')
st.sidebar.info('Paper trading only. Trades are submitted only when you explicitly click Run Paper Bot, or when you separately schedule bot.py.')
st.sidebar.metric('Target starting balance', '$1,000')
st.sidebar.write('Maximum position: **$200**')
st.sidebar.write('Maximum positions: **3**')
st.sidebar.write('Cash reserve: **$400**')
st.sidebar.write('Daily new-entry cutoff: **−$20**')
st.sidebar.write('Stop / target signals: **−3% / +5%**')

if os.getenv('ALPACA_PAPER', '').lower() != 'true':
    st.error('Safety lock: set ALPACA_PAPER=true in .env. Live accounts are unsupported.')
    st.stop()
key, secret = os.getenv('ALPACA_API_KEY'), os.getenv('ALPACA_SECRET_KEY')
if not key or not secret:
    st.warning('Add your Alpaca PAPER API keys to the local .env file to display your account.')
    st.code('ALPACA_PAPER=true\nALPACA_API_KEY=your_paper_key\nALPACA_SECRET_KEY=your_paper_secret', language='ini')
    st.stop()

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus
client = TradingClient(key, secret, paper=True)
try:
    account = client.get_account()
    positions = client.get_all_positions()
    orders = client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, limit=30))
    clock = client.get_clock()
except Exception as exc:
    st.error(f'Unable to retrieve Alpaca paper account: {exc}')
    st.stop()

st.subheader('Account overview')
a, b, c, d = st.columns(4)
equity = float(account.equity)
last_equity = float(account.last_equity)
a.metric('Paper account equity', f'${equity:,.2f}', f'${equity-last_equity:+,.2f} since prior close')
b.metric('Available cash', f'${float(account.cash):,.2f}')
c.metric('Open positions', f'{len(positions)} / 3')
d.metric('Market', 'Open' if clock.is_open else 'Closed')
if abs(equity-1000) > 0.01:
    st.info('Your Alpaca paper account currently has a different balance from the $1,000 target. Adjust the paper account balance in Alpaca if supported; this dashboard does not change it.')
if equity-last_equity <= -20:
    st.warning('Daily loss threshold reached: the bot should not open new positions on its next run.')

st.subheader('Open positions')
if positions:
    rows = []
    for p in positions:
        rows.append({'Symbol':p.symbol, 'Shares':float(p.qty), 'Entry price':float(p.avg_entry_price), 'Current price':float(p.current_price), 'Market value':float(p.market_value), 'Unrealized P/L':float(p.unrealized_pl)})
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
else:
    st.info('No open paper positions.')

st.subheader('Recent orders')
if orders:
    rows = [{'Submitted (UTC)':str(o.submitted_at or ''), 'Symbol':o.symbol, 'Side':str(o.side).split('.')[-1], 'Status':str(o.status).split('.')[-1], 'Qty':str(o.qty or ''), 'Notional':str(o.notional or ''), 'Filled price':str(o.filled_avg_price or '')} for o in orders]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
else:
    st.info('No recent paper orders.')

st.subheader('Run bot manually')
st.caption('The bot checks signals and may submit PAPER orders. It only runs during eligible market hours. Clicking does not enable background scheduling.')
confirm = st.checkbox('I understand this may place simulated orders in my Alpaca PAPER account.')
if st.button('Run Paper Trading Bot', type='primary', disabled=not confirm):
    try:
        from bot import run
        with st.spinner('Checking paper-trading signals…'):
            run()
        st.success('Bot run completed. Refresh to see updated paper orders and positions.')
    except Exception as exc:
        st.error(f'Bot run failed: {exc}')
if st.button('Refresh dashboard'):
    st.rerun()
st.divider()
st.caption('Paper simulation only. Stop-loss signals are checked only when bot.py runs, not continuously. Loss limits are not guarantees. Never paste API secrets into chat.')
