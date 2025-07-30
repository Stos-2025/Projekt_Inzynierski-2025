from fastapi import APIRouter
from security import get_api_key
from typing import Dict, List, Optional
from submission_repository import SubmissionRepository
from fastapi import HTTPException, Response, Depends, status
from common.schemas import SubmissionCreateSchema, SubmissionResultSchema,SubmissionStatus, SubmissionSchema

router = APIRouter(tags=["submissions"])


@router.put("/submissions/{submission_id}")
async def put_submission(
    submission_id: str,
    submission: SubmissionCreateSchema,
    repository: SubmissionRepository = Depends(SubmissionRepository.get),
    _: str = Depends(get_api_key)
) -> Response:
    with repository.session.begin():
        if repository.exists(submission_id):
            raise HTTPException(status_code=400, detail="Submission ID already exists.")
        submission = repository.create(submission_id, submission)
        submission.status = SubmissionStatus.PENDING

    print(f"Submission {submission_id} added with task URL {submission.task_url}.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/submissions/{submission_id}", response_model=SubmissionSchema)
async def get_submission(
    submission_id: str,
    repository: SubmissionRepository = Depends(SubmissionRepository.get),
    _: str = Depends(get_api_key)
) -> SubmissionSchema:
    with repository.session.begin():
        submission = repository.get_by_id(submission_id)
        if submission is None:
            raise HTTPException(status_code=404, detail="Submission not found.")
    return submission


@router.get("/submissions/{submission_id}/result", response_model=Optional[SubmissionResultSchema])
async def get_submission_result(
    submission_id: str,
    repository: SubmissionRepository = Depends(SubmissionRepository.get),
    _: str = Depends(get_api_key)
) -> Optional[SubmissionResultSchema]:
    with repository.session.begin():
        submission = repository.get_by_id(submission_id)
        if submission is None:
            raise HTTPException(status_code=404, detail="Submission not found.")
    return submission.to_schema().result


@router.patch("/submissions/{submission_id}/mark-as-reported")
async def mark_submission_as_reported(
    submission_id: str,
    repository: SubmissionRepository = Depends(SubmissionRepository.get),
    _: str = Depends(get_api_key)
) -> Response:
    with repository.session.begin():
        submission = repository.get_by_id(submission_id)
        if submission is None:
            raise HTTPException(status_code=404, detail="Submission not found.")
        if submission.status != SubmissionStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Submission is not completed.")
        submission.status = SubmissionStatus.REPORTED

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/submissions-completed", response_model=Dict[str, List[str]])
async def get_completed_submissions(
    skip: int = 0,
    limit: int = 100,
    repository: SubmissionRepository = Depends(SubmissionRepository.get),
    _: str = Depends(get_api_key)
) -> Dict[str, List[str]]:
    if skip < 0 or limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="Invalid pagination params")

    with repository.session.begin():
        completed = repository.get_submissions_by_status(SubmissionStatus.COMPLETED, skip, limit)
        if not completed:
            raise HTTPException(status_code=404, detail="No completed submissions found.")

        return {"submission_ids": [submission.id for submission in completed]}


@router.delete("/submissions/{submission_id}", response_model=SubmissionSchema)
async def pop_submission(
    submission_id: str,
    repository: SubmissionRepository = Depends(SubmissionRepository.get),
    _: str = Depends(get_api_key)                     
) -> SubmissionSchema:
    with repository.session.begin():
        submission = repository.get_by_id(submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        if repository.get_status(submission_id) != SubmissionStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Submission is not completed")
        repository.delete(submission_id)
        
        return submission