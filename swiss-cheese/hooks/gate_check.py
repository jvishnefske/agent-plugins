#!/usr/bin/env python3
"""
Swiss Cheese Gate Check - UserPromptSubmit hook.

Checks Makefile gate targets and reports status before each user prompt.
Stateless, lightweight validation using exit codes from make targets.

Exit codes from Makefile targets:
  0 = PASS
  Non-zero = FAIL

If no Makefile exists or target missing, silently proceeds.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple


class GateStatus(str, Enum):
    """Gate validation result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"


@dataclass(frozen=True)
class GateResult:
    """Immutable gate result."""
    layer: int
    name: str
    status: GateStatus
    message: Optional[str] = None


# Layer definitions: layer_num -> (name, make_target)
# Simplified 4-layer model combining swiss-cheese verification + ultraplan parallelism
LAYERS: dict[int, Tuple[str, str]] = {
    1: ("requirements", "validate-requirements"),
    2: ("tdd", "validate-tdd"),
    3: ("implementation", "validate-implementation"),
    4: ("verify", "validate-verify"),
}


def get_project_dir() -> Path:
    """Get project directory from environment or current directory."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))


def makefile_exists(project_dir: Path) -> bool:
    """Check if Makefile exists in project."""
    return (project_dir / "Makefile").exists()


def has_target(project_dir: Path, target: str) -> Tuple[bool, str]:
    """Check if Makefile has a specific target.

    Returns (exists, error_message).
    """
    try:
        result = subprocess.run(
            ["make", "-n", target],
            cwd=project_dir,
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0, ""
    except subprocess.TimeoutExpired:
        return False, "timeout checking target"
    except FileNotFoundError:
        return False, "make not found"
    except Exception as e:
        return False, str(e)


def run_gate(project_dir: Path, target: str, timeout: int = 3) -> Tuple[bool, str]:
    """Run a Makefile gate target.

    Returns (passed, output).
    """
    try:
        result = subprocess.run(
            ["make", target],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = (result.stdout + result.stderr)[-500:]
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, f"Gate timed out after {timeout}s"
    except FileNotFoundError:
        return False, "make not found"
    except Exception as e:
        return False, str(e)


def detect_current_layer(project_dir: Path) -> int:
    """Detect current layer by finding first failing gate.

    Returns the first layer that fails, or 4 if all pass.
    """
    if not makefile_exists(project_dir):
        return 1

    for layer_num in sorted(LAYERS.keys()):
        _, target = LAYERS[layer_num]
        exists, _ = has_target(project_dir, target)
        if not exists:
            continue
        passed, _ = run_gate(project_dir, target)
        if not passed:
            return layer_num

    return 4


def check_current_gate(project_dir: Path, layer: int) -> GateResult:
    """Check the gate for the specified layer."""
    if layer not in LAYERS:
        return GateResult(layer, "unknown", GateStatus.NOT_RUN)

    name, target = LAYERS[layer]

    if not makefile_exists(project_dir):
        return GateResult(layer, name, GateStatus.NOT_RUN, "No Makefile")

    exists, err = has_target(project_dir, target)
    if not exists:
        msg = f"No target: {target}" if not err else err
        return GateResult(layer, name, GateStatus.NOT_RUN, msg)

    passed, output = run_gate(project_dir, target)
    status = GateStatus.PASS if passed else GateStatus.FAIL

    return GateResult(layer, name, status, output if not passed else None)


def format_status_message(result: GateResult, layer: int) -> str:
    """Format gate status for display to user."""
    name = LAYERS.get(layer, ("unknown", ""))[0]
    lines = [
        "## Swiss Cheese Gate Status",
        "",
        f"**Current Layer**: {layer} - {name}",
        f"**Status**: {result.status.value}",
    ]

    if result.status == GateStatus.FAIL and result.message:
        target = LAYERS.get(layer, ("", "unknown"))[1]
        lines.extend([
            "",
            "**Gate Output**:",
            "```",
            result.message[:400],
            "```",
            "",
            f"Run `make {target}` to debug.",
        ])
    elif result.status == GateStatus.NOT_RUN and result.message:
        lines.extend([
            "",
            f"**Note**: {result.message}",
        ])

    return "\n".join(lines)


def main() -> None:
    """Entry point for UserPromptSubmit hook."""
    try:
        _ = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        pass

    project_dir = get_project_dir()

    # No Makefile = no gate validation, proceed silently
    if not makefile_exists(project_dir):
        print(json.dumps({"continue": True}))
        return

    # Check if any validate-* target exists
    has_any_target = False
    for _, target in LAYERS.values():
        exists, _ = has_target(project_dir, target)
        if exists:
            has_any_target = True
            break

    if not has_any_target:
        print(json.dumps({"continue": True}))
        return

    # Detect current layer and check gate
    current_layer = detect_current_layer(project_dir)
    result = check_current_gate(project_dir, current_layer)

    # Only show system message if gate failed
    if result.status == GateStatus.FAIL:
        message = format_status_message(result, current_layer)
        print(json.dumps({
            "continue": True,
            "systemMessage": message,
        }))
    else:
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
