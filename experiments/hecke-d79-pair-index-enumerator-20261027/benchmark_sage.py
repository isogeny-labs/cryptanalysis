"""Paired exact-output and exploratory operation comparison on sealed traces."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())
CODE_SEAL = json.loads((HERE / "pre-run-v2.json").read_text())


def sealed(path, digest):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, str(path)
    return json.loads(raw)


def module(path, digest, name):
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def canonical(rows):
    keys = [(tuple(x["sources"]), tuple(x["coefficients"]),
             tuple(sorted((int(j), int(v)) for j, v in x["row"].items()))) for x in rows]
    assert len(keys) == len(set(keys)), "DUPLICATE_RELATION"
    return sorted(keys)


def digest(keys):
    raw = json.dumps(keys, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def save(out):
    (HERE / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


def main():
    baseline_item = PLAN["exhaustive_helper"]
    baseline = module(ROOT / baseline_item["path"], baseline_item["sha256"], "pair_benchmark_exhaustive")
    pair = module(HERE / "pair_index.py", CODE_SEAL["pair_index_sha256"], "pair_benchmark_index")
    out = {"schema": "hecke-d79-pair-index-benchmark-v1", "status": "RUNNING", "cases": [],
           "repetitions": PLAN["repetitions"], "pair_index_sha256": CODE_SEAL["pair_index_sha256"],
           "candidate_id": None, "target_online_ms": None}
    save(out)
    for family in PLAN["families"]:
        directory = ROOT / family["dir"]
        selection = sealed(directory / family["selection"], family["selection_sha256"])
        challenge = sealed(directory / family["challenge"], family["challenge_sha256"])
        audit = sealed(directory / "audit.json", family["audit_sha256"])
        assert challenge["status"] == "COMPLETE" and audit["status"] == "PASS"
        for frozen, produced, audited in zip(selection["selected"], challenge["cases"], audit["cases"]):
            p = frozen["p"]
            assert produced["p"] == audited["p"] == p and produced["status"] == "COMPLETE"
            entries = {x["source"]: x for x in produced["source_entries"]}
            assert len(entries) == 40 and all(x["status"] == "OUTSIDE_CLASS_TRACE" for x in entries.values())
            expected_count = produced["hecke_candidate_count"]
            assert expected_count == audited.get("hecke_candidate_count", audited.get("hecke_rows_verified"))
            points = [tuple(x) for x in frozen["class"]["class_points"]]
            cell = {"family": family["name"], "p": p, "q": frozen["q"],
                    "status": "RUNNING", "pairs": [], "expected_candidate_count": expected_count,
                    "candidate_id": None, "target_online_ms": None}
            out["cases"].append(cell)
            save(out)
            for repetition in range(1, PLAN["repetitions"] + 1):
                order = ["exhaustive", "pair_index"] if repetition % 2 else ["pair_index", "exhaustive"]
                record = {"repetition": repetition, "order": order, "methods": {}, "status": "RUNNING"}
                cell["pairs"].append(record)
                save(out)
                try:
                    rowsets = {}
                    for method in order:
                        neg_raw, add_raw = baseline.group_law(p)
                        counts = {"group_add_calls": 0, "group_neg_calls": 0}

                        def neg(x):
                            counts["group_neg_calls"] += 1
                            return neg_raw(x)

                        def add(x, y):
                            counts["group_add_calls"] += 1
                            return add_raw(x, y)

                        t0 = time.perf_counter_ns()
                        if method == "exhaustive":
                            rows, trials = baseline.hecke_rows(entries, points, neg, add)
                            metrics = {"signed_support_trials": trials}
                        else:
                            rows, metrics = pair.hecke_rows_pair_index(entries, points, neg, add)
                        wall_ns = time.perf_counter_ns() - t0
                        keys = canonical(rows)
                        rowsets[method] = keys
                        record["methods"][method] = {"wall_ns": wall_ns, "row_count": len(rows),
                                                     "row_digest": digest(keys), **counts, **metrics}
                        save(out)
                    assert rowsets["exhaustive"] == rowsets["pair_index"]
                    assert len(rowsets["pair_index"]) == cell["expected_candidate_count"]
                    record["status"] = "EXACT_ROWS_MATCH"
                except Exception as exc:
                    record.update({"status": "FAILED", "error_type": type(exc).__name__,
                                   "error": str(exc)[:300]})
                save(out)
                print(json.dumps({"p": p, "repetition": repetition, "status": record["status"]}), flush=True)
            cell["status"] = "COMPLETE" if all(x["status"] == "EXACT_ROWS_MATCH" for x in cell["pairs"]) else "FAILED_PAIR"
            save(out)
    out["status"] = "COMPLETE" if all(x["status"] == "COMPLETE" for x in out["cases"]) else "COMPLETE_WITH_FAILURES"
    out["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save(out)
    print(json.dumps({"status": out["status"], "cases": len(out["cases"])}))


if __name__ == "__main__":
    main()
