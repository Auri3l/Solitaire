"""Standalone single-file Windows executable packaging pipeline for Solitaire Suite.

Packages the entire Python application, Pygame-ce runtime, and rules engine
into a self-contained single-file PE binary (SolitaireSuite.exe) placed in the
project root directory.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build() -> int:
    project_root = Path(__file__).resolve().parent
    dist_dir = project_root
    build_dir = project_root / "build"
    output_exe = dist_dir / "SolitaireSuite.exe"

    print("===============================================================")
    print("  Solitaire Suite — Standalone Single-File Windows Packaging")
    print("===============================================================")
    print(f"Project root: {project_root}")
    print(f"Target binary: {output_exe}")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        "SolitaireSuite",
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        "--specpath",
        str(project_root),
        "--collect-all",
        "pygame",
        "--collect-all",
        "solitaire",
        "--hidden-import",
        "solitaire",
        "--hidden-import",
        "solitaire.core",
        "--hidden-import",
        "solitaire.games",
        "--hidden-import",
        "solitaire.ai",
        "--hidden-import",
        "solitaire.gui",
        str(project_root / "main.py"),
    ]

    print("\nExecuting PyInstaller command:")
    print(" ".join(cmd))
    print()

    proc = subprocess.run(cmd, cwd=str(project_root))
    if proc.returncode != 0:
        print(f"\n[BUILD ERROR] PyInstaller exited with code {proc.returncode}", file=sys.stderr)
        return proc.returncode

    if not output_exe.exists():
        print(f"\n[BUILD ERROR] Expected executable not found at {output_exe}", file=sys.stderr)
        return 1

    file_size_mb = output_exe.stat().st_size / (1024 * 1024)
    print(f"\n[BUILD SUCCESS] Standalone executable created: {output_exe} ({file_size_mb:.2f} MB)")

    # Clean up intermediate build directory to keep repository clean
    if build_dir.exists():
        print("Cleaning up intermediate build files...")
        shutil.rmtree(build_dir, ignore_errors=True)

    print("===============================================================")
    print("  Verifying Standalone Executable with Headless Smoke Test")
    print("===============================================================")
    verify_cmd = [str(output_exe), "--test-ui-smoke"]
    print(f"Running: {' '.join(verify_cmd)}")
    verify_proc = subprocess.run(verify_cmd, cwd=str(project_root))
    if verify_proc.returncode != 0:
        print(f"\n[VERIFICATION ERROR] Standalone executable failed smoke verification with code {verify_proc.returncode}", file=sys.stderr)
        return verify_proc.returncode

    print("\n[VERIFICATION SUCCESS] Standalone single-file executable passed all tests out-of-the-box!")
    return 0


if __name__ == "__main__":
    sys.exit(build())
