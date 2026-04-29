---
id: local-development
title: Local Development
sidebar_position: 2
---

# Local Development

This guide covers running the backend and frontend outside of Docker for active development, where hot-reload and direct debugger access are required.

## Prerequisites

In addition to the [standard prerequisites](/getting-started/prerequisites), local development requires:

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Backend runtime |
| Node.js | 20 LTS+ | Frontend build tooling |
| PostgreSQL | 16 | Database (or use Docker for the DB only) |

## Backend Setup

### 1. Create a Virtual Environment

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and configure it:

```bash
cp ../.env.example .env
```

Set `DATABASE_URL` to point to your local PostgreSQL instance:

```bash
DATABASE_URL=postgresql://cra_user:changeme@localhost:5432/cra_db
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start the Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. The interactive OpenAPI documentation is at `http://localhost:8000/docs`.

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure the API Base URL

The frontend expects the backend at `http://localhost:8000` by default. To override, set `VITE_API_BASE_URL` in `frontend/.env.local`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start the Development Server

```bash
npm run dev
```

The frontend is available at `http://localhost:5173` with hot module replacement enabled.

## Running Only the Database via Docker

If you prefer not to install PostgreSQL locally, you can run only the database service via Docker Compose while running the backend and frontend natively:

```bash
docker compose up -d db
```

Then configure the backend's `DATABASE_URL` to `postgresql://cra_user:changeme@localhost:5432/cra_db`.

## Type Checking

```bash
# Backend
cd backend && mypy app/

# Frontend
cd frontend && npx vue-tsc --noEmit
```

## Linting

```bash
# Backend
cd backend && ruff check app/

# Frontend
cd frontend && npm run lint
```
