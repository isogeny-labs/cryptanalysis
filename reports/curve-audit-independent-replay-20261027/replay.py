#!/usr/bin/env python3
"""Independent exact-integer replay of two archived curve-audit certificates.

This checker does not import the producer's Rust or Sage code. It checks the
committed source/input identities, recursive Lucas certificates, generator
arithmetic, candidate-order bounds, archived field consistency, and mutations.
It does not compute the actual curve cardinality independently of Hasse's
theorem and Lagrange's theorem or prove the Rust implementation correct.
"""

from __future__ import annotations

import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PIN = json.loads((HERE / "input-hashes.json").read_text())
BASE = "bindings/rust/curve-audit/examples/nist-p"
SMALL_LIMIT = 10**12


class CheckFailure(Exception):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise CheckFailure(reason)


def blob(path: str) -> bytes:
    data = subprocess.check_output(
        ["git", "show", f"{PIN['producer_commit']}:{path}"], cwd=HERE
    )
    actual = hashlib.sha256(data).hexdigest()
    require(actual == PIN["sha256"][path], f"SHA-256 mismatch: {path}")
    return data


def strict_json(data: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=unique)


def integer(text: Any) -> int:
    require(isinstance(text, str), "integer must be a string")
    if text.startswith("0x") or text.startswith("-0x"):
        return int(text, 16)
    require(text.lstrip("-").isdigit(), "invalid decimal integer")
    return int(text, 10)


def exact_small_prime(n: int) -> bool:
    require(0 <= n <= SMALL_LIMIT, "small-prime checker outside its domain")
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    for d in range(3, math.isqrt(n) + 1, 2):
        if n % d == 0:
            return False
    return True


def verify_prime_node(node: Any, expected: int, counters: dict[str, int], depth: int = 0) -> None:
    require(isinstance(node, dict), "prime node is not an object")
    require(depth <= 64, "certificate exceeds depth limit")
    counters["nodes"] += 1
    require(counters["nodes"] <= 256, "certificate exceeds node limit")
    n = integer(node.get("n"))
    require(n == expected, "certificate node does not match expected integer")
    if n <= SMALL_LIMIT:
        require(set(node) == {"n", "small"}, "small node has invalid keys")
        require(node["small"] is True and exact_small_prime(n), "small node is not prime")
        counters["small_nodes"] += 1
        return

    require(set(node) == {"n", "a", "factors", "sub"}, "large node has invalid keys")
    a = integer(node["a"])
    require(1 < a < n, "Lucas witness out of range")
    factors = node["factors"]
    sub = node["sub"]
    require(isinstance(factors, list) and 0 < len(factors) <= 128, "invalid factor list")
    require(isinstance(sub, list) and len(sub) <= 128, "invalid subcertificate list")
    product = 1
    seen: set[int] = set()
    large: list[int] = []
    for pair in factors:
        require(isinstance(pair, list) and len(pair) == 2, "factor is not a pair")
        q = integer(pair[0])
        e = pair[1]
        require(type(e) is int and 1 <= e <= 1024, "invalid factor exponent")
        require(1 < q < n and q not in seen, "invalid or repeated factor")
        seen.add(q)
        product *= q**e
        require(product <= n - 1, "factor product exceeds n-1")
        if q <= SMALL_LIMIT:
            require(exact_small_prime(q), "factor is not prime")
            counters["small_factors"] += 1
        else:
            large.append(q)
        require(pow(a, (n - 1) // q, n) != 1, "Lucas witness has insufficient order")
    require(product == n - 1, "factor product differs from n-1")
    require(pow(a, n - 1, n) == 1, "Lucas witness fails Fermat relation")
    require(len(large) == len(sub), "large-factor subcertificate count differs")
    for q, child in zip(large, sub):
        verify_prime_node(child, q, counters, depth + 1)


def verify_cert(cert: Any, input_bytes: bytes, p: int, r: int) -> dict[str, int]:
    require(isinstance(cert, dict), "certificate root is not an object")
    require(set(cert) == {"schema", "input_sha256", "field_characteristic", "selected_order"},
            "certificate root has invalid keys")
    require(cert["schema"] == "ca.prime_certificates.v1", "wrong certificate schema")
    require(cert["input_sha256"] == hashlib.sha256(input_bytes).hexdigest(),
            "certificate is bound to different input bytes")
    counters = {"nodes": 0, "small_nodes": 0, "small_factors": 0}
    verify_prime_node(cert["field_characteristic"], p, counters)
    verify_prime_node(cert["selected_order"], r, counters)
    return counters


Point = tuple[int, int] | None


def add(left: Point, right: Point, p: int, a: int) -> Point:
    if left is None:
        return right
    if right is None:
        return left
    x1, y1 = left
    x2, y2 = right
    if x1 == x2 and (y1 + y2) % p == 0:
        return None
    if x1 == x2:
        numerator, denominator = (3 * x1 * x1 + a) % p, (2 * y1) % p
    else:
        numerator, denominator = (y2 - y1) % p, (x2 - x1) % p
    require(denominator != 0, "zero addition denominator")
    inverse = pow(denominator, p - 2, p)
    require((inverse * denominator) % p == 1, "invalid denominator inverse")
    slope = numerator * inverse % p
    x3 = (slope * slope - x1 - x2) % p
    y3 = (slope * (x1 - x3) - y1) % p
    return x3, y3


def multiply(point: Point, scalar: int, p: int, a: int) -> Point:
    require(scalar >= 0, "negative scalar")
    acc: Point = None
    base = point
    while scalar:
        if scalar & 1:
            acc = add(acc, base, p, a)
        base = add(base, base, p, a)
        scalar >>= 1
    return acc


def curve_checks(record: Any, cert: Any, raw: bytes) -> dict[str, Any]:
    p = integer(record["field"]["characteristic"])
    r = integer(record["subgroup"]["order"])
    n = integer(record["curve_order"])
    a = integer(record["curve"]["a"]) % p
    b = integer(record["curve"]["b"]) % p
    x = integer(record["subgroup"]["generator"]["x"])
    y = integer(record["subgroup"]["generator"]["y"])
    counters = verify_cert(cert, raw, p, r)
    require(p > 3 and 0 <= x < p and 0 <= y < p, "unsupported or noncanonical field/point")
    require((4 * pow(a, 3, p) + 27 * pow(b, 2, p)) % p != 0, "singular curve")
    require((y * y - x * x * x - a * x - b) % p == 0, "generator is off curve")
    require(multiply((x, y), r, p, a) is None, "prime order does not annihilate generator")
    require(n % r == 0, "candidate order not divisible by selected prime")
    delta = abs(n - (p + 1))
    require(delta * delta <= 4 * p, "candidate is outside Hasse interval")
    require(r * r > 16 * p, "selected prime does not exceed Hasse width")
    return {
        "p": str(p), "r": str(r), "candidate_order": str(n),
        "discriminant_nonzero": True, "generator_on_curve": True,
        "r_times_generator_is_infinity": True, "candidate_divisible": True,
        "candidate_hasse_bound": True, "strict_spacing": True,
        "trace": str(p + 1 - n), "twist_order": str(2 * p + 2 - n),
        "certificate_counts": counters,
    }


def must_reject(label: str, fn: Any) -> dict[str, str]:
    try:
        fn()
    except CheckFailure as exc:
        return {"name": label, "status": "rejected", "reason": str(exc)}
    raise CheckFailure(f"negative control unexpectedly accepted: {label}")


def run() -> dict[str, Any]:
    # Check every frozen source, input, certificate, and archived receipt blob.
    blobs = {path: blob(path) for path in PIN["sha256"]}
    source_digest = hashlib.sha256()
    for name in ("arithmetic.rs", "certificates.rs", "input.rs", "main.rs"):
        source_digest.update(name.encode("ascii") + b"\0")
        source_digest.update(blobs["bindings/rust/curve-audit/src/" + name])
    compiled_source_hash = source_digest.hexdigest()
    curves: dict[str, Any] = {}
    for label in ("192", "224"):
        stem = BASE + label
        raw = blobs[stem + ".json"]
        cert = strict_json(blobs[stem + "-pratt.json"])
        record = strict_json(raw)
        audit = strict_json(blobs[stem + "-audit.json"])
        sage = strict_json(blobs[stem + "-sage-replay.json"])
        result = curve_checks(record, cert, raw)
        require(audit["auditor_source_sha256"] == compiled_source_hash,
                "archived auditor source digest")
        require(audit["input_sha256"] == hashlib.sha256(raw).hexdigest(), "archived audit input hash")
        require(audit["validation"]["prime_certificate_sha256"] ==
                hashlib.sha256(blobs[stem + "-pratt.json"]).hexdigest(), "archived audit cert hash")
        require(audit["validation"]["curve_order_status"] ==
                "hasse_unique_multiple_certificate", "archived audit status")
        for field in ("curve_nonsingular", "generator_on_curve", "generator_exact_order",
                      "r_times_generator_is_infinity", "hasse_claim_in_interval",
                      "hasse_unique_multiple_bound", "selected_order_divides_curve_order"):
            require(audit["validation"][field] is True, f"archived audit {field}")
        require(audit["derived"]["curve_order"] == result["candidate_order"], "archived audit order")
        require(audit["derived"]["trace"] == result["trace"], "archived audit trace")
        require(audit["derived"]["quadratic_twist_order"] == result["twist_order"],
                "archived audit twist")
        require(sage["input_sha256"] == hashlib.sha256(raw).hexdigest(), "archived Sage input hash")
        require(sage["prime_certificate_sha256"] ==
                hashlib.sha256(blobs[stem + "-pratt.json"]).hexdigest(), "archived Sage cert hash")
        require(sage["curve_order"] == result["candidate_order"], "archived Sage order")
        require(sage["generator_order"] == result["r"], "archived Sage generator order")
        require(sage["trace"] == result["trace"], "archived Sage trace")
        require(sage["twist_order"] == result["twist_order"], "archived Sage twist")
        require(sage["p_prime"] is True and sage["r_prime"] is True and
                sage["matches_claim"] is True, "archived Sage status")

        bad_hash = json.loads(json.dumps(cert))
        bad_hash["input_sha256"] = "0" * 64
        bad_witness = json.loads(json.dumps(cert))
        bad_witness["field_characteristic"]["a"] = "1"
        bad_factor = json.loads(json.dumps(cert))
        bad_factor["field_characteristic"]["factors"][0][1] += 1
        bad_point = json.loads(json.dumps(record))
        bad_point["subgroup"]["generator"] = {"x": "0", "y": "0"}
        bad_order = json.loads(json.dumps(record))
        bad_order["curve_order"] = str(int(result["candidate_order"]) + 1)
        p, r = int(result["p"]), int(result["r"])
        controls = [
            must_reject("wrong_input_hash", lambda: verify_cert(bad_hash, raw, p, r)),
            must_reject("witness_one", lambda: verify_cert(bad_witness, raw, p, r)),
            must_reject("factor_exponent_plus_one", lambda: verify_cert(bad_factor, raw, p, r)),
            must_reject("off_curve_generator", lambda: curve_checks(bad_point, cert, raw)),
            must_reject("candidate_order_plus_one", lambda: curve_checks(bad_order, cert, raw)),
        ]
        result["controls"] = controls
        result["archived_field_consistency"] = True
        curves["P-" + label] = result
    return {
        "schema": "cryptanalysis.curve_audit_independent_replay.v1",
        "producer_commit": PIN["producer_commit"],
        "verifier": "replay.py",
        "python_version": platform.python_version(),
        "input_manifest_sha256": hashlib.sha256((HERE / "input-hashes.json").read_bytes()).hexdigest(),
        "auditor_source_sha256": compiled_source_hash,
        "curves": curves,
        "claim_boundary": "Independent exact-integer certificate and point replay; archived Rust/Sage fields consistent. This does not authenticate archived execution or replace an independent finite-field cardinality computation or full Lean bridge.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
