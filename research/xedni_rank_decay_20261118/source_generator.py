#!/usr/bin/env python3
"""Fresh finite-field source generator for Xedni rank-decay experiments."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

from field import (
    HashStream,
    generate_curve,
    on_curve,
    point_mul,
    point_neg,
    sample_point,
)
from prime_manifest import is_prime_u32


SCHEMA = "xedni-rank-decay-source/v1"


class BackendUnavailable(RuntimeError):
    pass


class PariBackend:
    name = "pari-gp-ellcard-factor"

    def __init__(self, executable: str = "gp", timeout_seconds: int = 60):
        resolved = shutil.which(executable)
        if resolved is None:
            raise BackendUnavailable(f"PARI/GP executable not found: {executable}")
        self.executable = resolved
        self.timeout_seconds = timeout_seconds
        self.command = [self.executable, "-q", "-f"]

    def cardinality_and_factors(self, prime: int, a: int, b: int):
        program = (
            f"E=ellinit([Mod({a},{prime}),Mod({b},{prime})]);\n"
            "N=ellcard(E); F=factor(N); print(N); "
            "for(i=1,matsize(F)[1],print(F[i,1],\" \",F[i,2]));\nquit\n"
        )
        completed = subprocess.run(
            self.command,
            input=program,
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"PARI ellcard/factor failed with exit {completed.returncode}: "
                f"{completed.stderr.strip()}"
            )
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if not lines or not re.fullmatch(r"[0-9]+", lines[0]):
            raise RuntimeError("PARI output did not begin with a cardinality")
        cardinality = int(lines[0])
        factors = []
        for line in lines[1:]:
            match = re.fullmatch(r"([0-9]+)\s+([0-9]+)", line)
            if match is None:
                raise RuntimeError(f"unparseable PARI factor line: {line!r}")
            factors.append((int(match.group(1)), int(match.group(2))))
        validate_factorization(cardinality, factors)
        return cardinality, factors


class PariContainerBackend(PariBackend):
    def __init__(
        self,
        image: str,
        runtime: str = "docker",
        timeout_seconds: int = 60,
    ):
        resolved = shutil.which(runtime)
        if resolved is None:
            raise BackendUnavailable(f"container runtime not found: {runtime}")
        if not image:
            raise ValueError("PARI container image must be nonempty")
        self.executable = resolved
        self.image = image
        self.timeout_seconds = timeout_seconds
        self.name = f"pari-container-ellcard-factor:{image}"
        self.command = [
            resolved,
            "run",
            "--rm",
            "-i",
            "--network=none",
            "--entrypoint",
            "gp",
            image,
            "-q",
            "-f",
        ]


def validate_factorization(cardinality: int, factors) -> None:
    product = 1
    previous = 1
    for prime, exponent in factors:
        if prime <= previous or exponent <= 0 or not _factor_is_prime(prime):
            raise ValueError("invalid ordered prime-power factorization")
        product *= prime**exponent
        previous = prime
    if product != cardinality:
        raise ValueError("factorization does not multiply to the cardinality")


def _factor_is_prime(value: int) -> bool:
    if value <= 2**32 - 1:
        return is_prime_u32(value)
    if value < 2 or value % 2 == 0:
        return False
    divisor = 3
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def exact_point_order(point, a: int, prime: int, cardinality: int, factors):
    if point_mul(cardinality, point, a, prime) is not None:
        raise ArithmeticError("reported cardinality does not annihilate sampled point")
    order = cardinality
    for factor, exponent in factors:
        for _ in range(exponent):
            if order % factor or point_mul(order // factor, point, a, prime) is not None:
                break
            order //= factor
    if point_mul(order, point, a, prime) is not None:
        raise ArithmeticError("derived point order does not annihilate point")
    return order


def hasse_radius(prime: int) -> int:
    """Largest integral Hasse deviation: floor(2*sqrt(p))."""
    return math.isqrt(4 * prime)


def choose_source_subgroup(cardinality: int, factors, max_r: int):
    eligible = [factor for factor, _ in factors if factor >= 2 * max_r + 1]
    if not eligible:
        raise RuntimeError("cardinality has no sufficiently large prime subgroup")
    subgroup_order = max(eligible)
    return subgroup_order, cardinality // subgroup_order


def generate_source(
    prime: int,
    family: str,
    source_index: int,
    max_r: int,
    master_seed: str,
    backend,
):
    if not is_prime_u32(prime):
        raise ValueError("source modulus is not a certified 32-bit prime")
    if source_index < 0:
        raise ValueError("source_index must be nonnegative")
    if not 2 <= max_r <= 9:
        raise ValueError("max_r must be in [2,9]")
    seed = f"{master_seed}|p={prime}|family={family}|source={source_index}"
    stream = HashStream(seed)
    a, b, curve_attempts = generate_curve(stream, prime, family)
    cardinality, factors = backend.cardinality_and_factors(prime, a, b)
    validate_factorization(cardinality, factors)
    radius = hasse_radius(prime)
    if not prime + 1 - radius <= cardinality <= prime + 1 + radius:
        raise ArithmeticError("reported cardinality violates the Hasse bound")

    subgroup_order, source_cofactor = choose_source_subgroup(
        cardinality, factors, max_r
    )

    base = None
    point_attempts = 0
    for _ in range(512):
        candidate, attempts = sample_point(stream, prime, a, b)
        point_attempts += attempts
        projected = point_mul(source_cofactor, candidate, a, prime)
        if projected is not None:
            if point_mul(subgroup_order, projected, a, prime) is not None:
                raise ArithmeticError("cofactor projection missed the source subgroup")
            base = projected
            break
    if base is None:
        raise RuntimeError("prime-subgroup projection stayed trivial within fixed cap")

    scalar_classes = set()
    scalars = []
    scalar_attempts = 0
    while len(scalars) < max_r:
        scalar_attempts += 1
        if scalar_attempts > 4096:
            raise RuntimeError("scalar sampling exhausted its fixed attempt cap")
        if len(scalar_classes) >= (subgroup_order - 1) // 2:
            raise RuntimeError("point order has too few sign classes")
        scalar = 1 + stream.randbelow(subgroup_order - 1)
        canonical = min(scalar, subgroup_order - scalar)
        if canonical in scalar_classes:
            continue
        scalar_classes.add(canonical)
        scalars.append(scalar)
    points = [point_mul(scalar, base, a, prime) for scalar in scalars]
    if any(point is None or not on_curve(point, a, b, prime) for point in points):
        raise ArithmeticError("generated tuple contains an invalid point")
    if len({point for point in points} | {point_neg(point, prime) for point in points}) != 2 * max_r:
        raise ArithmeticError("generated tuple is not distinct up to sign")

    prefix_order = list(range(max_r))
    stream.shuffle(prefix_order)
    prefixes = {
        str(r): {
            "indices": prefix_order[:r],
            "target_index": prefix_order[r - 1],
        }
        for r in range(2, max_r + 1)
    }
    return {
        "schema": SCHEMA,
        "master_seed": master_seed,
        "source_id": f"p{prime}-{family}-{source_index:08d}",
        "source_index": source_index,
        "p": prime,
        "bits": prime.bit_length(),
        "family": family,
        "curve": {"a": a, "b": b, "generation_attempts": curve_attempts},
        "cardinality": cardinality,
        "cardinality_factors": [[q, e] for q, e in factors],
        "cardinality_backend": getattr(backend, "name", type(backend).__name__),
        "source_subgroup_order": subgroup_order,
        "source_cofactor": source_cofactor,
        "base_point": list(base),
        "base_point_order": subgroup_order,
        "point_sampling_attempts": point_attempts,
        "max_r": max_r,
        "ordered_scalars": scalars,
        "ordered_points": [list(point) for point in points],
        "prefix_permutation": prefix_order,
        "prefixes": prefixes,
    }


def render_json(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


def render_jsonl(values) -> str:
    return "".join(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
        for value in values
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p", type=int, required=True)
    parser.add_argument("--family", choices=("generic", "j0"), required=True)
    parser.add_argument("--source-index", type=int, required=True)
    parser.add_argument("--max-r", type=int, default=9)
    parser.add_argument("--master", default="xedni-rank-decay-20261118-v1")
    parser.add_argument("--gp", default="gp")
    parser.add_argument("--pari-container-image")
    parser.add_argument("--container-runtime", default="docker")
    parser.add_argument("--format", choices=("json", "jsonl"), default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    backend = (
        PariContainerBackend(args.pari_container_image, args.container_runtime)
        if args.pari_container_image
        else PariBackend(args.gp)
    )
    value = generate_source(
        args.p,
        args.family,
        args.source_index,
        args.max_r,
        args.master,
        backend,
    )
    rendered = render_json(value) if args.format == "json" else render_jsonl([value])
    if args.output is None:
        print(rendered, end="")
    else:
        args.output.write_text(rendered)


if __name__ == "__main__":
    main()
