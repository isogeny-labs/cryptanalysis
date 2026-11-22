#!/usr/bin/env python3
"""CT190 block-intercept diagnostic for CT188 physical crossover times.

Only accepts source-level/untrusted times. Neither PCC, actual native measurements
nor a complete ECDLP timing claim follows. [pcc:unverified]
"""
import json
import math
import statistics
from fractions import Fraction

import ct188_physical_crossover_design as original

SCHEMA = "ct190-physical-crossover-block-fixed-effects/v1"
PARAMETERS = ("period_1", "period_2", "period_3",
              "physical_B", "previous_B", "physical_B_x_previous_B")
N_BLOCK_COLUMNS = original.BLOCKS + len(PARAMETERS)
EXPECTED_ROSTER_SHA256 = "1bc8c26a01e7952e57d944fd535c9832607f2ab7bcc910342ad704171ab67af1"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def _design(packet):
    """Exact integer rows: eight block dummies + six treatment/nuisance terms."""
    full = []
    centered = []
    for block in range(original.BLOCKS):
        sequence = original.order(block, packet)[:4]
        x = [original.model_row(sequence, pos)[1:] for pos in range(4)]
        sums = [sum(row[col] for row in x) for col in range(6)]
        for row in x:
            full.append(tuple(int(b == block) for b in range(original.BLOCKS)) +
                        tuple(row))
            # Multiplication by four avoids floating point in the rank proof.
            centered.append(tuple(4 * row[col] - sums[col] for col in range(6)))
    require(original.exact_rank(full) == N_BLOCK_COLUMNS,
            "block/nuisance model not identified over the rationals")
    require(original.exact_rank(centered) == len(PARAMETERS),
            "within-block treatment model not identified over the rationals")
    return full, centered


def previous_b_roster_share(packet):
    """Exact, model-based standardization weight from frozen treatment slots."""
    prior = [original.model_row(original.order(block, packet)[:4], pos)[5]
             for block in range(original.BLOCKS) for pos in range(4)]
    require(len(prior) == 32 and sum(prior) == 12,
            "CT188 previous-B roster mix changed; refuse model standardization")
    return Fraction(sum(prior), len(prior))


def assert_design():
    require(original.assert_design() is True and
            original.roster_sha256() == EXPECTED_ROSTER_SHA256,
            "original immutable physical roster changed")
    for packet in range(original.PACKETS):
        _design(packet)
        require(previous_b_roster_share(packet) == Fraction(3, 8),
                "unexpected previous-B standardization weight")
    return True


def _solve(rows, ys):
    """Solve 6-column within-block OLS with checked finite arithmetic."""
    n = len(PARAMETERS)
    require(len(rows) == len(ys) == original.BLOCKS * 4,
            "unexpected per-packet treatment population")
    gram = [[sum(row[i] * row[j] for row in rows) for j in range(n)]
            for i in range(n)]
    rhs = [sum(row[i] * value for row, value in zip(rows, ys))
           for i in range(n)]
    for pivot in range(n):
        best = max(range(pivot, n), key=lambda r: abs(gram[r][pivot]))
        require(abs(gram[best][pivot]) > 1e-10,
                "singular within-block timing design")
        gram[pivot], gram[best] = gram[best], gram[pivot]
        rhs[pivot], rhs[best] = rhs[best], rhs[pivot]
        scale = gram[pivot][pivot]
        gram[pivot] = [value / scale for value in gram[pivot]]
        rhs[pivot] /= scale
        for r in range(n):
            if r == pivot:
                continue
            factor = gram[r][pivot]
            if factor:
                gram[r] = [a - factor * b for a, b in zip(gram[r], gram[pivot])]
                rhs[r] -= factor * rhs[pivot]
    require(all(math.isfinite(value) for value in rhs),
            "nonfinite treatment or carryover coefficient")
    return dict(zip(PARAMETERS, rhs))


def analyze_untrusted_times(records):
    """Return legacy CT188 and new block-fixed-effect diagnostics side-by-side.

    A validated complete roster is required, but record integrity is a
    source-only claim. A/A slots remain controls, never treatment estimators.
    """
    assert_design()
    legacy = original.adjudicate_untrusted_times(records)
    grouped = [[None for _ in range(original.BLOCKS)] for _ in range(original.PACKETS)]
    for (block, packet, position, arm), rec in zip(original.roster(), records):
        # original.adjudicate_untrusted_times already checks every field/type,
        # physical arm and sequence; this function does not relax it.
        if position < 4:
            if grouped[packet][block] is None:
                grouped[packet][block] = []
            grouped[packet][block].append(math.log(rec["wall_ns"]))
    coefficients = []
    for packet in range(original.PACKETS):
        xs = []
        ys = []
        for block in range(original.BLOCKS):
            times = grouped[packet][block]
            require(type(times) is list and len(times) == 4,
                    "packet/block incomplete")
            sequence = original.order(block, packet)[:4]
            rows = [original.model_row(sequence, pos)[1:] for pos in range(4)]
            xavg = [sum(row[col] for row in rows) / 4 for col in range(6)]
            yavg = sum(times) / 4
            for row, logtime in zip(rows, times):
                xs.append(tuple(row[col] - xavg[col] for col in range(6)))
                ys.append(logtime - yavg)
        coefficients.append(_solve(xs, ys))
    # CT199: the historical physical_B estimate is a *conditional* effect
    # when previous_B=0. Include both conditional contrasts, and separately
    # standardize to the frozen (not arbitrarily chosen) previous-B mix.
    q = previous_b_roster_share(0)
    require(all(previous_b_roster_share(packet) == q
                for packet in range(original.PACKETS)),
            "packet-specific carryover standardization weights differ")
    previous_a = [-c["physical_B"] for c in coefficients]
    previous_b = [-(c["physical_B"] + c["physical_B_x_previous_B"])
                  for c in coefficients]
    standardized = [-(c["physical_B"] + float(q) * c["physical_B_x_previous_B"])
                    for c in coefficients]
    contrasts = previous_a  # preserved legacy alias; never a marginal ratio
    return {
        "schema": SCHEMA,
        "standing": "[pcc:unverified]",
        "scope": "source-only untrusted times, conditional additive block/period/first-order model",
        "fixture_git_blob": original.FIXTURE_GIT_BLOB,
        "physical_roster_sha256": EXPECTED_ROSTER_SHA256,
        "supplied_processes": original.N,
        "packets": original.PACKETS,
        "periods_per_block_for_treatment": 4,
        "block_intercepts_per_packet": original.BLOCKS,
        "exact_model_columns": N_BLOCK_COLUMNS,
        "median_direct_over_retained_ratio_block_fixed":
            math.exp(statistics.median(contrasts)),  # LEGACY previous-A only
        "legacy_ratio_condition": "previous_B=0; NOT marginal",
        "roster_standardization_previous_B_fraction": "3/8",
        "median_direct_over_retained_ratio_previous_A":
            math.exp(statistics.median(previous_a)),
        "median_direct_over_retained_ratio_previous_B":
            math.exp(statistics.median(previous_b)),
        "median_direct_over_retained_ratio_roster_standardized":
            math.exp(statistics.median(standardized)),
        "per_packet_direct_over_retained_log_ratios": [
            {"previous_A": a, "previous_B": b, "roster_standardized": s}
            for a, b, s in zip(previous_a, previous_b, standardized)
        ],
        "median_previous_B_coefficient_block_fixed":
            statistics.median(c["previous_B"] for c in coefficients),
        "median_interaction_coefficient_block_fixed":
            statistics.median(c["physical_B_x_previous_B"] for c in coefficients),
        "per_packet_block_fixed_coefficients": coefficients,
        "original_seven_column_diagnostic": legacy,
        "native_execution_verified": False,
        "signed_independent_pcc": False,
        "complete_single_target_ecdlp_advantage_established": False,
    }


if __name__ == "__main__":
    print(json.dumps({"schema": SCHEMA, "standing": "[pcc:unverified]",
                      "full_roster_sha256": original.roster_sha256(),
                      "block_fixed_design_identified": assert_design(),
                      "full_design_columns": N_BLOCK_COLUMNS},
                     sort_keys=True))
