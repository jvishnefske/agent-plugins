#!/usr/bin/env python3
"""
.claude/hooks/verify_gate.py

Stop hook - blocks completion until make verify passes
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


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
    """Allow stop - just exit cleanly."""
    sys.exit(0)


def run_verify(project_dir: Path, timeout: int = 300) -> tuple[bool, str]:
    """Run make verify and return (success, output)."""
    try:
        result = subprocess.run(
            ["make", "verify"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"Verification timed out after {timeout}s"
    except FileNotFoundError:
        return False, "make not found - ensure build tools are installed"
    except Exception as e:
        return False, f"Verification error: {e}"


def main() -> None:
    input_data = load_input()
    
    # Prevent infinite loop - if we're already in a stop hook continuation, allow exit
    if input_data.get("stop_hook_active", False):
        allow()
    
    project_dir = Path(input_data.get("project_dir", ".")).resolve()
    
    # Check if Makefile exists
    makefile = project_dir / "Makefile"
    if not makefile.exists():
        # No Makefile - allow stop (plugin may not be fully configured)
        allow()
    
    # Run verification
    success, output = run_verify(project_dir)
    
    if success:
        allow()
    
    # Truncate long output
    max_len = 2000
    if len(output) > max_len:
        output = output[:max_len] + "\n... (truncated)"
    
    block(
        f"Verification failed. Fix issues before completing:\n\n"
        f"```\n{output}\n```\n\n"
        f"Run `make verify` to check your fixes."
    )


if __name__ == "__main__":
    main()
