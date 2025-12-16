# Swiss Cheese Plugin

A Claude Code plugin providing iterative Rust software development lifecycle tooling with multi-layer defect escape reduction methodology.

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
/plugin install swiss-cheese
```

## Quick Start

```bash
# Start with design review
/swiss-cheese "CAN-based motor controller"

# Answer all design review questions...

# Orchestrator runs 9-layer verification automatically
# Gates validate each layer by exit code
# Loop continues until ALL_GATES_PASS
```

## Commands

| Command | Description |
|---------|-------------|
| `/swiss-cheese` | Start new verification with design review |
| `/swiss-cheese:gate N` | Run gate N validation (exit 0=pass) |
| `/swiss-cheese:loop` | Start iterative loop until completion |
| `/swiss-cheese:status` | Show verification status |
| `/swiss-cheese:skip-layer N` | Request layer skip (requires proof) |
| `/swiss-cheese:cancel` | Cancel active loop |

## 9-Layer Swiss Cheese Model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 9: Release Analysis   → Gate 9 (exit 0/1)        │
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
2. **Risk**: Failure modes, mitigations, fallback behavior
3. **Rust**: no_std, panic policy, target
4. **Verification**: Tools, coverage, timing
5. **Skips**: Pre-approved layer skips

## Iterative Loop

Using ralph-wiggum pattern:

```
/swiss-cheese:loop
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
.swiss-cheese/
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
│   └── layer-9/          # Release case
└── release/              # Release package
```

## Hooks

- **Stop**: Blocks exit during loop, re-injects prompt
- **PostToolUse**: Invalidates layers when files change
- **SessionStart**: Restores state, shows paused loops

## Skills

- `design-review`: Upfront question methodology
- `gate-validation`: Exit code gate implementation
- `swiss-cheese-patterns`: Type-state, newtypes, no-panic

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
- `release-agent`: Layer 9

## Disclaimer

THIS SOFTWARE IS PROVIDED AS-IS WITHOUT WARRANTY OF ANY KIND. This plugin is intended for educational and process improvement purposes only. It does not constitute certification tooling and provides no guarantee of defect escape reduction.

Users deploying software in regulated, mission-critical, or high-reliability applications bear sole responsibility for all verification, validation, and compliance activities required by applicable standards and regulatory bodies.

The authors and contributors explicitly disclaim all liability for defects, defect escapes, incidents, or damages arising from use of this tooling.

## License

MIT
