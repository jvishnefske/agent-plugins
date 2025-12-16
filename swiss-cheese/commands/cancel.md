# /safe-rust:cancel Command

Cancel the current verification loop.

## Usage

```bash
/safe-rust:cancel
/safe-rust:cancel --save-state
/safe-rust:cancel --force
```

## Behavior

Cancelling the loop:
1. Marks loop as inactive
2. Saves current state
3. Outputs progress summary
4. Allows normal session exit

## Output

```
> /safe-rust:cancel

╔═══════════════════════════════════════════════════════════════════╗
║  LOOP CANCELLED                                                   ║
╠═══════════════════════════════════════════════════════════════════╣
║  Progress saved. You can resume later.                            ║
╠═══════════════════════════════════════════════════════════════════╣
║  Layers Completed: 5/9                                            ║
║  Current Layer: 6 (Formal Verification)                           ║
║  Iterations Used: 3/10                                            ║
╠═══════════════════════════════════════════════════════════════════╣
║  TO RESUME:                                                       ║
║  /safe-rust:loop --from-layer 6                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

## State Preservation

On cancel, state is saved to `.safe-rust/state.json`:

```json
{
  "component_id": "COMP-MOTOR-001",
  "design_review_complete": true,
  "current_layer": 6,
  "iteration": 3,
  "cancelled_at": "2024-01-15T11:30:00Z",
  "layers": {
    "1": {"status": "PASS"},
    "2": {"status": "PASS"},
    "3": {"status": "PASS"},
    "4": {"status": "PASS"},
    "5": {"status": "PASS"},
    "6": {"status": "IN_PROGRESS"},
    "7": {"status": "PENDING"},
    "8": {"status": "PENDING"},
    "9": {"status": "PENDING"}
  },
  "resume_info": {
    "from_layer": 6,
    "last_action": "Kani harness verify_state_machine running"
  }
}
```

## Force Cancel

If the loop is stuck:

```bash
> /safe-rust:cancel --force

Force cancelling loop...
Warning: Current layer work may be lost.
State saved to .safe-rust/state.json

Loop terminated.
```
