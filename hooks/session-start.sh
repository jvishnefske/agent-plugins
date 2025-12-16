#!/bin/bash
# session-start.sh
# Runs at session start to restore state and provide context

STATE_FILE=".swiss-cheese/state.json"
LOOP_STATE=".swiss-cheese/loop-state.json"

# Check if we're in a swiss-cheese project
if [[ ! -d ".swiss-cheese" ]]; then
  exit 0
fi

# Check for paused loop
if [[ -f "$LOOP_STATE" ]]; then
  paused=$(jq -r '.paused // false' "$LOOP_STATE")
  
  if [[ "$paused" == "true" ]]; then
    current_layer=$(jq -r '.current_layer // 1' "$LOOP_STATE")
    iteration=$(jq -r '.iteration // 1' "$LOOP_STATE")
    
    cat << EOF
╔═══════════════════════════════════════════════════════════════════╗
║  SAFE RUST - PAUSED VERIFICATION                                  ║
╠═══════════════════════════════════════════════════════════════════╣
║  A verification loop was previously paused.                       ║
║                                                                   ║
║  Current Layer: $current_layer                                    ║
║  Iteration: $iteration                                            ║
║                                                                   ║
║  Commands:                                                        ║
║    /swiss-cheese:status   - View current state                       ║
║    /swiss-cheese:loop     - Resume verification                      ║
║    /swiss-cheese:cancel   - Abandon and start fresh                  ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
  fi
fi

# Check for design review in progress
if [[ -f "$STATE_FILE" ]]; then
  design_complete=$(jq -r '.design_review_complete // false' "$STATE_FILE")
  
  if [[ "$design_complete" == "false" ]]; then
    cat << EOF
╔═══════════════════════════════════════════════════════════════════╗
║  SAFE RUST - DESIGN REVIEW IN PROGRESS                            ║
╠═══════════════════════════════════════════════════════════════════╣
║  Design review was started but not completed.                     ║
║                                                                   ║
║  Run /swiss-cheese to continue the design review.                    ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
  fi
fi

exit 0
