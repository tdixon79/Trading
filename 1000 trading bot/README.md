# $1,000 Alpaca paper swing bot — browser dashboard

**Paper trading only.** This prototype is not backtested or approved for live trading. It does not run continuously unless you separately schedule it. The $1,000 is a *target*, not a deposit or a reset of your Alpaca account balance.

## Secure online deployment (Streamlit Community Cloud)

1. Open an Alpaca paper-trading account and generate **paper** API keys (never live keys). Set/reset the simulated cash balance to $1,000 in Alpaca if that feature is available.
2. Create a **private GitHub repository** and upload the project files, preserving `dashboard.py` at repository root. Do **not** upload `.env`, `.streamlit/secrets.toml`, real keys, or passwords. `.gitignore` excludes local secret files.
3. Go to https://share.streamlit.io/ and create an app from your repository. Set the main file to `dashboard.py`. Check the host's current private-app and access settings. If your app is publicly reachable, **a password form alone is not enterprise-grade access protection**; use an access-controlled hosting setup or a trusted identity-aware proxy before relying on it with financial credentials.
4. In the deployment's **Secrets** settings, paste the entries from `secrets.example.toml` after replacing placeholders. Choose a unique 16+ character password. Keep `ALPACA_PAPER = "true"`.
5. Deploy. Visit the resulting HTTPS URL from your phone or computer, unlock it, and verify that the account is labeled **PAPER**. Never share the password or API keys.
6. If credentials leak, revoke/rotate paper keys in Alpaca and change the dashboard password.

## Run locally first (recommended)

Install Python 3.11+, then from the project folder:

```bash
python -m pip install -r requirements.txt
```

Create `.env` using `.env.example` and add `DASHBOARD_PASSWORD` (16+ characters), paper API key and secret. Then:

```bash
streamlit run dashboard.py
```

## What it does

- Displays paper account equity, cash, positions, orders, and market status.
- After password authentication, lets you click **Run Paper Trading Bot** to execute one simulated trading cycle. This can submit paper orders.
- Applies max $200 per new position, 3 positions, $400 minimum reserve, $20 daily new-entry cutoff, and price/trend exit signals in `bot.py`.
- Does **not** guarantee that losses stop at $20 or that exit orders fill at stop prices. Exit signals are checked only on bot runs.
- Does **not** auto-schedule runs, host itself, or link to your Fidelity account.

## Important limitations

A password in Streamlit is only an application-layer gate; it has no account-level MFA, lockout, or identity management. Use platform-level private access, HTTPS, and strong secrets. A Streamlit app may sleep when idle. Do not treat it as a reliable always-on trading scheduler. Before unattended paper execution, add an independent scheduler, logging, alerting, tests, and failure recovery. Before live trading, obtain a separate security and trading-risk review.
