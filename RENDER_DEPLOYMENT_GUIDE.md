# CRA Compliance Tool — Render Deployment Guide

This guide covers deploying the CRA Compliance Tool to Render.com (free tier) with a PostgreSQL database.

## Architecture Overview

- **Frontend**: Vue 3 static site (Render Static Site)
- **Backend**: FastAPI application (Render Web Service)
- **Database**: PostgreSQL (Render Managed PostgreSQL)

## Prerequisites

- Render.com account (free tier available)
- GitHub account with the repository
- Local terminal with Python 3.12+
- `.venv` virtual environment activated locally

---

## Step 1: Create PostgreSQL Database on Render

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. Click **New +** → **PostgreSQL**
3. Fill in the form:
   - **Name**: `cra-compliance-db` (or your choice)
   - **Database**: `cra_compliance`
   - **User**: `admin` (avoid `postgres`)
   - **Region**: Choose closest to your location (e.g., Ohio)
   - **Version**: PostgreSQL 15 or higher
   - **Plan**: Free tier available

4. Click **Create Database**
5. Wait for the database to initialize (2-3 minutes)
6. Copy the **External Database URL** from the database info page:
   ```
   postgresql+psycopg://admin:PASSWORD@dpg-XXXX.REGION-postgres.render.com/cra_compliance
   ```
   Save this — you'll need it later.

---

## Step 2: Deploy Backend Service

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository (authorize if needed)
4. Select the repository containing the code
5. Fill in the form:
   - **Name**: `cra-compliance-tool` (or your choice)
   - **Environment**: `Docker`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Plan**: Free tier available

6. Click **Create Web Service**

### Set Backend Environment Variables

Once the service is created, go to **Environment** tab and add:

| Key | Value |
|---|---|
| `BACKEND_SECRET_KEY` | Generate using: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `BACKEND_ENVIRONMENT` | `production` |
| `BACKEND_DEBUG` | `false` |
| `BACKEND_LOG_LEVEL` | `INFO` |
| `POSTGRES_DB` | `cra_compliance` |
| `POSTGRES_USER` | `admin` |
| `POSTGRES_PASSWORD` | From your database setup |
| `BACKEND_DATABASE_URL` | The External Database URL from Step 1 |
| `BACKEND_CORS_ORIGINS` | Leave empty for now, update after frontend deployment |

Save and redeploy.

### Get Backend URL

Once deployed, copy the backend service URL (e.g., `https://cra-compliance-tool.onrender.com`). You'll need this for the frontend.

---

## Step 3: Run Database Migrations

Migrations must be run locally against the Render database. This creates all tables.

1. Activate your local virtual environment:
   ```bash
   cd backend
   source ../.venv/bin/activate
   ```

2. Run migrations:
   ```bash
   BACKEND_DATABASE_URL="postgresql+psycopg://admin:PASSWORD@dpg-XXXX.REGION-postgres.render.com/cra_compliance" python -m alembic upgrade head
   ```

   This runs all 17 migration files and creates the database schema.

3. Seed initial data (creates admin user and permissions):
   ```bash
   BACKEND_DATABASE_URL="postgresql+psycopg://admin:PASSWORD@dpg-XXXX.REGION-postgres.render.com/cra_compliance" python -c "
   from sqlalchemy import create_engine
   from sqlalchemy.orm import sessionmaker
   from app.core.seed import seed_initial_data

   engine = create_engine('postgresql+psycopg://admin:PASSWORD@dpg-XXXX.REGION-postgres.render.com/cra_compliance')
   Session = sessionmaker(bind=engine)
   db = Session()
   seed_initial_data(db)
   print('Seeding complete. Admin user: admin@example.com / admin1234')
   "
   ```

   **Replace the database URL with your actual connection string.**

---

## Step 4: Deploy Frontend Service

1. Go to [render.com/dashboard](https://render.com/dashboard)
2. Click **New +** → **Static Site**
3. Connect your GitHub repository
4. Fill in the form:
   - **Name**: `cra-compliance-tool-frontend` (or your choice)
   - **Branch**: `main`
   - **Build Command**: `cd frontend && npm install --legacy-peer-deps && npx vite build`
   - **Publish Directory**: `frontend/dist`
   - **Plan**: Free tier available

5. Click **Create Static Site**

### Get Frontend URL

Once deployed, copy the frontend URL (e.g., `https://cra-compliance-tool-frontend.onrender.com`).

---

## Step 5: Configure CORS on Backend

Now that you have both URLs, update the backend CORS settings:

1. Go to the backend service in Render
2. Go to **Environment** tab
3. Update `BACKEND_CORS_ORIGINS`:
   ```
   https://cra-compliance-tool-frontend.onrender.com,https://cra-compliance-tool.onrender.com
   ```
4. Save and redeploy

---

## Step 6: Configure Frontend API URL

1. Go to the frontend service in Render
2. Go to **Environment** tab
3. Add environment variable:
   ```
   VITE_API_BASE_URL=https://cra-compliance-tool.onrender.com/api/v1
   ```
4. Save and trigger a redeploy

---

## Step 7: Test the Deployment

1. Open your frontend URL in a browser: `https://cra-compliance-tool-frontend.onrender.com`
2. Log in with:
   - **Email**: `admin@example.com`
   - **Password**: `admin1234`
3. If login succeeds, the deployment is working end-to-end

---

## Troubleshooting

### Backend showing "Starting application" but not responding

- Check the backend logs in Render → **Logs** tab
- Common issues:
  - Database URL is wrong
  - Secret key is too short (needs 32+ characters)
  - Migrations haven't been run yet

### "relation 'users' does not exist" error on login

- Run migrations (Step 3) and seed the database
- Verify the migration command completes without errors

### CORS error in frontend console

- Update `BACKEND_CORS_ORIGINS` to include your frontend URL
- Redeploy the backend service
- Clear browser cache and retry

### Frontend showing 404 for API calls

- Check `VITE_API_BASE_URL` in frontend environment variables
- Verify backend service is running and responding to health checks
- Test with: `curl https://cra-compliance-tool.onrender.com/healthz`

### Database connection timeout

- Verify the database is running in Render
- Check the connection string has the correct hostname and password
- Ensure database is in the same region as backend service

---

## Database Backups

Render's free PostgreSQL tier does not include automatic backups. To protect your data:

1. Set up a manual backup schedule by exporting the database locally:
   ```bash
   PGPASSWORD="PASSWORD" pg_dump -h dpg-XXXX.REGION-postgres.render.com -U admin cra_compliance > backup.sql
   ```

2. Store the `backup.sql` file securely (e.g., git-ignored, cloud storage)

---

## Cost Summary

| Service | Free Tier | Cost |
|---|---|---|
| PostgreSQL | 256 MB storage | $7/month over limit |
| Backend Web Service | 750 hrs/month | Free (auto-sleeps) |
| Frontend Static Site | Unlimited | Free |
| **Total** | **Fully free** | Only if storage exceeds 256 MB |

---

## Next Steps

1. Create additional user accounts in the tool
2. Test all features (products, release gates, risk assessments)
3. Monitor logs for errors: Render → Service → **Logs**
4. Set up email notifications for crashes (Render → **Notifications**)

---

## Quick Reference — Connection Strings

**Backend Database URL:**
```
postgresql+psycopg://admin:PASSWORD@dpg-XXXX.REGION-postgres.render.com/cra_compliance
```

**Frontend API Base URL:**
```
https://cra-compliance-tool.onrender.com/api/v1
```

**Backend CORS Origins:**
```
https://cra-compliance-tool-frontend.onrender.com,https://cra-compliance-tool.onrender.com
```

Replace `PASSWORD` and `dpg-XXXX` with your actual database credentials from Render.
