---
description: Context-resilient wave-based orchestration (2-4 parallel subagents per wave)
argument-hint: [target] [--depth shallow|standard|deep]
model: opus
---

# Ultra Parallel Orchestration Command

Initiate the **ultraplan** wave-based orchestration workflow. This command MANDATES the use of subagents via the Task tool for all planning and implementation work, while preventing context exhaustion.

## Arguments Received

- **Target**: $1 (module name, file path, or task description)
- **Depth**: $2 (--depth shallow|standard|deep, default: standard)

## CRITICAL: Context-Resilient Architecture

**Wave-Based Execution Prevents Context Exhaustion.**

Do NOT spawn more than 4 parallel subagents at once. Instead:
1. Spawn waves of 2-4 parallel subagents
2. Wait for wave completion and checkpoint to PROGRESS.md
3. Synthesize brief summaries (under 200 words each)
4. Spawn next wave only after checkpointing

## Wave-Based Subagent Dispatch Protocol

### Step 1: Scope Analysis (Wave 0 - 1 subagent)

Launch a single Task subagent to:
- Identify all files relevant to target "$1"
- Map dependencies between modules
- Partition work into waves of 2-4 items
- Return a wave decomposition plan

### Step 2: Wave Execution (2-4 subagents per wave)

Execute waves sequentially, each with 2-4 parallel subagents:

**Wave Pattern:**
```
Wave 1: [Explore-A, Explore-B] -> checkpoint -> summarize
Wave 2: [Explore-C, Explore-D] -> checkpoint -> summarize
Wave 3: [Plan-Types, Plan-Impl] -> checkpoint -> summarize
Wave 4: [Impl-A, Impl-B] -> checkpoint -> summarize
...
```

### Step 3: Checkpoint After Each Wave

After each wave completes:
1. Extract 1-2 sentence summaries from each subagent
2. Write to PROGRESS.md for recovery
3. Update TodoWrite
4. Only then spawn next wave

### Step 4: Synthesis (Final wave - 1 subagent)

Launch a Task subagent to:
- Read PROGRESS.md for accumulated context
- Generate unified report with changes and recommendations

## Depth Profiles (Context-Aware)

| Depth | Wave Size | Total Waves | Use Case |
|-------|-----------|-------------|----------|
| shallow | 2 | 2-3 | Quick reconnaissance |
| standard | 3 | 4-6 | Balanced exploration |
| deep | 4 | 8-12 | Comprehensive verification |

## Wave Execution Feedback

For EACH wave, output:

```
[WAVE N] Starting with [2-4] subagents
  - Subagent-A: <target>
  - Subagent-B: <target>
```

After wave completes:

```
[WAVE N COMPLETE]
  Checkpointed to: PROGRESS.md
  Context status: [low|moderate|high]
  Proceeding to: Wave N+1
```

## Context Recovery

If context runs low:
1. STOP spawning immediately
2. Write state to PROGRESS.md
3. Report: "Context constrained. Run /compact to continue from PROGRESS.md"

## Begin Orchestration

Analyze the target "$1" and spawn Wave 0 (scope analysis). After completion, spawn waves of 2-4 subagents with checkpointing between each wave.

**Remember: Maximum 4 parallel Task invocations per wave. Checkpoint after every wave.**

Start now with scope analysis for target: $1
