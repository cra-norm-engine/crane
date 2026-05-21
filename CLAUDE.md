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
