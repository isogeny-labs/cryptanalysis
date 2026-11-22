#!/usr/bin/env python3
"""Reproduce bounded experiments; outputs distinguish demos from the challenge."""

import argparse
import json
from pathlib import Path
import random
import time
from types import SimpleNamespace

from sympy import nextprime

from ecc2k import (BudgetExceeded, FactorBase, MITMRelations, atomic_json, bsgs,
                   challenge, parameters, rho, solve_hashed, toy, validate,
                   verify_certificate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--seconds-per-search", type=float, default=30)
    parser.add_argument("--bsgs-bound", type=lambda x: int(x, 0), default=1 << 32)
    parser.add_argument("--rho-steps", type=int, default=100000)
    parser.add_argument("--tensor-only", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    def save(name, data):
        atomic_json(args.output_dir / name, data)
        print(f"{name}: {data.get('status', data.get('experiment', 'recorded'))}", flush=True)

    def tensor_experiments():
        from tensor_cli import challenge_network, recursive_check
        settings = SimpleNamespace(max_operations=2000000, seconds=args.seconds_per_search,
                                   tight_precision=False, slots=2, seed=1, plan_only=False,
                                   max_edges=10000000)
        save("recursive-tensor-check.json", recursive_check(settings))
        result = solve_hashed(toy(13, 1427), slots=2, backend="tensor_indexed", seed=1,
                              seconds=args.seconds_per_search)
        if result["status"] == "solved":
            result.update(demo_only=True, demo_expected_scalar="1427",
                          certificate_verification=verify_certificate(result))
        save("tensor-demo13.json", result)
        save("challenge-tensor.json", challenge_network(settings))

    if args.tensor_only:
        tensor_experiments()
        return

    instance = challenge()
    save("challenge-validation.json", validate(instance))
    for degree, scalar in ((13, 1427), (19, 114415)):
        demo = solve_hashed(toy(degree, scalar), slots=3, seed=1, seconds=args.seconds_per_search)
        if demo["status"] == "solved":
            demo.update(demo_only=True, demo_expected_scalar=str(scalar),
                        certificate_verification=verify_certificate(demo))
        save(f"demo{degree}.json", demo)
    for slots in (2, 3):
        save(f"challenge-estimate-m{slots}.json", {"instance": instance.name, **parameters(instance, slots)})
    try:
        result = solve_hashed(instance, seconds=args.seconds_per_search)
    except BudgetExceeded as exc:
        result = {"status": "budget_exhausted", "reason": str(exc), "challenge_solved": False}
    save("challenge-hashed-preflight.json", result)

    started, rng = time.monotonic(), random.Random(1729)
    prime = int(nextprime(instance.curve.field.size << 1))
    try:
        bases = [FactorBase.build(instance, prime, 128, rng, started + args.seconds_per_search)
                 for _ in range(3)]
        finder = MITMRelations(instance.curve, bases, 200000, started + args.seconds_per_search)
        result = {"instance": instance.name, "seed": 1729,
                  "experiment": "small factor-base sample, not full-size factor bases",
                  "threshold": 128, "factor_base_sizes": [len(b.points) for b in bases],
                  "bases": [b.as_dict(instance.curve) for b in bases],
                  "target_decomposition": finder.find(instance.Q), "challenge_solved": False,
                  "elapsed_seconds": time.monotonic() - started}
    except BudgetExceeded as exc:
        result = {"status": "budget_exhausted", "reason": str(exc), "challenge_solved": False}
    save("challenge-factor-base-sample.json", result)

    try:
        result = bsgs(instance, args.bsgs_bound, 200000, args.seconds_per_search)
    except BudgetExceeded as exc:
        result = {"status": "budget_exhausted", "reason": str(exc), "challenge_solved": False}
    save("challenge-bsgs.json", result)
    result = rho(instance, args.rho_steps, args.seconds_per_search, 1,
                 args.output_dir / "challenge-rho-checkpoint.json")
    save("challenge-rho.json", result)
    tensor_experiments()
    print(json.dumps({"challenge_solved": result["status"] == "solved",
                      "rho_checkpoint": str(args.output_dir / "challenge-rho-checkpoint.json")}, indent=2))


if __name__ == "__main__":
    main()
