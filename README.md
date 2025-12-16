# Safe Rust Plugin

A Claude Code plugin for safety-critical Rust development using the 9-layer Swiss Cheese verification model.

## Features

- **Single Orchestrator Architect**: All coordination through one top-level agent
- **Upfront Design Review**: ALL questions asked before any work begins
- **Gate Validation by Exit Code**: Each layer validated with exit 0/1/2/3
- **Iterative Loop (ralph-wiggum)**: Automatic retry until all gates pass
- **Layer Skip with Proof**: Skip only with proven inapplicability

## Installation

```bash
# Add Anthropic marketplace
/plugin marketplace add anthropics/claude-code

# Install plugin
/plugin install safe-rust
```

## Quick Start

```bash
# Start with design review
/safe-rust "CAN-based motor controller for ASIL-C"

# Answer all design review questions...

# Orchestrator runs 9-layer verification automatically
# Gates validate each layer by exit code
# Loop continues until ALL_GATES_PASS
```

## Commands

| Command | Description |
|---------|-------------|
| `/safe-rust` | Start new verification with design review |
| `/safe-rust:gate N` | Run gate N validation (exit 0=pass) |
| `/safe-rust:loop` | Start iterative loop until completion |
| `/safe-rust:status` | Show verification status |
| `/safe-rust:skip-layer N` | Request layer skip (requires proof) |
| `/safe-rust:cancel` | Cancel active loop |

## 9-Layer Swiss Cheese Model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 9: Safety Analysis    → Gate 9 (exit 0/1)        │
├─────────────────────────────────────────────────────────┤
│ Layer 8: Independent Review → Gate 8 (exit 0/1)        │
├─────────────────────────────────────────────────────────┤
│ Layer 7: Dynamic Analysis   → Gate 7 (exit 0/1)        │
│          Miri, Fuzz, Coverage, Timing                   │
├─────────────────────────────────────────────────────────┤
│ Layer 6: Formal Verification → Gate 6 (exit 0/1/3)     │
│          Kani, Prusti, Creusot                          │
├─────────────────────────────────────────────────────────┤
│ Layer 5: Static Analysis    → Gate 5 (exit 0/1)        │
│          Clippy, audit, deny, geiger                    │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Implementation     → Gate 4 (exit 0/1)        │
│          Safe Rust, all tests pass                      │
├─────────────────────────────────────────────────────────┤
│ Layer 3: TDD Tests          → Gate 3 (exit 0/1)        │
│          Tests MUST FAIL (Red phase)                    │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Architecture       → Gate 2 (exit 0/1)        │
│          Type-state, newtypes, ownership                │
├─────────────────────────────────────────────────────────┤
│ Layer 1: Requirements       → Gate 1 (exit 0/1)        │
│          Formalized FR/SR/RC/TR                         │
└─────────────────────────────────────────────────────────┘
```

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | PASS | Advance to next layer |
| 1 | FAIL | Route to root cause layer |
| 2 | BLOCKED | Resolve prerequisites |
| 3 | SKIP | Approved skip |

## Design Review

The Orchestrator asks ALL questions upfront:

1. **Functional**: What, inputs, outputs, timing
2. **Safety**: Level, hazards, safe state
3. **Rust**: no_std, panic policy, target
4. **Verification**: Tools, coverage, timing
5. **Skips**: Pre-approved layer skips

## Iterative Loop

Using ralph-wiggum pattern:

```
/safe-rust:loop
  → Execute Layer N
  → Run Gate N
  → If PASS: advance
  → If FAIL: route to root cause
  → Stop hook blocks exit
  → Re-inject prompt
  → Continue until ALL_GATES_PASS
```

## Layer Skip Policy

**Convenience is NOT a valid reason.**

Valid: "Pure lookup table with no arithmetic"
Invalid: "We don't have time"

## Project Structure

```
.safe-rust/
├── design-spec.yaml      # Complete design specification
├── state.json            # Verification state
├── loop-state.json       # Loop iteration state
├── gates/                # Gate validation results
├── artifacts/
│   ├── layer-1/          # Requirements
│   ├── layer-2/          # Architecture
│   ├── layer-3/          # Tests
│   ├── layer-4/          # Implementation (src/)
│   ├── layer-5/          # Static analysis reports
│   ├── layer-6/          # Formal verification
│   ├── layer-7/          # Dynamic analysis
│   ├── layer-8/          # Review findings
│   └── layer-9/          # Safety case
└── release/              # Certification package
```

## Hooks

- **Stop**: Blocks exit during loop, re-injects prompt
- **PostToolUse**: Invalidates layers when files change
- **SessionStart**: Restores state, shows paused loops

## Skills

- `design-review`: Upfront question methodology
- `gate-validation`: Exit code gate implementation
- `safe-rust-patterns`: Type-state, newtypes, no-panic

## Agents

- `orchestrator-architect`: Top-level coordinator
- `requirements-agent`: Layer 1
- `architecture-agent`: Layer 2
- `tdd-agent`: Layer 3
- `implementation-agent`: Layer 4
- `static-analysis-agent`: Layer 5
- `formal-verification-agent`: Layer 6
- `dynamic-analysis-agent`: Layer 7
- `review-agent`: Layer 8
- `safety-agent`: Layer 9

## Safety Standards

Supports:
- ISO 26262 (ASIL-A to ASIL-D)
- IEC 61508 (SIL-1 to SIL-4)
- DO-178C (DAL-A to DAL-E)
- Ferrocene-qualified Rust

## License

MIT
