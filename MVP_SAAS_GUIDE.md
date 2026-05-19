# CRA Compliance Tool — MVP SaaS Architecture

**Goal**: Launch with 2-3 paying customers, minimal infrastructure, maximum simplicity.

---

## Architecture (One Box)

```
User Browser
    ↓
Nginx (reverse proxy, SSL)
    ↓
FastAPI (single instance)
    ├─ All endpoints
    ├─ Auth logic
    └─ Background jobs (Celery Worker)
    ↓
PostgreSQL (single instance, shared DB)
    └─ tenant_id column on all tables
    ↓
File storage (local disk or S3)
    └─ /uploads/{tenant_id}/{entity_id}/
```

**Deployment**: 
- Single EC2 instance (t3.large, $100/month)
- RDS PostgreSQL (db.t4g.medium, $50/month)
- S3 for backups ($5/month)
- **Total: ~$155/month**

---

## Multitenancy (Simplified)

### Database Schema
```sql
-- Every table includes tenant_id
CREATE TABLE changes (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,  -- ← Multitenancy key
    title VARCHAR(255),
    description TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,  -- ← Users belong to tenant
    email VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(50),
    created_at TIMESTAMP,
    UNIQUE(tenant_id, email)  -- Email unique per tenant
);

-- Audit log (not HMAC-chained yet, just append-only)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(100),
    entity_type VARCHAR(100),
    entity_id UUID,
    changes_json JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Application-Level Isolation
```python
# middleware.py
from fastapi import Request
from app.models import User

async def enforce_tenant_isolation(request: Request, call_next):
    # Get user from JWT token
    user: User = request.state.user
    # Store tenant_id in request context
    request.state.tenant_id = user.tenant_id
    response = await call_next(request)
    return response

# routes/changes.py
@router.get("/changes")
async def list_changes(
    request: Request,
    db: Session = Depends(get_db)
):
    tenant_id = request.state.tenant_id
    # Query automatically filtered by tenant
    changes = db.query(Change).filter(
        Change.tenant_id == tenant_id
    ).all()
    return changes
```

---

## Authentication

### Simple Email/Password Flow
```
1. User enters email + password
   ↓
2. API validates against users table
3. If valid, issue JWT token
   {
     "sub": "user-uuid",
     "tenant_id": "acme-corp-uuid",
     "role": "change_assessor",
     "exp": 1800  (30 min)
   }
4. Frontend stores token in localStorage
5. All requests include Authorization: Bearer <token>
6. API validates token signature + expiration
```

### No LDAP Initially
- Focus on local user management
- Admin creates users manually
- Email + password only
- **Later**: Add LDAP for enterprise customers

---

## File Storage

### Option A: Local Disk (Simplest for MVP)
```
/var/lib/cra-uploads/
├── acme-corp-uuid/
│   ├── change-uuid-1/
│   │   ├── artifact-v1.pdf
│   │   ├── sbom-v1.json
│   │   └── evidence-v1.doc
│   └── change-uuid-2/
└── globex-inc-uuid/
    └── ...
```

**Pros:**
- No external dependencies
- Easy to set up
- Cheap (disk space only)

**Cons:**
- No automatic backups (manual rsync)
- Single instance = single point of failure
- Can't scale across servers

### Option B: S3 (Recommended)
```
s3://cra-uploads-prod/
├── acme-corp-uuid/
│   ├── change-uuid-1/
│   │   ├── artifact-v1.pdf
│   │   └── sbom-v1.json
│   └── ...
└── globex-inc-uuid/
    └── ...
```

**Pros:**
- Automatic redundancy
- Can serve directly to users (pre-signed URLs)
- Cheap ($0.023 per GB/month)
- Easy to migrate to CDN later

**Cons:**
- Requires AWS account
- Slightly more complex setup

**Cost for 100 customers × 100 MB each = 10 GB**: ~$0.25/month

---

## Background Jobs

### Use APScheduler (Simple Alternative to Celery)
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

app = FastAPI()
scheduler = AsyncIOScheduler()

# Job: Parse SBOM files
@scheduler.scheduled_job('interval', minutes=5)
async def process_sbom_queue():
    for artifact in db.query(Artifact).filter_by(parsed=False):
        try:
            sbom = parse_sbom(artifact.file_path)
            artifact.components = sbom.components
            artifact.parsed = True
            db.commit()
        except Exception as e:
            logger.error(f"SBOM parse failed: {e}")

# Job: Send email notifications
@scheduler.scheduled_job('interval', hours=1)
async def send_pending_notifications():
    for notification in db.query(Notification).filter_by(sent=False):
        send_email(notification.email, notification.message)
        notification.sent = True
        db.commit()

@app.on_event("startup")
async def start_scheduler():
    scheduler.start()
```

**No Celery needed for MVP:**
- APScheduler runs in-process
- Simple to debug
- 5-10 concurrent jobs max
- Later: Add Celery if needed

---

## Logging & Monitoring

### Keep It Simple
```python
# logging.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # Local file
        logging.StreamHandler()  # Also print to stdout
    ]
)

logger = logging.getLogger(__name__)

# In routes
logger.info(f"User {user_id} accessed changes for tenant {tenant_id}")
logger.error(f"Database error: {str(e)}", exc_info=True)
```

### Basic Metrics (Manual)
```
Monitor via logs + simple dashboard:
- Response times (add timing to logs)
- Error count (grep ERROR in logs)
- Active users (check JWT issues per day)
- Storage usage (du -sh /uploads/)
- Database size (SELECT pg_database_size('cra_compliance'))
```

### Optional: Use Free Tier Services
- **Sentry** (free tier): Error tracking
- **New Relic** (free tier): Performance monitoring
- **Datadog** (free tier): Log aggregation

---

## Scaling Path (When Needed)

### Stage 1: MVP (Now)
- Single instance
- Shared database
- Local storage
- **Cost**: ~$155/month

### Stage 2: Growing (10-20 customers)
- Upgrade instance (t3.xlarge)
- Read replica for reporting
- Move to S3 storage
- Add Sentry/NewRelic
- **Cost**: ~$400/month
- **No code changes required**

### Stage 3: Multi-Instance (50+ customers)
- Add load balancer (ALB)
- Multiple API instances
- RDS Multi-AZ
- Redis for caching
- Celery for background jobs
- **Cost**: ~$1000/month
- **Code migration**: Session management, job scheduling

### Stage 4: Enterprise (100+ customers)
- Kubernetes cluster
- Database-per-tenant option
- Dedicated LDAP integration
- Advanced observability
- **Cost**: ~$3000/month
- **Requires architecture redesign** (use the enterprise blueprint)

---

## Deployment

### Local Development
```bash
# Start database
docker run -d \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15

# Create database
createdb cra_compliance

# Run migrations
alembic upgrade head

# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend (separate terminal)
cd frontend
npm run dev
```

### Production (Single EC2 Instance)

**1. Launch EC2 instance**
```bash
# Ubuntu 22.04 LTS, t3.large, 30GB disk
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.large \
  --key-name my-key \
  --security-groups cra-app
```

**2. SSH into instance**
```bash
ssh ubuntu@<instance-ip>
```

**3. Install dependencies**
```bash
sudo apt update && sudo apt install -y \
  python3.11 python3-pip \
  nodejs npm \
  postgresql-client \
  nginx \
  git
```

**4. Clone repository**
```bash
git clone https://github.com/myorg/cra-compliance-tool.git
cd cra-compliance-tool
```

**5. Create RDS database**
```bash
# Via AWS Console or CLI
aws rds create-db-instance \
  --db-instance-identifier cra-prod \
  --db-instance-class db.t4g.medium \
  --engine postgres \
  --master-username postgres \
  --master-user-password <strong-password> \
  --allocated-storage 20
```

**6. Set environment variables**
```bash
# .env
DATABASE_URL=postgresql://postgres:password@cra-prod.xxx.rds.amazonaws.com:5432/cra_compliance
SECRET_KEY=<generate-with-secrets.token_hex(32)>
ENVIRONMENT=production
DEBUG=false
S3_BUCKET=cra-uploads-prod
S3_REGION=us-east-1
```

**7. Run migrations**
```bash
cd backend
alembic upgrade head
```

**8. Build frontend**
```bash
cd ../frontend
npm install
npm run build
```

**9. Configure Nginx**
```nginx
# /etc/nginx/sites-available/cra
server {
    listen 443 ssl http2;
    server_name app.cra-compliance.com;
    
    ssl_certificate /etc/letsencrypt/live/app.cra-compliance.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.cra-compliance.com/privkey.pem;
    
    # Static frontend assets
    location / {
        root /var/www/cra-compliance/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # API backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

**10. Start application**
```bash
# Use systemd for auto-restart
sudo systemctl start cra-app
sudo systemctl enable cra-app

# Or use PM2 (Node.js style process manager)
npm install -g pm2
pm2 start "uvicorn app.main:app --port 8000" --name cra-api
pm2 start "python -m celery -A app.tasks worker" --name cra-worker
pm2 save
```

**11. SSL Certificate**
```bash
# Use Let's Encrypt (free)
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --standalone -d app.cra-compliance.com
# Nginx automatically picks up the certificate
```

**Total setup time: ~30 minutes**

---

## Pricing (MVP Tier)

For early customers:
```
Startup Plan: $199/month
├── 3 users
├── 10 changes/month
├── 1GB storage
├── Email support (24h response)
└── Basic audit trail

Growth Plan: $499/month
├── 10 users
├── Unlimited changes
├── 10GB storage
├── Email support (4h response)
└── Advanced audit trail

Enterprise: Custom pricing
└── Contact sales
```

**Revenue model for profitability:**
- 5 customers @ $199 = $995
- 2 customers @ $499 = $998
- **Monthly revenue: $1,993**
- **Monthly cost: $155** (infrastructure)
- **Gross margin: 92%** 🎉

---

## What's NOT in MVP (Do Later)

✗ ~~Multi-region failover~~
✗ ~~Kubernetes orchestration~~
✗ ~~LDAP/OAuth integration~~
✗ ~~Row-Level Security database policies~~
✗ ~~HMAC-chained audit trail~~
✗ ~~Prometheus/Grafana monitoring~~
✗ ~~Distributed tracing (Jaeger)~~
✗ ~~Database-per-tenant option~~
✗ ~~Webhook integrations~~
✗ ~~Advanced SBOM diffing service~~

**MVP Focus**: 
- ✅ Core change assessment workflow
- ✅ Release gate lifecycle
- ✅ Certification record tracking
- ✅ Audit logging (append-only, JSON format)
- ✅ Multitenancy (app-enforced isolation)
- ✅ STRIDE/TARA assessment
- ✅ Role-based access control

---

## Migration Path (Enterprise)

When/if you grow to 50+ customers:

**1. Split database** (if needed)
   - Migrate large tenants to dedicated RDS instances
   - Keep small tenants on shared database
   - Code changes: Update connection pool logic

**2. Add load balancer**
   - Use AWS ALB
   - Route to multiple API instances
   - Code changes: Make sessions distributed (Redis)

**3. Move to Kubernetes** (if needed)
   - Use EKS (managed Kubernetes)
   - Auto-scale API servers
   - Easier deployment pipeline
   - Code changes: Containerize (already have Dockerfile)

**4. Add advanced monitoring**
   - Prometheus for metrics
   - ELK for logs
   - Jaeger for tracing
   - Code changes: Add instrumentation

---

## Success Metrics (MVP)

✅ **Shipping**
- Deployed to production by Month 1
- 2-3 paying customers by Month 3

✅ **Reliability**
- 99% uptime SLA
- <2s response time (p95)
- <5 error rate

✅ **Product**
- Users complete assessments without friction
- Can track release gates end-to-end
- Audit logs capture all actions

✅ **Operations**
- Can onboard new customer in <1 hour
- Can debug issues from logs
- Can restore from backup in <1 hour

---

## Checklist to Ship

- [ ] Setup EC2 instance
- [ ] Setup RDS database
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Configure SSL (Let's Encrypt)
- [ ] Setup basic monitoring (log files)
- [ ] Create first customer account
- [ ] Run smoke tests
- [ ] Create status page (statuspage.io - free tier)
- [ ] Setup email notifications (SendGrid free tier)
- [ ] Create support channel (email + Slack)
- [ ] Write runbook for common issues
- [ ] Setup database backups (daily)

**Total effort: ~2 weeks (one engineer)**

---

## Conclusion

This MVP architecture:
- ✅ Costs ~$150/month to run
- ✅ Can handle 50+ customers
- ✅ Takes 2 weeks to deploy
- ✅ Requires minimal ops knowledge
- ✅ Scales horizontally when needed
- ✅ No technical debt (will refactor for scale)

Focus on **product-market fit**, not infrastructure perfection. The best architecture is the one you can iterate on fastest.
