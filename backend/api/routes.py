from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.api.analysis_api import router as analysis_router
from backend.api.dependency_api import router as dependency_router
from backend.api.developer_api import router as developer_router
from backend.api.health_api import router as health_router
from backend.api.job_status_api import router as job_status_router
from backend.api.state import analysis_service, error_response, success_response
from backend.models.response_models import HealthResponse
from backend.reporting.report_exporter import export_report


router = APIRouter()
router.include_router(analysis_router)
router.include_router(job_status_router)
router.include_router(health_router)
router.include_router(developer_router)
router.include_router(dependency_router)


@router.get("/", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="online",
        service="ai-repository-agent-backend",
        message="Backend server is running.",
    )


@router.get("/repository-report", tags=["Reporting"])
async def repository_report(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_repository_report(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached repository report unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/issue-details", tags=["Reporting"])
async def issue_details(repository_id: str, issue_key: str | None = None) -> dict:
    try:
        return success_response(analysis_service.get_issue_details(repository_id, issue_key))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached issue report unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/developer-report", tags=["Reporting"])
async def developer_report(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_developer_score(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached developer report unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/score-explanation", tags=["Reporting"])
async def score_explanation(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_score_explanation(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached score explanation unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/risk-predictions", tags=["Reporting"])
async def risk_predictions(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_risk_predictions(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached risk predictions unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/repository-summary", tags=["Reporting"])
async def repository_summary(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_repository_summary(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached repository summary unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/developer-intelligence", tags=["Reporting"])
async def developer_intelligence(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_developer_intelligence(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached developer intelligence unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/technical-debt", tags=["Reporting"])
async def technical_debt(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_technical_debt(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached technical debt report unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/risk-heatmap", tags=["Reporting"])
async def risk_heatmap(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_risk_heatmap(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached risk heatmap unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/priority-fixes", tags=["Reporting"])
async def priority_fixes(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_priority_fixes(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached priority fixes unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/knowledge-insights", tags=["Reporting"])
async def knowledge_insights(repository_id: str | None = None) -> dict:
    try:
        return success_response(analysis_service.get_knowledge_insights(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached repository report unavailable for knowledge insights.",
                code="analysis_not_completed",
            ),
        )


@router.get("/dashboard-data", tags=["Reporting"])
async def dashboard_data(repository_id: str) -> dict:
    try:
        return success_response(analysis_service.get_dashboard_data(repository_id))
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached dashboard data unavailable.",
                code="analysis_not_completed",
            ),
        )


@router.get("/export-report", tags=["Reporting"])
async def export_repository_report(repository_id: str, format: str = "json") -> Response:
    try:
        report = analysis_service.get_repository_report(repository_id)
        content, media_type = export_report(report, format)
        extension = format.lower()
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="repository-report.{extension}"'
            },
        )
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=error_response(
                "Analysis job not completed or cached repository report unavailable.",
                code="analysis_not_completed",
            ),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=error_response(str(exc), code="invalid_export_format"),
        ) from exc
