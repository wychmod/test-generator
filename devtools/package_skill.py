"""Skill packager with preflight audit and archive validation."""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "_pkg_log.txt"
MANIFEST_PATH = ROOT / "skill.manifest.json"
ARCHIVE_BASENAME = "testcase-generator"
ARCHIVE_EXTENSIONS = (".skill", ".zip")
STATIC_EXCLUDES = {
    "_pkg_log.txt",
    "_pkg_result.txt",
    "package_log.txt",
    "PACKAGING.md",
    "run_package.bat",
    ".git",
    ".venv",
    ".idea",
    ".workbuddy",
    "__pycache__",
    ".DS_Store",
    "devtools",
}
REQUIRED_ARCHIVE_MEMBERS = {
    "SKILL.md",
    "README.md",
    "DISTRIBUTION.md",
    "skill.manifest.json",
}
FORBIDDEN_ARCHIVE_PATTERNS = {
    "test-output/**",
    ".workbuddy/**",
    ".agents/**",
    ".claude/**",
    ".qoder/**",
    ".trae/**",
    "skills/**",
    "skills-lock.json",
    "*.skill",
    "*.zip",
}


def read_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def normalize_patterns(values: Iterable[str]) -> list[str]:
    patterns: list[str] = []
    for value in values:
        if value.endswith("/**"):
            base = value[:-3].rstrip("/")
            patterns.extend([value, base, f"{base}/**"])
        else:
            patterns.append(value)
    return patterns


def path_matches(path_str: str, patterns: Iterable[str]) -> bool:
    normalized = path_str.replace("\\", "/")
    for pattern in patterns:
        if fnmatch(normalized, pattern):
            return True
    return False


def build_allowed_patterns(manifest: dict) -> list[str]:
    runtime_files = manifest.get("运行时文件", [])
    return normalize_patterns(runtime_files + ["DISTRIBUTION.md", "skill.manifest.json"])


def build_excluded_patterns(manifest: dict) -> list[str]:
    dynamic = list(manifest.get("分发排除", []))
    dynamic.extend([f"{ARCHIVE_BASENAME}.skill", f"{ARCHIVE_BASENAME}.zip"])
    return normalize_patterns(dynamic)


def should_skip(rel_path: Path, excluded_patterns: list[str], allowed_patterns: list[str]) -> bool:
    path_str = rel_path.as_posix()
    parts = set(rel_path.parts)
    if rel_path.name.startswith("."):
        return True
    if parts & STATIC_EXCLUDES:
        return True
    if path_matches(path_str, excluded_patterns):
        return True
    if not path_matches(path_str, allowed_patterns):
        return True
    return False


def run_audit() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "devtools/capability_audit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def collect_package_members(excluded_patterns: list[str], allowed_patterns: list[str]) -> tuple[list[Path], int]:
    included: list[Path] = []
    skipped = 0
    for file_path in sorted(ROOT.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(ROOT)
        if should_skip(rel, excluded_patterns, allowed_patterns):
            skipped += 1
            continue
        included.append(rel)
    return included, skipped


def validate_archive(archive_path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(archive_path, "r") as zf:
        names = sorted(zf.namelist())

    missing = sorted(REQUIRED_ARCHIVE_MEMBERS - set(names))
    if missing:
        errors.append(f"{archive_path.name} 缺少必需文件: {', '.join(missing)}")

    forbidden = [name for name in names if path_matches(name, normalize_patterns(FORBIDDEN_ARCHIVE_PATTERNS))]
    if forbidden:
        errors.append(f"{archive_path.name} 包含禁止项: {', '.join(forbidden)}")

    return errors


def compare_archives(skill_archive: Path, zip_archive: Path) -> list[str]:
    with zipfile.ZipFile(skill_archive, "r") as skill_zf:
        skill_names = sorted(skill_zf.namelist())
    with zipfile.ZipFile(zip_archive, "r") as zip_zf:
        zip_names = sorted(zip_zf.namelist())

    if skill_names != zip_names:
        return [".skill 与 .zip 产物内容不一致"]
    return []


with open(LOG_PATH, "w", encoding="utf-8", errors="replace") as log:
    def log_write(msg: str = "") -> None:
        print(msg, flush=True)
        log.write(msg + "\n")
        log.flush()

    manifest = read_manifest()
    allowed_patterns = build_allowed_patterns(manifest)
    excluded_patterns = build_excluded_patterns(manifest)

    audit_result = run_audit()
    log_write("Preflight audit:")
    log_write(audit_result.stdout.rstrip())
    if audit_result.stderr:
        log_write(audit_result.stderr.rstrip())
    if audit_result.returncode != 0:
        raise SystemExit("Packaging aborted: capability audit failed.")

    included_files, skipped = collect_package_members(excluded_patterns, allowed_patterns)

    skill_md = ROOT / "SKILL.md"
    log_write(f"Skill root: {ROOT}")
    log_write(f"SKILL.md: {skill_md.exists()}")
    log_write(f"prompts/: {(ROOT / 'prompts').exists()}")
    log_write(f"config/: {(ROOT / 'config').exists()}")
    log_write(f"templates/: {(ROOT / 'templates').exists()}")
    log_write(f"resources/: {(ROOT / 'resources').exists()}")
    log_write(f"manifest 驱动入包规则: {MANIFEST_PATH}")

    archives: list[Path] = []
    for ext in ARCHIVE_EXTENSIONS:
        archive_path = ROOT / f"{ARCHIVE_BASENAME}{ext}"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for rel in included_files:
                zf.write(ROOT / rel, rel)
                log_write(f"  + {rel}")
        size_kb = archive_path.stat().st_size / 1024
        log_write(f"Created: {archive_path} ({size_kb:.1f} KB)")
        archives.append(archive_path)

    validation_errors: list[str] = []
    for archive in archives:
        validation_errors.extend(validate_archive(archive))
    validation_errors.extend(compare_archives(archives[0], archives[1]))

    if validation_errors:
        for error in validation_errors:
            log_write(f"[ERROR] {error}")
        raise SystemExit("Packaging aborted: archive validation failed.")

    log_write(f"\nPacked: {len(included_files)} files | Skipped: {skipped}")
    log_write("Archive validation: passed")
