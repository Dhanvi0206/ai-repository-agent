from __future__ import annotations

import json


def export_report(report_data: dict, format_type: str = "json") -> tuple[str | bytes, str]:
    """Export report data in JSON, HTML, or lightweight PDF format."""
    format_type = format_type.lower()
    if format_type == "json":
        return json.dumps(report_data, indent=2), "application/json"

    if format_type == "html":
        html = _build_html_report(report_data)
        return html, "text/html"

    if format_type == "pdf":
        pdf_bytes = _build_minimal_pdf(report_data)
        return pdf_bytes, "application/pdf"

    raise ValueError(f"Unsupported export format: {format_type}")


def _build_html_report(report_data: dict) -> str:
    issue_items = "".join(
        f"<li><strong>{issue['issue']}</strong> ({issue['severity']}) - {issue['file']}</li>"
        for issue in report_data.get("issues", [])[:20]
    )
    return (
        "<html><body>"
        f"<h1>Repository Report: {report_data.get('repository')}</h1>"
        f"<p>Health Score: {report_data.get('health_score')}</p>"
        f"<ul>{issue_items}</ul>"
        "</body></html>"
    )


def _build_minimal_pdf(report_data: dict) -> bytes:
    title = f"Repository Report: {report_data.get('repository', 'unknown')}"
    body = f"Health Score: {report_data.get('health_score', 'n/a')}"
    content = f"BT /F1 16 Tf 72 720 Td ({title}) Tj 0 -24 Td ({body}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj",
        f"4 0 obj << /Length {len(content)} >> stream\n{content}\nendstream endobj",
        "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
    ]
    pdf = "%PDF-1.4\n"
    offsets = []
    for obj in objects:
        offsets.append(len(pdf.encode("utf-8")))
        pdf += obj + "\n"
    xref_offset = len(pdf.encode("utf-8"))
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets:
        pdf += f"{offset:010d} 00000 n \n"
    pdf += (
        "trailer << /Size "
        f"{len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    )
    return pdf.encode("utf-8")
