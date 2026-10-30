"""Replay incremental index and rank basis on ten sealed historical traces."""
import hashlib
import importlib.util
import json
from pathlib import Path

from incremental import PairIndex, RankBasis, sparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())


def sealed(item):
    path = ROOT / item["path"]
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item["sha256"]
    return json.loads(raw)


def module(item, name):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def canonical(rows):
    return sorted((tuple(x["sources"]), tuple(x["coefficients"]),
                   tuple(sorted((int(j), int(v)) for j, v in x["row"].items()))) for x in rows)


def main():
    history = sealed(PLAN["retrospective_inputs"])
    R = module(PLAN["frozen"]["relation_helpers"], "incremental_baseline_helper")
    P = module(PLAN["pair_index_reference"], "incremental_static_reference")
    out = []
    for family in history["families"]:
        directory = ROOT / family["dir"]
        for name, digest in ((family["selection"], family["selection_sha256"]),
                             (family["challenge"], family["challenge_sha256"]),
                             ("audit.json", family["audit_sha256"])):
            assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest
        selection = json.loads((directory / family["selection"]).read_text())
        challenge = json.loads((directory / family["challenge"]).read_text())
        for frozen, produced in zip(selection["selected"], challenge["cases"]):
            p, q = frozen["p"], frozen["q"]
            entries = produced["source_entries"]
            neg, add = R.group_law(p)
            points = [tuple(x) for x in frozen["class"]["class_points"]]
            baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
            basis = RankBasis(q, baseline)
            index = PairIndex(points, neg, add)
            assert basis.rank == frozen["baseline_rank_mod_q"]
            first_goal = None
            for count, entry in enumerate(entries, 1):
                rows, _ = index.append(entry)
                for row in rows:
                    basis.insert(sparse(row["row"]))
                assert basis.rank == R.rank(baseline + [sparse(x["row"]) for x in index.rows], q)
                if first_goal is None and basis.rank >= PLAN["rank_goal"]:
                    first_goal = count
            static, _ = P.hecke_rows_pair_index({x["source"]: x for x in entries}, points, neg, add)
            assert canonical(index.rows) == canonical(static)
            assert basis.rank == produced["full_pool_rank_mod_q"]
            out.append({"p": p, "q": q, "status": "PASS", "rows": len(index.rows),
                        "full_rank": basis.rank, "first_rank39_source_count": first_goal})
            print(json.dumps(out[-1]), flush=True)
    assert len(out) == 10
    (HERE / "retrospective-validation.json").write_text(json.dumps({"status": "PASS", "cases": out}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
