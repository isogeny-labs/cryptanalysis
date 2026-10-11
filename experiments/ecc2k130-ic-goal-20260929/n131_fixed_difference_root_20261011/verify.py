"""Read-only identity and receipt audit for fixed-difference root extraction."""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "n131_w14_coupled_fouratom_inverse_20261010"
TERMS = ROOT / "resultant_terms.json"
INPUTS = ROOT / "inputs.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def symmetric_quotient(original):
    sums = [set(), {(1, 0)}]
    for _ in range(2, 9):
        sums.append({(a+1, b) for a, b in sums[-1]}
                    ^ {(a, b+1) for a, b in sums[-2]})
    output, visited = set(), set()
    for s, p, q, z in sorted(original):
        if (s, p, q, z) in visited:
            continue
        assert (s, q, p, z) in original
        if p == q:
            orbit = {(s, 0, p, z)}
        else:
            orbit = {(s, a, b+min(p, q), z) for a, b in sums[abs(p-q)]}
        output ^= orbit
        visited.update(((s, p, q, z), (s, q, p, z)))
    assert visited == original
    return output


def expand(quotient):
    expanded = set()
    for s, P, T, z in quotient:
        expanded ^= {(s, i+T, P-i+T, z)
                      for i in range(P+1) if i & P == i}
    return expanded


def main():
    p, q = read("protocol.json"), read("quotient_protocol.json")
    first, second = read("result.json"), read("quotient_result.json")
    assert p["status"] == "FROZEN_FIXED_DIFFERENCE_ROOT_GATE"
    assert q["status"] == "FROZEN_FIXED_DIFFERENCE_QUOTIENT"
    assert p["sha256"] == {"source": sha(HERE / "run.py"), "terms": sha(TERMS),
                           "inputs": sha(INPUTS), "runtime": sha(HERE / "sage_runtime_info.json")}
    assert q["sha256"] == {"source": sha(HERE / "quotient.py"), "terms": sha(TERMS),
                           "inputs": sha(INPUTS), "prior": sha(HERE / "result.json"),
                           "runtime": sha(HERE / "sage_runtime_info.json")}
    assert first["status"] == second["status"] == "COMPLETE"
    assert first["protocol_sha256"] == sha(HERE / "protocol.json")
    assert second["protocol_sha256"] == sha(HERE / "quotient_protocol.json")
    assert first["source_sha256"] == sha(HERE / "run.py")
    assert not (HERE / "run.stderr.txt").read_bytes()
    assert not (HERE / "quotient.stderr.txt").read_bytes()
    assert '"status": "COMPLETE"' in (HERE / "run.stdout.txt").read_text()
    assert '"status": "COMPLETE"' in (HERE / "quotient.stdout.txt").read_text()
    original = {tuple(row) for row in json.loads(TERMS.read_text())["terms_s_p_q_z"]}
    quotient = symmetric_quotient(original)
    assert len(original) == 150 and len(quotient) == second["quotient_terms"] == 87
    assert expand(quotient) == original
    assert max(t[2] for t in quotient) == 8
    for label, count, expected in (("41", 32, [24, 72]),
                                   ("131", 8192, [1112, 1376])):
        a, b = first["panels"][label], second["panels"][label]
        assert a["curve_id"] == b["curve_id"]
        assert a["source_product_image_size"] == count
        for name in ("positive", "trace_zero_control"):
            direct, reduced = a["cases"][name], b["cases"][name]
            assert direct["degree"] == 16
            assert reduced["quotient_degree"] == 8
            assert direct["all_field_roots"] == reduced["recovered_product_roots"]
            assert direct["source_products_checked_by_scan"] == count
            assert direct["root_query_ns"] < p["cap_seconds_per_case"]*10**9
            assert direct["full_image_scan_ns"] < p["cap_seconds_per_case"]*10**9
            assert reduced["query_ns"] < q["cap_seconds_per_case"]*10**9
        assert a["cases"]["positive"]["source_supported_roots"] == expected
        assert a["cases"]["trace_zero_control"]["source_supported_roots"] == []
    assert first["peak_rss_bytes"] < p["rss_cap_bytes"]
    assert second["peak_rss_bytes"] < q["rss_cap_bytes"]
    record = {"status": "PASS_FIXED_DIFFERENCE_QUOTIENT_ROOT_GATE",
              "universal_symmetric_identity": True,
              "original_term_count": 150, "quotient_term_count": 87,
              "degree_in_product": 16, "degree_in_symmetric_product": 8,
              "producer_sha256": sha(HERE / "result.json"),
              "quotient_sha256": sha(HERE / "quotient_result.json"),
              "n131_positive_products": [1112, 1376],
              "n131_control_supported_roots": 0}
    (HERE / "verification.json").write_text(json.dumps(record, indent=2, sort_keys=True)+"\n")
    print(json.dumps(record, sort_keys=True))


if __name__ == "__main__":
    main()
