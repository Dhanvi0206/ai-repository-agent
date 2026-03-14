from __future__ import annotations

from collections import defaultdict

from backend.collaboration.confidence_fusion import fuse_confidence
from backend.models.reasoning_models import AgentReasoningOutput


class ResultAggregator:
    """Merge overlapping agent findings into collaboration groups."""

    def aggregate(self, reasoning_outputs: list[AgentReasoningOutput]) -> list[dict]:
        grouped: dict[str, list[AgentReasoningOutput]] = defaultdict(list)
        for output in reasoning_outputs:
            grouped[_issue_key(output)].append(output)

        aggregated_results: list[dict] = []
        for issue_key, outputs in grouped.items():
            representative = max(outputs, key=lambda output: output.confidence)
            aggregated_results.append(
                {
                    "issue_key": issue_key,
                    "issue": representative.issue_type,
                    "file_path": representative.file_path,
                    "line_number": representative.line_number,
                    "severity": _combined_severity([output.severity for output in outputs]),
                    "recommendation": representative.recommendation,
                    "reasoning_chain": [
                        f"{output.agent} detected {output.issue_type.lower()}."
                        for output in outputs
                    ],
                    "detected_by": sorted({output.agent for output in outputs}),
                    "raw_outputs": outputs,
                    "confidence": fuse_confidence(
                        [(output.agent, output.confidence) for output in outputs]
                    ),
                }
            )

        return aggregated_results


def _combined_severity(severities: list[str]) -> str:
    severity_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    return max(severities, key=lambda severity: severity_order.get(severity, 0))


def _issue_key(output: AgentReasoningOutput) -> str:
    return f"{output.file_path}:{output.line_number or 0}:{output.issue_type}"
