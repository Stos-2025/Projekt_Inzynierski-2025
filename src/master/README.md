# Master Service
> [!WARNING]
> Work is still in progress. This file can be outdated.

This directory contains the **master** service for the STOS project. The master is responsible for managing submissions, coordinating workers, and providing a REST API for CRUD operations and status tracking.

## Files

- [`master.py`](./app/master.py)  
  The main FastAPI application. Responsible for:
  - Initializing the database and routers.
  - Handling API requests for submissions and workers.
  - Managing middleware and logging.

- [`worker_controller.py`](./app/worker_controller.py)  
  Endpoints for worker communication:
  - Assigns pending submissions to workers.
  - Receives and stores results from workers.

- [`submission_controller.py`](./app/submission_controller.py)  
  Endpoints for submission management:
  - Create, read, and delete submissions.
  - Query submission status and results.

- [`models.py`](./app/models.py)  
  SQLAlchemy models for submissions.

- [`submission_repository.py`](./app/submission_repository.py)  
  Database access layer for submissions.

- [`dockerfile`](./dockerfile)  
  Dockerfile for building the master image:
  - Based on Alpine Linux.
  - Installs Python and dependencies.
  - Copies source code and shared models.
  - Creates a `stos` user and sets environment variables.
  - Entrypoint runs the FastAPI app with Uvicorn.

## Environment Variables

- `MASTER_API_KEY` – API key for authenticating requests.
- `WORKER_URLS` – URLs for worker services.

## Building and Running

To build the master image:
```sh
docker build -f src/master/dockerfile -t stos_master src
```

To run the service using docker-compose, use the [`src/conf/compose.yml`](../conf/compose.yml) file.

## Workflow

1. The master receives new submissions via API.
2. Tracks submission status (pending, running, completed).
3. Assigns pending submissions to available workers.
4. Receives results from workers and updates submission status.
5. Provides endpoints for querying and managing submissions.

---

For more information about the architecture, see