# Network Simulation Server — Application Overview

This directory (`app/`) contains the core application code for the Network Simulation Server. The project is organized into modular layers, each responsible for a distinct aspect of the system, ensuring maintainability, scalability, and clear separation of concerns.

Below is a summary of each major subfolder. For detailed information, see the `README.md` in each subfolder.

---

## Folder Structure & Summaries

- **api/**
  - Implements the REST API using FastAPI. Defines endpoints for simulation management, data retrieval, and debugging. Handles request validation, dependency injection, and robust error handling. See `api/README.md` for endpoint and structure details.

- **business_logic/**
  - Contains the core business rules and orchestration logic for simulations, link execution, and topology management. Centralizes validation, error handling, and transactional workflows. See `business_logic/README.md` for module and validator details.

- **db/**
  - Data access layer for MongoDB. Encapsulates all CRUD operations, connection management, and transaction handling for events, topologies, and simulations. See `db/README.md` for repository and transaction details.

- **messageBroker/**
  - Messaging and event-driven infrastructure, primarily for RabbitMQ. Manages connections, producers, consumers, and backpressure. See `messageBroker/README.md` for messaging patterns and extension guidelines.

- **models/**
  - Defines all core data models, enums, and mapping utilities for requests, responses, events, and internal state. Ensures type safety and structured data flow. See `models/README.md` for model overviews.

- **utils/**
  - Utility modules for logging, error handling, system info, time conversions, and object normalization. Supports the core logic and reliability of the server. See `utils/README.md` for utility details.

- **workers/**
  - Background worker processes for message queue consumption and event production. Designed for horizontal scaling (multiple instances). See `workers/README.md` for worker types and scaling notes.

- **config/**
  - Configuration files and logic for environment-specific settings and dependency injection.

- **monitoring/**
  - Monitoring tools and scripts, such as message bus health and metrics collection.

- **app_container.py**
  - Dependency injection container for managing application-wide resources and configuration.

- **asgi.py**
  - ASGI entry point for running the FastAPI application.

---

## Modular Architecture

- **Separation of Concerns:** Each layer is responsible for a specific aspect of the system, making the codebase easier to maintain and extend.
- **Scalability:** Workers and message-driven components are designed for horizontal scaling.
- **Reliability:** Robust error handling, transaction management, and monitoring are built in at every layer.

---

For more details on any part of the system, refer to the `README.md` in the relevant subfolder. 