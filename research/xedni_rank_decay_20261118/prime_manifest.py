#!/usr/bin/env python3
"""Deterministic prime manifest for the prospective Xedni rank-decay panel."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SCHEMA = "xedni-rank-decay-primes/v1"
MASTER_SEED = "xedni-rank-decay-20261118-v1"
BIT_SIZES = tuple(range(16, 33, 2))
SLOTS = 3
MR_BASES = (2, 3, 5, 7, 11, 13, 17)


def is_prime_u32(value: int) -> bool:
    """Deterministic Miller--Rabin for integers in the unsigned 32-bit range."""
    if not 0 <= value <= 2**32 - 1:
        raise ValueError("is_prime_u32 input is outside the unsigned 32-bit range")
    if value < 2:
        return False
    for prime in MR_BASES:
        if value == prime:
            return True
        if value % prime == 0:
            return False
    odd = value - 1
    shifts = 0
    while odd % 2 == 0:
        odd //= 2
        shifts += 1
    for base in MR_BASES:
        if base >= value:
            continue
        witness = pow(base, odd, value)
        if witness in (1, value - 1):
            continue
        for _ in range(shifts - 1):
            witness = witness * witness % value
            if witness == value - 1:
                break
        else:
            return False
    return True


def slot_candidate(seed: str, bits: int, slot: int) -> int:
    if bits not in BIT_SIZES:
        raise ValueError(f"unsupported bit size {bits}")
    digest = hashlib.sha256(f"{seed}|{bits}|{slot}".encode()).digest()
    low = 1 << (bits - 1)
    candidate = low | (int.from_bytes(digest, "big") % low) | 1
    if candidate >= 1 << bits:
        raise AssertionError("candidate escaped its bit-size interval")
    return candidate


def derive_primes(seed: str = MASTER_SEED):
    rows = []
    for bits in BIT_SIZES:
        selected = set()
        low = 1 << (bits - 1)
        for slot in range(SLOTS):
            start = slot_candidate(seed, bits, slot)
            candidate = start
            decrements = 0
            while candidate >= low:
                if candidate not in selected and is_prime_u32(candidate):
                    break
                candidate -= 2
                decrements += 1
            else:
                raise RuntimeError(f"no distinct {bits}-bit prime for slot {slot}")
            selected.add(candidate)
            rows.append(
                {
                    "bits": bits,
                    "slot": slot,
                    "hash_candidate": start,
                    "downward_odd_steps": decrements,
                    "prime": candidate,
                }
            )
    return rows


def source_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def manifest(seed: str = MASTER_SEED):
    return {
        "schema": SCHEMA,
        "master_seed": seed,
        "bit_sizes": list(BIT_SIZES),
        "slots_per_bit_size": SLOTS,
        "derivation": "sha256(seed|bits|slot), set top bit and odd bit, scan downward by two",
        "miller_rabin_bases": list(MR_BASES),
        "generator_sha256": source_sha256(),
        "primes": derive_primes(seed),
    }


def render(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def validate(value) -> None:
    if value.get("schema") != SCHEMA or value.get("master_seed") != MASTER_SEED:
        raise ValueError("manifest schema or seed mismatch")
    if value.get("generator_sha256") != source_sha256():
        raise ValueError("prime generator hash mismatch")
    if value != manifest(MASTER_SEED):
        raise ValueError("prime manifest differs from deterministic derivation")
    rows = value["primes"]
    if len(rows) != len(BIT_SIZES) * SLOTS:
        raise ValueError("wrong prime count")
    for bits in BIT_SIZES:
        primes = [row["prime"] for row in rows if row["bits"] == bits]
        if len(primes) != SLOTS or len(set(primes)) != SLOTS:
            raise ValueError(f"non-distinct or missing primes at {bits} bits")
        if any(prime.bit_length() != bits or not is_prime_u32(prime) for prime in primes):
            raise ValueError(f"invalid prime at {bits} bits")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("print", "write", "check"))
    parser.add_argument("path", nargs="?", type=Path)
    args = parser.parse_args()
    value = manifest()
    if args.command == "print":
        if args.path is not None:
            parser.error("print takes no path")
        print(render(value), end="")
        return
    if args.path is None:
        parser.error(f"{args.command} requires a path")
    if args.command == "write":
        args.path.write_text(render(value))
        return
    stored = json.loads(args.path.read_text())
    validate(stored)
    print(json.dumps({"status": "PASS", "path": str(args.path), "primes": len(stored["primes"])}, sort_keys=True))


if __name__ == "__main__":
    main()
