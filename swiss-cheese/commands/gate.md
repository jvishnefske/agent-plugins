---
description: "Gate to run: requirements, tdd, implementation, verify"
arguments:
  - name: gate_name
    description: "Gate to run: requirements, tdd, implementation, verify"
    required: true
---

You are manually running the **{{gate_name}}** verification gate.

## Running the Gate

Execute the Makefile target for this gate:

```bash
make validate-{{gate_name}}
```

## Gate Details

{{#if (eq gate_name "requirements")}}
### Layer 1: Requirements Validation

**Makefile Target**: `validate-requirements`

**What it checks**:
- `design.toml` or `design.md` exists
- Requirements have testable acceptance criteria

**To pass manually**:
1. Create `design.toml` with [[requirements]] section
2. Each requirement needs: id, title, description, acceptance_criteria

{{else if (eq gate_name "tdd")}}
### Layer 2: TDD Tests

**Makefile Target**: `validate-tdd`

**What it checks**:
- Test files exist
- Tests compile

**To pass manually**:
1. Write tests for all requirements
2. Tests should compile (may fail - TDD red phase)

{{else if (eq gate_name "implementation")}}
### Layer 3: Implementation

**Makefile Target**: `validate-implementation`

**What it checks**:
- All tests pass

**To pass manually**:
1. Implement code to pass all tests
2. TDD green phase

{{else if (eq gate_name "verify")}}
### Layer 4: Verify

**Makefile Target**: `validate-verify`

**What it checks**:
- Static analysis (clippy) passes
- Coverage meets threshold

**To pass manually**:
1. Fix all Clippy warnings: `cargo clippy -- -D warnings`
2. Achieve coverage target: `cargo llvm-cov`

{{else}}
### Unknown Gate: {{gate_name}}

Valid gates are:
- requirements
- tdd
- implementation
- verify

{{/if}}

## Instructions

1. Run `make validate-{{gate_name}}`
2. If it fails, review the output and fix issues
3. Re-run until the gate passes

## Exit Codes

- **0**: Gate passed
- **Non-zero**: Gate failed (see output for details)
