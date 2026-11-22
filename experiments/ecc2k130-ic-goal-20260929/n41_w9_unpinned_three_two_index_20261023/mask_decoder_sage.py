"""Direct inverse source-product map: reciprocal root -> canonical mask."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from oracle_sage import HERE, INPUT, F, dec, enc, load, point, s3_roots


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(states):
    seed_mask = 56
    seed = dec(seed_mask << 1)
    trace_half = sum((seed**(1 << (2*j)) for j in range(21)), F.zero())
    assert trace_half**2 + trace_half == seed
    H = (trace_half**2)**(1 << 6)
    C = 1+H
    assert C
    h = H/C
    bits = [i for i in range(9) if i != 5]

    def forward(mask):
        a = dec(mask << 1)
        return (a*(a+seed))**(1 << 6)/C

    basis = {}
    for bit in bits:
        value = enc(forward(1 << bit))
        mask = 1 << bit
        for pivot in sorted(basis, reverse=True):
            if (value >> pivot) & 1:
                value ^= basis[pivot][0]
                mask ^= basis[pivot][1]
        assert value
        basis[value.bit_length()-1] = (value, mask)
    assert len(basis) == 8

    def inverse(word):
        value = word
        mask = 0
        for pivot in sorted(basis, reverse=True):
            if (value >> pivot) & 1:
                value ^= basis[pivot][0]
                mask ^= basis[pivot][1]
        return mask if value == 0 else None

    for mask in range(512):
        if mask & seed_mask & 32:
            continue
        assert inverse(enc(forward(mask))) == mask

    raw = INPUT.read_text().splitlines()
    mask_to_code = {}
    for line in raw[1:]:
        f = line.split()
        if f[0] == "S" and int(f[1]) == 1 and int(f[2]) % 4 == 0:
            code = int(f[2])//4
            mask = int(f[3])
            assert mask not in mask_to_code
            mask_to_code[mask] = code
    assert len(mask_to_code) == 71
    for mask, code in mask_to_code.items():
        a = dec(mask << 1)
        assert not a.trace() and not (1/a).trace()
        partner = a+seed
        assert not partner.trace() and not (1/partner).trace()
        for sid in range(4*code, 4*code+4):
            b = 1/states[1][sid][0]
            assert C*b*b + (forward(mask)*C)*b + H == 0
            assert b+h/b == forward(mask)
            assert inverse(enc(b+h/b)) == mask

    def decode_root(b):
        if not b:
            return None
        mask = inverse(enc(b+h/b))
        if mask is None or mask not in mask_to_code:
            return None
        return mask_to_code[mask]

    return h, basis, mask_to_code, decode_root


def freeze():
    batch = json.loads((HERE/"batch_protocol.json").read_text())
    protocol = {"status": "FROZEN", "candidate_id": None,
                "curve_id": batch["curve_id"],
                "query_count": batch["key_count"],
                "batch_protocol_sha256": sha(HERE/"batch_protocol.json"),
                "input_sha256": sha(INPUT),
                "oracle_script_sha256": sha(HERE/"oracle_sage.py"),
                "mask_decoder_script_sha256": sha(Path(__file__)),
                "runtime_info_sha256": sha(HERE/"sage_runtime_info.json"),
                "worker_count": 1, "wall_cap_seconds": 120,
                "rss_cap_bytes": 4*1024**3}
    with (HERE/"mask_decoder_protocol.json").open("x") as out:
        json.dump(protocol, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({"status": "FROZEN", "query_count": batch["key_count"]}))


def run():
    p = json.loads((HERE/"mask_decoder_protocol.json").read_text())
    for name, path in (("batch_protocol_sha256", HERE/"batch_protocol.json"),
                       ("input_sha256", INPUT),
                       ("oracle_script_sha256", HERE/"oracle_sage.py"),
                       ("mask_decoder_script_sha256", Path(__file__)),
                       ("runtime_info_sha256", HERE/"sage_runtime_info.json")):
        assert p[name] == sha(path)
    assert not (HERE/"mask_decoder_result.json").exists()
    batch = json.loads((HERE/"batch_protocol.json").read_text())
    _, states, cols = load()
    setup_start = time.monotonic()
    h, basis, valid, decoder = build(states)
    left = {}
    for sid, P in enumerate(states[0]):
        left.setdefault(enc(1/P[0]), []).append(sid)
    setup_seconds = time.monotonic()-setup_start
    rows = []
    start = time.monotonic()
    valid_roots = 0
    for item in batch["keys"]:
        key = point(item["key"])
        t = 1/key[0]
        tick = time.monotonic_ns()
        hits = set()
        for aword, a_ids in left.items():
            roots = s3_roots(dec(aword), t)
            assert roots is not None
            for b in roots:
                code = decoder(b)
                if code is None:
                    continue
                valid_roots += 1
                for bid in range(4*code, 4*code+4):
                    if 1/states[1][bid][0] == b:
                        for aid in a_ids:
                            if cols[0][aid].isdisjoint(cols[1][bid]) and states[0][aid]+states[1][bid] == key:
                                hits.add((aid,bid))
        rows.append({"suffix_ids": item["suffix_ids"],
                     "matches": [list(v) for v in sorted(hits)],
                     "query_ns": time.monotonic_ns()-tick})
    elapsed = time.monotonic()-start
    times = sorted(row["query_ns"] for row in rows)
    result = {"status": "PASS_DIRECT_MASK_DECODER", "candidate_id": None,
              "protocol_sha256": sha(HERE/"mask_decoder_protocol.json"),
              "batch_protocol_sha256": sha(HERE/"batch_protocol.json"),
              "setup_seconds": setup_seconds, "query_seconds": elapsed,
              "query_ns_min_median_p90_max": [times[0], times[len(times)//2],
                                              times[(9*len(times))//10], times[-1]],
              "root_calls": 142*len(rows), "valid_decoded_roots": valid_roots,
              "source_product_rank": len(basis),
              "validated_source_codes": len(valid),
              "right_coordinate_index_entries": 0,
              "shared_root_product": enc(h),
              "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "rows": rows}
    with (HERE/"mask_decoder_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({k:result[k] for k in ("status", "query_seconds", "root_calls", "valid_decoded_roots", "source_product_rank", "right_coordinate_index_entries")}, sort_keys=True))


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
