---
name: swiss-cheese:status
description: Show current verification status across all layers
---

# /swiss-cheese:status Command

Display current verification status across all layers.

## Usage

```bash
/swiss-cheese:status
/swiss-cheese:status --verbose
/swiss-cheese:status --layer 5
```

## Output

```
> /swiss-cheese:status

╔═══════════════════════════════════════════════════════════════════╗
║  SAFE RUST VERIFICATION STATUS                                    ║
╠═══════════════════════════════════════════════════════════════════╣
║  Component: COMP-MOTOR-001                                        ║
║  Safety Level: ASIL-C                                             ║
║  Started: 2024-01-15T10:00:00Z                                    ║
║  Current Iteration: 3                                             ║
╠═══════════════════════════════════════════════════════════════════╣
║  LAYER STATUS                                                     ║
╠═══════════════════════════════════════════════════════════════════╣
║  Layer │ Name                  │ Status  │ Gate │ Attempts       ║
║  ──────┼───────────────────────┼─────────┼──────┼────────────────║
║  1     │ Requirements          │ ✓ PASS  │ 0    │ 1              ║
║  2     │ Architecture          │ ✓ PASS  │ 0    │ 1              ║
║  3     │ TDD Tests             │ ✓ PASS  │ 0    │ 1              ║
║  4     │ Implementation        │ ✓ PASS  │ 0    │ 2              ║
║  5     │ Static Analysis       │ ✓ PASS  │ 0    │ 1              ║
║  6     │ Formal Verification   │ → RUN   │ -    │ 0              ║
║  7     │ Dynamic Analysis      │ ○ PEND  │ -    │ 0              ║
║  8     │ Independent Review    │ ○ PEND  │ -    │ 0              ║
║  9     │ Safety Analysis       │ ○ PEND  │ -    │ 0              ║
╠═══════════════════════════════════════════════════════════════════╣
║  DEFECTS                                                          ║
╠═══════════════════════════════════════════════════════════════════╣
║  Found: 2  │  Resolved: 2  │  Open: 0  │  Escaped: 0             ║
╠═══════════════════════════════════════════════════════════════════╣
║  SKIPPED LAYERS                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  None                                                             ║
╠═══════════════════════════════════════════════════════════════════╣
║  LOOP STATUS                                                      ║
╠═══════════════════════════════════════════════════════════════════╣
║  Active: YES  │  Iteration: 3/10  │  Rework: 1                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## Status Symbols

| Symbol | Meaning |
|--------|---------|
| ✓ PASS | Layer complete, gate passed |
| ✗ FAIL | Layer complete, gate failed |
| → RUN  | Currently executing |
| ○ PEND | Pending (not yet started) |
| ⊘ SKIP | Skipped (approved) |
| ⟳ WORK | Rework in progress |

## Verbose Output

```
> /swiss-cheese:status --verbose

... header ...

LAYER 4 DETAILS:
  Status: PASS (after rework)
  Attempts: 2
  First attempt: FAIL
    - Reason: clippy::unwrap_used
    - Location: src/controller.rs:42
  Second attempt: PASS
    - Fix: Replaced unwrap() with proper Result handling
  Artifacts:
    - src/lib.rs
    - src/controller.rs
    - src/types.rs
    - src/error.rs
  Test Results:
    - Passed: 47
    - Failed: 0
    - Skipped: 2

LAYER 5 DETAILS:
  Status: PASS
  Attempts: 1
  Checks:
    - Clippy: PASS (0 warnings)
    - cargo-audit: PASS (0 vulnerabilities)
    - cargo-deny: PASS (all licenses OK)
    - Unsafe audit: PASS (0 unsafe blocks)
  Artifacts:
    - .swiss-cheese/artifacts/layer-5/clippy-report.json
    - .swiss-cheese/artifacts/layer-5/audit-report.json
```

## Layer-Specific Status

```
> /swiss-cheese:status --layer 6

╔═══════════════════════════════════════════════════════════════════╗
║  LAYER 6: FORMAL VERIFICATION                                     ║
╠═══════════════════════════════════════════════════════════════════╣
║  Status: IN PROGRESS                                              ║
║  Tool: Kani                                                       ║
╠═══════════════════════════════════════════════════════════════════╣
║  HARNESSES                                                        ║
╠═══════════════════════════════════════════════════════════════════╣
║  Harness                        │ Status    │ Time               ║
║  ───────────────────────────────┼───────────┼────────────────────║
║  verify_rpm_bounded             │ ✓ PASS    │ 2.3s               ║
║  verify_no_overflow             │ ✓ PASS    │ 5.1s               ║
║  verify_rate_limiter            │ → RUNNING │ 12.4s...           ║
║  verify_state_machine           │ ○ PENDING │ -                  ║
╠═══════════════════════════════════════════════════════════════════╣
║  ASSUMPTIONS                                                      ║
╠═══════════════════════════════════════════════════════════════════╣
║  - VA-001: Hardware tick called regularly                         ║
║  - VA-002: SpeedConfig validated at construction                  ║
╚═══════════════════════════════════════════════════════════════════╝
```

## JSON Output

For programmatic access:

```bash
> /swiss-cheese:status --json

{
  "component_id": "COMP-MOTOR-001",
  "safety_level": "ASIL-C",
  "started": "2024-01-15T10:00:00Z",
  "current_layer": 6,
  "iteration": 3,
  "layers": {
    "1": {"status": "PASS", "gate_exit_code": 0, "attempts": 1},
    "2": {"status": "PASS", "gate_exit_code": 0, "attempts": 1},
    "3": {"status": "PASS", "gate_exit_code": 0, "attempts": 1},
    "4": {"status": "PASS", "gate_exit_code": 0, "attempts": 2},
    "5": {"status": "PASS", "gate_exit_code": 0, "attempts": 1},
    "6": {"status": "IN_PROGRESS", "gate_exit_code": null, "attempts": 1},
    "7": {"status": "PENDING", "gate_exit_code": null, "attempts": 0},
    "8": {"status": "PENDING", "gate_exit_code": null, "attempts": 0},
    "9": {"status": "PENDING", "gate_exit_code": null, "attempts": 0}
  },
  "defects": {
    "found": 2,
    "resolved": 2,
    "open": 0,
    "escaped": 0
  },
  "skipped_layers": [],
  "loop": {
    "active": true,
    "iteration": 3,
    "max_iterations": 10,
    "rework_count": 1
  }
}
```
