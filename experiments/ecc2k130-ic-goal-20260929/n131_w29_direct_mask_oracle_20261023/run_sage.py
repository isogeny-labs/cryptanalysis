"""Frozen N131 W29 direct-mask decoder and S3 root-cost control."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/"n41_n131_fivepair_w9_w29_20261017/n131_control.json"
SAMPLE = HERE.parent/"n41_n131_fivepair_w9_w29_20261017/sample_audit_result.json"
R = PolynomialRing(GF(2), "t")
tpoly = R.gen()
F = GF(2**131, name="t", modulus=tpoly**131+tpoly**13+tpoly**2+tpoly+1)
E = EllipticCurve(F, [1,0,0,0,1])
SEED_MASK = 898618
SEED = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dec(word):
    n = int(word)
    return F(R([(n >> i) & 1 for i in range(131)]))


def enc(value):
    return sum(int(c) << i for i,c in enumerate(value.polynomial().list()))


def halftrace(value):
    out = F.zero()
    current = value
    for _ in range(66):
        out += current
        current = current**4
    assert out**2+out == value
    return out


def source_valid(mask, seed):
    if mask <= 0 or mask >= (1 << 29) or mask & (1 << 19):
        return False
    a = dec(mask << 1)
    b = a+seed
    return bool(a and b and not a.trace() and not b.trace()
                and not (1/a).trace() and not (1/b).trace())


def pair_roots(mask, seed, H, C, rotation):
    a = dec(mask << 1)
    p = (a*(a+seed))**(1 << rotation)
    assert p
    rhs = C*H/p**2
    assert not rhs.trace()
    h = halftrace(rhs)
    scale = p/C
    roots = [scale*h, scale*(h+1)]
    assert roots[0] != roots[1] and all(z and C*z*z+p*z+H == 0 for z in roots)
    return roots


def s3_roots(a, target):
    A = 1+(a*target)**2
    B = a*target
    D = a*a+target*target
    assert A and B
    rhs = A*D/B**2
    if rhs.trace():
        return []
    h = halftrace(rhs)
    scale = B/A
    roots = [scale*h, scale*(h+1)]
    assert all(A*z*z+B*z+D == 0 for z in roots)
    return roots


def constants():
    seed = dec(SEED_MASK << 1)
    assert not seed.trace()
    half = halftrace(seed)
    H0 = half**2
    H1 = H0**(1 << 18)
    C0, C1 = 1+H0, 1+H1
    assert C0 and C1
    return seed,H0,C0,H1,C1


def freeze():
    data = json.loads(SOURCE.read_text())
    assert data["seed_mask"] == SEED_MASK
    seed,H0,C0,H1,C1 = constants()
    positive_left = data["pairs"][0]["masks"][0]
    positive_right = data["pairs"][1]["masks"][0]
    assert positive_left == 3 and positive_right == 18
    assert source_valid(positive_left,seed) and source_valid(positive_right,seed)
    left_roots = pair_roots(positive_left,seed,H0,C0,0)
    right_roots = pair_roots(positive_right,seed,H1,C1,18)
    assert dec(data["pairs"][0]["output_reciprocal"]) in left_roots
    assert dec(data["pairs"][1]["output_reciprocal"])**(1 << 18) in right_roots
    target = dec(data["middle_reciprocals"][0])
    a = dec(data["pairs"][0]["output_reciprocal"])
    b = dec(data["pairs"][1]["output_reciprocal"])**(1 << 18)
    assert b in s3_roots(a,target)
    masks = [positive_left]
    seen = {positive_left}
    state = 0x131C0DEC
    while len(masks) < 128:
        state = (state*6364136223846793005+1442695040888963407) & ((1<<64)-1)
        word = (state >> 16) & ((1<<28)-1)
        mask = (word & ((1<<19)-1)) | ((word >> 19) << 20)
        if mask not in seen and source_valid(mask,seed):
            seen.add(mask)
            masks.append(mask)
    protocol = {"status":"FROZEN", "candidate_id":None,
                "curve_id":data["curve_id"],
                "source_sha256":sha(SOURCE), "sample_audit_sha256":sha(SAMPLE),
                "script_sha256":sha(Path(__file__)),
                "runtime_info_sha256":sha(HERE/"sage_runtime_info.json"),
                "input_law":"128 fixed source-valid canonical left W29 masks, one constructed pair-sum target reciprocal",
                "left_masks":masks,"right_positive_mask":positive_right,
                "target_reciprocal":enc(target),
                "left_positive_reciprocal":enc(a),
                "right_positive_reciprocal":enc(b),
                "worker_count":1,"wall_cap_seconds":120,
                "rss_cap_bytes":4*1024**3}
    with (HERE/"protocol.json").open("x") as out:
        json.dump(protocol,out,sort_keys=True,indent=2)
        out.write("\n")
    print(json.dumps({"status":"FROZEN","left_masks":len(masks)}))


def run():
    protocol = json.loads((HERE/"protocol.json").read_text())
    assert sha(SOURCE) == protocol["source_sha256"]
    assert sha(SAMPLE) == protocol["sample_audit_sha256"]
    assert sha(Path(__file__)) == protocol["script_sha256"]
    assert sha(HERE/"sage_runtime_info.json") == protocol["runtime_info_sha256"]
    assert not (HERE/"result.json").exists()
    seed,H0,C0,H1,C1 = constants()
    setup = time.monotonic()
    basis = {}
    bits = [i for i in range(29) if i != 19]

    def forward(mask):
        a = dec(mask << 1)
        return (a*(a+seed))**(1 << 18)/C1

    for bit in bits:
        value = enc(forward(1 << bit))
        mask = 1 << bit
        for pivot in sorted(basis,reverse=True):
            if (value >> pivot)&1:
                value ^= basis[pivot][0]
                mask ^= basis[pivot][1]
        assert value
        basis[value.bit_length()-1] = (value,mask)
    assert len(basis)==28

    def inverse(word):
        value = word
        mask = 0
        for pivot in sorted(basis,reverse=True):
            if (value >> pivot)&1:
                value ^= basis[pivot][0]
                mask ^= basis[pivot][1]
        return mask if value==0 else None

    for mask in protocol["left_masks"]+[protocol["right_positive_mask"]]:
        assert inverse(enc(forward(mask))) == mask
    prep_seconds = time.monotonic()-setup
    target=dec(protocol["target_reciprocal"])
    positive_a=dec(protocol["left_positive_reciprocal"])
    positive_b=dec(protocol["right_positive_reciprocal"])
    assert positive_a in pair_roots(protocol["left_masks"][0],seed,H0,C0,0)
    assert positive_b in pair_roots(protocol["right_positive_mask"],seed,H1,C1,18)
    rows=[]
    start=time.monotonic()
    total_s3=0
    valid_candidate_count=0
    for mask in protocol["left_masks"]:
        roots=pair_roots(mask,seed,H0,C0,0)
        for a in roots:
            tick=time.monotonic_ns()
            bs=s3_roots(a,target)
            decoded=[]
            for b in bs:
                if not b:
                    continue
                k=enc(b+(H1/C1)/b)
                candidate=inverse(k)
                if candidate is not None and source_valid(candidate,seed):
                    decoded.append({"mask":candidate,"root":enc(b)})
            valid_candidate_count += len(decoded)
            total_s3 += 1
            rows.append({"left_mask":mask,"left_root":enc(a),
                         "field_root_count":len(bs),
                         "valid_source_candidates":decoded,
                         "query_ns":time.monotonic_ns()-tick})
    elapsed=time.monotonic()-start
    assert total_s3==256
    positive=[row for row in rows if row["left_mask"]==protocol["left_masks"][0]
              and row["left_root"]==enc(positive_a)]
    assert len(positive)==1
    assert {"mask":protocol["right_positive_mask"],"root":enc(positive_b)} in positive[0]["valid_source_candidates"]
    result={"status":"PASS_N131_W29_DIRECT_MASK_ORACLE_COMPONENT",
            "candidate_id":None,"protocol_sha256":sha(HERE/"protocol.json"),
            "source_product_rank":len(basis),
            "left_valid_codes":len(protocol["left_masks"]),
            "s3_root_calls":total_s3,"valid_source_candidates":valid_candidate_count,
            "setup_seconds":prep_seconds,"query_seconds":elapsed,
            "query_ns_min_median_p90_max":[min(r["query_ns"] for r in rows),
                 sorted(r["query_ns"] for r in rows)[len(rows)//2],
                 sorted(r["query_ns"] for r in rows)[(9*len(rows))//10],
                 max(r["query_ns"] for r in rows)],
            "self_maxrss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "positive_left_mask":protocol["left_masks"][0],
            "positive_right_mask":protocol["right_positive_mask"],
            "rows":rows}
    with (HERE/"result.json").open("x") as out:
        json.dump(result,out,sort_keys=True,indent=2)
        out.write("\n")
    print(json.dumps({k:result[k] for k in ("status","source_product_rank","s3_root_calls","valid_source_candidates","query_seconds")}))


if __name__=="__main__":
    {"freeze":freeze,"run":run}[sys.argv[1]]()
