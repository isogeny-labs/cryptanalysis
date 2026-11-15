"""Replay file custody and native JSON comparison only, not a math verifier.

All cryptographic arithmetic runs in the original Rust engines; Lean/PCC use
the unchanged original verifiers. Known-answer data is outside public input.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys

mode = sys.argv[1]
if mode == "snapshot":
    repo, producer, out = map(Path, sys.argv[2:])
    ref = repo / "experiments/chained-transfer-public-target/reference-02.sha256"
    for line in ref.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        source = (repo / relative).resolve()
        if source.is_relative_to(repo):
            destination = out / "source/cryptanalysis" / source.relative_to(repo)
        else:
            assert source.is_relative_to(producer)
            destination = out / "source/crypto" / source.relative_to(producer)
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
elif mode == "oversize":
    index, target = map(Path, sys.argv[2:])
    spec = json.loads(index.read_text())["oversize"]
    raw = b" " * 65537  # Exact original process-control bytes, not crypto arithmetic.
    assert len(raw) == spec["bytes"] and hashlib.sha256(raw).hexdigest() == spec["sha256"]
    target.write_bytes(raw)
elif mode == "outputs":
    study, out = map(Path, sys.argv[2:])
    assert json.loads((out / "describe.json").read_text()) == json.loads((study / "fixtures/identity.json").read_text())
    result = json.loads((out / "public-five.json").read_text())
    expected = json.loads((study / "fixtures/expected-OUTSIDE-input.json").read_text())
    assert result["ok"] and len(result["results"]) == 5
    for row, answer in zip(result["results"], expected, strict=True):
        assert row["ok"] and row["k_found"] == answer["original_native_recovered_scalar"]
        assert len(row["attempts"]) == 2
        assert row["attempts"][-1]["independent_original_source_check"]
        assert not row["attempts"][0]["original"]["ok"]
    names = ["foreign-q", "schema", "field", "model", "noncanonical", "offcurve", "nonmember", "unknown-scalar", "unknown-witness", "empty", "six", "oversize", "extra-arg"]
    assert all(not (out / ("reject-" + label + ".json")).exists() for label in names)
    assert (out / "overwrite.json").read_bytes() == b"original output sentinel\n"
    print("Native JSON bytes/answers and rejection-output custody match; not a new mathematical verdict.")
elif mode == "phases":
    out = Path(sys.argv[2])
    rows = [line.split() for line in (out / "phase-index.txt").read_text().splitlines()]
    policy = json.loads((Path(__file__).resolve().parent / "fixtures/phase-policy.json").read_text())
    assert [[row[0], int(row[1])] for row in rows] == policy["ordered_expected_native_exits"]
    assert len(rows) == len({row[0] for row in rows})
    for label, expected, original in rows:
        pair = (out / (label + ".pipe-exits")).read_text().split()
        assert pair == [original, "0"] and original == expected
    assert sum(row[1] == "2" for row in rows) == 14
    print("All", len(rows), "phase pairs match expected native/tee exits;14 native exit2 controls intentional.")
else:
    raise SystemExit("unknown byte-custody mode")
