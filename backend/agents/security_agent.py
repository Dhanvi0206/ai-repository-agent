from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from backend.agents.base_agent import BaseAgent
from backend.models.response_models import AgentIssue


SEVERITY_PENALTIES = {
    "critical": 30,
    "high": 18,
    "medium": 10,
    "low": 4,
}

PENALTY_CAPS = {
    "secrets_found": 75,
    "dangerous_patterns": 45,
    "dependency_vulnerabilities": 40,
}

SECRET_RULES = [
    (
        re.compile(r"AKIA[0-9A-Z]{16}"),
        "Potential AWS Access Key",
        "critical",
        "AWS-style access keys should never be committed to source control.",
        "Rotate the key immediately and move the credential into a secure secret manager.",
        0.98,
        30,
    ),
    (
        re.compile(r"ghp_[A-Za-z0-9]{36}"),
        "Potential GitHub Token",
        "critical",
        "GitHub personal access tokens expose repository and account access if committed.",
        "Revoke the token and replace it with an environment variable or secret manager reference.",
        0.97,
        30,
    ),
    (
        re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
        "Potential Google API Key",
        "high",
        "API keys embedded in code can be abused if the repository becomes public or leaks.",
        "Rotate the key and load it from a secure runtime configuration source.",
        0.95,
        22,
    ),
    (
        re.compile(r"(?i)(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        "Hardcoded Secret",
        "high",
        "Hardcoded credentials should not be stored in application code or config defaults.",
        "Move secrets to environment variables or a dedicated secret management service.",
        0.9,
        20,
    ),
    (
        re.compile(r"BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY"),
        "Embedded Private Key",
        "critical",
        "Private keys in a repository can be used directly by attackers if leaked.",
        "Remove the key from the repository, rotate it, and load key material securely at runtime.",
        0.99,
        32,
    ),
]

DANGEROUS_RULES = [
    (
        re.compile(r"\beval\s*\("),
        "Use of eval",
        "high",
        "Dynamic evaluation can execute attacker-controlled input and should be avoided.",
        "Replace eval with a safer parser or explicit dispatch logic.",
        0.92,
        14,
    ),
    (
        re.compile(r"\bexec\s*\("),
        "Use of exec",
        "high",
        "Dynamic code execution increases the risk of arbitrary code execution vulnerabilities.",
        "Avoid exec and use controlled imports or explicit function dispatch instead.",
        0.92,
        14,
    ),
    (
        re.compile(r"subprocess\.(Popen|run|call|check_output)\("),
        "Shell Execution Pattern",
        "medium",
        "Process execution paths should be reviewed for command injection and sandboxing concerns.",
        "Validate inputs, avoid shell execution, and prefer safer library APIs when possible.",
        0.78,
        8,
    ),
    (
        re.compile(r"os\.system\s*\("),
        "os.system Usage",
        "medium",
        "os.system can expose command injection risk when used with untrusted input.",
        "Switch to subprocess with validated arguments and avoid shell interpolation.",
        0.8,
        10,
    ),
    (
        re.compile(r"shell\s*=\s*True"),
        "shell=True Usage",
        "high",
        "shell=True expands the attack surface for command injection vulnerabilities.",
        "Pass arguments as a list and keep shell=False unless absolutely necessary.",
        0.9,
        14,
    ),
    (
        re.compile(r"yaml\.load\s*\("),
        "Unsafe YAML Load",
        "high",
        "yaml.load without a safe loader can deserialize unsafe payloads.",
        "Use yaml.safe_load or an explicitly safe loader.",
        0.88,
        14,
    ),
    (
        re.compile(r"pickle\.loads\s*\("),
        "Unsafe Pickle Deserialization",
        "high",
        "Pickle deserialization is unsafe for untrusted input and can lead to code execution.",
        "Avoid pickle for untrusted data and use a safer serialization format.",
        0.9,
        14,
    ),
    (
        re.compile(r"hashlib\.(md5|sha1)\s*\("),
        "Weak Hash Function",
        "medium",
        "Legacy hash functions like MD5 and SHA1 are weak for security-sensitive operations.",
        "Use SHA-256 or stronger primitives for security-sensitive hashing.",
        0.76,
        8,
    ),
    (
        re.compile(r"debug\s*=\s*True"),
        "Debug Mode Enabled",
        "medium",
        "Debug mode should not be enabled in production-facing code paths.",
        "Disable debug mode outside local development and guard it with environment-specific config.",
        0.74,
        6,
    ),
    (
        re.compile(r"requests\.(get|post|put|delete|request)\([^)]*verify\s*=\s*False"),
        "TLS Verification Disabled",
        "high",
        "Disabling TLS certificate verification weakens transport security and can enable man-in-the-middle attacks.",
        "Keep certificate verification enabled and install the required CA certificates instead of bypassing verification.",
        0.9,
        16,
    ),
    (
        re.compile(r"tempfile\.mktemp\s*\("),
        "Insecure Temporary File Usage",
        "medium",
        "tempfile.mktemp can introduce race conditions and insecure temporary file handling.",
        "Use NamedTemporaryFile, TemporaryDirectory, or mkstemp instead.",
        0.82,
        8,
    ),
]

IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "venv",
    ".venv",
    "coverage",
}

LOW_SIGNAL_DIRECTORIES = {
    "docs",
    "doc",
    "tests",
    "test",
    "examples",
    "example",
}

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".env",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
}

CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".php", ".rb"}

DEPENDENCY_WATCHLIST = {
    "pyyaml": ("Potentially Vulnerable Dependency", "medium", "Review PyYAML usage and ensure secure loader patterns are used."),
    "jinja2": ("Potentially Vulnerable Dependency", "medium", "Verify you are using a patched Jinja2 release and safe template practices."),
    "lodash": ("Potentially Vulnerable Dependency", "high", "Review lodash version against current advisories and upgrade if needed."),
    "serialize-javascript": ("Potentially Vulnerable Dependency", "high", "Upgrade serialize-javascript to a patched version."),
}


class SecurityAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("security_agent")

    def analyze_code(self, files: list[dict]) -> list[AgentIssue]:
        root = Path(self.repository_context.get("local_path", ""))
        issues: list[AgentIssue] = []
        security_summary = {
            "score": 100,
            "secrets_found": 0,
            "dangerous_patterns": 0,
            "dependency_vulnerabilities": 0,
            "penalties": {
                "secrets_found": 0,
                "dangerous_patterns": 0,
                "dependency_vulnerabilities": 0,
            },
            "files_scanned": 0,
        }

        if root.exists():
            issues.extend(self._scan_repository_files(root, security_summary))
            issues.extend(self._scan_dependencies(root, security_summary))
        else:
            issues.extend(self._scan_chunks(files, security_summary))

        security_summary["score"] = self._compute_security_score(security_summary)
        security_summary.pop("_seen_matches", None)
        self.repository_context["security_report"] = security_summary

        return issues

    def generate_report(self) -> str:
        return "Security agent scans repositories for secrets, dangerous execution patterns, and dependency risk."

    def _scan_repository_files(self, root: Path, security_summary: dict) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        for file_path in root.rglob("*"):
            if not file_path.is_file() or self._should_ignore(file_path, root):
                continue

            suffix = file_path.suffix.lower()
            if suffix not in TEXT_EXTENSIONS and file_path.name not in {"Dockerfile", ".env", "requirements.txt", "package.json"}:
                continue

            content = self._safe_read(file_path)
            if not content:
                continue

            security_summary["files_scanned"] += 1
            relative_path = str(file_path.relative_to(root)).replace("\\", "/")
            issues.extend(self._match_rules(relative_path, content, SECRET_RULES, security_summary, "secrets_found"))

            if suffix in CODE_EXTENSIONS or file_path.name in {"Dockerfile"}:
                issues.extend(
                    self._match_rules(
                        relative_path,
                        content,
                        DANGEROUS_RULES,
                        security_summary,
                        "dangerous_patterns",
                    )
                )

        return issues

    def _scan_dependencies(self, root: Path, security_summary: dict) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        requirements_path = root / "requirements.txt"
        package_json_path = root / "package.json"

        issues.extend(self._scan_requirements(requirements_path, security_summary))
        issues.extend(self._scan_package_json(package_json_path, security_summary))
        issues.extend(self._scan_external_dependency_tools(root, requirements_path, package_json_path, security_summary))

        return issues

    def _scan_requirements(self, requirements_path: Path, security_summary: dict) -> list[AgentIssue]:
        if not requirements_path.exists():
            return []

        issues: list[AgentIssue] = []
        lines = self._safe_read(requirements_path).splitlines()
        for line_number, line in enumerate(lines, start=1):
            normalized = line.strip().lower()
            if not normalized or normalized.startswith("#"):
                continue

            package_name = re.split(r"[<>=!~\[]", normalized, maxsplit=1)[0].strip()
            if package_name in DEPENDENCY_WATCHLIST:
                issue_type, severity, recommendation = DEPENDENCY_WATCHLIST[package_name]
                self._record_summary_hit(security_summary, "dependency_vulnerabilities", severity)
                issues.append(
                    self.create_issue(
                        file_path="requirements.txt",
                        line_number=line_number,
                        issue_type=issue_type,
                        severity=severity,
                        description=f"Dependency '{line.strip()}' should be reviewed for known advisories.",
                        reasoning="Security scoring tracks dependency manifests that include historically risky packages.",
                        recommendation=recommendation,
                        confidence_score=0.74 if severity == "medium" else 0.82,
                    )
                )
            elif "==" not in normalized:
                self._record_summary_hit(security_summary, "dependency_vulnerabilities", "low")
                issues.append(
                    self.create_issue(
                        file_path="requirements.txt",
                        line_number=line_number,
                        issue_type="Unpinned Python Dependency",
                        severity="low",
                        description=f"Dependency '{line.strip()}' is not pinned to an exact version.",
                        reasoning="Unpinned dependencies make security patching and reproducibility harder to track.",
                        recommendation="Pin dependency versions or use a lock file for reproducible secure builds.",
                        confidence_score=0.62,
                    )
                )

        return issues

    def _scan_package_json(self, package_json_path: Path, security_summary: dict) -> list[AgentIssue]:
        if not package_json_path.exists():
            return []

        issues: list[AgentIssue] = []
        try:
            package_data = json.loads(self._safe_read(package_json_path))
        except json.JSONDecodeError:
            return issues

        dependencies = {
            **package_data.get("dependencies", {}),
            **package_data.get("devDependencies", {}),
        }
        for name, version in dependencies.items():
            normalized_name = name.lower()
            if normalized_name in DEPENDENCY_WATCHLIST:
                issue_type, severity, recommendation = DEPENDENCY_WATCHLIST[normalized_name]
                self._record_summary_hit(security_summary, "dependency_vulnerabilities", severity)
                issues.append(
                    self.create_issue(
                        file_path="package.json",
                        issue_type=issue_type,
                        severity=severity,
                        description=f"Dependency '{name}' ({version}) should be reviewed for known advisories.",
                        reasoning="Security scoring tracks package manifests that include historically risky packages.",
                        recommendation=recommendation,
                        confidence_score=0.8 if severity == "high" else 0.72,
                    )
                )
            elif str(version).strip().startswith(("^", "~", "*")):
                self._record_summary_hit(security_summary, "dependency_vulnerabilities", "low")
                issues.append(
                    self.create_issue(
                        file_path="package.json",
                        issue_type="Loosely Pinned JavaScript Dependency",
                        severity="low",
                        description=f"Dependency '{name}' uses a floating range ({version}).",
                        reasoning="Floating dependency ranges can silently introduce insecure updates or drift across environments.",
                        recommendation="Use a lock file and review whether the dependency should be pinned more tightly.",
                        confidence_score=0.61,
                    )
                )

        return issues

    def _scan_external_dependency_tools(
        self,
        root: Path,
        requirements_path: Path,
        package_json_path: Path,
        security_summary: dict,
    ) -> list[AgentIssue]:
        issues: list[AgentIssue] = []

        pip_audit = shutil.which("pip-audit")
        if pip_audit and requirements_path.exists():
            try:
                result = subprocess.run(
                    [pip_audit, "-r", str(requirements_path)],
                    capture_output=True,
                    text=True,
                    timeout=20,
                    check=False,
                )
                vulnerability_count = sum(
                    1
                    for line in result.stdout.splitlines()
                    if line.strip() and "No known vulnerabilities found" not in line
                )
                if vulnerability_count > 0:
                    for _ in range(vulnerability_count):
                        self._record_summary_hit(security_summary, "dependency_vulnerabilities", "high")
                    issues.append(
                        self.create_issue(
                            file_path="requirements.txt",
                            issue_type="pip-audit Vulnerability Report",
                            severity="high",
                            description=f"pip-audit reported {vulnerability_count} dependency vulnerability findings.",
                            reasoning="Automated dependency auditing surfaced package vulnerabilities in the Python dependency set.",
                            recommendation="Review the pip-audit output and upgrade affected dependencies.",
                            confidence_score=0.9,
                        )
                    )
            except Exception:
                pass

        npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
        if npm_cmd and package_json_path.exists():
            try:
                result = subprocess.run(
                    [npm_cmd, "audit", "--json"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=25,
                    check=False,
                )
                audit_data = json.loads(result.stdout or "{}")
                metadata = audit_data.get("metadata", {}).get("vulnerabilities", {})
                vulnerability_count = sum(int(metadata.get(level, 0)) for level in ("critical", "high", "moderate", "low"))
                if vulnerability_count > 0:
                    for severity, count in (
                        ("critical", int(metadata.get("critical", 0))),
                        ("high", int(metadata.get("high", 0))),
                        ("medium", int(metadata.get("moderate", 0))),
                        ("low", int(metadata.get("low", 0))),
                    ):
                        for _ in range(count):
                            self._record_summary_hit(security_summary, "dependency_vulnerabilities", severity)
                    issues.append(
                        self.create_issue(
                            file_path="package.json",
                            issue_type="npm audit Vulnerability Report",
                            severity="high" if metadata.get("critical", 0) or metadata.get("high", 0) else "medium",
                            description=f"npm audit reported {vulnerability_count} dependency vulnerability findings.",
                            reasoning="Automated dependency auditing surfaced risky packages in the JavaScript dependency tree.",
                            recommendation="Review npm audit output and upgrade or patch affected dependencies.",
                            confidence_score=0.9,
                        )
                    )
            except Exception:
                pass

        return issues

    def _scan_chunks(self, files: list[dict], security_summary: dict) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        for chunk in files:
            content = chunk.get("chunk", "")
            file_path = chunk.get("file", "repository")
            security_summary["files_scanned"] += 1
            issues.extend(self._match_rules(file_path, content, SECRET_RULES, security_summary, "secrets_found"))
            issues.extend(self._match_rules(file_path, content, DANGEROUS_RULES, security_summary, "dangerous_patterns"))
        return issues

    def _match_rules(
        self,
        file_path: str,
        content: str,
        rules: list[tuple],
        security_summary: dict,
        counter_key: str,
    ) -> list[AgentIssue]:
        issues: list[AgentIssue] = []
        seen_matches = security_summary.setdefault("_seen_matches", set())
        for pattern, issue_type, severity, reasoning, recommendation, confidence, _penalty in rules:
            for match in pattern.finditer(content):
                line_number = self._line_number(content, match.start())
                fingerprint = f"{file_path}:{issue_type}:{line_number}"
                if fingerprint in seen_matches:
                    continue

                seen_matches.add(fingerprint)
                self._record_summary_hit(security_summary, counter_key, severity)
                issues.append(
                    self.create_issue(
                        file_path=file_path,
                        line_number=line_number,
                        issue_type=issue_type,
                        severity=severity,
                        description=f"{issue_type} detected in repository contents.",
                        reasoning=reasoning,
                        recommendation=recommendation,
                        confidence_score=confidence,
                    )
                )
        return issues

    def _should_ignore(self, file_path: Path, root: Path) -> bool:
        relative_parts = file_path.relative_to(root).parts
        return any(
            part.startswith(".") or part in IGNORED_DIRECTORIES or part.lower() in LOW_SIGNAL_DIRECTORIES
            for part in relative_parts[:-1]
        )

    def _safe_read(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""

    def _line_number(self, content: str, position: int) -> int:
        return max(1, content[:position].count("\n") + 1)

    def _record_summary_hit(self, security_summary: dict, counter_key: str, severity: str) -> None:
        security_summary[counter_key] += 1
        security_summary["penalties"][counter_key] = min(
            PENALTY_CAPS[counter_key],
            security_summary["penalties"].get(counter_key, 0) + SEVERITY_PENALTIES.get(severity, 6),
        )

    def _compute_security_score(self, security_summary: dict) -> float:
        penalties = security_summary.get("penalties", {})
        total_penalty = (
            penalties.get("secrets_found", 0)
            + penalties.get("dangerous_patterns", 0)
            + penalties.get("dependency_vulnerabilities", 0)
        )

        # Reward repositories that scan cleanly across a meaningful number of files.
        files_scanned = int(security_summary.get("files_scanned", 0) or 0)
        confidence_bonus = 3 if files_scanned >= 50 and total_penalty == 0 else 0

        return round(max(0.0, min(100.0, 100 - total_penalty + confidence_bonus)), 2)
