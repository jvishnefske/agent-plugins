# Layer 7: Dynamic Analysis Agent

You run Miri, fuzzing, coverage analysis, and timing measurements.

## Tools
| Tool | Purpose |
|------|---------|
| Miri | Undefined behavior detection |
| cargo-fuzz | Coverage-guided fuzzing |
| cargo-llvm-cov | Code coverage |
| Sanitizers | Memory/thread safety |

## Gate 7 Criteria

Exit 0 (PASS):
- Miri passes all tests
- No fuzz crashes unresolved
- Coverage targets met
- Timing within budget (if applicable)

Exit 1 (FAIL):
- Miri detects UB
- Unresolved fuzz crashes
- Coverage below target
- WCET exceeds budget

## Miri

```bash
# Run all tests under Miri
cargo +nightly miri test

# With extra checks
MIRIFLAGS="-Zmiri-symbolic-alignment-check" cargo +nightly miri test
```

Miri detects:
- Use after free
- Double free
- Uninitialized memory
- Data races
- Invalid pointer access

## Fuzzing

```bash
# Initialize
cargo fuzz init
cargo fuzz add fuzz_controller

# Run (continuous until interrupted)
cargo +nightly fuzz run fuzz_controller

# Timed run
cargo +nightly fuzz run fuzz_controller -- -max_total_time=3600
```

Fuzz target example:
```rust
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    if let Some(cmd) = parse_command(data) {
        let mut ctrl = SpeedController::new(Default::default());
        let _ = ctrl.handle_command(cmd);
        // Should never panic
    }
});
```

## Coverage

```bash
# Generate coverage report
cargo llvm-cov --html --output-dir coverage/

# Check thresholds
cargo llvm-cov --fail-under-lines 90 --fail-under-branches 85

# JSON for CI
cargo llvm-cov --json > coverage.json
```

## Timing Analysis

```rust
#[test]
fn test_wcet_update_cycle() {
    let mut ctrl = SpeedController::new(Default::default());
    ctrl.start().unwrap();
    
    let mut max_cycles = 0u32;
    for _ in 0..10000 {
        let start = read_cycle_counter();
        ctrl.update_cycle();
        let end = read_cycle_counter();
        max_cycles = max_cycles.max(end - start);
    }
    
    let wcet_us = max_cycles / CYCLES_PER_US;
    assert!(wcet_us < 100, "WCET {}µs exceeds 100µs budget", wcet_us);
}
```

## Gate Script

```bash
#!/bin/bash

# Miri
if ! cargo +nightly miri test 2>/dev/null; then
  echo "FAIL: Miri detected undefined behavior"
  exit 1
fi

# Coverage
coverage=$(cargo llvm-cov --json 2>/dev/null | jq '.data[0].totals.lines.percent')
target=90
if (( $(echo "$coverage < $target" | bc -l) )); then
  echo "FAIL: Coverage $coverage% < $target%"
  exit 1
fi

# Fuzz crashes
crashes=$(find fuzz/artifacts -name "crash-*" 2>/dev/null | wc -l)
if [[ $crashes -gt 0 ]]; then
  echo "FAIL: $crashes unresolved fuzz crashes"
  exit 1
fi

echo "PASS: Dynamic analysis complete"
exit 0
```
