"""Independently replay linked Frobenius-pair N41 public relation and row."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, Zmod


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "n41_w7_entropy_cubic_20261011/w8"
INPUT = HERE / "adjacent_input.tsv"
R = 549756390943
ROTATIONS = (0, 1, 14, 21, 28, 35)
SLOTS = (0, 1, 2, 3, 4, 5, 0, 1, 2, 3)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


audit_protocol = json.loads((HERE / "audit_protocol.json").read_text())
for name, path in {
    "audit_source": HERE / "audit_sage.py",
    "native_receipt": HERE / "receipt.json",
    "stdout": HERE / "stdout.log",
    "input": INPUT,
    "geometry": BASE / "geometry.json",
    "fixture": BASE / "fixture.json",
    "sage_runtime": HERE / "sage_runtime_info.json",
}.items():
    assert sha(path) == audit_protocol["sha256"][name]
receipt = json.loads((HERE / "receipt.json").read_text())
assert receipt["status"] == "HIT_PENDING_INDEPENDENT_REPLAY"
assert receipt["worker_count"] == 1 and receipt["stop_reason"] is None
assert receipt["peak_combined_rss_bytes_sampled"] < 4 * 1024**3
assert receipt["runner_wall_ns"] < 180 * 10**9

geometry = json.loads((BASE / "geometry.json").read_text())
fixture = json.loads((BASE / "fixture.json").read_text())
rows = {int(row["mask"]): row for row in geometry["rows"]}
edges = [(a, a ^ 184) for a in sorted(rows)
         if a < (a ^ 184) and a ^ 184 in rows
         and rows[a]["column"] != rows[a ^ 184]["column"]]
assert len(edges) == 35

ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def dec(value):
    return field(ring([(int(value) >> i) & 1 for i in range(41)]))


def enc(value):
    return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))


def xy(point):
    return [enc(point[0]), enc(point[1])]


def frobenius(point, exponent):
    return curve(point[0]**(1 << exponent), point[1]**(1 << exponent))


raw = {mask: curve(*map(dec, row["raw_point"])) for mask, row in rows.items()}
projected = {mask: 4 * point for mask, point in raw.items()}
assert all(point != curve(0) and R * point == curve(0) for point in projected.values())
input_states, input_targets = {}, {}
for line in INPUT.read_text().splitlines()[1:]:
    parts = line.split()
    if parts[0] == "T":
        input_targets[int(parts[1])] = [int(parts[2]), int(parts[3])]
    if parts[0] == "S":
        input_states[(int(parts[1]), int(parts[2]))] = [int(parts[-2]), int(parts[-1])]
assert len(input_states) == 840 and len(input_targets) == 4
assert [input_targets[i] for i in range(4)] == fixture["raw_target_preimages"]

# Exact adjacent-Frobenius map on every frozen signed source state.
for sid in range(140):
    point = curve(*map(dec, input_states[(0, sid)]))
    x = point[0]
    assert x not in (0, 1)
    near = frobenius(point, 1)
    plus = point + near
    minus = point - near
    f = x + 1/x
    assert plus != curve(0) and minus != curve(0)
    assert plus[0] == f and minus[0] == f + 1/f

hit_lines = [line.split() for line in (HERE / "stdout.log").read_text().splitlines()
             if line.startswith("HIT ")]
assert len(hit_lines) == 1
hit = hit_lines[0]
assert len(hit) == 22
target_index = int(hit[1])
state_ids = list(map(int, hit[2:12]))
assert 0 <= target_index < 4 and len(state_ids) == 10
assert int(hit[12]) == 5000000

representatives = {}
for mask, row in sorted(rows.items()):
    representatives.setdefault(int(row["column"]), mask)
ring_r = PolynomialRing(Zmod(R), "L")
L = ring_r.gen()
roots = [int(root) for root, _ in (L**2 + L + 2).roots()]
sample = projected[representatives[min(representatives)]]
eigenvalues = [value for value in roots if value * sample == frobenius(sample, 1)]
assert len(eigenvalues) == 1
eigenvalue = eigenvalues[0]

assert state_ids[0] == state_ids[1]
selected_masks = {mask for sid in state_ids for mask in edges[sid // 4]}
assert len(selected_masks) == 18
quotient = {}
for mask in selected_masks:
    column = int(rows[mask]["column"])
    rep = projected[representatives[column]]
    matches = []
    for exponent in range(41):
        image = frobenius(rep, exponent)
        if image == projected[mask]:
            matches.append((exponent, 1))
        if -image == projected[mask]:
            matches.append((exponent, -1))
    assert len(matches) == 1
    quotient[mask] = matches[0]

running = curve(0)
occupied_edges = set()
terms, sources = [], []
coefficients = defaultdict(int)
for position, (slot, sid) in enumerate(zip(SLOTS, state_ids)):
    assert 0 <= sid < 140
    edge_id, choice = divmod(sid, 4)
    if edge_id in occupied_edges:
        assert position == 1 and edge_id == state_ids[0] // 4
    else:
        occupied_edges.add(edge_id)
    a, b = edges[edge_id]
    sign_a, sign_b = divmod(choice, 2)
    first = -raw[a] if sign_a else raw[a]
    second = -raw[b] if sign_b else raw[b]
    rotation = ROTATIONS[slot]
    pair = frobenius(first + second, rotation)
    assert xy(pair) == input_states[(slot, sid)]
    running += pair
    sources.append({"position": position, "slot": slot, "state_id": sid,
                    "edge_id": edge_id, "masks": [a, b],
                    "sign_bits": [sign_a, sign_b], "rotation": rotation,
                    "pair_point": xy(pair)})
    for mask, sign_bit in ((a, sign_a), (b, sign_b)):
        column = int(rows[mask]["column"])
        exponent, orbit_sign = quotient[mask]
        coefficient = ((-1 if sign_bit else 1) * orbit_sign *
                       pow(eigenvalue, rotation + exponent, R)) % R
        coefficients[column] = (coefficients[column] + coefficient) % R
        terms.append({"position": position, "mask": mask, "column": column,
                      "coefficient_mod_r": str(coefficient)})
assert len(occupied_edges) == 9 and len(terms) == 20
assert sources[1]["pair_point"] == xy(frobenius(
    curve(*map(dec, sources[0]["pair_point"])), 1))
assert xy(running) == input_targets[target_index]
assert xy(4 * running) == fixture["public_target_transported"]
row_sum = curve(0)
for column, coefficient in coefficients.items():
    row_sum += coefficient * projected[representatives[column]]
assert row_sum == 4 * running
nonzero = {column: str(value) for column, value in coefficients.items() if value}
six = json.loads((ROOT / "n41_w8_sixpair_mitm_20261011/audit_result.json").read_text())
nine = json.loads((ROOT / "n41_w8_ninepair_join_control_20261012/audit_result.json").read_text())
ten = json.loads((ROOT / "n41_w8_tenpair_xquotient_20261012/audit_result.json").read_text())
assert six["public_target_transported"] == nine["public_target_transported"] == xy(4 * running)
assert ten["public_target_transported"] == xy(4 * running)
prior_columns = {int(term["column"]) for term in six["relation_row"]}
prior_columns |= {int(column) for column in nine["relation_row"]}
prior_columns |= {int(column) for column in ten["relation_row"]}
new_columns = set(nonzero) - prior_columns
assert nonzero


def row_dict(row):
    if isinstance(row, dict):
        return {int(k): int(v) % R for k, v in row.items() if int(v) % R}
    result = defaultdict(int)
    for term in row:
        k = int(term["column"])
        result[k] = (result[k] + int(term["coefficient_mod_r"])) % R
    return {k: v for k, v in result.items() if v}


def rank(vectors):
    pivots = {}
    for row in vectors:
        work = dict(row)
        while work:
            lead = min(work)
            if lead not in pivots:
                factor = pow(work[lead], -1, R)
                pivots[lead] = {k: v * factor % R for k, v in work.items()}
                break
            factor = work[lead]
            for k, v in pivots[lead].items():
                residue = (work.get(k, 0) - factor * v) % R
                if residue:
                    work[k] = residue
                else:
                    work.pop(k, None)
    return len(pivots)


prior_rows = [row_dict(six["relation_row"]), row_dict(nine["relation_row"]),
              row_dict(ten["relation_row"])]
rank_before = rank(prior_rows)
rank_after = rank(prior_rows + [row_dict(nonzero)])
linked_factor = (1 + pow(eigenvalue, 1, R)) % R
assert linked_factor
for mask in edges[state_ids[0] // 4]:
    column = int(rows[mask]["column"])
    linked_terms = [int(term["coefficient_mod_r"]) for term in terms[:4]
                    if term["mask"] == mask]
    assert len(linked_terms) == 2
    assert sum(linked_terms) % R == linked_terms[0] * linked_factor % R
result = {
    "status": "PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION",
    "candidate_id": None,
    "curve_id": "EC1N41Ckb1h7d5e80d3c4d0",
    "target_count": 1,
    "raw_target_preimage_index": target_index,
    "raw_target_replayed": xy(running),
    "public_target_transported": xy(4 * running),
    "source_pairs_free": 9,
    "source_edges_distinct": len(occupied_edges),
    "linked_frobenius_exponent": 1,
    "linked_factor_mod_r": str(linked_factor),
    "term_count": len(terms),
    "folded_columns_nonzero": len(nonzero),
    "new_columns_vs_prior_six_nine_ten": len(new_columns),
    "rank_before_with_prior_six_nine_ten": rank_before,
    "rank_after_with_linked_row": rank_after,
    "relation_row": nonzero,
    "source_pairs": sources,
    "source_terms": terms,
    "sha256": {"audit_source": sha(HERE / "audit_sage.py"),
               "input": sha(INPUT), "geometry": sha(BASE / "geometry.json"),
               "fixture": sha(BASE / "fixture.json"),
               "stdout": sha(HERE / "stdout.log"),
               "sage_runtime": sha(HERE / "sage_runtime_info.json")},
}
(HERE / "audit_result.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
print(result["status"], len(nonzero), len(new_columns))
