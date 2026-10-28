"""Replay the audited control prefix before new early-stop source lifts."""
import hashlib
import importlib.util
import json
from math import comb
from pathlib import Path

from eight_index import EightIndex

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
    assert first == 27 and old_item["source_count"] == 40
    old_records = [json.loads(x) for x in pinned(PLAN["preflight_support_eight_journal"]).read_text().splitlines()]
    old_selection = json.loads(pinned(PLAN["preflight_support_eight_selection"]).read_text())
    frozen = next(x for x in old_selection["selected"] if x["p"] == PLAN["control_p"])
    R = module(PLAN["frozen"]["relation_helpers"], "early_stop_preflight_group")
    neg, add = R.group_law(PLAN["control_p"])
    index = EightIndex([tuple(x) for x in frozen["class"]["class_points"]], neg, add,
                       PLAN["support_eight_row_cap"], PLAN["support_eight_wall_cap_seconds"],
                       PLAN["support_eight_probe_cap"])
    for record in old_records[:first]:
        rows, metrics = index.append(record["entry"])
        assert metrics["status"] == "COMPLETE"
        assert canonical(rows) == canonical(record["rows"]["eight"])
    assert index.probes == 32 * comb(first, 5)
    assert old_records[first - 2]["rank_eight_mod_q"] < 39
    assert old_records[first - 1]["rank_eight_mod_q"] == 39
    out = {"schema": "hecke-d79-live-eight-stop-preflight-v1", "status": "PASS",
           "control_p": PLAN["control_p"], "first_eight_source_count": first,
           "rows_through_stop": len(index.rows), "actual_probes": index.probes,
           "skipped_through_40": 32 * (comb(40, 5) - comb(first, 5))}
    (HERE / "preflight.json").write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
