from __future__ import annotations

from pathlib import Path


class TechnicalDebtEngine:
    """Estimate technical debt from repository issues and lightweight file heuristics."""

    WEIGHTS = {
        "long_function": 8,
        "high_complexity": 10,
        "duplicate_logic": 9,
        "missing_docstring": 4,
        "missing_tests": 12,
    }

    def analyze(self, repository_report: dict, repository_metadata: dict) -> dict:
        issues = repository_report.get("issues", [])
        local_path_value = repository_metadata.get("local_path")
        local_path = Path(local_path_value) if local_path_value else None

        file_scores: dict[str, int] = {}
        file_reasons: dict[str, list[str]] = {}
        module_scores: dict[str, int] = {}
        debt_reasons: list[str] = []
        recommendations: list[str] = []

        for issue in issues:
            issue_type = issue.get("issue", "")
            weight = self._issue_weight(issue_type)
            file_path = issue.get("file", "repository")
            module = self._module_name(file_path)

            file_scores[file_path] = min(file_scores.get(file_path, 0) + weight, 100)
            module_scores[module] = min(module_scores.get(module, 0) + weight, 100)

            reason = self._reason_from_issue(issue_type, file_path)
            file_reasons.setdefault(file_path, []).append(reason)
            if reason not in debt_reasons:
                debt_reasons.append(reason)

            recommendation = issue.get("fix", {}).get("summary")
            if recommendation and recommendation not in recommendations:
                recommendations.append(recommendation)

        missing_test_penalty = 0
        if local_path and local_path.exists():
            missing_test_penalty = self._missing_test_penalty(local_path, file_scores, module_scores, debt_reasons)

        raw_score = sum(file_scores.values()) + missing_test_penalty
        file_count = max(len(file_scores), 1)
        technical_debt_score = min(round(raw_score / file_count), 100)

        highest_module = None
        if module_scores:
            highest_module = max(module_scores.items(), key=lambda item: item[1])

        return {
            "technical_debt_score": technical_debt_score,
            "debt_reasons": debt_reasons[:10],
            "file_level_debt": [
                {
                    "file": file_path,
                    "debt_score": score,
                    "reasons": file_reasons.get(file_path, [])[:3],
                }
                for file_path, score in sorted(
                    file_scores.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )[:10]
            ],
            "module_level_debt": {
                "highest_debt_module": highest_module[0] if highest_module else None,
                "highest_debt_score": highest_module[1] if highest_module else 0,
                "module_scores": module_scores,
            },
            "refactoring_recommendations": recommendations[:8],
        }

    def _issue_weight(self, issue_type: str) -> int:
        normalized = issue_type.strip().lower().replace(" ", "_")
        return self.WEIGHTS.get(normalized, 5)

    def _reason_from_issue(self, issue_type: str, file_path: str) -> str:
        reasons = {
            "Long Function": f"Large functions detected in {file_path}",
            "High Complexity": f"High cyclomatic-style complexity detected in {file_path}",
            "Duplicate Logic": f"Code duplication detected in {file_path}",
            "Missing Docstring": f"Missing documentation detected in {file_path}",
        }
        return reasons.get(issue_type, f"Maintainability issue detected in {file_path}")

    def _module_name(self, file_path: str) -> str:
        parts = [part for part in Path(file_path).parts if part not in {"src", "tests", "backend", "app"}]
        if not parts:
            return "repository"
        if len(parts) > 1:
            return parts[-2].replace("_", " ")
        return Path(parts[-1]).stem.replace("_", " ")

    def _missing_test_penalty(
        self,
        local_path: Path,
        file_scores: dict[str, int],
        module_scores: dict[str, int],
        debt_reasons: list[str],
    ) -> int:
        source_files = []
        test_files = []
        for file_path in local_path.rglob("*"):
            if not file_path.is_file() or ".git" in file_path.parts:
                continue
            suffix = file_path.suffix.lower()
            if suffix not in {".py", ".js", ".ts", ".java"}:
                continue
            relative = file_path.relative_to(local_path).as_posix()
            if "/tests/" in f"/{relative}/" or Path(relative).name.startswith("test_"):
                test_files.append(relative)
            else:
                source_files.append(relative)

        if not source_files:
            return 0

        penalty = 0
        test_blob = " ".join(test_files).lower()
        for source_file in source_files[:50]:
            module = self._module_name(source_file)
            stem = Path(source_file).stem.lower()
            if stem and stem not in test_blob:
                penalty += 1
                file_scores[source_file] = min(file_scores.get(source_file, 0) + 2, 100)
                module_scores[module] = min(module_scores.get(module, 0) + 2, 100)

        if penalty:
            debt_reasons.append("Missing tests were detected for several source modules")
        return min(penalty * self.WEIGHTS["missing_tests"], 30)
