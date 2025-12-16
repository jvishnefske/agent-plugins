# Design Review Skill

This skill provides guidance for conducting comprehensive upfront design reviews for safety-critical Rust components.

## Purpose

The design review is the FIRST and MOST IMPORTANT step. All questions are asked in a single interaction before any development begins. This prevents:

1. Mid-project scope changes
2. Missed requirements
3. Incorrect safety level assumptions
4. Incompatible technical choices

## Question Categories

### 1. Functional Requirements

Establish WHAT the component does:

- **Purpose**: Single-sentence description
- **Inputs**: All data sources with types, rates, formats
- **Outputs**: All data sinks with types, rates, formats
- **Timing**: Periods, deadlines, latency budgets
- **Interfaces**: Protocols, buses, peripherals

### 2. Safety Requirements

Establish WHY safety matters:

- **Safety Level**: ASIL, SIL, DAL classification
- **Hazards**: What can go wrong (from system FMEA/FTA)
- **Mitigations**: How each hazard is addressed
- **Safe State**: What the component does on failure
- **Fault Detection**: How faults are detected

### 3. Rust Constraints

Establish HOW Rust is used:

- **Environment**: no_std, alloc, std
- **Target**: MCU, architecture, memory constraints
- **Memory Policy**: Static, bounded heap, unlimited
- **Panic Policy**: Forbidden, reset, custom handler
- **Dependencies**: Required crates

### 4. Verification Scope

Establish HOW MUCH verification:

- **Formal Tools**: Kani, Prusti, Creusot availability
- **Coverage Targets**: Line, branch, MC/DC percentages
- **Dynamic Analysis**: Miri, fuzzing, sanitizers
- **Timing Analysis**: WCET requirements
- **Hardware**: HIL testing availability

### 5. Layer Applicability

Establish WHICH layers apply:

- Request skip justifications upfront
- Validate skip criteria before approving
- Document approved skips in design spec

## Question Phrasing

Questions should be:

1. **Specific**: Not "what are the requirements?" but "what is the control loop period in microseconds?"
2. **Bounded**: Provide options where possible
3. **Complete**: Cover all aspects before proceeding
4. **Actionable**: Answers directly inform design

## Anti-Patterns

Avoid these design review failures:

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Incremental questioning | Wastes iterations | Ask ALL questions upfront |
| Assuming defaults | May be wrong | Explicitly confirm each choice |
| Skipping safety questions | Hazards missed | Always ask about hazards |
| Vague timing | WCET undefined | Get specific numbers |
| "We'll figure it out later" | Scope creep | Resolve before starting |

## Output: Design Specification

After all questions are answered, generate:

```yaml
design_specification:
  metadata:
    component_id: "COMP-XXX"
    name: "{name}"
    version: "0.1.0"
    safety_level: "{level}"
    created: "{timestamp}"
    
  functional:
    purpose: "{from questions}"
    inputs: [...]
    outputs: [...]
    timing: {...}
    interfaces: [...]
    
  safety:
    hazards: [...]
    safe_state: {...}
    fault_detection: [...]
    
  rust:
    environment: {...}
    target: {...}
    policies: {...}
    
  verification:
    scope: {...}
    targets: {...}
    tools: [...]
    
  layers:
    skipped: []
    justifications: {}
```

## Validation

Before proceeding, validate:

- [ ] All questions answered (no TBD in critical fields)
- [ ] Safety level matches verification scope
- [ ] Timing requirements are specific and measurable
- [ ] Hazards have corresponding safety requirements
- [ ] Rust constraints are compatible with requirements
- [ ] Skip requests have valid justifications

## Example Complete Design Review

```
User: I need a CAN-based motor controller.

Orchestrator: I'll conduct a design review. Please answer ALL questions:

FUNCTIONAL:
1. Control loop frequency? → 1ms
2. CAN protocol? → CANopen
3. Speed range? → 0-5000 RPM
4. PWM frequency? → 20kHz

SAFETY:
5. Safety level? → ASIL-C
6. Hazards? → Overspeed, uncommanded motion
7. Safe state? → PWM=0, brake engaged
8. Detection? → Watchdog, range checking

RUST:
9. no_std required? → Yes
10. Target? → STM32F4
11. Heap allowed? → No
12. Panic policy? → Forbidden

VERIFICATION:
13. Kani available? → Yes
14. Coverage target? → 95%
15. HIL available? → Yes

SKIPS:
16. Any layers to skip? → None

→ Design Specification generated
→ Beginning Layer 1
```
