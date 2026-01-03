---
name: Ultraplan
description: This skill should be used when the user asks to "start parallel implementation", "orchestrate tasks", "run ultraplan", "wave-based orchestration", "parallel subagent execution", "plan and implement feature", "coordinate implementation across phases", "context-resilient workflow", or needs guidance on orchestrating multi-phase implementation workflows with wave-based parallel Task invocations.
version: 1.1.0
---

# Ultraplan - Context-Resilient Wave-Based Orchestration

Ultraplan enables coordinated multi-phase implementation using wave-based parallel Task invocations (2-4 per wave). It prevents context exhaustion through state externalization and checkpointing.

## Core Concept

Ultraplan orchestrates work through phases:

| Phase | Purpose | Subagent Role |
|-------|---------|---------------|
| Phase 1 | Exploration | Understand codebase areas |
| Phase 2 | Planning | Design implementation approach |
| Phase 3 | Implementation | Execute planned changes |
| Phase 4 | Verification | Validate correctness |

Each phase uses **wave-based execution** (2-4 parallel Task invocations per wave) to prevent context exhaustion.

## Context-Resilient Architecture

### Why Wave-Based?

Spawning 100+ parallel subagents causes unrecoverable "Context low" states because:
- Each subagent output consumes context tokens
- Aggregate outputs from many subagents exhaust the context window
- Autocompact cannot recover when context is critically full

**Solution**: Wave-based dispatch with state externalization.

### Wave Rules

1. **Maximum 4 parallel subagents per wave**
2. **Checkpoint to PROGRESS.md after each wave**
3. **Keep summaries brief (under 200 words each)**
4. **Use /compact or /clear to recover if context runs low**

## Invocation Process

### Step 1: Context Gathering

Before orchestrating, gather implementation context:

1. Identify target areas of the codebase
2. Partition work into waves of 2-4 items
3. Map dependencies - which tasks block others

Query the user if context is insufficient:
- "Which areas should I focus on?"
- "Should I work on a specific phase or orchestrate all phases?"

### Step 2: Wave Planning

For each task, decompose into waves:

**Wave Rules:**
- Maximum 4 parallel tasks per wave
- Tasks within the same phase MAY run in parallel if no data dependency
- Tasks across phases MUST respect phase ordering (1 -> 2 -> 3 -> 4)
- Checkpoint after EVERY wave completes

**Task Schema:**
```
task_id: unique-task-identifier
phase: 1|2|3|4
wave: wave-number
description: imperative description
deps: [task_id, ...]
files: [affected files]
```

### Step 3: Wave-Based Subagent Dispatch

Execute waves sequentially with parallel tasks within each wave:

**Dispatch Pattern:**
```
For each phase in [1, 2, 3, 4]:
  waves = partition(phase_tasks, max_wave_size=4)
  for wave in waves:
    parallel_invoke(Task, wave)  # Max 4 simultaneous
    await_all(wave)
    summarize_outputs()          # Brief summaries only
    checkpoint_to_PROGRESS_md()  # State externalization
  validate_phase_output()
  proceed_to_next_phase()
```

**Subagent Prompt Template:**

Each Task invocation receives:
1. Specific task identifier
2. Target file paths
3. Instruction: "Return summary under 200 words"
4. Phase-specific instructions

### Step 4: Progress Tracking with Checkpointing

Track implementation progress with state externalization:

1. **Before wave**: Mark tasks as in-progress in TodoWrite
2. **After wave**: Extract brief summaries, write to PROGRESS.md
3. **Checkpoint**: PROGRESS.md enables recovery after /compact or /clear

### Step 5: Context Recovery

If "Context low" warning appears:

1. **STOP** spawning immediately
2. **Write** current state to PROGRESS.md
3. **Run** /compact or /clear
4. **Resume** from PROGRESS.md

### Step 6: Verification Gate

Before marking orchestration complete:

1. Run build - no warnings
2. Run tests - all pass
3. Run linting - no warnings

## Phase-Specific Subagent Instructions

### Phase 1 Subagent: Exploration

Instructions for Phase 1 Task invocations:
- Read and understand target files
- Identify key types and APIs
- Find existing patterns
- Map dependencies
- Report findings (do NOT make changes)

### Phase 2 Subagent: Planning

Instructions for Phase 2 Task invocations:
- Design changes based on exploration
- Specify file paths and line ranges
- Order changes by dependency
- Identify test cases needed
- Return structured plan

### Phase 3 Subagent: Implementation

Instructions for Phase 3 Task invocations:
- Execute planned changes
- Follow existing code patterns
- Add documentation
- Run local tests
- Report completion status

### Phase 4 Subagent: Verification

Instructions for Phase 4 Task invocations:
- Run full test suite
- Check linting
- Verify documentation
- Report any issues found

## Orchestration Commands

| Action | How to Invoke |
|--------|---------------|
| Start ultraplan | "Run /ultraplan" or "start parallel implementation" |
| Target specific area | "Implement changes to the auth module" |
| Single phase only | "Run exploration phase only" |
| Check status | "What tasks remain?" |
| Verify completion | "Validate all tasks are complete" |

## Error Handling

When a subagent Task fails:

1. Capture failure context - error message, affected files
2. Determine retry eligibility - transient vs. fundamental failure
3. Isolate affected tasks - do not block unrelated parallel work
4. Report to orchestrator - aggregate failure summary
5. Suggest remediation - specific fix guidance

## Best Practices

### Context Management

1. **Limit wave size to 4** - Never spawn more than 4 parallel subagents
2. **Checkpoint after every wave** - Write summaries to PROGRESS.md
3. **Keep summaries brief** - Under 200 words per subagent output
4. **Monitor context usage** - Stop and checkpoint if context runs low
5. **Use state externalization** - PROGRESS.md is the source of truth, not context

### Parallelization Guidelines

1. Parallelize within waves only (max 4 subagents)
2. Respect phase boundaries - never start Phase N+1 before Phase N completes
3. Execute waves sequentially with checkpointing between
4. Use explicit dependencies - model task DAG accurately

### Code Quality Gates

Every subagent must ensure:
- No compiler/linter warnings
- All tests pass
- Documentation complete

## Quick Start

To begin an ultraplan orchestration:

1. Identify target areas of the codebase
2. Confirm scope with user
3. Partition into waves of 2-4 tasks
4. Dispatch Phase 1 Wave 1, checkpoint, then Wave 2, etc.
5. On Phase 1 completion, dispatch Phase 2 waves
6. Run verification gate
7. Report final status

## PROGRESS.md Template

```markdown
# Ultraplan Progress

## Current Phase: [1-Exploration | 2-Planning | 3-Implementation | 4-Verification]
## Current Wave: [N]

## Completed Waves

### Phase 1 Wave 1 - COMPLETE
- Explore-A: [brief summary]
- Explore-B: [brief summary]

### Phase 1 Wave 2 - COMPLETE
- Explore-C: [brief summary]

## Next Wave
Phase 1 Wave 3: Explore-D, Explore-E

## Key Findings
- [Critical insight 1]
- [Critical insight 2]
```
