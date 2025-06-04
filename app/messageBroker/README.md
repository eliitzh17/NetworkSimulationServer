# Message Broker Layer (`app/messageBroker`)

This directory contains the messaging and event-driven infrastructure for the Network Simulation Server. It provides all logic for interacting with RabbitMQ, including connection management, producers, consumers, and backpressure handling.

## Purpose

- Implements asynchronous, event-driven communication between services and components.
- Encapsulates all RabbitMQ connection, channel, queue, and exchange management.
- Provides robust producer and consumer abstractions for simulation events and link processing.
- Ensures reliability, scalability, and observability for message-based workflows.

---

## Message Broker Modules

### `rabbit_mq_manager.py` — RabbitMQ Resource Manager

- Manages RabbitMQ channels, exchanges, and queues.
- Handles safe declaration, deletion, and rebinding of exchanges/queues with retry logic.
- Supports dead-letter exchanges (DLX) and queue TTLs for robust message handling.
- Used by both producers and consumers for consistent resource management.

---

### `rabbit_mq_client.py` — RabbitMQ Connection Client

- Manages the lifecycle of the RabbitMQ connection using `aio_pika`.
- Handles connection setup, teardown, and reconnection logic.
- Provides access to channels for publishing and consuming messages.
- Used as a dependency by the manager, producers, and consumers.

---

### `backpressure_manager.py` — Backpressure & Flow Control

- Monitors queue sizes and consumer counts to dynamically apply backpressure.
- Calculates and enforces publishing delays based on queue load and consumer availability.
- Prevents message overload and ensures system stability under high load.

---

### `producers/` — Message Producers

- Contains producer classes for publishing simulation and link events to RabbitMQ.
- Implements logic for serializing, batching, and routing messages to the correct exchanges/queues.
- Includes base producer abstractions for code reuse and consistency.

---

### `consumers/` — Message Consumers

- Contains consumer classes for processing messages from RabbitMQ queues.
- Implements logic for deserializing, validating, and handling simulation and link events.
- Includes base consumer abstractions for code reuse and consistency.

---

## Key Features

- **Resilient Messaging:** Automatic reconnection, retry logic, and dead-letter handling for robust message delivery.
- **Backpressure Management:** Dynamic delay and flow control to prevent queue overload and ensure smooth operation.
- **Producer/Consumer Abstractions:** Modular, reusable classes for all message publishing and consumption patterns.
- **Observability:** Extensive logging for all connection, channel, and message operations.

---

## Extending

To add new message types or workflows:

1. Create a new producer or consumer class in the appropriate subdirectory.
2. Use the manager and client for consistent resource and connection handling.
3. Implement serialization, validation, and error handling as needed.
4. Update the backpressure manager if new queues require flow control.

## Related Layers

- **Business Logic Layer:** See `app/business_logic/` for domain logic and workflows.
- **Data Access Layer:** See `app/db/` for database models and persistence logic.
- **API Layer:** See `app/api/` for endpoint definitions and request handling. 