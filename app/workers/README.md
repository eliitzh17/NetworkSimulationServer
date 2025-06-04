# Workers Directory

This directory contains the worker processes responsible for handling background tasks, message queue consumption, and event production in the Network Simulation Server. These workers are designed to be scalable and can run in multiple instances for high availability and throughput.

## Subfolders & File Overview

### outbox_producers_workers/
- **base_producer_worker.py**: Base class and runner for outbox producer workers, providing shared logic for all producer workers.
- **simulation_completed_producer_worker.py**: Worker for producing events when simulations are completed.
- **simulations_producer_worker.py**: Worker for producing events related to new simulations.
- **links_producer_worker.py**: Worker for producing events related to link processing.

### consumer_workers/
- **base_consumer_worker.py**: Base class for consumer workers, handling setup and execution of message queue consumers.
- **consumer_links_worker.py**: Worker for consuming and processing link-related messages from the queue.
- **consumer_simulations_worker.py**: Worker for consuming and processing simulation-related messages from the queue.
---

**Note:**  
Workers in this directory are designed to be run as independent processes and can be scaled horizontally (multiple instances) to handle increased load or provide redundancy.

--- 