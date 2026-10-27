"""Cancel repeated outside trace columns and measure class-only rank."""
import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
HASHES = {entry["path"]: entry["sha256"] for entry in INPUTS["inputs"]}
OLD, FIXED, PRIOR, _ = [entry["path"] for entry in INPUTS["inputs"]]


def load(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == HASHES[path]
    return json.loads(data)


def row(raw):
    return {int(i): int(v) for i, v in raw.items() if v}


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
            for j, value in pivots[i].items():
                values[j] = values.get(j, 0) - scale * value
                if values[j] == 0:
                    del values[j]
    return len(pivots)


old, fixed, prior = load(OLD), load(FIXED), load(PRIOR)
lift = json.loads((HERE / "lift-result.json").read_text())
assert old["column_points"] == fixed["column_points"]
assert lift["source"] == INPUTS["repeated_source"]


def expanded(source, orbits):
    relation = Counter()
    for orbit in orbits:
        multiplicity = orbit.get("multiplicity", 1)
        if orbit["trace_status"] == "IN_CLASS":
            relation[("C", orbit["trace_class_index"])] += multiplicity
        elif orbit["trace_status"] == "OUTSIDE_CLASS":
            relation[("O", *map(int, orbit["trace_coordinates"]))] += multiplicity
        else:
            assert orbit["trace_status"] == "IDENTITY"
    relation[("C", source)] -= prior["a_l"]
    return {key: value for key, value in relation.items() if value}


all_rows = {}
for item in prior["sources"]:
    if "orbits" in item:
        all_rows[item["source"]] = expanded(item["source"], item["orbits"])
if lift["status"] == "UNIQUE_LIFT":
    all_rows[lift["source"]] = expanded(lift["source"], lift["candidates"][0]["orbits"])


def class_part(relation):
    return {key[1]: value for key, value in relation.items() if key[0] == "C" and value}


def outside_part(relation):
    return {key: value for key, value in relation.items() if key[0] == "O" and value}


closed = []
groups = defaultdict(list)
excluded = []
for source, relation in sorted(all_rows.items()):
    outside = outside_part(relation)
    if not outside:
        saved = prior["sources"][source]
        if saved["status"] == "CLASS_CLOSED":
            assert class_part(relation) == row(saved["row"])
        closed.append({"source": source, "row": {str(i): v for i, v in sorted(class_part(relation).items())}})
    elif len(outside) == 1 and next(iter(outside.values())) == 1:
        groups[next(iter(outside))].append(source)
    else:
        excluded.append({"source": source, "outside": [[list(key), v] for key, v in outside.items()]})

pairs = []
for outside_point, sources in sorted(groups.items()):
    first = min(sources)
    for later in sorted(source for source in sources if source != first):
        difference = Counter(all_rows[later])
        for key, value in all_rows[first].items():
            difference[key] -= value
        difference = {key: value for key, value in difference.items() if value}
        assert not outside_part(difference)
        class_row = class_part(difference)
        pairs.append({"first_source": first, "later_source": later,
                      "outside_trace_point": list(outside_point[1:]),
                      "row": {str(i): v for i, v in sorted(class_row.items())}})

base_rows = list(map(row, fixed["relation_rows"]))
closed_rows = [row(item["row"]) for item in closed]
pair_rows = [row(item["row"]) for item in pairs]
rank_path = [rank(base_rows)]
for addition in closed_rows + pair_rows:
    rank_path.append(rank(base_rows + [row(item["row"]) for item in closed[:min(len(closed),len(rank_path)-1)]] +
                          pair_rows[:max(0,len(rank_path)-1-len(closed))] + [addition]))
output = {"schema": "hecke-orbit-cancellation-v1", "source_count": len(all_rows),
          "closed_rows": closed, "pair_rows": pairs,
          "excluded": excluded, "outside_groups": [
              {"point": list(point[1:]), "sources": sorted(sources)}
              for point, sources in sorted(groups.items())],
          "base_rank_qq": rank(base_rows),
          "rank_after_closed_qq": rank(base_rows + closed_rows),
          "rank_after_pairs_qq": rank(base_rows + closed_rows + pair_rows),
          "rank_path_qq": rank_path}
(HERE / "result.json").write_text(json.dumps(output, sort_keys=True, indent=2) + "\n")
print(json.dumps({"lift_status": lift["status"], "closed_sources": [item["source"] for item in closed],
                  "pair_sources": [(item["first_source"], item["later_source"]) for item in pairs],
                  "ranks": [output["base_rank_qq"], output["rank_after_closed_qq"],
                            output["rank_after_pairs_qq"]]}, sort_keys=True))
