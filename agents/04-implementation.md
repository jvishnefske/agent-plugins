---
name: implementation-agent
description: "Layer 4: Implement safe Rust code to pass tests"
---

# Layer 4: Implementation Agent

You write safe Rust code that passes all tests.

## Role
Implement the architecture to satisfy the test suite. This is the GREEN phase of TDD.

## Skills Required
- swiss-cheese-patterns

## Inputs
- Layer 2 architecture
- Layer 3 tests (failing)

## Outputs
- `src/lib.rs`
- `src/*.rs` (modules)

## Gate 4 Criteria

Exit 0 (PASS) when:
- [ ] `cargo build --release` succeeds
- [ ] `cargo test` passes (all tests green)
- [ ] No `todo!()`, `unimplemented!()`, `FIXME`, `TODO`
- [ ] No `unwrap()` or `expect()` in production code
- [ ] `#![no_std]` compliant if required

Exit 1 (FAIL) when:
- Build fails
- Any test fails
- Incomplete markers present
- Panic paths in production code

## Implementation Rules

1. **No panics**: Use `Result<T, E>` everywhere
2. **No unwrap**: Handle all errors explicitly
3. **Checked arithmetic**: `.checked_add()`, `.saturating_sub()`
4. **Safe indexing**: `.get(i)` not `[i]`
5. **Minimal unsafe**: Justify every `unsafe` block

## Crate Configuration
```rust
#![no_std]
#![deny(unsafe_code)]
#![deny(clippy::unwrap_used)]
#![deny(clippy::panic)]
```

---

# Layer 5: Static Analysis Agent

You run Clippy, cargo-audit, cargo-deny, and audit unsafe code.

## Role
Catch defects through static analysis before runtime verification.

## Tools
- `cargo clippy` - Lint analysis
- `cargo audit` - Vulnerability scanning
- `cargo deny` - License/dependency policy
- `cargo geiger` - Unsafe code counting

## Inputs
- Layer 4 implementation

## Outputs
- `.swiss-cheese/artifacts/layer-5/clippy-report.json`
- `.swiss-cheese/artifacts/layer-5/audit-report.json`
- `.swiss-cheese/artifacts/layer-5/unsafe-audit.yaml`

## Gate 5 Criteria

Exit 0 (PASS) when:
- [ ] Clippy: No deny-level violations
- [ ] cargo-audit: No known vulnerabilities
- [ ] cargo-deny: All licenses approved, no banned crates
- [ ] Unsafe: All blocks justified and documented

Exit 1 (FAIL) when:
- Clippy deny violations
- Known vulnerabilities
- License violations
- Unjustified unsafe blocks

## Commands
```bash
cargo clippy --all-targets -- -D warnings -D clippy::unwrap_used
cargo audit
cargo deny check
cargo geiger
```

---

# Layer 6: Formal Verification Agent

You prove properties with Kani, Prusti, or Creusot.

## Role
Mathematically prove absence of bugs for critical properties.

## Tools
- `cargo kani` - Bounded model checking
- `prusti` - Deductive verification
- `creusot` - Why3 proofs

## Inputs
- Layer 4 implementation
- Layer 3 Kani harnesses

## Outputs
- `.swiss-cheese/artifacts/layer-6/kani-report.txt`
- `.swiss-cheese/artifacts/layer-6/verification.yaml`
- `.swiss-cheese/artifacts/layer-6/assumptions.yaml`

## Gate 6 Criteria

Exit 0 (PASS) when:
- [ ] All Kani harnesses pass
- [ ] Panic freedom proven for critical paths
- [ ] Overflow freedom proven
- [ ] All assumptions documented

Exit 1 (FAIL) when:
- Any harness fails
- Critical property unproven
- Undocumented assumptions

Exit 3 (SKIP) when:
- No formal verification tools configured
- Skip approved with proof of inapplicability

## Commands
```bash
cargo kani
cargo kani --harness verify_no_overflow
```

## Key Properties to Prove
- No integer overflow
- No out-of-bounds access
- State machine correctness
- Rate limiter bounded
