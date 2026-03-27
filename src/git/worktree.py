import subprocess
import os
from pathlib import Path
from typing import Optional, Dict
import json


class GitWorktreeManager:
    """Manages git worktrees for parallel agent branches."""

    def __init__(self, repo_path: str, worktree_base: str = "/tmp/agent-worktrees"):
        self.repo_path = Path(repo_path)
        self.worktree_base = Path(worktree_base)
        self.worktree_base.mkdir(parents=True, exist_ok=True)

    def create_worktree(self, branch_name: str, agent_type: str) -> Path:
        """Create a new worktree for an agent branch."""
        worktree_path = self.worktree_base / f"{agent_type}-{branch_name}"
        worktree_path.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            if "already exists" in result.stderr:
                return worktree_path
            raise RuntimeError(f"Failed to create worktree: {result.stderr}")

        return worktree_path

    def create_branch(self, branch_name: str, base_branch: str = "main") -> str:
        """Create a new branch for agent work."""
        result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create branch: {result.stderr}")

        return branch_name

    def create_pr(self, branch_name: str, title: str, body: str) -> str:
        """Create a PR for the agent's changes."""
        result = subprocess.run(
            [
                "gh",
                "pr",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--head",
                branch_name,
            ],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to create PR: {result.stderr}")

        return result.stdout.strip()

    def cleanup_worktree(self, worktree_path: Path):
        """Remove a worktree after agent completes."""
        result = subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"Failed to remove worktree: {result.stderr}")

    def get_worktree_status(self) -> Dict[str, any]:
        """Get status of all worktrees."""
        result = subprocess.run(
            ["git", "worktree", "list", "--json"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
