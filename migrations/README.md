# Database Migrations

This directory contains database migration scripts managed by Alembic.

## Usage

### Initialize the database

To create the initial database schema:

```bash
cd /path/to/DokuCORE
alembic upgrade head
```

### Create a new migration

After making changes to the database schema:

```bash
alembic revision -m "Description of changes"
```

### Apply migrations

To apply all pending migrations:

```bash
alembic upgrade head
```

To apply specific migrations:

```bash
alembic upgrade +1  # Apply the next migration
alembic upgrade abc123  # Apply up to revision abc123
```

### Downgrade migrations

To roll back the last migration:

```bash
alembic downgrade -1
```

To roll back to a specific migration:

```bash
alembic downgrade abc123
```

To roll back to the beginning:

```bash
alembic downgrade base
```

## Migration File Structure

Each migration file has an `upgrade()` and `downgrade()` function:

- `upgrade()`: Changes to apply when upgrading the database
- `downgrade()`: Changes to revert when downgrading the database

## Important Notes

- The vector type is not natively supported by SQLAlchemy, so we use raw SQL to set up those columns.
- Always back up your database before applying migrations in production.
- Test migrations on a staging environment before applying to production.