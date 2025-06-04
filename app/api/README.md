# API Layer (`app/api`)

This directory contains the API layer for the Network Simulation Server. It defines all FastAPI routers, endpoint logic, and API-specific utilities, serving as the main interface between external clients and the server's business logic and data layers.

## Purpose

- Exposes RESTful endpoints for simulation management, creation, data retrieval, and debugging.
- Handles request validation, robust error handling, and dependency injection for database and message broker connections.
- Provides a clear separation between API logic and business/data access logic.
- Ensures data consistency and reliability through atomic transactions and centralized exception handling.

## Structure & Modules

| File                          | Description                                                                                  |
|-------------------------------|----------------------------------------------------------------------------------------------|
| `simulation_creator_api.py`    | Endpoints for creating new network simulations. Handles simulation requests and triggers business logic. |
| `simulation_management_api.py` | Endpoints for managing simulations (restart, pause, resume, edit). Transactional DB support. |
| `simulation_data_api.py`       | Endpoints for retrieving simulation data and statuses, including paginated queries.           |
| `debug_api.py`                 | Debug and health-check endpoints. Allows sending test messages and checking API health.       |
| `api_error_handler.py`         | Decorators and utilities for consistent API error handling and logging.                       |
| `api_utils.py`                 | Shared utility functions for API endpoints (e.g., fetching simulations or raising HTTP errors).|
| `dependencies.py`              | FastAPI dependency providers for MongoDB and RabbitMQ connections, with transaction support.  |

> **Note:** The `__pycache__` directory contains Python bytecode and can be ignored.

## Conventions

- All routers are defined using FastAPI's `APIRouter` and are intended to be included in the main application.
- Error handling is standardized using decorators from `api_error_handler.py`.
- Database and message broker connections are managed via dependency injection for testability and modularity.

## Extending

To add new endpoints:
1. Create a new `*_api.py` file or extend an existing one.
2. Define a new `APIRouter` and endpoints.
3. Use dependency injection for DB or broker access as needed.
4. Register the router in your main FastAPI app.

## Related Layers

- **Business Logic:** See `app/business_logic/` for core simulation logic.
- **Data Access:** See `app/db/` for database models and queries.

## Atomic Transactions

Some endpoints (such as those in `simulation_management_api.py` and `simulation_creator_api.py`) require multiple database operations to be executed as a single, atomic transaction. This is achieved using FastAPI dependencies (see `dependencies.py`) that:

- Start a MongoDB session and transaction before the endpoint logic executes.
- Commit the transaction if the endpoint completes successfully.
- Abort (roll back) the transaction if an exception occurs, ensuring no partial updates are persisted.

This approach guarantees data integrity, especially for operations that modify multiple documents or collections.

**Example:**
```python
@simulation_management_router.post("/restart/{simulation_id}")
async def restart_simulation(..., db_session: Annotated[Tuple[AsyncIOMotorDatabase, ClientSession], Depends(get_db_with_transaction())]):
    # All DB operations in this endpoint are atomic
```

## Exception Handling

Consistent and robust exception handling is implemented using the `handle_api_exceptions` decorator (see `api_error_handler.py`). This decorator:

- Catches and logs all exceptions raised in API endpoints.
- Maps custom business logic exceptions to appropriate HTTP status codes and error messages.
- Ensures clients receive clear, standardized error responses, while sensitive details are logged for debugging.

**Example:**
```python
@handle_api_exceptions
async def create_simulation(...):
    ...
```

This centralization of error handling reduces code duplication and improves maintainability and reliability across the API layer. 