# CRA Compliance Tool

Self-hosted CRA compliance management foundation for manufacturers of products with digital elements.

## Stack

- Frontend: Vue 3 + TypeScript + Pinia + Vue Router + Axios
- Backend: FastAPI + SQLAlchemy 2.x + Pydantic v2 + Alembic
- Database: PostgreSQL

## Included in this scaffold

- FastAPI application startup with structured logging
- `/api/v1` API prefix
- PostgreSQL integration with SQLAlchemy 2.x
- UUID primary keys and UTC timestamps
- Alembic migration setup
- Role and permission foundation
- JWT authentication foundation
- Immutable audit event model and audit helper
- Product and ProductRelease domain foundation
- Release gate readiness fields
- Vue 3 frontend with router, Pinia, Axios client, layout shell, error handling
- Docker Compose local development environment

## Project structure

```text
cra-compliance-tool/
  backend/
  frontend/
  docs/
  docker-compose.yml
  .env.example
  README.md