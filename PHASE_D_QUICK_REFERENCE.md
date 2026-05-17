# Phase D Quick Reference Card

**Deployment-ready summary for ops team**

---

## What's New (9 Endpoints)

### Assessment Wizard (STRIDE/TARA)
```
GET  /changes/assessment-templates/{stride|tara}  → 6/4 questions
GET  /changes/{id}/recommended-actions             → compliance actions
```

### Certification Evidence
```
POST   /certification-records/{id}/evidence                 → link existing
POST   /certification-records/{id}/evidence/upload          → upload + link
DELETE /certification-records/{id}/evidence/{link_id}       → remove
```

### Release Gate Prerequisites & Snapshot
```
POST   /product-releases/{id}/gate/prerequisites          → add dependency
DELETE /product-releases/{id}/gate/prerequisites          → remove dependency
GET    /product-releases/{id}/gate/prerequisites          → list
GET    /product-releases/{id}/gate/snapshot               → frozen state
```

---

## Database Changes (4 Migrations)

| # | Table | Action |
|---|-------|--------|
| 0029 | `release_gate_item_prerequisites` | CREATE TABLE (NEW) |
| 0030 | `substantial_modification_assessments` | ADD methodology, template_answers |
| 0031 | `certification_record_artifact_links` | CREATE TABLE (NEW) |
| 0032 | `release_gates` | ADD snapshot_json |

---

## Deploy in 5 Steps

```bash
# 1. Backup database
pg_dump postgresql://postgres:postgres@localhost:5432/cra_compliance \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Apply migrations
cd backend && alembic upgrade head

# 3. Build frontend
cd frontend && npm run build

# 4. Start services
docker-compose up -d

# 5. Verify health
sleep 10
curl http://localhost:8000/api/v1/changes/assessment-templates/stride | jq '.questions[0].id'
# Should output: "S1"
```

---

## Critical Features

### ✅ CRA Art. 3(4) Enforcement
Security changes are NEVER substantial (even if all criteria met)

### ✅ Evidence Tracking
Upload → Revision → SHA-256 Verify → Audit Trail

### ✅ Dependencies
Item B blocked until Item A accepted (visual graph)

### ✅ Snapshots
Frozen gate state at approval for audit trail

---

## Audit Events

| Operation | Event |
|-----------|-------|
| Evidence link added | `certification_record.update` / `evidence_attached` |
| Evidence uploaded | `certification_record.update` / `evidence_uploaded_attached` |
| Evidence removed | `certification_record.update` / `evidence_removed` |
| Prerequisite added | `release_gate.update` / `prerequisite_added` |
| Prerequisite removed | `release_gate.update` / `prerequisite_removed` |

---

## Permissions

| Endpoint | Permission |
|----------|-----------|
| Assessment templates | `change_read` |
| Certification evidence | `certification_record_write` |
| Gate prerequisites | `release_lifecycle_write` |
| Snapshot | `release_read` |

---

## Test Scenarios (Quick Smoke Tests)

### Assessment Wizard
```bash
# Get STRIDE questions
curl http://localhost:8000/api/v1/changes/assessment-templates/stride | jq '.questions | length'
# Expected: 6

# Get TARA questions  
curl http://localhost:8000/api/v1/changes/assessment-templates/tara | jq '.questions | length'
# Expected: 4
```

### Certification Evidence
```bash
# Create record (setup step, use your change_id)
# Upload evidence
curl -X POST http://localhost:8000/api/v1/certification-records/{id}/evidence/upload \
  -F "title=Test Report" \
  -F "artifact_type=test_report" \
  -F "upload=@test.pdf"

# Verify in response
jq '.artifact_links | length'
# Expected: >= 1
```

### Prerequisites
```bash
# Set prerequisite
curl -X POST http://localhost:8000/api/v1/product-releases/{id}/gate/prerequisites \
  -H "Content-Type: application/json" \
  -d '{
    "dependent_item_id": "item-b-uuid",
    "prerequisite_item_id": "item-a-uuid"
  }'

# List prerequisites
curl http://localhost:8000/api/v1/product-releases/{id}/gate/prerequisites | jq '. | length'
# Expected: >= 1
```

---

## Rollback (1 Command)

```bash
# Undo Phase D (back to 0028)
cd backend && alembic downgrade -4
```

---

## Monitoring Commands

```bash
# Check migrations applied
alembic current
# Expected: 20260517_0032

# Verify tables exist
psql -c "SELECT tablename FROM pg_tables WHERE tablename IN ('release_gate_item_prerequisites', 'certification_record_artifact_links');"
# Expected: 2 rows

# Check recent audit events (Phase D types)
psql -c "SELECT COUNT(*) FROM audit_log_events WHERE details_json::text ILIKE '%evidence%' OR details_json::text ILIKE '%prerequisite%';"

# Check logs
docker-compose logs -f backend | grep -E "ERROR|WARNING|POST|PUT|DELETE"
```

---

## Common Issues

| Issue | Fix |
|-------|-----|
| Migration fails (already exists) | `alembic downgrade -1` then `alembic upgrade head` |
| API 404 (endpoint not found) | Verify migrations applied: `alembic current` |
| Evidence upload hangs | Check file size (must be < server limit) |
| Frontend shows "No questions" | Check API response: `curl http://localhost:8000/api/v1/changes/assessment-templates/stride` |
| Blocking doesn't work | Verify gates have prerequisites set and item status in response |

---

## Files Changed

**Backend**: 12 files
- New: `assessment_template_service.py`
- Modified: models, services, routes, schemas
- New: 4 Alembic migrations

**Frontend**: 6 files
- New: `AssessmentWizard.vue`, `SbomDiffPanel.vue`
- Modified: 4 views, 1 type definition

**Documentation**: 4 guides + memory files
- `PHASE_D_API_SPEC.md` (400+ lines)
- `PHASE_D_FRONTEND_TESTING.md` (600+ lines)
- `PHASE_D_DEPLOYMENT_GUIDE.md` (500+ lines)
- Memory files in `.claude/projects/.../memory/`

---

## Team Contacts

**Phase D Lead**: (assign from team)
**Backend Expert**: (assign from team)
**Frontend Expert**: (assign from team)
**DBA**: (assign from team)

---

## Documentation Links

- Full API spec: `PHASE_D_API_SPEC.md`
- Testing procedures: `PHASE_D_FRONTEND_TESTING.md`
- Deployment guide: `PHASE_D_DEPLOYMENT_GUIDE.md`
- Architecture: Memory files in `.claude/projects/...`

---

## Success Criteria

- [x] All migrations apply without error
- [x] All 9 endpoints return expected responses
- [x] Evidence uploads and downloads work
- [x] Prerequisite blocking prevents invalid transitions
- [x] Snapshot captures at gate approval
- [x] Audit trail shows Phase D events
- [x] Frontend loads without console errors
- [x] TypeScript type-check passes (Phase D code)

---

## Post-Deploy Checklist

- [ ] All 4 migrations applied (`alembic current`)
- [ ] Both new tables exist
- [ ] Backend API responding (health check)
- [ ] Frontend loads without errors
- [ ] At least 1 smoke test passed
- [ ] Audit logs show Phase D events
- [ ] Logs monitored for 1 hour
- [ ] Team notified of completion

---

**Estimated Time**: 5 minutes deployment + 30 minutes testing = 35 minutes total

**Rollback Time**: < 2 minutes (single command)

**Go-Live**: When smoke tests pass and monitoring looks good
