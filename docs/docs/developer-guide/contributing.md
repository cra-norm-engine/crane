---
id: contributing
title: Contributing
sidebar_position: 4
---

# Contributing

Contributions to CRA Conformity Management are welcome. This guide describes the conventions and process for submitting changes.

## Development Workflow

1. Fork the repository on GitHub
2. Create a feature branch from `main`: `git checkout -b feature/your-feature-name`
3. Make your changes, following the conventions described below
4. Run type checking and linting (see [Local Development](/developer-guide/local-development))
5. Commit with a descriptive commit message
6. Open a pull request against `main`

## Code Conventions

### Backend

- **Python 3.12+** — use modern type annotation syntax (`str | None`, `list[str]`, etc.)
- **SQLAlchemy 2.x** — use `select()` statements and `Mapped` type annotations; do not use the legacy Query API
- **Pydantic v2** — use `model_dump()`, `model_validate()`, and `model_fields`; do not use v1 aliases
- **Repository pattern** — all database queries belong in a repository class; services must not call `db.execute()` directly
- **No lazy loading** — use `selectinload()` in repository queries; do not rely on SQLAlchemy lazy relationship loading
- **Audit events** — all state-changing service operations must call `create_audit_event()`
- **Date serialisation** — convert `datetime.date` objects to ISO strings before passing to `create_audit_event()`; `json.dumps` cannot serialise `date` objects directly

### Frontend

- **Vue 3 Composition API** — all components use `<script setup lang="ts">`
- **TypeScript** — all service functions, props, emits, and reactive state must be typed
- **Service modules** — all API calls are made through service modules in `src/services/`; views must not use Axios directly
- **No inline styles** — all styling is done via scoped CSS in the component `<style scoped>` block

### Comments

All code must include meaningful comments to support human readability. Comments should explain **why** a decision was made, not restate what the code does. Particular attention should be given to:

- Non-obvious SQLAlchemy relationship configurations (e.g. `foreign_keys=` disambiguation)
- CRA regulatory references that explain why a specific field or constraint exists
- Workarounds for known library behaviours

## Commit Messages

Use the imperative mood and reference the relevant CRA article or feature area where applicable:

```
Add product_id filter to change list endpoint

Scopes the GET /changes response to a specific product so the release
form can offer only same-product substantial changes for linking.
CRA Art. 13(8) traceability.
```

## Pull Request Guidelines

- Keep pull requests focused on a single concern
- Include a description of the regulatory context for compliance-related changes
- Ensure all existing functionality is unaffected (no regressions)
- Update the documentation in `docs/` if the change affects user-facing behaviour

## Reporting Issues

Open an issue on GitHub with:

- A clear description of the problem
- Steps to reproduce
- Expected and actual behaviour
- Relevant CRA context if the issue relates to regulatory compliance logic
