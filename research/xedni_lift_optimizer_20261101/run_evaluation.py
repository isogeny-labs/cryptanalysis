#!/usr/bin/env python3
"""Run the frozen deterministic xedni affine-lift quality diagnostic."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path


CASES = ((0, 1), (1, 27), (2, 125), (4, 729))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    fixture = root / "inputs" / "p67_balanced_snf.json"
    args.output.mkdir(parents=True, exist_ok=False)

    rows = []
    for radius, cap in CASES:
        command = [
            str(args.binary.resolve()),
            "--json",
            "xedni-lift",
            "--input",
            str(fixture),
            "--radius",
            str(radius),
            "--max-candidates",
            str(cap),
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        raw_path = args.output / f"radius-{radius}.json"
        if completed.returncode != 0:
            failure = {
                "command": command,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
            raw_path.write_text(json.dumps(failure, indent=2) + "\n")
            raise SystemExit(f"radius {radius} failed; retained {raw_path}")
        report = json.loads(completed.stdout)
        raw_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        result = report["result"]
        assert result["exact_constraints_preserved"] is True
        assert result["congruence_preserved"] is True
        assert result["optimized_score"]["nonsingular"] is True
        assert result["candidates_evaluated"] <= cap
        rows.append(
            {
                "radius": radius,
                "candidate_cap": cap,
                "candidates_evaluated": result["candidates_evaluated"],
                "raw_discriminant_bits": result["baseline_score"]["discriminant_bits"],
                "babai_discriminant_bits": result["babai_score"]["discriminant_bits"],
                "optimized_discriminant_bits": result["optimized_score"]["discriminant_bits"],
                "raw_coefficient_bits": result["baseline_score"]["coefficient_height_bits"],
                "babai_coefficient_bits": result["babai_score"]["coefficient_height_bits"],
                "optimized_coefficient_bits": result["optimized_score"]["coefficient_height_bits"],
                "exact_constraints_preserved": result["exact_constraints_preserved"],
                "congruence_preserved": result["congruence_preserved"],
                "raw_file": raw_path.name,
            }
        )

    summary = {
        "schema_version": 1,
        "status": "complete",
        "claim_scope": "one deterministic toy prime-field coefficient coset; no timing or ECDLP-success claim",
        "binary": str(args.binary.resolve()),
        "binary_sha256": sha256(args.binary),
        "input": str(fixture),
        "input_sha256": sha256(fixture),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "rows": rows,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()

