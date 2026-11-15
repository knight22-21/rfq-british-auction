# RFQ British Auction

A freight RFQ platform with configurable British auction bidding. Suppliers
continuously underbid each other, qualifying activity near the deadline extends the
auction, and a forced close time puts a hard ceiling on extensions.

The repository contains a FastAPI backend, a React + Vite frontend, an HLD, and a
schema guide.

## Features

- Create RFQs with bid start, bid close, forced close, pickup date, and auction rules.
- Three extension triggers: any bid in the window, any rank change, or an L1 change.
- Extensions are clamped to the forced close time and can never breach it.
- Transactional bids: quote insert, rank rewrite, extension, and audit log commit
  together.
- Deterministic ranking (`L1`, `L2`, …) by total landed cost with early-bid tie-break.
- Listing page with status, lowest bid, live countdown, and trigger configuration.
- Bidding room with server-clock countdown, leaderboard, quote form, and activity log.
- Buyer/Supplier role switch for demonstration purposes (not authentication).

## Stack

| Layer | Choice |
| :--- | :--- |
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database | SQLite by default (WAL); PostgreSQL-compatible schema |
| Frontend | React 19, Vite, TypeScript, Tailwind CSS |
| Tests | pytest + FastAPI TestClient |

## Project layout

```
GoComet/
├── backend/
│   ├── app/
│   │   ├── main.py            # app factory, lifespan, CORS, error handlers
│   │   ├── routes.py          # REST endpoints
│   │   ├── schemas.py         # request/response models + envelope
│   │   ├── models.py          # SQLAlchemy tables and constraints
│   │   ├── db.py              # engine, SQLite pragmas, BEGIN IMMEDIATE
│   │   ├── presenters.py      # read-model mapping
│   │   ├── seed.py            # idempotent demo auctions
│   │   └── services/          # rank/extension engine, RFQ and bid services
│   ├── tests/                 # unit, API, and concurrency tests
│   ├── requirements.txt
│   └── pytest.ini
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── components/        # list, create form, bidding room, countdown, tables
│   ├── package.json
│   └── vite.config.ts
├── HLD.md
├── SCHEMA.md
└── README.md
```

## Quick start

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8004
```

On macOS/Linux, use `.venv/bin/python` instead of `.venv\Scripts\python.exe`.
Port 8004 is used because 8000 is commonly occupied; the Vite proxy and all commands
below point at 8004.

- API: <http://127.0.0.1:8004>
- OpenAPI docs: <http://127.0.0.1:8004/docs>
- Health: <http://127.0.0.1:8004/api/health>

The first start creates the SQLite database and seeds four sample auctions.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite proxies `/api` to the backend on port 8004.

### 3. Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

The suite covers ranking and tie-breaking, all three trigger types, the forced-close
invariant, lifecycle guards, and parallel bids in the final window.

## Configuration

The backend reads standard environment variables. `backend/.env.example` documents
the available keys; export them in your shell before starting the API.

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///<backend>/auction.db` | SQLAlchemy connection string. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated allowed origins. |
| `SEED_DEMO_DATA` | `1` | Seed sample auctions when the database is empty. |
| `SQL_ECHO` | `0` | Log SQL statements. |

To reset the demo data, stop the backend and delete `backend/auction.db`,
`backend/auction.db-wal`, and `backend/auction.db-shm`.

## Auction rules

1. Creation requires `forcedClose > bidClose > bidStart`.
2. A bid is accepted only while the auction is `ACTIVE`.
3. Total cost is `freight + origin + destination`, rounded to two decimals.
4. Rank order is total ascending, then submission time ascending, then id. Each
   submission is ranked independently; a supplier who bids several times occupies
   one position per bid, and their best bid is their effective position.
5. If British auction rules are enabled and the bid lands inside
   `[close - X, close]`:
   - `ANY_BID` always triggers.
   - `ANY_RANK_CHANGE` triggers when an existing supplier’s rank changes.
   - `L1_RANK_CHANGE` triggers when the lowest bidder changes.
6. The new close time is `min(close + Y, forcedClose)`.
7. Once `close == forcedClose`, a triggered bid logs `EXTENSION_BLOCKED` and the
   close time stays unchanged.
8. Every accepted bid, rank change, extension, blocked extension, and status change
   is written to `activity_logs`.

## API overview

All responses use `{ success, data, serverTime }` or
`{ success, error: { code, message }, serverTime }`.

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Liveness probe. |
| `POST` | `/api/rfqs` | Create an RFQ. |
| `GET` | `/api/rfqs` | List auctions with status and lowest bid. |
| `GET` | `/api/rfqs/{id}` | Auction detail, ranked quotes, activity. |
| `GET` | `/api/rfqs/{id}/activity` | Activity timeline. |
| `POST` | `/api/rfqs/{id}/quotes` | Submit a quote and evaluate extensions. |

Example quote request:

```json
{
  "carrierName": "Maersk",
  "freightCharges": "2150.00",
  "originCharges": "340.00",
  "destinationCharges": "410.00",
  "transitTimeDays": 31,
  "validityDate": "2026-12-15T23:59:59Z"
}
```

## Demo script

1. Open the listing. `RFQ-2026-002` is already live and has been extended twice.
2. Open it, switch the header role to **Supplier**, and submit a lower quote.
3. Watch the leaderboard reorder and the activity log append the extension reason.
4. Switch back to **Buyer**, create an RFQ with a two-minute forced close and a
   five-minute extension, then bid from the supplier role to see the clamp.
5. Refresh the page: roles, carrier name, and auction state persist; the countdown
   stays aligned with server time.

## Documentation

- [HLD.md](HLD.md) — architecture, bid sequence, concurrency, API, trade-offs.
- [SCHEMA.md](SCHEMA.md) — tables, constraints, indexes, invariants.
