#!/usr/bin/env python3
"""Independent check of a Z[tau]-closure base header and of its factor-log table.

Runs in the pinned pure-Python oracle (`oracle.py` through the pinned
harness), not the producer and not the generator's code path:

Base (`verify_base`):

* identity: kind, n, a, r, field modulus equal to B's K600 header; the K'
  column representatives are B's first K' representatives;
* multipliers: every (a, b) has a odd, a > 0, a^2 + ab + 2b^2 <= cap, no
  repeats; every column has the same multiplier list;
* every orbit representative P = alpha(R_c) is on the curve, not the
  identity, in the prime-order subgroup ([r]P = O), and equal to
  [(a + b lambda) mod r]R_c (a scalar multiplication, where the generator
  formed [a]R_c + [b]phi(R_c));
* the orbits are distinct up to sign and Frobenius: the orbit keys (min x
  over the 83 conjugates) are pairwise different across all columns, and
  all |B| x-coordinates are distinct;
* every member and label: the coordinate list is exactly +-phi^k(P) for
  each orbit with labels (c, +-(a + b lambda) lambda^k mod r), and the
  base hash recomputes.

Table (`verify_table`, with a base that passed): kind, n/a/r, base hash,
width K', range, [L_c]G = R_c for every column, and [w L_c]G = P for every
orbit (w = a + b lambda), so every one of the |B| labels is the discrete log
of its point relative to G.

`planted_controls` corrupts copies in memory (one label coefficient, one
duplicated orbit, one log) and requires each check to fail.

Usage: verify_closure.py --base H [--table T] [--planted] [--out J]
"""

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_closure_base import K600, oracle  # noqa: E402  (paths and the pinned oracle only)

DOMAIN = b"n83-closure-base-v1"


def _hash(points, labels):
    digest = hashlib.sha256(DOMAIN)
    for (x, y), (column, coefficient) in zip(points, labels):
        for word, width in ((x, 16), (y, 16), (column, 8), (coefficient, 8)):
            digest.update(int(word).to_bytes(width, "little"))
    return digest.hexdigest()


def _sq(curve, v):
    return curve.fm(v, v)


def verify_base(header, curve, k600):
    r, lam, n = curve.r, curve.lam, curve.n
    checks, notes = {}, {}
    closure = header.get("closure") or {}
    checks["identity"] = (header.get("kind") == "point_defined_factor_base" and header.get("n") == n
                          and header.get("a") == curve.a and int(header.get("subgroup_order")) == r
                          and header.get("field_modulus_low_terms") == k600["field_modulus_low_terms"])
    columns = header["orbit_columns"]
    column_reps = header["factor_base_representatives"]
    checks["column_representatives_are_B_first_K"] = (
        len(column_reps) == columns and column_reps == k600["factor_base_representatives"][:columns])
    orbit_reps, orbit_labels = header["orbit_representatives"], header["orbit_labels"]
    cap = closure.get("norm_cap", -1)
    per_column = {}
    for column, a, b in orbit_labels:
        per_column.setdefault(column, []).append((a, b))
    lists = list(per_column.values())
    checks["multipliers"] = (
        sorted(per_column) == list(range(columns)) and all(m == lists[0] for m in lists)
        and len(set(lists[0])) == len(lists[0]) and lists[0][0] == (1, 0)
        and all(a % 2 == 1 and a > 0 and a * a + a * b + 2 * b * b <= cap for a, b in lists[0])
        and len(orbit_reps) == len(orbit_labels) == columns * len(lists[0]))
    notes["orbits"] = len(orbit_reps)
    notes["orbits_per_column"] = len(lists[0])
    decoded_columns = [curve.decode([int(p[0]), int(p[1])]) for p in column_reps]
    in_subgroup, closure_relation, keys = True, True, {}
    decoded_orbits = []
    for (column, a, b), raw in zip(orbit_labels, orbit_reps):
        p = curve.decode([int(raw[0]), int(raw[1])])
        decoded_orbits.append(p)
        if p is None or curve.mul(p, r) is not None:
            in_subgroup = False
        if curve.mul(decoded_columns[column], (a + b * lam) % r) != p:
            closure_relation = False
        x, key = p[0], p[0]
        for _ in range(1, n):
            x = _sq(curve, x)
            key = min(key, x)
        keys.setdefault(key, []).append((column, a, b))
    checks["every_orbit_in_prime_order_subgroup"] = in_subgroup
    checks["every_orbit_is_alpha_of_its_column"] = closure_relation
    repeats = [v for v in keys.values() if len(v) > 1]
    checks["orbits_distinct_up_to_sign_and_frobenius"] = not repeats
    notes["repeated_orbits"] = repeats[:5]
    points, labels = header["factor_base_point_coordinates"], header["factor_base_point_labels"]
    members_ok = len(points) == len(labels) == header["factor_base_points"] == 2 * n * len(orbit_reps)
    if members_ok:
        i = 0
        for (column, a, b), p in zip(orbit_labels, decoded_orbits):
            x, y = p
            coefficient = (a + b * lam) % r
            for _ in range(n):
                want = ([str(x), str(y)], [column, coefficient], [str(x), str(x ^ y)], [column, (r - coefficient) % r])
                if (points[i], labels[i], points[i + 1], labels[i + 1]) != want:
                    members_ok = False
                    break
                i += 2
                x, y = _sq(curve, x), _sq(curve, y)
                coefficient = coefficient * lam % r
            if not members_ok:
                break
    checks["every_member_and_label"] = members_ok
    checks["all_x_distinct"] = len({p[0] for p in points}) == len(points) // 2
    checks["base_hash"] = header.get("base_hash") == _hash(points, labels)
    return {"checks": checks, "notes": notes, "status": "PASS" if all(checks.values()) else "FAIL"}


def verify_table(table, header, curve):
    r, lam = curve.r, curve.lam
    logs = [int(v) for v in table["logs"]]
    columns = header["orbit_columns"]
    checks = {
        "kind": table.get("kind") == "compact_orbit_factor_log_table",
        "n_a_r": (table.get("n"), table.get("a"), str(table.get("subgroup_order"))) ==
                 (header["n"], header["a"], str(header["subgroup_order"])),
        "base_hash": table.get("base_hash") == header["base_hash"],
        "width": table.get("orbit_columns") == columns == len(logs),
        "range": all(0 < log < r for log in logs),
    }
    reps = header["factor_base_representatives"]
    bad_columns = [c for c, (log, rep) in enumerate(zip(logs, reps))
                   if curve.mul(curve.g, log) != curve.decode([int(rep[0]), int(rep[1])])]
    checks["every_column_log_maps_G_to_R_c"] = not bad_columns
    bad_orbits = []
    if checks["width"]:
        for o, ((column, a, b), raw) in enumerate(zip(header["orbit_labels"], header["orbit_representatives"])):
            if curve.mul(curve.g, (a + b * lam) * logs[column] % r) != curve.decode([int(raw[0]), int(raw[1])]):
                bad_orbits.append(o)
    checks["every_orbit_log_maps_G_to_its_representative"] = checks["width"] and not bad_orbits
    return {"checks": checks, "bad_columns": bad_columns[:20], "bad_orbits": bad_orbits[:20],
            "logs_sha256": hashlib.sha256(json.dumps(table["logs"]).encode()).hexdigest(),
            "status": "PASS" if all(checks.values()) else "FAIL"}


def planted_controls(header, table, curve, k600):
    """Each corruption must be caught."""
    out = {}
    bad = copy.deepcopy(header)
    bad["factor_base_point_labels"][2 * 83 + 1][1] = (bad["factor_base_point_labels"][2 * 83 + 1][1] + 1) % curve.r
    out["label_coefficient_off_by_one"] = verify_base(bad, curve, k600)["status"] == "FAIL"
    bad = copy.deepcopy(header)
    p = curve.decode([int(v) for v in bad["orbit_representatives"][0]])
    q = curve.frob(p)
    bad["orbit_representatives"][1] = [str(q[0]), str(q[1])]
    out["duplicated_orbit"] = (lambda res: res["status"] == "FAIL"
                               and not res["checks"]["orbits_distinct_up_to_sign_and_frobenius"])(
        verify_base(bad, curve, k600))
    if table is not None:
        bad = copy.deepcopy(table)
        bad["logs"][0] = str((int(bad["logs"][0]) + 1) % curve.r) if isinstance(bad["logs"][0], str) \
            else (int(bad["logs"][0]) + 1) % curve.r
        out["log_off_by_one"] = verify_table(bad, header, curve)["status"] == "FAIL"
    return {"caught": out, "status": "PASS" if all(out.values()) else "FAIL"}


def run(base_path, table_path=None, planted=False, curve=None):
    curve = curve or oracle()
    k600 = json.loads(K600.read_text().splitlines()[0])
    raw = Path(base_path).read_bytes()
    header = json.loads(raw.split(b"\n", 1)[0])
    result = {"base": str(base_path), "base_sha256": hashlib.sha256(raw).hexdigest(),
              "base_hash": header.get("base_hash"),
              "checker": "oracle.py pure-Python field arithmetic (pinned harness), not the producer",
              "base_check": verify_base(header, curve, k600)}
    table = None
    if table_path is not None:
        table_bytes = Path(table_path).read_bytes()
        table = json.loads(table_bytes)
        result["table"] = str(table_path)
        result["table_sha256"] = hashlib.sha256(table_bytes).hexdigest()
        result["table_check"] = verify_table(table, header, curve)
    if planted:
        result["planted_controls"] = planted_controls(header, table, curve, k600)
    parts = [result["base_check"]["status"]] + [result[k]["status"] for k in ("table_check", "planted_controls")
                                                 if k in result]
    result["status"] = "PASS" if all(s == "PASS" for s in parts) else "FAIL"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--table", type=Path)
    parser.add_argument("--planted", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = run(args.base, args.table, args.planted)
    text = json.dumps(result, indent=1, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text)
    print(json.dumps({"status": result["status"], "base": str(args.base)}))
    sys.exit(0 if result["status"] == "PASS" else 3)


if __name__ == "__main__":
    main()
