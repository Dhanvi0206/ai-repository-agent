from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.state import analysis_service, error_response, success_response


router = APIRouter(tags=["Dependency Reports"])


@router.get("/dependency-risk/{repository_id}")
async def dependency_risk(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_dependency_risk(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached dependency report unavailable.",
                code="analysis_not_completed",
            ),
        )
