# Backend gateway (secure scaffold)

This is a real FastAPI integration scaffold for Google token validation and MT5 read-only data. **It is not a production-ready automated trading engine.**

1. Run on Windows with MetaTrader 5 desktop installed, signed into a DEMO account.
2. `python -m venv .venv` then `.venv\\Scripts\\activate` and `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`. Configure `GOOGLE_CLIENT_ID`, **ALLOWED_EMAILS**, `MT5_ENABLED=true`, and terminal/account settings. Keep `TRADING_ENABLED=false`.
4. Run `uvicorn main:app --host 127.0.0.1 --port 8000` in the `backend` folder.
5. Google frontend obtains an ID token using Google Identity Services; pass `Authorization: Bearer <ID_TOKEN>` for `/api/account`, `/api/candles`, `/api/trades`, `/api/orders/preview`, `/api/kill-switch`.
6. `/api/health` is public and does not reveal account data.

**Safety:** No live order routing is implemented: `/api/orders` always fails closed, even with flags enabled. `kill-switch` blocks new orders but does not close existing positions. Add robust broker stop-distance checks, cumulative daily loss including realized/floating P&L, exposure limits, idempotency, order audit trail, retry/reconciliation, per-user account authorization, persistence and comprehensive demo tests before enabling live execution. Never expose the bridge directly to the internet; use HTTPS and an authenticated reverse proxy. No secrets in Git.

AI signals must be advisory until a separately tested inference service, versioned models, confidence calibration, drift monitoring and server-side risk gates exist.
