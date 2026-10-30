"""Derive earliest rank-39 prefix from sealed full-pool relation supports."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "inputs.json").read_text())


def pinned(item):
    path = ROOT / item["path"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    return path


def main():
    selection = json.loads(pinned(PLAN["source_selection"]).read_text())
    result = json.loads((HERE / "result.json").read_text())
    assert selection["status"] == "CLASSES_FROZEN" and result["status"] == "COMPLETE"
    spec = importlib.util.spec_from_file_location("seven_prefix_rank", pinned(PLAN["incremental_module"]))
    I = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(I)
    cases = []
    for frozen, item, result_item in zip(selection["selected"], PLAN["cases"], result["cases"]):
        p, q = frozen["p"], frozen["q"]
        assert p == item["p"] == result_item["p"]
        journal = [json.loads(line) for line in pinned(item["journal"]).read_text().splitlines()]
        six = json.loads(pinned(item["six_case"]).read_text())["rows"]
        seven_path = HERE / result_item["path"]
        assert hashlib.sha256(seven_path.read_bytes()).hexdigest() == result_item["sha256"]
        seven = json.loads(seven_path.read_text())["rows"]
        baseline = [I.sparse(x["row"]) for x in frozen["class"]["base_rows"] + frozen["direct_candidates"]]
        basis = I.RankBasis(q, baseline)
        assert basis.rank == frozen["baseline_rank_mod_q"]
        six_by_source = [[] for _ in range(40)]
        seven_by_source = [[] for _ in range(40)]
        for row in six:
            six_by_source[max(row["sources"])].append(row)
        for row in seven:
            seven_by_source[max(row["sources"])].append(row)
        trajectory = []
        first_goal = None
        for k, record in enumerate(journal):
            increments = {}
            for name, rows in (("support_le4", record["four_rows"]),
                               ("support5", record["five_rows"]),
                               ("support6", six_by_source[k]),
                               ("support7", seven_by_source[k])):
                increments[name] = sum(bool(basis.insert(I.sparse(row["row"]))) for row in rows)
            trajectory.append({"source_count": k + 1, "rank_mod_q": basis.rank,
                               "novel_by_support": increments})
            if first_goal is None and basis.rank >= PLAN["rank_goal"]:
                first_goal = k + 1
        assert basis.rank == result_item["rank_with_seven"] == PLAN["rank_goal"]
        assert first_goal is not None
        cases.append({"p": p, "q": q, "baseline_rank": frozen["baseline_rank_mod_q"],
                      "first_rank_goal_source_count": first_goal,
                      "final_rank": basis.rank, "trajectory": trajectory})
        print(json.dumps({"p": p, "first_rank_goal_source_count": first_goal}), flush=True)
    (HERE / "prefix.json").write_text(json.dumps({"schema": "hecke-d79-support-seven-prefix-v1",
                                                 "status": "DERIVED", "candidate_id": None,
                                                 "target_online_ms": None, "cases": cases},
                                                sort_keys=True, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
