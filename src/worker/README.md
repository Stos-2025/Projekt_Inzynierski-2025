# Worker Service

This directory contains the **worker** service for the STOS project. The worker is responsible for fetching tasks from the master service, executing them in isolated containers, and reporting the results.

## Files

- [`worker.py`](src/worker/worker.py)  
  The main script for the worker service. It is responsible for:
  - Fetching submissions from the master service (`/worker/submission` endpoint).
  - Downloading problem and submission files.
  - Preparing the working environment for each task.
  - Running compilation, execution, and judging in separate Docker containers.
  - Collecting test results and reporting them back to the master (`/worker/submissions/{submission_id}/result` endpoint).
  - Handling system signals and periodically checking for new submissions.

- [`dockerfile`](src/worker/dockerfile)  
  The Dockerfile for building the worker image:
  - Based on the `docker:dind` (Docker-in-Docker) image.
  - Installs required dependencies: Python, requests, pydantic.
  - Copies the source code and shared models.
  - Creates a `stos` user and sets necessary environment variables.
  - Sets the default entrypoint to run `worker.py`.

## Environment Variables

- `MASTER_URL` – address of the master service.
- `WORKERS_DATA_LOCAL_PATH` – path to the worker's data directory inside the container.
- `WORKERS_DATA_HOST_PATH` – path to the worker's data directory on the host.
- `COMP_IMAGE_NAME`, `EXEC_IMAGE_NAME`, `JUDGE_IMAGE_NAME` – names of Docker images for compilation, execution, and judging.

## Building and Running

To build the worker image:
```sh
docker build -t stos_worker ./src/worker
```

To run the service using docker-compose, use the [`src/conf/up.sh`](src/conf/up.sh) script or the [`src/conf/compose.yml`](src/conf/compose.yml) file.

## Workflow

1. The worker periodically requests new submissions from the master.
2. Upon receiving a submission, it downloads the problem and submission files.
3. Prepares the working directories.
4. Runs compilation, execution, and judging in separate containers.
5. Collects test results and reports them to the master.
6. Waits for the next submission.

---

For more information about the architecture, see the main [README.md](README.md) file.