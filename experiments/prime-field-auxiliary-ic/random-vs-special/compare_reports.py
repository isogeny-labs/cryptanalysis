#!/usr/bin/env python3
"""Align three existing relation-yield reports; never launch or qualify a benchmark.

This is a producer-side consistency check, not independent execution validation.
Full-solve costs need phase accounting and signed replay and are not inferred here.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ARMS = ("auxiliary", "same_base", "random")
SAMPLER = "splitmix64-rejection-public-coefficient-walks"
PHASES = ("initialization", "target_walk", "decomposition", "row_validation",
          "graph_recovery", "certificate_replay", "bookkeeping")
CLI_PHASES = ("preparation", "before_online", "online", "reporting", "reference")


class Mismatch(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Mismatch(message)


def obj(value, name):
    require(isinstance(value, dict), name + " must be an object")
    return value


def integer(value, name, minimum=0):
    require(type(value) is int and minimum <= value < 2**64, name + " must be a bounded integer")
    return value


def digest(value, name, length=64):
    require(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{" + str(length) + "}", value),
            name + " must be an explicit lowercase hex identity")
    return value


def summary(report):
    report = report if isinstance(report, dict) else {}
    work = report.get("work")
    work = work if isinstance(work, dict) else {}
    base = report.get("factor_base")
    base = base if isinstance(base, dict) else {}
    return {"status": report.get("status"), "stop_reason": report.get("stop_reason"),
            "columns_blake3": base.get("columns_blake3"),
            "work": {k: work.get(k) for k in ("queries", "generated_targets", "lane_rounds",
                                               "relations", "duplicate_rows")}}


def check_phases(report, settings, name):
    enabled = settings.get("profile_phases", False)  # Older, unprofiled reports.
    require(type(enabled) is bool, name + ": phase-profiling flag must be boolean")
    phases = report.get("online_exclusive_phases")
    if not enabled:
        require(phases is None, name + ": phase accounting present without profiling")
        if report["schema_version"] == 2:
            check_call_costs(report, None, name)
        return
    phases = obj(phases, name + ".online_exclusive_phases")
    require(phases.get("schema") == "auxiliary-ic-online-phases/v1"
            and phases.get("unit") == "ns"
            and phases.get("scope") == "core-search-including-local-replay"
            and phases.get("clock") == "std::time::Instant"
            and phases.get("clock_overhead") == "included-not-subtracted",
            name + ": unknown phase accounting scope")
    require("independent_replay" in phases and phases["independent_replay"] is None,
            name + ": producer profiling cannot attest independent replay")
    durations = obj(phases.get("durations"), name + ".phase durations")
    require(set(durations) == set(PHASES), name + ": phase partition is incomplete")
    total = integer(phases.get("total"), name + ".phase total")
    require(sum(integer(durations[k], name + ".phase." + k) for k in PHASES) == total,
            name + ": phase partition does not sum to the online interval")
    require(durations["graph_recovery"] == durations["certificate_replay"] == 0,
            name + ": recovery time mixed into yield mode")
    integer(phases.get("clock_reads"), name + ".clock_reads", 2)
    if report["schema_version"] == 2:
        check_call_costs(report, total, name)
        return
    wall, call_wall = report.get("online_wall_seconds"), report.get("online_call_wall_seconds")
    require(type(wall) in (int, float) and 0 <= wall < 2**64
            and type(call_wall) in (int, float) and 0 <= call_wall < 2**64,
            name + ": invalid online duration")
    require(math.isclose(wall, total / 1e9, rel_tol=1e-12, abs_tol=1e-12)
            and call_wall >= wall >= 0, name + ": online interval differs from its phase total")


def seconds_match(seconds, ns, name):
    require(type(seconds) in (int, float) and 0 <= seconds < 2**64
            and math.isclose(seconds, ns / 1e9, rel_tol=1e-12, abs_tol=1e-12),
            name + ": seconds differ from integer nanoseconds")


def check_call_costs(report, core, name):
    total = integer(report.get("online_wall_ns"), name + ".online_wall_ns")
    call = obj(report.get("online_accounting"), name + ".online_accounting")
    require(call.get("schema") == "auxiliary-ic-online-call/v1" and call.get("unit") == "ns"
            and call.get("scope") == "target-point-validation-through-local-replay",
            name + ": unknown caller accounting scope")
    require(integer(call.get("total"), name + ".call.total") == total,
            name + ": caller total differs from online wall")
    validation = integer(call.get("input_validation"), name + ".call.input_validation")
    require(validation <= total, name + ": target validation exceeds caller interval")
    for key in ("independent_replay", "core", "call_overhead"):
        require(key in call, name + ": missing caller declaration " + key)
    require(call["independent_replay"] is None, name + ": caller cannot attest independent replay")
    if core is None:
        require(call["core"] is None and call["call_overhead"] is None,
                name + ": unprofiled core costs must remain unknown")
    else:
        require(integer(call["core"], name + ".call.core") == core,
                name + ": core interval differs from its phase partition")
        overhead = integer(call["call_overhead"], name + ".call.overhead")
        require(validation + core + overhead == total, name + ": target/core/caller costs do not partition online wall")
    seconds_match(report.get("online_wall_seconds"), total, name + ".online_wall_seconds")
    seconds_match(report.get("online_call_wall_seconds"), total, name + ".online_call_wall_seconds")
    cli = obj(report.get("cli_accounting"), name + ".cli_accounting")
    require(cli.get("schema") == "auxiliary-ic-cli-costs/v1" and cli.get("unit") == "ns"
            and cli.get("scope") == "run-entry-through-resource-snapshot; excludes accounting serialization",
            name + ": unknown CLI accounting scope")
    values = {k: integer(cli.get(k), name + ".cli." + k) for k in CLI_PHASES}
    observed = integer(cli.get("observed_total"), name + ".cli.observed_total")
    require(sum(values.values()) == observed, name + ": CLI phases overlap or leave a gap")
    require(integer(cli.get("ic_observed_total"), name + ".cli.ic_observed_total")
            == observed - values["reference"], name + ": reference cost charged to IC")
    require(values["reference"] == 0, name + ": rho reference mixed into yield collection")
    require(values["online"] == total, name + ": CLI and online intervals differ")
    prep = integer(report.get("target_independent_preparation_ns"), name + ".preparation_ns")
    require(prep == values["preparation"], name + ": preparation cost differs")
    seconds_match(report.get("target_independent_preparation_seconds"), prep, name + ".preparation_seconds")
    for key in ("upstream_preparation", "process_start_exit", "independent_replay", "cold_total"):
        require(key in cli and cli[key] is None, name + ": CLI cannot supply " + key)


def compare_reports(reports):
    result = {"schema": "auxiliary-ic-relation-comparison/v1", "status": "incomparable",
              "qualification": "unsigned producer alignment and derived counters only",
              "qualified_speedup": None, "end_to_end_cost_comparison": None,
              "arms": {k: summary(reports.get(k)) for k in ARMS}, "issues": []}
    try:
        require(set(reports) == set(ARMS), "exactly the auxiliary, same_base and random arms are required")
        for name in ARMS:
            report = obj(reports[name], name)
            require(type(report.get("schema_version")) is int and report["schema_version"] in (1, 2)
                    and report.get("operation") == "auxiliary-prime-field-ic",
                    name + ": unknown report schema")
            require(report.get("mode") == "bounded-relation-yield",
                    name + ": only fixed-prefix relation yield is comparable here; solve/replay costs are separate")
            require(report.get("sampler") == SAMPLER, name + ": unknown public query sampler")
            digest(report.get("source_commit"), name + ".source_commit", 40)
            digest(report.get("binary_blake3"), name + ".binary_blake3")
            public = obj(report.get("public"), name + ".public")
            for key in ("p", "a", "b", "n"):
                integer(public.get(key), name + ".public." + key, 1 if key in ("p", "n") else 0)
            bits = integer(report.get("field_bits"), name + ".field_bits", 1)
            require(bits in (3, 5, 7, 13, 17, 19, 31, 61) and public["p"] == (1 << bits) - 1,
                    name + ": field size does not match its declared Mersenne field")
            require(public["a"] < public["p"] and public["b"] < public["p"]
                    and public["n"] >= 3 and public["n"] % 2 == 1, name + ": invalid curve/subgroup parameters")
            for key in ("P", "Q"):
                point = public.get(key)
                require(isinstance(point, list) and len(point) == 2, name + ": public point missing")
                for value in point:
                    require(integer(value, name + ".public." + key) < public["p"], name + ": noncanonical public point")
            base = obj(report.get("factor_base"), name + ".factor_base")
            columns = integer(base.get("folded_columns"), name + ".columns", 1)
            require(base.get("affine_points") == 2 * columns, name + ": unequal signed-column/affine accounting")
            integer(base.get("raw_roots"), name + ".raw_roots", 1)
            digest(base.get("columns_blake3"), name + ".columns_blake3")
            settings = obj(report.get("configured_search"), name + ".configured_search")
            for key in ("seed", "max_relations", "max_proof_nodes", "max_queries", "walk_lanes"):
                integer(settings.get(key), name + "." + key, 1 if key in ("max_proof_nodes", "max_queries", "walk_lanes") else 0)
            require(settings["walk_lanes"] <= 1024, name + ": invalid lane count")
            require("max_millis" in settings, name + ": missing time-cap declaration")
            if settings["max_millis"] is not None:
                integer(settings["max_millis"], name + ".max_millis")
            check_phases(report, settings, name)
            work = obj(report.get("work"), name + ".work")
            for key in ("queries", "generated_targets", "lane_rounds", "relations", "duplicate_rows",
                        "circuit_queries", "matrix_rank", "proof_nodes"):
                integer(work.get(key), name + ".work." + key)
            require(work["relations"] + work["duplicate_rows"] <= work["queries"], name + ": more row hits than queries")
            require(work["matrix_rank"] == work["proof_nodes"] == 0, name + ": recovery work mixed into yield mode")
            require(work["circuit_queries"] <= work["queries"], name + ": invalid circuit-query count")
            require(work.get("backend") == base.get("backend") == "scalar",
                    name + ": scalar arithmetic must match; a native SIMD comparison needs a separate scope")
            require("certificate" in report and report["certificate"] is None, name + ": missing yield-mode certificate declaration")

        special, direct, random = (reports[k] for k in ARMS)
        for key in ("schema_version", "public", "field_bits", "source_commit", "binary_blake3", "configured_search"):
            require(all(report.get(key) == special.get(key) for report in (direct, random)),
                    "arms disagree on " + key)
        bases = [report["factor_base"] for report in (special, direct, random)]
        require(all(b["folded_columns"] == bases[0]["folded_columns"] for b in bases), "usable base sizes differ")
        require(bases[0].get("uses_auxiliary_maps") is True and bases[0].get("uses_circuit") is True
                and obj(bases[0].get("encoding"), "auxiliary.encoding").get("kind") == "auxiliary",
                "auxiliary arm must use special auxiliary-curve maps")
        for name, base in zip(("same_base", "random"), bases[1:]):
            require(base.get("uses_auxiliary_maps") is False and base.get("uses_circuit") is False
                    and obj(base.get("encoding"), name + ".encoding").get("kind") == "direct",
                    name + " must use direct IC without a membership circuit")
            require(reports[name]["work"]["circuit_queries"] == 0, name + ": unexpected circuit work")
        require(bases[0]["columns_blake3"] == bases[1]["columns_blake3"], "same-base control uses different actual columns")
        require(bases[0]["raw_roots"] == bases[1]["raw_roots"], "same-base raw-root accounting differs")
        recipe = obj(bases[2].get("selection_encoding"), "random.selection_encoding")
        preparation = obj(bases[2].get("random_preparation"), "random.random_preparation")
        require(recipe.get("kind") == "random-subgroup", "random arm is not an ordinary sampled base")
        require(preparation.get("sampler") == "splitmix64-rejection-field-coordinates-cofactor-clear-negation-fold",
                "random base sampler is unknown")
        seed = integer(recipe.get("seed"), "random base seed")
        require(type(preparation.get("seed")) is int and preparation["seed"] == seed, "random seed metadata differs")
        columns = bases[2]["folded_columns"]
        require(integer(recipe.get("columns"), "random requested columns", 1) == columns,
                "random requested and usable columns differ")
        draws = integer(preparation.get("draws"), "random draws", 1)
        rejected = sum(integer(preparation.get(k), "random." + k) for k in
                       ("field_rejections", "non_lifts", "cleared_to_identity", "duplicate_columns"))
        require(draws == columns + rejected, "random draw accounting does not reconcile")
        require(draws <= integer(recipe.get("max_draws"), "random draw limit", 1), "random preparation exceeded its cap")
        p, n = special["public"]["p"], special["public"]["n"]
        radius = math.isqrt(4 * p)
        lower, upper = (p + 1 - radius + n - 1) // n, (p + 1 + radius) // n
        require(lower == upper and lower > 0 and math.gcd(lower, n) == 1,
                "random cofactor metadata is not Hasse-certifiable")
        require(integer(recipe.get("cofactor"), "random recipe cofactor", 1)
                == integer(preparation.get("cofactor"), "random preparation cofactor", 1) == lower,
                "random cofactor metadata differs")
        require(lower != 1 or preparation["cleared_to_identity"] == 0,
                "cofactor-one preparation cannot clear an affine lift to the identity")
        q = special["configured_search"]["max_queries"]
        lanes = special["configured_search"]["walk_lanes"]
        rounds = (q + lanes - 1) // lanes
        for name in ARMS:
            report, work = reports[name], reports[name]["work"]
            require(report.get("status") == "complete" and report.get("stop_reason") == "QueryBudget",
                    name + ": incomplete or censored prefix retained; no comparison is derived")
            require(work["queries"] == q, name + ": processed prefix differs from the requested budget")
            require(work["generated_targets"] == rounds * lanes and work["lane_rounds"] == rounds,
                    name + ": generated/unused-lane accounting differs")
            row_limit = report["configured_search"]["max_relations"] or 4 * columns + 64
            require(work["relations"] <= row_limit, name + ": retained rows exceed their cap")
        for key in ("relations", "duplicate_rows", "queries", "generated_targets", "lane_rounds"):
            require(special["work"][key] == direct["work"][key], "same-base controls disagree on " + key)
        for name in ARMS:
            work = reports[name]["work"]
            result["arms"][name]["derived_counts"] = {
                "distinct_rows_per_query": {"numerator": work["relations"], "denominator": q},
                "hits_per_query": {"numerator": work["relations"] + work["duplicate_rows"], "denominator": q}}
        result["status"] = "aligned"
        result["common"] = {key: special[key] for key in
                            ("public", "field_bits", "source_commit", "binary_blake3", "configured_search")}
        result["random_base_coincides_with_special"] = bases[0]["columns_blake3"] == bases[2]["columns_blake3"]
    except Mismatch as error:
        result["issues"].append(str(error))
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def nonfinite_constant(value):
    raise Mismatch("nonfinite JSON constant: " + value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ARMS:
        parser.add_argument("--" + name.replace("_", "-"), required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    reports, raw, errors = {}, [], []
    for name in ARMS:
        path = getattr(args, name)
        try:
            with path.open("rb") as stream:
                data = stream.read((64 << 20) + 1)
            require(len(data) <= 64 << 20, name + ": report exceeds 64 MiB")
            raw.append({"arm": name, "path": str(path), "sha256": hashlib.sha256(data).hexdigest()})
            reports[name] = json.loads(data, object_pairs_hook=unique_object,
                                      parse_constant=nonfinite_constant)
        except (OSError, ValueError) as error:
            reports[name] = None
            errors.append(name + ": " + str(error))
    result = compare_reports(reports)
    if errors:
        result["status"] = "incomparable"
        result["issues"].extend(errors)
    result["raw_data"] = raw
    text = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end="")
    return 0 if result["status"] == "aligned" else 2


if __name__ == "__main__":
    raise SystemExit(main())
