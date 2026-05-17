# Phase D Frontend Testing Guide

Step-by-step test scenarios for all new Phase D UI components and features.

## Test Environment Setup

```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
# Opens at http://localhost:5173
```

## Component 1: AssessmentWizard

**Location**: Change Detail View → "Assess Change" button

### Test 1.1: STRIDE Methodology Flow

**Steps:**
1. Navigate to a change in `under_review` status
2. Click "Assess Change" button
3. Select "STRIDE" card
4. Click "Continue"

**Expected Result:**
- Step 2 loads with progress bar "Question 1 of 6"
- First question (S1: Spoofing) displays with:
  - Question text
  - Threat category: "Spoofing"
  - CRA criteria label: "Increases cybersecurity risk"
  - Hint text visible
  - Three radio options: Yes/No/Unsure

**Test 1.1a: Navigation**
1. Click "Next" button
2. Verify progress updates to "Question 2 of 6"
3. Previous button is now enabled
4. Click "Previous"
5. Return to S1 question

**Expected Result:**
- Navigation buttons work correctly
- Progress bar updates
- Selected answer is preserved when returning

**Test 1.1b: Review Step**
1. Answer all 6 STRIDE questions (mix of Yes/No/Unsure)
2. Click "Review" on last question
3. Step 3 displays

**Expected Result:**
- Answers Summary grid shows all 6 questions with selected values
- CRA Article 3(3)(c) Criteria section shows:
  - 4 checkboxes for the criteria
  - Checkmarks only on criteria met by "Yes" answers
- Substantiality badge shows "Substantial Modification" or "Non-Substantial Change"
- Optional reasoning textarea is visible

**Test 1.1c: Submit**
1. Enter optional reasoning text
2. Click "Submit Assessment"
3. Wait for loading state

**Expected Result:**
- Button shows "Submitting…" state
- Request goes to POST `/changes/{id}/assess`
- Payload includes:
  - `methodology: "stride"`
  - `template_answers: {S1: false, S2: true, ...}`
  - Other assessment fields
- Modal closes
- Success message displays: "Assessment recorded. Change is [substantial/not substantial]."
- Change detail view reloads with updated assessment

### Test 1.2: TARA Methodology Flow

**Steps:**
1. Navigate to another change
2. Click "Assess Change"
3. Select "TARA" card
4. Click "Continue"

**Expected Result:**
- Step 2 shows "Question 1 of 4"
- First question (T1: Asset Identification)
- All other behavior matches STRIDE

**Expected Result (Review Step):**
- Only 4 questions appear in the grid
- Same criteria mapping applies

### Test 1.3: Manual/Custom Assessment

**Steps:**
1. Navigate to another change
2. Click "Assess Change"
3. Select "Manual Assessment" card
4. Click "Continue"

**Expected Result:**
- Skips directly to Step 3 (Review)
- No questions appear
- Can manually select criteria checkboxes

**Expected Result (Submit):**
- `methodology: "custom"` in payload
- No template_answers (only explicit criteria values)

### Test 1.4: CRA Article 3(4) Enforcement

**Setup:** Create or find a change with `change_type: "security"`

**Steps:**
1. Open the security-type change
2. Click "Assess Change"
3. Select STRIDE, answer "Yes" to ALL questions
4. Review step should show ALL criteria marked as met
5. Click Submit

**Expected Result:**
- Assessment shows "Non-Substantial Change" badge (NOT "Substantial Modification")
- Audit log shows change.is_substantial = false
- Recommended actions are: ["Review for regression risk", "Run full test suite"]

**Why This Matters:**
- CRA Article 3(4) mandates that security fixes can never be substantial modifications
- The system must enforce this regardless of the criteria answers

### Test 1.5: Error Handling

**Steps:**
1. Open the assessment wizard
2. Select STRIDE
3. Answer some questions
4. Disconnect network (DevTools → Offline)
5. Click "Next" on a question

**Expected Result:**
- Error message displays
- "Submitting…" button state clears
- Can retry after reconnecting network

**Test 1.5b: Invalid Change ID**
1. Manually modify URL to invalid change ID
2. Click "Assess Change"

**Expected Result:**
- Error message: "Failed to load assessment templates"
- Modal shows graceful error state

---

## Component 2: Certification Evidence Section

**Location**: Certification Records → Detail Modal → Evidence Section

### Test 2.1: Evidence Display

**Setup:** Open or create a certification record

**Steps:**
1. Scroll down in detail modal to "Evidence" section
2. Verify section shows evidence count badge

**Expected Result:**
- If no evidence: "No evidence attached yet"
- If evidence exists: List shows each piece with:
  - Filename
  - Revision number
  - Artifact type (document/test_report/certificate/audit)
  - File size
  - Three action buttons: Download / Open Link / Remove

### Test 2.2: Upload Evidence

**Steps:**
1. In Evidence section, click "Upload Evidence" button
2. Form appears with fields:
   - Title (required, text input)
   - Artifact Type (required, dropdown)
   - Description (optional, textarea)
3. Select a test PDF file
4. Enter title: "Test Report V1"
5. Select type: "test_report"
6. Enter description: "Initial test findings"
7. Click "Upload"

**Expected Result:**
- Upload button shows "Uploading…" state
- After success, form closes
- Evidence appears in list with proper metadata
- File size is formatted (e.g., "2.5 MB")

**Test 2.2a: Type Selection**
1. Click on Artifact Type dropdown
2. Verify options: document, test_report, certificate, audit

**Test 2.2b: Large File Upload**
1. Select a file > 100MB
2. Attempt upload

**Expected Result:**
- Either shows error (file too large) or uploads successfully
- No hanging or incomplete states

### Test 2.3: Download Evidence

**Steps:**
1. In evidence list, click "Download" button on first item
2. Browser download begins

**Expected Result:**
- File downloads with correct filename
- File size matches original
- File content is intact

**Test 2.3a: Download External Link**
1. Add evidence that's an external link (source_type = "external_link")
2. Click download button

**Expected Result:**
- Browser opens the external_url in a new tab
- Does not trigger file download

### Test 2.4: Remove Evidence

**Steps:**
1. Click "Remove" button on an evidence item
2. Confirmation dialog appears

**Expected Result:**
- Dialog shows: "Remove this evidence?"
3. Click "Confirm"

**Expected Result:**
- Evidence is removed from list
- Success message shows briefly
- Audit log shows `certification_record.evidence_removed`

### Test 2.5: Evidence Type Icons/Labels

**Steps:**
1. Add multiple evidence items with different types
2. Verify each shows correct type label

**Expected Result:**
- document → "Document"
- test_report → "Test Report"
- certificate → "Certificate"
- audit → "Audit"
- Labels are consistent with form options

---

## Component 3: Release Gate Detail Tabs

**Location**: Release Gate View → Item Detail Panel

### Test 3.1: Tab Navigation

**Setup:** Open a release gate and select an item to view details

**Steps:**
1. Verify 5 tabs appear: Evidence, History, Diff, Dependencies, Snapshot
2. Click each tab in order

**Expected Result:**
- Content changes for each tab
- Tab highlight indicates active tab
- Content doesn't reload when switching (smooth transition)

### Test 3.2: Evidence Tab

**Steps:**
1. Click "Evidence" tab
2. Verify linked artifacts display with review panels

**Expected Result:**
- Shows existing evidence display (pre-Phase D functionality)
- Review decision status visible
- Content matches existing behavior

### Test 3.3: History Tab

**Setup:** Item must have at least one linked artifact with revisions

**Steps:**
1. Click "History" tab
2. Wait for loading (spinner should show briefly)

**Expected Result:**
- Tab shows artifact title: "[Artifact Name]"
- Meta line: "sbom · 3 revisions"
- Revision list with cards showing:
  - Revision number (Rev 1, Rev 2, Rev 3)
  - Upload date
  - Uploader name
  - File size
  - Source type (upload/external_link)
  - SHA-256 truncated (first 12 chars)

**Test 3.3a: Revision Details**
1. Hover over SHA-256 field

**Expected Result:**
- Tooltip shows full SHA-256 hash (or copy button appears)

**Test 3.3b: Empty History**
1. For item with no linked artifact

**Expected Result:**
- Tab shows: "No artifact linked to this item yet."
- Loading state doesn't appear

### Test 3.4: SBOM Diff Tab

**Setup:** Item must have code = "sbom" AND have an uploaded SBOM with analysis

**Steps:**
1. Click "Diff" tab
2. Wait for loading

**Expected Result:**
- If no SBOM record: "No SBOM diff available"
- If SBOM exists: SbomDiffPanel component displays
  - Summary chips: "Added: X · Changed: Y · Removed: Z"
  - Three collapsible sections: Added, Changed, Removed
  - Each component shows with:
    - Name
    - Version
    - License (if available)
    - Type (library, framework, etc.)

**Test 3.4a: Expand Sections**
1. Click "Added" section header
2. List expands showing all added components

**Expected Result:**
- Components display in a readable list
- Can collapse/expand sections independently

**Test 3.4b: SBOM Diff Not Available**
1. For item without code="sbom"

**Expected Result:**
- Diff tab is hidden (or shows "Not applicable for this item type")

### Test 3.5: Dependencies Tab

**Steps:**
1. Click "Dependencies" tab
2. Wait for loading

**Expected Result:**
- Visual dependency graph appears
- Shows all gate items as nodes
- Prerequisite edges shown as arrows

**Test 3.5a: Node Details**
1. Verify each node shows:
   - Gate item code (sbom, architecture, etc.)
   - Item status badge (green/amber/red)
   - Title

**Test 3.5b: Edge Visualization**
1. If prerequisites set: arrows point from prerequisite → dependent

**Expected Result:**
- Blocked items show red status
- Dependency chain is visually clear

**Test 3.5c: Add Prerequisite (if canWrite)**
1. For a gate item, click "Add prerequisite" link
2. Dropdown appears showing other items

**Expected Result:**
- Can select another item to set as prerequisite
- Dependency edge is created

**Test 3.5d: Remove Prerequisite (if canWrite)**
1. Click × on a prerequisite edge

**Expected Result:**
- Edge is removed
- Dependent item status updates (unblocks if needed)

### Test 3.6: Snapshot Tab

**Setup:** Gate must be in "approved" status

**Steps:**
1. Click "Snapshot" tab
2. Tab loads

**Expected Result:**
- If not approved: Tab hidden or shows "No snapshot available"
- If approved: Shows frozen compliance state:
  - "Approved at: 2026-05-17 10:30:00 UTC"
  - "Approved by: [User Name]"
  - For each item:
    - Item code and title
    - Status at approval time
    - Evidence list with:
      - Artifact title
      - Revision number
      - SHA-256
      - Decision (approved/rejected/etc.)
      - Reviewer name
  - Bundle SHA-256 at bottom

**Test 3.6a: Download Bundle**
1. Click "Download Bundle" button

**Expected Result:**
- ZIP file downloads with compliance artifacts

---

## Component 4: SbomDiffPanel

**Location**: Release Gate View → Detail Panel → SBOM Diff Tab, OR SbomRecordsView → Detail

### Test 4.1: Basic Rendering

**Setup:** Have an SBOM record with analysis_findings.diff

**Steps:**
1. View the Diff tab or SBOM record detail
2. SbomDiffPanel component renders

**Expected Result:**
- Summary bar shows: "Added: X · Changed: Y · Removed: Z"
- Three collapsible sections below
- Sections can be expanded/collapsed independently

### Test 4.2: Added Components

**Steps:**
1. Click "Added" section header

**Expected Result:**
- Lists all components in analysis_findings.diff.added
- Each shows: name, version, type, license
- Components grouped or sorted logically

### Test 4.3: Changed Components

**Steps:**
1. Click "Changed" section header

**Expected Result:**
- For each changed component:
  - Name and before/after versions
  - Highlight what changed (bold/color)
  - License, type, etc.

### Test 4.4: Removed Components

**Steps:**
1. Click "Removed" section header

**Expected Result:**
- Lists removed components with:
  - Name, version that was removed
  - Type, license info
  - Strikethrough or faded styling

---

## Component 5: Type-Checking & Compilation

### Test 5.1: No TypeScript Errors

**Steps:**
1. Run: `cd frontend && npm run type-check`

**Expected Result:**
```
✓ 0 errors in Phase D files:
  - src/components/AssessmentWizard.vue ✓
  - src/components/SbomDiffPanel.vue ✓
  - src/views/ReleaseGateView.vue ✓
  - src/views/CertificationRecordsView.vue ✓
  - src/views/ChangeDetailView.vue ✓

Note: 18 pre-existing errors in other files (unrelated to Phase D)
```

### Test 5.2: Production Build

**Steps:**
1. Run: `npm run build`
2. Wait for build to complete

**Expected Result:**
- No build errors
- `dist/` directory created with optimized bundles
- All Phase D code is included in minified output

---

## Cross-Component Integration Tests

### Integration Test 1: End-to-End Assessment & Actions

**Scenario**: Assess a substantial change and verify recommended actions appear

**Steps:**
1. Create a new change
2. Click "Assess Change"
3. Select STRIDE methodology
4. Answer questions to trigger substantiality
5. Submit assessment
6. Navigate to change detail page
7. Verify:
   - Assessment summary shows "Substantial"
   - Recommended actions panel shows compliance action checklist

### Integration Test 2: Evidence Trail in Multiple Views

**Scenario**: Upload evidence to certification, verify it appears in audit timeline

**Steps:**
1. Create certification record
2. Upload evidence file
3. In audit timeline (if visible), verify:
   - Event shows "certification_record.evidence_uploaded_attached"
   - Timestamp and uploader are correct
4. In certification detail, evidence appears in list
5. In artifact detail, revision shows linked to certification

### Integration Test 3: Gate Dependencies & Blocking

**Scenario**: Set prerequisites and verify blocking works

**Steps:**
1. Create release gate with 3 items
2. Set item_b depends on item_a, item_c depends on item_b
3. Try to accept item_b while item_a is pending
4. Verify error or "blocked" status
5. Accept item_a, then item_b becomes unblocked
6. Verify dependency visualization shows chain

### Integration Test 4: Snapshot & Rollback Scenario

**Scenario**: Approve gate, view frozen snapshot, then modify items

**Steps:**
1. Create and fill gate with evidence
2. Submit for review, then approve
3. Snapshot captured
4. View snapshot tab - shows frozen state
5. Remove evidence from an item
6. View snapshot again - still shows original state
7. Verify current state differs from snapshot

---

## Performance Tests

### Test P.1: Large File Upload

**Steps:**
1. Upload 500MB SBOM file to evidence

**Expected Result:**
- Upload progresses without hanging
- Completion time < 2 minutes
- File integrity verified via SHA-256

### Test P.2: Many Prerequisites

**Setup:** Create gate with 10+ items and set 5+ prerequisites

**Steps:**
1. Open Dependencies tab
2. Observe load time

**Expected Result:**
- Tab loads within 1 second
- Graph renders smoothly
- No lag when clicking edges

### Test P.3: Wizard with Many Questions

**Setup:** Future scenario with 20+ STRIDE questions

**Steps:**
1. Open assessment wizard
2. Rapidly click through questions

**Expected Result:**
- Smooth navigation
- No UI freezing
- Questions load from API without delay

---

## Accessibility Tests

### Test A.1: Keyboard Navigation

**Steps:**
1. In AssessmentWizard, use Tab key to navigate
2. Use Enter to select radio options
3. Use arrow keys if implemented

**Expected Result:**
- All interactive elements are keyboard accessible
- Focus indicators are visible
- No keyboard traps

### Test A.2: Screen Reader

**Steps:**
1. Use screen reader (NVDA/JAWS/VoiceOver)
2. Navigate through Assessment Wizard
3. Read question and options

**Expected Result:**
- Question text is read aloud
- Radio labels are associated
- Progress indicator is announced
- Button states are clear

### Test A.3: Color Contrast

**Steps:**
1. Use color contrast analyzer
2. Check:
   - Substantiality badge colors
   - Tab active indicator
   - Prerequisite edges in graph

**Expected Result:**
- All text meets WCAG AA standards (4.5:1)
- No critical colors are the only distinguisher

---

## Regression Tests

### Test R.1: Existing Evidence Tab Still Works

**Steps:**
1. On Release Gate, open item with linked evidence
2. Click "Evidence" tab

**Expected Result:**
- Existing review panel functionality unchanged
- Evidence displays with decision badges
- Review functionality works

### Test R.2: Existing Change List Works

**Steps:**
1. Navigate to Changes list view
2. Filter by various status values

**Expected Result:**
- List loads
- Filters work
- No impact from new assessment fields

### Test R.3: Certification Record CRUD Still Works

**Steps:**
1. Create new certification record
2. Edit details
3. Delete record

**Expected Result:**
- All operations succeed
- Evidence section doesn't interfere
- Existing audit trail unaffected

---

## Final Verification Checklist

- [ ] AssessmentWizard loads and submits correctly (all 3 methodologies)
- [ ] CRA Art. 3(4) enforcement verified (security changes are never substantial)
- [ ] Evidence upload/download/remove work without errors
- [ ] Certification records display evidence links correctly
- [ ] Release gate tabs load content correctly
- [ ] SBOM diff displays if analysis exists
- [ ] Prerequisite graph renders and is interactive
- [ ] Snapshot captures frozen state at approval
- [ ] All new API endpoints return expected data structures
- [ ] Audit events are logged for all operations
- [ ] No TypeScript errors in Phase D code
- [ ] No regressions in existing functionality
- [ ] Error handling shows user-friendly messages
- [ ] Loading states are visible where applicable
- [ ] Responsive design works on mobile (if applicable)
- [ ] No console errors or warnings from Phase D code
