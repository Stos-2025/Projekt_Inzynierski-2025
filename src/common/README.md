# Common Module

The `common` directory contains shared model and DTO definitions used by various services in the STOS project.

## Files

- [`models.py`](src/common/models.py)  
  Contains Pydantic classes describing main data structures, such as:
  - [`TestResult`](src/common/models.py)
  - [`SubmissionResult`](src/common/models.py)
  - [`Test`](src/common/models.py)
  - [`Problem`](src/common/models.py)
  - [`Submission`](src/common/models.py)

- [`dtos.py`](src/common/dtos.py)  
  Defines Data Transfer Objects (DTOs), e.g. [`SubmissionWorkerDto`](src/common/dtos.py), used for communication between services.

## Purpose

All services (e.g. master, worker, adapter) use these shared data models to ensure consistency in information exchange and validation.

## Extending

To add a new model or DTO:
1. Add the appropriate class to `models.py` or `dtos.py`.
2. Make sure to use Pydantic types (`BaseModel`).
3. Import the new model in the services that require it.
