"""Independently replay every N41 prefix-join hit and folded relation rank."""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, Zmod

HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
SOURCE = GOAL / "n131_w18_allseed_fourpair_20261012/n41_diagonal"
GEOMETRY = GOAL / "n41_w7_entropy_cubic_20261011/w8/geometry.json"
PAIR_TABLE = SOURCE / "pairs.tsv"
FIXTURE = SOURCE / "control_fixture.json"
R = 549756390943


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rank(matrix):
    pivots = {}
    for row in matrix:
        work = {int(k): int(v) % R for k, v in row.items() if int(v) % R}
        while work:
            pivot = min(work)
            if pivot not in pivots:
                scale = pow(work[pivot], -1, R)
                pivots[pivot] = {k: v * scale % R for k, v in work.items()}
                break
            factor = work[pivot]
            for k, v in pivots[pivot].items():
                work[k] = (work.get(k, 0) - factor * v) % R
                if not work[k]:
                    work.pop(k, None)
    return len(pivots)


protocol = json.loads((HERE / "audit_protocol.json").read_text())
for path, digest in protocol["sources"].items():
    assert sha(path) == digest, path
panel = json.loads((HERE / "panel.json").read_text())
cases = {row["label"]: row for row in panel["rows"]}
joins = json.loads((HERE / "join_summary.json").read_text())
geo = json.loads(GEOMETRY.read_text())
fixture = json.loads(FIXTURE.read_text())
rows = {int(row["mask"]): row for row in geo["rows"]}
ring = PolynomialRing(GF(2), "t")
t = ring.gen()
field = GF(2**41, name="t", modulus=t**41 + t**3 + 1)
curve = EllipticCurve(field, [1, 0, 0, 0, 1])


def dec(n):
    return field(ring([(int(n) >> i) & 1 for i in range(41)]))


def enc(v):
    return sum(int(bit) << i for i, bit in enumerate(v.polynomial().list()))


def xy(point):
    return [enc(point[0]), enc(point[1])]


def frob(point, power):
    return curve(point[0] ** (1 << power), point[1] ** (1 << power))


raw = {mask: curve(*map(dec, row["raw_point"])) for mask, row in rows.items()}
diagonal = {mask: raw[mask] + frob(raw[mask], 1) for mask in raw}
assert all(point != curve(0) and point[0] == 1 / dec(mask << 1)
           for mask, point in diagonal.items())
projected = {mask: 4 * point for mask, point in raw.items()}
assert all(point != curve(0) and R * point == curve(0) for point in projected.values())

target = {}
source = [[] for _ in range(4)]
for line in PAIR_TABLE.read_text().splitlines()[1:]:
    parts = line.split()
    if parts[0] == "T":
        target[int(parts[1])] = [int(parts[2]), int(parts[3])]
    elif parts[0] == "S":
        slot = int(parts[1])
        source[slot].append(list(map(int, parts[2:])))
assert all(len(slot) == 30952 for slot in source)
assert target[1] == fixture["raw_target"]
assert len(target) == 4

representative = {}
for mask, row in sorted(rows.items()):
    representative.setdefault(int(row["column"]), mask)
poly = PolynomialRing(Zmod(R), "L")
L = poly.gen()
roots = [int(value) for value, _ in (L**2 + L + 2).roots()]
sample = projected[representative[min(representative)]]
lambdas = [value for value in roots if value * sample == frob(sample, 1)]
assert len(lambdas) == 1
lam = lambdas[0]

prior = []
for name in ("n41_w8_sixpair_mitm_20261011", "n41_w8_ninepair_join_control_20261012",
             "n41_w8_tenpair_xquotient_20261012"):
    old = json.loads((GOAL / name / "audit_result.json").read_text())["relation_row"]
    if isinstance(old, list):
        prior.append({int(item["column"]): int(item["coefficient_mod_r"]) for item in old})
    else:
        prior.append({int(k): int(v) for k, v in old.items()})
old = json.loads((SOURCE / "audit_result.json").read_text())["relation_row"]
prior.append({int(k): int(v) for k, v in old.items()})
assert rank(prior) == 4

audited = []
for receipt in joins["receipts"]:
    if receipt["status"] != "HIT_PENDING_SAGE":
        continue
    case = cases[receipt["label"]]
    depth = case["depth"]
    prefixes = case["prefixes"]
    filtered = [[] for _ in range(4)]
    for slot in range(4):
        for item in source[slot]:
            sid, a, b, ca, cb, sa, sb, x, y = item
            pa, pb = a >> (8 - depth), b >> (8 - depth)
            if ((pa == prefixes[2 * slot] and pb == prefixes[2 * slot + 1]) or
                (pb == prefixes[2 * slot] and pa == prefixes[2 * slot + 1])):
                filtered[slot].append(item)
    words = receipt["hit"].split()
    assert words[:2] == ["HIT", "1"]
    ids = [int(word) for word in words[2:6]]
    assert all(0 <= sid < len(filtered[slot]) for slot, sid in enumerate(ids))
    selected = []
    occupied = set()
    running = curve(0)
    coefficient = defaultdict(int)
    for slot, sid in enumerate(ids):
        _, a, b, ca, cb, sa, sb, x, y = filtered[slot][sid]
        assert a < b and int(rows[a]["column"]) == ca and int(rows[b]["column"]) == cb
        assert ca not in occupied and cb not in occupied and ca != cb
        occupied.update([ca, cb])
        point = frob((-diagonal[a] if sa else diagonal[a]) +
                     (-diagonal[b] if sb else diagonal[b]), (0, 7, 14, 21)[slot])
        assert xy(point) == [x, y]
        running += point
        selected.append({"slot": slot, "state_id": filtered[slot][sid][0],
                         "masks": [a, b], "columns": [ca, cb],
                         "sign_bits": [sa, sb], "point": [x, y]})
        for mask, sign in ((a, sa), (b, sb)):
            col = int(rows[mask]["column"])
            base = projected[representative[col]]
            choices = []
            for k in range(41):
                q = frob(base, k)
                if q == projected[mask]:
                    choices.append((k, 1))
                if -q == projected[mask]:
                    choices.append((k, -1))
            assert len(choices) == 1
            k, orientation = choices[0]
            coefficient[col] = (coefficient[col] +
                                (-1 if sign else 1) * orientation * (1 + lam) *
                                pow(lam, (0, 7, 14, 21)[slot] + k, R)) % R
    assert len(occupied) == 8 and xy(running) == target[1]
    assert xy(4 * running) == fixture["public_target"]
    rowcheck = curve(0)
    for col, value in coefficient.items():
        rowcheck += value * projected[representative[col]]
    assert rowcheck == 4 * running
    old_rank = rank(prior)
    new_rank = rank(prior + [coefficient])
    prior.append(dict(coefficient))
    audited.append({"label": receipt["label"], "status": "PASS_INDEPENDENT_N41_PREFIX_RELATION",
                    "raw_target_preimage_index": 1,
                    "source_state_ids": ids, "pairs": selected,
                    "raw_sum": xy(running), "public_point": xy(4 * running),
                    "distinct_folded_columns": len(occupied),
                    "prior_rank": old_rank, "new_rank": new_rank,
                    "relation_row": {str(k): str(v) for k, v in coefficient.items()}})

result = {"status": "PASS_INDEPENDENT_SAGE_PREFIX_HITS",
          "curve_id": "EC1N41Ckb1h7d5e80d3c4d0", "candidate_id": None,
          "public_point": fixture["public_target"],
          "hit_count": len(audited), "relations": audited,
          "final_rank_with_prior_rows": rank(prior),
          "source_sha256": sha(__file__),
          "audit_protocol_sha256": sha(HERE / "audit_protocol.json")}
with (HERE / "sage_audit_result.json").open("x") as out:
    json.dump(result, out, sort_keys=True, indent=2)
    out.write("\n")
print(result["status"], len(audited), result["final_rank_with_prior_rows"])
