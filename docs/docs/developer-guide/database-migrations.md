---
id: database-migrations
title: Database Migrations
sidebar_position: 3
---

# Database Migrations

Database schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/), the standard migration tool for SQLAlchemy projects. All schema changes must be made through Alembic migrations — direct DDL modifications to the database are not supported.

## Migration File Naming Convention

Migration files follow the convention:

```
YYYYMMDD_HHMM_short_description.py
```

For example: `20260428_0018_release_caused_by_change.py`

This naming scheme keeps migrations sorted chronologically and makes the purpose of each migration immediately identifiable.

## Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply migrations up to a specific revision
alembic upgrade <revision_id>

# Check current migration state
alembic current

# View migration history
alembic history --verbose
```

## Creating a New Migration

### 1. Modify the ORM Model

Make the required changes to the SQLAlchemy model in `app/models/`. For example, to add a column:

```python
# In app/models/product.py
new_field: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

### 2. Generate the Migration Script

```bash
alembic revision --autogenerate -m "short_description"
```

Alembic compares the current model definitions against the database schema and generates a migration script. Review the generated script carefully before applying it — autogeneration is not always accurate for complex changes such as renamed columns or custom constraint names.

### 3. Review the Generated Script

Open the generated file in `alembic/versions/` and verify:

- The `upgrade()` function correctly adds the intended schema changes
- The `downgrade()` function correctly reverses them
- Constraint names follow the project's `uq_`, `ix_`, `fk_` naming conventions
- Foreign key `ondelete` behaviour is correctly specified

### 4. Apply the Migration

```bash
alembic upgrade head
```

### 5. Rename the File

Rename the generated file to match the project naming convention:

```bash
# Example
mv alembic/versions/abc123_short_description.py \
   alembic/versions/20260501_1430_short_description.py
```

Update the `revision` and `down_revision` references inside the file if the filename is used in the revision identifier.

## Downgrading

```bash
# Revert the most recent migration
alembic downgrade -1

# Revert to a specific revision
alembic downgrade <revision_id>

# Revert all migrations (empty database)
alembic downgrade base
```

:::warning
Downgrading in production should only be performed during a planned maintenance window with a prior database backup. Irreversible data-loss migrations (such as dropping columns with data) cannot be safely downgraded.
:::

## Multiple Foreign Keys Between Tables

SQLAlchemy raises `AmbiguousForeignKeysError` when two or more foreign keys exist between the same pair of tables. This has occurred in the project when `ProductRelease` gained a second FK to the `changes` table. The resolution is to add explicit `foreign_keys=` arguments to all affected `relationship()` declarations on both sides. See the `product.py` and `change.py` model files for the established pattern.
