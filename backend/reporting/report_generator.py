from __future__ import annotations

from backend.reporting.reporting_agent import ReportingAgent


def generate_repository_report(analysis_response) -> dict:
    """Convert backend analysis into a final Reporting Agent repository report."""
    return ReportingAgent().generate_report(analysis_response)
