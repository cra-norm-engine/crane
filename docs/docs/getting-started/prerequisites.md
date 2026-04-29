---
id: prerequisites
title: Prerequisites
sidebar_position: 1
---

# Prerequisites

Before installing CRA Conformity Management, ensure the following dependencies are available on the host system.

## Runtime Dependencies

| Dependency | Minimum Version | Purpose |
|---|---|---|
| [Docker](https://docs.docker.com/engine/install/) | 24.0 | Container runtime for all services |
| [Docker Compose](https://docs.docker.com/compose/install/) | 2.20 | Multi-container orchestration |

Docker Compose v2 is bundled with Docker Desktop on macOS and Windows. On Linux, install it as a plugin following the official Docker documentation.

## Supported Host Operating Systems

- **Linux** — Ubuntu 22.04 LTS or later (recommended for production)
- **macOS** — 13 (Ventura) or later via Docker Desktop
- **Windows** — Windows 11 with Docker Desktop and WSL 2 backend

## Network Requirements

| Port | Service | Required |
|---|---|---|
| 5173 | Frontend (Vue 3 dev server) | Local development only |
| 8000 | Backend API (FastAPI) | Local development only |
| 5432 | PostgreSQL | Internal (not exposed externally) |

In production, a reverse proxy (Nginx, Caddy, or Cloudflare Tunnel) should terminate TLS and forward traffic to the application. Direct exposure of ports 5173 or 8000 to the public internet is not recommended.

## Optional: LDAP Directory

If your organisation uses LDAP-based user authentication, an accessible LDAP or Active Directory server is required. See [User Management](/user-guide/user-management) for configuration details.

## Hardware Recommendations

| Environment | CPU | RAM | Storage |
|---|---|---|---|
| Development | 2 cores | 4 GB | 10 GB |
| Small team (< 20 users) | 2 cores | 8 GB | 50 GB |
| Larger deployment | 4 cores | 16 GB | 100 GB SSD |

PostgreSQL I/O is the primary bottleneck; SSD-backed storage is strongly recommended for production deployments.
