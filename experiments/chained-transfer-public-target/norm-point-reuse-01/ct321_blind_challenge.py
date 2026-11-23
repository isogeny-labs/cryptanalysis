#!/usr/bin/env python3
"""CT321: CSPRNG public ECDLP challenges with separately held scalar/salt reveal.

Only conditional source-level arithmetic/custody checks. Not an independently
authenticated blind run or a complete ECDLP speedup. [pcc:unverified]
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tempfile

import ct317_group_replay as group
import ct320_distinct_public_targets as cold_gate

CURVE = "ct321-source-curve/v1"
PUBLIC = "ct321-public-challenge/v1"
PRIVATE = "ct321-private-reveal/v1"
DOMAIN = b"ct321-source-ecdlp-commit-v1\0"
SALT = re.compile(r"[0-9a-f]{64}\Z")


def refuse(why):
    raise ValueError("CT321: " + why)


def canonical(x):
    return (json.dumps(x, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def strict(raw):
    return group.strict(raw)


def validate_curve(c):
    if type(c) is not dict or set(c) != {
            "schema", "curve_id", "p", "a", "b", "generator",
            "subgroup_prime"} or c["schema"] != CURVE:
        refuse("curve schema or keys")
    if type(c["curve_id"]) is not str or not c["curve_id"] or len(c["curve_id"]) > 160:
        refuse("curve id")
    p = group.num(c["p"], "p", 5)
    n = group.num(c["subgroup_prime"], "subgroup_prime", 3)
    if p > 2**31 - 1 or n > 2**32 - 1 or not group.prime(p) or not group.prime(n):
        refuse("only prime p<=2^31-1, prime n<=2^32-1")
    a = group.num(c["a"], "a")
    b = group.num(c["b"], "b")
    if a >= p or b >= p or (4*a*a*a + 27*b*b) % p == 0:
        refuse("noncanonical or singular curve")
    P = group.point(c["generator"], p, a, b)
    if group.mul(n, P, p, a) is not None:
        refuse("generator not annihilated by prime order")
    return p, a, b, P, n


def curve_from_witness(w):
    if type(w) is not dict or set(w) != {
            "schema", "curve_id", "p", "a", "b", "generator",
            "subgroup_prime", "targets"} or w["schema"] != group.SCHEMA:
        refuse("public CT317 witness schema")
    return {k: v for k, v in w.items() if k != "targets"} | {"schema": CURVE}


def commitment(cid, tid, Q, k, salt):
    return sha(DOMAIN + canonical({
        "curve_id": cid, "target_id": tid, "Q": Q,
        "scalar": k, "salt_hex": salt}))


def generate(curve, count=4, draw=None, saltgen=None):
    p, a, b, P, n = validate_curve(curve)
    if type(count) is not int or count < 4 or count > min(128, n-1):
        refuse("count out of range")
    draw = secrets.randbelow if draw is None else draw
    saltgen = secrets.token_hex if saltgen is None else saltgen
    targets, commitments, reveals = [], [], []
    qs, salts = set(), set()
    tries = 0
    while len(targets) < count:
        tries += 1
        if tries > count*1024:
            refuse("random source failed uniqueness bound")
        r = draw(n-1)
        if type(r) is not int or not 0 <= r < n-1:
            refuse("random source out of range")
        k = r + 1
        Q = group.mul(k, P, p, a)
        if Q is None:
            refuse("unexpected point at infinity")
        if Q in qs:
            continue
        secret_salt = saltgen(32)
        if type(secret_salt) is not str or SALT.fullmatch(secret_salt) is None:
            refuse("salt generator returned malformed salt")
        if secret_salt in salts:
            refuse("salt generator repeated secret nonce")
        salts.add(secret_salt)
        qs.add(Q)
        tid = "ct321-%04d" % len(targets)
        q = list(Q)
        targets.append({"target_id": tid, "Q": q})
        commitments.append({"target_id": tid,
                            "sha256": commitment(curve["curve_id"], tid,
                                                 q, k, secret_salt)})
        reveals.append({"target_id": tid, "scalar": k, "salt_hex": secret_salt})
    witness = {**{k:v for k,v in curve.items() if k != "schema"},
               "schema": group.SCHEMA, "targets": targets}
    public = {"schema": PUBLIC, "witness": witness,
              "commitments": commitments}
    private = {"schema": PRIVATE, "public_sha256": sha(canonical(public)),
               "reveals": reveals}
    return public, private


def audit(public_raw, private_raw, panel_raw=None, raw_root=None, fixture=None):
    public = strict(public_raw)
    private = strict(private_raw)
    if type(public) is not dict or set(public) != {
            "schema", "witness", "commitments"} or public["schema"] != PUBLIC:
        refuse("public keys/schema")
    if type(private) is not dict or set(private) != {
            "schema", "public_sha256", "reveals"} or private["schema"] != PRIVATE:
        refuse("private keys/schema")
    if private["public_sha256"] != sha(public_raw):
        refuse("published public bytes do not match reveal receipt")
    w = public["witness"]
    c = curve_from_witness(w)
    p, a, b, P, n = validate_curve(c)
    targets = w["targets"]
    cms = public["commitments"]
    rv = private["reveals"]
    if (type(targets) is not list or type(cms) is not list or
            type(rv) is not list or not 4 <= len(targets) <= min(128, n-1) or
            len(cms) != len(targets) or len(rv) != len(targets)):
        refuse("target/reveal/commitment population differs")
    qs, tids, salts = set(), set(), set()
    revealed = {}
    for i, (t, m, s) in enumerate(zip(targets, cms, rv)):
        if (type(t) is not dict or set(t) != {"target_id", "Q"} or
                type(m) is not dict or set(m) != {"target_id", "sha256"} or
                type(s) is not dict or set(s) != {
                    "target_id", "scalar", "salt_hex"}):
            refuse("invalid target or reveal fields")
        tid = "ct321-%04d" % i
        if t["target_id"] != tid or m["target_id"] != tid or s["target_id"] != tid:
            refuse("ordered target/commit/reveal identity mismatch")
        Q = group.point(t["Q"], p, a, b)
        if Q in qs or Q is None:
            refuse("duplicate or zero public group element")
        if group.mul(n, Q, p, a) is not None:
            refuse("public Q outside prime subgroup")
        qs.add(Q)
        if tid in tids:
            refuse("duplicate target id")
        tids.add(tid)
        k = group.num(s["scalar"], "scalar", 1)
        if k >= n or group.mul(k, P, p, a) != Q:
            refuse("revealed scalar does not solve public ECDLP")
        salt = s["salt_hex"]
        if type(salt) is not str or SALT.fullmatch(salt) is None or salt in salts:
            refuse("bad or reused commitment nonce")
        salts.add(salt)
        cm = commitment(c["curve_id"], tid, t["Q"], k, salt)
        if type(m["sha256"]) is not str or m["sha256"] != cm:
            refuse("commitment does not match challenge reveal")
        revealed[tid] = k
    summary = {
        "schema": "ct321-conditional-reveal-audit/v1",
        "public_sha256": sha(public_raw),
        "target_count": len(targets),
        "distinct_public_group_points": len(qs),
        "commitments_and_source_group_equations_replayed": len(targets),
        "private_values_disclosed_in_audit": False,
        "blindness_or_independent_custody_authenticated": False,
        "original_native_jacobian_executions": 0,
        "complete_speedup_claim": False,
        "pcc": "unverified",
    }
    if panel_raw is not None:
        if raw_root is None or fixture is None:
            refuse("panel requires raw-root and fixture")
        measured = cold_gate.audit(panel_raw, canonical(w), raw_root, fixture)
        panel = strict(panel_raw)
        used = set()
        for row in panel["runs"]:
            tid = row["target_id"]
            if tid not in revealed or row["expected_scalar"] != revealed[tid]:
                refuse("cold run scalar/target disagrees with blind reveal")
            used.add(tid)
        if used != tids:
            refuse("cold panel did not cover all precommitted targets")
        summary["cold_panel_source_gates_passed"] = measured["schema"]
        summary["cold_panel_processes_checked"] = len(panel["runs"])
        summary["best_baseline_over_candidate_exact"] = measured[
            "provisional_best_baseline_over_candidate_exact"]
        summary["cold_panel_executions_independently_authenticated"] = False
    return summary


def _exclusive(path, raw, mode):
    path = Path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, mode)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as f:
            fd = -1
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        if fd >= 0:
            os.close(fd)
        path.unlink(missing_ok=True)
        raise


def publish(curve, count, pubpath, privpath, draw=None, saltgen=None):
    if os.path.abspath(pubpath) == os.path.abspath(privpath):
        refuse("public and private paths alias")
    pubpath, privpath = Path(pubpath), Path(privpath)
    if pubpath.exists() or pubpath.is_symlink() or privpath.exists() or privpath.is_symlink():
        refuse("refuse to overwrite existing challenge or reveal")
    public, private = generate(curve, count, draw, saltgen)
    pubraw, privraw = canonical(public), canonical(private)
    _exclusive(privpath, privraw, 0o600)
    try:
        _exclusive(pubpath, pubraw, 0o644)
    except BaseException:
        privpath.unlink(missing_ok=True)
        raise
    return {"schema": "ct321-issued-public-digest/v1",
            "public_sha256": sha(pubraw),
            "target_count": count,
            "secret_manifest_not_printed": True,
            "independent_escrow_unverified": True,
            "pcc": "unverified"}


def self_test():
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="ct321-source-only-") as temp:
        root = Path(temp)
        c = {"schema": CURVE, "curve_id": "toy-prime97",
             "p": 97, "a": 2, "b": 3,
             "generator": [3, 6], "subgroup_prime": 5}
        samples = iter(range(4))
        serial = iter(range(4))
        pub, private = generate(c, 4, lambda n: next(samples),
                                lambda n: ("%064x" % next(serial)))
        praw, sraw = canonical(pub), canonical(private)
        result = audit(praw, sraw)
        if result["distinct_public_group_points"] != 4:
            raise AssertionError("distinct toy Q missing")
        if any("salt_hex" in target or "scalar" in target
               for target in pub["witness"]["targets"]):
            raise AssertionError("secret leaked into public challenge")
        mutations = (
            ("changed-Q", "public", lambda x: x["witness"]["targets"][0].update(Q=[3,91])),
            ("changed-commitment", "public", lambda x: x["commitments"][0].update(sha256="0"*64)),
            ("missing-Q", "public", lambda x: x["witness"]["targets"].pop()),
            ("duplicate-Q", "public", lambda x: x["witness"]["targets"][1].update(
                Q=x["witness"]["targets"][0]["Q"])),
            ("wrong-curve", "public", lambda x: x["witness"].update(p=101)),
            ("reveal-scalar", "private", lambda x: x["reveals"][0].update(scalar=2)),
            ("reveal-salt", "private", lambda x: x["reveals"][0].update(salt_hex="f"*64)),
            ("reveal-order", "private", lambda x: x["reveals"].reverse()),
            ("reveal-sha", "private", lambda x: x.update(public_sha256="0"*64)),
            ("invalid-private-key", "private", lambda x: x.update(extra=1)),
        )
        for name, which, mutate in mutations:
            q, s = copy.deepcopy(pub), copy.deepcopy(private)
            if which == "public":
                mutate(q)
                # Simulate hostile rewrite with digest adjusted, not a stale-hash-only test.
                s["public_sha256"] = sha(canonical(q))
            else:
                mutate(s)
            try:
                audit(canonical(q), canonical(s))
            except ValueError:
                rejected += 1
            else:
                raise AssertionError("admitted corruption " + name)
        outpub, outpriv = root/"issue.json", root/"secret.json"
        x = publish(c, 4, outpub, outpriv,
                    iter(range(4)).__next__, lambda n: secrets.token_hex(n))
        if x["target_count"] != 4 or stat.S_IMODE(outpriv.stat().st_mode) != 0o600:
            raise AssertionError("private issue/file mode mismatch")
        if audit(outpub.read_bytes(), outpriv.read_bytes())["target_count"] != 4:
            raise AssertionError("published challenge doesn't audit")
        for path in (outpub, outpriv):
            try:
                publish(c, 4, path, root/"another.json")
            except ValueError:
                rejected += 1
            else:
                raise AssertionError("overwrote existing challenge")
        # Bind a complete synthetic 28-process receipt panel to a preissued
        # public challenge. Clocks, receipts and binaries are fabricated.
        child = root/"panel"
        child.mkdir()
        panel, witness, fixture = cold_gate.make_fixture(
            child, 700, (1, 2, 3, 4),
            [t["target_id"] for t in pub["witness"]["targets"]])
        if witness["curve_id"] != "synthetic-prime97":
            raise AssertionError("unexpected upstream synthetic curve fixture")
        # This is the same *arithmetic* curve as the CT320 fixture but its
        # source-curve identifier must be equal across panel and witness.
        pub2 = copy.deepcopy(pub)
        pub2["witness"]["curve_id"] = witness["curve_id"]
        priv2 = copy.deepcopy(private)
        priv2["public_sha256"] = sha(canonical(pub2))
        for i, item in enumerate(pub2["commitments"]):
            s = priv2["reveals"][i]
            item["sha256"] = commitment(
                witness["curve_id"], item["target_id"],
                pub2["witness"]["targets"][i]["Q"], s["scalar"], s["salt_hex"])
        priv2["public_sha256"] = sha(canonical(pub2))
        valid = audit(canonical(pub2), canonical(priv2),
                      canonical(panel), child, fixture)
        if valid["cold_panel_processes_checked"] != 28:
            raise AssertionError("failed CT320 whole synthetic panel")
        altered = copy.deepcopy(panel)
        altered["runs"][0]["expected_scalar"] = 3
        try:
            audit(canonical(pub2), canonical(priv2),
                  canonical(altered), child, fixture)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError("accepted changed panel answer")
    return {
        "schema": "ct321-source-only-selftest/v1",
        "toy_source_Q_and_commit_reveals": 4,
        "synthetic_seven_arm_receipt_rows": 28,
        "corruptions_and_exclusive-create_refused": rejected,
        "original_native_jacobian_executions": 0,
        "pcc": "unverified",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test", action="store_true")
    g.add_argument("--issue", action="store_true")
    g.add_argument("--audit", action="store_true")
    ap.add_argument("--curve", type=Path)
    ap.add_argument("--public", type=Path)
    ap.add_argument("--private", type=Path)
    ap.add_argument("--count", type=int, default=4)
    ap.add_argument("--panel", type=Path)
    ap.add_argument("--raw-root", type=Path)
    ap.add_argument("--fixture", type=Path)
    args = ap.parse_args()
    if args.self_test:
        out = self_test()
    elif args.issue:
        if args.curve is None or args.public is None or args.private is None:
            refuse("issue requires --curve --public --private")
        out = publish(strict(args.curve.read_bytes()), args.count,
                      args.public, args.private)
    else:
        if args.public is None or args.private is None:
            refuse("audit requires --public --private")
        if (args.panel is None) != (args.raw_root is None) or (
                args.panel is None) != (args.fixture is None):
            refuse("panel, raw-root and fixture must be supplied together")
        out = audit(args.public.read_bytes(), args.private.read_bytes(),
                    args.panel.read_bytes() if args.panel else None,
                    args.raw_root, args.fixture)
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
