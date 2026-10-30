"""Measure the class-part row-span upper bound on sealed D79 source traces."""
import hashlib
import importlib.util
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())


def sealed(path, expected):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected, str(path)
    return json.loads(raw)


def module(item):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    spec = importlib.util.spec_from_file_location("classpart_independent_pairs", path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def sparse(raw):
    return {int(k): int(v) for k, v in raw.items() if v}


def rank(rows, field):
    return int(matrix(field, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def main():
    pair_index = module(PLAN["pair_index"])
    results = []
    for family in PLAN["families"]:
        base = ROOT / family["dir"]
        selection = sealed(base / family["selection"], family["selection_sha256"])
        challenge = sealed(base / family["challenge"], family["challenge_sha256"])
        audit = sealed(base / "audit.json", family["audit_sha256"])
        assert challenge["status"] == "COMPLETE" and audit["status"] == "PASS"
        for frozen, produced, checked in zip(selection["selected"], challenge["cases"], audit["cases"]):
            p, q = frozen["p"], frozen["q"]
            assert produced["p"] == checked["p"] == p
            assert produced["q"] == checked["q"] == q
            assert produced["status"] == "COMPLETE"
            curve = EllipticCurve(GF(p), [0, -1, 1, -10, -20])
            points = [curve(x, y) for x, y in frozen["class"]["class_points"]]
            baseline = [sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
            entries = produced["source_entries"]
            assert len(entries) == 40 and [x["source"] for x in entries] == list(range(40))
            assert all(x["status"] == "OUTSIDE_CLASS_TRACE" for x in entries)
            source_rows = [sparse(x["class_part"]) for x in entries]
            hecke = pair_index.independent_rows(entries, points)
            assert len(hecke) == produced["hecke_candidate_count"]
            field = GF(q)
            base_rank = rank(baseline, field)
            source_rank = rank(baseline + source_rows, field)
            attained_rank = rank(baseline + [row for _, row in hecke], field)
            assert base_rank == checked["baseline_rank_mod_q"]
            assert attained_rank == checked["full_pool_rank_mod_q"]
            assert attained_rank <= source_rank
            prefix = []
            for count in range(41):
                seen = set(range(count))
                bound = rank(baseline + source_rows[:count], field)
                actual = rank(baseline + [row for support, row in hecke if set(support) <= seen], field)
                assert base_rank <= actual <= bound
                prefix.append({"source_count": count, "bound_rank_mod_q": bound,
                               "attained_rank_mod_q": actual})
            first_bound = next((x["source_count"] for x in prefix if x["bound_rank_mod_q"] >= PLAN["rank_goal"]), None)
            first_actual = next((x["source_count"] for x in prefix if x["attained_rank_mod_q"] >= PLAN["rank_goal"]), None)
            cell = {"family": family["name"], "p": p, "q": q, "status": "PASS",
                    "baseline_rank_mod_q": base_rank,
                    "classpart_span_rank_mod_q": source_rank,
                    "hecke_rank_mod_q": attained_rank,
                    "bound_gain": source_rank - base_rank,
                    "attained_gain": attained_rank - base_rank,
                    "gap": source_rank - attained_rank,
                    "first_bound_rank39_source_count": first_bound,
                    "first_attained_rank39_source_count": first_actual,
                    "verified_hecke_rows": len(hecke),
                    "prefix": prefix,
                    "candidate_id": None, "target_online_ms": None}
            results.append(cell)
            print(json.dumps({k: cell[k] for k in ("p", "baseline_rank_mod_q", "classpart_span_rank_mod_q", "hecke_rank_mod_q", "first_bound_rank39_source_count", "first_attained_rank39_source_count")}), flush=True)
    out = {"schema": "hecke-d79-classpart-span-bound-result-v1", "status": "PASS", "cases": results,
           "candidate_id": None, "target_online_ms": None}
    (HERE / "result.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
