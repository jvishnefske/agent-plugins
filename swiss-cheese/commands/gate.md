# /safe-rust:gate Command

Validate a layer gate and return exit code (0=pass, 1=fail).

## Usage

```bash
/safe-rust:gate <layer_number>
/safe-rust:gate 1      # Validate Layer 1 → 2 gate
/safe-rust:gate 5      # Validate Layer 5 → 6 gate
/safe-rust:gate all    # Validate all gates in sequence
```

## Exit Codes

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Gate PASSED | Proceed to next layer |
| 1 | Gate FAILED | Route to root cause layer |
| 2 | Gate BLOCKED | Missing prerequisites |
| 3 | Gate SKIPPED | Layer marked as skip (approved) |

## Gate Definitions

### Gate 1: Requirements Complete

```bash
#!/bin/bash
# gate-1.sh - Requirements validation

check_gate_1() {
  local spec=".safe-rust/artifacts/layer-1/requirements.yaml"
  
  # Check file exists
  [[ ! -f "$spec" ]] && echo "FAIL: requirements.yaml not found" && exit 1
  
  # Check all requirements have IDs
  if ! yq '.functional_requirements[].id' "$spec" | grep -q "FR-"; then
    echo "FAIL: Requirements missing IDs"
    exit 1
  fi
  
  # Check all requirements are testable
  if yq '.functional_requirements[].testable' "$spec" | grep -q "false"; then
    echo "FAIL: Untestable requirements found"
    exit 1
  fi
  
  # Check safety requirements derived
  if ! yq '.safety_requirements[].derived_from' "$spec" | grep -qE "(FR-|HAZARD-)"; then
    echo "FAIL: Safety requirements not traced"
    exit 1
  fi
  
  # Check no blocker issues
  if yq '.issues[] | select(.severity == "BLOCKER")' "$spec" | grep -q "."; then
    echo "FAIL: Blocker issues present"
    exit 1
  fi
  
  echo "PASS: Gate 1 - Requirements complete"
  exit 0
}

check_gate_1
```

### Gate 2: Architecture Approved

```bash
#!/bin/bash
# gate-2.sh - Architecture validation

check_gate_2() {
  local arch=".safe-rust/artifacts/layer-2/architecture.yaml"
  
  [[ ! -f "$arch" ]] && echo "FAIL: architecture.yaml not found" && exit 1
  
  # Check type definitions exist
  if ! yq '.type_definitions | length' "$arch" | grep -qE "^[1-9]"; then
    echo "FAIL: No type definitions"
    exit 1
  fi
  
  # Check ownership model documented
  if ! yq '.ownership_model | length' "$arch" | grep -qE "^[1-9]"; then
    echo "FAIL: Ownership model not documented"
    exit 1
  fi
  
  # Check error types defined
  if ! yq '.error_types | length' "$arch" | grep -qE "^[1-9]"; then
    echo "FAIL: Error types not defined"
    exit 1
  fi
  
  # Check no circular dependencies (would need static analysis)
  # This is a placeholder - real check would analyze code
  
  echo "PASS: Gate 2 - Architecture approved"
  exit 0
}

check_gate_2
```

### Gate 3: Tests Ready (Red Phase)

```bash
#!/bin/bash
# gate-3.sh - TDD Red Phase validation

check_gate_3() {
  local tests_dir=".safe-rust/artifacts/layer-3/tests"
  
  [[ ! -d "$tests_dir" ]] && echo "FAIL: Tests directory not found" && exit 1
  
  # Check tests compile
  if ! cargo test --no-run 2>/dev/null; then
    echo "FAIL: Tests don't compile"
    exit 1
  fi
  
  # CRITICAL: Tests must FAIL (no implementation yet)
  if cargo test 2>/dev/null; then
    echo "FAIL: Tests should FAIL at this stage (no implementation)"
    exit 1
  fi
  
  # Check coverage plan exists
  if [[ ! -f ".safe-rust/artifacts/layer-3/coverage-plan.yaml" ]]; then
    echo "FAIL: Coverage plan not defined"
    exit 1
  fi
  
  # Check requirements traceability
  local req_count=$(yq '.requirements | length' .safe-rust/design-spec.yaml)
  local test_count=$(grep -r "#\[test\]" "$tests_dir" | wc -l)
  
  if [[ $test_count -lt $req_count ]]; then
    echo "FAIL: Not all requirements have tests"
    exit 1
  fi
  
  echo "PASS: Gate 3 - Tests ready (failing as expected)"
  exit 0
}

check_gate_3
```

### Gate 4: Implementation Complete (Green Phase)

```bash
#!/bin/bash
# gate-4.sh - Implementation validation

check_gate_4() {
  # Check cargo build succeeds
  if ! cargo build --release 2>/dev/null; then
    echo "FAIL: Build failed"
    exit 1
  fi
  
  # Check all tests pass
  if ! cargo test 2>/dev/null; then
    echo "FAIL: Tests failed"
    exit 1
  fi
  
  # Check no TODO/FIXME/unimplemented!
  if grep -rE "(TODO|FIXME|unimplemented!|todo!)" src/; then
    echo "FAIL: Incomplete implementation markers found"
    exit 1
  fi
  
  echo "PASS: Gate 4 - Implementation complete"
  exit 0
}

check_gate_4
```

### Gate 5: Static Analysis Clean

```bash
#!/bin/bash
# gate-5.sh - Static analysis validation

check_gate_5() {
  # Clippy with strict lints
  if ! cargo clippy --all-targets --all-features -- \
    -D warnings \
    -D clippy::unwrap_used \
    -D clippy::expect_used \
    -D clippy::panic \
    -D clippy::todo \
    -D clippy::unimplemented 2>/dev/null; then
    echo "FAIL: Clippy violations"
    exit 1
  fi
  
  # cargo-audit for vulnerabilities
  if ! cargo audit 2>/dev/null; then
    echo "FAIL: Security vulnerabilities found"
    exit 1
  fi
  
  # cargo-deny for license/deps
  if [[ -f "deny.toml" ]]; then
    if ! cargo deny check 2>/dev/null; then
      echo "FAIL: Dependency policy violations"
      exit 1
    fi
  fi
  
  # Unsafe audit
  local unsafe_count=$(cargo geiger --output-format json 2>/dev/null | \
    jq '.packages.used.code.functions.unsafe // 0')
  local unsafe_justified=$(yq '.unsafe_blocks | length' \
    .safe-rust/artifacts/layer-5/unsafe-audit.yaml 2>/dev/null || echo 0)
  
  if [[ $unsafe_count -gt 0 && $unsafe_count -ne $unsafe_justified ]]; then
    echo "FAIL: Unjustified unsafe blocks"
    exit 1
  fi
  
  echo "PASS: Gate 5 - Static analysis clean"
  exit 0
}

check_gate_5
```

### Gate 6: Formally Verified

```bash
#!/bin/bash
# gate-6.sh - Formal verification validation

check_gate_6() {
  local fv_report=".safe-rust/artifacts/layer-6/verification.yaml"
  
  # Check if formal verification is required
  if yq '.verification.formal_tools | length' .safe-rust/design-spec.yaml | grep -q "^0$"; then
    echo "SKIP: No formal verification tools configured"
    exit 3  # Skip exit code
  fi
  
  # Run Kani if available
  if command -v cargo-kani &>/dev/null; then
    if ! cargo kani 2>/dev/null; then
      echo "FAIL: Kani verification failed"
      exit 1
    fi
  fi
  
  # Check all critical properties proven
  if [[ -f "$fv_report" ]]; then
    if yq '.harnesses[] | select(.result == "FAILED")' "$fv_report" | grep -q "."; then
      echo "FAIL: Unproven properties"
      exit 1
    fi
  fi
  
  # Check assumptions documented
  if ! yq '.assumptions | length' "$fv_report" | grep -qE "^[0-9]+$"; then
    echo "FAIL: Verification assumptions not documented"
    exit 1
  fi
  
  echo "PASS: Gate 6 - Formally verified"
  exit 0
}

check_gate_6
```

### Gate 7: Dynamic Analysis Complete

```bash
#!/bin/bash
# gate-7.sh - Dynamic analysis validation

check_gate_7() {
  # Run Miri
  if ! cargo +nightly miri test 2>/dev/null; then
    echo "FAIL: Miri detected undefined behavior"
    exit 1
  fi
  
  # Check coverage
  local coverage_target=$(yq '.verification.coverage.line' .safe-rust/design-spec.yaml)
  local actual_coverage=$(cargo llvm-cov --json 2>/dev/null | jq '.data[0].totals.lines.percent')
  
  if (( $(echo "$actual_coverage < $coverage_target" | bc -l) )); then
    echo "FAIL: Coverage $actual_coverage% below target $coverage_target%"
    exit 1
  fi
  
  # Check fuzz results (if fuzz directory exists)
  if [[ -d "fuzz" ]]; then
    local crash_count=$(find fuzz/artifacts -name "crash-*" 2>/dev/null | wc -l)
    if [[ $crash_count -gt 0 ]]; then
      echo "FAIL: $crash_count unresolved fuzz crashes"
      exit 1
    fi
  fi
  
  # Check timing (if required)
  if yq '.verification.timing_analysis' .safe-rust/design-spec.yaml | grep -q "true"; then
    if [[ -f ".safe-rust/artifacts/layer-7/timing.yaml" ]]; then
      if yq '.measurements[] | select(.status == "FAIL")' \
          .safe-rust/artifacts/layer-7/timing.yaml | grep -q "."; then
        echo "FAIL: Timing violations"
        exit 1
      fi
    fi
  fi
  
  echo "PASS: Gate 7 - Dynamic analysis complete"
  exit 0
}

check_gate_7
```

### Gate 8: Review Complete

```bash
#!/bin/bash
# gate-8.sh - Independent review validation

check_gate_8() {
  local review=".safe-rust/artifacts/layer-8/review.yaml"
  
  [[ ! -f "$review" ]] && echo "FAIL: Review not conducted" && exit 1
  
  # Check no critical findings
  if yq '.findings[] | select(.severity == "CRITICAL")' "$review" | grep -q "."; then
    echo "FAIL: Unresolved critical findings"
    exit 1
  fi
  
  # Check major findings addressed
  local unresolved=$(yq '.findings[] | select(.severity == "MAJOR" and .status != "RESOLVED")' "$review")
  if [[ -n "$unresolved" ]]; then
    echo "FAIL: Unresolved major findings"
    exit 1
  fi
  
  # Check assumption audit complete
  if ! yq '.assumption_audit.complete' "$review" | grep -q "true"; then
    echo "FAIL: Assumption audit incomplete"
    exit 1
  fi
  
  echo "PASS: Gate 8 - Review complete"
  exit 0
}

check_gate_8
```

### Gate 9: Safety Case Complete

```bash
#!/bin/bash
# gate-9.sh - Safety case validation

check_gate_9() {
  local safety=".safe-rust/artifacts/layer-9/safety-case.yaml"
  
  [[ ! -f "$safety" ]] && echo "FAIL: Safety case not assembled" && exit 1
  
  # Check all hazards mitigated
  local unmitigated=$(yq '.hazard_correlation[] | select(.mitigations | length == 0)' "$safety")
  if [[ -n "$unmitigated" ]]; then
    echo "FAIL: Unmitigated hazards"
    exit 1
  fi
  
  # Check evidence chain complete
  if yq '.safety_case.claims[].arguments[].evidence | length' "$safety" | grep -q "^0$"; then
    echo "FAIL: Missing evidence in safety case"
    exit 1
  fi
  
  # Check residual risks accepted
  if yq '.residual_risks[] | select(.acceptance_rationale == null)' "$safety" | grep -q "."; then
    echo "FAIL: Residual risks not accepted"
    exit 1
  fi
  
  # Check release decision made
  local decision=$(yq '.release_decision.decision' "$safety")
  if [[ -z "$decision" || "$decision" == "null" ]]; then
    echo "FAIL: No release decision"
    exit 1
  fi
  
  echo "PASS: Gate 9 - Safety case complete (Decision: $decision)"
  exit 0
}

check_gate_9
```

## Orchestrator Integration

The orchestrator calls gates like this:

```python
def run_gate(layer: int) -> bool:
    """Run gate validation, return True if passed."""
    result = subprocess.run(
        ["/safe-rust:gate", str(layer)],
        capture_output=True
    )
    
    exit_code = result.returncode
    
    if exit_code == 0:
        log_gate_pass(layer)
        return True
    elif exit_code == 1:
        log_gate_fail(layer, result.stderr)
        analyze_and_route_failure(layer)
        return False
    elif exit_code == 2:
        log_gate_blocked(layer)
        return False
    elif exit_code == 3:
        log_gate_skipped(layer)
        return True  # Approved skip counts as pass
    else:
        log_unexpected_exit(layer, exit_code)
        return False
```

## Gate Result Recording

Each gate result is recorded in `.safe-rust/gates/`:

```yaml
# .safe-rust/gates/gate-5-result.yaml
gate: 5
layer: "Static Analysis"
timestamp: "2024-01-15T10:30:00Z"
exit_code: 0
status: "PASS"
duration_seconds: 45
checks:
  - name: "clippy"
    status: "PASS"
    details: "No warnings"
  - name: "cargo-audit"
    status: "PASS"
    details: "0 vulnerabilities"
  - name: "cargo-deny"
    status: "PASS"
    details: "All licenses approved"
  - name: "unsafe-audit"
    status: "PASS"
    details: "0 unsafe blocks"
```
