"""Skill packager with preflight audit."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parent.parent
LOG_PATH = SKILL_PATH / "_pkg_log.txt"

EXCLUDE = {
    ".agents",
    ".claude",
    ".qoder",
    ".trae",
    "skills",
    "test-output",
    "src",
    "_do_package.py",
    "package_skill.py",
    "run_package.bat",
    "_pkg_log.txt",
    "_pkg_result.txt",
    "package_log.txt",
    "PACKAGING.md",
    ".git",
    ".venv",
    ".idea",
    ".workbuddy",
    "__pycache__",
    ".DS_Store",
    "testcase-generator.zip",
}


def run_audit() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/capability_audit.py"],
        cwd=SKILL_PATH,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


with open(LOG_PATH, "w", encoding="utf-8", errors="replace") as log:
    def log_write(msg: str = "") -> None:
        print(msg, flush=True)
        log.write(msg + "\n")
        log.flush()

    audit_result = run_audit()
    log_write("Preflight audit:")
    log_write(audit_result.stdout.rstrip())
    if audit_result.stderr:
        log_write(audit_result.stderr.rstrip())
    if audit_result.returncode != 0:
        raise SystemExit("Packaging aborted: capability audit failed.")

    skill_md = SKILL_PATH / "SKILL.md"
    log_write(f"Skill root: {SKILL_PATH}")
    log_write(f"SKILL.md: {skill_md.exists()}")
    log_write(f"prompts/: {(SKILL_PATH / 'prompts').exists()}")
    log_write(f"config/: {(SKILL_PATH / 'config').exists()}")
    log_write(f"templates/: {(SKILL_PATH / 'templates').exists()}")
    log_write(f"resources/: {(SKILL_PATH / 'resources').exists()}")

    zip_file = SKILL_PATH / "testcase-generator.zip"
    count = 0
    skipped = 0
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(SKILL_PATH.rglob("*")):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(SKILL_PATH)
            parts = set(rel.parts)
            if any(ex in parts or rel.name in EXCLUDE for ex in EXCLUDE):
                skipped += 1
                continue
            if rel.name.startswith("."):
                skipped += 1
                continue
            zf.write(file_path, rel)
            log_write(f"  + {rel}")
            count += 1

    size_kb = zip_file.stat().st_size / 1024
    log_write(f"\nPacked: {count} files | Skipped: {skipped}")
    log_write(f"Created: {zip_file} ({size_kb:.1f} KB)")
