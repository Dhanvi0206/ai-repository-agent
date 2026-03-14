from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.state import analysis_service, error_response, success_response


router = APIRouter(tags=["Job Status"])


@router.get("/analysis-status/{job_id}")
async def get_analysis_status(job_id: str) -> dict:
    job = analysis_service.get_job_status(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=error_response("Analysis job not found.", code="job_not_found"),
        )
    return success_response(job)


@router.get("/agent-status")
async def get_agent_status(job_id: str) -> dict:
    status = analysis_service.get_agent_status(job_id)
    if not status:
        raise HTTPException(
            status_code=404,
            detail=error_response("Agent execution status not found.", code="agent_status_not_found"),
        )
    return success_response(status)
