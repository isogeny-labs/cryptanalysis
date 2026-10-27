"""Produce exact mixed-degree span and local-commutator receipts."""
import hashlib
import importlib.util
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import QQ, classical_modular_polynomial, lcm, matrix, vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
HASHES = {entry["path"]: entry["sha256"] for entry in INPUTS["inputs"]}
ARCHIVE = "experiments/ecdlp-hecke-cross-discriminant-20261012/data/exp11_class_walk_D7_f14.json"
REPAIRED = "experiments/ecdlp-hecke-cross-discriminant-20261012/repeated_generic/data/exp11_class_walk_D7_f14.json"
HECKE = "experiments/ecdlp-hecke-floor-rank-20261012/tools/hecke11.py"
COLLECTOR = "experiments/hecke-multiplicity-collector-20261026/multiplicity.py"
BOUNDARY = "experiments/hecke-commutator-boundary-20261027/result_D7_f14.json"


def raw(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == HASHES[path]
    return data


def load(path):
    return json.loads(raw(path))


def module(path, name):
    raw(path)
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def row(entry):
    return {int(i): int(v) for i, v in entry.items() if v}


def key(entry):
    return tuple(sorted(row(entry).items()))


def rank(rows, width):
    return matrix(QQ, [[r.get(i, 0) for i in range(width)] for r in rows]).rank()


def main():
    old = load(ARCHIVE)
    repaired = load(REPAIRED)
    boundary = load(BOUNDARY)
    assert old["DK"] == repaired["DK"] == -7
    assert old["f"] == repaired["f"] == 14
    assert old["column_points"] == repaired["column_points"]
    archived = list(map(row, old["relation_rows"]))
    new_keys = Counter(map(key, repaired["relation_rows"])) - Counter(map(key, archived))
    assert sum(new_keys.values()) == 3
    H = module(HECKE, "_mixed_hecke11")
    C = module(COLLECTOR, "_mixed_collector")
    degrees = old["hecke_primes"]
    funcs, jfun = H.build(degrees)
    collector = C.MultiplicityReduced(int(old["p"]), funcs, jfun, degrees)
    points = []
    for encoded in old["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match is not None
        points.append(collector.E([int(match.group(1)), int(match.group(2)), 1]))
    index = {point: i for i, point in enumerate(points)}
    assert len(index) == len(points)
    modular = {ell: classical_modular_polynomial(ell) for ell in degrees}
    T, rows = {}, {}
    key_to_archived = {key(entry): i for i, entry in enumerate(archived)}
    recovered = {}
    for source, point in enumerate(points):
        for ell in degrees:
            status, neighbors = collector.recover(ell, point)
            if neighbors is None or not all(Q in index for Q in neighbors):
                continue
            jpoint = collector.j(point)
            assert jpoint is not None
            assert all(collector.j(Q) is not None and
                       modular[ell](jpoint, collector.j(Q)) == 0 for Q in neighbors)
            assert sum(neighbors, collector.E(0)) == collector.a_l[ell] * point
            counts = Counter(index[Q] for Q in neighbors)
            T[ell, source] = counts
            relation = Counter(counts)
            relation[source] -= collector.a_l[ell]
            relation = {i: int(value) for i, value in relation.items() if value}
            rows[ell, source] = relation
            if new_keys[key(relation)]:
                recovered[ell, source] = relation
    assert Counter(map(key, recovered.values())) == new_keys
    assert sorted(source for (ell, source) in recovered if ell == 2) == [10, 25]
    degree7 = [(source, relation) for (ell, source), relation in recovered.items() if ell == 7]
    assert len(degree7) == 1
    source7, row7 = degree7[0]
    target = recovered[2, 25]
    assert target == row(next(item["target_row"] for item in boundary["certificates"] if item["source"] == 25))
    width = len(points)
    base_rank = rank(archived, width)
    subset_ranks = {}
    new_items = sorted(recovered.items())
    for mask in range(1 << len(new_items)):
        chosen = [new_items[i][1] for i in range(len(new_items)) if mask & (1 << i)]
        subset_ranks[str(mask)] = rank(archived + chosen, width)
    assert base_rank == 17 and all(v in (17, 18) for v in subset_ranks.values())

    basis = archived + [row7]
    A = matrix(QQ, [[r.get(i, 0) for r in basis] for i in range(width)])
    coefficients = A.solve_right(vector(QQ, [target.get(i, 0) for i in range(width)]))
    assert len(coefficients) == len(basis)
    denominator = int(lcm([c.denominator() for c in coefficients]))
    numerators = [int(c * denominator) for c in coefficients]
    common = math.gcd(denominator, *(abs(n) for n in numerators))
    denominator //= common
    numerators = [n // common for n in numerators]
    assert denominator > 0 and numerators[-1] != 0
    assert all(sum(n * basis[j].get(i, 0) for j, n in enumerate(numerators)) ==
               denominator * target.get(i, 0) for i in range(width))

    commutator_probes = []
    for ell in sorted(x for x in degrees if x != 2):
        for anchor in range(width):
            if (2, anchor) not in T or (ell, anchor) not in T:
                continue
            terms = defaultdict(int)
            for point, multiplicity in T[ell, anchor].items():
                terms[2, point] += multiplicity
            terms[2, anchor] -= collector.a_l[ell]
            for point, multiplicity in T[2, anchor].items():
                terms[ell, point] -= multiplicity
            terms[ell, anchor] += collector.a_l[2]
            terms = {item: value for item, value in terms.items() if value}
            if not terms.get((2, 25), 0):
                continue
            total = Counter()
            for item, coefficient in terms.items():
                assert item in rows
                for i, value in rows[item].items():
                    total[i] += coefficient * value
            assert all(value == 0 for value in total.values())
            missing = [{"degree": degree, "source": source, "coefficient": value,
                        "is_new_degree7": (degree, source) == (7, source7)}
                       for (degree, source), value in sorted(terms.items())
                       if key(rows[degree, source]) not in key_to_archived]
            commutator_probes.append({"anchor": anchor, "partner_degree": ell,
                                      "anchor_neighbors": {"2": {str(i): v for i, v in sorted(T[2, anchor].items())},
                                                           str(ell): {str(i): v for i, v in sorted(T[ell, anchor].items())}},
                                      "missing_terms": missing,
                                      "terms": [{"degree": degree, "source": source,
                                                 "coefficient": value,
                                                 "archived_row_index": key_to_archived.get(key(rows[degree, source]))}
                                                for (degree, source), value in sorted(terms.items())]})
    output = {"schema": "hecke-mixed-degree-witness-v1", "DK": -7, "conductor": 14,
              "p": 347, "width": width, "archived_rank_qq": base_rank,
              "eigenvalues": {str(ell): int(collector.a_l[ell]) for ell in degrees},
              "new_rows": [{"degree": ell, "source": source,
                            "row": {str(i): value for i, value in sorted(relation.items())}}
                           for (ell, source), relation in new_items],
              "subset_bit_order": [{"degree": ell, "source": source} for (ell, source), _ in new_items],
              "subset_ranks_qq": subset_ranks,
              "target_degree2_source": 25, "degree7_source": source7,
              "dependency": {"denominator": denominator,
                             "archived_coefficients": [{"row_index": i, "numerator": n}
                                                       for i, n in enumerate(numerators[:-1]) if n],
                             "degree7_numerator": numerators[-1],
                             "archived_support_size": sum(n != 0 for n in numerators[:-1])},
              "commutator_probes": commutator_probes}
    (HERE / "result.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"degree7_source": source7,
                      "dependency": output["dependency"],
                      "commutator_probes": commutator_probes,
                      "subset_bit_order": output["subset_bit_order"],
                      "subset_ranks_qq": subset_ranks}, sort_keys=True))


if __name__ == "__main__":
    main()
