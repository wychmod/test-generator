# .harness/hooks/install-hooks.ps1
# Cross-platform-ish: works on Windows PowerShell 5.1+ and PowerShell 7+.
#
# Usage (from the repository root):
#   powershell -ExecutionPolicy Bypass -File .harness/hooks/install-hooks.ps1
#
# Behaviour:
#   1. Verifies the current working directory is the project root (.git/ exists).
#   2. Refuses to clobber any pre-commit / pre-package hook that is not ours.
#   3. Copies precommit.py and prepackage.py into .git/hooks/.
#   4. Emits a small "installed" banner so the operator sees the result.
#
# The script is idempotent: re-running it overwrites our own copies
# only.  If you want a different pre-commit hook, remove
# `.git/hooks/pre-commit` first and re-run this script.

[CmdletBinding()]
param(
    [string]$RepoRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

function Write-Banner([string]$message) {
    Write-Host "[install-hooks] $message" -ForegroundColor Cyan
}

function Test-OwnedByUs([string]$hookPath) {
    if (-not (Test-Path -LiteralPath $hookPath)) {
        return $true
    }
    $content = Get-Content -LiteralPath $hookPath -Raw -Encoding UTF8
    return ($content -match "testcase-generator")
}

function Install-OneHook([string]$SourceRelative, [string]$HookName) {
    $sourcePath = Join-Path -Path $RepoRoot -ChildPath ".harness/hooks/$SourceRelative"
    $targetPath = Join-Path -Path $RepoRoot -ChildPath ".git/hooks/$HookName"

    if (-not (Test-Path -LiteralPath $sourcePath)) {
        throw "missing source hook: $sourcePath"
    }

    if ((Test-Path -LiteralPath $targetPath) -and -not (Test-OwnedByUs $targetPath)) {
        throw "refusing to overwrite ${targetPath}: existing hook is not owned by testcase-generator"
    }

    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    Write-Banner "installed $HookName (-> $targetPath)"
}

function Main {
    $gitDir = Join-Path -Path $RepoRoot -ChildPath ".git"
    if (-not (Test-Path -LiteralPath $gitDir)) {
        throw "no .git directory at $gitDir. Run this script from the project root."
    }

    Install-OneHook -SourceRelative "precommit.py" -HookName "pre-commit"
    Install-OneHook -SourceRelative "prepackage.py" -HookName "pre-package"

    Write-Banner "done.  use --dry-run to test before you commit:"
    Write-Host "    python .harness/hooks/precommit.py --dry-run"
}

Main
