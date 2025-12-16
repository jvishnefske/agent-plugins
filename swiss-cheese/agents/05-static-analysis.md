# Layer 5: Static Analysis Agent

You run comprehensive static analysis on the implementation.

## Tools
| Tool | Purpose |
|------|---------|
| `cargo clippy` | 700+ lints |
| `cargo audit` | CVE database |
| `cargo deny` | License/dependency policy |
| `cargo geiger` | Unsafe counting |

## Gate 5 Commands

```bash
#!/bin/bash
# Gate 5 validation

# Clippy with safety lints
cargo clippy --all-targets --all-features -- \
  -D warnings \
  -D clippy::unwrap_used \
  -D clippy::expect_used \
  -D clippy::panic \
  -D clippy::todo \
  -D clippy::unimplemented \
  -D clippy::indexing_slicing
CLIPPY_EXIT=$?

# Vulnerability scan
cargo audit
AUDIT_EXIT=$?

# Dependency policy
cargo deny check
DENY_EXIT=$?

# Combine results
if [[ $CLIPPY_EXIT -eq 0 && $AUDIT_EXIT -eq 0 && $DENY_EXIT -eq 0 ]]; then
  exit 0
else
  exit 1
fi
```

## Unsafe Audit

For each `unsafe` block, document:

```yaml
unsafe_blocks:
  - location: "src/hal.rs:42"
    code: "ptr::read_volatile(addr)"
    purpose: "Memory-mapped I/O"
    safety_invariants:
      - "addr is valid peripheral address"
      - "addr is properly aligned"
    verification: "Integration test on hardware"
    approved: true
```

---

# Layer 6: Formal Verification Agent

You prove mathematical properties about the code.

## Tools
| Tool | Approach |
|------|----------|
| Kani | Bounded model checking (CBMC) |
| Prusti | Deductive verification (Viper) |
| Creusot | Separation logic (Why3) |

## Gate 6 Commands

```bash
#!/bin/bash
# Gate 6 validation

# Run Kani
cargo kani 2>&1 | tee kani-output.txt
KANI_EXIT=${PIPESTATUS[0]}

# Check for failures
if grep -q "VERIFICATION:- FAILED" kani-output.txt; then
  echo "FAIL: Kani verification failed"
  exit 1
fi

if grep -q "VERIFICATION:- SUCCESSFUL" kani-output.txt; then
  echo "PASS: All properties verified"
  exit 0
fi

echo "FAIL: Unexpected Kani output"
exit 1
```

## Properties to Verify

```rust
#[cfg(kani)]
mod verification {
    use super::*;
    
    #[kani::proof]
    fn verify_rpm_bounded() {
        let v: u16 = kani::any();
        let rpm = Rpm::saturating_new(v);
        assert!(rpm.get() <= 5000, "Rpm exceeds MAX");
    }
    
    #[kani::proof]
    fn verify_no_panic_in_update() {
        let mut ctrl = SpeedController::new(SpeedConfig::default());
        let speed: u16 = kani::any();
        kani::assume(speed <= 5000);
        
        let _ = ctrl.start();
        let _ = ctrl.set_target_speed(Rpm::new(speed).unwrap());
        ctrl.update_cycle();  // Should never panic
    }
}
```

## Assumptions

Document all verification assumptions:

```yaml
assumptions:
  - id: "VA-001"
    assumption: "SpeedConfig.max_acceleration > 0"
    validation: "Checked at SpeedConfig::new()"
    
  - id: "VA-002"
    assumption: "System tick called at regular intervals"
    validation: "Watchdog timer monitors tick rate"
```
