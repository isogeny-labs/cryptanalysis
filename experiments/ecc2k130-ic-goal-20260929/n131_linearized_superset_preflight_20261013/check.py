#!/usr/bin/env python3
"""Independent GF(2^131) W18 source/resultant chart preflight."""

import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
GOAL = HERE.parent
protocol = json.loads((HERE / "protocol.json").read_text())
assert protocol["status"] == "FROZEN"
for path, digest in protocol["sources"].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
fixture = json.loads((GOAL / "n131_w18_allseed_fourpair_20261012/n131_control_fixture.json").read_text())
universal = json.loads((GOAL / "n131_w15_rotated_fouratom_inverse_20261010/resultant.json").read_text())
support_path = GOAL / "n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv"
columns = {int(mask): int(column) for mask, column in
           (line.split() for line in support_path.read_text().splitlines())}
N = 131
MOD = (1 << N) | (1 << 13) | (1 << 2) | (1 << 1) | 1


def mul(left, right):
    out = 0
    while right:
        if right & 1:
            out ^= left
        right >>= 1
        left <<= 1
        if left & (1 << N):
            left ^= MOD
    return out


def sq(value):
    return mul(value, value)


def frob(value, rotation):
    for _ in range(rotation):
        value = sq(value)
    return value


def coordinate(mask):
    return mask << 1


def pair_product(mask_pair, rotation):
    a, b = mask_pair
    return frob(mul(coordinate(a), coordinate(b)), rotation)


def pair_seed(mask_pair, rotation):
    a, b = mask_pair
    return frob(coordinate(a ^ b), rotation)


def pair_equation(seed, product, reciprocal):
    return mul(1 ^ sq(product), sq(reciprocal)) ^ \
        mul(product, reciprocal) ^ sq(seed)


def upper(left, right, target):
    lr = mul(left, right)
    return mul(1 ^ sq(lr), sq(target)) ^ mul(lr, target) ^ sq(left ^ right)


def powers(value):
    out = [1]
    for _ in range(8):
        out.append(mul(out[-1], value))
    return out


def fouratom(a, b, p, q, z):
    aa, bb, pp, qq, zz = map(powers, (a, b, p, q, z))
    out = 0
    for ea, eb, ep, eq, ez in universal["terms"]:
        term = mul(mul(aa[ea], bb[eb]), mul(pp[ep], qq[eq]))
        out ^= mul(term, zz[ez])
    return out


def rank(values):
    pivots = {}
    for value in values:
        while value:
            bit = value.bit_length()-1
            if bit in pivots:
                value ^= pivots[bit]
            else:
                pivots[bit] = value
                break
    return len(pivots)


assert fixture["status"] == "PASS_N131_DIAGONAL_ALLSEED_FOURPAIR_CONSTRUCTED_CHART"
assert fixture["curve_id"] == "EC1N131Ckb1heb5f1998f20b"
assert len(columns) == 131307
assert [columns[mask] for pair in fixture["masks"] for mask in pair] == fixture["columns"]
seeds = [a ^ b for a, b in fixture["masks"]]
assert seeds == [7,3,5,1]
usable_counts = []
full_ranks = []
for seed, masks in zip(seeds, fixture["masks"]):
    usable = sum(a < (a ^ seed) and (a ^ seed) in columns and
                 columns[a] != columns[a ^ seed] for a in columns)
    usable_counts.append(usable)
    assert all(mask in columns for mask in masks)
    assert columns[masks[0]] != columns[masks[1]]
    pivot = seed.bit_length()-1
    basis = [mul(coordinate(1 << bit), coordinate((1 << bit) ^ seed))
             for bit in range(18) if bit != pivot]
    full_ranks.append(rank(basis))
assert full_ranks == [17]*4
assert usable_counts == [32947,32916,32827,32842]
pair_seeds = [pair_seed(masks, rotation)
              for masks, rotation in zip(fixture["masks"], fixture["rotations"])]
pair_products = [pair_product(masks, rotation)
                 for masks, rotation in zip(fixture["masks"], fixture["rotations"])]
pair_values = [pair_equation(s, p, c) for s, p, c in
               zip(pair_seeds, pair_products, fixture["pair_reciprocals"])]
block_values = [fouratom(pair_seeds[i], pair_seeds[i+1],
                         pair_products[i], pair_products[i+1],
                         fixture["intermediate_reciprocals"][i//2])
                for i in (0,2)]
pair_upper_values = [upper(fixture["pair_reciprocals"][i],
                           fixture["pair_reciprocals"][i+1],
                           fixture["intermediate_reciprocals"][i//2])
                     for i in (0,2)]
target_upper_value = upper(*fixture["intermediate_reciprocals"],
                           fixture["target_reciprocal"])
assert pair_values == [0]*4, pair_values
assert block_values == [0,0], block_values
assert pair_upper_values == [0,0], pair_upper_values
assert target_upper_value == 0, target_upper_value
output = {
    "status": "PASS_N131_W18_CONSTRUCTED_SOURCE_RESULTANT_BRIDGE",
    "curve_id": fixture["curve_id"], "candidate_id": None,
    "target_kind": "constructed_correctness_control",
    "source_dimension": 18, "full_product_dimension": 17,
    "full_product_space_size": 1 << 17,
    "usable_pair_counts_by_slot": usable_counts,
    "seeds_by_slot": seeds, "rotations": fixture["rotations"],
    "pair_equation_values": pair_values,
    "fouratom_resultant_values": block_values,
    "pair_upper_values": pair_upper_values,
    "target_upper_value": target_upper_value,
    "source_sha256": {"protocol": hashlib.sha256((HERE / "protocol.json").read_bytes()).hexdigest(),
                      "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
}
with (HERE / "result.json").open("x") as stream:
    json.dump(output, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(output["status"], usable_counts)
