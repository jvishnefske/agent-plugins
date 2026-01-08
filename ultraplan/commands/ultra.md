---
description: Maximum parallelism orchestration - spawns ALL tasks per phase in a single message
argument-hint: [target]
model: opus
---

# Ultra Command

Initiate ultraplan orchestration with maximum parallelism.

## Target: $1

## Execution Protocol

1. **Scope Analysis**: Identify all files/modules relevant to "$1"
2. **Spawn ALL Explore tasks** in a single message
3. **Spawn ALL Plan tasks** in a single message
4. **Spawn ALL Implement tasks** in a single message (respect deps)
5. **Run verification tools** with JSON output to `.ultraplan/`

## Verification Commands

```bash
mkdir -p .ultraplan
cargo clippy --message-format=json > .ultraplan/clippy.json 2>&1
cargo test -- --format json > .ultraplan/test-results.json 2>&1
```

## Progress File

Track state in `.ultraplan/progress.toml` for recovery.

## Begin

Analyze target "$1" and spawn ALL exploration subagents in a single message.
