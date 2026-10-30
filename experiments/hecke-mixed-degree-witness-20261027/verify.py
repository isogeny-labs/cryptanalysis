"""Independent exact replay of the mixed-degree witness and all subset ranks."""
import hashlib
import itertools
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
HASHES = {entry["path"]: entry["sha256"] for entry in INPUTS["inputs"]}


def load(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == HASHES[path]
    return json.loads(data)


def row(entry):
    return {int(i): int(v) for i, v in entry.items() if v}


def key(entry):
    return tuple(sorted(row(entry).items()))


def rank(rows):
    pivots = {}
    for original in rows:
        values = {i: Fraction(v) for i, v in original.items() if v}
        while values:
            i = min(values)
            if i not in pivots:
                scale = values[i]
                pivots[i] = {j: v / scale for j, v in values.items()}
                break
            scale = values[i]
            for j, v in pivots[i].items():
                values[j] = values.get(j, 0) - scale * v
                if values[j] == 0:
                    del values[j]
    return len(pivots)


paths = [entry["path"] for entry in INPUTS["inputs"]]
old = load(paths[0])
corrected = load(paths[1])
boundary = load(paths[4])
result = json.loads((HERE / "result.json").read_text())
assert old["column_points"] == corrected["column_points"]
archived = list(map(row, old["relation_rows"]))
new = {(entry["degree"], entry["source"]): row(entry["row"]) for entry in result["new_rows"]}
assert Counter(map(key, new.values())) == (Counter(map(key, corrected["relation_rows"])) -
                                         Counter(map(key, archived)))
assert sorted(new) == [(2, 10), (2, 25), (7, 11)]
assert new[2, 25] == row(next(entry["target_row"] for entry in boundary["certificates"]
                          if entry["source"] == 25))
bit_order = [(item["degree"], item["source"]) for item in result["subset_bit_order"]]
assert bit_order == sorted(new)
for mask in range(8):
    chosen = [new[item] for i, item in enumerate(bit_order) if mask & (1 << i)]
    assert rank(archived + chosen) == result["subset_ranks_qq"][str(mask)]

dependency = result["dependency"]
total = defaultdict(int)
for item in dependency["archived_coefficients"]:
    for i, value in archived[item["row_index"]].items():
        total[i] += item["numerator"] * value
for i, value in new[7, 11].items():
    total[i] += dependency["degree7_numerator"] * value
for i, value in new[2, 25].items():
    total[i] -= dependency["denominator"] * value
assert not any(total.values())
assert dependency["archived_support_size"] == len(dependency["archived_coefficients"]) == 8
assert dependency["denominator"] == 3 and dependency["degree7_numerator"] == 1

assert len(result["commutator_probes"]) == 1
probe = result["commutator_probes"][0]
anchor, ell = probe["anchor"], probe["partner_degree"]
neighbors = {int(degree): Counter({int(i): int(v) for i, v in counts.items()})
             for degree, counts in probe["anchor_neighbors"].items()}
a = {int(degree): int(value) for degree, value in result["eigenvalues"].items()}
terms = Counter()
for point, multiplicity in neighbors[ell].items():
    terms[2, point] += multiplicity
terms[2, anchor] -= a[ell]
for point, multiplicity in neighbors[2].items():
    terms[ell, point] -= multiplicity
terms[ell, anchor] += a[2]
terms = {item: value for item, value in terms.items() if value}
saved = {(item["degree"], item["source"]): item for item in probe["terms"]}
assert {item: entry["coefficient"] for item, entry in saved.items()} == terms
assert terms[2, 25] == 3 and terms[7, 11] == -1
expanded = defaultdict(int)
for item, coefficient in terms.items():
    entry = saved[item]
    relation = archived[entry["archived_row_index"]] if entry["archived_row_index"] is not None else new[item]
    for i, value in relation.items():
        expanded[i] += coefficient * value
assert not any(expanded.values())
assert {(entry["degree"], entry["source"]) for entry in probe["missing_terms"]} == {(2, 25), (7, 11)}
print("MIXED_DEGREE_WITNESS_PASS", "base_rank", rank(archived),
      "subset_ranks", result["subset_ranks_qq"], "archived_support", 8)
