---
description: Parallel orchestration workflow with up to 100 subagent invocations
argument-hint: [target] [--depth shallow|standard|deep]
model: opus
---

# Ultra Parallel Orchestration Command

Initiate the **ultrathink** parallel orchestration workflow. This command MANDATES the use of subagents via the Task tool for all planning and implementation work.

## Arguments Received

- **Target**: $1 (module name, file path, or task description)
- **Depth**: $2 (--depth shallow|standard|deep, default: standard)

## CRITICAL: Subagent Delegation Requirement

**USE THE TASK TOOL FOR ALL WORK.**

Do NOT perform analysis or implementation directly. Instead:
1. Spawn parallel subagents for independent work items
2. Run up to 100 Task invocations in a SINGLE message when work items are independent
3. Wait for subagent completion before synthesizing results

## Parallel Subagent Dispatch Protocol

### Step 1: Scope Analysis (Spawn 1 analysis subagent)

Launch a Task subagent to:
- Identify all files relevant to target "$1"
- Map dependencies between modules
- Determine which work items are independent (parallelizable)
- Return a work decomposition plan

### Step 2: Parallel Work Execution (Spawn N subagents)

Based on Step 1 results, spawn parallel Task subagents:

- Subagent per affected module
- Subagent for test coverage analysis
- Subagent for documentation verification

### Step 3: Synthesis (Spawn 1 integration subagent)

Launch a Task subagent to:
- Collect all parallel subagent outputs
- Verify consistency across results
- Generate unified report with:
  - Changes needed per file
  - Test coverage status
  - Recommended next steps

## Depth Profiles

| Depth | Subagent Count | Analysis Level | Use Case |
|-------|----------------|----------------|----------|
| shallow | 2-5 | File-level | Quick reconnaissance |
| standard | 10-30 | Function-level | Balanced exploration |
| deep | 50-100 | Line-level | Comprehensive verification |

## Subagent Spawning Feedback

For EACH Task invocation, output:

```
[SUBAGENT SPAWN] Purpose: <brief description>
  Target: <file or module>
  Parallelizable: yes|no
  Estimated complexity: low|medium|high
```

After ALL parallel subagents complete:

```
[ORCHESTRATION COMPLETE]
  Subagents spawned: <count>
  Parallel batches: <count>
  Results synthesized: yes|no
```

## Begin Orchestration

Analyze the target "$1" and immediately spawn parallel subagents using the Task tool. Do NOT attempt to perform the work yourself - delegate everything to subagents.

Remember: Invoke up to 100 Task tools in a SINGLE response message for maximum parallelism when work items are independent.

Start now by spawning your first batch of parallel subagents for target: $1
