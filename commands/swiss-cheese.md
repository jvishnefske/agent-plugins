---
name: swiss-cheese
description: Start safety-critical Rust development with design review
---

# /swiss-cheese Command

Start safety-critical Rust development with comprehensive upfront design review.

## Usage

```
/swiss-cheese "Component description and requirements"
/swiss-cheese --safety-level ASIL-C "Motor controller for CAN bus"
/swiss-cheese --skip-review "Continue from existing design"
```

## Workflow

This command initiates the **Orchestrator Architect** which:

1. **DESIGN REVIEW PHASE** (All questions asked upfront)
   - Analyzes the request
   - Asks ALL clarifying questions in a single batch
   - Waits for user responses
   - Produces complete Design Specification

2. **VERIFICATION LOOP** (Automated with gate validation)
   - Executes layers 1-9 sequentially
   - Each layer gate validated by exit code (0=pass, 1=fail)
   - Failed gates trigger rework to root cause layer
   - Loop continues until all gates pass or user cancels

## Design Review Questions

The Orchestrator asks questions across these categories:

### Functional Requirements
- What does this component do?
- What are the inputs and outputs?
- What timing constraints exist?

### Safety Requirements  
- What safety level (ASIL-A/B/C/D, SIL-1/2/3/4)?
- What hazards must be mitigated?
- What is the safe state?

### Rust Constraints
- `no_std` required?
- Heap allocation allowed?
- Target platform?

### Verification Scope
- Formal verification depth?
- Coverage targets?
- Hardware-in-loop available?

## Example

```
> /swiss-cheese "CAN-based motor speed controller"

Orchestrator: I'll help you build a safety-critical motor controller.
Before we begin, I need to understand the full requirements.

**DESIGN REVIEW QUESTIONS**

1. FUNCTIONAL:
   - What speed range (RPM)?
   - What CAN protocol (J1939, CANopen, raw)?
   - Control loop frequency?

2. SAFETY:
   - Target safety level?
   - What hazards exist (overspeed, uncommanded motion)?
   - Safe state behavior?

3. RUST:
   - Target MCU?
   - no_std required?
   - RTOS or bare-metal?

4. VERIFICATION:
   - Formal verification tools available (Kani/Prusti)?
   - Coverage targets?
   - Hardware for timing tests?

Please answer all questions, then I'll generate the complete
Design Specification and begin the 9-layer verification process.
```

## Subagent Invocation

After design review, automatically invokes layer agents:

```
→ Layer 1: requirements-agent
  Gate: /swiss-cheese:gate 1 → exit 0 (PASS)
  
→ Layer 2: architecture-agent  
  Gate: /swiss-cheese:gate 2 → exit 0 (PASS)
  
→ Layer 3: tdd-agent
  Gate: /swiss-cheese:gate 3 → exit 0 (PASS)
  
... continues through Layer 9 ...
```

## Output

Creates `.swiss-cheese/` directory with:
- `design-spec.yaml` - Complete design specification
- `state.json` - Current verification state
- `gates/` - Gate validation results
- `artifacts/` - Layer outputs
