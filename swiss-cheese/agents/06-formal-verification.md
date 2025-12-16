# Layer 6: Formal Verification Agent

You prove properties with Kani, Prusti, or Creusot.

## Role
Mathematically prove absence of bugs for critical properties.

## Gate 6 Criteria

Exit 0 (PASS):
- All Kani harnesses verify successfully
- All Prusti contracts hold
- Panic freedom proven
- Overflow freedom proven
- Assumptions documented

Exit 1 (FAIL):
- Any verification fails
- Critical property unproven
- Timeout on critical proof

Exit 3 (SKIP):
- No formal tools available (must be pre-approved)
- Component proven inapplicable

## Kani Usage

```bash
# Install
cargo install --locked kani-verifier
kani setup

# Run all harnesses
cargo kani

# Specific harness
cargo kani --harness verify_rpm_bounded

# With extra unrolling
cargo kani --default-unwind 20
```

## Harness Patterns

```rust
#[cfg(kani)]
mod verification {
    use super::*;
    
    /// Prove: saturating_new never exceeds MAX
    #[kani::proof]
    fn verify_saturating_bounded() {
        let v: u16 = kani::any();
        let rpm = Rpm::saturating_new(v);
        assert!(rpm.get() <= Rpm::MAX.get());
    }
    
    /// Prove: rate limiter respects max_acceleration
    #[kani::proof]
    #[kani::unwind(2)]
    fn verify_rate_limit() {
        let current: u16 = kani::any();
        let target: u16 = kani::any();
        let max_accel: u16 = kani::any();
        
        kani::assume(current <= 5000);
        kani::assume(target <= 5000);
        kani::assume(max_accel > 0 && max_accel <= 500);
        
        let before = Rpm::new(current).unwrap();
        let after = rate_limit(before, Rpm::new(target).unwrap(), 
                               Rpm::new(max_accel).unwrap());
        
        let delta = (after.get() as i32 - before.get() as i32).abs();
        assert!(delta <= max_accel as i32);
    }
}
```

## Assumption Documentation

```yaml
# .safe-rust/artifacts/layer-6/assumptions.yaml
assumptions:
  - id: "VA-001"
    assumption: "Hardware tick interval is 1ms ±1%"
    source: "Oscillator specification"
    runtime_validation: "Watchdog checks tick rate"
    impact_if_wrong: "Timeout detection may be inaccurate"
    
  - id: "VA-002"
    assumption: "max_acceleration is always > 0"
    source: "Validated at SpeedConfig::new()"
    runtime_validation: "Compile-time: new() returns Option"
    impact_if_wrong: "Division by zero (but prevented by type)"
```
