#!/usr/bin/env python3
"""Independently verify a known-log factor base and its factor-log table.

The generator (`knownlog/`, Rust, no dependencies) writes a
`point_defined_factor_base` header and a `compact_orbit_factor_log_table`.
This checker shares no code with it or with the producer that reads its
output. It uses the pinned pure-Python oracle of crypto 770f6a69
(`oracle.py`, through the reconcile experiment's `verify_log_table.verify`)
and Python's own SHA-256 to check:

* the header fields (kind, n, a, r, field modulus, widths, point count);
* every log: [L_j]G = R_j for every representative, in the oracle
  (`verify_log_table.verify`, the check B's archived table passes);
* the scalars: L_j equals the j-th scalar of the declared rule
  (splitmix64(seed), rejection below floor(2^64/r)*r, mod r, 0 rejected),
  re-derived here;
* every base point and label: point 166 j + 2 s is phi^s(R_j) with label
  [j, lambda^s mod r], point 166 j + 2 s + 1 is its negative with label
  [j, -lambda^s mod r], where lambda is the oracle's Frobenius eigenvalue
  (and phi(G) = [lambda]G is checked); so the log of every base point,
  sum(coefficient * L_column), is known;
* distinct orbits (no representative in the orbit of another);
* the base hash, recomputed from the points and labels;
* optionally the files' SHA-256 against the protocol's frozen digests.

`--planted` runs the positive control of this check: three corrupted copies
of the base (one log off by one; one non-representative label coefficient
changed; one orbit point replaced by another point of the curve's subgroup)
must each FAIL. Exit status is nonzero unless every check passes (and, with
`--planted`, every corruption is detected).
"""

import argparse
import copy
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RANKPROBE = HERE.parent / "koblitz-n83-rankprobe-20261019"
RECONCILE = HERE.parent / "koblitz-n83-reconcile-20261014"
SNAPSHOT = RANKPROBE / "snapshots" / "r770"
R = 8569786107849059
MASK64 = (1 << 64) - 1


def oracle_curve():
    sys.path.insert(0, str(RECONCILE))
    import verify_log_table  # noqa: E402  (the reconcile experiment's checker)
    verify_log_table.SNAPSHOT = SNAPSHOT
    verify_log_table.AUTOLAB = SNAPSHOT / "research/sat_factor_base_review_20260908/autolab"
    return verify_log_table, verify_log_table.oracle_curve()


def scalar_rule(seed, count, r):
    limit = (MASK64 // r) * r
    state, out = seed & MASK64, []
    while len(out) < count:
        state = (state + 0x9E3779B97F4A7C15) & MASK64
        z = state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
        z ^= z >> 31
        if z >= limit:
            continue
        if z % r:
            out.append(z % r)
    return out


def base_hash(header):
    columns = header["orbit_columns"]
    data = bytearray(b"n83-knownlog-base-v1")
    data += struct.pack("<IBQQ", header["n"], header["a"], header["subgroup_order"], columns)
    for (x, y), (column, coefficient) in zip(header["factor_base_point_coordinates"],
                                             header["factor_base_point_labels"]):
        data += int(x).to_bytes(16, "little") + int(y).to_bytes(16, "little")
        data += struct.pack("<QQ", column, coefficient)
    return hashlib.sha256(bytes(data)).hexdigest()


def check_base(header, table, curve, vlt, header_path, table_path):
    r = curve.r
    lam = curve.lam
    columns = header.get("orbit_columns")
    reps = [curve.decode([int(v) for v in p]) for p in header["factor_base_representatives"]]
    points = [tuple(int(v) for v in p) for p in header["factor_base_point_coordinates"]]
    labels = header["factor_base_point_labels"]
    checks = {
        "header_kind_n_a_r_modulus": (header.get("kind"), header.get("n"), header.get("a"),
                                      header.get("subgroup_order"), header.get("field_modulus_low_terms")) ==
                                     ("point_defined_factor_base", 83, 1, r, [0, 2, 4, 7]) and r == R,
        "widths": columns == len(reps) == len(table.get("logs", [])) and
                  len(points) == len(labels) == header.get("factor_base_points") == 166 * columns,
        "frobenius_eigenvalue": curve.frob(curve.g) == curve.mul(curve.g, lam) and pow(lam, 83, r) == 1,
    }
    # every [L_j]G = R_j in the oracle (the same function that checks B's archived table)
    log_check = vlt.verify(table_path, header_path, curve)
    checks.update({"log_table_" + key: value for key, value in log_check["checks"].items()})
    logs = [int(v) for v in table["logs"]]
    seed = (header.get("generator") or {}).get("seed")
    checks["logs_equal_declared_scalar_rule"] = (isinstance(seed, int) and table.get("provenance", {}).get("seed") == seed
                                                 and logs == scalar_rule(seed, columns, r))
    bad_points, bad_labels, keys = [], [], set()
    powers = [pow(lam, s, r) for s in range(83)]
    for j, rep in enumerate(reps):
        q = rep
        key = None
        for s in range(83):
            i = 166 * j + 2 * s
            want_plus, want_minus = q, curve.neg(q)
            if curve.decode(list(points[i])) != want_plus:
                bad_points.append(i)
            if curve.decode(list(points[i + 1])) != want_minus:
                bad_points.append(i + 1)
            if labels[i] != [j, powers[s]]:
                bad_labels.append(i)
            if labels[i + 1] != [j, (-powers[s]) % r]:
                bad_labels.append(i + 1)
            key = q[0] if key is None else min(key, q[0])
            q = curve.frob(q)
        if q != rep:
            bad_points.append(166 * j)
        keys.add(key)
    checks["every_point_is_its_signed_frobenius_conjugate"] = not bad_points
    checks["every_label_is_plus_minus_lambda_power"] = not bad_labels
    checks["orbits_distinct"] = len(keys) == columns
    recomputed = base_hash(header)
    checks["base_hash_recomputed"] = recomputed == header.get("base_hash") == table.get("base_hash")
    return checks, {"bad_points": bad_points[:20], "bad_labels": bad_labels[:20],
                    "bad_columns": log_check["bad_columns"], "recomputed_base_hash": recomputed}


def verify(header_path, table_path, curve, vlt, expect=None):
    header = json.loads(Path(header_path).read_text().splitlines()[0])
    table = json.loads(Path(table_path).read_text())
    checks, detail = check_base(header, table, curve, vlt, header_path, table_path)
    digests = {"base_sha256": hashlib.sha256(Path(header_path).read_bytes()).hexdigest(),
               "log_table_sha256": hashlib.sha256(Path(table_path).read_bytes()).hexdigest()}
    if expect:
        checks["frozen_digests"] = all(digests[k] == expect[k] for k in ("base_sha256", "log_table_sha256")) and \
            header.get("base_hash") == expect.get("base_hash")
    return {"orbit_columns": header.get("orbit_columns"), "base_hash": header.get("base_hash"), **digests,
            "checks": checks, "detail": detail, "status": "PASS" if all(checks.values()) else "FAIL",
            "checker": "pinned pure-Python oracle (crypto 770f6a69 oracle.py) and hashlib; shares no code "
                       "with the generator or the producer"}


def planted(header_path, table_path, curve, vlt):
    header = json.loads(Path(header_path).read_text().splitlines()[0])
    table = json.loads(Path(table_path).read_text())
    cases = {}
    with tempfile.TemporaryDirectory(prefix="knownlog-planted-") as folder:
        folder = Path(folder)
        variants = {}
        t = copy.deepcopy(table)
        t["logs"][1] = str((int(t["logs"][1]) + 1) % curve.r)
        variants["log_off_by_one_column_1"] = (header, t)
        h = copy.deepcopy(header)
        h["factor_base_point_labels"][7][1] = (h["factor_base_point_labels"][7][1] + 1) % curve.r
        variants["label_coefficient_changed_point_7"] = (h, table)
        h = copy.deepcopy(header)
        other = curve.mul(curve.g, 123456789)
        h["factor_base_point_coordinates"][9] = [str(other[0]), str(other[1])]
        variants["orbit_point_replaced_point_9"] = (h, table)
        for name, (hv, tv) in variants.items():
            hp, tp = folder / (name + ".jsonl"), folder / (name + ".json")
            hp.write_text(json.dumps(hv, separators=(",", ":")) + "\n")
            tp.write_text(json.dumps(tv, separators=(",", ":")) + "\n")
            result = verify(hp, tp, curve, vlt)
            cases[name] = {"status": result["status"],
                           "failed_checks": sorted(k for k, v in result["checks"].items() if not v),
                           "detected": result["status"] == "FAIL"}
    return {"cases": cases, "status": "PASS" if all(c["detected"] for c in cases.values()) else "FAIL"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", action="append", required=True, type=Path, help="header (repeatable)")
    parser.add_argument("--table", action="append", required=True, type=Path, help="log table (repeatable)")
    parser.add_argument("--expect-protocol", action="store_true",
                        help="compare each base with protocol.json knownlog.bases[<columns>]")
    parser.add_argument("--planted", action="store_true", help="also run the planted corruptions on the last base")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    vlt, curve = oracle_curve()
    frozen = json.loads((HERE / "protocol.json").read_text())["knownlog"]["bases"] if args.expect_protocol else {}
    results = []
    for header_path, table_path in zip(args.base, args.table):
        columns = json.loads(header_path.read_text().splitlines()[0]).get("orbit_columns")
        results.append(verify(header_path, table_path, curve, vlt, frozen.get(str(columns))))
    out = {"bases": results}
    if args.expect_protocol:
        out["every_frozen_base_checked"] = sorted(str(r["orbit_columns"]) for r in results) == sorted(frozen)
    if args.planted:
        out["planted"] = planted(args.base[-1], args.table[-1], curve, vlt)
    ok = all(r["status"] == "PASS" for r in results) and out.get("every_frozen_base_checked", True) and \
        out.get("planted", {}).get("status", "PASS") == "PASS"
    out["status"] = "PASS" if ok else "FAIL"
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text)
    print(json.dumps({"status": out["status"], "bases": [(r["orbit_columns"], r["status"]) for r in results],
                      "planted": out.get("planted", {}).get("status")}))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
