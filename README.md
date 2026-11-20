# G.SMART MONEY FX ULTRA PRO
Experimental telegram market monitor. Not execution bot, not verified signal system.

## Features
- London/New York session approximate filter (UTC, DST not reliably handled)
- Higher timeframe trend confirmation
- Sweep, BOS, FVG, OB heuristic candidates
- Confluence scoring and alert cooldown
- 7 symbols; scan M15 every 5 minutes

**News filter:** This version does NOT connect to an economic calendar. It explicitly reports unavailable; manually check high-impact events before decisions.

## Install
Create Telegram bot with @BotFather. Set GitHub Codespaces secrets:
`TELEGRAM_BOT_TOKEN`, `TWELVE_DATA_API_KEY`.
Run in Codespaces:
```
pip install -r requirements.txt
python bot.py
```
Commands `/start`, `/analyze XAUUSD M15`, `/market`, `/pairs`, `/monitor`, `/stopmonitor`.
