#!/bin/bash
# post-edit.sh
# Triggers after any Edit/MultiEdit/Write operation
# Invalidates affected verification layers

set -e

STATE_FILE=".safe-rust/state.json"
CHANGE_LOG=".safe-rust/changes.log"

# Get the edited file from hook context
EDITED_FILE="${HOOK_FILE:-unknown}"

# Log the change
log_change() {
  local timestamp=$(date -Iseconds)
  echo "$timestamp|EDIT|$EDITED_FILE" >> "$CHANGE_LOG"
}

# Determine which layers are affected by the change
analyze_impact() {
  local file="$1"
  local affected_layers=""
  
  case "$file" in
    # Requirements changes affect everything
    *requirements*.yaml|*requirements*.md)
      affected_layers="1 2 3 4 5 6 7 8 9"
      ;;
    
    # Architecture changes affect implementation onward
    *architecture*.yaml|*architecture*.md)
      affected_layers="2 3 4 5 6 7 8 9"
      ;;
    
    # Test changes affect tests and onward
    tests/*.rs|*_test.rs|*_tests.rs)
      affected_layers="3 4 5 6 7 8 9"
      ;;
    
    # Source code changes affect implementation onward
    src/*.rs)
      affected_layers="4 5 6 7 8 9"
      ;;
    
    # Cargo.toml changes affect static analysis onward
    Cargo.toml|Cargo.lock)
      affected_layers="5 6 7 8 9"
      ;;
    
    # Config changes (deny.toml, etc)
    deny.toml|.cargo/*.toml)
      affected_layers="5"
      ;;
    
    # Verification artifacts
    *kani*.rs|*prusti*.rs)
      affected_layers="6 7 8 9"
      ;;
    
    # Fuzz targets
    fuzz/*.rs)
      affected_layers="7 8 9"
      ;;
    
    # Safety documentation
    *safety*.yaml|*safety*.md)
      affected_layers="9"
      ;;
    
    *)
      # Unknown file type - be conservative
      affected_layers="4 5 6 7 8 9"
      ;;
  esac
  
  echo "$affected_layers"
}

# Invalidate layer status
invalidate_layers() {
  local layers="$1"
  
  if [[ ! -f "$STATE_FILE" ]]; then
    return
  fi
  
  for layer in $layers; do
    # Mark layer as needing re-verification
    jq ".layers[\"$layer\"].status = \"INVALIDATED\" | .layers[\"$layer\"].invalidated_at = \"$(date -Iseconds)\"" \
      "$STATE_FILE" > "$STATE_FILE.tmp"
    mv "$STATE_FILE.tmp" "$STATE_FILE"
  done
}

# Notify about invalidation
notify_invalidation() {
  local file="$1"
  local layers="$2"
  
  if [[ -n "$layers" ]]; then
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  CHANGE DETECTED                                              ║"
    echo "╠═══════════════════════════════════════════════════════════════╣"
    echo "  File: $file"
    echo "  Layers invalidated: $layers"
    echo ""
    echo "  These layers will need re-verification."
    echo "  Run /safe-rust:status to see current state."
    echo "╚═══════════════════════════════════════════════════════════════╝"
  fi
}

# Main
main() {
  # Only run if we're in a safe-rust project
  if [[ ! -d ".safe-rust" ]]; then
    exit 0
  fi
  
  # Log the change
  log_change
  
  # Analyze impact
  local affected=$(analyze_impact "$EDITED_FILE")
  
  # Invalidate affected layers
  if [[ -n "$affected" ]]; then
    invalidate_layers "$affected"
    notify_invalidation "$EDITED_FILE" "$affected"
  fi
}

main "$@"
