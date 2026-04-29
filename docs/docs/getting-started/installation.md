---
id: installation
title: Installation
sidebar_position: 2
---

# Installation

This guide covers deploying CRA Conformity Management using Docker Compose, which is the supported installation method for both development and production environments.

## 1. Clone the Repository

```bash
git clone https://github.com/amh1036/CRA-Compliance-Tool.git
cd CRA-Compliance-Tool
```

## 2. Configure Environment Variables

Copy the provided example environment file and edit it for your environment:

```bash
cp .env.example .env
```

Open `.env` and configure the following required variables:

| Variable | Description | Example |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL username | `cra_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password (use a strong random value) | `changeme` |
| `POSTGRES_DB` | Database name | `cra_db` |
| `SECRET_KEY` | JWT signing key (minimum 32 characters, random) | `openssl rand -hex 32` |
| `FIRST_ADMIN_EMAIL` | Email address of the initial administrator account | `admin@example.com` |
| `FIRST_ADMIN_PASSWORD` | Initial administrator password | `changeme` |

:::warning
Change `POSTGRES_PASSWORD`, `SECRET_KEY`, and `FIRST_ADMIN_PASSWORD` before starting the application. Never commit the `.env` file to version control.
:::

### Optional Variables

| Variable | Description | Default |
|---|---|---|
| `LDAP_ENABLED` | Enable LDAP authentication (`true`/`false`) | `false` |
| `LDAP_SERVER` | LDAP server URI | — |
| `LDAP_BIND_DN` | LDAP bind distinguished name | — |
| `LDAP_BIND_PASSWORD` | LDAP bind password | — |
| `LDAP_BASE_DN` | LDAP search base DN | — |
| `AI_PROVIDER` | AI provider for scope evaluation (`openai` / `anthropic`) | — |
| `AI_API_KEY` | API key for the AI provider | — |

## 3. Start the Application

```bash
docker compose up -d
```

Docker Compose will pull the required images, build the application containers, and start all services. On first run, the database schema is automatically created via Alembic migrations.

Verify all containers are running:

```bash
docker compose ps
```

Expected output shows `backend`, `frontend`, and `db` services with status `running`.

## 4. Verify the Installation

| Service | URL |
|---|---|
| Frontend application | `http://localhost:5173` |
| Backend API | `http://localhost:8000` |
| API documentation (OpenAPI) | `http://localhost:8000/docs` |

## 5. Stopping and Restarting

```bash
# Stop all services (preserves data)
docker compose down

# Stop and remove all data (destructive — use with caution)
docker compose down -v
```

## Production Considerations

For production deployment:

1. Place the application behind a TLS-terminating reverse proxy
2. Restrict database port (5432) to the internal Docker network only
3. Configure regular PostgreSQL backups
4. Set `CORS_ORIGINS` to your specific frontend domain rather than a wildcard
5. Rotate `SECRET_KEY` periodically and invalidate all active sessions when doing so
