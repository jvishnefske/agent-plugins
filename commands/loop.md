---
name: swiss-cheese:loop
description: Start iterative refinement loop until all gates pass
---

# /swiss-cheese:loop Command

Start an iterative verification loop that continues until all gates pass (ralph-wiggum pattern).

## Usage

```bash
/swiss-cheese:loop
/swiss-cheese:loop --max-iterations 10
/swiss-cheese:loop --from-layer 4
/swiss-cheese:loop --completion-promise "ALL_GATES_PASS"
```

## How It Works

This implements the **ralph-wiggum** pattern: a self-referential AI loop where Claude works on verification, attempts to exit, and the Stop hook re-injects the task until completion.

```
┌─────────────────────────────────────────────────────────┐
│  1. /swiss-cheese:loop starts                              │
│  2. Claude executes current layer                       │
│  3. Runs gate validation                                │
│  4. If gate fails: routes to root cause, continues      │
│  5. If gate passes: advances to next layer              │
│  6. Claude attempts to exit                             │
│  7. Stop hook intercepts:                               │
│     - Checks if ALL_GATES_PASS                          │
│     - If no: re-injects prompt, goto step 2             │
│     - If yes: allows exit, outputs final report         │
└─────────────────────────────────────────────────────────┘
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-iterations` | Maximum loop iterations before forced exit | 10 |
| `--from-layer` | Resume from specific layer | 1 (or current) |
| `--completion-promise` | Token that signals completion | `ALL_GATES_PASS` |
| `--auto-fix` | Attempt automatic fixes on failures | false |

## State File

The loop maintains state in `.swiss-cheese/loop-state.json`:

```json
{
  "active": true,
  "started": "2024-01-15T10:00:00Z",
  "iteration": 3,
  "max_iterations": 10,
  "current_layer": 5,
  "completion_promise": "ALL_GATES_PASS",
  "gates_passed": [1, 2, 3, 4],
  "gates_remaining": [5, 6, 7, 8, 9],
  "rework_count": 1,
  "last_failure": {
    "layer": 5,
    "reason": "clippy::unwrap_used violation",
    "routed_to": 4
  }
}
```

## Stop Hook Integration

The Stop hook (`.claude-plugin/hooks/stop-hook.sh`) checks:

```bash
#!/bin/bash
# stop-hook.sh - Intercept exit attempts during loop

LOOP_STATE=".swiss-cheese/loop-state.json"

# Check if loop is active
if [[ -f "$LOOP_STATE" ]]; then
  active=$(jq -r '.active' "$LOOP_STATE")
  
  if [[ "$active" == "true" ]]; then
    # Check completion criteria
    gates_remaining=$(jq -r '.gates_remaining | length' "$LOOP_STATE")
    iteration=$(jq -r '.iteration' "$LOOP_STATE")
    max_iterations=$(jq -r '.max_iterations' "$LOOP_STATE")
    
    if [[ $gates_remaining -eq 0 ]]; then
      # All gates passed - allow exit
      echo "ALL_GATES_PASS - Verification complete"
      jq '.active = false' "$LOOP_STATE" > tmp.$$ && mv tmp.$$ "$LOOP_STATE"
      exit 0  # Allow exit
    elif [[ $iteration -ge $max_iterations ]]; then
      # Max iterations reached - allow exit with warning
      echo "MAX_ITERATIONS_REACHED - $gates_remaining gates remaining"
      jq '.active = false' "$LOOP_STATE" > tmp.$$ && mv tmp.$$ "$LOOP_STATE"
      exit 0  # Allow exit
    else
      # Continue loop - block exit and re-inject
      current_layer=$(jq -r '.current_layer' "$LOOP_STATE")
      jq ".iteration = $((iteration + 1))" "$LOOP_STATE" > tmp.$$ && mv tmp.$$ "$LOOP_STATE"
      
      echo "CONTINUE_LOOP - Iteration $((iteration + 1)), Layer $current_layer"
      
      # Re-inject the verification prompt
      cat << EOF
Continue verification loop. Current state:
- Iteration: $((iteration + 1)) of $max_iterations
- Current Layer: $current_layer
- Gates Passed: $(jq -r '.gates_passed | join(", ")' "$LOOP_STATE")
- Gates Remaining: $(jq -r '.gates_remaining | join(", ")' "$LOOP_STATE")

Execute Layer $current_layer, run gate validation, and proceed.
EOF
      
      exit 2  # Block exit, continue loop
    fi
  fi
fi

# No active loop - allow normal exit
exit 0
```

## Example Session

```
> /swiss-cheese:loop

Starting verification loop...
Max iterations: 10
Completion criteria: ALL_GATES_PASS

[Iteration 1]
Executing Layer 1: Requirements
  → Invoking requirements-agent...
  → Running /swiss-cheese:gate 1
  → Exit code: 0 (PASS)
  → Advancing to Layer 2

Executing Layer 2: Architecture
  → Invoking architecture-agent...
  → Running /swiss-cheese:gate 2
  → Exit code: 0 (PASS)
  → Advancing to Layer 3

... continues ...

Executing Layer 5: Static Analysis
  → Invoking static-analysis-agent...
  → Running /swiss-cheese:gate 5
  → Exit code: 1 (FAIL)
  → Failure: clippy::unwrap_used in src/controller.rs:42
  → Root cause analysis: Implementation defect
  → Routing to Layer 4

[Iteration 2]
Resuming from Layer 4 (rework)
Executing Layer 4: Implementation
  → Fixing clippy::unwrap_used violation...
  → Running /swiss-cheese:gate 4
  → Exit code: 0 (PASS)
  → Advancing to Layer 5

Executing Layer 5: Static Analysis
  → Running /swiss-cheese:gate 5
  → Exit code: 0 (PASS)
  → Advancing to Layer 6

... continues through Layer 9 ...

[Iteration 3]
Executing Layer 9: Safety Analysis
  → Running /swiss-cheese:gate 9
  → Exit code: 0 (PASS)
  
ALL_GATES_PASS
Verification complete in 3 iterations.

╔═══════════════════════════════════════╗
║  VERIFICATION SUMMARY                 ║
╠═══════════════════════════════════════╣
║  Status: COMPLETE                     ║
║  Iterations: 3                        ║
║  Layers Passed: 9/9                   ║
║  Defects Found: 1                     ║
║  Defects Resolved: 1                  ║
║  Release Decision: RELEASE            ║
╚═══════════════════════════════════════╝
```

## Failure Routing Logic

When a gate fails, the loop analyzes and routes:

```python
def route_failure(failed_layer: int, failure_reason: str) -> int:
    """Determine root cause layer for rework."""
    
    routing_rules = {
        # Layer 5 failures
        "clippy::unwrap_used": 4,      # Implementation issue
        "clippy::panic": 4,            # Implementation issue
        "cargo-audit": 5,              # Dependency issue (fix at L5)
        "unsafe_unjustified": 4,       # Implementation issue
        
        # Layer 6 failures
        "kani_overflow": 4,            # Implementation arithmetic
        "kani_bounds": 4,              # Implementation indexing
        "prusti_contract": 2,          # Architecture contract wrong
        
        # Layer 7 failures
        "miri_ub": 4,                  # Implementation unsafe
        "coverage_low": 3,             # Need more tests
        "timing_violation": 4,         # Implementation too slow
        "fuzz_crash": 4,               # Implementation bug
        
        # Layer 8 failures
        "missing_requirement": 1,      # Requirements gap
        "assumption_invalid": 2,       # Architecture assumption
        "logic_error": 4,              # Implementation logic
        
        # Layer 9 failures
        "unmitigated_hazard": 1,       # Requirements missing
        "missing_evidence": 7,         # Need more testing
    }
    
    for pattern, target_layer in routing_rules.items():
        if pattern in failure_reason.lower():
            return target_layer
    
    # Default: route to layer before failed layer
    return max(1, failed_layer - 1)
```

## Cancellation

To cancel an active loop:

```
> /swiss-cheese:cancel

Loop cancelled.
State saved to .swiss-cheese/loop-state.json
Resume with: /swiss-cheese:loop --from-layer 5
```

## Safety Limits

The loop includes safety limits:

1. **Max Iterations**: Default 10, prevents infinite loops
2. **Rework Limit**: Max 3 reworks to same layer before escalation
3. **Time Limit**: Optional wall-clock timeout
4. **User Interrupt**: Ctrl+C always respected

```json
{
  "safety_limits": {
    "max_iterations": 10,
    "max_rework_per_layer": 3,
    "timeout_minutes": 60,
    "escalation_on_limit": "PAUSE_FOR_HUMAN"
  }
}
```

## Completion Report

On successful completion, generates `.swiss-cheese/completion-report.yaml`:

```yaml
completion_report:
  component_id: "COMP-MOTOR-001"
  status: "ALL_GATES_PASS"
  
  execution:
    started: "2024-01-15T10:00:00Z"
    completed: "2024-01-15T10:45:00Z"
    duration_minutes: 45
    iterations: 3
    
  layers:
    - layer: 1
      status: "PASS"
      attempts: 1
    - layer: 2
      status: "PASS"
      attempts: 1
    # ... etc ...
    
  defects:
    total_found: 4
    total_resolved: 4
    escaped: 0
    by_layer:
      4: 2  # Implementation bugs
      5: 1  # Clippy finding
      8: 1  # Review finding
      
  rework:
    total_rework_events: 2
    layers_reworked: [4, 5]
    
  release:
    decision: "RELEASE"
    safety_case: ".swiss-cheese/artifacts/layer-9/safety-case.yaml"
    certification_package: ".swiss-cheese/release/"
```
