from __future__ import annotations

import json
from pathlib import Path

from backend.agents.base_agent import BaseAgent
from backend.models.response_models import AgentIssue


DEPRECATED_PACKAGES = {"django-rest-swagger", "urllib3<1.26", "request"}
KNOWN_VULNERABLE_PACKAGES = {"lodash", "pyyaml", "jinja2"}


class DependencyAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("dependency_agent")

    def analyze_code(self, files: list[dict]) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        root = Path(self.repository_context.get("local_path", "."))

        for dependency_file in ("requirements.txt", "package.json", "pom.xml"):
            target_file = root / dependency_file
            if not target_file.exists():
                continue

            if dependency_file == "requirements.txt":
                issues.extend(self._analyze_requirements(target_file))
            elif dependency_file == "package.json":
                issues.extend(self._analyze_package_json(target_file))
            elif dependency_file == "pom.xml":
                issues.extend(self._analyze_pom(target_file))

        return issues

    def generate_report(self) -> str:
        return "Dependency agent reviews dependency manifests for risky or outdated packages."

    def _analyze_requirements(self, file_path: Path) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line_number, line in enumerate(lines, start=1):
            normalized = line.strip().lower()
            if not normalized or normalized.startswith("#"):
                continue
            if any(pkg in normalized for pkg in KNOWN_VULNERABLE_PACKAGES | DEPRECATED_PACKAGES):
                issues.append(
                    self.create_issue(
                        file_path="requirements.txt",
                        line_number=line_number,
                        issue_type="Potentially Risky Dependency",
                        severity="medium",
                        description=f"Dependency entry '{line.strip()}' may be outdated or vulnerable.",
                        reasoning="Dependency manifests should avoid deprecated or historically vulnerable packages.",
                        recommendation="Review the dependency version and upgrade to the latest secure release.",
                        confidence_score=0.7,
                    )
                )
        return issues

    def _analyze_package_json(self, file_path: Path) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        try:
            package_data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return issues

        dependencies = package_data.get("dependencies", {}) | package_data.get("devDependencies", {})
        for name, version in dependencies.items():
            if name.lower() in KNOWN_VULNERABLE_PACKAGES:
                issues.append(
                    self.create_issue(
                        file_path="package.json",
                        issue_type="Known Vulnerability Candidate",
                        severity="high",
                        description=f"Dependency '{name}' ({version}) should be reviewed for known CVEs.",
                        reasoning="This package appears on the local high-risk dependency watchlist.",
                        recommendation="Cross-check with a vulnerability database and upgrade if a fix exists.",
                        confidence_score=0.76,
                    )
                )
        return issues

    def _analyze_pom(self, file_path: Path) -> list[AgentIssue]:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        if "<version>LATEST</version>" not in content:
            return []
        return [
            self.create_issue(
                file_path="pom.xml",
                issue_type="Floating Dependency Version",
                severity="medium",
                description="Maven dependency uses a floating version such as LATEST.",
                reasoning="Floating versions reduce build reproducibility and can introduce unexpected issues.",
                recommendation="Pin the dependency to a tested version and track updates explicitly.",
                confidence_score=0.72,
            )
        ]
