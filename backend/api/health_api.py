from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.api.state import analysis_service, error_response, success_response


router = APIRouter(tags=["Health Reports"])


@router.get("/repo-health/{repository_id}")
async def repo_health(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_repository_health(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached report unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/issues")
async def paginated_issues(repo_id: str, page: int = 1, limit: int = 20) -> dict:
    try:
        return success_response(analysis_service.get_issues(repo_id, page, limit))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached report unavailable.",
                code="analysis_not_completed",
            ),
        )
