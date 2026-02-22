# Product Aggregator Microservice

A stateful backend service that owns a product catalogue and periodically synchronizes product offers from an external offers microservice.

## Features

- **Product CRUD API** - Create, read, update, and delete products
- **Offer Synchronization** - Background job periodically fetches offers from external service
- **Cached Offers API** - Read-only API serving locally stored offers
- **PostgreSQL Storage** - Async SQLAlchemy with Alembic migrations
- **Docker Support** - Full containerized setup with docker-compose
- **Deployed on Render** - Docker-based deployment with managed PostgreSQL

## Architecture

- Products are created via our API and registered with the external offers service
- Background scheduler syncs offers for all registered products (configurable cron schedule, can be disabled by not setting `SYNC_SCHEDULE`)
- Offers are stored locally and served from the database

## API Endpoints

### Products

- `POST /products` - Create a product (auto-registers with external service)
- `GET /products` - List all products
- `GET /products/{id}` - Get a single product
- `PUT /products/{id}` - Update a product
- `DELETE /products/{id}` - Delete a product and its offers

### Offers

- `GET /products/{id}/offers` - Get cached offers for a product

### Health

- `GET /health` - Database connectivity check (returns 503 if DB is down)

## Requirements

- Python 3.11+
- PostgreSQL 16+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker & docker-compose (optional)

## Environment Variables

Create a `.env` file in the project root according to `.env.example`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `postgresql+asyncpg://aggregator:aggregator@localhost:5432/aggregator` | Database connection string (auto-normalizes `postgres://` schemes) |
| `OFFERS_SERVICE_URL` | Yes | — | Base URL of the external offers microservice |
| `OFFERS_REFRESH_TOKEN` | Yes | — | Refresh token for offers service authentication |
| `SYNC_SCHEDULE` | No | `*/30 * * * * *` | 6-field cron expression. Omit or leave empty to disable |
| `LOG_LEVEL` | No | `INFO` | Logging level |

## Local Development

### 1. Install dependencies

```bash
uv sync
```

### 2. Start PostgreSQL

```bash
docker-compose up db -d
```

Or use your own PostgreSQL instance and update `DATABASE_URL`.

### 3. Run migrations

```bash
uv run alembic upgrade head
```

### 4. Start the application

```bash
uv run uvicorn app.main:app --reload
```

API available at: http://localhost:8000

Interactive docs: http://localhost:8000/docs

## Docker Deployment

### Build and run

```bash
docker-compose up --build
```

The application will:
1. Wait for PostgreSQL to be healthy
2. Run Alembic migrations automatically
3. Start the FastAPI server
4. Start the background offer sync scheduler (unless disabled)

### Environment variables for Docker

Set `OFFERS_SERVICE_URL` and `OFFERS_REFRESH_TOKEN` in your environment:

```bash
export OFFERS_SERVICE_URL=https://your-offers-service.com
export OFFERS_REFRESH_TOKEN=your-token
docker-compose up
```

Or create a `.env` file (already gitignored).

## Database Migrations

### Create a new migration

```bash
uv run alembic revision --autogenerate -m "description"
```

### Apply migrations

```bash
uv run alembic upgrade head
```

### Rollback

```bash
uv run alembic downgrade -1
```

## Background Sync

The scheduler runs a cron job (configurable via `SYNC_SCHEDULE`) that:

1. Fetches all products with registered `external_id`
2. Queries the external offers service for each product
3. Reconciles offers (upsert new/changed, remove stale)
4. Logs errors but continues processing other products

Default schedule: every 30 seconds (`*/30 * * * * *`)

## Testing

Tests use an in-memory SQLite database and mock the external offers service.

```bash
uv run pytest -v
```

Test coverage:
- **Product CRUD** - create, read, update, delete, 404 handling
- **Offers API** - cached offers retrieval, empty results, missing products
- **Sync logic** - offer insert, update, stale removal, full reconciliation

## Project Structure

```
aggregator/
├── app/
│   ├── db/
│   │   ├── database.py      # DB connection & session management
│   │   └── models.py        # SQLAlchemy models
│   ├── routers/
│   │   ├── products.py      # Product CRUD endpoints
│   │   └── offers.py        # Offers read-only endpoint
│   ├── services/
│   │   ├── offers_client.py # External API client
│   │   └── sync_service.py  # Offer reconciliation logic
│   ├── tasks/
│   │   └── scheduler.py     # APScheduler background job
│   ├── config.py            # Settings from environment
│   ├── schemas.py           # Pydantic models
│   └── main.py              # FastAPI app & lifespan
├── alembic/                 # Database migrations
├── tests/                   # Pytest tests
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```
