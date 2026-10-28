"""Independent Sage point and matrix audit of the support-eight residual result."""
import hashlib
import json
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / "experiments/hecke-d79-live-seven-20261027"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def rank(rows, field):
    return int(matrix(field, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def main():
    for directory in (HERE, HERE / "full"):
        seal = json.loads((directory / "pre-run.json").read_text())
        for path, digest in seal["inputs"].items():
            assert sha(ROOT / path) == digest, path
        for name, field in (("PROTOCOL.md", "protocol_sha256"),
                            ("run_sage.py", "runner_sha256"),
                            ("sage-runtime-info.txt", "runtime_info_sha256")):
            assert sha(directory / name) == seal[field]
    initial = json.loads((HERE / "result.json").read_text())
    result = json.loads((HERE / "full/result.json").read_text())
    assert initial["status"] == "CENSORED_PROBE_CAP"
    assert (initial["quintuple_sign_probes"], initial["rank_after"], initial["matches"]) == (12000000, 38, 168)
    assert result["status"] == "RANK_39_FOUND"
    assert result["quintuple_sign_probes"] > initial["quintuple_sign_probes"]
    assert result["triple_entries"] == 39520
    assert result["matches"] == result["verified_rows"] == 225
    selection = json.loads((SOURCE / "selection.json").read_text())
    frozen = next(x for x in selection["selected"] if x["p"] == 1825517)
    records = [json.loads(line) for line in (SOURCE / "cases/p1825517.jsonl").read_text().splitlines()]
    assert len(records) == 40
    E = EllipticCurve(GF(1825517), [0, -1, 1, -10, -20])
    assert int(E.cardinality()) == frozen["class"]["curve_order"]
    points = [E(x, y) for x, y in frozen["class"]["class_points"]]
    zero = E(0)
    rows = [sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
    for k, rec in enumerate(records):
        entry = rec["entry"]
        assert rec["source"] == entry["source"] == k
        assert entry["status"] == "OUTSIDE_CLASS_TRACE"
        outside = sum((E(x, y) for x, y in entry["outside_traces"]), zero)
        inside = sum((value * points[j] for j, value in sparse(entry["class_part"]).items()), zero)
        assert outside + inside == zero
        for family in ("four", "five", "six", "seven"):
            rows.extend(sparse(x["row"]) for x in rec["rows"][family])
    F = GF(6091)
    assert rank(rows, F) == result["rank_before"] == 38
    selected = result["selected_row"]
    sources = tuple(selected["sources"])
    signs = tuple(selected["coefficients"])
    assert len(sources) == len(set(sources)) == len(signs) == 8
    assert sources == tuple(sorted(sources)) and signs[0] == 1
    assert all(sign in (-1, 1) for sign in signs)
    assert sum((sign * sum((E(x, y) for x, y in records[i]["entry"]["outside_traces"]), zero)
                for i, sign in zip(sources, signs)), zero) == zero
    row = Counter()
    for i, sign in zip(sources, signs):
        for j, value in sparse(records[i]["entry"]["class_part"]).items():
            row[j] += sign * value
    row = {j: value for j, value in row.items() if value}
    assert row == sparse(selected["row"])
    assert sum((value * points[j] for j, value in row.items()), zero) == zero
    rows.append(row)
    assert rank(rows, F) == result["rank_after"] == 39
    projected = [(frozen["class"]["curve_order"] // 6091) * point for point in points]
    anchor = result["anchor_index"]
    T = projected[anchor]
    assert int(T.order()) == 6091
    A = matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0))
    augmented = A.stack(matrix(F, 1, 40, lambda _, j: int(j == anchor)))
    logs = [int(x) for x in augmented.solve_right(vector(F, [0] * len(rows) + [1]))]
    assert logs == result["anchored_logs"]
    assert all(log * T == point for log, point in zip(logs, projected))
    audit = {"schema": "hecke-d79-support-eight-audit-v1", "status": "PASS",
             "source_equations": 40, "rank_before": 38, "rank_after": 39,
             "selected_row": selected, "anchored_log_replay": "PASS"}
    (HERE / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps({k: v for k, v in audit.items() if k != "selected_row"}), flush=True)


if __name__ == "__main__":
    main()
