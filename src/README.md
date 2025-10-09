# `src` Directory

> [!WARNING]
> Work is still in progress. This file can be outdated.

This directory contains the source code for the STOS project, including all main services, shared modules, and configuration files.

## Structure

- [`common/`](common/)  
  Shared Pydantic models and DTOs used by all services for consistent data exchange.

- [`worker/`](worker/)  
  Source code for the worker service, which processes tasks assigned by the master.

- [`gui_mock/`](gui_mock/)  
  Mock GUI service for testing and development purposes.

- [`deploy/`](deploy/)  
  Deployment scripts and configuration files for systemd service management.

- [`dependencies/`](dependencies/)  
  Project dependencies and requirements files.

- [`compose.yml`](compose.yml)
  Docker Compose configuration file for building and running all services.

## Getting Started

1. **Configure Environment:**  
   Edit `src/.env` to set environment variables as needed.

2. **Build and Run Services:**

   ```sh
   docker compose -f src/compose.yml up --build
   ```

3. **Development:**  
   Each service can be developed and tested independently. Shared models are imported from `src/common`.

> [!NOTE]
>
> - All services rely on the shared models in `src/common` for data validation and communication.
> - Configuration is in `.env` and in `compose.yml`.
> - For detailed information about each service or module, see the respective README files in their subdirectories or ask the authors directly.

---

For more details, refer to the documentation in each subdirectory or the main [README.md](../README.md).
