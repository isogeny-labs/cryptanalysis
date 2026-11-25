#!/usr/bin/env python3
"""Run the recursive tensor engine or encode a published Certicom target."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import time

from ecc2k import BudgetExceeded, atomic_json, challenge, parameters
from tensor_contraction import ContractionPolicy, TensorContraction, WorkBudget
from tensor_encoding import BinaryCurveEncoding
from tensor_network import BooleanNetwork, Tensor


def recursive_check(args):
    # Two crossing packet orientations exercise modes and the full recovery.
    tensors = []
    for side, edge, values in ((0, 0, (1, 2)), (0, 1, (2, 3)),
                               (1, 0, (3, 4)), (1, 1, (5, 1))):
        tensors.append(Tensor(side, (edge,), lambda bits, values=values: values[bits[0]]))
    network = BooleanNetwork(tuple(tensors))
    policy = ContractionPolicy(experimental=True, forced_a=1, forced_u=1, groups=2,
                               max_depth=1, leaf_edges=0, tight_precision=args.tight_precision)
    engine = TensorContraction(policy, WorkBudget(args.max_operations, args.seconds))
    actual = engine.contract(network, precision=8, labels_override=((0,), (1,), (1,), (0,)))
    expected = (1 * 3 + 2 * 4) * (2 * 5 + 3 * 1)
    if actual != expected:
        raise ArithmeticError("recursive contraction disagrees with independent sum")
    return {"status": "verified", "recursive_contraction": actual, "independent_sum": expected,
            "statistics": engine.stats, "operations": engine.budget.operations,
            "experimental_parameters": True, "subexponential_runtime_claimed": False}


def challenge_network(args):
    if args.instance == "eccp131":
        from eccp import challenge as prime_challenge, validate
        from tensor_prime import PrimeCurveEncoding
        instance, encoding_class = prime_challenge(), PrimeCurveEncoding
        validate(instance)
    else:
        instance, encoding_class = challenge(), BinaryCurveEncoding
    rng = random.Random(args.seed)
    settings = parameters(instance, args.slots)
    prime = int(settings["hash_prime"])
    seeds = [{"prime": prime, "alpha": rng.randrange(1, prime), "beta": rng.randrange(prime),
              "threshold": settings["threshold"]} for _ in range(args.slots)]
    started = time.monotonic()
    encoding = encoding_class(instance.curve)
    points = encoding.relation(instance.Q, seeds, instance.order, instance.cofactor)
    interface = tuple(v for point in points for word in point.words for v in word)
    stats = encoding.circuit.statistics(interface)
    histogram = Counter((m["type"], m["input_bits"], m["ring_bits"], m["transform_length"])
                        for m in stats.pop("multiplication_encodings"))
    stats["multiplication_blocks"] = [{"type": key[0], "input_bits": key[1], "ring_bits": key[2],
                                      "transform_length": key[3], "count": count}
                                     for key, count in histogram.items()]
    engine = TensorContraction(budget=WorkBudget(args.max_operations, args.seconds))
    plan = engine.plan(stats["boolean_network_edges"], stats["boolean_network_edges"] + 1)
    result = {"instance": instance.name, "instance_sha256": instance.fingerprint,
              "target": "published Q", "encoding": "implicit prime-field point coordinates" if args.instance == "eccp131" else "implicit binary point coordinates",
              "factor_base_seed": args.seed, "factor_base_seeds": seeds,
              "network": stats, "contraction_plan": plan,
              "backend": "recursive_cauchy_modes_hermite", "scalar_ring_ell": 1,
              "status": "encoded", "challenge_solved": False,
              "subexponential_runtime_claimed": False,
              "source": "https://github.com/openai/math/blob/main/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026/build/quantitative-contraction.tex"}
    print(json.dumps({"stage": "encoded", "edges": stats["boolean_network_edges"],
                      "variables": stats["variables"], "root_u": plan["root_u"]}), flush=True)
    if not args.plan_only:
        if stats["boolean_network_edges"] > args.max_edges:
            raise BudgetExceeded(f"encoding needs {stats['boolean_network_edges']} edges; max-edges is {args.max_edges}")
        network, mapping = encoding.circuit.builder.compile(interface)
        if network.edges != stats["boolean_network_edges"] or network.degree != stats["maximum_degree"]:
            raise ArithmeticError("compiled network disagrees with encoded graph statistics")
        result["compiled_graph_verified"] = True
        try:
            result["decomposition_count"] = str(engine.contract(network))
            result["status"] = "contracted"
        except BudgetExceeded as exc:
            result["status"], result["reason"] = "budget_exhausted", str(exc)
        result["statistics"] = engine.stats
    result["elapsed_seconds"] = time.monotonic() - started
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["recursive-check", "challenge"])
    parser.add_argument("--instance", choices=["ecc2k130", "eccp131"], default="ecc2k130")
    parser.add_argument("--slots", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--max-operations", type=int, default=2000000)
    parser.add_argument("--max-edges", type=int, default=10000000)
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--tight-precision", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = recursive_check(args) if args.command == "recursive-check" else challenge_network(args)
    except BudgetExceeded as exc:
        result = {"status": "budget_exhausted", "reason": str(exc), "challenge_solved": False}
    if args.output:
        atomic_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in ("verified", "encoded", "contracted") else 2


if __name__ == "__main__":
    raise SystemExit(main())
