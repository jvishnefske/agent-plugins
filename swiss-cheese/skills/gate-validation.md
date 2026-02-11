---
description: Use this skill when the user needs guidance on implementing gate validation, understanding exit codes, gate criteria by layer, the two-phase validation architecture, or failure analysis and routing.
---

# Gate Validation Skill

This skill provides guidance on implementing and validating verification gates using Makefile targets.

## Two-Phase Validation Architecture

Swiss Cheese uses a **read-only check** on every user prompt with **report generation on demand**:

### Phase 1: Fast Read-Only Check (UserPromptSubmit hook)

**File**: `hooks/gate_check.py`

- Reads `.swiss-cheese/reports/validation_report.json`
- Compares git hash in report vs current HEAD
- Reports staleness if hashes differ
- Shows gate failures from cached report
- **Target execution: <100ms**
- **Does NOT run make targets**

### Phase 2: Report Generation (on-demand)

**File**: `scripts/generate_reports.py`

- Run via `/swiss-cheese:generate-reports` command
- Executes all `make validate-*` targets
- Collects coverage, test results, traceability metrics
- Writes report with current git hash
- **Execution time: varies by project**

### Workflow

1. Developer makes changes
2. On each prompt, gate_check.py reads cached report
3. If report is stale (different git hash), shows warning
4. Developer runs `/swiss-cheese:generate-reports` to update
5. Report regenerates with current state

## Exit Code Standard

| Code | Meaning | Action |
|------|---------|--------|
| 0 | PASS | Advance to next layer |
| Non-zero | FAIL | Fix issues and retry |

## Gate Implementation

Each gate is a Makefile target that:

1. Checks prerequisites
2. Runs validation checks
3. Returns appropriate exit code
4. Outputs diagnostic information

### Makefile Target Template

```makefile
validate-<layer>:
	@echo "=== Validating <Layer> ==="
	@# Check prerequisites
	@test -f design.toml || (echo "ERROR: design.toml not found" && exit 1)
	@# Run validation
	@<validation-command> || exit 1
	@echo "<Layer> validation passed"
```

## Report File Format

**Location**: `.swiss-cheese/reports/validation_report.json`

```json
{
  "meta": {
    "git_hash": "3a31afb...",
    "git_hash_short": "3a31afb",
    "timestamp": "2026-02-03T12:30:45Z",
    "generator_version": "1.0.0"
  },
  "layers": {
    "requirements": { "status": "PASS", "checked_at": "..." },
    "tdd": { "status": "PASS", "checked_at": "..." },
    "implementation": { "status": "FAIL", "message": "...", "output": "..." },
    "verify": { "status": "NOT_RUN", "message": "Skipped" }
  },
  "coverage": {
    "line_percent": 68.5,
    "branch_percent": 55.2,
    "threshold": 70,
    "meets_threshold": false
  },
  "tests": {
    "total": 45, "passed": 43, "failed": 2, "skipped": 0, "all_passed": false
  },
  "traceability": {
    "requirements_count": 8,
    "requirements_with_tests": 6,
    "coverage_percent": 75.0,
    "unmapped_requirements": ["REQ-007", "REQ-008"]
  }
}
```

## Gate Criteria by Layer (Simplified 4-Layer Model)

### Gate 1: Requirements (`validate-requirements`)

```yaml
criteria:
  - design.toml exists and is valid TOML
  - all requirements have unique IDs (REQ-NNN)
  - all requirements have acceptance_criteria
  - safety requirements identified
```

### Gate 2: TDD (`validate-tdd`)

```yaml
criteria:
  - test files exist
  - tests compile (cargo test --no-run)
  - coverage plan defined
  - requirements traced to tests
```

### Gate 3: Implementation (`validate-implementation`)

```yaml
criteria:
  - cargo build succeeds
  - cargo test passes
  - no TODO/FIXME/unimplemented!
  - no_std compliant (if required)
```

### Gate 4: Verify (`validate-verify`)

```yaml
criteria:
  - all previous gates passed
  - traceability matrix complete
  - evidence chain documented
  - static analysis clean (clippy, audit)
```

## Staleness Detection

The read-only check compares git hashes:

```python
def check_staleness(report_hash: str, current_hash: str) -> StalenessResult:
    """
    Compare git hashes. If different, report is stale.
    Stale = informational warning, not a failure.
    """
    is_stale = report_hash[:7] != current_hash[:7]
    return StalenessResult(
        is_stale=is_stale,
        report_hash=report_hash[:7],
        current_hash=current_hash[:7]
    )
```

**Staleness is informational**: The check does not fail when stale, it just warns. This allows development to continue while reminding the developer to regenerate reports.

## Failure Analysis

When a gate fails, analyze root cause:

| Gate | Symptom | Root Cause | Route To |
|------|---------|------------|----------|
| 1 | Missing design.toml | No requirements | Create design.toml |
| 2 | Tests don't compile | API changes | Fix test code |
| 3 | Tests fail | Implementation bug | Layer 3 |
| 4 | clippy warnings | Code quality | Layer 3 |

## Integration with Orchestrator

The orchestrator uses the report for decision making:

```
User Prompt → gate_check.py reads report →
  All Pass + Fresh → Continue silently
  All Pass + Stale → Show staleness warning
  Gate Fail → Show failure details
```

Report generation is triggered explicitly via `/swiss-cheese:generate-reports`.
