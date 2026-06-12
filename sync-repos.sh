#!/bin/bash

# ============================================================================
# Multi-Repo Sync Script
# Syncs frontend and backend files between CRA-Compliance-Tool and crane-oss
# ============================================================================

set -e

# Configuration
CRA_REPO="$HOME/Desktop/CRA Project/CRA-Compliance-Tool"
CRANE_REPO="$HOME/Desktop/crane-oss"
TEMP_DIR="/tmp/repo-sync-$$"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend files to sync
BACKEND_FILES=(
  "backend/app/api/routes/my_tasks.py"
  "backend/app/api/routes/support_periods.py"
  "backend/app/models/product.py"
  "backend/app/models/support_period_record.py"
  "backend/app/repositories/support_period_record_repository.py"
  "backend/app/schemas/support_period_record.py"
  "backend/app/services/support_period_record_service.py"
)

# Frontend files to sync
FRONTEND_FILES=(
  "frontend/src/components/TaskDrawer.vue"
  "frontend/src/services/support-period-service.ts"
  "frontend/src/types/product.ts"
  "frontend/src/types/task.ts"
  "frontend/src/views/MyTasksView.vue"
  "frontend/src/views/ProductDetailView.vue"
  "frontend/src/views/ProductsView.vue"
)

# Functions
log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
  exit 1
}

setup_ssh() {
  log_info "Setting up SSH keys..."

  # Add both keys to SSH agent if not already present
  if ! ssh-add -l | grep -q "id_ed25519"; then
    ssh-add ~/.ssh/id_ed25519
  fi

  if ! ssh-add -l | grep -q "id_ed25519_amh1036"; then
    ssh-add ~/.ssh/id_ed25519_amh1036
  fi

  log_info "SSH keys configured"
}

extract_files() {
  local source_repo=$1
  local commit=$2

  log_info "Extracting files from commit $commit..."

  mkdir -p "$TEMP_DIR"

  # Extract backend files
  for file in "${BACKEND_FILES[@]}"; do
    cd "$source_repo"
    git show "$commit:$file" > "$TEMP_DIR/$(basename $file)" 2>/dev/null || \
      log_warn "File not found in source: $file"
  done

  # Extract frontend files
  for file in "${FRONTEND_FILES[@]}"; do
    cd "$source_repo"
    git show "$commit:$file" > "$TEMP_DIR/$(basename $file)" 2>/dev/null || \
      log_warn "File not found in source: $file"
  done

  log_info "Files extracted to $TEMP_DIR"
}

copy_files() {
  local target_repo=$1

  log_info "Copying files to target repo..."

  # Copy backend files
  for file in "${BACKEND_FILES[@]}"; do
    src_file="$TEMP_DIR/$(basename $file)"
    dst_file="$target_repo/$file"
    if [ -f "$src_file" ]; then
      cp "$src_file" "$dst_file"
      log_info "  ✓ $(basename $file)"
    fi
  done

  # Copy frontend files
  for file in "${FRONTEND_FILES[@]}"; do
    src_file="$TEMP_DIR/$(basename $file)"
    dst_file="$target_repo/$file"
    if [ -f "$src_file" ]; then
      cp "$src_file" "$dst_file"
      log_info "  ✓ $(basename $file)"
    fi
  done
}

commit_and_push() {
  local target_repo=$1
  local commit_msg=$2

  log_info "Committing and pushing changes..."

  cd "$target_repo"

  # Stage all modified files
  git add backend/app/api/routes/my_tasks.py \
          backend/app/api/routes/support_periods.py \
          backend/app/models/product.py \
          backend/app/models/support_period_record.py \
          backend/app/repositories/support_period_record_repository.py \
          backend/app/schemas/support_period_record.py \
          backend/app/services/support_period_record_service.py \
          frontend/src/components/TaskDrawer.vue \
          frontend/src/services/support-period-service.ts \
          frontend/src/types/product.ts \
          frontend/src/types/task.ts \
          frontend/src/views/MyTasksView.vue \
          frontend/src/views/ProductDetailView.vue \
          frontend/src/views/ProductsView.vue 2>/dev/null || true

  # Check if there are changes to commit
  if ! git diff --cached --quiet; then
    git commit -m "$commit_msg"
    git push origin main
    log_info "Changes committed and pushed"
  else
    log_warn "No changes to commit"
  fi
}

sync_cra_to_crane() {
  local commit=${1:-HEAD}
  local msg=${2:-"Support period"}

  log_info "Syncing CRA-Compliance-Tool → crane-oss"
  log_info "Source commit: $commit"

  extract_files "$CRA_REPO" "$commit"
  copy_files "$CRANE_REPO"
  commit_and_push "$CRANE_REPO" "$msg"

  log_info "Sync complete!"
}

sync_crane_to_cra() {
  local commit=${1:-HEAD}
  local msg=${2:-"Support period"}

  log_info "Syncing crane-oss → CRA-Compliance-Tool"
  log_info "Source commit: $commit"

  extract_files "$CRANE_REPO" "$commit"
  copy_files "$CRA_REPO"
  commit_and_push "$CRA_REPO" "$msg"

  log_info "Sync complete!"
}

push_all() {
  log_info "Pushing both repos..."

  cd "$CRA_REPO"
  git push origin main 2>/dev/null && log_info "CRA-Compliance-Tool pushed" || log_warn "CRA-Compliance-Tool already up to date"

  cd "$CRANE_REPO"
  git push origin main 2>/dev/null && log_info "crane-oss pushed" || log_warn "crane-oss already up to date"
}

pull_all() {
  log_info "Pulling both repos..."

  cd "$CRA_REPO"
  git pull origin main 2>/dev/null && log_info "CRA-Compliance-Tool pulled" || log_warn "Failed to pull CRA-Compliance-Tool"

  cd "$CRANE_REPO"
  git pull origin main 2>/dev/null && log_info "crane-oss pulled" || log_warn "Failed to pull crane-oss"
}

cleanup() {
  rm -rf "$TEMP_DIR"
  log_info "Cleanup complete"
}

# Main script
main() {
  if [ $# -lt 1 ]; then
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  cra-to-crane [COMMIT] [MESSAGE]     Sync CRA-Compliance-Tool → crane-oss"
    echo "  crane-to-cra [COMMIT] [MESSAGE]     Sync crane-oss → CRA-Compliance-Tool"
    echo "  push-all                             Push both repos"
    echo "  pull-all                             Pull both repos"
    echo "  setup-ssh                            Configure SSH keys for both accounts"
    echo ""
    echo "Examples:"
    echo "  $0 cra-to-crane                                    # Sync latest commit"
    echo "  $0 cra-to-crane 9e6e956                            # Sync specific commit"
    echo "  $0 cra-to-crane 9e6e956 'Custom message'           # Sync with custom message"
    echo "  $0 push-all                                        # Push both repos"
    exit 1
  fi

  setup_ssh

  case "$1" in
    cra-to-crane)
      sync_cra_to_crane "${2:-HEAD}" "${3:-Support period}"
      ;;
    crane-to-cra)
      sync_crane_to_cra "${2:-HEAD}" "${3:-Support period}"
      ;;
    push-all)
      push_all
      ;;
    pull-all)
      pull_all
      ;;
    setup-ssh)
      log_info "SSH already configured"
      ;;
    *)
      log_error "Unknown command: $1"
      ;;
  esac

  cleanup
}

trap cleanup EXIT
main "$@"
