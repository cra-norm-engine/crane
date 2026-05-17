# Phase D API Endpoint Specification

Complete reference for all new Phase D endpoints with request/response examples.

## Assessment Template Endpoints

### GET /changes/assessment-templates/{methodology}

Returns the question bank for a given threat assessment methodology.

**Parameters:**
- `methodology` (path): `"stride"` or `"tara"`

**Response (200 OK):**
```json
{
  "methodology": "stride",
  "questions": [
    {
      "id": "S1",
      "text": "Could this change allow impersonation of users, services, or components?",
      "threat_category": "Spoofing",
      "cra_criteria_key": "increases_cybersecurity_risk",
      "hint": "E.g. bypassing authentication, weakening identity verification"
    },
    ...6 total for STRIDE, 4 total for TARA
  ]
}
```

**Expected Behavior:**
- STRIDE returns 6 questions (S1-S6)
- TARA returns 4 questions (T1-T4)
- Each question maps to one of 4 CRA Article 3(3)(c) criteria
- Hints are provided for user context

---

### GET /changes/{change_id}/recommended-actions

Returns compliance actions recommended based on the change's assessment outcome.

**Parameters:**
- `change_id` (path): UUID of the change

**Response (200 OK):**
```json
{
  "change_id": "550e8400-e29b-41d4-a716-446655440000",
  "change_type": "feature",
  "is_assessed": true,
  "is_substantial": true,
  "recommended_actions": [
    "Conduct risk assessment (STRIDE/TARA)",
    "Update hazard analysis",
    "Review threat model",
    "Test against compliance profile",
    "Document security change rationale",
    "Notify relevant competent authorities if applicable"
  ]
}
```

**Expected Behavior:**
- Returns empty list if change not yet assessed
- Security-type changes return: ["Review for regression risk", "Run full test suite"] (never substantial)
- Substantial changes get full compliance action list
- Non-substantial changes get minimal action list

**Error Cases:**
- 404: Change not found
- 403: Insufficient permissions (requires change_read)

---

## Certification Evidence Endpoints

### POST /certification-records/{record_id}/evidence

Link an existing artifact revision to a certification record as evidence.

**Path Parameters:**
- `record_id`: UUID of the certification record

**Request Body:**
```json
{
  "artifact_revision_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "product_id": "550e8400-e29b-41d4-a716-446655440001",
  "certification_scheme": "eu_cybersecurity_act",
  "certification_body_name": "Example Cert Body",
  "status": "active",
  ...other certification fields...,
  "artifact_links": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "artifact_revision": {
        "id": "550e8400-e29b-41d4-a716-446655440003",
        "artifact_id": "550e8400-e29b-41d4-a716-446655440004",
        "revision_number": 2,
        "source_type": "upload",
        "original_filename": "test_report.pdf",
        "file_size_bytes": 2048576,
        "sha256": "abc123def456...",
        "created_at": "2026-05-17T10:30:00Z"
      },
      "linked_by_user_id": "550e8400-e29b-41d4-a716-446655440005"
    }
  ]
}
```

**Expected Behavior:**
- Creates a unique constraint preventing duplicate revision links
- Emits audit event: "evidence_attached"
- Returns updated certification record with artifact_links populated

**Error Cases:**
- 404: Record or artifact revision not found
- 400: Duplicate link (same revision already linked)
- 403: Insufficient permissions (requires certification_record_write)

---

### POST /certification-records/{record_id}/evidence/upload

Upload a new artifact file and automatically link it to the certification record.

**Path Parameters:**
- `record_id`: UUID of the certification record

**Form Parameters:**
- `title` (required): Name/title of the artifact
- `artifact_type` (required): `"document"`, `"test_report"`, `"certificate"`, or `"audit"`
- `description` (optional): Extended description
- `change_summary` (optional): Summary of changes in this revision
- `upload` (required, file): Binary file content

**Response (200 OK):**
Same as POST /evidence above, with new artifact linked.

**Expected Behavior:**
- Calls artifact_service.upload_artifact() internally
- Automatically links the uploaded artifact's latest revision
- Emits audit event: "evidence_uploaded_attached"
- Returns updated certification record

**Error Cases:**
- 400: Missing required fields or invalid artifact_type
- 413: File too large
- 403: Insufficient permissions

---

### DELETE /certification-records/{record_id}/evidence/{link_id}

Remove an evidence link from a certification record.

**Path Parameters:**
- `record_id`: UUID of the certification record
- `link_id`: UUID of the evidence link to remove

**Response (200 OK):**
Updated certification record with the link removed from artifact_links array.

**Expected Behavior:**
- Removes the specific link (artifact revision can still exist elsewhere)
- Emits audit event: "evidence_removed"
- Returns updated certification record

**Error Cases:**
- 404: Record or link not found
- 400: Link does not belong to this record
- 403: Insufficient permissions

---

## Release Gate Prerequisite Endpoints

### POST /product-releases/{release_id}/gate/prerequisites

Add a prerequisite dependency between two gate items (item B cannot be accepted until item A is resolved).

**Path Parameters:**
- `release_id`: UUID of the product release

**Request Body:**
```json
{
  "dependent_item_id": "550e8400-e29b-41d4-a716-446655440001",
  "prerequisite_item_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "dependent_item_id": "550e8400-e29b-41d4-a716-446655440001",
  "prerequisite_item_id": "550e8400-e29b-41d4-a716-446655440002",
  "created_at": "2026-05-17T10:30:00Z"
}
```

**Expected Behavior:**
- Creates unique constraint preventing duplicate edges
- Dependent item's status becomes "blocked" if prerequisite is not "accepted"
- Emits audit event: "prerequisite_added"

**Error Cases:**
- 404: Item(s) not found
- 400: Self-dependency or duplicate edge
- 403: Insufficient permissions (requires release_lifecycle_write)

---

### DELETE /product-releases/{release_id}/gate/prerequisites

Remove a prerequisite dependency.

**Path Parameters:**
- `release_id`: UUID of the product release

**Request Body:**
```json
{
  "dependent_item_id": "550e8400-e29b-41d4-a716-446655440001",
  "prerequisite_item_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

**Response (204 No Content)** or **(200 OK)** depending on implementation.

**Expected Behavior:**
- Removes the prerequisite edge
- Dependent item's status is re-evaluated (may become unblocked)
- Emits audit event: "prerequisite_removed"

**Error Cases:**
- 404: Edge not found
- 403: Insufficient permissions

---

### GET /product-releases/{release_id}/gate/prerequisites

Fetch all prerequisite edges for a release gate.

**Path Parameters:**
- `release_id`: UUID of the product release

**Query Parameters:**
- None

**Response (200 OK):**
```json
[
  {
    "dependent_item_id": "550e8400-e29b-41d4-a716-446655440001",
    "prerequisite_item_id": "550e8400-e29b-41d4-a716-446655440002",
    "created_at": "2026-05-17T10:30:00Z"
  },
  ...more edges...
]
```

**Expected Behavior:**
- Returns all edges for the gate
- Empty array if no prerequisites set

---

## Release Gate Snapshot Endpoint

### GET /product-releases/{release_id}/gate/snapshot

Fetch the compliance snapshot captured at the time of gate approval.

**Path Parameters:**
- `release_id`: UUID of the product release

**Response (200 OK):**
```json
{
  "approved_at": "2026-05-17T10:30:00Z",
  "approved_by": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "code": "sbom",
      "title": "Software Bill of Materials",
      "status": "accepted",
      "evidence": [
        {
          "artifact_title": "CycloneDX SBOM 1.0",
          "revision_number": 2,
          "sha256": "abc123def456...",
          "decision": "approved",
          "reviewed_by": "550e8400-e29b-41d4-a716-446655440001"
        }
      ]
    },
    ...more items...
  ],
  "bundle_sha256": "fedcba987654..."
}
```

**Expected Behavior:**
- Only available after gate is approved
- Returns frozen state at approval time
- Includes all items and their evidence with SHA-256 for integrity verification

**Error Cases:**
- 404: Release or gate not found
- 400: Gate not yet approved (no snapshot exists)

---

## Integration Testing Workflow

### Test Scenario 1: Complete Assessment Workflow

```bash
# 1. Get STRIDE questions
GET /changes/assessment-templates/stride

# 2. Create a change (not shown here, assume change_id = abc123)

# 3. Submit assessment with STRIDE answers
POST /changes/abc123/assess
{
  "alters_intended_use": false,
  "increases_cybersecurity_risk": true,
  "changes_hazard_nature": false,
  "expands_attack_surface": false,
  "methodology": "stride",
  "template_answers": {
    "S1": false,
    "S2": true,
    "S3": false,
    "S4": false,
    "S5": false,
    "S6": false
  }
}

# 4. Get recommended actions
GET /changes/abc123/recommended-actions
# Should return: is_substantial=true with full compliance action list

# 5. Test with security change type
# Create change with change_type="security", then assess
# Result: is_substantial should always be false (CRA Art. 3(4))
```

### Test Scenario 2: Evidence Attachment Workflow

```bash
# 1. Create certification record (assume record_id = def456)

# 2. Upload evidence
POST /certification-records/def456/evidence/upload
(multipart form with file, title="Test Report", artifact_type="test_report")

# 3. Verify evidence appears in detail
GET /certification-records/def456
# Should have artifact_links array with 1 item

# 4. Link additional existing artifact revision
POST /certification-records/def456/evidence
{
  "artifact_revision_id": "existing-revision-uuid"
}
# Should have 2 items in artifact_links

# 5. Remove evidence
DELETE /certification-records/def456/evidence/{link_id}
# Should have 1 item again
```

### Test Scenario 3: Prerequisite Workflow

```bash
# 1. Create release with gate items (assume release_id = ghi789)

# 2. Set prerequisite: item_b depends on item_a
POST /product-releases/ghi789/gate/prerequisites
{
  "dependent_item_id": "item_b_uuid",
  "prerequisite_item_id": "item_a_uuid"
}

# 3. Check prerequisites
GET /product-releases/ghi789/gate/prerequisites
# Should show the edge

# 4. Try to accept item_b while item_a is pending
# Should fail or return "blocked" status

# 5. Accept item_a, then accept item_b
# Both should succeed

# 6. Remove prerequisite
DELETE /product-releases/ghi789/gate/prerequisites
{
  "dependent_item_id": "item_b_uuid",
  "prerequisite_item_id": "item_a_uuid"
}
```

### Test Scenario 4: CRA Art. 3(4) Enforcement

```bash
# Test that security changes are NEVER substantial

# 1. Create change with change_type="security"
POST /changes
{
  "product_id": "...",
  "change_type": "security",
  ...
}

# 2. Assess with all criteria marked as yes
POST /changes/{id}/assess
{
  "alters_intended_use": true,
  "increases_cybersecurity_risk": true,
  "changes_hazard_nature": true,
  "expands_attack_surface": true
}

# 3. Verify result
GET /changes/{id}
# assessment.is_substantial should be FALSE despite all criteria being true

# 4. Get recommendations
GET /changes/{id}/recommended-actions
# Should return: ["Review for regression risk", "Run full test suite"]
# NOT the full substantial modification action list
```

---

## Permission Requirements

| Endpoint | Required Permission |
|----------|-------------------|
| GET /changes/assessment-templates/{methodology} | change_read |
| GET /changes/{id}/recommended-actions | change_read |
| POST /certification-records/{id}/evidence | certification_record_write |
| POST /certification-records/{id}/evidence/upload | certification_record_write |
| DELETE /certification-records/{id}/evidence/{link_id} | certification_record_write |
| POST /product-releases/{id}/gate/prerequisites | release_lifecycle_write |
| DELETE /product-releases/{id}/gate/prerequisites | release_lifecycle_write |
| GET /product-releases/{id}/gate/prerequisites | release_read |
| GET /product-releases/{id}/gate/snapshot | release_read |

---

## Audit Events Emitted

All evidence and prerequisite operations emit audit events:

| Operation | Audit Action | Entity Type | Details |
|-----------|-------------|-------------|---------|
| Evidence attached | `update` | `certification_record` | `{action: "evidence_attached", revision_id: "..."}` |
| Evidence uploaded & attached | `update` | `certification_record` | `{action: "evidence_uploaded_attached", artifact_id: "..."}` |
| Evidence removed | `update` | `certification_record` | `{action: "evidence_removed", link_id: "..."}` |
| Prerequisite added | `update` | `release_gate` | `{action: "prerequisite_added", ...}` |
| Prerequisite removed | `update` | `release_gate` | `{action: "prerequisite_removed", ...}` |

---

## Common Error Responses

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid request body or parameters"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Database Constraints Enforced

- **release_gate_item_prerequisites**: Unique constraint on (dependent_item_id, prerequisite_item_id)
- **certification_record_artifact_links**: Unique constraint on (certification_record_id, artifact_revision_id)
- Both tables have CASCADE delete on certification_record/release_gate, RESTRICT on artifact_revision/user

---

## Notes for Testers

1. All endpoints require valid authentication tokens
2. Timestamps are ISO 8601 format with timezone
3. UUIDs are in standard hyphenated format
4. Soft-deleted records should not appear in responses
5. Pagination not yet implemented for endpoint list responses
6. Batch operations not supported (add one prerequisite or link at a time)
