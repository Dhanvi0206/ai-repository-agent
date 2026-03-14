from __future__ import annotations

import json
from pathlib import Path


class CodebaseSummaryEngine:
    """Build a high-level, developer-friendly summary of a repository."""

    def generate_summary(self, repository_report: dict, repository_metadata: dict) -> dict:
        local_path = Path(repository_metadata.get("local_path", "")) if repository_metadata.get("local_path") else None
        framework = self._detect_framework(local_path)
        primary_language = self._detect_primary_language(local_path, repository_report)
        project_type = self._detect_project_type(framework, primary_language)
        key_modules = self._extract_key_modules(repository_report)
        architecture = self._detect_architecture(local_path, key_modules)
        main_functionality = self._detect_main_functionality(project_type, key_modules, local_path)
        dependency_map = self._build_module_dependency_map(key_modules, repository_report)
        complexity_overview = self._complexity_overview(repository_report)

        return {
            "repository_overview": {
                "type": project_type,
                "primary_language": primary_language,
                "main_functionality": main_functionality,
                "key_modules": key_modules,
            },
            "architecture_detection": architecture,
            "module_dependency_mapping": dependency_map,
            "code_complexity_overview": complexity_overview,
            "natural_language_summary": self._natural_language_summary(
                project_type,
                primary_language,
                main_functionality,
                key_modules,
                complexity_overview,
            ),
        }

    def _detect_framework(self, local_path: Path | None) -> str | None:
        if not local_path or not local_path.exists():
            return None

        requirements = local_path / "requirements.txt"
        if requirements.exists():
            content = requirements.read_text(encoding="utf-8", errors="ignore").lower()
            if "flask" in content:
                return "Flask"
            if "django" in content:
                return "Django"
            if "fastapi" in content:
                return "FastAPI"

        package_json = local_path / "package.json"
        if package_json.exists():
            try:
                package_data = json.loads(package_json.read_text(encoding="utf-8", errors="ignore"))
            except json.JSONDecodeError:
                package_data = {}
            dependencies = {
                **package_data.get("dependencies", {}),
                **package_data.get("devDependencies", {}),
            }
            dependency_names = {name.lower() for name in dependencies}
            if "react" in dependency_names:
                return "React"
            if "next" in dependency_names or "next.js" in dependency_names:
                return "Next.js"
            if "express" in dependency_names:
                return "Express"

        return None

    def _detect_primary_language(self, local_path: Path | None, repository_report: dict) -> str:
        if local_path and local_path.exists():
            counts: dict[str, int] = {}
            extension_map = {
                ".py": "Python",
                ".js": "JavaScript",
                ".ts": "TypeScript",
                ".java": "Java",
                ".go": "Go",
                ".rs": "Rust",
                ".php": "PHP",
                ".cpp": "C++",
                ".c": "C",
            }
            for file_path in local_path.rglob("*"):
                if not file_path.is_file() or ".git" in file_path.parts:
                    continue
                language = extension_map.get(file_path.suffix.lower())
                if language:
                    counts[language] = counts.get(language, 0) + 1
            if counts:
                return max(counts.items(), key=lambda item: item[1])[0]

        owner = repository_report.get("owner")
        if owner:
            return "Python"
        return "Unknown"

    def _detect_project_type(self, framework: str | None, primary_language: str) -> str:
        if framework == "Flask":
            return "Flask Web Application"
        if framework == "Django":
            return "Django Web Application"
        if framework == "FastAPI":
            return "FastAPI Service"
        if framework == "React":
            return "React Frontend Application"
        if framework == "Next.js":
            return "Next.js Web Application"
        if framework == "Express":
            return "Express API Service"
        if primary_language != "Unknown":
            return f"{primary_language} Application"
        return "Software Repository"

    def _extract_key_modules(self, repository_report: dict) -> list[str]:
        module_scores: dict[str, int] = {}
        for issue in repository_report.get("issues", []):
            file_path = issue.get("file") or ""
            module = self._module_name_from_path(file_path)
            if not module:
                continue
            module_scores[module] = module_scores.get(module, 0) + 1

        fallback_modules = []
        for issue_group in (
            repository_report.get("security_report", {}).get("security_issues", []),
            repository_report.get("code_quality_report", {}).get("code_quality_issues", []),
        ):
            for issue in issue_group:
                module = self._module_name_from_path(issue.get("file", ""))
                if module and module not in fallback_modules:
                    fallback_modules.append(module)

        ranked = [name for name, _ in sorted(module_scores.items(), key=lambda item: item[1], reverse=True)]
        modules = ranked[:5] or fallback_modules[:5]
        return modules or ["core application"]

    def _detect_architecture(self, local_path: Path | None, key_modules: list[str]) -> str:
        if not local_path or not local_path.exists():
            return "Layered architecture signals detected."

        names = {path.name.lower() for path in local_path.rglob("*") if path.is_file()}
        if {"models.py", "views.py", "controllers.py"} & names:
            return "MVC architecture detected."
        if {"routes.py", "schemas.py", "services.py"} & names:
            return "Service-oriented API architecture detected."
        if any("auth" in module for module in key_modules):
            return "Modular web application architecture detected."
        return "Layered application structure detected."

    def _detect_main_functionality(
        self,
        project_type: str,
        key_modules: list[str],
        local_path: Path | None,
    ) -> str:
        key_modules_lower = [module.lower() for module in key_modules]
        if "web" in project_type.lower() or "api" in project_type.lower():
            if any("auth" in module for module in key_modules_lower):
                return "REST API service with authentication features"
            return "Web application and API service"
        if local_path and (local_path / "package.json").exists():
            return "Frontend application"
        return "General-purpose software service"

    def _build_module_dependency_map(
        self,
        key_modules: list[str],
        repository_report: dict,
    ) -> list[str]:
        relationships: list[str] = []
        seen: set[str] = set()
        for issue in repository_report.get("issues", []):
            file_path = issue.get("file", "")
            module = self._module_name_from_path(file_path)
            if module not in key_modules:
                continue
            related = self._infer_related_module(issue)
            if related and related != module:
                relation = f"{module} depends on {related}"
                if relation not in seen:
                    seen.add(relation)
                    relationships.append(relation)
        return relationships[:5]

    def _complexity_overview(self, repository_report: dict) -> str:
        quality_issues = repository_report.get("code_quality_report", {}).get(
            "code_quality_issues",
            [],
        )
        if not quality_issues:
            return "Code complexity appears manageable across the main modules."

        top_issue = quality_issues[0]
        module = self._module_name_from_path(top_issue.get("file", ""))
        if module:
            return f"{module.capitalize()} module has elevated complexity and may need refactoring."
        return "Several modules show elevated complexity and should be reviewed."

    def _natural_language_summary(
        self,
        project_type: str,
        primary_language: str,
        main_functionality: str,
        key_modules: list[str],
        complexity_overview: str,
    ) -> str:
        module_text = ", ".join(key_modules[:3])
        return (
            f"This repository is a {project_type.lower()} built primarily with "
            f"{primary_language}. It appears to implement {main_functionality.lower()}, "
            f"with key modules such as {module_text}. {complexity_overview}"
        )

    def _module_name_from_path(self, file_path: str) -> str | None:
        if not file_path:
            return None
        parts = [part for part in Path(file_path).parts if part not in {"src", "app", "backend", "tests"}]
        if not parts:
            return None
        candidate = Path(parts[-1]).stem.lower()
        if candidate in {"__init__", "index", "main", "app"} and len(parts) > 1:
            candidate = parts[-2].lower()
        return candidate.replace("_", " ")

    def _infer_related_module(self, issue: dict) -> str | None:
        issue_text = " ".join(
            str(issue.get(key, "")) for key in ("issue", "reasoning", "fix")
        ).lower()
        for module_hint in ("database", "auth", "config", "api", "user", "route"):
            if module_hint in issue_text:
                return module_hint
        return None
