#!/usr/bin/env python3
"""Bounded heuristic PARI proposer for selected-point relations.

This is not a relation certificate. It uses numerical canonical-height Gram
matrices and exact LLL on frozen integer roundings only to propose vectors.
Proposals are retained here only after exact generalized-Weierstrass replay;
experimental counting still requires ``relation_certificate`` replay.

The strict input schema contains no source scalars: ``row_id``, ``r``,
``ainvs``, and ``selected_points`` only.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, ROUND_FLOOR, localcontext
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import invariants_pari as invariants
import relation_certificate


SCHEMA_VERSION = 1
ADAPTER = "pari-height-lll-relation-proposer-v1"
BEGIN = "XEDNI_RELATION_PROPOSER_BEGIN_V1"
END = "XEDNI_RELATION_PROPOSER_END_V1"
REQUIRED_PARI_VERSION = "2.17.2"
PARISIZEMAX = 2_147_483_648
SCHEDULE = ((256, 64), (384, 128), (768, 192))
LLL_FLAG = 1
PER_SCHEDULE_CANDIDATE_CAP = 64
TOTAL_REPLAY_CANDIDATE_CAP = len(SCHEDULE) * PER_SCHEDULE_CANDIDATE_CAP
COEFFICIENT_ABS_MAX = 1 << 20
COEFFICIENT_L1_MAX = 1 << 22
MIN_PRECISION_SUPPORT = 2
MIN_R = 2
MAX_R = 6
INPUT_KEYS = {"row_id", "r", "ainvs", "selected_points"}


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def validate_row(row) -> tuple[str, int, tuple[int, ...], tuple[tuple[Fraction, Fraction], ...]]:
    if not isinstance(row, dict):
        raise ValueError("row must be a JSON object")
    if set(row) != INPUT_KEYS:
        raise ValueError(
            f"input keys must be exactly {sorted(INPUT_KEYS)}; source scalars and metadata are prohibited"
        )
    row_id, ainvs, points = invariants.validate_row(row)
    r = row.get("r")
    if isinstance(r, bool) or not isinstance(r, int) or not MIN_R <= r <= MAX_R:
        raise ValueError("r must be an integer in 2..6")
    if len(points) != r:
        raise ValueError("selected_points length must equal r")
    return row_id, r, ainvs, points


def make_script(
    ainvs: tuple[int, ...],
    points: tuple[tuple[Fraction, Fraction], ...],
    parisizemax: int = PARISIZEMAX,
) -> str:
    r = len(points)
    coefficient_text = ",".join(str(value) for value in ainvs)
    point_text = ",".join(
        f"[{invariants._fraction_text(x)},{invariants._fraction_text(y)}]" for x, y in points
    )
    lines = [
        f"default(parisizemax,{parisizemax});",
        f"default(realbitprecision,{max(precision for precision, _ in SCHEDULE)});",
        f"E=ellinit([{coefficient_text}],1);",
        "M=ellminimalmodel(E,&V);",
        "C=ellchangecurve(E,V);",
        f"PTS=[{point_text}];",
        f"R={r};",
        "MPTS=vector(R,i,ellchangepoint(PTS[i],V));",
        "ON0=vector(R,i,ellisoncurve(E,PTS[i]));",
        "ONM=vector(R,i,ellisoncurve(M,MPTS[i]));",
        "ROUNDTRIP=vector(R,i,ellchangepointinv(MPTS[i],V)==PTS[i]);",
        f'print("{BEGIN}");',
        'print("STATUS=OK");',
        'print("R=",R);',
        'print("PARISIZEMAX=",default(parisizemax));',
        'print("CONSTRUCTION_DISC=",E.disc);',
        'print("MINIMAL_DISC=",M.disc);',
        'print("CURVE_MAP_OK=",C.a1==M.a1 && C.a2==M.a2 && C.a3==M.a3 && C.a4==M.a4 && C.a6==M.a6);',
        'print("POINTS_ON_CONSTRUCTION_OK=",vecsum(ON0)==R);',
        'print("POINTS_ON_MINIMAL_OK=",vecsum(ONM)==R);',
        'print("POINT_ROUNDTRIP_OK=",vecsum(ROUNDTRIP)==R);',
        f'print("SCHEDULE_COUNT=",{len(SCHEDULE)});',
    ]
    for name, member in zip(invariants.AINV_NAMES, ("a1", "a2", "a3", "a4", "a6")):
        lines.append(f'print("MIN_{name}=",M.{member});')
    for index, name in enumerate(invariants.TRANSFORM_NAMES, 1):
        lines.extend(
            [
                f'print("TRANS_{name}_NUM=",numerator(V[{index}]));',
                f'print("TRANS_{name}_DEN=",denominator(V[{index}]));',
            ]
        )
    for schedule_index, (precision, scale) in enumerate(SCHEDULE, 1):
        h_name, g_name, t_name = f"H{schedule_index}", f"G{schedule_index}", f"T{schedule_index}"
        lines.extend(
            [
                f"default(realbitprecision,{precision});",
                f"{h_name}=ellheightmatrix(M,MPTS);",
                f"{h_name}=({h_name}+{h_name}~)/2;",
                f"{g_name}=matrix(R,R,i,j,round(2^{scale}*{h_name}[i,j]))+{r + 1}*matid(R);",
                f"{t_name}=qflllgram({g_name},{LLL_FLAG});",
                f'print("S{schedule_index}_PRECISION_BITS=",default(realbitprecision));',
                f'print("S{schedule_index}_REALPRECISION=",default(realprecision));',
                f'print("S{schedule_index}_SCALE_BITS=",{scale});',
            ]
        )
        for i in range(1, r + 1):
            for j in range(1, r + 1):
                lines.extend(
                    [
                        f'print("S{schedule_index}_H_{i}_{j}=",{h_name}[{i},{j}]);',
                        f'print("S{schedule_index}_G_{i}_{j}=",{g_name}[{i},{j}]);',
                        f'print("S{schedule_index}_T_{i}_{j}=",{t_name}[{i},{j}]);',
                    ]
                )
    lines.extend((f'print("{END}");', "quit();"))
    return "\n".join(lines) + "\n"


def _expected_keys(r: int) -> set[str]:
    keys = {
        "STATUS", "R", "PARISIZEMAX", "CONSTRUCTION_DISC", "MINIMAL_DISC",
        "CURVE_MAP_OK", "POINTS_ON_CONSTRUCTION_OK", "POINTS_ON_MINIMAL_OK",
        "POINT_ROUNDTRIP_OK", "SCHEDULE_COUNT",
    }
    keys.update(f"MIN_{name}" for name in invariants.AINV_NAMES)
    for name in invariants.TRANSFORM_NAMES:
        keys.update((f"TRANS_{name}_NUM", f"TRANS_{name}_DEN"))
    for schedule_index in range(1, len(SCHEDULE) + 1):
        keys.update(
            (
                f"S{schedule_index}_PRECISION_BITS",
                f"S{schedule_index}_REALPRECISION",
                f"S{schedule_index}_SCALE_BITS",
            )
        )
        for i in range(1, r + 1):
            for j in range(1, r + 1):
                keys.update(
                    (
                        f"S{schedule_index}_H_{i}_{j}",
                        f"S{schedule_index}_G_{i}_{j}",
                        f"S{schedule_index}_T_{i}_{j}",
                    )
                )
    return keys


def parse_transcript(stdout: str, r: int) -> dict[str, str]:
    if stdout.count(BEGIN) != 1 or stdout.count(END) != 1:
        raise ValueError(
            f"expected one begin and one end marker, found {stdout.count(BEGIN)} and {stdout.count(END)}"
        )
    pattern = re.compile(
        rf"(?m)^{re.escape(BEGIN)}\s*$\n(?P<body>.*?)^(?:{re.escape(END)})\s*$", re.DOTALL
    )
    matches = list(pattern.finditer(stdout))
    if len(matches) != 1:
        raise ValueError(f"expected one complete marker block, found {len(matches)}")
    values: dict[str, str] = {}
    for line in matches[0].group("body").splitlines():
        if "=" not in line:
            raise ValueError(f"unparseable marker line: {line!r}")
        key, value = line.strip().split("=", 1)
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not value or key in values:
            raise ValueError(f"invalid or duplicate marker line: {line!r}")
        values[key] = value
    expected = _expected_keys(r)
    if set(values) != expected:
        raise ValueError(
            f"marker keys differ; missing={sorted(expected - set(values))}, extra={sorted(set(values) - expected)}"
        )
    if values["STATUS"] != "OK":
        raise ValueError(f"unexpected status {values['STATUS']!r}")
    return values


def _integer(values: dict[str, str], key: str) -> int:
    raw = values[key]
    if not re.fullmatch(r"-?(?:0|[1-9][0-9]*)", raw):
        raise ValueError(f"{key} is not a canonical integer")
    return int(raw)


def _flag(values: dict[str, str], key: str) -> bool:
    value = _integer(values, key)
    if value not in (0, 1):
        raise ValueError(f"{key} is not boolean")
    return bool(value)


def _fraction(values: dict[str, str], prefix: str) -> Fraction:
    numerator = _integer(values, f"{prefix}_NUM")
    denominator = _integer(values, f"{prefix}_DEN")
    if denominator <= 0:
        raise ValueError(f"{prefix} denominator is not positive")
    value = Fraction(numerator, denominator)
    if (value.numerator, value.denominator) != (numerator, denominator):
        raise ValueError(f"{prefix} is not reduced")
    return value


def _decimal(values: dict[str, str], key: str) -> tuple[Decimal, str]:
    return invariants._parse_decimal(values, key)


def _determinant(matrix: list[list[int]]) -> int:
    n = len(matrix)
    work = [[Fraction(value) for value in row] for row in matrix]
    determinant = Fraction(1)
    for column in range(n):
        pivot = next((row for row in range(column, n) if work[row][column]), None)
        if pivot is None:
            return 0
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            determinant = -determinant
        pivot_value = work[column][column]
        determinant *= pivot_value
        for row in range(column + 1, n):
            factor = work[row][column] / pivot_value
            for index in range(column + 1, n):
                work[row][index] -= factor * work[column][index]
    if determinant.denominator != 1:
        raise ValueError("integer matrix determinant was not integral")
    return determinant.numerator


def _positive_definite(matrix: list[list[int]]) -> bool:
    n = len(matrix)
    if any(matrix[i][j] != matrix[j][i] for i in range(n) for j in range(n)):
        return False
    return all(
        _determinant([row[:size] for row in matrix[:size]]) > 0
        for size in range(1, n + 1)
    )


def _gp_round_scaled(value: Decimal, scale_bits: int) -> int:
    with localcontext() as context:
        context.prec = 300
        scaled = value * Decimal(1 << scale_bits)
        return int((scaled + Decimal("0.5")).to_integral_value(rounding=ROUND_FLOOR))


def _relative_close(left: Decimal, right: Decimal, precision_bits: int) -> bool:
    digits = max(30, int(precision_bits * math.log10(2)))
    return invariants._relative_close(left, right, digits)


def _primitive(vector: list[int]) -> list[int]:
    divisor = 0
    for value in vector:
        divisor = math.gcd(divisor, abs(value))
    if divisor == 0:
        return vector
    normalized = [value // divisor for value in vector]
    first = next(value for value in normalized if value)
    return [-value for value in normalized] if first < 0 else normalized


def _matrix_vector(matrix: list[list[int]], vector: tuple[int, ...]) -> list[int]:
    return [sum(value * vector[j] for j, value in enumerate(row)) for row in matrix]


def _quadratic_norm(vector: list[int], gram: list[list[int]]) -> int:
    return sum(vector[i] * gram[i][j] * vector[j] for i in range(len(vector)) for j in range(len(vector)))


def _parse_model(
    parsed: dict[str, str],
    ainvs: tuple[int, ...],
    points: tuple[tuple[Fraction, Fraction], ...],
    parisizemax: int,
) -> tuple[tuple[int, ...], tuple[Fraction, Fraction, Fraction, Fraction]]:
    r = len(points)
    if _integer(parsed, "R") != r or _integer(parsed, "SCHEDULE_COUNT") != len(SCHEDULE):
        raise ValueError("dimension or schedule count mismatch")
    if _integer(parsed, "PARISIZEMAX") != parisizemax:
        raise ValueError("parisizemax mismatch")
    if _integer(parsed, "CONSTRUCTION_DISC") != invariants.curve_discriminant(ainvs):
        raise ValueError("construction discriminant mismatch")
    flags = (
        "CURVE_MAP_OK",
        "POINTS_ON_CONSTRUCTION_OK",
        "POINTS_ON_MINIMAL_OK",
        "POINT_ROUNDTRIP_OK",
    )
    if not all(_flag(parsed, key) for key in flags):
        raise ValueError("exact model or point-map flag failed")
    minimal_ainvs = tuple(_integer(parsed, f"MIN_{name}") for name in invariants.AINV_NAMES)
    minimal_disc = _integer(parsed, "MINIMAL_DISC")
    if invariants.curve_discriminant(minimal_ainvs) != minimal_disc or minimal_disc == 0:
        raise ValueError("minimal discriminant mismatch")
    transform = tuple(_fraction(parsed, f"TRANS_{name}") for name in invariants.TRANSFORM_NAMES)
    u = transform[0]
    if u <= 0 or Fraction(minimal_disc) * u**12 != invariants.curve_discriminant(ainvs):
        raise ValueError("exact discriminant transformation failed")
    for point in points:
        mapped = invariants.map_point_to_new(point, transform)
        if not invariants.on_curve(minimal_ainvs, mapped):
            raise ValueError("independent exact point-map replay failed")
    return minimal_ainvs, transform  # type: ignore[return-value]


def _parse_schedules(parsed: dict[str, str], r: int) -> list[dict]:
    schedules = []
    for schedule_index, (expected_precision, expected_scale) in enumerate(SCHEDULE, 1):
        precision = _integer(parsed, f"S{schedule_index}_PRECISION_BITS")
        realprecision = _integer(parsed, f"S{schedule_index}_REALPRECISION")
        scale = _integer(parsed, f"S{schedule_index}_SCALE_BITS")
        if (precision, scale) != (expected_precision, expected_scale) or realprecision <= 0:
            raise ValueError(f"schedule {schedule_index} differs from frozen schedule")
        heights, height_text = [], []
        gram, transform = [], []
        for i in range(1, r + 1):
            height_row, height_text_row, gram_row, transform_row = [], [], [], []
            for j in range(1, r + 1):
                height, rendered = _decimal(parsed, f"S{schedule_index}_H_{i}_{j}")
                if not height.is_finite():
                    raise ValueError(f"nonfinite height entry in schedule {schedule_index}")
                height_row.append(height)
                height_text_row.append(rendered)
                gram_row.append(_integer(parsed, f"S{schedule_index}_G_{i}_{j}"))
                transform_row.append(_integer(parsed, f"S{schedule_index}_T_{i}_{j}"))
            heights.append(height_row)
            height_text.append(height_text_row)
            gram.append(gram_row)
            transform.append(transform_row)
        for i in range(r):
            if heights[i][i] < 0:
                raise ValueError(f"negative height diagonal in schedule {schedule_index}")
            for j in range(r):
                if heights[i][j] != heights[j][i]:
                    raise ValueError(f"height matrix not symmetric in schedule {schedule_index}")
                expected = _gp_round_scaled(heights[i][j], scale) + ((r + 1) if i == j else 0)
                if gram[i][j] != expected:
                    raise ValueError(f"integer Gram mismatch in schedule {schedule_index}")
        if not _positive_definite(gram):
            raise ValueError(f"integer Gram not positive definite in schedule {schedule_index}")
        if abs(_determinant(transform)) != 1:
            raise ValueError(f"qflll transformation not unimodular in schedule {schedule_index}")
        schedules.append(
            {
                "schedule_index": schedule_index,
                "precision_bits": precision,
                "realprecision": realprecision,
                "scale_bits": scale,
                "height_matrix": heights,
                "height_matrix_text": height_text,
                "integer_gram": gram,
                "lll_transform": transform,
            }
        )
    reference = schedules[-1]
    for schedule in schedules[:-1]:
        for i in range(r):
            for j in range(r):
                if not _relative_close(
                    schedule["height_matrix"][i][j],
                    reference["height_matrix"][i][j],
                    schedule["precision_bits"],
                ):
                    raise ValueError("height_precision_instability")
    return schedules


def _enumerate_candidates(schedule: dict, r: int) -> tuple[list[dict], dict]:
    generated = 0
    filtered_bound = 0
    best: dict[tuple[int, ...], dict] = {}
    transform, gram = schedule["lll_transform"], schedule["integer_gram"]
    for alpha in itertools.product((-1, 0, 1), repeat=r):
        if not any(alpha):
            continue
        if next(value for value in alpha if value) < 0:
            continue
        generated += 1
        vector = _primitive(_matrix_vector(transform, alpha))
        if not any(vector):
            continue
        if max(abs(value) for value in vector) > COEFFICIENT_ABS_MAX or sum(
            abs(value) for value in vector
        ) > COEFFICIENT_L1_MAX:
            filtered_bound += 1
            continue
        key = tuple(vector)
        candidate = {
            "alpha": list(alpha),
            "vector": vector,
            "integer_gram_norm": _quadratic_norm(vector, gram),
            "l1_norm": sum(abs(value) for value in vector),
            "max_abs": max(abs(value) for value in vector),
            "schedule_index": schedule["schedule_index"],
            "precision_bits": schedule["precision_bits"],
            "scale_bits": schedule["scale_bits"],
        }
        previous = best.get(key)
        order = (candidate["integer_gram_norm"], candidate["l1_norm"], candidate["vector"])
        if previous is None or order < (
            previous["integer_gram_norm"], previous["l1_norm"], previous["vector"]
        ):
            best[key] = candidate
    ordered = sorted(
        best.values(), key=lambda item: (item["integer_gram_norm"], item["l1_norm"], item["vector"])
    )
    retained = ordered[:PER_SCHEDULE_CANDIDATE_CAP]
    return retained, {
        "sign_canonical_alpha_generated": generated,
        "coefficient_bound_filtered": filtered_bound,
        "unique_before_cap": len(ordered),
        "retained_after_cap": len(retained),
        "cap": PER_SCHEDULE_CANDIDATE_CAP,
    }


def _text(value) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def _base(row, tool: dict) -> dict:
    return {
        "adapter": ADAPTER,
        "counted_relation_count": 0,
        "heuristic_only": True,
        "input_sha256": _sha256(row),
        "reason": "not_run",
        "row_id": row.get("row_id") if isinstance(row, dict) else None,
        "schema_version": SCHEMA_VERSION,
        "status": "UNKNOWN",
        "tool": tool,
        "uses_source_scalars": False,
    }


def process_row(
    row,
    tool: dict,
    timeout: float,
    parisizemax: int = PARISIZEMAX,
) -> dict:
    output = _base(row, tool)
    try:
        row_id, r, ainvs, points = validate_row(row)
    except ValueError as error:
        output.update(reason="invalid_input", error=str(error))
        return output
    output.update(
        row_id=row_id,
        r=r,
        ainvs=[str(value) for value in ainvs],
        selected_points=[
            [invariants._fraction_text(x), invariants._fraction_text(y)] for x, y in points
        ],
    )
    construction_disc = invariants.curve_discriminant(ainvs)
    output["construction_discriminant"] = str(construction_disc)
    if construction_disc == 0:
        output["reason"] = "singular_curve"
        return output
    for index, point in enumerate(points):
        if not invariants.on_curve(ainvs, point):
            output.update(
                reason="point_not_on_construction_curve",
                error=f"selected_points[{index}] is off curve",
            )
            return output
    if not tool["available"]:
        output.update(reason="missing_tool", error=f"executable not found: {tool['executable_requested']}")
        return output
    if tool["version_returncode"] != 0 or tool["version_timed_out"]:
        output["reason"] = "version_probe_failed"
        return output
    if REQUIRED_PARI_VERSION not in tool["version_stdout"] + tool["version_stderr"]:
        output.update(
            reason="unsupported_pari_version",
            error=f"required PARI/GP version {REQUIRED_PARI_VERSION}",
        )
        return output

    script = make_script(ainvs, points, parisizemax)
    command = [tool["executable_resolved"], "-q", "-f"]
    execution = {
        "command": command,
        "returncode": None,
        "script": script,
        "script_sha256": hashlib.sha256(script.encode()).hexdigest(),
        "stderr": "",
        "stdout": "",
        "timed_out": False,
        "timeout_seconds": timeout,
        "wall_ns": 0,
    }
    started = time.perf_counter_ns()
    try:
        completed = subprocess.run(
            command,
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        execution.update(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    except subprocess.TimeoutExpired as error:
        execution.update(
            timed_out=True,
            stdout=_text(error.stdout),
            stderr=_text(error.stderr),
        )
        output["reason"] = "timeout"
    except OSError as error:
        execution["stderr"] = f"{type(error).__name__}: {error}"
        output["reason"] = "launch_error"
    execution["wall_ns"] = time.perf_counter_ns() - started
    output["execution"] = execution
    if output["reason"] in {"timeout", "launch_error"}:
        return output
    if execution["returncode"] != 0:
        output["reason"] = "tool_nonzero_exit"
        return output

    try:
        parsed = parse_transcript(execution["stdout"], r)
        minimal_ainvs, transform = _parse_model(parsed, ainvs, points, parisizemax)
        schedules = _parse_schedules(parsed, r)
    except ValueError as error:
        output.update(reason="parser_or_semantic_error", error=str(error))
        return output

    per_schedule_candidates, enumeration = [], []
    for schedule in schedules:
        candidates, counts = _enumerate_candidates(schedule, r)
        per_schedule_candidates.append(candidates)
        enumeration.append({"schedule_index": schedule["schedule_index"], **counts})

    merged: dict[tuple[int, ...], dict] = {}
    for candidates in per_schedule_candidates:
        for candidate in candidates:
            key = tuple(candidate["vector"])
            record = merged.setdefault(
                key,
                {
                    "vector": candidate["vector"],
                    "origins": [],
                    "precision_support": [],
                    "eligible_for_exact_replay": False,
                    "exact_rational_replay": False,
                },
            )
            record["origins"].append(
                {
                    key: candidate[key]
                    for key in (
                        "schedule_index",
                        "precision_bits",
                        "scale_bits",
                        "alpha",
                        "integer_gram_norm",
                        "l1_norm",
                        "max_abs",
                    )
                }
            )
            record["precision_support"] = sorted(
                {origin["precision_bits"] for origin in record["origins"]}
            )
    candidates = sorted(
        merged.values(),
        key=lambda item: (
            -len(item["precision_support"]),
            sum(abs(value) for value in item["vector"]),
            item["vector"],
        ),
    )
    replay_candidates = [
        candidate
        for candidate in candidates
        if len(candidate["precision_support"]) >= MIN_PRECISION_SUPPORT
    ][:TOTAL_REPLAY_CANDIDATE_CAP]
    replay_keys = {tuple(candidate["vector"]) for candidate in replay_candidates}
    ainvs_q = tuple(Fraction(value) for value in ainvs)
    points_q = list(points)
    exact_relations = []
    for candidate in candidates:
        candidate["eligible_for_exact_replay"] = tuple(candidate["vector"]) in replay_keys
        if not candidate["eligible_for_exact_replay"]:
            candidate["exact_replay_reason"] = "insufficient_precision_support_or_total_cap"
            continue
        total = relation_certificate.relation_sum(candidate["vector"], points_q, ainvs_q)
        candidate["exact_rational_replay"] = total is None
        candidate["exact_replay_reason"] = (
            "sum_is_identity" if total is None else "sum_is_not_identity"
        )
        if total is not None:
            candidate["exact_final_sum"] = [
                invariants._fraction_text(total[0]),
                invariants._fraction_text(total[1]),
            ]
        else:
            exact_relations.append(list(candidate["vector"]))

    schedule_evidence = [
        {
            "schedule_index": schedule["schedule_index"],
            "precision_bits": schedule["precision_bits"],
            "realprecision": schedule["realprecision"],
            "scale_bits": schedule["scale_bits"],
            "height_matrix": schedule["height_matrix_text"],
            "integer_gram": schedule["integer_gram"],
            "lll_transform": schedule["lll_transform"],
        }
        for schedule in schedules
    ]
    output.update(
        status="OK",
        reason="heuristic_search_complete",
        scope="heuristic_proposals_with_exact_Q_replay; relation_certificate_required_for_counting",
        minimal_model={
            "ainvs": [str(value) for value in minimal_ainvs],
            "transformation": {
                name.lower(): invariants._fraction_text(value)
                for name, value in zip(invariants.TRANSFORM_NAMES, transform)
            },
        },
        frozen_protocol={
            "pari_version": REQUIRED_PARI_VERSION,
            "parisizemax": parisizemax,
            "schedule": [
                {"precision_bits": precision, "scale_bits": scale}
                for precision, scale in SCHEDULE
            ],
            "lll_function": "qflllgram",
            "lll_flag": LLL_FLAG,
            "regularizer": "(r+1)*I",
            "alpha_domain": [-1, 0, 1],
            "sign_canonical_alpha": True,
            "per_schedule_candidate_cap": PER_SCHEDULE_CANDIDATE_CAP,
            "total_replay_candidate_cap": TOTAL_REPLAY_CANDIDATE_CAP,
            "coefficient_abs_max": COEFFICIENT_ABS_MAX,
            "coefficient_l1_max": COEFFICIENT_L1_MAX,
            "minimum_precision_support": MIN_PRECISION_SUPPORT,
        },
        schedules=schedule_evidence,
        enumeration=enumeration,
        candidates=candidates,
        exact_rational_relations=exact_relations,
        proposal_accounting={
            "qflll_calls": len(SCHEDULE),
            "generated_sign_canonical_alpha": sum(
                item["sign_canonical_alpha_generated"] for item in enumeration
            ),
            "unique_after_schedule_caps": len(candidates),
            "precision_stable_replay_candidates": len(replay_candidates),
            "exact_generalized_weierstrass_replays": len(replay_candidates),
            "exact_rational_relation_count": len(exact_relations),
            "certificate_count": 0,
            "counted_relation_count": 0,
        },
        finder_outcome=(
            "EXACT_Q_RELATION_PROPOSED" if exact_relations else "NO_EXACT_Q_RELATION_WITHIN_FROZEN_BUDGET"
        ),
        counted_relation_count=0,
        relation_certificate_required=True,
    )
    return output


def compose_with_relation_certificate(
    proposer_report: dict,
    lift: dict,
    source: dict,
    local_config: dict | None = None,
) -> dict:
    """Bind exact-Q proposer hits through the independent exact certificate layer."""

    if not isinstance(proposer_report, dict) or proposer_report.get("status") != "OK":
        raise ValueError("proposer report is not a completed report")
    projection = {
        "row_id": lift.get("row_id"),
        "r": lift.get("r"),
        "ainvs": lift.get("ainvs"),
        "selected_points": lift.get("points"),
    }
    validate_row(projection)
    if proposer_report.get("input_sha256") != _sha256(projection):
        raise ValueError("proposer report is not bound to this lift projection")
    vectors = proposer_report.get("exact_rational_relations")
    if not isinstance(vectors, list):
        raise ValueError("proposer report has malformed exact relation list")
    replay = relation_certificate.replay_supplied_candidates(
        lift, source, vectors, local_config
    )
    return {
        "schema": "xedni.pari-relation-certificate-composition/v1",
        "status": "exact_certificate_replay_complete",
        "row_id": lift.get("row_id"),
        "phase_separation": {
            "proposer_used_source_scalars": False,
            "source_first_used_by": "relation_certificate",
            "heuristic_proposer_is_certificate": False,
        },
        "proposer_input_sha256": proposer_report["input_sha256"],
        "proposer_exact_Q_relation_count": len(vectors),
        "certificate_replay": replay,
        "counted_relation_count": replay["counted_relation_count"],
    }


def _streams(input_path: str, output_path: str):
    source = sys.stdin if input_path == "-" else Path(input_path).open(encoding="utf-8")
    destination = sys.stdout if output_path == "-" else Path(output_path).open("w", encoding="utf-8")
    return source, destination


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSONL path or - for stdin")
    parser.add_argument("--output", default="-", help="JSONL path or - for stdout")
    parser.add_argument("--gp", default="gp")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--parisizemax", type=int, default=PARISIZEMAX)
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.parisizemax <= 0:
        parser.error("timeout must be finite and positive; parisizemax must be positive")
    tool = invariants.probe_tool(args.gp)
    source, destination = _streams(args.input, args.output)
    close_source, close_destination = source is not sys.stdin, destination is not sys.stdout
    try:
        for line_number, line in enumerate(source, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                row = {"row_id": f"invalid-json-line-{line_number}"}
                result = _base(row, tool)
                result["input_sha256"] = hashlib.sha256(line.encode()).hexdigest()
                result["input_line_bytes"] = len(line.encode())
                result.update(reason="invalid_json", error=str(error))
            else:
                result = process_row(row, tool, args.timeout, args.parisizemax)
            destination.write(_canonical(result) + "\n")
            destination.flush()
    finally:
        if close_source:
            source.close()
        if close_destination:
            destination.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
