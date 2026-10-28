"""Replay row-level rank stopping on an audited frozen control journal."""
import hashlib
import importlib.util
import json
from math import comb
from pathlib import Path

from rank_stop_index import RankStopEightIndex

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


def canonical(rows):
    return sorted((tuple(x["sources"]), tuple(x["coefficients"]),
                   tuple(sorted((int(k), int(v)) for k, v in x["row"].items()))) for x in rows)


def main():
    post = json.loads((HERE / "post-selection.json").read_text())
    assert hashlib.sha256((HERE / "selection.json").read_bytes()).hexdigest() == post["selection_sha256"]
    old_index = json.loads(pinned(PLAN["preflight_support_eight_result"]).read_text())
    old_item = next(x for x in old_index["cases"] if x["p"] == PLAN["control_p"])
    first = old_item["first_eight_source_count"]
    assert first == 24 and old_item["source_count"] == 40
    old_records = [json.loads(x) for x in pinned(PLAN["preflight_support_eight_journal"]).read_text().splitlines()]
    old_selection = json.loads(pinned(PLAN["preflight_support_eight_selection"]).read_text())
    frozen = next(x for x in old_selection["selected"] if x["p"] == PLAN["control_p"])
    I = module(PLAN["incremental_module"], "row_stop_preflight_rank")
    R = module(PLAN["frozen"]["relation_helpers"], "row_stop_preflight_group")
    neg, add = R.group_law(PLAN["control_p"])
    baseline = [I.sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
    basis = I.RankBasis(frozen["q"], baseline)
    assert basis.rank == frozen["baseline_rank_mod_q"]
    index = RankStopEightIndex([tuple(x) for x in frozen["class"]["class_points"]], neg, add,
                               PLAN["support_eight_row_cap"], PLAN["support_eight_wall_cap_seconds"],
                               PLAN["support_eight_probe_cap"], basis, PLAN["rank_goal"])
    reached = None
    for k, record in enumerate(old_records[:first]):
        for family in ("four", "five", "six", "seven"):
            for relation in record["rows"][family]:
                basis.insert(I.sparse(relation["row"]))
        if basis.rank == PLAN["rank_goal"]:
            reached = k + 1
            break
        rows, metrics = index.append(record["entry"])
        assert set(canonical(rows)).issubset(set(canonical(record["rows"]["eight"])))
        if metrics["status"] == "RANK_GOAL_REACHED":
            reached = k + 1
            break
        assert metrics["status"] == "COMPLETE"
    assert reached == first and basis.rank == PLAN["rank_goal"]
    assert index.probes < 32 * comb(first, 5)
    out = {"schema": "hecke-d79-live-eight-row-stop-preflight-v1", "status": "PASS",
           "control_p": PLAN["control_p"], "first_eight_source_count": reached,
           "rows_through_stop": len(index.rows), "actual_probes": index.probes,
           "whole_prefix_probes": 32*comb(first, 5),
           "saved_within_prefix": 32*comb(first, 5)-index.probes}
    (HERE / "preflight.json").write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
