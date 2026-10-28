"""Replay the known full-row control through both ordered rank-stop producers."""
import hashlib
import importlib.util
import json
from pathlib import Path

from ordered_index import OrderedRankStopEightIndex

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())

def pinned(item):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    return path

def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out

def main():
    I = module(PLAN["incremental_module"], "preflight_incremental")
    R = module(PLAN["frozen"]["relation_helpers"], "preflight_group")
    selection = json.loads(pinned(PLAN["preflight_support_eight_selection"]).read_text())
    frozen = next(x for x in selection["selected"] if x["p"] == PLAN["control_p"])
    records = [json.loads(line) for line in pinned(PLAN["preflight_support_eight_journal"]).read_text().splitlines()]
    design = json.loads(pinned(PLAN["design_result"]).read_text())
    expected = next(x for x in design["cases"] if x["p"] == PLAN["control_p"])
    points = [tuple(x) for x in frozen["class"]["class_points"]]
    neg, add = R.group_law(frozen["p"])
    baseline = [I.sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
    results = {}
    for policy in ("lex", "reverse_lex"):
        basis = I.RankBasis(frozen["q"], baseline)
        index = OrderedRankStopEightIndex(points, neg, add, PLAN["support_eight_row_cap"],
            PLAN["support_eight_wall_cap_seconds"], PLAN["support_eight_probe_cap"],
            basis, PLAN["rank_goal"], policy)
        first = final_metrics = final_rows = None
        for record in records:
            for name in ("four", "five", "six", "seven"):
                for row in record["rows"][name]:
                    basis.insert(I.sparse(row["row"]))
            if basis.rank >= PLAN["rank_goal"]:
                first = record["source"] + 1
                final_metrics = {"step_probes": 0, "status": "SKIPPED_LOWER_RANK_GOAL"}
                break
            rows, metrics = index.append(record["entry"])
            assert metrics["status"] in ("COMPLETE", "RANK_GOAL_REACHED")
            if metrics["status"] == "RANK_GOAL_REACHED":
                first, final_metrics, final_rows = record["source"] + 1, metrics, rows
                break
        want = expected["orders"][policy]
        assert first == expected["first_rank39_source_count"]
        assert final_metrics["step_probes"] == want["probe_position"]
        assert list(final_rows[-1]["sources"]) == want["sources"]
        assert list(final_rows[-1]["coefficients"]) == want["coefficients"]
        results[policy] = {"first_rank39_source_count": first,
            "step_probes": final_metrics["step_probes"], "total_probes": index.probes,
            "rank": basis.rank, "last_row": final_rows[-1]}
    output = {"status": "PASS", "p": frozen["p"], "results": results,
        "candidate_id": None, "target_online_ms": None}
    (HERE / "preflight.json").write_text(json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(output, sort_keys=True))

if __name__ == "__main__":
    main()
