#!/bin/bash
# stop-hook.sh
# Intercepts exit attempts during verification loop (ralph-wiggum pattern)

set -e

LOOP_STATE=".safe-rust/loop-state.json"
STATE_FILE=".safe-rust/state.json"

# Check if loop is active
check_loop_active() {
  if [[ -f "$LOOP_STATE" ]]; then
    jq -r '.active // false' "$LOOP_STATE"
  else
    echo "false"
  fi
}

# Get current iteration
get_iteration() {
  jq -r '.iteration // 1' "$LOOP_STATE"
}

# Get max iterations
get_max_iterations() {
  jq -r '.max_iterations // 10' "$LOOP_STATE"
}

# Get gates remaining
get_gates_remaining() {
  jq -r '.gates_remaining | length // 9' "$LOOP_STATE"
}

# Get current layer
get_current_layer() {
  jq -r '.current_layer // 1' "$LOOP_STATE"
}

# Check completion criteria
check_completion() {
  local gates_remaining=$(get_gates_remaining)
  local iteration=$(get_iteration)
  local max_iterations=$(get_max_iterations)
  
  if [[ $gates_remaining -eq 0 ]]; then
    echo "COMPLETE"
  elif [[ $iteration -ge $max_iterations ]]; then
    echo "MAX_ITERATIONS"
  else
    echo "CONTINUE"
  fi
}

# Increment iteration
increment_iteration() {
  local current=$(get_iteration)
  jq ".iteration = $((current + 1))" "$LOOP_STATE" > "$LOOP_STATE.tmp"
  mv "$LOOP_STATE.tmp" "$LOOP_STATE"
}

# Generate continuation prompt
generate_continuation_prompt() {
  local layer=$(get_current_layer)
  local iteration=$(get_iteration)
  local max_iter=$(get_max_iterations)
  local passed=$(jq -r '.gates_passed | join(", ")' "$LOOP_STATE" 2>/dev/null || echo "none")
  local remaining=$(jq -r '.gates_remaining | join(", ")' "$LOOP_STATE" 2>/dev/null || echo "all")
  
  cat << EOF
VERIFICATION LOOP CONTINUATION

Iteration: $iteration of $max_iter
Current Layer: $layer
Gates Passed: $passed
Gates Remaining: $remaining

Continue executing Layer $layer verification.
After completion, run gate validation:
  /safe-rust:gate $layer

Based on gate result:
- Exit 0 (PASS): Advance to next layer
- Exit 1 (FAIL): Analyze failure, route to root cause layer
- Exit 2 (BLOCKED): Resolve prerequisites
- Exit 3 (SKIP): Layer approved for skip, advance

Continue the verification process.
EOF
}

# Main hook logic
main() {
  local loop_active=$(check_loop_active)
  
  if [[ "$loop_active" != "true" ]]; then
    # No active loop - allow exit
    exit 0
  fi
  
  local completion_status=$(check_completion)
  
  case "$completion_status" in
    "COMPLETE")
      echo "═══════════════════════════════════════════════════"
      echo "  ALL_GATES_PASS - Verification Complete!"
      echo "═══════════════════════════════════════════════════"
      
      # Mark loop as complete
      jq '.active = false | .completed = true' "$LOOP_STATE" > "$LOOP_STATE.tmp"
      mv "$LOOP_STATE.tmp" "$LOOP_STATE"
      
      # Generate final report
      echo ""
      echo "Final report available at: .safe-rust/completion-report.yaml"
      
      # Allow exit
      exit 0
      ;;
      
    "MAX_ITERATIONS")
      echo "═══════════════════════════════════════════════════"
      echo "  MAX_ITERATIONS_REACHED"
      echo "  Verification incomplete - human review required"
      echo "═══════════════════════════════════════════════════"
      
      local remaining=$(get_gates_remaining)
      echo "  Gates remaining: $remaining"
      echo "  Resume with: /safe-rust:loop"
      
      # Mark loop as paused
      jq '.active = false | .paused = true' "$LOOP_STATE" > "$LOOP_STATE.tmp"
      mv "$LOOP_STATE.tmp" "$LOOP_STATE"
      
      # Allow exit
      exit 0
      ;;
      
    "CONTINUE")
      # Increment iteration counter
      increment_iteration
      
      echo "═══════════════════════════════════════════════════"
      echo "  CONTINUE_LOOP"
      echo "═══════════════════════════════════════════════════"
      
      # Output continuation prompt
      generate_continuation_prompt
      
      # Block exit - return code 2 tells Claude to continue
      exit 2
      ;;
  esac
}

main "$@"
