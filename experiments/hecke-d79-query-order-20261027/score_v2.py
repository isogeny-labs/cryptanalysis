"""Score frozen support-eight query orders from audited complete relation journals."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / "design-inputs.json").read_text())
SEAL = json.loads((HERE / "pre-design-v2.json").read_text())
NAMES = ("lex", "reverse_lex", "latest_min", "largest_sum")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned(item):
    path = ROOT / item["path"]
    assert sha(path) == item["sha256"], str(path)
    return path


def sparse(row):
    return {int(j): int(value) for j, value in row.items() if value}


def query_key(row):
    sources = tuple(row["sources"])
    signs = tuple(row["coefficients"])
    assert len(sources) == len(signs) == 8 and sources == tuple(sorted(sources))
    assert signs[0] == 1 and all(sign in (-1, 1) for sign in signs)
    latter_four = sources[3:7]
    sign_index = sum((sign == 1) << (4 - j) for j, sign in enumerate(signs[3:]))
    return latter_four, sign_index


def support_order(k, name):
    combos = list(itertools.combinations(range(k), 4))
    if name == "reverse_lex":
        combos.reverse()
    elif name == "latest_min":
        combos.sort(key=lambda ids: (-ids[0], ids))
    elif name == "largest_sum":
        combos.sort(key=lambda ids: (-sum(ids), ids))
    else:
        assert name == "lex"
    return {combo: position for position, combo in enumerate(combos)}


def main():
    assert sha(HERE / "DESIGN_PROTOCOL.md") == SEAL["protocol_sha256"]
    assert sha(HERE / "design-inputs.json") == SEAL["inputs_sha256"]
    assert sha(HERE / "score_v2.py") == SEAL["score_sha256"]
    assert sha(HERE / "DESIGN_AMENDMENT.md") == SEAL["amendment_sha256"]
    frozen = PLAN["frozen"]
    selection = json.loads(pinned(frozen["experiments/hecke-d79-live-eight-20261027/selection.json"]).read_text())
    index = json.loads(pinned(frozen["experiments/hecke-d79-live-eight-20261027/index.json"]).read_text())
    audit = json.loads(pinned(frozen["experiments/hecke-d79-live-eight-20261027/audit.json"]).read_text())
    assert audit["status"] == "PASS" and len(audit["cases"]) == 9
    path = pinned(frozen["experiments/hecke-d79-rank-stopped-collector-20261027/incremental.py"])
    spec = importlib.util.spec_from_file_location("query_order_rank", path)
    Rank = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(Rank)
    cases = []
    root = ROOT / "experiments/hecke-d79-live-eight-20261027"
    for p in PLAN["design_p"]:
        item = next(x for x in index["cases"] if x["p"] == p)
        frozen_class = next(x for x in selection["selected"] if x["p"] == p)
        audited = next(x for x in audit["cases"] if x["p"] == p)
        assert item["cohort"] == audited["cohort"] == "fresh"
        assert item["final_rank_eight_mod_q"] == audited["final_eight_rank"] == 39
        source_count = item["first_eight_source_count"]
        assert source_count == audited["first_eight_source_count"]
        journal = root / item["journal"]
        assert sha(journal) == item["journal_sha256"]
        records = [json.loads(line) for line in journal.read_text().splitlines()]
        assert len(records) >= source_count
        k = source_count - 1
        q = item["q"]
        baseline = [sparse(x["row"]) for x in frozen_class["class"]["base_rows"] + frozen_class["direct_candidates"]]
        before = Rank.RankBasis(q, baseline)
        assert before.rank == frozen_class["baseline_rank_mod_q"]
        for record in records[:source_count]:
            for family in ("four", "five", "six", "seven"):
                for relation in record["rows"][family]:
                    before.insert(sparse(relation["row"]))
            if record["source"] < k:
                for relation in record["rows"]["eight"]:
                    before.insert(sparse(relation["row"]))
        if before.rank == 39:
            result = {"p": p, "q": q, "first_rank39_source_count": source_count,
                      "rank_before_last_eight": before.rank, "last_source_eight_rows": 0,
                      "orders": {name: {"probe_position": 0, "matched_rows_checked": 0,
                                         "sources": None, "coefficients": None} for name in NAMES}}
            cases.append(result)
            print(json.dumps({"p": p, "positions": {name: 0 for name in NAMES},
                              "reason": "LOWER_SUPPORT_COMPLETES_RANK"}), flush=True)
            continue
        assert before.rank < 39
        last = records[k]["rows"]["eight"]
        assert last
        result = {"p": p, "q": q, "first_rank39_source_count": source_count,
                  "rank_before_last_eight": before.rank,
                  "last_source_eight_rows": len(last), "orders": {}}
        for name in NAMES:
            order = support_order(k, name)
            positioned = []
            for journal_order, relation in enumerate(last):
                latter, signs = query_key(relation)
                assert latter in order
                position = order[latter] * 32 + signs + 1
                positioned.append((position, journal_order, relation))
            positioned.sort(key=lambda x: (x[0], x[1]))
            basis = Rank.RankBasis(q, baseline)
            for j, pivot in before.pivots.items():
                basis.pivots[j] = dict(pivot)
            selected = None
            checked_rows = 0
            for position, _, relation in positioned:
                checked_rows += 1
                if basis.insert(sparse(relation["row"])) and basis.rank == 39:
                    selected = {"probe_position": position, "matched_rows_checked": checked_rows,
                                "sources": relation["sources"],
                                "coefficients": relation["coefficients"]}
                    break
            assert selected is not None
            result["orders"][name] = selected
        cases.append(result)
        print(json.dumps({"p": p, "positions": {name: result["orders"][name]["probe_position"]
                                             for name in NAMES}}), flush=True)
    totals = {name: sum(x["orders"][name]["probe_position"] for x in cases) for name in NAMES}
    worst = {name: max(x["orders"][name]["probe_position"] for x in cases) for name in NAMES}
    selected = min(NAMES, key=lambda name: (totals[name], worst[name], NAMES.index(name)))
    out = {"schema": "hecke-d79-query-order-design-v2", "status": "PASS",
           "policies": list(NAMES), "cases": cases, "aggregate_probe_positions": totals,
           "worst_probe_position": worst, "selected_policy": selected,
           "candidate_id": None, "target_online_ms": None}
    (HERE / "design-v2.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"selected_policy": selected, "aggregate_probe_positions": totals}), flush=True)


if __name__ == "__main__":
    main()
