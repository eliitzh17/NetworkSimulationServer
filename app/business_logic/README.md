# Business Logic Layer (`app/business_logic`)

This directory contains the core business logic for the Network Simulation Server. It encapsulates all domain-specific operations, validation, and orchestration of simulations, ensuring a clear separation between API, data access, and business rules.

## Purpose

- Implements the main algorithms and workflows for network simulation, link execution, and topology management.
- Centralizes validation, error handling, and transactional logic for complex operations.
- Provides a single source of truth for business rules, making the system maintainable and testable.

---

## Business Logic Modules

### `link_bl.py` — Link Execution Logic

Handles the execution of individual network links within a simulation, including:

- Managing link state transitions (pending, running, done, failed).
- Performing atomic database updates for link events and simulation state.
- Integrating with `LinksValidators` for:
  - Node existence checks.
  - Link timing and latency validation.
  - Packet loss and simulation state validation (pre- and post-link execution).

**Related Validators:**  
- `validators/links_validators.py` — Ensures all link operations are valid within the simulation context.

---

### `topologies_simulation_bl.py` — Simulation Lifecycle Orchestration

Orchestrates the full lifecycle of a topology simulation:

- Creation, running, and completion of simulations.
- Event logging and time calculations.
- Ensures atomicity for multi-step operations.
- Integrates with `SimulationValidators` for:
  - Pre-simulation checks (duration, link nodes).
  - Post-simulation checks (packet loss, completion status).

**Related Validators:**  
- `validators/simulation_validators.py` — Validates simulation-wide constraints and leverages link validators for link-level checks.

---

### `topologies_bl.py` — Topology Management & Simulation Triggering

Manages simulation requests and topology validation:

- Splits requests into new and existing topologies.
- Validates and enriches new topologies before simulation.
- Triggers simulation creation and execution.
- Integrates with `TopologiesValidators` for:
  - Ensuring topologies have valid nodes and links.
  - Checking for duplicates and structural constraints.

**Related Validators:**  
- `validators/topolgy_validators.py` — Validates the structure and integrity of topologies before simulation.

---

### `topologies_actions_bl.py` — Simulation Actions

Manages runtime actions on simulations:

- Pause, resume, and restart operations.
- Updates simulation state and timing.
- Ensures state transitions are valid and logged.

**Related Validators:**  
- Indirectly relies on simulation and link validators to ensure state transitions are valid.

---

### `exceptions.py` — Custom Exceptions

Defines custom exception classes for business logic and domain errors, including:

- Topology, simulation, database, validation, configuration, and resource errors.

**Usage:**  
- Used throughout all business logic modules for clear, descriptive error handling.

---

### `error_handlers.py` — Centralized Error Handling

Provides static methods for handling business logic exceptions:

- Maps exceptions to standardized error responses.
- Logs errors for monitoring and debugging.
- Supports recovery strategies (e.g., retries, fallbacks).

**Usage:**  
- Used by business logic modules to ensure consistent error handling and response formatting.

---

### `validators/` — Validation Logic

Contains all validation logic for:

- Links (`links_validators.py`)
- Simulations (`simulation_validators.py`)
- Topologies (`topolgy_validators.py`)

Validators are tightly integrated with business logic modules to enforce domain rules and prevent invalid operations.

---

## Extending

To add new business rules or workflows:

1. Create or extend a `*_bl.py` file for the relevant domain logic.
2. Add or update validation logic in the `validators/` directory as needed.
3. Use custom exceptions for new error scenarios.
4. Ensure all operations that modify state are atomic and properly logged.

## Related Layers

- **API Layer:** See `app/api/` for endpoint definitions and request handling.
- **Data Access Layer:** See `app/db/` for database models and persistence logic. 