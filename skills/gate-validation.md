# Gate Validation Skill

This skill provides guidance on implementing and validating verification gates that return exit codes.

## Exit Code Standard

| Code | Meaning | Action |
|------|---------|--------|
| 0 | PASS | Advance to next layer |
| 1 | FAIL | Route to root cause layer |
| 2 | BLOCKED | Resolve prerequisites first |
| 3 | SKIP | Approved skip, advance |

## Gate Implementation Pattern

Each gate is a shell script or command that:

1. Checks prerequisites
2. Runs validation checks
3. Returns appropriate exit code
4. Outputs diagnostic information

### Template

```bash
#!/bin/bash
# gate-N.sh - Gate N validation

set -e  # Exit on error

ARTIFACTS=".swiss-cheese/artifacts/layer-N"
STATE=".swiss-cheese/state.json"

# Check prerequisites
check_prerequisites() {
  # Previous layer must be complete
  local prev_status=$(jq -r '.layers["N-1"].status' "$STATE")
  if [[ "$prev_status" != "PASS" ]]; then
    echo "BLOCKED: Layer N-1 not complete"
    exit 2
  fi
  
  # Required artifacts must exist
  if [[ ! -d "$ARTIFACTS" ]]; then
    echo "BLOCKED: Layer N artifacts not found"
    exit 2
  fi
}

# Run validation checks
run_checks() {
  local failures=0
  
  # Check 1: ...
  if ! check_1; then
    echo "FAIL: Check 1 failed - description"
    failures=$((failures + 1))
  fi
  
  # Check 2: ...
  if ! check_2; then
    echo "FAIL: Check 2 failed - description"
    failures=$((failures + 1))
  fi
  
  return $failures
}

# Main
main() {
  check_prerequisites
  
  if run_checks; then
    echo "PASS: Gate N"
    exit 0
  else
    echo "FAIL: Gate N - $(run_checks) checks failed"
    exit 1
  fi
}

main "$@"
```

## Gate Criteria by Layer

### Gate 1: Requirements

```yaml
criteria:
  - all_requirements_have_ids: "FR-*/SR-* format"
  - all_requirements_testable: "acceptance criteria defined"
  - safety_requirements_traced: "derived from hazards"
  - no_blocker_issues: "issues[].severity != BLOCKER"
  - rust_constraints_specified: "no_std, panic policy, etc"
```

### Gate 2: Architecture

```yaml
criteria:
  - types_defined: "newtype wrappers for domain values"
  - ownership_model: "no shared mutable state without sync"
  - error_types: "comprehensive error enum"
  - state_machines: "all states and transitions documented"
  - no_circular_deps: "dependency graph is acyclic"
```

### Gate 3: TDD Tests

```yaml
criteria:
  - tests_compile: "cargo test --no-run succeeds"
  - tests_fail: "cargo test fails (no implementation)"
  - coverage_plan: "targets defined"
  - requirements_traced: "each requirement has test(s)"
  - property_tests: "invariants have proptest/quickcheck"
```

### Gate 4: Implementation

```yaml
criteria:
  - builds: "cargo build succeeds"
  - tests_pass: "cargo test succeeds"
  - no_incomplete: "no TODO/FIXME/unimplemented!"
  - no_std_compliant: "if required"
```

### Gate 5: Static Analysis

```yaml
criteria:
  - clippy_clean: "no deny-level violations"
  - audit_clean: "no known vulnerabilities"
  - deny_clean: "license/source policy satisfied"
  - unsafe_justified: "all unsafe blocks documented"
```

### Gate 6: Formal Verification

```yaml
criteria:
  - harnesses_pass: "Kani proofs succeed"
  - contracts_verified: "Prusti contracts hold"
  - assumptions_documented: "all verification assumptions listed"
  - critical_properties: "overflow, bounds, panic freedom"
```

### Gate 7: Dynamic Analysis

```yaml
criteria:
  - miri_clean: "no undefined behavior"
  - coverage_met: "line/branch targets achieved"
  - fuzz_clean: "no crashes in corpus"
  - timing_met: "WCET within budget"
```

### Gate 8: Review

```yaml
criteria:
  - review_complete: "independent review conducted"
  - no_critical: "no critical findings open"
  - major_resolved: "all major findings addressed"
  - assumptions_audited: "all assumptions validated"
```

### Gate 9: Safety

```yaml
criteria:
  - hazards_mitigated: "all hazards have verified mitigations"
  - evidence_complete: "safety case has evidence chain"
  - risks_accepted: "residual risks documented and accepted"
  - decision_made: "RELEASE or HOLD decision recorded"
```

## Failure Analysis

When a gate fails, analyze root cause:

```python
def analyze_failure(gate: int, reason: str) -> int:
    """Return layer to route failure to."""
    
    # Layer 5 failures
    if gate == 5:
        if "clippy::unwrap" in reason:
            return 4  # Implementation issue
        if "cargo-audit" in reason:
            return 5  # Fix at this layer
        if "unsafe" in reason:
            return 4  # Implementation issue
    
    # Layer 7 failures
    if gate == 7:
        if "miri" in reason:
            return 4  # Unsafe implementation bug
        if "coverage" in reason:
            return 3  # Need more tests
        if "timing" in reason:
            return 4  # Implementation too slow
    
    # Default: previous layer
    return max(1, gate - 1)
```

## Recording Results

Gate results are recorded in `.swiss-cheese/gates/`:

```yaml
# gate-5-result.yaml
gate: 5
timestamp: "2024-01-15T10:30:00Z"
exit_code: 0
status: "PASS"
duration_ms: 45000
checks:
  - name: "clippy"
    status: "PASS"
    command: "cargo clippy ..."
    output: ""
  - name: "cargo-audit"
    status: "PASS"
    command: "cargo audit"
    output: "0 vulnerabilities found"
```

## Integration with Loop

The loop calls gates:

```bash
# Run gate
/swiss-cheese:gate $layer
exit_code=$?

case $exit_code in
  0) advance_layer ;;
  1) route_to_root_cause ;;
  2) resolve_prerequisites ;;
  3) skip_approved ;;
esac
```
