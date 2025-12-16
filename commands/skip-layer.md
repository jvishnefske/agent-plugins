---
name: swiss-cheese:skip-layer
description: Request to skip a layer with justification (requires proof of inapplicability)
---

# /swiss-cheese:skip-layer Command

Request to skip a verification layer. **Requires proof of inapplicability.**

## Usage

```bash
/swiss-cheese:skip-layer <layer_number> --reason "<reason>" --proof "<proof>"
```

## CRITICAL: Skip Policy

**Layers may ONLY be skipped with:**
1. Proof that the layer's checks are inapplicable
2. Risk assessment showing no safety impact
3. Orchestrator Architect approval

**Convenience is NOT a valid reason.**

## Valid Skip Criteria

### Layer 6 (Formal Verification)

```yaml
valid_skip:
  layer: 6
  criteria:
    - "Pure data transformation with no arithmetic"
    - "All types are Copy with no state"
    - "No loops or recursion"
    - "Type system provides equivalent guarantees"
  example_proof: |
    Component only maps enum variants to strings.
    No arithmetic operations.
    No unsafe code.
    No state transitions.
    String lookup is bounded by enum variant count.
```

### Layer 7 (Dynamic Analysis - Partial)

```yaml
valid_skip:
  layer: 7
  criteria:
    - "No unsafe code (Miri not needed)"
    - "No timing requirements (WCET not needed)"
    - "Deterministic code (fuzzing adds no value)"
  example_proof: |
    Component is a pure function: hash(input) -> output.
    No unsafe blocks.
    No timing constraints.
    Input space is small and fully covered by unit tests.
  note: "Coverage analysis still required"
```

### Invalid Skip Requests (REJECTED)

```yaml
invalid_skips:
  - reason: "We don't have time"
    response: "Schedule is not a safety argument"
    
  - reason: "The code is simple"
    response: "Simple code can have bugs. Therac-25 was 'simple'."
    
  - reason: "We've never had bugs here before"
    response: "Past performance doesn't guarantee future safety"
    
  - reason: "The tests are thorough enough"
    response: "Testing finds bugs, verification proves absence"
    
  - reason: "We trust the developer"
    response: "Trust but verify. Swiss Cheese requires independence"
```

## Skip Request Format

```yaml
skip_request:
  layer: N
  component_id: "COMP-XXX"
  requested_by: "{developer}"
  timestamp: "{ISO-8601}"
  
  reason: |
    {Brief reason for skip request}
    
  proof_of_inapplicability:
    claim: "{What makes this layer inapplicable}"
    evidence:
      - "{Evidence point 1}"
      - "{Evidence point 2}"
    verification: |
      {How the claim can be verified}
      
  risk_assessment:
    what_layer_catches: "{Defect types this layer detects}"
    alternative_coverage: "{How these defects are caught elsewhere}"
    residual_risk: "{Risk if skipped}"
    risk_level: "NONE | LOW | MEDIUM | HIGH"
    
  approval:
    status: "PENDING | APPROVED | REJECTED"
    approver: "orchestrator-architect"
    rationale: "{Why approved or rejected}"
```

## Example: Valid Skip

```
> /swiss-cheese:skip-layer 6 \
    --reason "Pure lookup table with no computation" \
    --proof "See analysis below"

SKIP REQUEST: Layer 6 (Formal Verification)

Analyzing request...

Component: ErrorCodeLookup
Function: Maps error codes to human-readable strings

Proof Analysis:
✓ No arithmetic operations (overflow impossible)
✓ No unsafe code (memory safety by construction)
✓ No loops (termination trivial)
✓ No state (no invariants to verify)
✓ Bounded array access (enum variant count is compile-time)

Risk Assessment:
- Layer 6 catches: overflow, bounds errors, invariant violations
- Alternative coverage: Type system guarantees bounds, no arithmetic
- Residual risk: NONE

Decision: APPROVED

Skip recorded in .swiss-cheese/state.json
Gate 6 will return exit code 3 (SKIPPED)
```

## Example: Rejected Skip

```
> /swiss-cheese:skip-layer 7 --reason "Takes too long"

SKIP REQUEST: Layer 7 (Dynamic Analysis)

Analyzing request...

REJECTED

Reason: "Takes too long" is not a valid safety argument.

Layer 7 detects:
- Undefined behavior in unsafe code (Miri)
- Edge cases missed by unit tests (fuzzing)
- Coverage gaps
- Timing violations

These defects cannot be detected by other layers.
Schedule constraints do not reduce technical risk.

Recommendation:
- Reduce fuzz duration instead of skipping
- Run Miri on subset of tests
- Use sampling for timing analysis

To proceed without Layer 7, provide:
1. Proof that no unsafe code exists
2. Proof that coverage targets are met by unit tests
3. Proof that no timing requirements exist
```

## Orchestrator Validation

The Orchestrator Architect validates skip requests:

```python
def validate_skip_request(request: SkipRequest) -> SkipDecision:
    """Validate a layer skip request."""
    
    # Check for disallowed reasons
    disallowed_patterns = [
        "time", "schedule", "deadline",
        "simple", "easy", "trivial",
        "trust", "never had bugs",
        "tests are enough"
    ]
    
    for pattern in disallowed_patterns:
        if pattern in request.reason.lower():
            return SkipDecision(
                approved=False,
                rationale=f"'{pattern}' is not a valid safety argument"
            )
    
    # Check proof completeness
    if not request.proof_of_inapplicability:
        return SkipDecision(
            approved=False,
            rationale="No proof provided"
        )
    
    # Check risk assessment
    if request.risk_assessment.risk_level in ["MEDIUM", "HIGH"]:
        return SkipDecision(
            approved=False,
            rationale=f"Risk level {request.risk_assessment.risk_level} too high"
        )
    
    # Verify claims
    verification_result = verify_claims(request)
    if not verification_result.valid:
        return SkipDecision(
            approved=False,
            rationale=f"Claim verification failed: {verification_result.reason}"
        )
    
    return SkipDecision(
        approved=True,
        rationale="Proof verified, risk acceptable"
    )
```

## Recording Skips

Approved skips are recorded in state:

```json
{
  "skipped_layers": [
    {
      "layer": 6,
      "reason": "Pure lookup table",
      "proof_summary": "No arithmetic, no unsafe, no loops",
      "risk_level": "NONE",
      "approved_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

## Audit Trail

All skip requests (approved and rejected) are logged:

```yaml
# .swiss-cheese/audit/skip-requests.yaml
skip_requests:
  - id: "SKIP-001"
    layer: 6
    timestamp: "2024-01-15T10:30:00Z"
    reason: "Pure lookup table"
    decision: "APPROVED"
    
  - id: "SKIP-002"
    layer: 7
    timestamp: "2024-01-15T11:00:00Z"
    reason: "Takes too long"
    decision: "REJECTED"
    rejection_reason: "Schedule is not a safety argument"
```
