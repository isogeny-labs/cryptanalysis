"""Complete ordered public-pair census for the new p=313 rank-one model."""
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    protocol = json.loads((HERE / "relation-protocol.json").read_text())
    screen = json.loads((HERE / "result.json").read_text())
    generator = json.loads((HERE / "generator.json").read_text())
    assert screen["status_counts"] == {"completed": 14, "rank_unknown": 1, "timeout": 1}
    qualified = [r["candidate"] for r in screen["rows"] if r.get("candidate", {}).get("rank") == 1]
    assert len(qualified) == 1 and qualified[0]["field_prime"] == 313 and qualified[0]["u"] == 5
    assert generator["generator_status"] == "proved" and generator["point_is_signed_generator"]
    p, q, w, K = 313, 331, 17, 4
    assert (protocol["field_prime"], protocol["subgroup_order"], protocol["coordinate_cap"]) == (p, q, K)
    maps = [{(k * u) % q: k for k in range(-K, K + 1)} for u in (1, 5)]
    assert len(maps[0]) == len(maps[1]) == 9
    counters = [Counter(), Counter()]
    hits = [[], []]
    out = HERE / "relation-rows.jsonl.gz"
    with out.open("wb") as f:
        with gzip.GzipFile(fileobj=f, mode="wb", filename="", mtime=0) as gz:
            for t1 in range(q):
                s1 = (w - t1) % q
                for t2 in range(q):
                    s2 = (w - t2) % q
                    statuses = []
                    for j, mapping in enumerate(maps):
                        if s1 == 0 or s2 == 0:
                            status = "identity"
                        elif s1 == s2:
                            status = "duplicate"
                        elif s1 not in mapping or s2 not in mapping:
                            status = "outside_cap"
                        else:
                            a, b = mapping[s1], mapping[s2]
                            relation = a + 2 * b == 0
                            assert relation == ((s1 + 2 * s2) % q == 0)
                            status = "rational_relation" if relation else "admitted_nonrelation"
                            if relation:
                                recovered = ((t1 + 2 * t2) * pow(3, -1, q)) % q
                                assert recovered == w
                                hits[j].append({"t": [t1, t2], "k": [a, b],
                                                "query_index_one_based": t1 * q + t2 + 1,
                                                "recovered_scalar": recovered})
                        counters[j][status] += 1
                        statuses.append(status)
                    gz.write((json.dumps({"t": [t1, t2], "status": statuses}, separators=(",", ":")) + "\n").encode())
    print(json.dumps({"schema": "xedni-nonisomorphic-expansion-relation-v1", "status": "PASS",
                      "protocol_sha256": sha(HERE / "relation-protocol.json"),
                      "screen_sha256": sha(HERE / "result.json"), "generator_sha256": sha(HERE / "generator.json"),
                      "source_sha256": sha(Path(__file__)), "raw_sha256": sha(out),
                      "queries": q * q, "membership_tests": 2 * q * q,
                      "models": [{"u": u, "curve_B": B, "counts": dict(counters[j]), "hits": hits[j]}
                                 for j, (u, B) in enumerate(((1, -2), (5, 804408)))]}, sort_keys=True, indent=2))

if __name__ == "__main__":
    main()
