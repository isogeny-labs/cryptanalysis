"""Recover a right source code from each S3 root by the pair quadratic."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from oracle_sage import HERE, INPUT, dec, enc, load, point, s3_roots


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_decoder(states):
    """Use h = root0*root1 and k = root0+root1 = b+h/b."""
    h = None
    code_k = []
    for code in range(71):
        roots = sorted({enc(1/states[1][sid][0])
                        for sid in range(4*code, 4*code+4)})
        assert len(roots) == 2 and all(roots)
        product = dec(roots[0])*dec(roots[1])
        if h is None:
            h = product
        assert product == h
        code_k.append(roots[0] ^ roots[1])
    basis = {}

    def reduce(word):
        vector = word
        signature = 0
        for pivot in sorted(basis, reverse=True):
            if (vector >> pivot) & 1:
                vector ^= basis[pivot][0]
                signature ^= basis[pivot][1]
        return vector, signature

    for k in code_k:
        remainder, _ = reduce(k)
        if remainder:
            rank = len(basis)
            basis[remainder.bit_length()-1] = (remainder, 1 << rank)
    assert len(basis) == 8
    signature_to_code = {}
    for code, k in enumerate(code_k):
        remainder, signature = reduce(k)
        assert remainder == 0 and signature not in signature_to_code
        signature_to_code[signature] = code

    def decode_root(b):
        if not b:
            return None
        k = enc(b + h/b)
        remainder, signature = reduce(k)
        return None if remainder else signature_to_code.get(signature)

    for code in range(71):
        for sid in range(4*code, 4*code+4):
            assert decode_root(1/states[1][sid][0]) == code
    return h, basis, signature_to_code, decode_root


def freeze():
    data = json.loads((HERE/"batch_protocol.json").read_text())
    protocol = {"status": "FROZEN", "candidate_id": None,
                "curve_id": data["curve_id"], "key_count": data["key_count"],
                "batch_protocol_sha256": sha(HERE/"batch_protocol.json"),
                "input_sha256": sha(INPUT),
                "oracle_script_sha256": sha(HERE/"oracle_sage.py"),
                "decoder_script_sha256": sha(Path(__file__)),
                "runtime_info_sha256": sha(HERE/"sage_runtime_info.json"),
                "worker_count": 1, "wall_cap_seconds": 120,
                "rss_cap_bytes": 4*1024**3}
    with (HERE/"decoder_protocol.json").open("x") as out:
        json.dump(protocol, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({"status": "FROZEN", "key_count": data["key_count"]}))


def run():
    protocol = json.loads((HERE/"decoder_protocol.json").read_text())
    batch = json.loads((HERE/"batch_protocol.json").read_text())
    for field, path in (("batch_protocol_sha256", HERE/"batch_protocol.json"),
                        ("input_sha256", INPUT),
                        ("oracle_script_sha256", HERE/"oracle_sage.py"),
                        ("decoder_script_sha256", Path(__file__)),
                        ("runtime_info_sha256", HERE/"sage_runtime_info.json")):
        assert protocol[field] == sha(path), field
    assert not (HERE/"decoder_result.json").exists()
    _, states, cols = load()
    setup_start = time.monotonic()
    h, basis, signatures, decoder = build_decoder(states)
    left = {}
    for sid, P in enumerate(states[0]):
        left.setdefault(enc(1/P[0]), []).append(sid)
    assert len(left) == 142
    setup_seconds = time.monotonic()-setup_start
    rows = []
    begin = time.monotonic()
    decoded_valid = 0
    for item in batch["keys"]:
        key = point(item["key"])
        t = 1/key[0]
        tick = time.monotonic_ns()
        matches = set()
        valid = 0
        for aword, a_ids in left.items():
            roots = s3_roots(dec(aword), t)
            assert roots is not None
            for b in roots:
                code = decoder(b)
                if code is None:
                    continue
                valid += 1
                for bid in range(4*code, 4*code+4):
                    if states[1][bid][0] and 1/states[1][bid][0] == b:
                        for aid in a_ids:
                            if cols[0][aid].isdisjoint(cols[1][bid]) and states[0][aid]+states[1][bid] == key:
                                matches.add((aid,bid))
        decoded_valid += valid
        rows.append({"suffix_ids": item["suffix_ids"],
                     "matches": [list(v) for v in sorted(matches)],
                     "valid_decoded_roots": valid,
                     "query_ns": time.monotonic_ns()-tick})
    elapsed = time.monotonic()-begin
    times = sorted(row["query_ns"] for row in rows)
    result = {"status": "PASS_MAPLESS_CODE_DECODER", "candidate_id": None,
              "protocol_sha256": sha(HERE/"decoder_protocol.json"),
              "batch_protocol_sha256": sha(HERE/"batch_protocol.json"),
              "setup_seconds": setup_seconds, "query_seconds": elapsed,
              "query_ns_min_median_p90_max": [times[0], times[len(times)//2],
                                              times[(9*len(times))//10], times[-1]],
              "root_calls": 142*len(rows),
              "valid_decoded_roots": decoded_valid,
              "field_basis_rank": len(basis),
              "valid_code_signatures": len(signatures),
              "right_coordinate_index_entries": 0,
              "shared_root_product": enc(h),
              "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "rows": rows}
    with (HERE/"decoder_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({k:result[k] for k in ("status", "query_seconds", "root_calls", "valid_decoded_roots", "field_basis_rank", "right_coordinate_index_entries")}, sort_keys=True))


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
