# CRA Compliance Tool — SaaS Multitenancy Architecture

## Executive Summary

This document describes a production-grade SaaS architecture for the CRA Compliance Tool with full multitenancy support, high availability, and CRA compliance audit requirements.

**Key Characteristics:**
- **Multitenancy Model**: Hybrid (shared infrastructure, isolated data + configs)
- **Scalability**: Horizontal (stateless API servers, read replicas)
- **Isolation Level**: Row-Level Security (RLS) + cryptographic audit
- **Deployment**: Kubernetes, auto-scaling, multi-zone
- **Compliance**: Full audit trail with HMAC chaining, non-repudiation

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│           Client Layer (Multi-tenant)                │
│         (Web, Mobile, API Consumers)                 │
└────────────────┬────────────────────────────────────┘
                 │
         ┌───────▼───────┐
         │  API Gateway   │ ◄─── Tenant routing
         │  Load Balancer │      Rate limiting
         └───────┬───────┘      SSL/TLS
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼──┐    ┌───▼──┐    ┌───▼──┐
│ API 1│    │ API 2│    │ API N│  ◄─── Stateless
└───┬──┘    └───┬──┘    └───┬──┘      Autoscaling
    │           │            │
    └───────────┼────────────┘
                │
         ┌──────▼──────┐
         │  Services   │  ◄─── Domain-driven
         │  Layer      │       Tenant-aware
         └──────┬──────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼──┐   ┌───▼──┐   ┌───▼──┐
│Tenant│   │Tenant│   │Shared │ ◄─── Data tier
│DB A  │   │DB B  │   │ Audit │      Isolation
└──────┘   └──────┘   └───────┘
```

---

## 1. Client Layer

### Frontend Applications
- **Web SPA** (Vue.js)
  - Multi-tenant UI components
  - Tenant selector/switcher
  - Context awareness via JWT claims
  
- **Supported Clients**
  - Browser-based (responsive, mobile-friendly)
  - API consumers (third-party integrations)
  - CLI tools (future expansion)

### Tenant Context
Propagated via:
```
JWT Token Payload:
{
  "sub": "user-uuid",
  "tenant_id": "acme-corp",
  "email": "user@acme-corp.com",
  "roles": ["change_assessor", "release_manager"],
  "org_name": "Acme Corp"
}

HTTP Headers:
X-Tenant-ID: acme-corp
Authorization: Bearer <jwt-token>
```

---

## 2. API Gateway & Load Balancing

### Components
- **CDN** (CloudFront/Cloudflare)
  - Static asset delivery (Vue.js bundles, CSS, images)
  - Geo-distribution for latency
  - DDoS protection
  
- **Application Load Balancer (ALB)**
  - Route by tenant subdomain (`tenant-a.example.com`)
  - TLS termination
  - Health checks
  - Rate limiting per tenant
  
- **API Gateway Features**
  - Request validation
  - Tenant extraction from Host/JWT
  - Request/response logging
  - Circuit breaker patterns

### Rate Limiting Strategy
```
Per-tenant limits:
- Startup tier:      100 req/min
- Growth tier:       500 req/min
- Enterprise tier:   5,000 req/min
- Custom:            Configurable

Protected endpoints:
- Auth: 10 attempts/min per IP
- Assessment: 100/hour per tenant
- File uploads: 50/hour per tenant
```

---

## 3. Authentication & Authorization

### Multi-Tenant Auth Flow

```
1. User submits credentials
   ↓
2. Auth Service validates against Identity Provider
   - Local user DB (with tenant_id foreign key)
   - LDAP (with tenant-specific OU/group mapping)
   - OAuth (with tenant claim in JWT)
   ↓
3. JWT issued with tenant_id + roles + permissions
   ↓
4. Frontend stores token in httpOnly cookie
5. All API requests include Authorization header
   ↓
6. API validates token:
   - Signature integrity
   - Expiration
   - Tenant match (from header vs. JWT claim)
   ↓
7. Request proceedes with tenant context
```

### Role-Based Access Control (RBAC)
```
Tenant-scoped roles:
├── change_viewer       (read changes)
├── change_assessor     (assess changes)
├── release_manager     (approve releases)
├── compliance_admin    (manage compliance settings)
├── audit_viewer        (view audit logs only)
└── system_admin        (full access including config)

Permissions enforced at:
- API endpoint level (route guards)
- Service layer (business logic checks)
- Database layer (Row-Level Security)
```

### Identity Provider Integration
```
LDAP Configuration per Tenant:
{
  "tenant_id": "acme-corp",
  "ldap_enabled": true,
  "ldap_server_url": "ldaps://ldap.acme-corp.com:636",
  "ldap_bind_dn": "cn=service,dc=acme-corp,dc=com",
  "ldap_base_dn": "ou=users,dc=acme-corp,dc=com",
  "ldap_user_filter": "(mail={email})",
  "ldap_group_mapping": {
    "cn=release-managers,ou=groups": "release_manager",
    "cn=assessors,ou=groups": "change_assessor"
  },
  "sync_interval": "6h"
}
```

---

## 4. API Layer (Microservices)

### API Server Design
- **Framework**: FastAPI (async, type-safe)
- **Instances**: N replicas behind load balancer
- **Stateless**: No session affinity required
- **Scaling**: Horizontal (add/remove instances based on CPU/memory)

### Services Deployed
```
Core Services:
├── Change Service
│   └── Substantial modification tracking
│       ├── Assessment (STRIDE/TARA)
│       ├── Compliance actions
│       └── Workflow transitions
│
├── Release Gate Service
│   └── Product release lifecycle
│       ├── Evidence collection
│       ├── SBOM analysis
│       ├── Prerequisite dependencies
│       └── Approval snapshots
│
├── Certification Service
│   └── Compliance documentation
│       ├── Evidence attachment
│       ├── Audit trail
│       └── Revision tracking
│
├── Assessment Template Service
│   └── Threat assessment frameworks
│       ├── STRIDE (6 questions)
│       ├── TARA (4 questions)
│       └── Recommendation engine
│
└── Artifact Service
    └── File & evidence management
        ├── Upload & versioning
        ├── SHA-256 integrity
        ├── SBOM parsing
        └── Virus scanning (via async job)
```

### Tenant Context Injection
```python
# Every endpoint receives tenant context
from fastapi import Depends
from app.core.security import get_current_tenant

@router.get("/changes")
async def list_changes(
    current_tenant: TenantContext = Depends(get_current_tenant),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # All queries automatically filtered by current_tenant.id
    # Via Row-Level Security policies in database
    changes = db.query(Change).filter(
        Change.tenant_id == current_tenant.id
    ).all()
    return changes
```

---

## 5. Data Layer (Multitenancy Strategy)

### Option A: Database-per-Tenant (Maximum Isolation)

**Pros:**
- Complete logical isolation
- Easy regulatory compliance (separate backups per tenant)
- Different DB versions/configurations per tenant
- Simplified compliance audits

**Cons:**
- Operational overhead (manage N databases)
- Higher cost (DB licenses, storage)
- Complex upgrades (must apply migrations to all DBs)

**Use for:** Enterprise tier customers, regulated industries

### Option B: Shared Database with Row-Level Security (Cost-Effective)

**Pros:**
- Single DB instance (lower cost)
- Unified backup/restore strategy
- Simpler operational management
- PostgreSQL RLS provides security enforcement

**Cons:**
- Noisy neighbor (one tenant can impact others)
- More complex audit compliance
- Requires careful RLS policy design

**PostgreSQL RLS Implementation:**
```sql
-- Create tenant column on every table
ALTER TABLE changes ADD COLUMN tenant_id UUID NOT NULL;
ALTER TABLE release_gates ADD COLUMN tenant_id UUID NOT NULL;
ALTER TABLE users ADD COLUMN tenant_id UUID NOT NULL;

-- Create RLS policies
CREATE POLICY tenant_isolation ON changes
  FOR ALL TO authenticated
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

CREATE POLICY tenant_isolation ON release_gates
  FOR ALL TO authenticated
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Set tenant context per session
SET app.current_tenant_id = 'acme-corp-uuid';

-- Verify isolation
SELECT * FROM changes; -- Only returns rows where tenant_id matches
```

**Use for:** Startup/Growth tier customers, standard compliance

### Option C: Hybrid (Recommended)
- **Default**: Shared DB with RLS (Cost-effective)
- **For Enterprise tenants**: Dedicated DB + read replicas
- **Dynamic routing**: API transparently routes to correct DB based on tenant_id

**Implementation:**
```python
# Tenant-aware DB routing
class TenantDatabaseRouter:
    def get_db_url(self, tenant_id: str) -> str:
        tenant = db.query(Tenant).filter_by(id=tenant_id).first()
        if tenant.isolation_level == "dedicated":
            return tenant.database_url  # Dedicated DB
        else:
            return DEFAULT_DB_URL  # Shared DB with RLS

# Usage in dependency injection
def get_db(tenant_id: str = Depends(get_current_tenant_id)):
    db_url = router.get_db_url(tenant_id)
    return SessionLocal(bind=create_engine(db_url))
```

---

## 6. Storage & Artifact Management

### S3 Bucket Structure
```
s3://cra-compliance-prod/
├── tenants/
│   ├── acme-corp-uuid/
│   │   ├── artifacts/
│   │   │   ├── sbom-files/
│   │   │   ├── evidence/
│   │   │   └── certificates/
│   │   ├── uploads/
│   │   └── backups/
│   ├── globex-inc-uuid/
│   │   └── [same structure]
│   └── ...
├── shared/
│   └── [templates, configs, etc.]
```

### Access Control
```
IAM Policy per tenant:
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::cra-compliance/tenants/acme-corp/*"
    }
  ]
}

Pre-signed URLs:
- Issued by API server
- 15-minute expiration
- Tenant scoped
- Audit logged
```

### Caching Layer
```
Redis (tenant-scoped keys):
- cache_key = f"{tenant_id}:artifact:{artifact_id}:metadata"
- TTL = 1 hour
- Invalidated on update

Use cases:
- Artifact metadata (size, type, hash)
- SBOM analysis results (component list, vulnerabilities)
- User session data
- Feature flags per tenant
```

---

## 7. Audit & Compliance

### Audit Trail System

**Requirements:**
- Non-repudiation (cryptographic proof of action)
- Immutability (append-only, cannot be deleted)
- Tenant isolation (cannot access other tenant's audit logs)
- Regulatory compliance (CRA Article 3, GDPR)

**HMAC-Chained Audit Events:**
```sql
CREATE TABLE audit_log_events (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    actor_user_id UUID,
    action_type VARCHAR(100),
    entity_type VARCHAR(100),
    entity_id UUID,
    changes_json JSONB,
    created_at TIMESTAMP,
    
    -- Security fields
    hmac_hash VARCHAR(64),  -- SHA-256 HMAC of previous event
    previous_event_id UUID REFERENCES audit_log_events(id),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE RESTRICT
);

-- Chain integrity validation
SELECT *
FROM audit_log_events
WHERE tenant_id = $1
ORDER BY created_at ASC
-- Each event's hmac_hash must equal HMAC(previous_event || secret_key)
```

**Audit Coverage:**
```
Changes:
├── change.created
├── change.submitted
├── change.claimed
├── change.assessed
├── change.closed
└── assessment_method_changed

Release Gates:
├── gate.opened
├── gate_item.evidence_attached
├── gate_item.evidence_reviewed
├── gate_item.prerequisite_added
├── gate_item.prerequisite_removed
└── gate.approved

Certification:
├── certification_record.evidence_attached
├── certification_record.evidence_removed
└── certification.completed

Administrative:
├── user.created (per tenant)
├── user.disabled
├── role.assigned
├── role.revoked
└── tenant_config.updated
```

---

## 8. Background Jobs & Event Processing

### Message Queue (RabbitMQ/SQS)

**Tenant-scoped topics:**
```
cra-events:
├── tenant:acme-corp:artifact:uploaded
├── tenant:acme-corp:sbom:analyzed
├── tenant:acme-corp:assessment:submitted
├── tenant:globex-inc:artifact:uploaded
└── ...
```

**Async Jobs:**
```
1. SBOM Analysis
   - Trigger: Artifact uploaded with .sbom extension
   - Process: Parse SBOM, extract components, diff vs. previous version
   - Storage: Result cached in Redis, stored in audit log
   - Time: 5-30 seconds per file

2. Virus Scanning
   - Trigger: Any artifact upload
   - Process: ClamAV scan, quarantine if infected
   - Notification: Email if malware detected
   - Time: 2-10 seconds per file

3. User Sync (LDAP)
   - Trigger: Scheduled (daily), on-demand via admin UI
   - Process: Query LDAP, sync users, update group memberships
   - Deprovisioning: Disable stale accounts
   - Time: Varies (1 min - 1 hour depending on LDAP size)

4. Email Notifications
   - Trigger: Assessment due date, gate approval, compliance actions
   - Process: Render template, send via SES/SendGrid
   - Retry: 3x with exponential backoff
   - Time: <1 second per email

5. Report Generation
   - Trigger: Scheduled (monthly), on-demand
   - Process: Aggregate audit events, generate PDF
   - Storage: S3, link sent via email
   - Time: 5-60 seconds depending on volume

6. Compliance Snapshot
   - Trigger: Gate approval
   - Process: Freeze evidence state, bundle artifacts, compute hash
   - Storage: Audit table + S3
   - Time: <5 seconds
```

### Dead Letter Queue (DLQ)
```
For failed jobs:
- Retry logic with backoff (1s, 10s, 60s, 5min, 30min)
- Move to DLQ after 5 failures
- Alert on DLQ arrival
- Manual replay capability
```

---

## 9. Observability & Monitoring

### Logging
```
Structured logs (JSON):
{
  "timestamp": "2026-05-19T10:30:00Z",
  "level": "INFO",
  "service": "change-service",
  "tenant_id": "acme-corp-uuid",
  "user_id": "user-uuid",
  "action": "assess_change",
  "change_id": "change-uuid",
  "result": "success",
  "duration_ms": 245,
  "trace_id": "abc123xyz789"
}

Log aggregation: ELK Stack / Datadog
Per-tenant log isolation: Tenant_id in every log entry
PII masking: Email addresses, passwords, secrets redacted
Retention: 30 days (hot), 1 year (archive for compliance)
```

### Metrics
```
Prometheus metrics (per tenant):
- api_request_duration_seconds (histogram)
- api_request_total (counter, by endpoint/method/status)
- db_query_duration_seconds (histogram)
- background_job_duration_seconds (by job_type)
- artifact_upload_size_bytes (histogram)
- cache_hit_rate (gauge, by cache_type)
- active_sessions_total (gauge)
- error_rate (by error_type)

Grafana dashboards:
- Per-tenant dashboard (isolated view of metrics)
- Shared operational dashboard (aggregate health)
- SLA tracking (uptime, latency P95/P99)
```

### Distributed Tracing
```
Jaeger/Zipkin for request tracing:
- Trace ID propagated across all services
- Span per service (API → Change Service → DB)
- Tenant context tagged on every span
- Latency analysis (where time is spent)
```

### Alerts
```
Trigger on:
- Error rate > 1% (per tenant, per endpoint)
- API latency P95 > 2s
- DB query duration > 5s
- Background job failure rate > 5%
- Authentication failures > 10/min
- RLS policy violations (suspicious queries)
- Audit log gaps (missing chained events)
- Certificate expiration < 30 days

Escalation:
- Slack #ops channel (non-critical)
- PagerDuty (critical)
- Email to tenant admin (if tenant-specific issue)
```

---

## 10. Deployment & Infrastructure

### Kubernetes Architecture

```
Namespace-per-tenant isolation:
k8s cluster
├── acme-corp (namespace)
│   ├── api-deployment (3 replicas)
│   ├── worker-deployment (2 replicas)
│   └── configmap (tenant-specific config)
├── globex-inc (namespace)
│   ├── api-deployment (5 replicas)
│   ├── worker-deployment (3 replicas)
│   └── configmap
└── shared (namespace)
    ├── postgres-statefulset (multi-tenant DB)
    ├── redis-statefulset (cache layer)
    ├── rabbitmq-statefulset (message queue)
    └── nginx-ingress (load balancing)
```

### Autoscaling Configuration
```yaml
# HPA per tenant namespace
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  namespace: acme-corp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Deployment Pipeline
```
GitHub → GitHub Actions → Registry → Kubernetes
│
├─ Code commit
├─ Run tests (unit, integration)
├─ Type checking (TypeScript, Python)
├─ SAST scan (security)
├─ Build Docker image (tag: git-sha)
├─ Push to ECR/Docker Hub
├─ Update K8s manifests
├─ Deploy to staging (automated)
├─ Run smoke tests
├─ Deploy to production (manual approval)
└─ Health checks + monitoring (30 min)
```

---

## 11. High Availability & Disaster Recovery

### RTO & RPO Targets
```
RTO (Recovery Time Objective): 15 minutes
RPO (Recovery Point Objective): 5 minutes

Meaning:
- If primary region fails, failover in 15 min
- Data loss ≤ 5 minutes (automated backups every 5 min)
```

### Database Replication
```
Primary DB (Frankfurt)
    ↓ (streaming replication)
Secondary DB (Berlin) — read-only replicas
    ↓ (async)
Backup DB (Paris) — offline backup

Switchover process:
1. Detect primary failure (5s detection)
2. Promote secondary to primary (30s)
3. Update connection strings (30s)
4. Run validation queries (1m)
5. Resume traffic to new primary
```

### Backup Strategy
```
Automated backups:
- Continuous WAL shipping (5 min RPO)
- Daily full backup (24h retention)
- Weekly snapshots (3 month retention)
- Monthly archive (1 year retention)

Backup storage:
- Hot: S3 Standard (2 regions)
- Warm: S3 Glacier (1 year)
- Cold: S3 Glacier Deep Archive (7 years for compliance)

Restore testing:
- Monthly restore drill (catch corruption)
- Per-tenant isolation (restore only specific tenant)
```

---

## 12. Security Considerations

### Encryption

**At Rest:**
- Database encryption (TDE on PostgreSQL)
- S3 encryption (AES-256)
- Redis encryption (TLS between app and cache)

**In Transit:**
- TLS 1.3 for all external connections
- Mutual TLS (mTLS) for service-to-service
- Certificate pinning for critical paths

### Secret Management
```
Vault (HashiCorp Vault or AWS Secrets Manager):
├── db-passwords (per tenant if isolated DB)
├── ldap-bind-passwords
├── api-keys (for integrations)
├── jwt-signing-keys (rotation every 90 days)
└── audit-hmac-keys (per tenant)

Access control:
- API servers: Read-only access to tenant's secrets
- Workers: Scoped to assigned tenants
- Admins: Full audit trail of secret access
```

### Rate Limiting & DDoS

```
Per-tenant request quotas:
- Startup: 100 req/min
- Growth: 500 req/min  
- Enterprise: Custom

Per-IP limits:
- Global auth endpoint: 10 attempts/min
- General endpoints: 30 req/min
- File uploads: 10 req/min

Cloudflare WAF rules:
- Block known exploit patterns
- Rate limit by IP + User-Agent combo
- Geo-blocking (optional per tenant)
- Bot detection (JavaScript challenge)
```

---

## 13. Operational Runbooks

### Tenant Onboarding
```
1. Create tenant in DB
   INSERT INTO tenants (id, name, tier, database_url, ...);

2. Initialize tenant database schema
   alembic upgrade head --target-tenant=<tenant_id>

3. Create initial admin user
   POST /admin/tenants/<id>/users/initialize

4. Configure LDAP (if enabled)
   PATCH /admin/tenants/<id>/config/ldap

5. Set feature flags
   POST /admin/tenants/<id>/feature-flags

6. Health check
   GET /health?tenant_id=<tenant_id> → must pass

7. Notify customer
   - Tenant URL
   - Initial admin credentials
   - Documentation link
```

### Scaling Tenant Resources
```
Monitoring: Tenant consuming > 80% quota
→ Alert → Manual review → Upgrade tier or add resources

Options:
1. Upgrade tier (auto-scaling limits increase)
2. Request quota increase (documented, with SLA)
3. Migrate to dedicated database (enterprise tier)

Procedure:
1. Plan during maintenance window
2. Verify backups
3. Scale resources (DB IOPS, K8s replicas)
4. Run smoke tests
5. Monitor for 24 hours
```

### Incident Response

**Example: High error rate in production**
```
1. Alert fires → #ops Slack
2. On-call engineer checks metrics
   - What endpoint? (GET /changes → 50% error rate)
   - What tenant? (acme-corp-uuid)
   - What error? (Database connection timeout)
3. Check database health
   - Connections exhausted → connection pool misconfiguration
   - CPU high → need query optimization or more resources
4. Immediate action
   - Rollback (if recent code change)
   - Increase DB connections (if quota available)
   - Failover to replica (if primary is failing)
5. Root cause analysis
   - Review logs (Datadog)
   - Check queries (PostgreSQL slow log)
   - Analyze metric trends (Grafana)
6. Fix & prevention
   - Optimize query (add index, rewrite logic)
   - Increase default connection pool
   - Add alert for connection count trending
7. Post-mortem (within 24 hours)
```

---

## 14. Cost Optimization

### Tiered Pricing Model
```
Startup ($199/month)
├── 100 req/min
├── 5 users
├── 10GB storage
├── Shared database
└── 7-day audit retention

Growth ($999/month)
├── 500 req/min
├── 50 users
├── 100GB storage
├── Shared DB with priority support
└── 30-day audit retention

Enterprise (Custom)
├── Unlimited req/min
├── Unlimited users
├── Custom storage
├── Dedicated database
└── 1-year audit retention + cold archive

Usage overages:
- Additional API calls: $0.01 per 100 requests
- Additional storage: $0.50 per GB/month
- Additional users: $10 per user/month
```

### Infrastructure Cost Reduction
```
1. Right-size resources
   - Monitor actual CPU/memory usage
   - Scale down during off-peak
   - Use spot instances for workers (80% savings)

2. Database optimization
   - Shared DB with RLS (vs. DB-per-tenant)
   - Read replicas for analytics (not application reads)
   - Optimize indices (monitor slow queries)

3. Storage optimization
   - Tiered storage (S3 → Glacier → Deep Archive)
   - Compress SBOM/artifact files
   - Deduplicate audit logs (only store deltas)

4. Caching strategy
   - Aggressive client-side caching (assets)
   - Redis for hot data (assessment templates, user configs)
   - CDN edge caching (reduce origin load)
```

---

## 15. Compliance & Governance

### Data Residency

```
EU tenants:
├── Application servers: Frankfurt (eu-central-1)
├── Primary database: Frankfurt
├── Read replicas: Berlin, Amsterdam
├── Backups: Multiple EU regions
└── GDPR compliance: Data never leaves EU

US tenants:
├── Application servers: N. Virginia (us-east-1)
├── Primary database: N. Virginia
├── Backups: Multiple US regions
└── SOC 2 Type II compliance
```

### Audit Trail Integrity

```
HMAC chaining:
Event[n].hmac = HMAC-SHA256(Event[n-1] || secret_key)

Verification:
- Periodic batch validation (daily)
- Alert on chain break (tampering detected)
- Immutable storage (append-only audit tables)

CRA Compliance:
- Non-repudiation (HMAC prevents denial)
- Auditability (complete event trail)
- Traceability (user_id + timestamp on all actions)
```

### Regulatory Compliance Checklist
```
☐ CRA (Cyber Resilience Act)
  ├─ Substantial change tracking
  ├─ Assessment methodologies (STRIDE/TARA)
  ├─ Compliance action tracking
  ├─ Non-repudiation via HMAC
  └─ Audit trail for 10 years

☐ GDPR (General Data Protection Regulation)
  ├─ User data encryption
  ├─ Right to erasure (anonymization procedure)
  ├─ Data processing agreements (DPA)
  ├─ Data breach notification (72 hour SLA)
  └─ Data subject requests (30 day SLA)

☐ SOC 2 Type II (US)
  ├─ Access controls
  ├─ Change management
  ├─ Incident response
  ├─ Monitoring & logging
  └─ Annual audit

☐ ISO 27001 (Information Security)
  ├─ Risk assessments
  ├─ Security policies
  ├─ Incident management
  ├─ Business continuity
  └─ Third-party assessments
```

---

## Summary

This architecture provides:

✅ **Scalability**: Horizontal scaling of APIs, auto-scaling based on demand
✅ **Isolation**: Tenant data never mixed, cryptographic audit trail
✅ **Compliance**: Full audit trail with non-repudiation, GDPR/CRA/SOC2 ready
✅ **Reliability**: 99.9% SLA, multi-region failover, automated backups
✅ **Cost-Effectiveness**: Shared infrastructure, usage-based pricing tiers
✅ **Operability**: Kubernetes-native, observability-first, runbooks for common tasks

### Next Steps
1. Review architecture with security team
2. Design database schema for multitenancy (RLS vs. isolated DBs)
3. Implement authentication/authorization middleware
4. Set up Kubernetes cluster with tenant namespaces
5. Build tenant provisioning workflow
6. Configure observability (logging, metrics, tracing)
7. Create operational runbooks
8. Run load tests (tenant isolation, resource limits)
9. Security audit (penetration testing, compliance review)
10. Go-live with pilot customer
