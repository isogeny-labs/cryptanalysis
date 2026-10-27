"""Check the live five-source index against the sealed retrospective panel."""
import hashlib
import importlib.util
import json
from pathlib import Path

from live_index import FiveIndex

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OLD = ROOT / "experiments/hecke-d79-support-five-20261027"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(item, name):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"]
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def key(row):
    return (tuple(row["sources"]), tuple(row["coefficients"]),
            tuple(sorted((int(k), int(v)) for k, v in row["row"].items())))


def main():
    plan = json.loads((OLD / "inputs.json").read_text())
    old = json.loads((OLD / "result.json").read_text())
    assert old["status"] == "COMPLETE"
    selected = json.loads((ROOT / "experiments/hecke-d79-source-priority-20261027/selection.json").read_text())
    R = module(plan["relation_helpers"], "live_five_preflight_group")
    results = []
    for frozen, source_item, old_item in zip(selected["selected"], plan["cases"], old["cases"]):
        p = frozen["p"]
        assert p == source_item["p"] == old_item["p"]
        source_path = ROOT / source_item["path"]
        assert sha(source_path) == source_item["sha256"]
        source = json.loads(source_path.read_text())
        prior_path = OLD / old_item["path"]
        assert sha(prior_path) == old_item["sha256"]
        prior = json.loads(prior_path.read_text())
        neg, add = R.group_law(p)
        points = [tuple(point) for point in frozen["class"]["class_points"]]
        index = FiveIndex(points, neg, add, 200000, 120)
        generated = []
        for entry in source["entries"]:
            rows, metrics = index.append(entry)
            assert metrics["status"] == "COMPLETE"
            generated.extend(rows)
        assert sorted(map(key, generated)) == sorted(map(key, prior["rows"]))
        results.append({"p": p, "rows": len(generated), "status": "PASS"})
        print(json.dumps(results[-1]), flush=True)
    (HERE / "preflight.json").write_text(json.dumps({"schema": "hecke-d79-live-five-preflight-v1",
                                                    "status": "PASS", "cases": results},
                                                   sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
