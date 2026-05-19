# Zero-Downtime Migration Strategy

## Overview

This guide explains how to scale from Stage 1 (MVP) → Stage 4 (Enterprise) without affecting active users.

**Key Principles:**
- ✅ **Blue-Green Deployment** — Old version stays active during migration
- ✅ **Backward Compatibility** — Never break existing clients
- ✅ **Gradual Rollout** — Shift traffic in waves, not all at once
- ✅ **Instant Rollback** — If issues arise, switch back in <1 minute
- ✅ **Data Consistency** — Database migrations run before code deployment

---

## Stage 1 → Stage 2 (MVP to Growing)

**Scenario**: Instance is at capacity. Need to scale up resources.

### Migration Timeline
```
T-0:   Plan maintenance window (2am-4am, lowest traffic)
T-1hr: Final database backup
T-30m: Start deployment (users still on old instance)
T-20m: Prepare new instance
T-10m: Switch DNS + load balancer
T+0:   New instance takes traffic
T+15m: Monitor error rates, rollback if needed
T+60m: Confirm all metrics healthy, notify customers
```

### Step 1: Prepare New Instance
```bash
# Launch new t3.xlarge instance (double the size)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.xlarge \  # Was t3.large
  --key-name my-key

# Copy code + config from old instance
ssh ubuntu@new-instance
git clone https://github.com/myorg/cra-compliance-tool.git
# ... same setup as initial deployment

# Verify connectivity to same RDS database
psql -h cra-prod.xxx.rds.amazonaws.com -U postgres -d cra_compliance
# If this works, new instance can access all data
```

### Step 2: Load Balancer Switch
```bash
# Update security group to allow new instance
aws ec2 modify-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp --port 8000 --cidr 0.0.0.0/0

# Update Nginx upstream to point to new instance
# In /etc/nginx/sites-available/cra:
upstream cra_backend {
    server 10.0.1.50:8000;  # OLD instance (keep for now)
    server 10.0.1.75:8000;  # NEW instance
}

# Reload Nginx (no downtime)
sudo systemctl reload nginx

# Monitor metrics to see traffic distributed
watch -n 1 'curl -s http://10.0.1.75:8000/health | jq .'
```

### Step 3: Verify New Instance
```bash
# Run smoke tests against new instance
./tests/smoke_test.sh --instance 10.0.1.75

# Check key endpoints respond correctly
curl -H "Authorization: Bearer $TEST_TOKEN" \
  http://10.0.1.75:8000/api/v1/changes

# Verify database queries work
psql -h cra-prod.xxx.rds.amazonaws.com -U postgres \
  -d cra_compliance \
  -c "SELECT COUNT(*) FROM changes;"
```

### Step 4: Gradual Traffic Shift
```nginx
# Update Nginx upstream with weights
upstream cra_backend {
    server 10.0.1.50:8000 weight=90;  # 90% OLD
    server 10.0.1.75:8000 weight=10;  # 10% NEW
}

# After 10 min: shift more traffic
upstream cra_backend {
    server 10.0.1.50:8000 weight=50;
    server 10.0.1.75:8000 weight=50;
}

# After 20 min: shift all traffic
upstream cra_backend {
    server 10.0.1.75:8000 weight=100;  # NEW takes 100%
}

# After 30 min: stop old instance
aws ec2 stop-instances --instance-ids i-xxx
```

### Step 5: Rollback Procedure (If Issues)
```bash
# If error rate spikes on new instance:
# 1. Update Nginx to point back to old instance
upstream cra_backend {
    server 10.0.1.50:8000 weight=100;  # OLD gets traffic back
}

# 2. Reload Nginx
sudo systemctl reload nginx

# 3. Verify requests work
curl http://10.0.1.50:8000/health

# 4. Investigate issue on new instance
ssh ubuntu@new-instance
tail -100 app.log
# ... debug ...

# 5. Once fixed, retry deployment
```

**No Data Lost**: Both instances connect to same RDS database, so switching traffic is just routing change.

---

## Stage 2 → Stage 3 (Growing to Multi-Instance)

**Scenario**: Need multiple API instances behind a load balancer for redundancy + scaling.

### Key Change: Session Management
With multiple instances, user sessions can't be stored in-memory. Must move to Redis.

### Migration Timeline
```
T-0:   Prepare Redis instance
T-1hr: Deploy code that reads/writes sessions to Redis
T-2hr: Old code (memory-based sessions) still active
T-3hr: Switch traffic to new code
T-4hr: Decommission old instance
```

### Step 1: Deploy Redis (No Code Change Yet)
```bash
# Create ElastiCache Redis cluster (managed)
aws elasticache create-cache-cluster \
  --cache-cluster-id cra-sessions \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --num-cache-nodes 1

# Get endpoint
aws elasticache describe-cache-clusters \
  --cache-cluster-id cra-sessions \
  --query 'CacheClusters[0].CacheNodes[0].Endpoint'
# Returns: cra-sessions.xxxxx.ng.0001.use1.cache.amazonaws.com:6379

# Add Redis URL to .env
echo "REDIS_URL=redis://cra-sessions.xxxxx.ng.0001.use1.cache.amazonaws.com:6379" >> .env
```

### Step 2: Update Code (Session Storage)
```python
# OLD: In-memory sessions
from fastapi.middleware.sessions import SessionMiddleware
app.add_middleware(SessionMiddleware, secret_key="secret")

# NEW: Redis-based sessions
import redis_sessions

SessionStore = redis_sessions.RedisSessionStore(
    redis_url=os.getenv("REDIS_URL")
)
app.add_middleware(RedisSessionMiddleware, store=SessionStore)
```

**Important**: Code remains backward compatible. If Redis is unavailable, fall back to memory (with warning).

```python
# Graceful degradation
try:
    SessionStore = redis_sessions.RedisSessionStore(redis_url)
except Exception as e:
    logger.warning(f"Redis unavailable, using memory sessions: {e}")
    SessionStore = MemorySessionStore()
```

### Step 3: Deploy Code Update
```bash
# On Stage 2 (single instance)
git pull origin main
# Code now reads/writes to Redis

# Sessions are still stored in Redis
# Old code still has in-memory sessions
# No conflict because they use different storage
```

### Step 4: Launch Load Balancer + Second Instance
```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name cra-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target group
aws elbv2 create-target-group \
  --name cra-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id vpc-xxx

# Register first instance
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=i-xxx

# Launch second instance with same code
aws ec2 run-instances --image-id ami-xxx --instance-type t3.large
# (Copy code + deploy, points to same Redis + RDS)

# Register second instance
aws elbv2 register-targets \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --targets Id=i-yyy
```

### Step 5: Update DNS to Point to Load Balancer
```bash
# Update DNS CNAME record
# app.cra-compliance.com → cra-alb-xxx.us-east-1.elb.amazonaws.com

# Gradual traffic shift (optional, depends on DNS TTL)
# Most clients will see new load balancer within 5 minutes

# Monitor both instances
watch -n 1 'aws elbv2 describe-target-health --target-group-arn ...'
# Status: healthy, healthy ✓
```

### Test Multi-Instance Behavior
```bash
# Verify sessions persist across instances
curl -c cookies.txt \
  -b cookies.txt \
  http://cra-alb-xxx.us-east-1.elb.amazonaws.com/api/v1/auth/login \
  -d '{"email": "user@acme.com", "password": "..."}'

# Make request that hits instance 1
curl -b cookies.txt \
  http://cra-alb-xxx.us-east-1.elb.amazonaws.com/api/v1/changes

# Make request that hits instance 2 (ALB round-robins)
curl -b cookies.txt \
  http://cra-alb-xxx.us-east-1.elb.amazonaws.com/api/v1/changes

# Both should work (session persists via Redis)
```

### Rollback (If Issues)
```bash
# If problems with Redis/multi-instance:

# 1. Revert DNS to point directly to single instance
# 2. Remove second instance from load balancer
# 3. Keep old instance running on single-instance mode
# 4. Debug Redis issues separately
# 5. Retry migration when ready
```

---

## Stage 3 → Stage 4 (Multi-Instance to Kubernetes)

**Scenario**: Need better orchestration, auto-scaling, and want to support database-per-tenant.

### Key Changes
1. **Containerization** — Docker image instead of direct EC2 deployment
2. **Service Discovery** — Kubernetes replaces manual instance management
3. **Database Routing** — Route to different DBs based on tenant_id (optional)

### Migration Timeline
```
T-0:   Create Kubernetes cluster
T-1hr: Build Docker image, push to registry
T-2hr: Deploy to K8s (alongside old ALB setup)
T-3hr: Gradual traffic shift to K8s ingress
T-4hr: Keep old EC2 instances running for rollback
T-5hr: Monitor for issues
T+24h: Decommission old EC2 instances
```

### Step 1: Containerize Application (No Breaking Changes)
```dockerfile
# Dockerfile (same code as before)
FROM python:3.11-slim

WORKDIR /app
COPY backend /app

RUN pip install -r requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build image
docker build -t cra-compliance:v2.0 .

# Push to ECR (or Docker Hub)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag cra-compliance:v2.0 123456789.dkr.ecr.us-east-1.amazonaws.com/cra-compliance:v2.0
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/cra-compliance:v2.0
```

### Step 2: Create Kubernetes Cluster
```bash
# Create EKS cluster
eksctl create cluster --name cra-prod --region us-east-1 --nodes 2

# Verify cluster
kubectl get nodes
# NAME                          STATUS
# ip-10-0-1-100.ec2.internal   Ready
# ip-10-0-1-101.ec2.internal   Ready
```

### Step 3: Deploy to Kubernetes
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cra-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: cra-api
  template:
    metadata:
      labels:
        app: cra-api
    spec:
      containers:
      - name: cra-api
        image: 123456789.dkr.ecr.us-east-1.amazonaws.com/cra-compliance:v2.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cra-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: cra-config
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi

---
apiVersion: v1
kind: Service
metadata:
  name: cra-api
spec:
  type: LoadBalancer
  selector:
    app: cra-api
  ports:
  - port: 80
    targetPort: 8000
```

```bash
# Create secrets (same values as old .env)
kubectl create secret generic cra-secrets \
  --from-literal=database-url=postgresql://postgres:password@cra-prod.xxx.rds.amazonaws.com:5432/cra_compliance

# Create config map
kubectl create configmap cra-config \
  --from-literal=redis-url=redis://cra-sessions.xxxxx.ng.0001.use1.cache.amazonaws.com:6379

# Deploy
kubectl apply -f deployment.yaml

# Verify pods are running
kubectl get pods -l app=cra-api
# NAME                      READY   STATUS    RESTARTS
# cra-api-abc123def-xyz     1/1     Running   0
# cra-api-abc123def-uvw     1/1     Running   0
```

### Step 4: Parallel Running (Both Systems Active)
```
OLD System:                NEW System:
┌─────────────────────────┐ ┌─────────────────────────┐
│ ALB                     │ │ Kubernetes Ingress      │
│ app.cra-compliance.com  │ │ k8s.cra-compliance.com  │
└─────────────────────────┘ └─────────────────────────┘
    ↓                            ↓
EC2 Instance 1             K8s Pod 1
EC2 Instance 2             K8s Pod 2
    ↓                            ↓
  RDS Database ←─────────────────┘
  Redis Cache  ←─────────────────┘
```

### Step 5: Gradual Traffic Shift
```bash
# Update DNS to point to both (via weighted routing)
# 90% → ALB (old)
# 10% → K8s (new)

# Or use AWS Route53 weighted routing
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123ABC \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "app.cra-compliance.com",
          "Type": "A",
          "SetIdentifier": "ALB-90",
          "Weight": 90,
          "AliasTarget": {
            "HostedZoneId": "Z35SXDOTRQ7X7K",
            "DNSName": "cra-alb-xxx.us-east-1.elb.amazonaws.com",
            "EvaluateTargetHealth": true
          }
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "app.cra-compliance.com",
          "Type": "A",
          "SetIdentifier": "K8s-10",
          "Weight": 10,
          "AliasTarget": {
            "HostedZoneId": "XXXXXX",
            "DNSName": "cra-k8s-xxx.us-east-1.elb.amazonaws.com",
            "EvaluateTargetHealth": true
          }
        }
      }
    ]
  }'

# Monitor error rates on K8s
kubectl logs -f deployment/cra-api --tail=50

# Gradually shift more traffic
# 50% ALB / 50% K8s
# 20% ALB / 80% K8s
# 0% ALB / 100% K8s (after 24 hours)
```

### Step 6: Verify K8s Health
```bash
# Check all pods are healthy
kubectl get pods -l app=cra-api
# All should be Ready and Running

# Check logs for errors
kubectl logs -l app=cra-api --tail=100 | grep ERROR
# Should be empty (or same error rate as old system)

# Run smoke tests against K8s endpoint
./tests/smoke_test.sh --instance k8s.cra-compliance.com

# Check resource usage
kubectl top pods -l app=cra-api
# NAME                    CPU(m)  MEMORY(Mi)
# cra-api-abc123-xyz      50      150
# cra-api-abc123-uvw      45      145
```

### Step 7: Rollback (If Issues)
```bash
# If K8s has problems:

# 1. Update DNS weights back to 100% ALB
aws route53 change-resource-record-sets ... \
  --change-batch '{weight: 100 for ALB, 0 for K8s}'

# 2. Verify old system gets all traffic
curl app.cra-compliance.com/health

# 3. Scale down K8s (but keep running for investigation)
kubectl scale deployment cra-api --replicas=0

# 4. Debug K8s issues separately
# 5. Keep old EC2 instances running for 48 hours before deleting

# 6. Once confident in K8s, delete old instances
aws ec2 terminate-instances --instance-ids i-xxx i-yyy
```

---

## Database Schema Migrations (For All Stages)

**Problem**: Adding a new column breaks old code if not handled properly.

**Solution**: Deploy code BEFORE schema changes.

### Example: Add `assessment_methodology` Column

### Phase 1: Code Supports Both Old & New (2 hours before DB change)
```python
# OLD schema: no methodology column
# NEW schema: has methodology column

# Code handles both:
class AssessmentCreate(BaseModel):
    alters_intended_use: bool
    increases_cybersecurity_risk: bool
    changes_hazard_nature: bool
    expands_attack_surface: bool
    methodology: str | None = None  # NEW field, optional

# When saving to DB:
assessment = SubstantialModificationAssessment(
    ...
    methodology=payload.methodology if hasattr(payload, 'methodology') else None,
)
```

### Phase 2: Run Database Migration
```bash
# During lowest-traffic window (2am-4am)
cd backend
alembic upgrade head

# Migration script:
def upgrade():
    op.add_column('substantial_modification_assessments', 
        sa.Column('methodology', sa.String(50), nullable=True)
    )

# Old code still works (methodology will be NULL)
# New code sets methodology on new records
```

### Phase 3: Deploy Code (2 hours after DB change)
```bash
# Old code: Can still read/write (methodology ignored or NULL)
# New code: Can read/write methodology

# Gradual deployment across instances ensures backward compatibility
```

---

## Feature Flags for Rollback

For complex features, use feature flags instead of code branches:

```python
# features.py
FEATURE_FLAGS = {
    "database_per_tenant": False,  # Disabled for MVP
    "advanced_sbom_diffing": True,
    "kubernetes_deployment": False,
}

# routes/changes.py
@router.get("/changes/{id}")
async def get_change(id: UUID, db: Session):
    change = db.query(Change).filter_by(id=id).first()
    
    # Only call new feature if enabled
    if FEATURE_FLAGS["advanced_sbom_diffing"]:
        change.sbom_diff = advanced_sbom_diff(change)
    
    return change
```

**Enable/disable without deploying:**
```bash
# Store flags in database or config service
UPDATE feature_flags 
SET enabled=true 
WHERE name='database_per_tenant';

# Or use environment variables
export FEATURE_FLAGS='{"database_per_tenant": true, "kubernetes": true}'
```

---

## Monitoring During Migrations

### Key Metrics to Watch
```
1. Error Rate
   - Should stay <1% during migration
   - If >2%, trigger rollback

2. Latency (p95)
   - Should stay <2 seconds
   - If >5s, investigate resource constraints

3. Connection Pool
   - Old: Should drain gradually
   - New: Should fill gradually
   - Never hit max connections

4. Session Consistency
   - Log in on instance 1
   - Request data on instance 2
   - Should work (session persists)

5. Database Locks
   - Monitor for long-running queries
   - Schema changes can cause locks
```

### Alert Setup
```bash
# CloudWatch alarm: Error rate > 2%
aws cloudwatch put-metric-alarm \
  --alarm-name cra-error-rate-high \
  --alarm-description "Alert if error rate exceeds 2%" \
  --metric-name ErrorRate \
  --namespace CRACompliance \
  --statistic Average \
  --period 300 \
  --threshold 2 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789:alerts
```

---

## Quick Reference: Migration Checklist

### Before Any Migration
- [ ] Full database backup
- [ ] Verify backup can be restored (test restore to staging)
- [ ] Notify customers of maintenance window
- [ ] Have rollback procedure documented
- [ ] Schedule on-call engineer
- [ ] Test in staging environment first

### During Migration
- [ ] Monitor error rates every 30 seconds
- [ ] Monitor database connections
- [ ] Check log files for warnings/errors
- [ ] Verify customer-facing features work
- [ ] Run smoke tests on both old and new systems

### After Migration
- [ ] Monitor for 24 hours
- [ ] Check for delayed errors (async jobs)
- [ ] Verify backups still work
- [ ] Update documentation
- [ ] Post-mortem (what went well, what to improve)

---

## Example: Complete Migration Script

```bash
#!/bin/bash
# migrate.sh - Automate Stage 2 → Stage 3 migration

set -e  # Exit on error

STAGE="3"
OLD_INSTANCE="i-xxx"
NEW_INSTANCE="i-yyy"
ALB_ARN="arn:aws:elasticloadbalancing:..."

echo "Starting migration to Stage $STAGE..."

# 1. Backup database
echo "Creating database backup..."
aws rds create-db-snapshot \
  --db-instance-identifier cra-prod \
  --db-snapshot-identifier cra-prod-pre-migration-$(date +%s)

# 2. Launch new instance
echo "Launching new instance..."
NEW_ID=$(aws ec2 run-instances \
  --image-id ami-xxx \
  --instance-type t3.large \
  --query 'Instances[0].InstanceId' \
  --output text)

# 3. Deploy code to new instance
echo "Deploying code to new instance..."
ssh -i ~/.ssh/id_rsa ubuntu@$NEW_ID << 'DEPLOY'
  git clone https://github.com/myorg/cra-compliance-tool.git
  cd cra-compliance-tool/backend
  ./scripts/deploy.sh
DEPLOY

# 4. Health check
echo "Running health checks..."
for i in {1..30}; do
  if curl -f http://$NEW_ID:8000/health > /dev/null 2>&1; then
    echo "✓ New instance is healthy"
    break
  fi
  echo "Waiting for new instance... ($i/30)"
  sleep 10
done

# 5. Register with ALB
echo "Registering new instance with ALB..."
aws elbv2 register-targets \
  --target-group-arn $ALB_ARN \
  --targets Id=$NEW_ID

# 6. Gradual traffic shift
echo "Shifting traffic to new instance..."
for weight in 10 25 50 75 100; do
  echo "  Traffic: $weight% to new instance"
  sleep 5 * 60  # Wait 5 minutes between shifts
  
  # Check error rate
  ERROR_RATE=$(aws cloudwatch get-metric-statistics \
    --metric-name ErrorRate \
    --namespace CRACompliance \
    --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Average \
    --query 'Datapoints[0].Average')
  
  if (( $(echo "$ERROR_RATE > 2" | bc -l) )); then
    echo "✗ Error rate too high ($ERROR_RATE%). Rolling back..."
    # Shift traffic back to old instance
    # ... rollback code ...
    exit 1
  fi
done

# 7. Decommission old instance
echo "Decommissioning old instance..."
aws elbv2 deregister-targets \
  --target-group-arn $ALB_ARN \
  --targets Id=$OLD_INSTANCE

aws ec2 stop-instances --instance-ids $OLD_INSTANCE

echo "✓ Migration to Stage $STAGE complete!"
```

---

## Summary

**Zero-downtime migration is possible for:**
- ✅ Upgrading instance size (same code, more resources)
- ✅ Adding load balancer (traffic shift via DNS)
- ✅ Moving to Kubernetes (container-based, easy to replicate)
- ✅ Adding new database replicas (asynchronous, read-only)
- ✅ Changing storage (S3 supports parallel writes from both old and new)

**Key principles:**
1. **Deploy code BEFORE schema changes** (code handles both old and new)
2. **Gradual traffic shift** (10% → 50% → 100% over hours, not seconds)
3. **Keep old system running** (for instant rollback if needed)
4. **Monitor error rates** (automated rollback if threshold exceeded)
5. **Test in staging first** (never migrate production first)

This approach ensures existing customers never experience downtime, errors, or data loss during scaling transitions.
