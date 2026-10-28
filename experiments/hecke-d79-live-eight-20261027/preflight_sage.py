"""Replay the audited support-eight residual row through the new incremental index."""
import hashlib
import importlib.util
import json
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


def main():
    assert hashlib.sha256((HERE / "selection.json").read_bytes()).hexdigest() == json.loads((HERE / "post-selection.json").read_text())["selection_sha256"]
    old = json.loads(pinned(PLAN["preflight_support_eight_result"]).read_text())
    entries = [json.loads(line)["entry"] for line in pinned(PLAN["preflight_support_eight_journal"]).read_text().splitlines()]
    source = ROOT / "experiments/hecke-d79-live-seven-20261027"
    frozen = next(x for x in json.loads((source / "selection.json").read_text())["selected"] if x["p"] == 1825517)
    R = module(PLAN["frozen"]["relation_helpers"], "eight_preflight_group")
    neg, add = R.group_law(1825517)
    index = EightIndex([tuple(x) for x in frozen["class"]["class_points"]], neg, add,
                       PLAN["support_eight_row_cap"], PLAN["support_eight_wall_cap_seconds"],
                       PLAN["support_eight_probe_cap"])
    selected = old["selected_row"]
    found = False
    for entry in entries[:32]:
        rows, metrics = index.append(entry)
        assert metrics["status"] == "COMPLETE"
        if any(tuple(row["sources"]) == tuple(selected["sources"]) and
               tuple(row["coefficients"]) == tuple(selected["coefficients"]) and
               row["row"] == selected["row"] for row in rows):
            found = True
    assert found and old["rank_after"] == 39
    out = {"schema": "hecke-d79-live-eight-preflight-v1", "status": "PASS",
           "p": 1825517, "source_count": 32, "selected_row_replayed": True,
           "rows_through_prefix": len(index.rows), "quintuple_sign_probes": index.probes}
    (HERE / "preflight.json").write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps(out), flush=True)


if __name__ == "__main__":
    main()
