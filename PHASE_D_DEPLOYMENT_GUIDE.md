# Phase D Deployment Guide

Complete instructions for deploying Phase D (Evidence Versioning & Change Log) to production.

## Pre-Deployment Checklist

### Code Review
- [x] All Phase D code syntax validated (Python AST parsing)
- [x] TypeScript compilation passes (0 errors in Phase D code)
- [x] 4 Alembic migrations created and verified
- [x] Backend models and services implemented
- [x] Frontend components implemented and tested
- [x] API endpoint specifications documented
- [x] No breaking changes to existing code
- [x] All new operations emit audit events

### Requirements
- PostgreSQL 14+ running and accessible
- Python 3.11+ with venv
- Node.js 18+ with npm
- Git with commit access
- 30-60 minutes for full deployment

---

## Step 1: Database Preparation

### 1.1 Verify Database Connectivity

```bash
# Test connection to PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/cra_compliance -c "SELECT version();"

# Should output PostgreSQL version info
```

**If connection fails:**
- Verify PostgreSQL is running: `systemctl status postgresql`
- Check credentials in `.env`
- Verify firewall allows port 5432

### 1.2 Backup Existing Database

```bash
# Create timestamped backup
pg_dump postgresql://postgres:postgres@localhost:5432/cra_compliance \
  > cra_compliance_backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup created
ls -lh cra_compliance_backup_*.sql
```

**Alternative: Docker backup**
```bash
docker exec cra-compliance-postgres pg_dump \
  -U postgres cra_compliance \
  > cra_compliance_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 1.3 Verify Current Migration State

```bash
cd backend

# Show current migration version
alembic current

# Should show: 20260510_0028_sbom_analysis_fields (or latest pre-Phase D migration)
```

---

## Step 2: Apply Database Migrations

### 2.1 Run Alembic Upgrade

```bash
cd backend

# Display migrations to be applied
alembic heads

# Should show 4 new migrations:
#  20260517_0029_release_gate_prerequisites
#  20260517_0030_assessment_methodology
#  20260517_0031_certification_evidence
#  20260517_0032_gate_snapshot

# Apply all pending migrations
alembic upgrade head

# Output should show:
# INFO [alembic.runtime.migration] Running upgrade 20260510_0028 -> 20260517_0029
# ...
# INFO [alembic.runtime.migration] Running upgrade 20260517_0031 -> 20260517_0032
```

### 2.2 Verify Migration Success

```bash
# Check current migration
alembic current
# Should now show: 20260517_0032_gate_snapshot

# Verify new tables exist
psql postgresql://postgres:postgres@localhost:5432/cra_compliance << EOF
SELECT tablename FROM pg_tables 
WHERE schemaname='public' 
AND tablename IN (
  'release_gate_item_prerequisites',
  'certification_record_artifact_links'
);
EOF

# Should output:
#  release_gate_item_prerequisites
#  certification_record_artifact_links
```

### 2.3 Rollback Plan (if needed)

If migration fails:
```bash
# Rollback to previous state
alembic downgrade -1

# Or rollback multiple steps
alembic downgrade 20260510_0028

# Then investigate the error and re-run with fixes
```

---

## Step 3: Backend Deployment

### 3.1 Install/Update Dependencies

```bash
cd backend

# Create or update virtual environment
python3 -m venv .venv --upgrade-deps

# Activate venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Verify installations
pip list | grep -E "fastapi|sqlalchemy|pydantic"
```

### 3.2 Environment Configuration

```bash
# Verify .env file has all required variables
cd /path/to/project

# Check critical settings
grep -E "BACKEND_SECRET_KEY|BACKEND_DATABASE_URL|BACKEND_PORT" .env

# Should output:
# BACKEND_SECRET_KEY=<long random string>
# BACKEND_DATABASE_URL=postgresql+psycopg://...
# BACKEND_PORT=8000
```

### 3.3 Start Backend Service

**Development:**
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production (with gunicorn):**
```bash
cd backend

# Install gunicorn if not present
pip install gunicorn

# Start with 4 workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

**Docker:**
```bash
# If using Docker, rebuild image
docker-compose build backend

# Start services
docker-compose up -d

# Verify backend health
curl http://localhost:8000/api/v1/health  # If endpoint exists
```

### 3.4 Verify Backend Startup

```bash
# Wait 10 seconds for startup
sleep 10

# Check API availability
curl http://localhost:8000/api/v1/  # Should return API documentation or status

# Check specific endpoint
curl http://localhost:8000/api/v1/changes/assessment-templates/stride

# Should return:
# {"methodology":"stride","questions":[...]}
```

---

## Step 4: Frontend Deployment

### 4.1 Install Dependencies

```bash
cd frontend

# Clean install
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

# Verify no build errors
npm run type-check  # Should show 0 Phase D errors
```

### 4.2 Build for Production

```bash
cd frontend

# Create optimized production build
npm run build

# Verify build output
ls -lh dist/
# Should contain: index.html, assets/, vite.svg
```

### 4.3 Serve Frontend

**Development:**
```bash
cd frontend
npm run dev
# Opens at http://localhost:5173
```

**Production (static serving):**
```bash
# Use any static server, e.g., Python
cd frontend/dist
python3 -m http.server 5173

# Or with nginx
cp -r dist/* /var/www/html/cra-tool/
systemctl restart nginx
```

**Docker:**
```bash
# Frontend is built in docker-compose.yml
docker-compose up -d frontend
```

### 4.4 Verify Frontend Startup

```bash
# Open browser
curl http://localhost:5173

# Should return HTML page
# Open in browser: http://localhost:5173
# Should load CRA Compliance Tool interface
```

---

## Step 5: Integration Testing

### 5.1 Smoke Tests

```bash
# Test basic connectivity
curl -s http://localhost:8000/api/v1/changes/assessment-templates/stride | jq '.questions | length'
# Should output: 6

curl -s http://localhost:8000/api/v1/changes/assessment-templates/tara | jq '.questions | length'
# Should output: 4
```

### 5.2 Data Integrity Tests

```bash
# Check database schemas
psql postgresql://postgres:postgres@localhost:5432/cra_compliance << EOF

-- Verify new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name='substantial_modification_assessments' 
AND column_name IN ('methodology', 'template_answers');

-- Verify unique constraints
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name IN (
  'release_gate_item_prerequisites',
  'certification_record_artifact_links'
);

EOF
```

### 5.3 Feature Tests (Manual)

Use **PHASE_D_API_SPEC.md** for API testing
Use **PHASE_D_FRONTEND_TESTING.md** for UI testing

Key scenarios to test:
1. AssessmentWizard with STRIDE and security-type change
2. Certification evidence upload and download
3. Release gate prerequisites and blocking
4. Gate snapshot on approval

---

## Step 6: Production Deployment

### 6.1 Pre-Production Checklist

- [ ] Database backups created
- [ ] Migrations tested in staging environment
- [ ] API endpoints responding correctly
- [ ] Frontend loads without console errors
- [ ] Audit events are being logged
- [ ] Performance baseline established
- [ ] Team notified of deployment window
- [ ] Rollback procedure documented and tested

### 6.2 Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Stop running services (if applicable)
docker-compose stop backend frontend
# OR
systemctl stop cra-compliance-backend

# 3. Apply database migrations
cd backend && alembic upgrade head

# 4. Build frontend
cd frontend && npm run build

# 5. Start services
docker-compose up -d
# OR
systemctl start cra-compliance-backend cra-compliance-frontend

# 6. Verify health
sleep 10
curl http://your-domain:8000/api/v1/health
curl http://your-domain:5173
```

### 6.3 Post-Deployment Verification

```bash
# Check logs for errors
docker-compose logs -f backend | head -50

# Run health checks
curl -s http://localhost:8000/api/v1/changes/assessment-templates/stride | jq '.questions[0].id'
# Should output: "S1"

# Verify database migrations applied
alembic current  # Should show 20260517_0032

# Check audit log for events
psql -c "SELECT COUNT(*) FROM audit_log_events WHERE created_at > NOW() - INTERVAL '1 hour';"
# Should show recent events from startup

# Monitor metrics
docker stats cra-compliance-backend cra-compliance-frontend
```

---

## Step 7: Monitoring & Maintenance

### 7.1 Application Monitoring

**Backend:**
```bash
# Monitor logs
docker-compose logs -f backend

# Watch for errors:
# - "OperationalError": Database connection issue
# - "ValidationError": Bad input data
# - "NotFoundException": Missing resource
```

**Frontend:**
```bash
# Browser console (F12)
# Watch for:
# - Network errors (red in Network tab)
# - Type errors (red in Console)
# - Failed API calls

# Performance (DevTools → Network)
# Assessment wizard should load < 200ms
# Evidence upload should show progress
```

### 7.2 Database Maintenance

```bash
# Weekly: Check table sizes
psql << EOF
SELECT 
  tablename,
  pg_size_pretty(pg_total_relation_size(tablename::regclass)) 
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(tablename::regclass) DESC;
EOF

# Monthly: Vacuum and analyze
psql << EOF
VACUUM ANALYZE;
REINDEX DATABASE cra_compliance;
EOF
```

### 7.3 Audit Trail Verification

```bash
# Check recent audit events
psql << EOF
SELECT entity_type, action_type, COUNT(*) 
FROM audit_log_events 
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY entity_type, action_type
ORDER BY entity_type;
EOF

# Expected Phase D events:
# - certification_record, update (evidence_attached, evidence_removed)
# - release_gate, update (prerequisite_added, prerequisite_removed)
# - change, update (assessment_submitted)
```

---

## Troubleshooting

### Issue: Migration Fails with "Column already exists"

**Cause:** Migration was partially run

**Solution:**
```bash
# Check alembic_version table
psql -c "SELECT * FROM alembic_version;"

# If partial migration exists, manually fix or rollback:
alembic downgrade -1
alembic upgrade head
```

### Issue: Frontend Can't Connect to Backend API

**Cause:** CORS, firewall, or wrong API URL

**Solution:**
```bash
# Check VITE_API_BASE_URL in .env
grep VITE_API_BASE_URL .env

# Verify backend is accessible
curl http://localhost:8000/api/v1/

# Check browser console for exact error URL
# Ensure backend CORS_ORIGINS includes frontend URL
grep BACKEND_CORS_ORIGINS .env
```

### Issue: Assessment Wizard Shows "No Questions"

**Cause:** API call failed or wrong response format

**Solution:**
```bash
# Test endpoint directly
curl http://localhost:8000/api/v1/changes/assessment-templates/stride

# Should return: {"methodology":"stride","questions":[...]}

# Check browser Network tab for:
# - 200 status (not 404, 500)
# - Response has "questions" array with 6+ items
```

### Issue: Evidence Upload Fails

**Cause:** File too large, permission issue, or upload endpoint down

**Solution:**
```bash
# Test upload endpoint
curl -X POST http://localhost:8000/api/v1/certification-records/{id}/evidence/upload \
  -F "title=test" \
  -F "artifact_type=document" \
  -F "upload=@test.pdf"

# Check response for:
# - 200 status
# - artifact_links array in response

# Check backend logs for upload size limit errors
```

### Issue: Prerequisite "Blocking" Doesn't Work

**Cause:** Service validation not enforced or frontend not checking status

**Solution:**
```bash
# Check backend validation in release_gate_service
grep -A 5 "unmet_prerequisites" backend/app/services/release_gate_service.py

# Test endpoint
curl http://localhost:8000/api/v1/product-releases/{id}/gate

# Verify response includes:
# - prerequisites array on each item
# - unmet_prerequisites array with blocking logic
```

---

## Rollback Procedure

If critical issues arise after deployment:

### 7.1 Quick Rollback (Database)

```bash
cd backend

# Undo last 4 migrations
alembic downgrade -4

# Or back to specific version
alembic downgrade 20260510_0028

# Verify
alembic current
```

### 7.2 Code Rollback (Git)

```bash
# Revert to previous commit
git revert HEAD  # Creates new commit undoing changes
# OR
git reset --hard HEAD~1  # Destroys commit (dangerous)

# Rebuild and restart
npm run build
docker-compose down
docker-compose up -d
```

### 7.3 Full Restore from Backup

```bash
# Stop services
docker-compose down

# Restore database from backup
psql -d cra_compliance < cra_compliance_backup_20260517_120000.sql

# Restart services
docker-compose up -d
```

---

## Sign-Off

### Deployment Checklist

- [ ] Database backups completed
- [ ] Migrations applied successfully
- [ ] Backend service started and healthy
- [ ] Frontend build completed and deployed
- [ ] Smoke tests passed (API endpoints responding)
- [ ] Feature tests passed (wizard, evidence, prerequisites)
- [ ] Audit logs showing new event types
- [ ] No console errors or warnings
- [ ] Performance baseline met (< 200ms API responses)
- [ ] Rollback procedure tested and documented
- [ ] Team trained on new features
- [ ] Documentation updated in wiki/confluence
- [ ] Monitoring alerts configured

### Post-Deployment

- Monitor logs for 24 hours
- Check performance metrics
- Gather user feedback
- Schedule Phase D demo/training if applicable
- Plan Phase E (if applicable) or close Phase D

---

## Support & Escalation

### First Contact
- Check PHASE_D_TROUBLESHOOTING.md
- Review logs: `docker-compose logs backend`
- Test manually using PHASE_D_API_SPEC.md

### Engineering Team
- Phase D lead: (team member name)
- Backend expert: (team member name)
- Frontend expert: (team member name)
- DBA: (team member name)

### Escalation Path
1. Initial troubleshooting (30 min)
2. Team slack channel: #cra-tool-phase-d
3. Daily standup: (time/location)
4. Critical issues: Exec escalation

---

## Related Documentation

- [PHASE_D_API_SPEC.md](./PHASE_D_API_SPEC.md) — API endpoint reference
- [PHASE_D_FRONTEND_TESTING.md](./PHASE_D_FRONTEND_TESTING.md) — UI testing guide
- [PHASE_D_IMPLEMENTATION_SUMMARY.md](./memory/implementation_summary.md) — Architecture overview
- [CRA Compliance Tool README](./README.md) — Project overview
