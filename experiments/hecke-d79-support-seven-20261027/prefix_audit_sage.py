"""Check every derived prefix rank with Sage matrices."""
import hashlib
import json
from pathlib import Path

from sage.all import GF, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())


def pinned(item):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    return path


def sparse(raw):
    return {int(j): int(v) for j, v in raw.items() if v}


def rank(rows, q):
    F = GF(q)
    return int(matrix(F, len(rows), 40, lambda i, j: rows[i].get(j, 0)).rank())


def main():
    selection = json.loads(pinned(PLAN["source_selection"]).read_text())
    result = json.loads((HERE / "result.json").read_text())
    prefix = json.loads((HERE / "prefix.json").read_text())
    assert result["status"] == "COMPLETE" and prefix["status"] == "DERIVED"
    audited = []
    for frozen, item, result_item, claimed in zip(selection["selected"], PLAN["cases"], result["cases"], prefix["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert p == item["p"] == result_item["p"] == claimed["p"]
        journal = [json.loads(line) for line in pinned(item["journal"]).read_text().splitlines()]
        six = json.loads(pinned(item["six_case"]).read_text())["rows"]
        seven_path = HERE / result_item["path"]
        assert hashlib.sha256(seven_path.read_bytes()).hexdigest() == result_item["sha256"]
        seven = json.loads(seven_path.read_text())["rows"]
        rows = [sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
        first = None
        for k, step in enumerate(claimed["trajectory"]):
            rows += [sparse(x["row"]) for x in journal[k]["four_rows"] + journal[k]["five_rows"]]
            rows += [sparse(x["row"]) for x in six if max(x["sources"]) == k]
            rows += [sparse(x["row"]) for x in seven if max(x["sources"]) == k]
            current = rank(rows, q)
            assert step["source_count"] == k + 1 and step["rank_mod_q"] == current
            if first is None and current >= PLAN["rank_goal"]:
                first = k + 1
        assert first == claimed["first_rank_goal_source_count"]
        assert rank(rows, q) == claimed["final_rank"] == result_item["rank_with_seven"]
        audited.append({"p": p, "q": q, "first_rank_goal_source_count": first,
                        "prefix_ranks_checked": 40, "status": "PASS"})
        print(json.dumps(audited[-1]), flush=True)
    (HERE / "prefix-audit.json").write_text(json.dumps({"schema": "hecke-d79-support-seven-prefix-audit-v1",
                                                        "status": "PASS", "cases": audited},
                                                       sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
