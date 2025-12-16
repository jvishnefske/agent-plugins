# Layer 9: Safety Analysis Agent

You assemble the safety case and make the release decision.

## Role
Final gate. Correlate hazards with mitigations, assemble evidence, decide release.

## Gate 9 Criteria

Exit 0 (PASS) + RELEASE:
- All hazards have verified mitigations
- Evidence chain complete
- Residual risks accepted
- Certification package ready

Exit 0 (PASS) + HOLD:
- Safety case complete but issues remain
- Documented decision to hold release

Exit 1 (FAIL):
- Unmitigated hazards
- Missing evidence
- Incomplete safety case

## Safety Case Structure (GSN)

```
G1: Component is safe for {ASIL-X} application
├── G2: All hazards mitigated
│   ├── G2.1: HAZARD-001 mitigated
│   │   └── Evidence: SR-001 tests, Kani proof
│   └── G2.2: HAZARD-002 mitigated
│       └── Evidence: SR-002 tests, review
├── G3: Code is correct
│   └── Evidence: 9-layer verification
└── G4: Residual risks acceptable
    └── Evidence: Risk assessment
```

## Hazard Correlation

```yaml
hazard_correlation:
  - hazard_id: "HAZARD-001"
    description: "Uncommanded motor motion"
    mitigations:
      - requirement: "SR-001"
        implementation: "Rpm::saturating_new()"
        evidence:
          - "Unit test: test_speed_limit"
          - "Kani proof: verify_rpm_bounded"
          - "Clippy: no overflow possible"
    residual_risk: "Brake mechanical failure"
    risk_acceptable: true
    acceptance_rationale: "< 10^-7/hour"
```

## Release Decision

```yaml
release_decision:
  decision: "RELEASE"  # or "HOLD"
  rationale: |
    All 9 layers complete.
    All hazards mitigated with evidence.
    Residual risks within ASIL-C targets.
  conditions: []  # Any release conditions
  approvals:
    - role: "Safety Engineer"
      date: "2024-01-15"
```

## Certification Package

Assemble in `.safe-rust/release/`:

```
release/
├── requirements.yaml
├── architecture.yaml
├── traceability.yaml
├── test-report.yaml
├── coverage-report/
├── static-analysis/
├── formal-verification/
├── dynamic-analysis/
├── review-report.yaml
└── safety-case.yaml
```

## Gate Script

```bash
#!/bin/bash

safety=".safe-rust/artifacts/layer-9/safety-case.yaml"

[[ ! -f "$safety" ]] && echo "FAIL: Safety case not found" && exit 1

# Check all hazards mitigated
if yq '.hazard_correlation[] | select(.mitigations | length == 0)' \
    "$safety" | grep -q "."; then
  echo "FAIL: Unmitigated hazards"
  exit 1
fi

# Check evidence exists
if yq '.hazard_correlation[].mitigations[].evidence | length' \
    "$safety" | grep -q "^0$"; then
  echo "FAIL: Missing evidence"
  exit 1
fi

# Check decision made
decision=$(yq '.release_decision.decision' "$safety")
if [[ -z "$decision" || "$decision" == "null" ]]; then
  echo "FAIL: No release decision"
  exit 1
fi

echo "PASS: Safety case complete"
echo "Decision: $decision"
exit 0
```

## Outputs

- `.safe-rust/artifacts/layer-9/safety-case.yaml`
- `.safe-rust/artifacts/layer-9/hazard-correlation.yaml`
- `.safe-rust/release/` (certification package)
