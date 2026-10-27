"""Test one-step commutator availability on two cross-discriminant records."""
import argparse
import hashlib
import importlib.util
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

from sage.all import QQ, classical_modular_polynomial, matrix


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = json.loads((HERE / "inputs.json").read_text())
CASES = {(case["DK"], case["f"]): case for case in INPUTS["cases"]}


def load(path):
    entry = next(item for item in INPUTS["inputs"] if item["path"] == str(path))
    full = ROOT / path
    assert hashlib.sha256(full.read_bytes()).hexdigest() == entry["sha256"]
    return json.loads(full.read_text())


def load_module(path, name):
    entry = next(item for item in INPUTS["inputs"] if item["path"] == str(path))
    full = ROOT / path
    assert hashlib.sha256(full.read_bytes()).hexdigest() == entry["sha256"]
    spec = importlib.util.spec_from_file_location(name, full)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_key(row):
    return tuple(sorted((int(i), int(v)) for i, v in row.items() if v))


def make_terms(T, a, anchor, ell):
    terms = defaultdict(int)
    for point, multiplicity in T[ell, anchor].items():
        terms[2, point] += multiplicity
    terms[2, anchor] -= a[ell]
    for point, multiplicity in T[2, anchor].items():
        terms[ell, point] -= multiplicity
    terms[ell, anchor] += a[2]
    return {key: value for key, value in terms.items() if value}


def row_sum(terms, rows):
    total = defaultdict(int)
    for key, coefficient in terms.items():
        for i, value in rows[key].items():
            total[i] += coefficient * value
    return {i: v for i, v in total.items() if v}


def verify_certificate(archived, target, coefficients, denominator):
    total = defaultdict(int)
    for item in coefficients:
        for i, value in archived[item["row_index"]].items():
            total[i] += item["numerator"] * value
    for i, value in target.items():
        total[i] -= denominator * value
    return all(value == 0 for value in total.values())


def rational_rank(rows, width):
    return matrix(QQ, [[row.get(i, 0) for i in range(width)] for row in rows]).rank()


def run(DK, f):
    case = CASES[DK, f]
    data = load(Path(case["archived"]))
    repaired = load(Path(case["corrected"]))
    assert data["DK"] == repaired["DK"] == DK
    assert data["f"] == repaired["f"] == f
    assert data["column_points"] == repaired["column_points"]
    H = load_module(Path("experiments/ecdlp-hecke-floor-rank-20261012/tools/hecke11.py"),
                    "_d7_commutator_hecke11")
    C = load_module(Path("experiments/hecke-multiplicity-collector-20261026/multiplicity.py"),
                    "_d7_commutator_collector")
    degrees = data["hecke_primes"]
    funcs, jfun = H.build(degrees)
    corrected = C.MultiplicityReduced(int(data["p"]), funcs, jfun, degrees)
    points = []
    for encoded in data["column_points"]:
        match = re.fullmatch(r"\((\d+) : (\d+) : 1\)", encoded)
        assert match is not None
        points.append(corrected.E([int(match.group(1)), int(match.group(2)), 1]))
    index = {point: i for i, point in enumerate(points)}
    assert len(index) == len(points)
    archived = [{int(i): int(v) for i, v in row.items()}
                for row in data["relation_rows"]]
    repaired_rows = [{int(i): int(v) for i, v in row.items()}
                     for row in repaired["relation_rows"]]
    new_keys = Counter(map(row_key, repaired_rows)) - Counter(map(row_key, archived))
    key_to_archived = {}
    for i, row in enumerate(archived):
        key_to_archived.setdefault(row_key(row), i)
    modular = {ell: classical_modular_polynomial(ell) for ell in degrees}
    T, rows, row_index = {}, {}, {}
    status = Counter()
    for source, P in enumerate(points):
        for ell in degrees:
            outcome, neighbors = corrected.recover(ell, P)
            status[outcome] += 1
            if neighbors is None or not all(Q in index for Q in neighbors):
                continue
            jP = corrected.j(P)
            assert jP is not None
            assert all(corrected.j(Q) is not None and
                       modular[ell](jP, corrected.j(Q)) == 0 for Q in neighbors)
            assert sum(neighbors, corrected.E(0)) == corrected.a_l[ell] * P
            counts = Counter(index[Q] for Q in neighbors)
            T[ell, source] = counts
            row = Counter(counts)
            row[source] -= corrected.a_l[ell]
            concrete = {int(i): int(v) for i, v in row.items() if v}
            rows[ell, source] = concrete
            row_index[ell, source] = key_to_archived.get(row_key(concrete))
    archived_retained = not (Counter(map(row_key, archived)) -
                             Counter(map(row_key, rows.values())))
    assert archived_retained
    recovered = {(ell, source): row for (ell, source), row in rows.items()
                 if new_keys[row_key(row)] and row_index[ell, source] is None}
    assert Counter(map(row_key, recovered.values())) == new_keys
    targets = {source: row for (ell, source), row in recovered.items() if ell == 2}
    assert len(targets) == 2
    certificates = []
    for target_source, target_row in sorted(targets.items()):
        probes = 0
        nonzero_coeff = 0
        available_terms = 0
        commutator_nonzero = 0
        certificate = None
        for ell in sorted(degree for degree in degrees if degree != 2):
            for anchor in range(len(points)):
                probes += 1
                if (2, anchor) not in T or (ell, anchor) not in T:
                    continue
                terms = make_terms(T, corrected.a_l, anchor, ell)
                coefficient = terms.get((2, target_source), 0)
                if not coefficient:
                    continue
                nonzero_coeff += 1
                if any(key not in rows for key in terms):
                    continue
                if any(key != (2, target_source) and row_index[key] is None
                       for key in terms):
                    continue
                available_terms += 1
                if row_sum(terms, rows):
                    commutator_nonzero += 1
                    continue
                denominator = abs(coefficient)
                sign = 1 if coefficient > 0 else -1
                numerators = Counter()
                for key, weight in terms.items():
                    if key == (2, target_source):
                        continue
                    numerators[row_index[key]] -= sign * weight
                numerators = {i: v for i, v in numerators.items() if v}
                common = math.gcd(denominator, *(abs(v) for v in numerators.values()))
                denominator //= common
                coefficients = [{"row_index": i, "numerator": v // common}
                                for i, v in sorted(numerators.items())]
                assert verify_certificate(archived, target_row, coefficients, denominator)
                certificate = {"status": "ONE_STEP_CERTIFICATE", "source": target_source,
                               "degree": 2, "anchor": anchor, "partner_degree": ell,
                               "target_row": {str(i): v for i, v in sorted(target_row.items())},
                               "denominator": denominator, "coefficients": coefficients,
                               "support_size": len(coefficients),
                               "anchor_neighbors": {
                                   "2": {str(i): v for i, v in sorted(T[2, anchor].items())},
                                   str(ell): {str(i): v for i, v in sorted(T[ell, anchor].items())}},
                               "commutator_terms": [
                                   {"degree": degree, "source": point,
                                    "coefficient": weight,
                                    "archived_row_index": row_index[degree, point]}
                                   for (degree, point), weight in sorted(terms.items())],
                               "commutator_integer_zero": True}
                break
            if certificate is not None:
                break
        if certificate is None:
            certificate = {"status": "NO_ONE_STEP", "source": target_source,
                           "degree": 2, "target_row": {str(i): v for i, v in sorted(target_row.items())}}
        certificate["search"] = {"probes": probes,
                                  "nonzero_target_coefficients": nonzero_coeff,
                                  "fully_available_terms": available_terms,
                                  "commutator_nonzero": commutator_nonzero}
        certificates.append(certificate)
    old_rank = rational_rank(archived, len(points))
    assert old_rank == data["rank"]
    individual_rank = {str(source): rational_rank(archived + [row], len(points))
                       for source, row in sorted(targets.items())}
    combined_rank = rational_rank(archived + list(targets.values()), len(points))
    output = {"DK": DK, "conductor": f, "p": int(data["p"]), "points": len(points),
              "degrees": degrees, "status": "ALL_ONE_STEP" if all(
                  item["status"] == "ONE_STEP_CERTIFICATE" for item in certificates)
                  else "PARTIAL_ONE_STEP", "collector_statuses": dict(status),
              "eigenvalues": {str(ell): corrected.a_l[ell] for ell in degrees},
              "complete_rows": len(rows), "archived_rows": len(archived),
              "corrected_rows": len(repaired_rows), "new_rows_by_degree": dict(Counter(ell for ell, _ in recovered)),
              "archived_rank_qq": old_rank, "individual_degree2_rank_qq": individual_rank,
              "joint_degree2_rank_qq": combined_rank,
              "archived_rows_retained": archived_retained,
              "certificates": certificates}
    (HERE / f"result_D{abs(DK)}_f{f}.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"DK": DK, "conductor": f, "status": output["status"],
                      "certificates": [{"source": item["source"], "status": item["status"],
                                        "anchor": item.get("anchor"),
                                        "degree": item.get("partner_degree"),
                                        "support": item.get("support_size"),
                                        "search": item["search"]} for item in certificates]},
                     sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--DK", type=int, required=True)
    parser.add_argument("--conductor", type=int, required=True)
    args = parser.parse_args()
    assert (args.DK, args.conductor) in CASES
    run(args.DK, args.conductor)
