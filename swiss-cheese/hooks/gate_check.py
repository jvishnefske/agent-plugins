#!/usr/bin/env python3
"""
Swiss Cheese Gate Check - UserPromptSubmit hook (Read-Only).

Reads validation_report.json and checks staleness against current git hash.
Does NOT run make targets - that's done by generate_reports.py.

Target execution time: <100ms
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Tuple


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


@dataclass(frozen=True)
class StalenessResult:
    """Staleness check result."""
    is_stale: bool
    report_hash: str
    current_hash: str


@dataclass(frozen=True)
class ValidationReport:
    """Parsed validation report."""
    git_hash: str
    git_hash_short: str
    timestamp: str
    layers: dict[str, dict[str, Any]]
    coverage: Optional[dict[str, Any]] = None
    tests: Optional[dict[str, Any]] = None
    traceability: Optional[dict[str, Any]] = None


# Layer definitions: layer_num -> (name, make_target)
# Simplified 4-layer model
LAYERS: dict[int, Tuple[str, str]] = {
    1: ("requirements", "validate-requirements"),
    2: ("tdd", "validate-tdd"),
    3: ("implementation", "validate-implementation"),
    4: ("verify", "validate-verify"),
}

# Report file location relative to project root
REPORT_PATH = Path(".swiss-cheese/reports/validation_report.json")


def get_project_dir() -> Path:
    """Get project directory from environment or current directory."""
    return Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd()))


def get_current_git_hash(project_dir: Path) -> str:
    """Get current HEAD git hash.

    Returns empty string if not a git repo or git unavailable.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""


def read_report(report_path: Path) -> Optional[ValidationReport]:
    """Read and parse validation_report.json.

    Returns None if file doesn't exist or is invalid JSON.
    """
    if not report_path.exists():
        return None

    try:
        data = json.loads(report_path.read_text())
        meta = data.get("meta", {})
        return ValidationReport(
            git_hash=meta.get("git_hash", ""),
            git_hash_short=meta.get("git_hash_short", ""),
            timestamp=meta.get("timestamp", ""),
            layers=data.get("layers", {}),
            coverage=data.get("coverage"),
            tests=data.get("tests"),
            traceability=data.get("traceability"),
        )
    except (json.JSONDecodeError, OSError, KeyError):
        return None


def check_staleness(report_hash: str, current_hash: str) -> StalenessResult:
    """Compare git hashes. If different, report is stale.

    Stale = informational warning, not a failure.
    """
    # Use short hashes for comparison (7 chars)
    report_short = report_hash[:7] if report_hash else ""
    current_short = current_hash[:7] if current_hash else ""

    is_stale = bool(report_short and current_short and report_short != current_short)

    return StalenessResult(
        is_stale=is_stale,
        report_hash=report_short,
        current_hash=current_short,
    )


def get_first_failing_layer(report: ValidationReport) -> Optional[Tuple[int, str, str]]:
    """Find first failing layer from report.

    Returns (layer_num, layer_name, message) or None if all pass.
    """
    for layer_num in sorted(LAYERS.keys()):
        layer_name, _ = LAYERS[layer_num]
        layer_data = report.layers.get(layer_name, {})
        status = layer_data.get("status", "NOT_RUN")

        if status == "FAIL":
            message = layer_data.get("message", "")
            output = layer_data.get("output", "")
            return (layer_num, layer_name, message or output or "Gate failed")

    return None


def format_staleness_warning(staleness: StalenessResult) -> str:
    """Format staleness warning message."""
    return (
        f"**Warning**: Report is stale (report: {staleness.report_hash}, "
        f"HEAD: {staleness.current_hash}). "
        "Run `/swiss-cheese:generate-reports` to update."
    )


def format_status_message(
    result: GateResult,
    layer: int,
    staleness: Optional[StalenessResult] = None
) -> str:
    """Format gate status for display to user."""
    name = LAYERS.get(layer, ("unknown", ""))[0]
    lines = [
        "## Swiss Cheese Gate Status",
        "",
        f"**Current Layer**: {layer} - {name}",
        f"**Status**: {result.status.value}",
    ]

    if staleness and staleness.is_stale:
        lines.extend([
            "",
            format_staleness_warning(staleness),
        ])

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
    """Entry point for UserPromptSubmit hook.

    Read-only behavior:
    - No report file -> proceed silently
    - Report exists, not stale, all pass -> proceed silently
    - Report exists, stale -> show staleness warning
    - Report exists, gate failed -> show failure + staleness if applicable
    """
    try:
        _ = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        pass

    project_dir = get_project_dir()
    report_path = project_dir / REPORT_PATH

    # No report file = no gate validation, proceed silently
    report = read_report(report_path)
    if report is None:
        print(json.dumps({"continue": True}))
        return

    # Check staleness
    current_hash = get_current_git_hash(project_dir)
    staleness = check_staleness(report.git_hash, current_hash)

    # Find first failing layer
    failure = get_first_failing_layer(report)

    if failure is None:
        # All gates pass
        if staleness.is_stale:
            # Show staleness warning even when passing
            print(json.dumps({
                "continue": True,
                "systemMessage": (
                    "## Swiss Cheese Gate Status\n\n"
                    "**Status**: All gates PASS\n\n"
                    + format_staleness_warning(staleness)
                ),
            }))
        else:
            print(json.dumps({"continue": True}))
        return

    # Gate failed - show status message
    layer_num, layer_name, message = failure
    result = GateResult(
        layer=layer_num,
        name=layer_name,
        status=GateStatus.FAIL,
        message=message,
    )

    status_message = format_status_message(result, layer_num, staleness)
    print(json.dumps({
        "continue": True,
        "systemMessage": status_message,
    }))


if __name__ == "__main__":
    main()
