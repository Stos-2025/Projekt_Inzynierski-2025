# Configuration (`conf`) Directory

> [!WARNING]
> Work is still in progress. This file can be outdated.

This directory contains configuration files and scripts for building and running the STOS project services.

## Files

- [`compose.yml`](../../src/conf/compose.yml)  
  Docker Compose file that defines and connects the main services: master, worker, and adapter.

- [`.env`](../../src/conf/.env)  
  Environment variable definitions used by Docker Compose and services.

  **Main variables:**
  - `STOS_FILES` – Path to the shared files directory (used by containers).
  - `GUI_URL` – URL of the GUI/frontend service.
  - `DOCKER_SOCK` – Path to the Docker socket for container management.
  - `DOCKER_GID` – Docker group ID (for permissions inside containers).
  - `COMP_IMAGE_NAME`, `EXEC_IMAGE_NAME`, `JUDGE_IMAGE_NAME` – Docker image names for the compiler, executor, and judge services.

  > [!IMPORTANT]
  > Edit this file to match your environment and deployment setup.

- [`dev/`](../../src/conf/dev/)  
  (Optional) Python virtual environment for local development.

## Usage

To build and start all services, run:
```sh
docker compose -f src/conf/compose.yml up --build
```

> [!NOTE]
> - Update the `.env` file to configure service-specific environment variables.
> - The `dev/` folder is not required for production and can be ignored if running in containers.

---
For more information, see the main [README.md](../README.md)