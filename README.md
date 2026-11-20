# G.SMART MONEY FX Telegram Bot — PRO MAX ✨

Educational market-monitoring bot. It does **not** execute trades. Candidate analysis is heuristic and must not be treated as verified trading signals.

## 1. Create Telegram bot
- Open Telegram and message **@BotFather**
- Run `/newbot`, follow prompts, and copy the token.
- Keep the token private.

## 2. API key
Get a Twelve Data API key and use it as a GitHub Codespaces secret.

## 3. GitHub Codespaces setup
1. Upload this folder's files to a GitHub repository.
2. In repository Settings → Secrets and variables → Codespaces, add:
   - `TELEGRAM_BOT_TOKEN`
   - `TWELVE_DATA_API_KEY`
3. Open Code → Codespaces → create codespace.
4. In terminal:
   ```bash
   pip install -r requirements.txt
   python bot.py
   ```
5. Open the bot on Telegram and type `/start`.

## Commands
- `/start` or `/help`
- `/pairs`
- `/market`
- `/analyze XAUUSD M15` (any supported pair/timeframe)
- `/monitor`
- `/stopmonitor`

## Monitoring
Checks every five minutes, with a per-symbol alert cooldown of 30 minutes. Monitor is a simple screening heuristic; it does not implement rigorous SMC, backtesting, execution, or risk sizing. Market API limits may constrain monitoring.

## Supported symbols/timeframes
XAUUSD, EURUSD, GBPUSD, USDJPY, BTCUSD, AUDUSD, GBPJPY.
M5, M15, M30, H1, H4, D1 (monitor currently scans M15 only).
