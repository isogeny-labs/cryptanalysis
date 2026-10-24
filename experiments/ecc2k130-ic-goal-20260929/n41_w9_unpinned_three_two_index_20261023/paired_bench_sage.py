"""ABBA comparison of the exact coordinate index and direct mask decoder."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

from oracle_sage import HERE, INPUT, dec, enc, load, point, s3_roots
from mask_decoder_sage import build as build_mask_decoder


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    batch = json.loads((HERE/"batch_protocol.json").read_text())
    protocol = {"status": "FROZEN", "candidate_id": None,
                "curve_id": batch["curve_id"],
                "key_count": batch["key_count"],
                "order": ["index", "decoder", "decoder", "index"],
                "batch_protocol_sha256": sha(HERE/"batch_protocol.json"),
                "input_sha256": sha(INPUT),
                "oracle_script_sha256": sha(HERE/"oracle_sage.py"),
                "mask_decoder_script_sha256": sha(HERE/"mask_decoder_sage.py"),
                "bench_script_sha256": sha(Path(__file__)),
                "runtime_info_sha256": sha(HERE/"sage_runtime_info.json"),
                "worker_count": 1, "wall_cap_seconds": 120,
                "rss_cap_bytes": 4*1024**3}
    with (HERE/"paired_protocol.json").open("x") as out:
        json.dump(protocol, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({"status": "FROZEN", "order": protocol["order"]}))


def run():
    protocol = json.loads((HERE/"paired_protocol.json").read_text())
    for name, path in (("batch_protocol_sha256", HERE/"batch_protocol.json"),
                       ("input_sha256", INPUT),
                       ("oracle_script_sha256", HERE/"oracle_sage.py"),
                       ("mask_decoder_script_sha256", HERE/"mask_decoder_sage.py"),
                       ("bench_script_sha256", Path(__file__)),
                       ("runtime_info_sha256", HERE/"sage_runtime_info.json")):
        assert protocol[name] == sha(path), name
    assert not (HERE/"paired_result.json").exists()
    batch = json.loads((HERE/"batch_protocol.json").read_text())
    _, states, cols = load()
    left = {}
    right = {}
    for sid in range(284):
        left.setdefault(enc(1/states[0][sid][0]), []).append(sid)
        right.setdefault(enc(1/states[1][sid][0]), []).append(sid)
    _, basis, _, decoder = build_mask_decoder(states)
    assert len(left) == len(right) == 142 and len(basis) == 8
    targets = [(point(item["key"]), item["suffix_ids"]) for item in batch["keys"]]
    reference = json.loads((HERE/"batch_audit_result.json").read_text())
    assert reference["query_count"] == len(targets)
    expected = {v["index"]:v["matches"] for v in reference["positive_rows"]}
    arms = []
    for method in protocol["order"]:
        tick = time.monotonic()
        hits = []
        candidate_roots = 0
        for index, (target, _) in enumerate(targets):
            t = 1/target[0]
            matches = set()
            for aword, a_ids in left.items():
                roots = s3_roots(dec(aword), t)
                assert roots is not None
                for b in roots:
                    if method == "index":
                        bids = right.get(enc(b), [])
                    else:
                        code = decoder(b)
                        if code is None:
                            bids = ()
                        else:
                            bids = [sid for sid in range(4*code, 4*code+4)
                                    if 1/states[1][sid][0] == b]
                    candidate_roots += bool(bids)
                    for bid in bids:
                        for aid in a_ids:
                            if cols[0][aid].isdisjoint(cols[1][bid]) and states[0][aid]+states[1][bid] == target:
                                matches.add((aid,bid))
            expected_row = expected.get(index, [])
            assert [list(pair) for pair in sorted(matches)] == expected_row
            if matches:
                hits.append(index)
        arms.append({"method": method, "seconds": time.monotonic()-tick,
                     "root_calls": len(targets)*len(left),
                     "candidate_root_count": candidate_roots,
                     "positive_key_indices": hits})
    assert [arm["positive_key_indices"] for arm in arms] == [[0]]*4
    result = {"status": "PASS_PAIRED_ABBA", "candidate_id": None,
              "protocol_sha256": sha(HERE/"paired_protocol.json"),
              "reference_sha256": sha(HERE/"batch_audit_result.json"),
              "arms": arms,
              "index_mean_seconds": (arms[0]["seconds"]+arms[3]["seconds"])/2,
              "decoder_mean_seconds": (arms[1]["seconds"]+arms[2]["seconds"])/2,
              "self_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    with (HERE/"paired_result.json").open("x") as out:
        json.dump(result, out, sort_keys=True, indent=2)
        out.write("\n")
    print(json.dumps({k:result[k] for k in ("status", "index_mean_seconds", "decoder_mean_seconds")}, sort_keys=True))


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
