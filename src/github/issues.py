import subprocess
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class GitHubIssue:
    number: int
    title: str
    body: str
    labels: List[str]
    assignee: Optional[str] = None


class GitHubIssuesClient:
    """GitHub Issues integration for task sourcing."""

    def __init__(self, repo: str, token: Optional[str] = None):
        self.repo = repo
        self.token = token or self._get_token()
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get_token(self) -> str:
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
        return result.stdout.strip()

    def get_issue(self, issue_number: int) -> GitHubIssue:
        """Fetch a single issue by number."""
        import requests

        response = requests.get(
            f"https://api.github.com/repos/{self.repo}/issues/{issue_number}",
            headers=self.headers,
        )
        response.raise_for_status()
        data = response.json()

        return GitHubIssue(
            number=data["number"],
            title=data["title"],
            body=data["body"] or "",
            labels=[l["name"] for l in data.get("labels", [])],
            assignee=data.get("assignee", {}).get("login"),
        )

    def list_issues(
        self, labels: Optional[List[str]] = None, state: str = "open"
    ) -> List[GitHubIssue]:
        """List issues with optional label filtering."""
        import requests

        params = {"state": state}
        if labels:
            params["labels"] = ",".join(labels)

        response = requests.get(
            f"https://api.github.com/repos/{self.repo}/issues",
            headers=self.headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        return [
            GitHubIssue(
                number=item["number"],
                title=item["title"],
                body=item["body"] or "",
                labels=[l["name"] for l in item.get("labels", [])],
                assignee=item.get("assignee", {}).get("login"),
            )
            for item in data
        ]

    def add_comment(self, issue_number: int, comment: str):
        """Add a comment to an issue."""
        import requests

        response = requests.post(
            f"https://api.github.com/repos/{self.repo}/issues/{issue_number}/comments",
            headers=self.headers,
            json={"body": comment},
        )
        response.raise_for_status()

    def close_issue(self, issue_number: int):
        """Close an issue after completion."""
        import requests

        response = requests.patch(
            f"https://api.github.com/repos/{self.repo}/issues/{issue_number}",
            headers=self.headers,
            json={"state": "closed"},
        )
        response.raise_for_status()
