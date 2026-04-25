# Migration from GraphDB/SPARQL to PostgreSQL with SQLModel

## Overview

This migration replaces the GraphDB/SPARQL backend with PostgreSQL and SQLModel ORM while maintaining the existing API interface with minimal changes.

## Key Changes

### 1. Database Models (`app/api/db_models.py`)

Created SQLModel models to replace the SPARQL-based data structure:

- **Dataset**: Represents a neuroscience dataset
- **Subject**: Represents a participant in a dataset
- **Session**: Represents either an imaging or phenotypic session
- **Acquisition**: Represents an imaging acquisition (linked to sessions)
- **CompletedPipeline**: Represents a pipeline run on a session
- **ControlledTerm**: Stores standardized terms
- **ControlledTermAttribute**: Stores controlled term attributes

All models use proper relationships and foreign keys for referential integrity.

### 2. Database Connection (`app/api/database.py`)

- Uses async SQLAlchemy with asyncpg driver
- Implements `get_session()` dependency for FastAPI
- Automatic table creation on startup via `init_db()`

### 3. CRUD Operations (`app/api/crud.py`)

Completely rewritten to use SQLModel ORM instead of SPARQL queries:

- `query_records()`: Query subjects/sessions with filters
- `post_subjects()`: Get subject data for specific datasets
- `post_datasets()`: Get dataset metadata matching query
- `query_matching_dataset_sizes()`: Count subjects per dataset
- `query_available_modalities_and_pipelines()`: Get imaging metadata
- `get_terms()`: Retrieve controlled terms
- `get_controlled_term_attributes()`: Get term attributes

All functions now accept an `AsyncSession` parameter and use SQLAlchemy queries.

### 4. Environment Variables (`app/api/env_settings.py`)

Replaced GraphDB settings with PostgreSQL settings:

**Removed:**
- `NB_GRAPH_USERNAME`
- `NB_GRAPH_PASSWORD`
- `NB_GRAPH_ADDRESS`
- `NB_GRAPH_DB`
- `NB_GRAPH_PORT`

**Added:**
- `NB_DB_HOST` (default: localhost)
- `NB_DB_PORT` (default: 5432)
- `NB_DB_NAME` (default: neurobagel)
- `NB_DB_USER` (required)
- `NB_DB_PASSWORD` (required)
- `NB_DB_ECHO` (default: false) - SQL query logging

### 5. Router Updates

All routers now use database session dependency injection:

```python
async def route_handler(
    db_session: AsyncSession = Depends(get_session)
):
    result = await crud.some_function(db_session, ...)
```

Updated routers:
- `app/api/routers/query.py`
- `app/api/routers/datasets.py`
- `app/api/routers/subjects.py`
- `app/api/routers/attributes.py`
- `app/api/routers/route_factory.py`

### 6. Application Startup (`app/main.py`)

- Removed GraphDB authentication validation
- Added database initialization on startup
- Updated environment variable validation for PostgreSQL

### 7. Docker Configuration

**docker-compose.yml:**
- Replaced GraphDB service with PostgreSQL 15
- Simplified configuration with standard Postgres environment variables

### 8. Data Loading (`app/api/data_loader.py`)

Created utility script to load data into PostgreSQL:

```bash
# Load data from JSON
python -m app.api.data_loader --json data.json

# Clear database
python -m app.api.data_loader --clear
```

Expected JSON format:
```json
{
  "datasets": [
    {
      "dataset_uuid": "uuid",
      "dataset_name": "name",
      "subjects": [
        {
          "sub_id": "sub-01",
          "sessions": [
            {
              "session_id": "ses-01",
              "session_type": "ImagingSession",
              "age": 25.5,
              "sex": "snomed:248152002",
              "acquisitions": [...],
              "pipelines": [...]
            }
          ]
        }
      ]
    }
  ]
}
```

## Migration Guide

### For Development

1. **Set up PostgreSQL:**
   ```bash
   # Using Docker Compose
   docker-compose up -d postgres
   ```

2. **Configure environment variables:**
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env with your database credentials
   nano .env
   ```

3. **Run the API:**
   ```bash
   # The database will be initialized automatically on startup
   uvicorn app.main:app --reload
   ```

4. **Load data:**
   ```bash
   python -m app.api.data_loader --json your_data.json
   ```

### For Production

1. Set up a PostgreSQL instance
2. Configure environment variables for database connection
3. Deploy the API (database tables will be created on first startup)
4. Load data using the data loader script or your own ETL pipeline

## What Stayed the Same

- All API endpoints remain unchanged
- Response models are identical
- Pydantic models for request/response validation unchanged
- Authentication mechanism unchanged
- Vocabulary and configuration loading unchanged
- Utility functions for data processing unchanged

## What's Different

- Backend storage: PostgreSQL instead of GraphDB
- Query language: SQLAlchemy ORM instead of SPARQL
- Data loading: Custom script instead of graph upload
- Environment variables: Database connection instead of graph connection
- No migration system (database cleared and reloaded on restart)

## Performance Considerations

- SQLModel/SQLAlchemy uses connection pooling
- Async operations for all database queries
- Proper indexes on frequently queried columns (dataset_uuid, sex, diagnosis, etc.)
- No N+1 query issues due to proper relationship loading

## Testing

Tests need to be updated to:
- Use in-memory SQLite for test database
- Mock database sessions instead of SPARQL responses
- Create test data using SQLModel models

## Future Enhancements

- Add proper database migration support (e.g., Alembic)
- Implement bulk loading for better performance
- Add database connection health checks
- Consider read replicas for scalability
- Add caching layer for frequently accessed data
