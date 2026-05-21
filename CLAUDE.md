# CLAUDE.md — CRA Compliance Tool Development Guide

## Error Handling Principles

All new code must follow these error handling conventions to maintain consistency, debuggability, and user experience across the application.

### Backend (FastAPI + Python)

**Logging:**
- All new services must have `logger = logging.getLogger(__name__)` at module level
- Never use bare `except Exception: pass` — always log or re-raise
- Log at ERROR level in exception handlers, DEBUG level for significant state transitions

**Exception Handling:**
- All exception handlers must return the canonical shape:
  ```json
  {
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable description",
      "details": {}
    }
  }
  ```
- Use `AppException` subclasses (`NotFoundException`, `ConflictException`, `ForbiddenException`) — never raise raw `HTTPException` from services
- Catch `SQLAlchemyError` (not just `IntegrityError`) in services; use `classify_sqlalchemy_error()` to convert DB errors to typed exceptions

**Examples:**
```python
# ❌ Wrong
except IntegrityError:
    raise ConflictException("...")

except Exception:
    pass  # Silent failure

# ✅ Correct
except SQLAlchemyError as e:
    raise classify_sqlalchemy_error(e) from e

except Exception:
    logger.exception("Failed to process request")
    raise
```

### Frontend (Vue 3 + TypeScript)

**Toast Notifications:**
- Use `useToast().showToast()` for all transient user-facing messages (errors, success, warnings)
- Never render inline `.feedback`, `.feedback-banner`, or `.alert` elements directly in views
- Toast system handles all notification display app-wide

**Data Fetching:**
- Use `useAsyncState()` composable for all async operations
- Do not create manual `isLoading`, `errorMessage`, `isError` refs in views
- `useAsyncState` automatically shows toasts on errors and tracks loading state

**Error Messages:**
- Never display raw exception strings to users
- Use user-friendly strings from `ERROR_CODE_MESSAGES` in `error-handler.ts`
- Map backend error codes to messages: `VALIDATION_ERROR` → "Please check your input and try again"

**Examples:**
```typescript
// ❌ Wrong
const errorMessage = ref("")
const isLoading = ref(false)
try {
  isLoading.value = true
  data.value = await api.get(id)
} catch (e) {
  errorMessage.value = e.message  // Raw exception message
  showAlert(errorMessage.value)
}

// ✅ Correct
const { data, isLoading, errorMessage, execute } = useAsyncState()
await execute(() => api.get(id))
// useAsyncState handles loading, error display, and user-friendly messages
```

---

## Implementation Record

All advanced error handling was implemented 2026-05-21:

1. **Backend:** 500 tracebacks now logged; DB sessions rollback explicitly on error; error responses normalized to canonical `{error: {code, message, details}}` shape
2. **Frontend:** Toast notification system; 401 auto-redirect to login; 403 permission errors shown as toasts; global Vue error handler for uncaught render errors; `useAsyncState` integrates with toast system
3. **Integration:** Correlation IDs flow through request/response headers (set up to start in Phase 1); error messages are user-friendly, not raw exceptions

These principles apply to all future code in this repository.

---

## CI/CD Pipeline & Quality Gates

To prevent mistakes during development ("vibe coding"), all code is validated automatically at multiple stages:

### Local Validation (Pre-Commit Hook)

**Runs automatically before every commit:**
- ❌ Block commits of `.env` files (secrets protection)
- ❌ Block commits of `node_modules/` (artifact protection)
- ✅ Lint backend Python files with `ruff` (syntax, imports, naming)
- ✅ Type check frontend TypeScript with `vue-tsc` (no `any` leaks)

If any check fails:
```bash
# Fix the issue:
cd backend && ruff check --fix .          # Auto-fix most issues
cd frontend && npm run lint               # Auto-fix frontend
git add <fixed files>
git commit -m "..."                       # Retry
```

### GitHub Actions (PR & Branch CI)

**On every push to a branch or PR to main:**

**Backend CI** (`.github/workflows/backend-ci.yml`):
1. **Lint** — ruff checks for syntax, imports, naming conventions
2. **Type Check** — mypy validates type annotations (non-blocking, warns only)
3. **Tests** — pytest runs all tests against a fresh PostgreSQL container
4. **Docker Build** — backend Dockerfile builds successfully (no syntax errors)

**Frontend CI** (`.github/workflows/frontend-ci.yml`):
1. **Type Check** — vue-tsc ensures no TypeScript errors
2. **Lint** — eslint checks Vue, TypeScript, and JavaScript code
3. **Build** — `vite build` creates production bundle (catches bundler errors)

### Branch Protection (Main Only)

Main branch requires:
- ✅ All GitHub Actions pass (lint, test, build, type check)
- ✅ At least 1 approval on PR (self-review checklist acceptable)
- ❌ No force pushes allowed
- ❌ No direct commits (PR only)

### Enforcement Rules

**You (developer) must:**
1. Create a feature branch: `git checkout -b feature/<name>`
2. Commit with conventional format: `feat(<scope>): description`
3. Push: `git push origin feature/<name>`
4. Open PR on GitHub
5. Wait for CI to pass (green checkmarks on PR)
6. Merge via "Squash and merge" to keep main history clean
7. Delete feature branch after merge

**Claude will:**
1. Remind you of failing checks if CI fails on your PR
2. Suggest fixes for lint/type errors
3. Ask you to commit locally and test before pushing (if risky)
4. Refuse to help with work on main branch directly
5. Enforce conventional commit format in commit messages

### Local Setup

**Backend (Python linting & type check):**
```bash
# Install dev dependencies
pip install -r backend/requirements-dev.txt

# Run locally before pushing
cd backend
ruff check --fix .    # Auto-fix style issues
mypy app              # Check types (warnings only)
pytest app/tests      # Run all tests
```

**Frontend (TypeScript & ESLint):**
```bash
# Linting and type checking
cd frontend
npm run type-check    # Check for TypeScript errors
npm run lint          # Run and auto-fix ESLint issues
npm run build         # Test production build
```

### What Triggers CI?

- **Backend CI** runs if `backend/**` or `requirements.txt` changed
- **Frontend CI** runs if `frontend/**` or `package*.json` changed
- All CI runs on: new pushes to any branch, pull requests to main
- CI **must pass** before merging to main

### Ignoring Checks (Almost Never)

If you hit a false positive:
```bash
# Type error that's intentional
# @ts-expect-error reason for exception
const result: any = fetchUnknownShape()

# Python import that's conditional
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from optional_module import Something
```

Never skip CI with `--no-verify` or merge broken branches to main.

---

## Implementation Record

CI/CD pipeline set up 2026-05-21:
- Created `.github/workflows/backend-ci.yml` (lint, type check, test, docker build)
- Created `.github/workflows/frontend-ci.yml` (type check, lint, build)
- Added `backend/requirements-dev.txt` with ruff, mypy, pytest
- Added ESLint config to frontend (`.eslintrc.cjs`)
- Added `backend/pyproject.toml` with ruff and mypy settings
- Updated pre-commit hook to run ruff on Python files and vue-tsc on TypeScript
- Updated `frontend/package.json` with lint script and ESLint dependencies

CI/CD pipeline is **active and enforced** starting with the next PR.
