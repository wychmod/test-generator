#!/usr/bin/env bash
# .harness/hooks/install-hooks.sh
#
# Usage (from the repository root):
#   bash .harness/hooks/install-hooks.sh
#
# Behaviour:
#   1. Verifies the current working directory is the project root (.git/ exists).
#   2. Refuses to clobber any pre-commit / pre-package hook that is not ours.
#   3. Copies precommit.py and prepackage.py into .git/hooks/.
#   4. chmod +x on the installed hooks so git will actually run them.
#
# Idempotent: re-running overwrites our own hooks only.  Drop a foreign
# pre-commit/pre-package hook to disable ours and you can re-install
# any time.

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(pwd)}"
HARNESS_HOOKS_DIR="$REPO_ROOT/.harness/hooks"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"

if [[ ! -d "$REPO_ROOT/.git" ]]; then
    echo "[install-hooks] no .git directory at $REPO_ROOT/.git" >&2
    echo "[install-hooks] run this script from the project root." >&2
    exit 1
fi

mkdir -p "$GIT_HOOKS_DIR"

is_ours() {
    local hook_path="$1"
    [[ ! -f "$hook_path" ]] && return 0
    grep -q "testcase-generator" "$hook_path"
}

install_one() {
    local source_name="$1"
    local target_name="$2"

    local source_path="$HARNESS_HOOKS_DIR/$source_name"
    local target_path="$GIT_HOOKS_DIR/$target_name"

    if [[ ! -f "$source_path" ]]; then
        echo "[install-hooks] missing source hook: $source_path" >&2
        exit 1
    fi

    if [[ -f "$target_path" ]] && ! is_ours "$target_path"; then
        echo "[install-hooks] refusing to overwrite $target_path: existing hook is not owned by testcase-generator" >&2
        exit 1
    fi

    cp "$source_path" "$target_path"
    chmod +x "$target_path"
    echo "[install-hooks] installed $target_name -> $target_path"
}

install_one "precommit.py" "pre-commit"
install_one "prepackage.py" "pre-package"

echo "[install-hooks] done. test with:"
echo "    python .harness/hooks/precommit.py --dry-run"
