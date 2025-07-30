
from submission_repository import SubmissionRepository
from fastapi import APIRouter, HTTPException, Response, Depends, status
from security import get_api_key 
from common.schemas import SubmissionWorkerSchema, SubmissionResultSchema,SubmissionStatus


router: APIRouter = APIRouter(
    prefix="/worker",
    tags=["worker"],
)


@router.put("/submissions/{submission_id}/result")
async def put_result(
    submission_id: str,
    submission_result: SubmissionResultSchema,
    repository: SubmissionRepository = Depends(SubmissionRepository.get),
    _: str = Depends(get_api_key)
) -> Response:
    with repository.session.begin():
        submission = repository.get_by_id(submission_id)
        if submission is None:
            raise HTTPException(status_code=404, detail="Submission not found.")
        if submission.status != SubmissionStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Submission is not in running state.")
        submission.result = submission_result.model_dump()
        submission.status = SubmissionStatus.COMPLETED

    print(f"Submission {submission_id} completed with points: {submission_result.points}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/submission", response_model=SubmissionWorkerSchema)
async def get_submission_worker(
    repository: SubmissionRepository = Depends(SubmissionRepository.get),
    _: str = Depends(get_api_key)
) -> SubmissionWorkerSchema:
    with repository.session.begin():
        submission = repository.get_submission_by_status_sorted_by_date(SubmissionStatus.PENDING)
        if submission is None:
            raise HTTPException(status_code=404, detail="No pending submissions.")
        submission.status = SubmissionStatus.RUNNING

    return submission
