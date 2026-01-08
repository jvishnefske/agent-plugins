---
name: Ultraplan
description: This skill should be used when the user asks to "start parallel implementation", "orchestrate tasks", "run ultraplan", "maximum parallelism", "spawn all tasks", or needs guidance on multi-phase implementation with parallel Task invocations.
version: 2.0.0
---

# Ultraplan - Maximum Parallelism Orchestration

Ultraplan coordinates multi-phase implementation by spawning ALL independent tasks in a SINGLE message per phase.

## Core Principle

**Spawn ALL independent tasks in a single message.** No artificial concurrency limits.

## 4-Phase Workflow

| Phase | Action |
|-------|--------|
| Explore | Spawn ALL explore subagents in one message |
| Plan | Spawn ALL plan subagents in one message |
| Implement | Spawn ALL impl subagents (respect dependencies) |
| Verify | Run cargo clippy/test/llvm-cov with JSON output |

## Tool-Native Outputs

Verification outputs go to `.ultraplan/` in native tool formats:

| Tool | Output |
|------|--------|
| `cargo clippy --message-format=json` | `.ultraplan/clippy.json` |
| `cargo test -- --format json` | `.ultraplan/test-results.json` |
| `cargo llvm-cov --json` | `.ultraplan/coverage.json` |

## Progress Tracking

State tracked in `.ultraplan/progress.toml`:

```toml
[meta]
phase = "implement"

[explore]
status = "complete"
tasks = ["auth", "middleware", "handlers"]

[plan]
status = "complete"

[implement]
status = "in_progress"
files_modified = ["src/auth.rs"]
```

## Invocation

| Action | Command |
|--------|---------|
| Start | `/ultra [target]` |
| Check status | Read `.ultraplan/progress.toml` |
| View results | Read `.ultraplan/*.json` |

## Context Recovery

If context runs low:
1. State is in `.ultraplan/progress.toml`
2. Run `/compact`
3. Resume from progress file
