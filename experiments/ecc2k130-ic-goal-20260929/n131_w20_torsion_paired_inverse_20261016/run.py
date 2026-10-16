"""Four-preimage W20 source join using reciprocal torsion-paired S3 roots."""
import hashlib
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT / "n131_w20_quadratic_two_pair_inverse_20261016" / "run_n131.py"
PRE = ROOT / "n131_fixed_seed_eight_pair_circuit_20261010" / "target_preimages.json"
spec = importlib.util.spec_from_file_location("two_pair", OLD)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def query(mode):
    setup_start = time.monotonic()
    assert mode in ("sample", "full")
    protocol = json.loads((HERE / (mode + "_protocol.json")).read_text())
    assert {"runner": digest(HERE / "run.py"), "old_solver": digest(OLD),
            "preimages": digest(PRE), "support": digest(old.SUPPORT)} == protocol["sources"]
    F = old.field()
    conv = F.from_integer
    preimages = json.loads(PRE.read_text())
    assert preimages["workload_id"] == protocol["workload_id"]
    zs = []
    for row in preimages["preimages"]:
        chart = conv(row["reciprocal_x_z"])
        x = conv(row["point"][0])
        assert chart * (x + 1) == 1
        z = chart / (chart + 1)
        assert z * x == 1
        zs.append(z)
    assert len(zs) == 4 and zs[0] * zs[1] == 1 and zs[2] * zs[3] == 1
    seed = protocol["seed"]
    edges = old.source_edges(seed)
    if mode == "sample":
        size = protocol["sample_size"]
        edges = [edges[i * len(edges) // size] for i in range(size)]
    w = conv(seed << 1)
    h = F.zero()
    term = w
    for _ in range(66):
        h += term
        term = term**4
    assert h*h + h == w
    h2 = h*h
    hright2 = (h**(1 << 18))**2
    Cr, Hr = F.one() + hright2, hright2
    right_index = {}
    for code, a, b, ca, cb in old.source_edges(seed):
        p = (conv(a << 1) * conv(b << 1))**(1 << 18)
        right_index[int(p.to_integer())] = (code, ca, cb)
    assert len(right_index) == 132045
    prepared = []
    for code, a, b, ca, cb in edges:
        p = conv(a << 1) * conv(b << 1)
        us = old.quadratic(F, F.one() + h2, p, h2)
        assert len(us) == 2
        prepared.append((code, (ca, cb), us))
    setup_done = time.monotonic()
    counts = [{"preimage_index": j, "proposals": 0, "eligible_source_hits": 0}
              for j in range(4)]
    hits = []
    quadratic_calls = 0
    root_checks = 0
    exceptional = 0
    started = time.monotonic()
    for i, (left_code, left_columns, us) in enumerate(prepared):
        for u in us:
            for j in (0, 2):
                z = zs[j]
                uz = u*z
                try:
                    roots = old.quadratic(F, F.one() + uz*uz, uz, u*u + z*z)
                except old.ZeroPolynomial:
                    exceptional += 1
                    continue
                quadratic_calls += 1
                if mode == "sample":
                    zp = zs[j+1]
                    uzp = u*zp
                    direct = old.quadratic(F, F.one() + uzp*uzp, uzp, u*u + zp*zp)
                    assert {int(d.to_integer()) for d in direct} == \
                           {int((1/d).to_integer()) for d in roots if d != 0}
                    root_checks += 1
                for d in roots:
                    if d == 0:
                        exceptional += 1
                        continue
                    dinv = 1/d
                    for k, e, q in ((j, d, Cr*d + Hr*dinv),
                                    (j+1, dinv, Cr*dinv + Hr*d)):
                        # A reciprocal root is exact for the torsion partner.
                        if mode == "sample":
                            ztest = zs[k]
                            assert (u*e*ztest)**2 + u*e*ztest + u*u + e*e + ztest*ztest == 0
                        counts[k]["proposals"] += 1
                        match = right_index.get(int(q.to_integer()))
                        if match is None:
                            continue
                        right_code, ca, cb = match
                        if ca in left_columns or cb in left_columns:
                            continue
                        counts[k]["eligible_source_hits"] += 1
                        hits.append({"preimage_index": k, "left_code": left_code,
                                     "right_code": right_code, "left_root": int(u.to_integer()),
                                     "right_root": int(e.to_integer())})
        if (i & 1023) == 0:
            assert time.monotonic() - started < protocol["query_cap_seconds"]
            assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss < protocol["rss_cap_bytes"]
    ended = time.monotonic()
    assert ended - started < protocol["query_cap_seconds"]
    result = {"status": "COMPLETE_TORSION_PAIRED_" + mode.upper(),
              "candidate_id": None, "curve_id": "EC1N131Ckb1heb5f1998f20b",
              "workload_id": preimages["workload_id"], "selected_seed_mask": seed,
              "left_codes": len(prepared), "right_index_size": len(right_index),
              "target_quadratic_calls": quadratic_calls, "direct_partner_root_checks": root_checks,
              "exceptional_cases": exceptional, "preimage_rows": counts,
              "eligible_source_hits": hits, "query_seconds_exploratory": ended-started,
              "setup_seconds_exploratory": setup_done-setup_start,
              "peak_self_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              "protocol_sha256": digest(HERE / (mode + "_protocol.json"))}
    path = HERE / (mode + "_result.json")
    with path.open("x") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")
    print(result["status"], quadratic_calls, sum(r["proposals"] for r in counts),
          len(hits), ended-started)


if __name__ == "__main__":
    assert len(sys.argv) == 2
    query(sys.argv[1])
