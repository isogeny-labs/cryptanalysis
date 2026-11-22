#!/usr/bin/env python3
"""Fail-closed PARI adapter for minimal-model and canonical-height invariants.

Input is canonical JSONL with ``row_id``, five integral ``ainvs``, and a
nonempty ``selected_points`` list. Point coordinates are JSON integers or
reduced rational strings such as ``"-5/8"``. Exact model and point maps are
certified with rational arithmetic. PARI ``ellheight`` values are retained as
high-precision numerical approximations, not rigorous real intervals.
"""

from __future__ import annotations

import argparse
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


SCHEMA_VERSION = 1
ADAPTER = "pari-minimal-height-invariants-v1"
REQUIRED_PARI_VERSION = "2.17.2"
BEGIN = "XEDNI_INVARIANTS_BEGIN_V1"
END = "XEDNI_INVARIANTS_END_V1"
AINV_NAMES = ("A1", "A2", "A3", "A4", "A6")
TRANSFORM_NAMES = ("U", "R", "S", "T")


def _canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _input_hash(value) -> str:
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _parse_fraction(value, name: str) -> Fraction:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an exact integer or reduced rational, not bool")
    if isinstance(value, int):
        return Fraction(value)
    if not isinstance(value, str) or not re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?", value):
        raise ValueError(f"{name} must be an exact integer or reduced rational string")
    parsed = Fraction(value)
    if _fraction_text(parsed) != value:
        raise ValueError(f"{name} is not in canonical reduced form")
    return parsed


def _parse_integer(value, name: str) -> int:
    parsed = _parse_fraction(value, name)
    if parsed.denominator != 1:
        raise ValueError(f"{name} must be integral")
    return parsed.numerator


def validate_row(row) -> tuple[str, tuple[int, ...], tuple[tuple[Fraction, Fraction], ...]]:
    if not isinstance(row, dict):
        raise ValueError("row must be a JSON object")
    row_id = row.get("row_id")
    if not isinstance(row_id, str) or not row_id:
        raise ValueError("row_id must be a nonempty string")
    raw_ainvs = row.get("ainvs")
    if not isinstance(raw_ainvs, list) or len(raw_ainvs) != 5:
        raise ValueError("ainvs must contain exactly five integral coefficients")
    ainvs = tuple(_parse_integer(value, f"ainvs[{index}]") for index, value in enumerate(raw_ainvs))
    raw_points = row.get("selected_points")
    if not isinstance(raw_points, list) or not raw_points:
        raise ValueError("selected_points must be a nonempty list")
    points = []
    for index, point in enumerate(raw_points):
        if not isinstance(point, list) or len(point) != 2:
            raise ValueError(f"selected_points[{index}] must be an affine [x,y] pair")
        points.append(
            (
                _parse_fraction(point[0], f"selected_points[{index}][0]"),
                _parse_fraction(point[1], f"selected_points[{index}][1]"),
            )
        )
    return row_id, ainvs, tuple(points)


def curve_discriminant(ainvs: tuple[int, ...]) -> int:
    a1, a2, a3, a4, a6 = ainvs
    b2 = a1 * a1 + 4 * a2
    b4 = a1 * a3 + 2 * a4
    b6 = a3 * a3 + 4 * a6
    b8 = a1 * a1 * a6 + 4 * a2 * a6 - a1 * a3 * a4 + a2 * a3 * a3 - a4 * a4
    return -(b2 * b2 * b8) - 8 * b4**3 - 27 * b6**2 + 9 * b2 * b4 * b6


def on_curve(ainvs, point: tuple[Fraction, Fraction]) -> bool:
    a1, a2, a3, a4, a6 = map(Fraction, ainvs)
    x, y = point
    return y * y + a1 * x * y + a3 * y == x**3 + a2 * x * x + a4 * x + a6


def map_point_to_new(
    point: tuple[Fraction, Fraction], transform: tuple[Fraction, Fraction, Fraction, Fraction]
) -> tuple[Fraction, Fraction]:
    """Apply PARI's old-to-new [u,r,s,t] convention exactly."""

    u, r, s, t = transform
    if u == 0:
        raise ValueError("zero u in model transformation")
    x, y = point
    new_x = (x - r) / (u * u)
    new_y = (y - s * u * u * new_x - t) / (u**3)
    return new_x, new_y


def make_script(
    ainvs: tuple[int, ...],
    points: tuple[tuple[Fraction, Fraction], ...],
    precision_bits: int,
    stability_bits: int = 256,
) -> str:
    coefficient_text = ",".join(str(value) for value in ainvs)
    point_text = ",".join(f"[{_fraction_text(x)},{_fraction_text(y)}]" for x, y in points)
    lines = [
        f"default(realbitprecision,{precision_bits});",
        f"E=ellinit([{coefficient_text}],1);",
        "M=ellminimalmodel(E,&V);",
        "C=ellchangecurve(E,V);",
        "M2=ellminimalmodel(M,&W);",
        "MDI=ellminimaldisc(E);",
        "COND=ellglobalred(M)[1];",
        f"PTS=[{point_text}];",
        "N=#PTS;",
        "MPTS=vector(N,i,ellchangepoint(PTS[i],V));",
        "ON0=vector(N,i,ellisoncurve(E,PTS[i]));",
        "ONM=vector(N,i,ellisoncurve(M,MPTS[i]));",
        "ROUNDTRIP=vector(N,i,ellchangepointinv(MPTS[i],V)==PTS[i]);",
        f"default(realbitprecision,{stability_bits});",
        "HL=vector(N,i,ellheight(M,MPTS[i]));",
        "H0L=vector(N,i,ellheight(E,PTS[i]));",
        "HML=ellheightmatrix(M,MPTS);",
        "HML=(HML+HML~)/2;",
        "DETL=matdet(HML);",
        "HMAXL=vecmax(HL);",
        "if(HMAXL>0,RHOL=log(abs(M.disc))/HMAXL,RHOL=0);",
        "LOWREALPREC=default(realprecision);",
        f"default(realbitprecision,{precision_bits});",
        "H=vector(N,i,ellheight(M,MPTS[i]));",
        "H0=vector(N,i,ellheight(E,PTS[i]));",
        "HM=ellheightmatrix(M,MPTS);",
        "HM=(HM+HM~)/2;",
        "DET=matdet(HM);",
        "HD=vector(N,i,abs(H[i]-H0[i]));",
        "HMAX=vecmax(H);",
        "if(HMAX>0,RHO=log(abs(M.disc))/HMAX,RHO=0);",
        f'print("{BEGIN}");',
        'print("STATUS=OK");',
        'print("REALBITPRECISION=",default(realbitprecision));',
        'print("REALPRECISION=",default(realprecision));',
        f'print("STABILITY_REALBITPRECISION=",{stability_bits});',
        'print("STABILITY_REALPRECISION=",LOWREALPREC);',
        'print("CONSTRUCTION_DISC=",E.disc);',
        'print("MINIMAL_DISC=",M.disc);',
        'print("MINIMAL_DISC_IDEAL=",MDI);',
        'print("CONDUCTOR=",COND);',
    ]
    for name, member in zip(AINV_NAMES, ("a1", "a2", "a3", "a4", "a6")):
        lines.append(f'print("MIN_{name}=",M.{member});')
    for index, name in enumerate(TRANSFORM_NAMES, 1):
        lines.extend(
            [
                f'print("TRANS_{name}_NUM=",numerator(V[{index}]));',
                f'print("TRANS_{name}_DEN=",denominator(V[{index}]));',
            ]
        )
    for i in range(1, len(points) + 1):
        for j in range(1, len(points) + 1):
            lines.extend(
                [
                    f'print("GRAM_{i}_{j}=",HM[{i},{j}]);',
                    f'print("STABILITY_GRAM_{i}_{j}=",HML[{i},{j}]);',
                ]
            )
    curve_members_equal = " && ".join(f"C.{member}==M.{member}" for member in ("a1", "a2", "a3", "a4", "a6"))
    minimal_members_equal = " && ".join(f"M2.{member}==M.{member}" for member in ("a1", "a2", "a3", "a4", "a6"))
    lines.extend(
        [
            f'print("CURVE_MAP_OK=",{curve_members_equal});',
            f'print("MINIMAL_IDEMPOTENT_OK=",{minimal_members_equal});',
            'print("MINIMAL_TRIVIAL_MAP_OK=",W==[1,0,0,0]);',
            'print("DISC_RELATION_OK=",E.disc==M.disc*V[1]^12);',
            'print("MINIMAL_DISC_IDEAL_OK=",MDI==abs(M.disc));',
            'print("POINT_COUNT=",N);',
            'for(i=1,N,print("P",i,"_X_NUM=",numerator(MPTS[i][1])));',
            'for(i=1,N,print("P",i,"_X_DEN=",denominator(MPTS[i][1])));',
            'for(i=1,N,print("P",i,"_Y_NUM=",numerator(MPTS[i][2])));',
            'for(i=1,N,print("P",i,"_Y_DEN=",denominator(MPTS[i][2])));',
            'for(i=1,N,print("P",i,"_ON_CONSTRUCTION=",ON0[i]));',
            'for(i=1,N,print("P",i,"_ON_MINIMAL=",ONM[i]));',
            'for(i=1,N,print("P",i,"_ROUNDTRIP=",ROUNDTRIP[i]));',
            'for(i=1,N,print("P",i,"_HEIGHT=",H[i]));',
            'for(i=1,N,print("P",i,"_HEIGHT_TYPE=",type(H[i])));',
            'for(i=1,N,print("P",i,"_HEIGHT_PRECISION=",if(type(H[i])=="t_REAL",precision(H[i]),0)));',
            'for(i=1,N,print("P",i,"_CONSTRUCTION_HEIGHT=",H0[i]));',
            'for(i=1,N,print("P",i,"_CONSTRUCTION_HEIGHT_TYPE=",type(H0[i])));',
            'for(i=1,N,print("P",i,"_CONSTRUCTION_HEIGHT_PRECISION=",if(type(H0[i])=="t_REAL",precision(H0[i]),0)));',
            'for(i=1,N,print("P",i,"_HEIGHT_DELTA=",HD[i]));',
            'for(i=1,N,print("P",i,"_STABILITY_HEIGHT=",HL[i]));',
            'for(i=1,N,print("P",i,"_STABILITY_CONSTRUCTION_HEIGHT=",H0L[i]));',
            'print("MAX_HEIGHT=",HMAX);',
            'print("MAX_HEIGHT_PRECISION=",if(type(HMAX)=="t_REAL",precision(HMAX),0));',
            'print("RHO=",RHO);',
            'print("RHO_PRECISION=",if(type(RHO)=="t_REAL",precision(RHO),0));',
            'print("STABILITY_MAX_HEIGHT=",HMAXL);',
            'print("STABILITY_RHO=",RHOL);',
            'print("HEIGHT_GRAM_DETERMINANT=",DET);',
            'print("HEIGHT_GRAM_DETERMINANT_PRECISION=",if(type(DET)=="t_REAL",precision(DET),0));',
            'print("STABILITY_HEIGHT_GRAM_DETERMINANT=",DETL);',
            f'print("{END}");',
            "quit();",
        ]
    )
    return "\n".join(lines) + "\n"


def _expected_keys(point_count: int) -> set[str]:
    keys = {
        "STATUS", "REALBITPRECISION", "REALPRECISION", "CONSTRUCTION_DISC", "MINIMAL_DISC",
        "MINIMAL_DISC_IDEAL", "CONDUCTOR", "STABILITY_REALBITPRECISION", "STABILITY_REALPRECISION",
        "CURVE_MAP_OK", "MINIMAL_IDEMPOTENT_OK", "MINIMAL_TRIVIAL_MAP_OK",
        "DISC_RELATION_OK", "MINIMAL_DISC_IDEAL_OK", "POINT_COUNT", "MAX_HEIGHT",
        "MAX_HEIGHT_PRECISION", "RHO", "RHO_PRECISION", "STABILITY_MAX_HEIGHT", "STABILITY_RHO",
        "HEIGHT_GRAM_DETERMINANT", "HEIGHT_GRAM_DETERMINANT_PRECISION",
        "STABILITY_HEIGHT_GRAM_DETERMINANT",
    }
    keys.update(f"MIN_{name}" for name in AINV_NAMES)
    for name in TRANSFORM_NAMES:
        keys.update((f"TRANS_{name}_NUM", f"TRANS_{name}_DEN"))
    suffixes = (
        "X_NUM", "X_DEN", "Y_NUM", "Y_DEN", "ON_CONSTRUCTION", "ON_MINIMAL", "ROUNDTRIP",
        "HEIGHT", "HEIGHT_TYPE", "HEIGHT_PRECISION", "CONSTRUCTION_HEIGHT",
        "CONSTRUCTION_HEIGHT_TYPE", "CONSTRUCTION_HEIGHT_PRECISION", "HEIGHT_DELTA",
        "STABILITY_HEIGHT", "STABILITY_CONSTRUCTION_HEIGHT",
    )
    for index in range(1, point_count + 1):
        keys.update(f"P{index}_{suffix}" for suffix in suffixes)
        for other in range(1, point_count + 1):
            keys.update((f"GRAM_{index}_{other}", f"STABILITY_GRAM_{index}_{other}"))
    return keys


def parse_transcript(stdout: str, expected_point_count: int) -> dict[str, str]:
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
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or not value:
            raise ValueError(f"unparseable marker line: {line!r}")
        if key in values:
            raise ValueError(f"duplicate marker key: {key}")
        values[key] = value
    expected = _expected_keys(expected_point_count)
    if set(values) != expected:
        missing, extra = sorted(expected - set(values)), sorted(set(values) - expected)
        raise ValueError(f"marker keys differ; missing={missing}, extra={extra}")
    if values["STATUS"] != "OK":
        raise ValueError(f"unexpected tool status: {values['STATUS']}")
    try:
        actual_count = int(values["POINT_COUNT"])
    except ValueError as error:
        raise ValueError("POINT_COUNT is not integral") from error
    if actual_count != expected_point_count:
        raise ValueError(f"point count differs: {actual_count} != {expected_point_count}")
    return values


def _parse_int(values: dict[str, str], key: str) -> int:
    raw = values[key]
    if not re.fullmatch(r"-?(?:0|[1-9][0-9]*)", raw):
        raise ValueError(f"{key} is not a canonical integer: {raw!r}")
    return int(raw)


def _parse_flag(values: dict[str, str], key: str) -> bool:
    value = _parse_int(values, key)
    if value not in (0, 1):
        raise ValueError(f"{key} is not boolean")
    return bool(value)


def _parse_output_fraction(values: dict[str, str], prefix: str) -> Fraction:
    numerator, denominator = _parse_int(values, f"{prefix}_NUM"), _parse_int(values, f"{prefix}_DEN")
    if denominator <= 0:
        raise ValueError(f"{prefix}_DEN must be positive")
    value = Fraction(numerator, denominator)
    if value.numerator != numerator or value.denominator != denominator:
        raise ValueError(f"{prefix} is not reduced")
    return value


def _parse_decimal(values: dict[str, str], key: str) -> tuple[Decimal, str]:
    raw = re.sub(r"\s+([Ee])", r"\1", values[key])
    if raw not in {"NaN", "Infinity", "+Infinity", "-Infinity"} and not re.fullmatch(
        r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?", raw
    ):
        raise ValueError(f"{key} is not a PARI real literal: {values[key]!r}")
    try:
        return Decimal(raw), raw
    except InvalidOperation as error:
        raise ValueError(f"{key} is not decimal") from error


def _text(value) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def probe_tool(executable: str) -> dict:
    resolved = shutil.which(executable)
    if resolved is None:
        return {
            "available": False, "executable_requested": executable, "executable_resolved": None,
            "version_command": [executable, "--version"], "version_returncode": None,
            "version_stdout": "", "version_stderr": "", "version_timed_out": False,
            "version_timeout_seconds": 15.0, "version_wall_ns": 0,
        }
    command = [resolved, "--version"]
    started, timed_out = time.perf_counter_ns(), False
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        returncode, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as error:
        timed_out, returncode = True, None
        stdout, stderr = _text(error.stdout), _text(error.stderr)
    except OSError as error:
        returncode, stdout, stderr = None, "", f"{type(error).__name__}: {error}"
    return {
        "available": True, "executable_requested": executable, "executable_resolved": resolved,
        "version_command": command, "version_returncode": returncode, "version_stdout": stdout,
        "version_stderr": stderr, "version_timed_out": timed_out, "version_timeout_seconds": 15.0,
        "version_wall_ns": time.perf_counter_ns() - started,
    }


def _base(row, tool: dict) -> dict:
    return {
        "adapter": ADAPTER, "input_sha256": _input_hash(row), "reason": "not_run",
        "row_id": row.get("row_id") if isinstance(row, dict) else None,
        "schema_version": SCHEMA_VERSION, "status": "UNKNOWN", "tool": tool,
    }


def _relative_close(left: Decimal, right: Decimal, decimal_digits: int) -> bool:
    if not left.is_finite() or not right.is_finite():
        return False
    with localcontext() as context:
        context.prec = decimal_digits + 20
        scale = max(abs(left), abs(right), Decimal(1))
        tolerance = Decimal(10) ** (-(max(20, decimal_digits - 12)))
        return abs(left - right) <= tolerance * scale


def stable_decimal_key(value: Decimal, significant_digits: int = 40) -> str:
    """Round a positive finite score deterministically for frozen M1 ordering."""

    if not value.is_finite() or value <= 0:
        raise ValueError("stable score must be positive and finite")
    with localcontext(Context(prec=significant_digits + 10, rounding=ROUND_HALF_EVEN)):
        quantum = Decimal(1).scaleb(value.adjusted() - significant_digits + 1)
        rounded = value.quantize(quantum)
        return format(rounded, f".{significant_digits - 1}E")


def stable_selection_components(key: str) -> tuple[int, str]:
    """Return numerically sortable exponent/significand components for a positive key."""

    value = Decimal(key)
    if not value.is_finite() or value <= 0:
        raise ValueError("stable key must be positive and finite")
    digits = "".join(str(digit) for digit in value.as_tuple().digits)
    return value.adjusted(), digits


def selection_evidence(record) -> dict:
    """Replay the precision-stable values used to freeze an M1 candidate."""

    stability = record["rho_stability"]
    height_text = record["max_canonical_height"]
    low_height_text = stability["low_precision_max_height"]
    rho_text, low_rho_text = record["rho"], stability["low_precision_rho"]
    score_texts = (height_text, low_height_text, rho_text, low_rho_text)
    if not all(isinstance(value, str) for value in score_texts):
        raise ValueError("selection scores must be decimal strings")
    max_height = stable_decimal_key(Decimal(height_text))
    if max_height != stable_decimal_key(Decimal(low_height_text)):
        raise ValueError("stable maximum-height key does not replay")
    rho = stable_decimal_key(Decimal(rho_text))
    if rho != stability["stable_40_significant_digit_key"] or rho != stable_decimal_key(
        Decimal(low_rho_text)
    ):
        raise ValueError("stable rho key does not replay")
    key = [
        *stable_selection_components(rho), record["candidate_sha256"], record["row_id"]
    ]
    if key != record["stable_selection_key"]:
        raise ValueError("stable rho key does not replay")
    return {
        "raw_delta": record["construction_discriminant"],
        "delta_min": record["minimal_model"]["discriminant"],
        "max_height": max_height,
        "candidate_sha256": record["candidate_sha256"],
        "stable_selection_key": key,
    }


def process_row(
    row, tool: dict, timeout: float, precision_bits: int, stability_bits: int = 256
) -> dict:
    output = _base(row, tool)
    try:
        row_id, ainvs, points = validate_row(row)
    except ValueError as error:
        output.update(reason="invalid_input", error=str(error))
        return output
    output["row_id"] = row_id
    output["ainvs"] = [str(value) for value in ainvs]
    output["selected_points"] = [[_fraction_text(x), _fraction_text(y)] for x, y in points]
    candidate_material = {
        "ainvs": output["ainvs"],
        "selected_points": output["selected_points"],
    }
    output["candidate_sha256"] = _input_hash(candidate_material)
    construction_disc = curve_discriminant(ainvs)
    output["construction_discriminant"] = str(construction_disc)
    if construction_disc == 0:
        output["reason"] = "singular_curve"
        return output
    for index, point in enumerate(points):
        if not on_curve(ainvs, point):
            output.update(reason="point_not_on_construction_curve", error=f"selected_points[{index}] is off curve")
            return output
    if not tool["available"]:
        output.update(reason="missing_tool", error=f"executable not found: {tool['executable_requested']}")
        return output
    if tool["version_returncode"] != 0 or tool["version_timed_out"]:
        output["reason"] = "version_probe_failed"
        return output
    version_transcript = tool["version_stdout"] + tool["version_stderr"]
    if REQUIRED_PARI_VERSION not in version_transcript:
        output.update(
            reason="unsupported_pari_version",
            error=f"required PARI/GP version {REQUIRED_PARI_VERSION}",
        )
        return output

    script = make_script(ainvs, points, precision_bits, stability_bits)
    command = [tool["executable_resolved"], "-q", "-f"]
    execution = {
        "command": command, "returncode": None, "script": script,
        "script_sha256": hashlib.sha256(script.encode()).hexdigest(), "stderr": "", "stdout": "",
        "timed_out": False, "timeout_seconds": timeout, "wall_ns": 0,
    }
    started = time.perf_counter_ns()
    try:
        completed = subprocess.run(command, input=script, capture_output=True, text=True, timeout=timeout, check=False)
        execution.update(returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
    except subprocess.TimeoutExpired as error:
        execution.update(timed_out=True, stdout=_text(error.stdout), stderr=_text(error.stderr))
        output["reason"] = "timeout"
    except OSError as error:
        execution["stderr"], output["reason"] = f"{type(error).__name__}: {error}", "launch_error"
    execution["wall_ns"] = time.perf_counter_ns() - started
    output["execution"] = execution
    if output["reason"] in {"timeout", "launch_error"}:
        return output
    if execution["returncode"] != 0:
        output["reason"] = "tool_nonzero_exit"
        return output
    try:
        parsed = parse_transcript(execution["stdout"], len(points))
        actual_precision_bits = _parse_int(parsed, "REALBITPRECISION")
        actual_realprecision = _parse_int(parsed, "REALPRECISION")
        actual_stability_bits = _parse_int(parsed, "STABILITY_REALBITPRECISION")
        actual_stability_realprecision = _parse_int(parsed, "STABILITY_REALPRECISION")
        parsed_construction_disc = _parse_int(parsed, "CONSTRUCTION_DISC")
        minimal_disc = _parse_int(parsed, "MINIMAL_DISC")
        minimal_disc_ideal = _parse_int(parsed, "MINIMAL_DISC_IDEAL")
        conductor = _parse_int(parsed, "CONDUCTOR")
        minimal_ainvs = tuple(_parse_int(parsed, f"MIN_{name}") for name in AINV_NAMES)
        transform = tuple(_parse_output_fraction(parsed, f"TRANS_{name}") for name in TRANSFORM_NAMES)
        model_flags = {key: _parse_flag(parsed, key) for key in (
            "CURVE_MAP_OK", "MINIMAL_IDEMPOTENT_OK", "MINIMAL_TRIVIAL_MAP_OK",
            "DISC_RELATION_OK", "MINIMAL_DISC_IDEAL_OK",
        )}
    except ValueError as error:
        output.update(reason="parser_error", error=str(error))
        return output

    if (
        actual_precision_bits != precision_bits
        or actual_stability_bits != stability_bits
        or actual_realprecision <= 0
        or actual_stability_realprecision <= 0
    ):
        output["reason"] = "precision_mismatch"
        return output
    if parsed_construction_disc != construction_disc or minimal_disc == 0 or conductor <= 0:
        output["reason"] = "bad_discriminant"
        return output
    if not all(model_flags.values()):
        output.update(reason="bad_minimal_model_map", proof_flags=model_flags)
        return output
    u = transform[0]
    if u <= 0 or Fraction(minimal_disc) * u**12 != construction_disc:
        output["reason"] = "bad_minimal_model_map"
        return output
    if minimal_disc_ideal != abs(minimal_disc):
        output["reason"] = "bad_minimal_discriminant"
        return output

    mapped_points, height_records = [], []
    try:
        for index, source_point in enumerate(points, 1):
            mapped = (_parse_output_fraction(parsed, f"P{index}_X"), _parse_output_fraction(parsed, f"P{index}_Y"))
            point_flags = {
                "on_construction": _parse_flag(parsed, f"P{index}_ON_CONSTRUCTION"),
                "on_minimal": _parse_flag(parsed, f"P{index}_ON_MINIMAL"),
                "roundtrip": _parse_flag(parsed, f"P{index}_ROUNDTRIP"),
            }
            if not all(point_flags.values()):
                output.update(reason="bad_point_map", failed_point_index=index - 1)
                return output
            independently_mapped = map_point_to_new(source_point, transform)
            if mapped != independently_mapped or not on_curve(minimal_ainvs, mapped):
                output.update(reason="bad_point_map", failed_point_index=index - 1)
                return output
            height, height_text = _parse_decimal(parsed, f"P{index}_HEIGHT")
            construction_height, construction_height_text = _parse_decimal(parsed, f"P{index}_CONSTRUCTION_HEIGHT")
            height_delta, height_delta_text = _parse_decimal(parsed, f"P{index}_HEIGHT_DELTA")
            stability_height, stability_height_text = _parse_decimal(parsed, f"P{index}_STABILITY_HEIGHT")
            stability_construction_height, stability_construction_height_text = _parse_decimal(
                parsed, f"P{index}_STABILITY_CONSTRUCTION_HEIGHT"
            )
            mapped_points.append(mapped)
            height_records.append({
                "construction_height": construction_height,
                "construction_height_precision": _parse_int(parsed, f"P{index}_CONSTRUCTION_HEIGHT_PRECISION"),
                "construction_height_text": construction_height_text,
                "construction_height_type": parsed[f"P{index}_CONSTRUCTION_HEIGHT_TYPE"],
                "height": height, "height_delta": height_delta, "height_delta_text": height_delta_text,
                "height_precision": _parse_int(parsed, f"P{index}_HEIGHT_PRECISION"),
                "height_text": height_text, "height_type": parsed[f"P{index}_HEIGHT_TYPE"],
                "stability_construction_height": stability_construction_height,
                "stability_construction_height_text": stability_construction_height_text,
                "stability_height": stability_height,
                "stability_height_text": stability_height_text,
                "point_flags": point_flags,
            })
        maximum_height, maximum_height_text = _parse_decimal(parsed, "MAX_HEIGHT")
        maximum_height_precision = _parse_int(parsed, "MAX_HEIGHT_PRECISION")
        rho, rho_text = _parse_decimal(parsed, "RHO")
        rho_precision = _parse_int(parsed, "RHO_PRECISION")
        stability_maximum, stability_maximum_text = _parse_decimal(parsed, "STABILITY_MAX_HEIGHT")
        stability_rho, stability_rho_text = _parse_decimal(parsed, "STABILITY_RHO")
        gram, gram_text, stability_gram, stability_gram_text = [], [], [], []
        for i in range(1, len(points) + 1):
            gram_row, gram_text_row, stability_row, stability_text_row = [], [], [], []
            for j in range(1, len(points) + 1):
                value, rendered = _parse_decimal(parsed, f"GRAM_{i}_{j}")
                stability_value, stability_rendered = _parse_decimal(
                    parsed, f"STABILITY_GRAM_{i}_{j}"
                )
                gram_row.append(value)
                gram_text_row.append(rendered)
                stability_row.append(stability_value)
                stability_text_row.append(stability_rendered)
            gram.append(gram_row)
            gram_text.append(gram_text_row)
            stability_gram.append(stability_row)
            stability_gram_text.append(stability_text_row)
        gram_determinant, gram_determinant_text = _parse_decimal(
            parsed, "HEIGHT_GRAM_DETERMINANT"
        )
        gram_determinant_precision = _parse_int(
            parsed, "HEIGHT_GRAM_DETERMINANT_PRECISION"
        )
        stability_gram_determinant, stability_gram_determinant_text = _parse_decimal(
            parsed, "STABILITY_HEIGHT_GRAM_DETERMINANT"
        )
    except ValueError as error:
        output.update(reason="parser_error", error=str(error))
        return output

    decimal_digits = max(30, int(precision_bits * math.log10(2)))
    stability_digits = max(30, int(stability_bits * math.log10(2)))
    for index, record in enumerate(height_records):
        numeric_values = (
            record["height"], record["construction_height"], record["height_delta"],
            record["stability_height"], record["stability_construction_height"],
        )
        if not all(value.is_finite() for value in numeric_values):
            output.update(reason="nonfinite_height", failed_point_index=index)
            return output
        if record["height"] == 0 or record["construction_height"] == 0:
            output.update(reason="zero_height", failed_point_index=index)
            return output
        if record["stability_height"] <= 0 or record["stability_construction_height"] <= 0:
            output.update(reason="nonpositive_stability_height", failed_point_index=index)
            return output
        if record["height"] < 0 or record["construction_height"] < 0 or record["height_delta"] < 0:
            output.update(reason="negative_height", failed_point_index=index)
            return output
        if record["height_type"] != "t_REAL" or record["construction_height_type"] != "t_REAL":
            output.update(reason="unexpected_height_type", failed_point_index=index)
            return output
        if record["height_precision"] <= 0 or record["construction_height_precision"] <= 0:
            output.update(reason="missing_height_precision", failed_point_index=index)
            return output
        if not _relative_close(record["height"], record["construction_height"], decimal_digits):
            output.update(reason="height_invariance_failure", failed_point_index=index)
            return output
        if not _relative_close(
            record["stability_height"], record["stability_construction_height"], stability_digits
        ):
            output.update(reason="stability_height_invariance_failure", failed_point_index=index)
            return output
        if not _relative_close(record["height"], record["stability_height"], stability_digits):
            output.update(reason="height_precision_instability", failed_point_index=index)
            return output
        expected_delta = abs(record["height"] - record["construction_height"])
        if not _relative_close(record["height_delta"], expected_delta, decimal_digits):
            output.update(reason="height_delta_mismatch", failed_point_index=index)
            return output

    for i in range(len(points)):
        for j in range(len(points)):
            values = (gram[i][j], stability_gram[i][j])
            if not all(value.is_finite() for value in values):
                output["reason"] = "nonfinite_height_gram"
                return output
            if gram[i][j] != gram[j][i] or stability_gram[i][j] != stability_gram[j][i]:
                output["reason"] = "nonsymmetric_height_gram"
                return output
            if not _relative_close(gram[i][j], stability_gram[i][j], stability_digits):
                output["reason"] = "height_gram_precision_instability"
                return output
        if not _relative_close(gram[i][i], height_records[i]["height"], decimal_digits):
            output["reason"] = "height_gram_diagonal_mismatch"
            return output
    if not gram_determinant.is_finite() or not stability_gram_determinant.is_finite():
        output["reason"] = "nonfinite_height_gram_determinant"
        return output
    if not _relative_close(
        gram_determinant, stability_gram_determinant, stability_digits
    ):
        output["reason"] = "height_gram_determinant_precision_instability"
        return output
    if gram_determinant != 0 and gram_determinant_precision <= 0:
        output["reason"] = "missing_height_gram_determinant_precision"
        return output

    if not maximum_height.is_finite() or maximum_height <= 0:
        output["reason"] = "nonfinite_or_nonpositive_max_height"
        return output
    if maximum_height_precision <= 0:
        output["reason"] = "missing_height_precision"
        return output
    expected_maximum = max(record["height"] for record in height_records)
    if not _relative_close(maximum_height, expected_maximum, decimal_digits):
        output["reason"] = "max_height_mismatch"
        return output
    if not rho.is_finite() or rho <= 0 or rho_precision <= 0:
        output["reason"] = "nonfinite_or_nonpositive_rho"
        return output
    if (
        not stability_maximum.is_finite()
        or stability_maximum <= 0
        or not stability_rho.is_finite()
        or stability_rho <= 0
    ):
        output["reason"] = "nonfinite_or_nonpositive_stability_score"
        return output
    if not _relative_close(maximum_height, stability_maximum, stability_digits):
        output["reason"] = "max_height_precision_instability"
        return output
    with localcontext() as context:
        context.prec = decimal_digits + 20
        expected_rho = Decimal(abs(minimal_disc)).ln() / maximum_height
    if not _relative_close(rho, expected_rho, decimal_digits):
        output["reason"] = "rho_mismatch"
        return output
    if not _relative_close(rho, stability_rho, stability_digits):
        output["reason"] = "rho_precision_instability"
        return output
    try:
        rho_key = stable_decimal_key(rho)
        stability_rho_key = stable_decimal_key(stability_rho)
    except ValueError as error:
        output.update(reason="rho_stable_key_error", error=str(error))
        return output
    if rho_key != stability_rho_key:
        output["reason"] = "rho_stable_key_instability"
        return output
    if stable_decimal_key(maximum_height) != stable_decimal_key(stability_maximum):
        output["reason"] = "max_height_stable_key_instability"
        return output
    try:
        rho_exponent, rho_significand = stable_selection_components(rho_key)
    except ValueError as error:
        output.update(reason="rho_stable_key_error", error=str(error))
        return output
    with localcontext() as context:
        context.prec = decimal_digits + 20
        rho_stability_difference = str(abs(rho - stability_rho))

    output["minimal_model"] = {
        "ainvs": [str(value) for value in minimal_ainvs], "discriminant": str(minimal_disc),
        "minimal_discriminant_ideal_norm": str(minimal_disc_ideal),
        "transformation": {
            "convention": "old x=u^2*x_new+r; old y=u^3*y_new+s*u^2*x_new+t",
            "r": _fraction_text(transform[1]), "s": _fraction_text(transform[2]),
            "t": _fraction_text(transform[3]), "u": _fraction_text(transform[0]),
        },
    }
    output["mapped_points"] = [{
        "canonical_height": record["height_text"],
        "canonical_height_on_construction_model": record["construction_height_text"],
        "height_delta": record["height_delta_text"], "height_precision": record["height_precision"],
        "stability_canonical_height": record["stability_height_text"],
        "minimal_point": [_fraction_text(point[0]), _fraction_text(point[1])],
    } for point, record in zip(mapped_points, height_records)]
    invariant_evidence = {
        "conductor": str(conductor),
        "height_gram_matrix": gram_text,
        "height_gram_determinant": gram_determinant_text,
        "max_canonical_height": maximum_height_text,
        "minimal_discriminant": str(minimal_disc),
        "rho": rho_text,
    }
    output.update(
        max_canonical_height=maximum_height_text, max_height_precision=maximum_height_precision,
        rho=rho_text, rho_precision=rho_precision,
        rho_stability={
            "absolute_difference": rho_stability_difference,
            "high_bits": actual_precision_bits,
            "low_bits": actual_stability_bits,
            "low_precision_max_height": stability_maximum_text,
            "low_precision_rho": stability_rho_text,
            "stable_40_significant_digit_key": rho_key,
        },
        stable_selection_key=[
            rho_exponent,
            rho_significand,
            output["candidate_sha256"],
            row_id,
        ],
        conductor=str(conductor),
        height_gram_matrix=gram_text,
        height_gram_stability={
            "high_bits": actual_precision_bits,
            "low_bits": actual_stability_bits,
            "low_precision_matrix": stability_gram_text,
        },
        selected_height_determinant={
            "certified_real_interval": False,
            "is_regulator": False,
            "meaning": "determinant of the selected-point Neron-Tate Gram matrix",
            "numerical_approximation": gram_determinant_text,
            "precision": gram_determinant_precision,
            "stability_value": stability_gram_determinant_text,
        },
        mordell_weil_regulator={
            "status": "UNAVAILABLE_BASIS_NOT_ESTABLISHED",
            "value": None,
            "reason": "a saturated Mordell-Weil basis modulo torsion has not been established",
        },
        minimum_height_lower_bound={
            "status": "UNAVAILABLE_NOT_CERTIFIED",
            "certified": False,
            "value": None,
            "reason": "PARI ellheight does not return a rigorous global minimum-height lower-bound certificate",
        },
        invariant_evidence_sha256=_input_hash(invariant_evidence),
        height_semantics={
            "certified_real_interval": False, "field": "Q", "function": "ellheight",
            "meaning": "global Neron-Tate height in Cremona normalization; over Q this is canonical height",
            "numerical_approximation": True, "realbitprecision": actual_precision_bits,
            "realprecision": actual_realprecision,
            "stability_realbitprecision": actual_stability_bits,
            "stable_score_rounding": "40 significant decimal digits, ROUND_HALF_EVEN",
            "stable_score_order": "numeric exponent, then 40-digit significand",
            "stable_score_tie_break": "candidate_sha256 then row_id, lexical order",
        },
        proof_flags={
            **model_flags, "exact_python_discriminant_check": True, "exact_python_point_map_check": True,
            "exact_python_points_on_models": True, "height_model_invariance_numerically_checked": True,
        },
        status="OK", reason="computed",
    )
    output["selection_evidence_sha256"] = _input_hash(selection_evidence(output))
    return output


def _streams(input_path: str, output_path: str):
    source = sys.stdin if input_path == "-" else Path(input_path).open(encoding="utf-8")
    destination = sys.stdout if output_path == "-" else Path(output_path).open("w", encoding="utf-8")
    return source, destination


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="JSONL path or - for stdin")
    parser.add_argument("--output", default="-", help="JSONL path or - for stdout")
    parser.add_argument("--gp", default="gp")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--precision-bits", type=int, default=384)
    parser.add_argument("--stability-bits", type=int, default=256)
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("timeout must be finite and positive")
    if args.precision_bits < 128:
        parser.error("precision-bits must be at least 128")
    if args.stability_bits < 128 or args.stability_bits >= args.precision_bits:
        parser.error("stability-bits must be at least 128 and less than precision-bits")
    tool = probe_tool(args.gp)
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
                result = process_row(
                    row, tool, args.timeout, args.precision_bits, args.stability_bits
                )
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
