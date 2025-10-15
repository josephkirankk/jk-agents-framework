#!/bin/bash

# JK-Agents Framework - Safe Deletion Script
# Generated: 2025-09-29T22:32:46+05:30
# Purpose: Safely delete identified candidates with backup and validation

set -euo pipefail

# Configuration
REPO_ROOT="/Users/A80997271/Documents/projects/jk-agents-framework"
BACKUP_DIR="$REPO_ROOT/backup/deletions/20250929_223246"
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Safe deletion script for JK-Agents Framework cleanup

OPTIONS:
    --dry-run           Show what would be deleted without actually deleting
    --verbose           Enable verbose output
    --backup-dir DIR    Specify custom backup directory (default: $BACKUP_DIR)
    --help              Show this help message

EXAMPLES:
    $0 --dry-run                    # Preview deletions
    $0 --verbose                    # Execute with detailed output
    $0 --dry-run --verbose          # Preview with detailed output
    $0 --backup-dir /custom/path    # Use custom backup location

SAFETY FEATURES:
    - Complete backup before any deletions
    - SHA256 checksum verification
    - Staged deletion with validation
    - Rollback capability
    - Git branch creation for tracking

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Verbose logging
vlog() {
    if [[ "$VERBOSE" == "true" ]]; then
        log "$1"
    fi
}

# Check if we're in the correct directory
check_repository() {
    if [[ ! -f "$REPO_ROOT/api.py" ]] || [[ ! -d "$REPO_ROOT/app" ]]; then
        error "Not in JK-Agents Framework repository root: $REPO_ROOT"
        exit 1
    fi
    success "Repository validation passed"
}

# Create backup directory structure
create_backup_structure() {
    log "Creating backup directory structure..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would create: $BACKUP_DIR"
        return 0
    fi
    
    mkdir -p "$BACKUP_DIR"/{debug_scripts,diagnostic_scripts,alternative_implementations,log_directories,test_artifacts}
    
    success "Backup directory structure created: $BACKUP_DIR"
}

# Backup a single file with checksum
backup_file() {
    local src="$1"
    local dst_dir="$2"
    local filename=$(basename "$src")
    
    vlog "Backing up: $src"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would backup: $src -> $dst_dir/$filename"
        return 0
    fi
    
    if [[ ! -f "$src" ]]; then
        warning "File not found: $src"
        return 1
    fi
    
    # Copy file
    cp "$src" "$dst_dir/$filename"
    
    # Generate checksum
    local checksum=$(sha256sum "$src" | cut -d' ' -f1)
    echo "$checksum  $filename" >> "$dst_dir/checksums.sha256"
    
    vlog "Backed up with checksum: $checksum"
}

# Backup a directory with checksums
backup_directory() {
    local src="$1"
    local dst_dir="$2"
    local dirname=$(basename "$src")
    
    vlog "Backing up directory: $src"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would backup directory: $src -> $dst_dir/$dirname"
        return 0
    fi
    
    if [[ ! -d "$src" ]]; then
        warning "Directory not found: $src"
        return 1
    fi
    
    # Copy directory
    cp -r "$src" "$dst_dir/$dirname"
    
    # Generate checksums for all files in directory
    find "$dst_dir/$dirname" -type f -exec sha256sum {} \; >> "$dst_dir/checksums.sha256"
    
    vlog "Directory backed up with checksums"
}

# Verify backup integrity
verify_backup() {
    local backup_subdir="$1"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would verify backup integrity in: $backup_subdir"
        return 0
    fi
    
    if [[ ! -f "$backup_subdir/checksums.sha256" ]]; then
        error "Checksum file not found: $backup_subdir/checksums.sha256"
        return 1
    fi
    
    cd "$backup_subdir"
    if sha256sum -c checksums.sha256 >/dev/null 2>&1; then
        success "Backup integrity verified: $backup_subdir"
        cd - >/dev/null
        return 0
    else
        error "Backup integrity check failed: $backup_subdir"
        cd - >/dev/null
        return 1
    fi
}

# Delete a file safely
delete_file() {
    local filepath="$1"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would delete: $filepath"
        return 0
    fi
    
    if [[ ! -f "$filepath" ]]; then
        warning "File not found for deletion: $filepath"
        return 1
    fi
    
    rm "$filepath"
    success "Deleted: $filepath"
}

# Delete a directory safely
delete_directory() {
    local dirpath="$1"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would delete directory: $dirpath"
        return 0
    fi
    
    if [[ ! -d "$dirpath" ]]; then
        warning "Directory not found for deletion: $dirpath"
        return 1
    fi
    
    rm -rf "$dirpath"
    success "Deleted directory: $dirpath"
}

# Create git branch for tracking changes
create_git_branch() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would create git branch: doc-refactor/20250929223246"
        return 0
    fi
    
    cd "$REPO_ROOT"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        warning "Not in a git repository, skipping branch creation"
        return 0
    fi
    
    # Create and checkout new branch
    git checkout -b "doc-refactor/20250929223246" 2>/dev/null || {
        warning "Branch may already exist, continuing..."
        git checkout "doc-refactor/20250929223246" 2>/dev/null || true
    }
    
    success "Git branch created/checked out: doc-refactor/20250929223246"
}

# Stage 1: Low-risk debug scripts
delete_debug_scripts() {
    log "Stage 1: Deleting low-risk debug scripts..."
    
    local backup_subdir="$BACKUP_DIR/debug_scripts"
    local files=(
        "debug_chromadb_v_error.py"
        "debug_langgraph_integration.py"
        "debug_ray12_corrected.py"
        "debug_ray12_retrieval.py"
        "debug_ray_11_storage.py"
        "debug_agent_test.py"
        "debug_v_error.log"
    )
    
    # Backup files
    for file in "${files[@]}"; do
        if [[ -f "$REPO_ROOT/$file" ]]; then
            backup_file "$REPO_ROOT/$file" "$backup_subdir"
        fi
    done
    
    # Verify backup
    verify_backup "$backup_subdir" || {
        error "Backup verification failed for debug scripts"
        return 1
    }
    
    # Delete files
    for file in "${files[@]}"; do
        if [[ -f "$REPO_ROOT/$file" ]]; then
            delete_file "$REPO_ROOT/$file"
        fi
    done
    
    success "Stage 1 completed: Debug scripts deleted"
}

# Stage 2: Diagnostic scripts
delete_diagnostic_scripts() {
    log "Stage 2: Deleting diagnostic scripts..."
    
    local backup_subdir="$BACKUP_DIR/diagnostic_scripts"
    local files=(
        "examine_stored_data.py"
        "diagnose_conversation_store_init.py"
        "diagnose_memory_issues.py"
        "diagnose_production_memory.py"
    )
    
    # Backup files
    for file in "${files[@]}"; do
        if [[ -f "$REPO_ROOT/$file" ]]; then
            backup_file "$REPO_ROOT/$file" "$backup_subdir"
        fi
    done
    
    # Verify backup
    verify_backup "$backup_subdir" || {
        error "Backup verification failed for diagnostic scripts"
        return 1
    }
    
    # Delete files
    for file in "${files[@]}"; do
        if [[ -f "$REPO_ROOT/$file" ]]; then
            delete_file "$REPO_ROOT/$file"
        fi
    done
    
    success "Stage 2 completed: Diagnostic scripts deleted"
}

# Stage 3: Archive log directories (move, don't delete)
archive_log_directories() {
    log "Stage 3: Archiving log directories..."
    
    local backup_subdir="$BACKUP_DIR/log_directories"
    local directories=(
        "agentlogs"
        "agents_direct_logs"
        "memory_logs"
    )
    
    # Backup and move directories
    for dir in "${directories[@]}"; do
        if [[ -d "$REPO_ROOT/$dir" ]]; then
            backup_directory "$REPO_ROOT/$dir" "$backup_subdir"
            
            # Verify backup before deletion
            verify_backup "$backup_subdir" || {
                error "Backup verification failed for $dir"
                return 1
            }
            
            delete_directory "$REPO_ROOT/$dir"
        fi
    done
    
    success "Stage 3 completed: Log directories archived"
}

# Stage 4: Test artifacts (requires manual review)
handle_test_artifacts() {
    log "Stage 4: Handling test artifacts (manual review required)..."
    
    local backup_subdir="$BACKUP_DIR/test_artifacts"
    local items=(
        "temp_tests"
        "test_checkpoints"
        "test_workflow_data"
        "test_results"
        "test_data.txt"
        "test_image.png"
    )
    
    warning "Test artifacts require manual review before deletion"
    warning "Items to review: ${items[*]}"
    
    # Only backup for now, don't delete
    for item in "${items[@]}"; do
        if [[ -f "$REPO_ROOT/$item" ]]; then
            backup_file "$REPO_ROOT/$item" "$backup_subdir"
        elif [[ -d "$REPO_ROOT/$item" ]]; then
            backup_directory "$REPO_ROOT/$item" "$backup_subdir"
        fi
    done
    
    # Verify backup
    verify_backup "$backup_subdir" || {
        error "Backup verification failed for test artifacts"
        return 1
    }
    
    warning "Test artifacts backed up but not deleted - manual review required"
    warning "To delete after review, run: rm -rf ${items[*]}"
}

# Validate system functionality
validate_system() {
    log "Validating system functionality..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would validate system functionality"
        return 0
    fi
    
    cd "$REPO_ROOT"
    
    # Check if Python files can be imported
    if python3 -c "import sys; sys.path.append('.'); from app.main import load_app_config; print('✅ Core imports working')" 2>/dev/null; then
        success "Core module imports validated"
    else
        error "Core module import validation failed"
        return 1
    fi
    
    # Check if API can be imported
    if python3 -c "from api import app; print('✅ API import working')" 2>/dev/null; then
        success "API module import validated"
    else
        error "API module import validation failed"
        return 1
    fi
    
    success "System validation completed"
}

# Commit changes to git
commit_changes() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would commit changes to git"
        return 0
    fi
    
    cd "$REPO_ROOT"
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir >/dev/null 2>&1; then
        warning "Not in a git repository, skipping commit"
        return 0
    fi
    
    # Add and commit documentation
    git add final_docs/
    git commit -m "Add comprehensive repository documentation and deletion plan

- Generated complete module documentation
- Created deletion plan with risk assessment
- Added setup and usage guides
- Documented architecture and data flows" || true
    
    # Commit deletions if any files were actually deleted
    if git status --porcelain | grep -q "^.D"; then
        git add -A
        git commit -m "Clean up debug scripts and diagnostic utilities

- Removed debug scripts (backed up to backup/deletions/20250929_223246/)
- Archived log directories to backup location
- All files backed up with SHA256 checksums for recovery" || true
    fi
    
    success "Changes committed to git"
}

# Generate rollback script
generate_rollback_script() {
    local rollback_script="$BACKUP_DIR/rollback.sh"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "[DRY-RUN] Would generate rollback script: $rollback_script"
        return 0
    fi
    
    cat > "$rollback_script" << 'EOF'
#!/bin/bash

# Rollback script for JK-Agents Framework cleanup
# Generated automatically during deletion process

set -euo pipefail

REPO_ROOT="/Users/A80997271/Documents/projects/jk-agents-framework"
BACKUP_DIR="$(dirname "$0")"

echo "🔄 Rolling back deletions from: $BACKUP_DIR"

# Restore debug scripts
if [[ -d "$BACKUP_DIR/debug_scripts" ]]; then
    echo "Restoring debug scripts..."
    cp "$BACKUP_DIR/debug_scripts"/*.py "$REPO_ROOT/" 2>/dev/null || true
    cp "$BACKUP_DIR/debug_scripts"/*.log "$REPO_ROOT/" 2>/dev/null || true
fi

# Restore diagnostic scripts
if [[ -d "$BACKUP_DIR/diagnostic_scripts" ]]; then
    echo "Restoring diagnostic scripts..."
    cp "$BACKUP_DIR/diagnostic_scripts"/*.py "$REPO_ROOT/" 2>/dev/null || true
fi

# Restore log directories
if [[ -d "$BACKUP_DIR/log_directories" ]]; then
    echo "Restoring log directories..."
    cp -r "$BACKUP_DIR/log_directories"/* "$REPO_ROOT/" 2>/dev/null || true
fi

# Restore test artifacts
if [[ -d "$BACKUP_DIR/test_artifacts" ]]; then
    echo "Restoring test artifacts..."
    cp -r "$BACKUP_DIR/test_artifacts"/* "$REPO_ROOT/" 2>/dev/null || true
fi

echo "✅ Rollback completed"
echo "⚠️  You may need to run 'git checkout .' to restore git state"
EOF

    chmod +x "$rollback_script"
    success "Rollback script generated: $rollback_script"
}

# Main execution function
main() {
    log "JK-Agents Framework Safe Deletion Script"
    log "========================================="
    
    if [[ "$DRY_RUN" == "true" ]]; then
        warning "DRY-RUN MODE: No actual changes will be made"
    fi
    
    # Pre-flight checks
    check_repository
    create_backup_structure
    create_git_branch
    
    # Execute deletion stages
    delete_debug_scripts || {
        error "Stage 1 failed: Debug scripts deletion"
        exit 1
    }
    
    delete_diagnostic_scripts || {
        error "Stage 2 failed: Diagnostic scripts deletion"
        exit 1
    }
    
    archive_log_directories || {
        error "Stage 3 failed: Log directory archival"
        exit 1
    }
    
    handle_test_artifacts || {
        error "Stage 4 failed: Test artifacts handling"
        exit 1
    }
    
    # Post-deletion validation
    validate_system || {
        error "System validation failed after deletions"
        exit 1
    }
    
    # Finalization
    generate_rollback_script
    commit_changes
    
    success "Deletion process completed successfully!"
    
    if [[ "$DRY_RUN" == "false" ]]; then
        log ""
        log "Summary:"
        log "- Debug scripts: Deleted and backed up"
        log "- Diagnostic scripts: Deleted and backed up"
        log "- Log directories: Archived to backup location"
        log "- Test artifacts: Backed up (manual review required)"
        log "- Backup location: $BACKUP_DIR"
        log "- Rollback script: $BACKUP_DIR/rollback.sh"
        log ""
        warning "To complete cleanup, manually review test artifacts in:"
        warning "$BACKUP_DIR/test_artifacts/"
    fi
}

# Execute main function
main "$@"
