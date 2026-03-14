from __future__ import annotations

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from backend.api.state import analysis_service, success_response
from backend.models.response_models import AnalyzeRepositoryRequest, CompareRepositoriesRequest
from backend.stability.error_handler import AppError, format_error_response


router = APIRouter(tags=["Repository Analysis"])


@router.post("/analyze-repository")
async def analyze_repository(payload: AnalyzeRepositoryRequest) -> dict:
    try:
        job_data = analysis_service.start_analysis(str(payload.repo_url))
        return success_response(job_data)
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=format_error_response(exc)) from exc


@router.post("/compare-repositories")
async def compare_repositories(payload: CompareRepositoriesRequest) -> dict:
    try:
        comparison = analysis_service.compare_repositories(
            payload.repo_a_id,
            payload.repo_b_id,
        )
        return success_response(comparison)
    except KeyError as exc:
        missing_repo = payload.repo_a_id if payload.repo_a_id not in analysis_service.repository_index and not analysis_service.get_cached_report(payload.repo_a_id) else payload.repo_b_id
        raise HTTPException(
            status_code=404,
            detail=format_error_response(
                AppError(
                    message=f"Repository comparison data unavailable for {missing_repo}.",
                    error_type="analysis_not_completed",
                    status_code=404,
                )
            ),
        ) from exc


@router.websocket("/ws/analysis-progress")
async def analysis_progress(websocket: WebSocket) -> None:
    await analysis_service.websocket_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        analysis_service.websocket_manager.disconnect(websocket)
    except Exception:
        analysis_service.websocket_manager.disconnect(websocket)
