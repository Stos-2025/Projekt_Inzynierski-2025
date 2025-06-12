# `src` Directory
> [!WARNING]
> Work is still in progress. This file can be outdated.

This directory contains the source code for the STOS project, including all main services, shared modules, and configuration files.

## Structure

- [`common/`](src/common/)  
  Shared Pydantic models and DTOs used by all services for consistent data exchange.

- [`master/`](src/master/)  
  Source code for the master service, responsible for managing tasks and coordinating workers.

- [`worker/`](src/worker/)  
  Source code for the worker service, which processes tasks assigned by the master.

- [`adapter/`](src/adapter/)  
  Source code for the adapter service, handling communication with external systems or user interfaces.

- [`conf/`](src/conf/)  
  Configuration files and scripts for building, running, and managing the services (e.g., Docker Compose, environment variables).

## Getting Started

1. **Configure Environment:**  
   Edit `src/conf/.env` to set environment variables as needed.

2. **Build and Run Services:**  
   ```sh
   docker compose -f src/conf/compose.yml up --build
   ```

3. **Development:**  
   Each service can be developed and tested independently. Shared models are imported from `src/common`.

> [!NOTE]
> - All services rely on the shared models in `src/common` for data validation and communication.
> - Configuration is centralized in `src/conf`.
> - For detailed information about each service or module, see the respective README files in their subdirectories.

---
For more details, refer to the documentation in each subdirectory or the main [README.md](../README.md).