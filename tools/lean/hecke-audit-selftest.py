#!/usr/bin/env python3
"""Real pinned-Lean controls for the exhaustive Hecke theorem auditor."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "experiments/hecke-432-formal-ci-20261025"


def command(args, env=None):
    result = subprocess.run(args, cwd=PROJECT, env=env, text=True, capture_output=True)
    print(result.stdout + result.stderr, end="", flush=True)
    return result.returncode


def main():
    lean_path = subprocess.check_output(
        ["lake", "env", "printenv", "LEAN_PATH"], cwd=PROJECT, text=True).strip()
    controls = {
        "Positive": ("theorem reflexive (x : Nat) : x = x := rfl\n", 0, 0),
        "Assumed": ("axiom unproved : False\ntheorem claimed : False := unproved\n", 0, 1),
        "Empty": ("def value := 1\n", 0, 1),
        "IllTyped": ("theorem impossible : False := by trivial\n", 1, None),
    }
    with tempfile.TemporaryDirectory(prefix="hecke-native-controls-") as scratch:
        for name, (source, compile_exit, audit_exit) in controls.items():
            path = Path(scratch) / f"{name}.lean"
            path.write_text(source)
            compiled = command(["lake", "env", "lean", "-R", scratch, "-o",
                                str(path.with_suffix(".olean")), str(path)])
            if compiled != compile_exit:
                raise ValueError(f"native compiler control failed: {name}: {compiled}")
            if audit_exit is not None:
                env = {**os.environ, "LEAN_PATH": scratch + os.pathsep + lean_path}
                audited = command(["lean", "--run",
                                   str(ROOT / "tools/lean/AuditHeckeAxioms.lean"), name], env)
                if audited != audit_exit:
                    raise ValueError(f"native axiom control failed: {name}: {audited}")
            print(f"PASS native control: {name}", flush=True)


if __name__ == "__main__":
    main()
