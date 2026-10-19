"""Find degree falls from affine first-code multipliers of a two-pair resultant."""
import hashlib
import itertools
import json
import random
import resource
import signal
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


cfg = json.loads((HERE / "protocol.json").read_text())
assert cfg["status"] == "FROZEN_BEFORE_DEGREE_FALL_SCAN"
for name, source in cfg["sources"].items():
    assert sha(source["path"]) == source["sha256"], name


class Field:
    def __init__(self, n, reduction):
        self.n, self.reduction, self.mask = n, reduction, (1 << n) - 1

    def mul(self, a, b):
        out = 0
        while b:
            if b & 1:
                out ^= a
            b >>= 1
            a <<= 1
            if a >> self.n:
                a = (a & self.mask) ^ self.reduction
        return out

    def square(self, a):
        return self.mul(a, a)

    def frob(self, a, k):
        for _ in range(k):
            a = self.square(a)
        return a


def poly_add(left, right):
    result = left.copy()
    for mask, value in right.items():
        result[mask] = result.get(mask, 0) ^ value
        if not result[mask]:
            del result[mask]
    return result


def poly_mul(field, left, right):
    out = {}
    for a, av in left.items():
        for b, bv in right.items():
            mask = a | b
            out[mask] = out.get(mask, 0) ^ field.mul(av, bv)
    return {mask: value for mask, value in out.items() if value}


def poly_pow(field, poly, degree):
    out = {0: 1}
    for _ in range(degree):
        out = poly_mul(field, out, poly)
    return out


def product_basis(field, seed, positions, rotation):
    return [field.frob(field.square(1 << (i+1)) ^ field.mul(seed, 1 << (i+1)), rotation)
            for i in positions]


def read_n41_terms(index):
    lines = Path(cfg["sources"]["n41_coefficients"]["path"]).read_text().splitlines()
    assert lines[0] == "FREECODE 25 281 13"
    start = 1 + 281 + index * 14
    assert lines[start].startswith(f"T {index} ")
    terms = []
    for line in lines[start+1:start+14]:
        tag, row, a, b, value = line.split()
        assert tag == "C" and int(row) == index
        terms.append((int(a), int(b), int(value)))
    return terms


def read_n131_terms(index):
    return json.loads(Path(cfg["sources"]["n131_coefficients"]["path"]).read_text())["rows"][index]["terms"]


def rank_and_kernel(rows, column_masks, min_degree):
    columns = {mask: i for i, mask in enumerate(m for m in column_masks if m.bit_count() >= min_degree)}
    pivots = {}
    dependencies = []
    for index, poly in enumerate(rows):
        value = 0
        for mask in poly:
            if mask in columns:
                value ^= 1 << columns[mask]
        combo = 1 << index
        while value:
            bit = value.bit_length()-1
            if bit not in pivots:
                pivots[bit] = (value, combo)
                break
            basis, provenance = pivots[bit]
            value ^= basis
            combo ^= provenance
        if not value:
            dependencies.append(combo)
    return len(pivots), dependencies, len(columns)


def combine(rows, selection):
    out = set()
    while selection:
        lsb = selection & -selection
        out.symmetric_difference_update(rows[lsb.bit_length()-1])
        selection ^= lsb
    return out


started = time.monotonic()
signal.signal(signal.SIGALRM, lambda _signal, _frame: (_ for _ in ()).throw(TimeoutError("wall cap")))
signal.alarm(cfg["wall_cap_seconds"])
results = []
for spec in cfg["panels"]:
    n, k = spec["field_degree"], spec["first_free_bits"]
    field = Field(n, (1 << 3) | 1 if n == 41 else (1 << 13) | (1 << 2) | (1 << 1) | 1)
    seed = 112 if n == 41 else 898618 << 1
    positions = [0,1,2,3,4,6,7,8,9,10] if n == 41 else [i for i in range(33) if i != 898618 .bit_length()-1]
    rotations = (12,24) if n == 41 else (0,18)
    p_basis = product_basis(field, seed, positions, rotations[0])
    q_basis = product_basis(field, seed, positions, rotations[1])
    offset = spec["first_code_offset"]
    assert offset & ((1 << k)-1) == 0
    p = {0: 0}
    for bit in range(k, len(p_basis)):
        if offset >> bit & 1:
            p[0] ^= p_basis[bit]
    p.update({1 << bit: p_basis[bit] for bit in range(k)})
    q = {1 << (k+bit): value for bit, value in enumerate(q_basis)}
    pp = [poly_pow(field, p, degree) for degree in range(5)]
    qq = [poly_pow(field, q, degree) for degree in range(5)]
    terms = read_n41_terms(spec["target_index"]) if n == 41 else read_n131_terms(spec["target_index"])
    F = {}
    for a,b,coefficient in terms:
        term = poly_mul(field, pp[a], qq[b])
        term = {mask:field.mul(coefficient,value) for mask,value in term.items()}
        F = poly_add(F,term)
    assert F and max(mask.bit_count() for mask in F) == 4
    rng = random.Random(20261019 + n + spec["target_index"])
    positive_value = None
    for first,second in [(spec["positive_first_code"],spec["positive_second_code"])] + [
            (offset | rng.randrange(1 << k),rng.randrange(1 << len(q_basis))) for _ in range(128)]:
        assignment = (first & ((1 << k)-1)) | (second << k)
        anf = 0
        for mask,coefficient in F.items():
            if mask & assignment == mask:
                anf ^= coefficient
        pv = p.get(0,0)
        for bit in range(k):
            if first >> bit & 1:
                pv ^= p_basis[bit]
        qv = 0
        for bit in range(len(q_basis)):
            if second >> bit & 1:
                qv ^= q_basis[bit]
        direct = 0
        for a,b,coefficient in terms:
            pa, qb = 1,1
            for _ in range(a): pa = field.mul(pa,pv)
            for _ in range(b): qb = field.mul(qb,qv)
            direct ^= field.mul(coefficient,field.mul(pa,qb))
        assert anf == direct, (n,spec["target_index"],first,second)
        if first == spec["positive_first_code"] and second == spec["positive_second_code"]:
            positive_value = direct
    if spec["target_index"] == 0:
        assert positive_value == 0
    rows = []
    for multiplier in [-1] + list(range(k)):
        by_bit = [{} for _ in range(n)]
        for mask,value in F.items():
            newmask = mask if multiplier < 0 else mask | (1 << multiplier)
            while value:
                low = value & -value
                bit = low.bit_length()-1
                bucket = by_bit[bit]
                bucket[newmask] = bucket.get(newmask,0) ^ 1
                value ^= low
        rows.extend([{mask for mask,one in bucket.items() if one} for bucket in by_bit])
    all_masks = sorted(set(itertools.chain.from_iterable(rows)))
    ranks = {}
    for cutoff in (5,4,3):
        rank,dependencies,cols = rank_and_kernel(rows,all_masks,cutoff)
        witness = min(dependencies,key=int.bit_count) if dependencies else None
        witness_poly = combine(rows,witness) if witness is not None else None
        if witness_poly is not None:
            assert all(mask.bit_count() < cutoff for mask in witness_poly)
        ranks[str(cutoff)] = {"rank":rank,"nullity":len(dependencies),"columns":cols,
                              "shortest_dependency_rows":witness.bit_count() if witness is not None else None,
                              "shortest_dependency_degree":max(map(int.bit_count,witness_poly),default=-1) if witness_poly is not None else None}
    results.append({"field_degree":n,"target_index":spec["target_index"],
                    "first_free_bits":k,"first_code_offset":offset,
                    "equations":len(rows),"anf_monomials":len(F),
                    "degree_histogram":{str(d):sum(m.bit_count()==d for m in F) for d in range(5)},
                    "ranks":ranks,"direct_evaluation_checks":129})

out={"status":"COMPLETE_DEGREE_FALL_SCAN","candidate_id":None,
     "protocol_sha256":sha(HERE/"protocol.json"),"script_sha256":sha(__file__),
     "wall_seconds":time.monotonic()-started,"self_peak_rss_raw":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "panels":results}
assert out["wall_seconds"] < cfg["wall_cap_seconds"]
assert out["self_peak_rss_raw"] < cfg["rss_cap_bytes"]
(HERE/"result.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps({"status":out["status"],"wall_seconds":out["wall_seconds"],
                  "ranks":[(r["field_degree"],r["target_index"],r["ranks"]) for r in results]},sort_keys=True))
