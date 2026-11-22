#!/usr/bin/env python3
"""Deterministic binomial-cloglog and cluster-bootstrap sensitivity artifact.

This is a companion to ``analyze.py``.  It computes, rather than accepts,
signed-beta lower bounds for both co-primary endpoints.  The ordinary fit is a
profile binomial complementary-log-log likelihood.  The cluster sensitivity
resamples prime clusters within bit-size and then source/curve clusters within
each sampled prime, preserving the frozen bit-size design, and reports a
Bonferroni-tail percentile lower bound.

The profile-likelihood and bootstrap bounds are sensitivity analyses, not
finite-sample exact confidence intervals.  The conditional Hoeffding interval
in ``analyze.py`` supplies the separately reported conservative Poisson gate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import random
from statistics import NormalDist
from typing import Any

import analyze


BINOMIAL_MODEL = "S~Binomial(N,q); cloglog(q)=alpha+beta*log(p)"
_PROFILE_CACHE: dict[tuple[Any, ...], str] = {}


def implementation_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _term(n: int, successes: int, eta: float) -> tuple[float, float]:
    """Return log likelihood and its eta derivative, stably."""
    failures = n - successes
    if eta > 40:
        if failures:
            return -math.inf, -math.inf
        return 0.0, 0.0
    if eta < -745:
        if successes:
            return -math.inf, float(successes)
        return 0.0, 0.0
    intensity = math.exp(eta)
    log_q = math.log(-math.expm1(-intensity))
    if intensity < 1e-6:
        d_log_q = 1 - intensity / 2 + intensity * intensity / 12
    elif intensity > 50:
        d_log_q = 0.0
    else:
        d_log_q = intensity / math.expm1(intensity)
    return (
        successes * log_q - failures * intensity,
        successes * d_log_q - failures * intensity,
    )


def _fixed_beta_profile(
    entries: list[tuple[int, int, int]], beta: float
) -> tuple[float, float, float]:
    xs = [math.log(prime) for prime, _, _ in entries]
    center = (min(xs) + max(xs)) / 2
    centered = [x - center for x in xs]

    def scores(intercept: float) -> tuple[float, float, float]:
        likelihood = 0.0
        score_alpha = 0.0
        score_beta = 0.0
        for z, (_, exposure, successes) in zip(centered, entries, strict=True):
            term, derivative = _term(exposure, successes, intercept + beta * z)
            likelihood += term
            score_alpha += derivative
            score_beta += derivative * z
        return likelihood, score_alpha, score_beta

    low, high = -1.0, 1.0
    for _ in range(96):
        if scores(low)[1] > 0:
            break
        low *= 2
    else:
        return -math.inf, -math.inf, math.nan
    for _ in range(96):
        if scores(high)[1] < 0:
            break
        high *= 2
    else:
        return -math.inf, math.inf, math.nan
    for _ in range(72):
        middle = (low + high) / 2
        if scores(middle)[1] > 0:
            low = middle
        else:
            high = middle
    intercept = (low + high) / 2
    likelihood, _, score_beta = scores(intercept)
    return likelihood, intercept, score_beta


def fit_binomial_cloglog(
    entries: list[tuple[int, int, int]],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
) -> dict[str, Any]:
    """Profile the cloglog intercept and return an asymptotic simultaneous LB."""
    total = sum(exposure for _, exposure, _ in entries)
    events = sum(successes for _, _, successes in entries)
    if (
        len({prime for prime, _, _ in entries}) < 2
        or events == 0
        or events == total
    ):
        return {
            "identifiable": False,
            "beta_hat": None,
            "signed_beta_lower": "-inf",
        }

    low, high = -1.0, 1.0
    for _ in range(72):
        score = _fixed_beta_profile(entries, low)[2]
        if math.isfinite(score) and score > 0:
            break
        low *= 2
    else:
        return {
            "identifiable": False,
            "beta_hat": "-inf",
            "signed_beta_lower": "-inf",
        }
    for _ in range(72):
        score = _fixed_beta_profile(entries, high)[2]
        if math.isfinite(score) and score < 0:
            break
        high *= 2
    else:
        return {
            "identifiable": False,
            "beta_hat": "+inf",
            "signed_beta_lower": "-inf",
        }
    for _ in range(72):
        middle = (low + high) / 2
        if _fixed_beta_profile(entries, middle)[2] > 0:
            low = middle
        else:
            high = middle
    beta_hat = (low + high) / 2
    likelihood_hat = _fixed_beta_profile(entries, beta_hat)[0]
    z = NormalDist().inv_cdf(
        1 - familywise_alpha / (2 * simultaneous_hypotheses)
    )
    cutoff = likelihood_hat - 0.5 * z * z

    lower = beta_hat - 1.0
    for _ in range(72):
        likelihood = _fixed_beta_profile(entries, lower)[0]
        if likelihood < cutoff:
            break
        lower = beta_hat - 2 * (beta_hat - lower)
    else:
        return {
            "identifiable": True,
            "beta_hat": beta_hat,
            "signed_beta_lower": "-inf",
        }
    upper = beta_hat
    for _ in range(72):
        middle = (lower + upper) / 2
        if _fixed_beta_profile(entries, middle)[0] >= cutoff:
            upper = middle
        else:
            lower = middle
    return {
        "identifiable": True,
        "beta_hat": beta_hat,
        "signed_beta_lower": (lower + upper) / 2,
    }


def minimum_cluster_replicates(
    familywise_alpha: float, simultaneous_hypotheses: int
) -> int:
    """At least one empirical order statistic in a Bonferroni tail."""
    return math.ceil(2 * simultaneous_hypotheses / familywise_alpha)


def _bootstrap_rows(
    rows: list[dict[str, Any]], rng: random.Random
) -> list[dict[str, Any]]:
    by_bits_prime_cluster: dict[
        int, dict[int, dict[tuple[str, str], list[dict[str, Any]]]]
    ] = {}
    for row in rows:
        prime_clusters = by_bits_prime_cluster.setdefault(row["bits"], {}).setdefault(
            row["p"], {}
        )
        prime_clusters.setdefault(
            (row["source_id"], row["curve_id"]), []
        ).append(row)
    sampled: list[dict[str, Any]] = []
    for bits in sorted(by_bits_prime_cluster):
        prime_map = by_bits_prime_cluster[bits]
        primes = sorted(prime_map)
        # Preserve the bit-size design while treating each prime as a cluster.
        for _ in range(len(primes)):
            prime = primes[rng.randrange(len(primes))]
            clusters = [prime_map[prime][key] for key in sorted(prime_map[prime])]
            # Within each sampled prime, resample source/curve clusters.
            for _ in range(len(clusters)):
                sampled.extend(clusters[rng.randrange(len(clusters))])
    return sampled


def _bootstrap_lower(values: list[float | str], tail_probability: float) -> float | str:
    if not values:
        return "-inf"
    if any(value == "-inf" for value in values):
        negative_infinity_count = sum(value == "-inf" for value in values)
    else:
        negative_infinity_count = 0
    order = max(0, math.ceil(tail_probability * len(values)) - 1)
    if order < negative_infinity_count:
        return "-inf"
    finite = sorted(float(value) for value in values if value != "-inf")
    return finite[order - negative_infinity_count]


def compute_profiles(
    rows: list[dict[str, Any]],
    *,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    cluster_method: str,
    cluster_replicates: int,
    cluster_seed: str,
    useful_event_min_bits: int,
) -> list[dict[str, Any]]:
    if cluster_method != "cluster_bootstrap_cloglog":
        raise analyze.AnalysisError(
            f"unsupported executable cluster method {cluster_method!r}"
        )
    if cluster_replicates <= 0:
        raise analyze.AnalysisError("cluster_replicates must be positive")
    cache_key = (
        analyze.rowset_sha256(rows),
        float(familywise_alpha),
        simultaneous_hypotheses,
        cluster_method,
        cluster_replicates,
        cluster_seed,
        useful_event_min_bits,
    )
    cached = _PROFILE_CACHE.get(cache_key)
    if cached is not None:
        return json.loads(cached)
    series: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in rows:
        if row["stage"] in analyze.INFERENCE_STAGES:
            series.setdefault(analyze._series_key(row), []).append(row)
    profiles: list[dict[str, Any]] = []
    tail_probability = familywise_alpha / (2 * simultaneous_hypotheses)
    combinations = [
        (endpoint, denominator, allocation)
        for endpoint in ("rank_lt_r", "nontrivial_useful_recovery")
        for denominator in ("admitted", "proposed")
        for allocation in ("all_failure", "all_success")
    ]
    for key in sorted(series):
        group = [
            row for row in series[key] if row["bits"] >= useful_event_min_bits
        ]
        series_object = dict(zip(analyze.SERIES_FIELDS, key, strict=True))
        for endpoint, denominator, allocation in combinations:
            entries = analyze._profile_inputs(
                group, endpoint, denominator, allocation
            )
            fit = fit_binomial_cloglog(
                entries,
                familywise_alpha=familywise_alpha,
                simultaneous_hypotheses=simultaneous_hypotheses,
            )
            profiles.append(
                {
                    "series": series_object,
                    "method": "binomial_cloglog",
                    "endpoint": endpoint,
                    "denominator": denominator,
                    "unresolved_allocation": allocation,
                    "signed_beta_lower": fit["signed_beta_lower"],
                }
            )

        bootstrap_values: dict[tuple[str, str, str], list[float | str]] = {
            combination: [] for combination in combinations
        }
        rng = random.Random(f"{cluster_seed}|{key!r}")
        for _ in range(cluster_replicates):
            sampled = _bootstrap_rows(group, rng)
            for combination in combinations:
                endpoint, denominator, allocation = combination
                entries = analyze._profile_inputs(
                    sampled, endpoint, denominator, allocation
                )
                fit = fit_binomial_cloglog(
                    entries,
                    familywise_alpha=familywise_alpha,
                    simultaneous_hypotheses=simultaneous_hypotheses,
                )
                bootstrap_values[combination].append(
                    fit["beta_hat"]
                    if fit["identifiable"] and isinstance(fit["beta_hat"], float)
                    else "-inf"
                )
        for endpoint, denominator, allocation in combinations:
            profiles.append(
                {
                    "series": series_object,
                    "method": "cluster_robust_cloglog",
                    "endpoint": endpoint,
                    "denominator": denominator,
                    "unresolved_allocation": allocation,
                    "signed_beta_lower": _bootstrap_lower(
                        bootstrap_values[(endpoint, denominator, allocation)],
                        tail_probability,
                    ),
                }
            )
    _PROFILE_CACHE[cache_key] = json.dumps(
        profiles,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return json.loads(_PROFILE_CACHE[cache_key])


def compute_artifact(
    rows: list[dict[str, Any]],
    *,
    artifact_id: str,
    freeze_manifest_sha256: str,
    familywise_alpha: float,
    simultaneous_hypotheses: int,
    cluster_replicates: int,
    cluster_seed: str,
    useful_event_min_bits: int,
) -> dict[str, Any]:
    validated = [analyze.validate_row(row) for row in rows]
    return {
        "schema": analyze.ROBUSTNESS_SCHEMA,
        "artifact_id": artifact_id,
        "input_rowset_sha256": analyze.rowset_sha256(validated),
        "protocol_sha256": analyze.protocol_sha256(),
        "sensitivity_implementation_sha256": implementation_sha256(),
        "freeze_manifest_sha256": freeze_manifest_sha256,
        "familywise_alpha": familywise_alpha,
        "simultaneous_hypotheses": simultaneous_hypotheses,
        "binomial_model": BINOMIAL_MODEL,
        "cluster_method": "cluster_bootstrap_cloglog",
        "cluster_keys": ["bits", "p", "source_id", "curve_id"],
        "cluster_replicates": cluster_replicates,
        "minimum_cluster_replicates": minimum_cluster_replicates(
            familywise_alpha, simultaneous_hypotheses
        ),
        "cluster_seed": cluster_seed,
        "useful_event_min_bits": useful_event_min_bits,
        "complete": True,
        "profiles": compute_profiles(
            validated,
            familywise_alpha=familywise_alpha,
            simultaneous_hypotheses=simultaneous_hypotheses,
            cluster_method="cluster_bootstrap_cloglog",
            cluster_replicates=cluster_replicates,
            cluster_seed=cluster_seed,
            useful_event_min_bits=useful_event_min_bits,
        ),
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="strict analysis-row JSONL")
    parser.add_argument("output", type=Path, help="sensitivity JSON")
    parser.add_argument("--artifact-id", required=True)
    parser.add_argument("--familywise-alpha", type=float, default=0.05)
    parser.add_argument("--simultaneous-hypotheses", type=int, required=True)
    parser.add_argument("--cluster-replicates", type=int, required=True)
    parser.add_argument("--cluster-seed", required=True)
    parser.add_argument("--freeze-manifest", required=True, type=Path)
    args = parser.parse_args()
    try:
        required_replicates = minimum_cluster_replicates(
            args.familywise_alpha, args.simultaneous_hypotheses
        )
        if args.cluster_replicates < required_replicates:
            raise analyze.AnalysisError(
                "cluster bootstrap has inadequate Bonferroni-tail resolution; "
                f"need at least {required_replicates} replicates"
            )
        freeze_object = analyze.read_json_object(args.freeze_manifest)
        analyze.validate_freeze_analysis(
            freeze_object,
            familywise_alpha=args.familywise_alpha,
            simultaneous_hypotheses=args.simultaneous_hypotheses,
            cluster_method="cluster_bootstrap_cloglog",
            cluster_replicates=args.cluster_replicates,
            cluster_seed=args.cluster_seed,
        )
        artifact = compute_artifact(
            analyze.read_jsonl(args.input),
            artifact_id=args.artifact_id,
            freeze_manifest_sha256=_sha256_file(args.freeze_manifest),
            familywise_alpha=args.familywise_alpha,
            simultaneous_hypotheses=args.simultaneous_hypotheses,
            cluster_replicates=args.cluster_replicates,
            cluster_seed=args.cluster_seed,
            useful_event_min_bits=freeze_object["analysis"][
                "useful_event_min_bits"
            ],
        )
    except (analyze.AnalysisError, OSError) as exc:
        parser.error(str(exc))
    args.output.write_text(analyze.render_json(artifact), encoding="utf-8")


if __name__ == "__main__":
    main()
