#!/usr/bin/env python3
"""Independently recheck finite p=997 Hecke records without touching the seal.

This checks finite chain formulas and saved B/E cosets. It cannot recompute
the quarter-shift projection or prove the modular map and cusp bridge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

P = 997
DEFAULT_ARCHIVE = Path(__file__).resolve().parents[2] / "experiments/hecke-432-prime997-20261025"


class VerificationError(Exception):
    pass


def require(ok: bool, label: str) -> None:
    if not ok:
        raise VerificationError(label)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_seal(root: Path) -> int:
    listed: dict[str, str] = {}
    for line in (root / "SEAL.sha256").read_text(encoding="utf-8").splitlines():
        digest, sep, name = line.partition("  ./")
        require(bool(sep) and len(digest) == 64 and name and name not in listed,
                f"invalid seal entry: {line!r}")
        path = Path(name)
        require(not path.is_absolute() and ".." not in path.parts,
                f"unsafe seal path: {name}")
        listed[name] = digest
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    require(actual == set(listed) | {"SEAL.sha256"},
            f"seal inventory mismatch: missing={sorted(set(listed)-actual)}, extra={sorted(actual-set(listed)-{'SEAL.sha256'})}")
    for name, digest in listed.items():
        got = hashlib.sha256((root / name).read_bytes()).hexdigest()
        require(got == digest, f"seal hash mismatch: {name}")
    return len(listed)


def j_invariant(a: int, b: int) -> int:
    denom = (4 * a**3 + 27 * b * b) % P
    require(denom != 0, f"singular curve a={a} b={b}")
    return 1728 * 4 * a**3 * pow(denom, -1, P) % P


@lru_cache(None)
def roots(a: int, b: int, ell: int) -> tuple[int, ...]:
    if ell == 2:
        return tuple(x for x in range(P) if (x**3 + a*x + b) % P == 0)
    require(ell == 3, f"unsupported ell={ell}")
    return tuple(x for x in range(P)
                 if (3*x**4 + 6*a*x*x + 12*b*x - a*a) % P == 0)


def target(a: int, b: int, r: int, ell: int) -> tuple[int, int]:
    if ell == 2:
        t = 3*r*r + a
        return (a - 5*t) % P, (b - 7*r*t) % P
    require(ell == 3, f"unsupported ell={ell}")
    return ((a - 5*(6*r*r + 2*a)) % P,
            (b - 7*(10*r**3 + 6*a*r + 4*b)) % P)


@lru_cache(None)
def enumerate_paths(a: int, b: int, ell: int, depth: int,
                    back: int | None = None) -> tuple[tuple[int, ...], ...]:
    if depth == 0:
        return ((),)
    out = []
    for r in roots(a, b, ell):
        if r == back:
            continue
        aa, bb = target(a, b, r, ell)
        for tail in enumerate_paths(aa, bb, ell, depth - 1, -ell*r % P):
            out.append((r,) + tail)
    return tuple(out)


def points(b: int) -> list[tuple[int, int] | None]:
    squares: dict[int, list[int]] = {}
    for y in range(P):
        squares.setdefault(y*y % P, []).append(y)
    return [None] + [(x, y) for x in range(P)
                     for y in squares.get((x**3 + b) % P, [])]


def dual(q: tuple[int, int] | None) -> tuple[int, int] | None:
    if q is None or q[0] == 0:
        return None
    x, y = q
    return ((x**3 - 64)*pow(x, -2, P) % P,
            y*(x**3 + 128)*pow(x, -3, P) % P)


def verify_records(census: dict, image: dict) -> dict:
    require(census.get("prime") == image.get("prime") == P, "prime mismatch")
    require(census.get("j_values_scanned") == P, "incomplete j scan metadata")
    rows = census["rows"]
    require(len(rows) == census["rows_with_chains"], "census row count")
    by_j = {r["j"]: r for r in rows}
    require(len(by_j) == len(rows), "duplicate source j")
    require(all(r["label"] == "generic" for r in rows), "unexpected source class")
    squares = Counter(y*y % P for y in range(P))
    edge_count = 0
    expected_sources = []
    for row in rows:
        j = row["j"]
        a, b = row["curve_ainvs"][3:]
        require(row["curve_ainvs"] == [0, 0, 0, a, b], f"curve model j={j}")
        require(j == j_invariant(a, b), f"source j mismatch j={j}")
        trace = P - sum(squares[(x**3 + a*x + b) % P] for x in range(P))
        require(row["trace"] == trace, f"trace mismatch j={j}")
        two, three = row["two_paths"], row["three_paths"]
        require(row["paired_chain_count"] == len(two)*len(three),
                f"pair count mismatch j={j}")
        for ell, depth, path_rows in ((2, 4, two), (3, 3, three)):
            listed = set()
            for path in path_rows:
                require(len(path) == depth, f"path depth j={j} ell={ell}")
                aa, bb, back = a, b, None
                chosen = []
                for edge in path:
                    r = edge["kernel_x"]
                    require(r in roots(aa, bb, ell) and r != back,
                            f"invalid kernel root j={j} ell={ell} root={r}")
                    require(edge["source_j"] == j_invariant(aa, bb),
                            f"edge source j mismatch j={j} ell={ell}")
                    aa, bb = target(aa, bb, r, ell)
                    require(edge["target_ainvs"] == [0, 0, 0, aa, bb],
                            f"target model mismatch j={j} ell={ell}")
                    require(edge["target_j"] == j_invariant(aa, bb),
                            f"target j mismatch j={j} ell={ell}")
                    back = -ell*r % P
                    require(edge["dual_kernel_x"] == back,
                            f"dual root mismatch j={j} ell={ell}")
                    chosen.append(r)
                    edge_count += 1
                listed.add(tuple(chosen))
            require(len(listed) == len(path_rows) and
                    listed == set(enumerate_paths(a, b, ell, depth)),
                    f"incomplete or duplicate path set j={j} ell={ell}")
        for i in range(len(two)):
            for k in range(len(three)):
                expected_sources.append((tuple(row["curve_ainvs"]), j, (i, k)))

    require(sum(r["paired_chain_count"] for r in rows) == census["paired_chain_count"],
            "census total mismatch")
    primitive = next(g for g in range(2, P)
                     if all(pow(g, (P-1)//q, P) != 1 for q in (2, 3, 83)))
    found = {}
    special_count = 0
    for j in range(P):
        if j in (0, 1728 % P):
            models = ([(0, pow(primitive, k, P)) for k in range(6)] if j == 0
                      else [(pow(primitive, k, P), 0) for k in range(4)])
            for a, b in models:
                special_count += 1
                require(not enumerate_paths(a, b, 2, 4) or
                        not enumerate_paths(a, b, 3, 3),
                        f"special twist contributes at j={j} a={a} b={b}")
            continue
        a, b = -3*j*(j-1728) % P, -2*j*(j-1728)**2 % P
        n2 = len(enumerate_paths(a, b, 2, 4))
        n3 = len(enumerate_paths(a, b, 3, 3)) if n2 else 0
        if n2*n3:
            found[j] = n2*n3
            require(j in by_j and by_j[j]["curve_ainvs"] == [0, 0, 0, a, b] and
                    by_j[j]["paired_chain_count"] == n2*n3,
                    f"generic source census mismatch j={j}")
    require(set(found) == set(by_j), "source j set mismatch")
    require(sum(found.values()) == len(expected_sources), "enumerated source total")

    B, E = points(-16), points(432)
    preimages: dict[tuple[int, int] | None, set[tuple[int, int] | None]] = {}
    for q in B:
        preimages.setdefault(dual(q), set()).add(q)
    require(all(len(v) == 3 for v in preimages.values()), "dual coset cardinality")
    actual = image["rows"]
    require(len(actual) == image["row_count"] == len(expected_sources),
            "image row count mismatch")
    fibers = Counter()
    for row, (model, j, pair) in zip(actual, expected_sources):
        require(tuple(row["source_ainvs"]) == model and tuple(row["pair"]) == pair,
                f"source key mismatch j={j} pair={pair}")
        require(row["source_j"] == j, f"source j metadata mismatch j={j} pair={pair}")
        require(row["source_label"] == "generic", f"source label j={j} pair={pair}")
        require(len(row["projections"]) == 1, f"projection count j={j} pair={pair}")
        value = row["projections"][0]
        e = tuple(value["E_point"]) if value["E_point"] is not None else None
        saved = {tuple(q) if q is not None else None for q in value["B_preimages"]}
        require(e in preimages and saved == preimages[e] and len(saved) == 3,
                f"incomplete B coset j={j} pair={pair}")
        fibers[e] += 1
    require(image["candidate_count_distribution"] == {"1": len(actual)},
            "candidate distribution metadata")
    require(None not in fibers, "identity in noncuspidal E image")
    histogram = dict(sorted(Counter(fibers.values()).items()))
    return {"schema": "cryptanalysis.p997.finite_record_guard.v1",
            "prime": P, "generic_classes": len(found),
            "special_twists_checked": special_count,
            "source_pairs": len(expected_sources), "raw_edges_checked": edge_count,
            "B_order": len(B), "E_order": len(E),
            "dual_image_points": len(preimages),
            "E_projection_images": len(fibers),
            "histogram": {str(k): v for k, v in histogram.items()},
            "scope": "finite chain and archived coset consistency; no quarter-shift or modular-map proof"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, help="write receipt here; otherwise print JSON")
    args = parser.parse_args()
    try:
        seal_count = check_seal(args.archive)
        result = verify_records(load(args.archive / "census.json"),
                                load(args.archive / "image.json"))
        result["seal_entries"] = seal_count
        result["seal_sha256"] = hashlib.sha256((args.archive / "SEAL.sha256").read_bytes()).hexdigest()
        result["census_sha256"] = hashlib.sha256((args.archive / "census.json").read_bytes()).hexdigest()
        result["image_sha256"] = hashlib.sha256((args.archive / "image.json").read_bytes()).hexdigest()
        result["verifier_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except (VerificationError, KeyError, ValueError, OSError, TypeError) as exc:
        print(f"p997 finite guard: FAIL: {exc}", file=sys.stderr)
        return 1
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8")
        except OSError as exc:
            print(f"p997 finite guard: cannot write receipt: {exc}", file=sys.stderr)
            return 1
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
