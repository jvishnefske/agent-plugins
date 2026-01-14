---
description: "Run all verification gates (requirements, tdd, implementation, verify)"
---

You are running **all verification gates** for the Swiss Cheese workflow.

## Running All Gates

Execute each gate in sequence:

```bash
make validate-requirements && \
make validate-tdd && \
make validate-implementation && \
make validate-verify
```

## Gate Summary

| Layer | Gate | What It Checks |
|-------|------|----------------|
| 1 | requirements | design.toml/design.md exists |
| 2 | tdd | tests compile |
| 3 | implementation | tests pass |
| 4 | verify | clippy + coverage |

## Output

Report the status of each gate:
- PASS: Gate succeeded
- FAIL: Gate failed (show relevant output)

## On Failure

If any gate fails:
1. Stop at that gate
2. Report which gate failed and why
3. Suggest how to fix it

## Exit Codes

- **0**: All gates passed
- **Non-zero**: At least one gate failed
