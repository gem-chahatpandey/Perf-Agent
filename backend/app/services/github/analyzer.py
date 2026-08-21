import httpx
from app.core.config import settings
from app.core.logging import logger


class GitHubAnalyzer:
    def __init__(self):
        self._token = settings.github_token

    @property
    def is_configured(self) -> bool:
        return bool(self._token)

    async def analyze_pr(self, repo: str, pr_number: int) -> dict:
        if not self._token:
            raise RuntimeError("GitHub token not configured")

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github.v3+json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            pr_resp = await client.get(f"https://api.github.com/repos/{repo}/pulls/{pr_number}", headers=headers)
            pr_resp.raise_for_status()
            pr_data = pr_resp.json()

            files_resp = await client.get(f"https://api.github.com/repos/{repo}/pulls/{pr_number}/files", headers=headers)
            files_resp.raise_for_status()
            files_data = files_resp.json()

        changed_files = []
        changed_services = set()
        changed_endpoints = []
        changed_db_files = []

        for file_info in files_data:
            filename = file_info.get("filename", "")
            changed_files.append({
                "filename": filename,
                "status": file_info.get("status", ""),
                "additions": file_info.get("additions", 0),
                "deletions": file_info.get("deletions", 0),
                "changes": file_info.get("changes", 0),
            })

            parts = filename.split("/")
            if len(parts) > 1:
                changed_services.add(parts[0])

            lower = filename.lower()
            if "controller" in lower or "route" in lower or "endpoint" in lower or "api" in lower:
                changed_endpoints.append(filename)
            if "dao" in lower or "repository" in lower or "migration" in lower or "sql" in lower:
                changed_db_files.append(filename)

        return {
            "pr_number": pr_number,
            "title": pr_data.get("title", ""),
            "author": pr_data.get("user", {}).get("login", ""),
            "state": pr_data.get("state", ""),
            "changed_files_count": len(changed_files),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
            "changed_files": changed_files,
            "changed_services": sorted(changed_services),
            "changed_endpoints": changed_endpoints,
            "changed_db_files": changed_db_files,
        }


github_analyzer = GitHubAnalyzer()
