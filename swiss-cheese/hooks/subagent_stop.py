#!/usr/bin/env python3
"""
SubagentStop hook - triggers git rebase if worktree branch not in linear history.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def load_input() -> dict[str, Any]:
    """Load hook input from stdin."""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def block(reason: str) -> None:
    """Output block decision and exit."""
    print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def allow() -> None:
    """Allow - just exit cleanly."""
    sys.exit(0)


def run_git(args: list[str], cwd: Path) -> tuple[bool, str]:
    """Run git command and return (success, output)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def is_worktree(path: Path) -> bool:
    """Check if path is a git worktree (not the main repo)."""
    git_dir = path / ".git"
    if not git_dir.exists():
        return False
    # Worktrees have .git as a file pointing to the main repo
    return git_dir.is_file()


def get_worktree_branch(path: Path) -> Optional[str]:
    """Get the branch name for a worktree."""
    success, output = run_git(["rev-parse", "--abbrev-ref", "HEAD"], path)
    if success and output and output != "HEAD":
        return output
    return None


def get_main_branch(path: Path) -> str:
    """Determine the main branch name (main or master)."""
    success, output = run_git(["rev-parse", "--verify", "refs/heads/main"], path)
    if success:
        return "main"
    return "master"


def is_branch_in_linear_history(path: Path, branch: str, main_branch: str) -> bool:
    """Check if branch commits are in main's linear history (rebased/merged)."""
    # Get the merge-base between branch and main
    success, merge_base = run_git(["merge-base", branch, main_branch], path)
    if not success:
        return False

    # Get the tip of the branch
    success, branch_tip = run_git(["rev-parse", branch], path)
    if not success:
        return False

    # If merge-base equals branch tip, branch is fully merged/rebased
    if merge_base == branch_tip:
        return True

    # Check if all commits from branch are in main (rebased with different SHAs)
    # Use cherry to find commits in branch not in main
    success, output = run_git(["cherry", main_branch, branch], path)
    if not success:
        return False

    # Lines starting with '+' are commits not in main
    unpicked = [line for line in output.splitlines() if line.startswith("+")]
    return len(unpicked) == 0


def get_main_repo_path(worktree_path: Path) -> Optional[Path]:
    """Get the main repository path from a worktree."""
    success, output = run_git(["rev-parse", "--git-common-dir"], worktree_path)
    if success and output:
        git_common = Path(output)
        if git_common.name == ".git":
            return git_common.parent
        return git_common.parent
    return None


def main() -> None:
    input_data = load_input()
    cwd = Path(input_data.get("cwd", ".")).resolve()

    # Only process if we're in a worktree
    if not is_worktree(cwd):
        allow()

    # Get branch info
    branch = get_worktree_branch(cwd)
    if not branch:
        allow()

    # Get main repo to check against main branch
    main_repo = get_main_repo_path(cwd)
    if not main_repo:
        allow()

    main_branch = get_main_branch(main_repo)

    # Check if branch is in linear history
    if is_branch_in_linear_history(main_repo, branch, main_branch):
        allow()

    # Branch not in linear history - trigger rebase
    block(
        f"## Rebase Required\n\n"
        f"Worktree branch `{branch}` has not been rebased into `{main_branch}`.\n\n"
        f"### Rebase Instructions\n\n"
        f"1. Ensure all changes are committed in worktree\n"
        f"2. Switch to main repo: `cd {main_repo}`\n"
        f"3. Update main: `git checkout {main_branch} && git pull`\n"
        f"4. Rebase branch:\n"
        f"   ```bash\n"
        f"   git checkout {branch}\n"
        f"   git rebase {main_branch}\n"
        f"   ```\n"
        f"5. Resolve any conflicts\n"
        f"6. Force push if needed: `git push --force-with-lease origin {branch}`\n"
        f"7. Return to worktree: `cd {cwd}`\n\n"
        f"### Or Fast-Forward Merge\n\n"
        f"If rebase is not needed (branch is ready):\n"
        f"```bash\n"
        f"cd {main_repo}\n"
        f"git checkout {main_branch}\n"
        f"git merge --ff-only {branch}\n"
        f"```\n"
    )


if __name__ == "__main__":
    main()
