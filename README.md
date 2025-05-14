# <img src="docs/logo.png" alt="Network Simulation Server Logo" height="60"/>  

Network Simulation Server

[![Build](https://img.shields.io/github/actions/workflow/status/your-org/your-repo/ci.yml)](https://github.com/your-org/your-repo/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker Pulls](https://img.shields.io/docker/pulls/your-image)](https://hub.docker.com/r/your-image)

---

## Objective

A scalable, FastAPI-based backend for managing and simulating network topologies. The system leverages MongoDB for data storage and RabbitMQ for distributed task processing, supporting simulation creation, management, and data retrieval via a RESTful API.

---

## Quickstart

```bash
git clone https://github.com/your-org/network-simulation-server.git
cd network-simulation-server
cp .env.example .env  # Edit as needed
cd deployment
docker-compose up --build
```

Then visit [http://localhost:9090/docs](http://localhost:9090/docs) for the interactive API documentation.

---

## Table of Contents

- [Features](#features)
- [Quickstart](#quickstart)
- [Architecture](#architecture)
- [Dependencies / Libraries](#dependencies--libraries)
- [Configuration](#configuration)
- [Running the Project](#running-the-project)
  - [With Docker](#with-docker)
- [API Overview](#api-overview)
- [Example API Usage](#example-api-usage)
- [Examples](#examples)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)
- [Contact & Community](#contact--community)

---

## Features

- **Simulation Management**: Create, restart, pause, stop, and edit network simulations.
- **Distributed Workers**: Background workers for handling simulation and link processing.
- **RESTful API**: FastAPI endpoints for simulation control and data access.
- **MongoDB Integration**: Stores simulation data and metadata.
- **RabbitMQ Messaging**: Decouples simulation tasks for scalability.
- **Docker Support**: Easy deployment with Docker and Docker Compose.

## Architecture

The Network Simulation Server is designed with a modular, service-oriented architecture for scalability and maintainability. The main components are:

- **API Server (FastAPI)**: Handles HTTP requests, exposes RESTful endpoints, and coordinates simulation tasks.
- **Workers**: Background processes that handle simulation execution and link processing, communicating via RabbitMQ.
- **MongoDB**: Stores simulation data, metadata, and results.
- **RabbitMQ**: Message broker for decoupling and distributing simulation and link processing tasks.

### Component Interaction Diagram

```mermaid
flowchart LR
    Client[Client / User]
    API[FastAPI Server]
    MQ[RabbitMQ]
    DB[MongoDB]
    Worker1[Simulation Worker(s)]
    Worker2[Link Worker(s)]

    Client -- HTTP --> API
    API -- Mongo Queries --> DB
    API -- Publishes Tasks --> MQ
    MQ -- Consumed by --> Worker1
    MQ -- Consumed by --> Worker2
    Worker1 -- Reads/Writes --> DB
    Worker2 -- Reads/Writes --> DB
```

### Directory Structure Overview

```
├── app/
│   ├── api/           # FastAPI route definitions
│   ├── core/          # Core business logic (simulation_bl.py, link_bl.py, validator_bl.py, error_handlers.py, exceptions.py)
│   ├── db/            # Database access and models (simulation_db.py, simulation_meta_data_db.py, mongo_db_client.py)
│   ├── models/        # Pydantic models and schemas (simulation_models.py, requests_models.py, statuses_enums.py, mapper.py)
│   ├── rabbit_mq/     # RabbitMQ publishers/consumers
│   │   ├── publishers/  # Message publishers (post_run_publisher.py, links_publisher.py, simulations_publisher.py, base_publisher.py)
│   │   └── consumers/   # Message consumers (link_post_run_consumer.py, run_links_consumer.py, simulations_consumer.py, base_consumer.py)
│   ├── utils/         # Utility modules (logger.py, error_handler.py, simulation_utils.py, system_info.py, time_utils.py)
│   └── workers/       # Worker scripts for background processing (handle_simulation_worker.py, handle_links_worker.py, handle_in_post_link_worker.py, base_worker.py)
├── deployment/        # Docker, docker-compose, and deployment configs
│   ├── kubernetes/    # Kubernetes deployment files
│   ├── docker-compose.yml
│   └── Dockerfile
├── examples/          # Example simulation input files (happy_flows.json, unhappy_flows.json, shapes.json)
├── tests/             # Test suite
│   ├── unit/
│   └── integration/
├── visual/            # Visualization scripts (nx.py)
├── main.py            # Entrypoint for API server
├── run_all.py         # Entrypoint to run API and all workers
├── config.py          # Configuration and environment variable handling
├── requirements.txt   # Python dependencies
├── README.md          # Project documentation
├── .gitignore
└── ...
```

This structure ensures clear separation of concerns, modularity, and ease of navigation for both users and contributors.

### Component Roles

- **API Server**: Receives client requests, validates input, stores/retrieves data from MongoDB, and dispatches simulation tasks to RabbitMQ.
- **Workers**: Listen to RabbitMQ queues, process simulation or link tasks, and update MongoDB with results.
- **MongoDB**: Central data store for all simulation-related information.
- **RabbitMQ**: Ensures reliable, asynchronous task distribution between the API and workers.

## Business Logic

The core business logic of the Network Simulation Server is implemented in the `app/core/` directory. This layer orchestrates the main simulation, link processing, validation, and error handling workflows. Below is an overview of the key modules:

- **simulation_bl.py**: Implements the main logic for managing and executing network simulations. Handles simulation lifecycle, state transitions, and coordination with the database and messaging layers.
- **link_bl.py**: Contains the logic for processing and simulating network links. Responsible for link-specific computations, updates, and interactions within a simulation.
- **validator_bl.py**: Provides validation routines for network topologies and simulation requests. Ensures that input data and configurations meet required constraints before processing.
- **error_handlers.py**: Centralizes error handling for the business logic layer. Defines custom error responses, logging, and exception management to ensure robust and predictable behavior.
- **exceptions.py**: Defines custom exception classes used throughout the business logic and API layers, enabling precise error reporting and handling.

These modules work together to:

- Validate incoming simulation and link requests
- Manage simulation and link processing workflows
- Handle errors and exceptions gracefully
- Interface with the database and messaging systems

This separation of concerns ensures that the application remains modular, testable, and easy to maintain as it grows.

## Validation

Validation is a critical part of the Network Simulation Server, ensuring that only correct and consistent data is processed and stored. The validation logic is implemented in `app/core/validator_bl.py` and is split into two main phases:

### Before Actions Validation

These checks are performed before executing or saving simulation and link data, to prevent invalid operations and data corruption:

- **Node Existence**: Ensures that all nodes referenced by links exist in the simulation topology.
- **Link Node Validation**: Verifies that both endpoints of every link are valid nodes.
- **Link Latency vs. Simulation Duration**: Checks that each link's latency does not exceed the total simulation duration.
- **Simulation Duration vs. Highest Link Latency**: Ensures the simulation duration is at least as long as the highest link latency.
- **Simulation State**: Validates that the simulation is in a state (e.g., running or pending) that allows the requested action.
- **Time Constraints for Links**: Confirms that there is enough time left in the simulation for a link's latency to be processed.

### Post Actions Validation

These checks are performed after actions or during simulation execution, to monitor ongoing correctness and performance:

- **Packet Loss Percent**: Validates that the current packet loss percentage does not exceed the configured threshold.
- **Timeouts**: Ensures that the simulation does not exceed its configured duration.
- **Completion Check**: Determines if all links in the simulation have been processed, marking the simulation as complete if so.

This two-phase validation approach helps maintain data integrity and simulation correctness throughout the lifecycle of each simulation and link.

## Application Flow

The following outlines the end-to-end flow of a simulation through the Network Simulation Server, highlighting the interactions between the API, database, message broker, and worker consumers:

1. **Simulation Creation (API Request)**
   - The client sends a request to create a new simulations via the API.
   - The API validates the request (pre-action validation), stores the simulation in MongoDB, and publishes a message to the `simulation` exchange in RabbitMQ.
   - The API immediately returns a 200 OK response to the client with the simulation ID(s).

2. **Simulation Consumer (Worker)**
   - The simulation consumer listens to the `simulation` queue.
   - Upon receiving a message, it:
     - Fetches the simulation data from MongoDB.
     - Updates the simulation state to `running` in the database.
     - Publishes a message for each link in the simulation to the `links` exchange in RabbitMQ.
     - Handles errors and retries; if a message fails after all retries, it is moved to the dead letter queue (DLQ) for monitoring.

3. **Link Consumer (Worker)**
   - The link consumer listens to the `links` queue.
   - For each link message, it:
     - Fetches the relevant simulation and link data from MongoDB.
     - Runs pre-action validators (e.g., node existence, latency checks).
     - Waits for the configured link latency (simulating network delay).
     - Executes post-action validators (e.g., packet loss, timeouts).
     - Publishes a post-link message to the `post-link` exchange in RabbitMQ.
     - Handles errors, retries, and moves failed messages to the DLQ if necessary.

4. **Post-Link Consumer (Worker)**
   - The post-link consumer listens to the `post-link` queue.
   - For each post-link message, it:
     - Updates the simulation metadata in MongoDB (e.g., processed links, packet loss stats).
     - Checks if all links for the simulation have been processed (completion check).
     - If the simulation is complete, updates the simulation state in MongoDB to `done`.
     - Triggers alerting if the simulation is not completed within the expected timeframe.

5. **Monitoring and Error Handling**
   - All consumers and workers log errors and state changes.
   - Messages that cannot be processed after retries are moved to the DLQ for further inspection and alerting.
   - The system supports future enhancements for alerting, transactional operations, and improved validation.

This flow ensures that simulations are processed reliably, with clear separation of concerns, robust validation, and support for monitoring and error recovery.

## Logger

Logging in the Network Simulation Server is handled via a flexible, extensible system built on top of the [Loguru](https://loguru.readthedocs.io/) library. The logging system is defined in `app/utils/logger.py` and provides the following features:

- **AbstractLogger Interface**: An abstract base class enforces a consistent logging interface (`debug`, `info`, `warning`, `error`, `critical`) across the application.
- **LoguruLogger Implementation**: A concrete implementation of the abstract logger, using Loguru for rich, structured, and configurable logging output.
- **LoggerManager**: A thread-safe singleton manager that provides named logger instances throughout the application. This ensures that each component or module can have its own logger context, improving traceability.
- **Usage**: Loggers are retrieved via `LoggerManager.get_logger('name')` and used for structured logging in all major modules, including business logic, API endpoints, and background workers.

This approach ensures robust observability, aids in debugging, and supports future enhancements such as log aggregation or external monitoring.

## Dependency Injection

The project uses dependency injection to manage and provide access to core resources like MongoDB and RabbitMQ. This is implemented in `app/api/dependencies.py` and offers several benefits:

- **MongoDB Dependency**: The `get_mongo_manager` async dependency provides a connected MongoDB client (and optionally a transaction/session) to API routes and business logic. It supports both simple and transactional usage, automatically handling connection setup, transaction commit/abort, and resource cleanup.
  - Example usage: `db = Depends(partial(get_mongo_manager, with_transaction=False))` or `db, session = Depends(partial(get_mongo_manager, with_transaction=True))`
- **RabbitMQ Dependency**: The `get_rabbitmq_client` async dependency provides a connected RabbitMQ client to API routes and workers, ensuring proper connection and channel management.
- **Resource Management**: Both dependencies ensure that connections and sessions are properly closed after use, preventing resource leaks and supporting robust error handling.
- **Benefits**: This approach improves modularity, testability, and maintainability by decoupling resource management from business logic and API code. It also enables easier mocking and testing of components in isolation.

Dependency injection is a key architectural pattern in the project, supporting clean separation of concerns and scalable, maintainable code.

---

## Dependencies / Libraries

All dependencies are listed in `requirements.txt`. Key libraries include:

- **[FastAPI](https://fastapi.tiangolo.com/)**: Web framework for building APIs.
- **[Uvicorn](https://www.uvicorn.org/)**: ASGI server for FastAPI.
- **[aio-pika](https://aio-pika.readthedocs.io/)**, **aiormq**: Async RabbitMQ client.
- **[Motor](https://motor.readthedocs.io/)**: Async MongoDB driver.
- **[Pydantic](https://pydantic-docs.helpmanual.io/)**: Data validation.
- **[Loguru](https://loguru.readthedocs.io/)**: Logging.
- **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Loads environment variables from `.env`.
- **[dependency-injector](https://python-dependency-injector.ets-labs.org/)**: Dependency injection.
- **[pandas](https://pandas.pydata.org/)**: Data analysis (used in visualization scripts).
- *(Optional for visualization: matplotlib, networkx)*

---

## Configuration

The application is configured via environment variables, typically set in a `.env` file at the project root. Required variables:

```env
# MongoDB
MONGODB_URI=***
MONGODB_DB_DEV=network_sim_db_dev
MONGODB_DB_PROD=network_sim_db_prod

# RabbitMQ
RABBITMQ_URL=***
RABBITMQ_MAX_RETRIES=3
RABBITMQ_INITIAL_RETRY_DELAY=1
RABBITMQ_RETRY_QUEUE_TTL=5000
RABBITMQ_PREFETCH_COUNT=5

# Environment
ENV=dev  # or 'prod'
```

Additional RabbitMQ-related variables may be required for advanced features:

- `LINKS_EXCHANGE`, `RUN_LINKS_QUEUE`, `SIMULATION_EXCHANGE`, `SIMULATION_QUEUE`, `POST_LINK_EXCHANGE`, `POST_LINK_QUEUE`

---

## Running the Project

### With Docker

**This project is designed to be run using Docker and Docker Compose.**

#### 1. Prepare your environment

- Ensure you have [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.
- Create a `.env` file in the project root and fill in the required environment variables (see [Configuration](#configuration)).

#### 2. Build and start all services

From the `deployment` directory, run:

```bash
cd deployment
# Build and start the API, workers, MongoDB, and RabbitMQ
docker-compose up --build
```

- This will build the application image and start all services defined in `docker-compose.yml`:
  - **API server** (FastAPI)
  - **Worker processes** (background simulation/link workers)
  - **MongoDB** (database)
  - **RabbitMQ** (message broker)

#### 3. Access the API

- Once all containers are running, access the API documentation at: [http://localhost:9090/docs](http://localhost:9090/docs)
- The API will be available at [http://localhost:9090](http://localhost:9090)
- RabbitMQ management UI: [http://localhost:15672](http://localhost:15672) (default user/pass: guest/guest)
- MongoDB will be available on port 27017 (for local tools)

#### 4. Stopping services

To stop all running containers, press `Ctrl+C` in the terminal where Docker Compose is running, or run:

```bash
docker-compose down
```

#### 5. Troubleshooting

- **Port conflicts**: Make sure ports 9090 (API), 27017 (MongoDB), and 5672/15672 (RabbitMQ) are free.
- **Environment variables**: If the app fails to start, check your `.env` file and ensure all required variables are set.
- **Logs**: Use `docker-compose logs` to view logs for all services, or `docker-compose logs <service>` for a specific service.
- **Rebuilding**: If you change dependencies or code, rebuild with `docker-compose up --build`.

---

## API Overview

The API is served under `/api`. Main endpoints include:

- **Simulation Creation**
  - `POST /api/simulate`: Create new simulations.
- **Simulation Management**
  - `POST /api/restart/{simulation_id}`: Restart a simulation.
  - `POST /api/pause/{simulation_id}`: Pause a simulation.
  - `POST /api/stop/{simulation_id}`: Stop a simulation.
  - `PUT /api/edit/{simulation_id}`: Edit a simulation.
- **Simulation Data**
  - `GET /api/simulation-data/status/{simulation_id}`: Get simulation status.
  - `GET /api/simulation-data/get-simulation/{simulation_id}`: Get simulation details.
  - `GET /api/simulation-data/get-simulation-meta-data/{simulation_id}`: Get simulation metadata.
  - `GET /api/simulation-data/get-all-simulations`: List all simulations.
- **Debug**
  - `POST /api/debug/send-simulation-message`: Send a simulation message.
  - `POST /api/debug/send-link-message`: Send a link message.
  - `GET /api/debug/ping`: Debug health check.
- **Health Check**
  - `GET /health`: Service health.

See [http://localhost:9090/docs](http://localhost:9090/docs) for full, interactive API documentation.

---

## Example API Usage

| Endpoint | Method | Request Example | Response Example |
|----------|--------|----------------|-----------------|
| `/api/simulate` | POST | `{ "topology": { ... }, "duration": 100 }` | `{ "simulation_id": "abc123", "status": "created" }` |
| `/api/simulation-data/status/abc123` | GET |  | `{ "simulation_id": "abc123", "status": "running" }` |

---

## Examples

Example simulation requests and topologies can be found in the `examples/` directory:

- `happy_flows.json`
- `unhappy_flows.json`
- `shapes.json`

---

## Development

---

## Contributing

We welcome contributions! To get started:

1. Fork this repository and clone your fork.
2. Create a new branch for your feature or bugfix.
3. Make your changes and add tests if applicable.
4. Open a pull request describing your changes.

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## License

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This project is licensed under the [MIT License](LICENSE).

---

## Contact & Community

- **Issues**: [GitHub Issues](https://github.com/your-org/network-simulation-server/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/network-simulation-server/discussions)
- **Email**: <your.email@example.com>
- **Docs**: [API Docs](http://localhost:9090/docs)

---

## What Next?

The following areas are identified as important next steps and improvements for the project:

- [ ] **Testing**: Add unit, integration, and E2E tests for reliability and CI/CD support.
- [ ] **Dead Letter Queue (DLQ) & Monitoring**: Move failed messages to DLQ and implement monitoring/alerting.
- [ ] **Validation**: Validate input data before saving to the database.
- [ ] **Transactions & ACID Compliance**: Refactor to use database transactions for atomic operations.
- [ ] **Alerting**: Add alerting for simulations not completed in time.
- [ ] **Application Features (Edit & Stop)**: Enhance support for editing and stopping simulations.
- [ ] **Batch Publish Message**: Use RabbitMQ batch publishing for performance.
- [ ] **Visualization**: Implement dashboards for simulation results and system metrics.

Contributions and suggestions for these and other improvements are welcome!
