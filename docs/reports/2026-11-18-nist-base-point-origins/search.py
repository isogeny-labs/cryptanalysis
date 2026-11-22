#!/usr/bin/env python3
"""Reproduce known base-point origins and test bounded alternative streams.

This is a provenance search, not a cryptographic attack.  A hit is accepted
only when the generated x coordinate equals the published coordinate exactly.
Negative results are scoped to the explicit generator, encoding, and bounds
recorded in the JSON output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


MASK48 = (1 << 48) - 1
DRAND_A = 0x5DEECE66D
DRAND_C = 0xB
FREELIP_M = (1 << 107) - 1
FREELIP_A = pow(3, 121, FREELIP_M)


def unix(when: str) -> int:
    return int(datetime.fromisoformat(when).replace(tzinfo=timezone.utc).timestamp())


@dataclass(frozen=True)
class Curve:
    name: str
    bits: int
    modulus: int
    gx: int
    timestamp: int | None = None
    seed_index: int | None = None
    seed: int | None = None
    calls_per_seed: int = 20
    srand_divisor: int = 1


P224 = (1 << 224) - (1 << 96) + 1
P256 = (1 << 256) - (1 << 224) + (1 << 192) + (1 << 96) - 1
P384 = (1 << 384) - (1 << 128) - (1 << 96) + (1 << 32) - 1
P521 = (1 << 521) - 1

PRIME = [
    Curve("P-224", 224, P224, int("b70e0cbd6bb4bf7f321390b94a03c1d356c21122343280d6", 16), unix("1998-04-03 12:52:07"), 7026, int("bd71344799d5c7fcdc45b59fa3b9ab8f6a948bc5", 16)),
    Curve("P-256", 256, P256, int("6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296", 16), unix("1997-08-16 01:52:34"), 1842, int("c49d360886e704936a6678e1139d26b7819f7e90", 16)),
    Curve("P-384", 384, P384, int("aa87ca22be8b05378eb1c71ef320ad746e1d3b628ba79b9859f741e082542a385502f25dbf55296c3a545e3872760ab7", 16), unix("1997-08-30 14:50:08"), 2688, int("a335926aa319a27a1d00896a6773a4827acdac73", 16)),
    Curve("P-521", 521, P521, int("c6858e06b70404e9cd9e3ecb662395b4429c648139053fb521f828af606b4d3dbaa14b5e77efe75928fe1dc127a2ffa8de3348b3c1856a429bf97e7e31c2e5bd66", 16), unix("1997-08-08 01:12:04"), 1136, int("d09e8800291cb85396cc6717393284aaa0da64ba", 16)),
]


def binary_modulus(bits: int) -> int:
    return 1 << bits


BINARY = [
    Curve("B-163", 163, binary_modulus(163), int("3f0eba16286a2d57ea0991168d4994637e8343e36", 16), seed=int("85e25bfe5c86226cdb12016f7553f9d0e693a268", 16)),
    Curve("B-233", 233, binary_modulus(233), int("fac9dfcbac8313bb2139f1bb755fef65bc391f8b36f8f8eb7371fd558b", 16), unix("1998-04-17 15:24:18"), 155, int("74d59ff07f6b413d0ea14b344b20a2db049b50c3", 16), 5, 2),
    Curve("B-283", 283, binary_modulus(283), int("5f939258db7dd90e1934f8c70b0dfec2eed25b8557eac9c80e2e198f8cdbecd86b12053", 16), unix("1998-04-17 15:27:44"), 32, int("77e2b07370eb0f832a6dd5b62dfc88cd06bb84be", 16), 5, 2),
    Curve("B-409", 409, binary_modulus(409), int("15d4860d088ddb3496b0c6064756260441cde4af1771d4db01ffe5b34e59703dc255a868a1180515603aeab60794e54bb7996a7", 16), unix("1998-04-17 15:30:18"), 60, int("4099b5a457f9d69f79213d094c4bcd4d4262210b", 16), 5, 2),
    Curve("B-571", 571, binary_modulus(571), int("303001d34b856296c16c0d40d3cd7750a93d1d2955fa80aa5f40fc8db7b2abdbde53950f4c0d293cdd711a35b67fb1499ae60038614f1394abfa3b4c850d927e1e7769c8eec2d19", 16), unix("1998-04-17 15:32:08"), 73, int("2aa058f73a0e33ab486b0f610410c53a7f132310", 16), 5, 2),
]

KOBLITZ = [
    Curve("K-163", 163, binary_modulus(163), int("2fe13c0537bbc11acaa07d793de4e6d5e5c94eee8", 16)),
    Curve("K-233", 233, binary_modulus(233), int("17232ba853a7e731af129f22ff4149563a419c26bf50a4c9d6eefad6126", 16)),
    Curve("K-283", 283, binary_modulus(283), int("503213f78ca44883f1a3b8162f188e553cd265f23c1567a16876913b0c2ac2458492836", 16)),
    Curve("K-409", 409, binary_modulus(409), int("60f05f658f49c1ad3ab1890f7184210efd0987e307c84c27accfb8f9f67cc2c460189eb5aaaa62ee222eb1b35540cfe9023746", 16)),
    Curve("K-571", 571, binary_modulus(571), int("26eb7a859923fbc82189631f8103fe4ac9ca2970012d5d46024804801841ca44370958493b205e647da304db4ceb08cbbd1ba39494776fb988b47174dca88c7e2945283a01c8972", 16)),
]


FREELIP_CONTROLS = [
    ("P-192", 20000, 2, (1 << 192) - (1 << 64) - 1, int("64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1", 16), int("188da80eb03090f67cbf20eb43a18800f4ff0afd82ff1012", 16)),
    ("prime239v1", 20420, 3, (1 << 239) - (1 << 143) - (1 << 95) + (1 << 47) - 1, int("6b016c3bdcf18941d0d654921475ca71a9db2fb27d1d37796185c2942c0a", 16), int("ffa963cdca8816ccc33b8642bedf905c3d358573d3f27fbbd3b3cb9aaaf", 16)),
    ("prime239v2", 20507, 2, (1 << 239) - (1 << 143) - (1 << 95) + (1 << 47) - 1, int("617fab6832576cbbfed50d99f0249c3fee58b94ba0038c7ae84c8c832f2c", 16), int("38af09d98727705120c921bb5e9e26296a3cdcf2f35757a0eafd87b830e7", 16)),
    ("prime239v3", 20509, 1, (1 << 239) - (1 << 143) - (1 << 95) + (1 << 47) - 1, int("255705fa2a306654b1f4cb03d6a750a30c250102d4988717d9ba15ab6d3e", 16), int("6768ae8e18bb92cfcf005c949aa2c6d94853d0e660bbf854b1c9505fe95a", 16)),
    ("prime192v2", 20512, 5, (1 << 192) - (1 << 64) - 1, int("cc22d6dfb95c6b25e49c0d6364a4e5980c393aa21668d953", 16), int("eea2bae7e1497842f2de7769cfe9c989c072ad696f48034a", 16)),
    ("prime192v3", 20517, 1, (1 << 192) - (1 << 64) - 1, int("22123dc2395a05caa7423daeccc94760a7d462256bd56916", 16), int("7d29778100c65a1da1783716588dce2b8b4aee8e228f1896", 16)),
]


def freelip_x(seed: int, p: int, b: int) -> tuple[int, int]:
    state = seed

    def limb() -> int:
        nonlocal state
        state = state * FREELIP_A % FREELIP_M
        return state & ((1 << 26) - 1)

    for _ in range(7):
        limb()
    limbs = -(-p.bit_length() // 26) + 1
    tries = 0
    while True:
        x = 0
        for _ in range(limbs):
            x = (x << 26) | limb()
        x %= p
        tries += 1
        if pow((x * x % p) * x - 3 * x + b, (p - 1) // 2, p) == 1:
            return x, tries


def verify_freelip_controls() -> list[dict[str, object]]:
    rows = []
    for name, seed, expected_tries, p, b, expected_x in FREELIP_CONTROLS:
        x, tries = freelip_x(seed, p, b)
        rows.append({
            "curve": name,
            "seed": seed,
            "expected_tries": expected_tries,
            "tries": tries,
            "x_match": x == expected_x,
        })
    return rows


def drand_states(seed: int, count: int) -> list[int]:
    state = ((seed & 0xFFFFFFFF) << 16) | 0x330E
    states = []
    for _ in range(count):
        state = (DRAND_A * state + DRAND_C) & MASK48
        states.append(state)
    return states


def rolling_hits(values: list[int], width: int, curve: Curve, label: str) -> list[dict[str, object]]:
    hits = []
    for limbs in sorted({-(-curve.bits // width), -(-curve.bits // width) + 1}):
        if len(values) < limbs:
            continue
        window_mask = (1 << (width * limbs)) - 1
        value = 0
        for item in values[:limbs]:
            value = (value << width) | item
        for start in range(len(values) - limbs + 1):
            if start:
                value = ((value << width) | values[start + limbs - 1]) & window_mask
            candidate = value % curve.modulus
            if candidate == curve.gx:
                hits.append({"curve": curve.name, "encoding": label, "order": "msb-first", "limbs": limbs, "offset": start})

        value = 0
        for position, item in enumerate(values[:limbs]):
            value |= item << (width * position)
        for start in range(len(values) - limbs + 1):
            if start:
                value = (value >> width) | (values[start + limbs - 1] << (width * (limbs - 1)))
            candidate = value % curve.modulus
            if candidate == curve.gx:
                hits.append({"curve": curve.name, "encoding": label, "order": "lsb-first", "limbs": limbs, "offset": start})
    return hits


def search_lrand_same_stream(extra_calls: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    searches = []
    hits = []
    paired_k = {curve.bits: curve for curve in KOBLITZ}
    for curve in PRIME + [c for c in BINARY if c.timestamp is not None]:
        assert curve.timestamp is not None and curve.seed_index is not None
        seed = curve.timestamp // curve.srand_divisor
        consumed = curve.seed_index * curve.calls_per_seed
        states = drand_states(seed, consumed + extra_calls)
        targets = [curve]
        if curve in BINARY:
            targets.append(paired_k[curve.bits])
        encodings = [
            ("state-top-8", 8, [state >> 40 for state in states]),
            ("lrand48-top-31", 31, [state >> 17 for state in states]),
            ("mrand48-top-32", 32, [state >> 16 for state in states]),
            ("state-low-26", 26, [state & ((1 << 26) - 1) for state in states]),
            ("full-state-48", 48, states),
        ]
        for target in targets:
            for label, width, values in encodings:
                found = rolling_hits(values, width, target, label)
                hits.extend(found)
                searches.append({
                    "curve": target.name,
                    "stream_anchor": curve.name,
                    "srand48_seed": seed,
                    "calls_scanned": len(states),
                    "published_seed_end": consumed,
                    "encoding": label,
                    "width": width,
                    "orders": ["msb-first", "lsb-first"],
                    "limb_counts": sorted({-(-target.bits // width), -(-target.bits // width) + 1}),
                    "hits": len(found),
                })
    return searches, hits


def x962_chain(seed: int, bits: int, counter: int, byte_order: str) -> int:
    blocks = []
    needed = -(-bits // 160) + 1
    for block in range(needed):
        value = (seed + counter + block) % (1 << 160)
        blocks.append(hashlib.sha1(value.to_bytes(20, byte_order)).digest())
    return int.from_bytes(b"".join(blocks), byte_order)


def search_hash_chains(counter_limit: int) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    searches = []
    hits = []
    for curve in PRIME + [c for c in BINARY if c.seed is not None]:
        assert curve.seed is not None
        found = []
        for order in ("big", "little"):
            for counter in range(counter_limit):
                candidate = x962_chain(curve.seed, curve.bits, counter, order) % curve.modulus
                if candidate == curve.gx:
                    found.append({"curve": curve.name, "encoding": "x9.62-sha1-chain", "byte_order": order, "counter": counter})
        hits.extend(found)
        searches.append({
            "curve": curve.name,
            "seed": f"{curve.seed:040x}",
            "counter_range": [0, counter_limit - 1],
            "byte_orders": ["big", "little"],
            "construction": "concatenate SHA1((seed + counter + block) mod 2^160), then reduce modulo field size",
            "hits": len(found),
        })
    return searches, hits


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extra-lrand-calls", type=int, default=50_000)
    parser.add_argument("--hash-counters", type=int, default=65_536)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    controls = verify_freelip_controls()
    lrand_searches, lrand_hits = search_lrand_same_stream(args.extra_lrand_calls)
    hash_searches, hash_hits = search_hash_chains(args.hash_counters)
    report = {
        "schema": "nist-base-point-origin-search/v1",
        "positive_controls": controls,
        "all_positive_controls_pass": all(row["x_match"] and row["tries"] == row["expected_tries"] for row in controls),
        "lrand48_same_stream": {"searches": lrand_searches, "hits": lrand_hits},
        "x962_sha1_chain": {"searches": hash_searches, "hits": hash_hits},
        "claim_boundary": "No hit excludes only the exact generators, encodings, coordinate basis, and bounds listed here.",
    }
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "controls_pass": report["all_positive_controls_pass"],
        "lrand_searches": len(lrand_searches),
        "lrand_hits": len(lrand_hits),
        "hash_searches": len(hash_searches),
        "hash_hits": len(hash_hits),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
