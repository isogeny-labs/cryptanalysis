"""Compare incremental six/seven rows with sealed full-pool enumerations."""
import hashlib
import importlib.util
import json
from pathlib import Path

from wide_index import WideIndex

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(item):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"]
    return path


def module(item, name):
    spec = importlib.util.spec_from_file_location(name, pinned(item))
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


def canonical(rows):
    return sorted((tuple(row["sources"]), tuple(row["coefficients"]),
                   tuple(sorted((int(k), int(v)) for k, v in row["row"].items()))) for row in rows)


def main():
    selection = json.loads(pinned(PLAN["preflight_source_selection"]).read_text())
    six_index = json.loads(pinned(PLAN["preflight_six_result"]).read_text())
    seven_index = json.loads(pinned(PLAN["preflight_seven_result"]).read_text())
    six_root = ROOT / "experiments/hecke-d79-support-six-20261027"
    seven_root = ROOT / "experiments/hecke-d79-support-seven-20261027"
    live_root = ROOT / "experiments/hecke-d79-live-five-20261027"
    R = module(PLAN["frozen"]["relation_helpers"], "wide_preflight_group")
    audited = []
    for frozen, six_item, seven_item in zip(selection["selected"], six_index["cases"], seven_index["cases"]):
        p = frozen["p"]
        assert p == six_item["p"] == seven_item["p"]
        six_path = six_root / six_item["path"]
        seven_path = seven_root / seven_item["path"]
        assert sha(six_path) == six_item["sha256"]
        assert sha(seven_path) == seven_item["sha256"]
        six = json.loads(six_path.read_text())["rows"]
        seven = json.loads(seven_path.read_text())["rows"]
        old_index = json.loads((live_root / "index.json").read_text())
        old_item = next(x for x in old_index["cases"] if x["p"] == p)
        journal_path = live_root / old_item["journal"]
        assert sha(journal_path) == old_item["journal_sha256"]
        entries = [json.loads(line)["entry"] for line in journal_path.read_text().splitlines()]
        neg, add = R.group_law(p)
        points = [tuple(x) for x in frozen["class"]["class_points"]]
        index = WideIndex(points, neg, add, PLAN["wide_row_cap"], PLAN["wide_wall_cap_seconds"])
        for entry in entries:
            _, _, metrics = index.append(entry)
            assert metrics["status"] == "COMPLETE"
        assert canonical(index.six_rows) == canonical(six)
        assert canonical(index.seven_rows) == canonical(seven)
        audited.append({"p": p, "six_rows": len(six), "seven_rows": len(seven), "status": "PASS"})
        print(json.dumps(audited[-1]), flush=True)
    (HERE / "preflight.json").write_text(json.dumps({"schema": "hecke-d79-live-seven-preflight-v1",
                                                    "status": "PASS", "cases": audited},
                                                   sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
