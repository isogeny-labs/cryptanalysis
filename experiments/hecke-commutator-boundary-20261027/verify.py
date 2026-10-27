"""Independent integer-identity and rational-rank replay from frozen JSON."""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MANIFEST = json.loads((HERE / "inputs.json").read_text())
HASHES = {item["path"]: item["sha256"] for item in MANIFEST["inputs"]}


def load(path):
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HASHES[path]
    return json.loads(raw)


def row(raw):
    return {int(i): int(value) for i, value in raw.items() if value}


def key(raw):
    return tuple(sorted(row(raw).items()))


def rank(rows):
    pivots = {}
    for original in rows:
        current = {i: Fraction(value) for i, value in original.items() if value}
        while current:
            i = min(current)
            if i not in pivots:
                scale = current[i]
                pivots[i] = {j: value / scale for j, value in current.items()}
                break
            scale = current[i]
            for j, value in pivots[i].items():
                current[j] = current.get(j, 0) - scale * value
                if current[j] == 0:
                    del current[j]
    return len(pivots)


for case in MANIFEST["cases"]:
    old = load(case["archived"])
    repaired = load(case["corrected"])
    result = json.loads((HERE / f'result_D{abs(case["DK"])}_f{case["f"]}.json').read_text())
    assert old["column_points"] == repaired["column_points"]
    archived = list(map(row, old["relation_rows"]))
    corrected = list(map(row, repaired["relation_rows"]))
    new = Counter(map(key, corrected)) - Counter(map(key, archived))
    targets = {item["source"]: row(item["target_row"]) for item in result["certificates"]}
    assert len(targets) == 2
    assert all(new[key(target)] == 1 for target in targets.values())
    assert rank(archived) == result["archived_rank_qq"]
    assert {str(source): rank(archived + [target]) for source, target in targets.items()} == result["individual_degree2_rank_qq"]
    assert rank(archived + list(targets.values())) == result["joint_degree2_rank_qq"]
    for item in result["certificates"]:
        if item["status"] != "ONE_STEP_CERTIFICATE":
            continue
        target = row(item["target_row"])
        total = Counter()
        for coefficient in item["coefficients"]:
            for i, value in archived[coefficient["row_index"]].items():
                total[i] += coefficient["numerator"] * value
        for i, value in target.items():
            total[i] -= item["denominator"] * value
        assert all(value == 0 for value in total.values())
        terms = item["commutator_terms"]
        assert sum(term["coefficient"] for term in terms if term["degree"] == 2 and term["source"] == item["source"]) != 0
        assert all(term["archived_row_index"] is not None or
                   (term["degree"], term["source"]) == (2, item["source"])
                   for term in terms)
    print(case["DK"], case["f"], "rank", result["archived_rank_qq"],
          "individual", result["individual_degree2_rank_qq"],
          "joint", result["joint_degree2_rank_qq"], "certificates",
          sum(item["status"] == "ONE_STEP_CERTIFICATE" for item in result["certificates"]))
