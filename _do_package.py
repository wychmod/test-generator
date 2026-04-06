"""Skill packager."""
import zipfile
from pathlib import Path

skill_path = Path.cwd()
log_path = Path("d:/pycharm/test-generator/_pkg_log.txt")

# Files/dirs to EXCLUDE
EXCLUDE = {
    "test-output", "src", "package_skill.py", "_do_package.py",
    "run_package.bat", "_pkg_log.txt", "_pkg_result.txt",
    "package_log.txt", "PACKAGING.md", ".git", ".venv", ".idea",
    ".workbuddy", "__pycache__", ".DS_Store", "testcase-generator.zip",
}

with open(log_path, "w", encoding="utf-8", errors="replace") as log:
    def log_write(msg=""):
        print(msg, flush=True)
        log.write(msg + "\n")
        log.flush()

    skill_md = skill_path / "SKILL.md"
    log_write(f"Skill root: {skill_path}")
    log_write(f"SKILL.md: {skill_md.exists()}")
    log_write(f"prompts/: {(skill_path / 'prompts').exists()}")
    log_write(f"config/: {(skill_path / 'config').exists()}")
    log_write(f"templates/: {(skill_path / 'templates').exists()}")
    log_write(f"resources/: {(skill_path / 'resources').exists()}")

    zip_file = skill_path / "testcase-generator.zip"
    count = 0
    skipped = 0
    with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in sorted(skill_path.rglob("*")):
            if not fp.is_file():
                continue
            rel = fp.relative_to(skill_path)
            parts = set(rel.parts)
            if any(ex in parts or rel.name in EXCLUDE for ex in EXCLUDE):
                skipped += 1
                continue
            if rel.name.startswith("."):
                skipped += 1
                continue
            zf.write(fp, rel)
            log_write(f"  + {rel}")
            count += 1

    size_kb = zip_file.stat().st_size / 1024
    log_write(f"\nPacked: {count} files | Skipped: {skipped}")
    log_write(f"Created: {zip_file} ({size_kb:.1f} KB)")
