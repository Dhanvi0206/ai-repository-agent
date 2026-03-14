from __future__ import annotations

import re

from backend.agents.base_agent import BaseAgent
from backend.models.response_models import AgentIssue


SECRET_PATTERNS = [
    (re.compile(r"password\s*=\s*['\"].+['\"]", re.IGNORECASE), "Hardcoded Credential", "high"),
    (re.compile(r"api[_-]?key\s*=\s*['\"].+['\"]", re.IGNORECASE), "Hardcoded API Key", "high"),
    (re.compile(r"jwt[_-]?secret\s*=\s*['\"].+['\"]", re.IGNORECASE), "Hardcoded JWT Secret", "high"),
    (re.compile(r"BEGIN\s+(RSA|DSA|EC)\s+PRIVATE\s+KEY"), "Embedded Private Key", "critical"),
    (re.compile(r"SELECT\s+.+\+\s*\w+", re.IGNORECASE), "Potential SQL Injection", "high"),
]


class SecurityAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("security_agent")

    def analyze_code(self, files: list[dict]) -> list[AgentIssue]:
        issues: list[AgentIssue] = []

        for chunk in files:
            content = chunk.get("chunk", "")
            for pattern, issue_type, severity in SECRET_PATTERNS:
                match = pattern.search(content)
                if not match:
                    continue

                line_number = chunk.get("start_line", 1) + content[: match.start()].count("\n")
                issues.append(
                    self.create_issue(
                        file_path=chunk["file"],
                        line_number=line_number,
                        issue_type=issue_type,
                        severity=severity,
                        description=f"{issue_type} detected in source code.",
                        reasoning="Sensitive values or unsafe query patterns should not appear directly in application code.",
                        recommendation="Move secrets to secure configuration and parameterize database queries.",
                        confidence_score=0.92 if severity in {"high", "critical"} else 0.78,
                    )
                )

        return issues

    def generate_report(self) -> str:
        return "Security agent scans for secrets, unsafe SQL, and key material."
