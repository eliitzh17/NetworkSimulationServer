# Models Directory

This directory contains all the core data models, enums, and mapping utilities used throughout the Network Simulation Server. These models define the structure of requests, responses, events, and internal state for network topology simulations.

## File Overview

- **message_bus_models.py**
  - Defines models for event routing and outbox publishing configuration, such as `EventTypeToRoutingKey` and `OutboxPublisher`.

- **topolgy_simulation_models.py**
  - Contains models for simulation state, including execution state of links, simulation timing, and the main `TopologySimulation` object.

- **mapper.py**
  - Provides mapping utilities to convert between simulation requests, events, and internal models. Handles enrichment and transformation logic.

- **requests_models.py**
  - Defines request models for simulation creation (`SimulationRequest`) and pagination (`PaginationRequest`, `CursorPaginationRequest`).

- **topolgy_models.py**
  - Contains core models for network topology (`Topology`), links (`Link`), configuration (`Config`), and their execution states.

- **statuses_enums.py**
  - Enumerations for simulation statuses (`TopologyStatusEnum`), link statuses (`LinkStatusEnum`), and event types (`EventType`).

- **pageination_models.py**
  - Models for pagination requests and responses, including generic cursor-based pagination.

- **events_models.py**
  - Event models for simulation and link events, including a generic `BaseEvent` and specialized `SimulationEvent` and `LinkEvent`.

---

This folder is essential for maintaining a clear, type-safe, and well-structured data flow throughout the simulation server. 