#!/usr/bin/env python3
"""Public/private isolation primitives for natural Xedni rows.

This module is intentionally independent of the natural runner.  It provides
the schema, redaction, formula binding, state ordering, and container boundary
that a future runner must compose.  A Python dictionary projection is not an
isolation boundary; production public tools are launched in a networkless,
read-only container that receives one redacted input mount and no host
environment or file descriptors.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from fractions import Fraction
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import re
import secrets
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Mapping, Sequence

import field as ec_field


PRIVATE_SOURCE_SCHEMA = "xedni-rank-decay-source/v1"
PUBLIC_SOURCE_SCHEMA = "xedni-public-source/v1"
LINK_SCHEMA = "xedni-public-private-link/v1"
PUBLIC_LIFT_SCHEMA = "xedni-public-lift/v1"
PUBLIC_CANDIDATE_SCHEMA = "xedni-public-candidate/v1"
CANDIDATE_BINDING_SCHEMA = "xedni-public-candidate-binding/v1"
M3_FORMULA_INPUT_SCHEMA = "xedni-m3-formula-input/v1"
M3_FORMULA_SPEC_SCHEMA = "xedni-m3-formula-spec/v1"
M3_FEATURE_SCHEMA = "xedni-m3-formula-feature/v1"
DIRECT_SEARCH_COST_SCHEMA = "xedni-direct-source-search-cost/v1"
DIRECT_SEARCH_ADAPTER_SPEC_SCHEMA = "xedni-direct-source-search-adapter-spec/v1"
DIRECT_SEARCH_BUNDLE_SCHEMA = "xedni-direct-source-search-bundle/v1"
STAGE_LEDGER_SCHEMA = "xedni-public-private-stage-ledger/v1"
PUBLIC_RUN_SCHEMA = "xedni-public-container-run/v1"
PRIVATE_REPLAY_LINK_SCHEMA = "xedni-private-replay-link/v1"
ISOLATION_CANARY_SCHEMA = "xedni-public-isolation-canary/v1"

# The primitives below pass their adversarial controls, but the existing
# natural runner does not yet call them or bind them into FREEZE.json.
PRODUCTION_READY = False
PRODUCTION_BLOCKER = "not integrated into the freeze-bound natural executor"

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+/-]{0,191}\Z")
PINNED_IMAGE = re.compile(r"(?:[^@\s]+@)?sha256:[0-9a-f]{64}\Z")
RATIONAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?\Z")

PRIVATE_SOURCE_KEYS = {
    "schema",
    "master_seed",
    "source_id",
    "source_index",
    "p",
    "bits",
    "family",
    "curve",
    "cardinality",
    "cardinality_factors",
    "cardinality_backend",
    "cardinality_evidence",
    "source_subgroup_order",
    "source_cofactor",
    "base_point",
    "base_point_order",
    "point_sampling_attempts",
    "scalar_sampling_attempts",
    "max_r",
    "ordered_scalars",
    "ordered_points",
    "prefix_permutation",
    "prefixes",
}
PUBLIC_SOURCE_KEYS = {
    "schema",
    "public_source_id",
    "link_id",
    "p",
    "bits",
    "curve",
    "cardinality",
    "cardinality_factors",
    "source_subgroup_order",
    "source_cofactor",
    "base_point",
    "base_point_order",
    "max_r",
    "ordered_points",
    "prefixes",
    "public_payload_sha256",
}
LINK_KEYS = {
    "schema",
    "link_nonce_hex",
    "private_source_sha256",
    "public_source_sha256",
    "public_payload_sha256",
    "link_id",
    "nonce_provenance",
    "production_eligible",
}
PUBLIC_CANDIDATE_KEYS = {
    "schema",
    "public_source_sha256",
    "public_lift_sha256",
    "ainvs",
    "selected_points",
    "construction_work",
}
PUBLIC_LIFT_KEYS = {
    "schema",
    "public_source_sha256",
    "private_lift_sha256",
    "r",
    "selected_indices",
    "ainvs",
    "selected_points",
    "model_sha256",
    "public_lift_sha256",
}
M3_FORMULA_INPUT_KEYS = {
    "schema",
    "selected_points",
    "formula_input_sha256",
}
WORK_KEYS = {
    "attempts",
    "rejections",
    "public_group_operations",
    "cpu_ns",
    "retained_bytes",
}
CANDIDATE_BINDING_KEYS = {
    "schema",
    "candidate_id",
    "candidate_sha256",
    "construction_work_sha256",
    "tie_break_rule",
    "tie_break_key",
    "formula_input_sha256",
    "binding_sha256",
}
FORMULA_SPEC_KEYS = {
    "schema",
    "formula_id",
    "implementation_sha256",
    "candidate_schema",
    "formula_input_schema",
    "formula_ast",
    "formula_ast_sha256",
    "spec_sha256",
}
M3_FEATURE_KEYS = {
    "schema",
    "formula_spec_sha256",
    "formula_id",
    "formula_implementation_sha256",
    "formula_input_sha256",
    "value",
    "executable",
    "executable_sha256",
    "script_sha256",
    "feature_sha256",
}
DIRECT_SEARCH_COST_KEYS = {
    "schema",
    "algorithm",
    "adapter_spec_sha256",
    "script_sha256",
    "public_source_sha256",
    "tool_identity",
    "counters",
    "transcript",
    "transcript_sha256",
    "complete",
    "cost_sha256",
}
DIRECT_ADAPTER_SPEC_KEYS = {
    "schema",
    "algorithm",
    "input_schema",
    "output_schema",
    "image",
    "script_sha256",
    "spec_sha256",
}
DIRECT_BUNDLE_KEYS = {
    "schema",
    "adapter_spec",
    "execution",
    "cost",
    "bundle_sha256",
}
DIRECT_TOOL_KEYS = {"name", "version", "executable_sha256"}
DIRECT_COUNTER_KEYS = {"group_operations", "cpu_ns", "candidates_tested"}
DIRECT_TRANSCRIPT_KEYS = {
    "schema",
    "input_sha256",
    "status",
    "candidates_tested",
    "group_operations",
    "result_coefficients",
}
STAGE_KEYS = {"schema", "row_id", "events", "chain_sha256"}
STAGES = (
    "private_validated",
    "public_redacted",
    "public_selected",
    "public_relation_proposed",
    "private_replayed",
    "public_ranked",
)

# These tokens may not occur as key components in a public-boundary object.
# Exact schemas are the primary defense against an innocuous-name smuggle.
FORBIDDEN_PUBLIC_KEY_TOKENS = frozenset(
    {
        "scalar",
        "scalars",
        "seed",
        "private",
        "secret",
        "master",
        "relation",
        "rank",
        "recovery",
        "known",
    }
)

M3_FORMULA_AST = {
    "schema": "xedni-m3-formula-ast/v1",
    "index_origin": 1,
    "reduction": "sum",
    "term": {
        "op": "multiply_index",
        "value": {
            "op": "add",
            "args": [
                {"op": "square", "var": "x"},
                {"op": "multiply", "left": "x", "right": "y"},
                {"op": "square", "var": "y"},
            ],
        },
    },
}

# This is the complete code executed for the M3 formula inside the pinned
# public-only image.  The launcher, evidence, and output all bind its digest.
M3_CONTAINER_SCRIPT = r'''import hashlib,json,os,shutil,sys
from fractions import Fraction
def reject_constant(value): raise ValueError("nonfinite JSON")
def no_duplicates(pairs):
 d={}
 for k,v in pairs:
  if k in d: raise ValueError("duplicate JSON key")
  d[k]=v
 return d
def canonical(v): return json.dumps(v,allow_nan=False,ensure_ascii=True,separators=(",",":"),sort_keys=True).encode("ascii")
raw=open(sys.argv[1],"rb").read()
value=json.loads(raw,parse_constant=reject_constant,object_pairs_hook=no_duplicates)
if set(value)!={"schema","selected_points","formula_input_sha256"} or value["schema"]!="xedni-m3-formula-input/v1": raise ValueError("formula input schema")
payload={"schema":value["schema"],"selected_points":value["selected_points"]}
if hashlib.sha256(canonical(payload)).hexdigest()!=value["formula_input_sha256"]: raise ValueError("formula input hash")
total=Fraction(0)
for i,point in enumerate(value["selected_points"],1):
 if not isinstance(point,list) or len(point)!=2: raise ValueError("point schema")
 x,y=Fraction(point[0]),Fraction(point[1])
 total+=i*(x*x+x*y+y*y)
text=str(total.numerator) if total.denominator==1 else f"{total.numerator}/{total.denominator}"
exe=os.path.realpath(sys.executable) if sys.executable and os.path.isfile(sys.executable) else shutil.which("python3")
if not exe or not os.path.isfile(exe): raise ValueError("python executable identity unavailable")
h=hashlib.sha256()
with open(exe,"rb") as stream:
 while True:
  block=stream.read(1048576)
  if not block: break
  h.update(block)
out={"schema":"xedni-m3-formula-feature/v1","formula_spec_sha256":sys.argv[2],"formula_id":"M3-C1-coordinate-quadratic-v1","formula_implementation_sha256":sys.argv[3],"formula_input_sha256":value["formula_input_sha256"],"value":text,"executable":exe,"executable_sha256":h.hexdigest(),"script_sha256":sys.argv[4]}
out["feature_sha256"]=hashlib.sha256(canonical(out)).hexdigest()
print(canonical(out).decode("ascii"))'''

DIRECT_SEARCH_ADAPTER_SCRIPT = r'''import hashlib,json,math,os,shutil,sys,time
def reject_constant(value): raise ValueError("nonfinite JSON")
def no_duplicates(pairs):
 d={}
 for k,v in pairs:
  if k in d: raise ValueError("duplicate JSON key")
  d[k]=v
 return d
def canonical(v): return json.dumps(v,allow_nan=False,ensure_ascii=True,separators=(",",":"),sort_keys=True).encode("ascii")
source=json.loads(open(sys.argv[1]).read(),parse_constant=reject_constant,object_pairs_hook=no_duplicates)
p=source["p"]; a=source["curve"]["a"]; q=source["source_subgroup_order"]; G=tuple(source["base_point"]); ops=0
def add(P,Q):
 global ops
 ops+=1
 if P is None: return Q
 if Q is None: return P
 x1,y1=P; x2,y2=Q
 if x1==x2 and (y1+y2)%p==0: return None
 if P==Q:
  if y1%p==0: return None
  slope=((3*x1*x1+a)*pow(2*y1,-1,p))%p
 else: slope=((y2-y1)*pow((x2-x1)%p,-1,p))%p
 x3=(slope*slope-x1-x2)%p
 return (x3,(slope*(x1-x3)-y1)%p)
def mul(n,P):
 R=None
 while n:
  if n&1: R=add(R,P)
  P=add(P,P); n//=2
 return R
started=time.process_time_ns(); m=math.isqrt(q-1)+1; baby={}; current=None
for j in range(m): baby[current]=j; current=add(current,G)
step=mul(m,G); step=None if step is None else (step[0],(-step[1])%p); coefficients=[]; tested=0
for raw in source["ordered_points"]:
 gamma=tuple(raw); found=None
 for i in range(m+1):
  tested+=1
  if gamma in baby:
   candidate=(i*m+baby[gamma])%q
   if mul(candidate,G)==tuple(raw): found=candidate; break
  gamma=add(gamma,step)
 if found is None: break
 coefficients.append(found)
complete=len(coefficients)==len(source["ordered_points"]); elapsed=max(1,time.process_time_ns()-started)
transcript={"schema":"xedni-direct-source-search-transcript/v1","input_sha256":hashlib.sha256(canonical(source)).hexdigest(),"status":"relation" if complete else "failed","candidates_tested":tested,"group_operations":ops,"result_coefficients":coefficients if complete else None}
exe=os.path.realpath(sys.executable) if sys.executable and os.path.isfile(sys.executable) else shutil.which("python3")
if not exe or not os.path.isfile(exe): raise ValueError("python executable identity unavailable")
h=hashlib.sha256()
with open(exe,"rb") as stream:
 while True:
  block=stream.read(1048576)
  if not block: break
  h.update(block)
payload={"schema":"xedni-direct-source-search-cost/v1","algorithm":"bsgs-v1","adapter_spec_sha256":sys.argv[2],"script_sha256":sys.argv[3],"public_source_sha256":transcript["input_sha256"],"tool_identity":{"name":"python-bsgs-adapter","version":"v1","executable_sha256":h.hexdigest()},"counters":{"group_operations":ops,"cpu_ns":elapsed,"candidates_tested":tested},"transcript":transcript,"transcript_sha256":hashlib.sha256(canonical(transcript)).hexdigest(),"complete":complete}
payload["cost_sha256"]=hashlib.sha256(canonical(payload)).hexdigest()
print(canonical(payload).decode("ascii"))'''


class BoundaryError(ValueError):
    """A schema, redaction, stage, or sandbox boundary is invalid."""


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise BoundaryError("value is not canonical finite JSON") from error


def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _exact(value: Any, keys: set[str], context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BoundaryError(f"{context}: expected an object")
    actual = set(value)
    if actual != keys:
        raise BoundaryError(
            f"{context}: key mismatch; missing={sorted(keys - actual)}, "
            f"extra={sorted(actual - keys)}"
        )
    return value


def _integer(value: Any, context: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BoundaryError(f"{context}: expected an integer")
    if minimum is not None and value < minimum:
        raise BoundaryError(f"{context}: expected an integer >= {minimum}")
    return value


def _is_prime(value: int) -> bool:
    if value < 2 or value % 2 == 0:
        return value == 2
    divisor = 3
    while divisor * divisor <= value:
        if value % divisor == 0:
            return False
        divisor += 2
    return True


def _token(value: Any, context: str) -> str:
    if not isinstance(value, str) or TOKEN.fullmatch(value) is None:
        raise BoundaryError(f"{context}: invalid token")
    return value


def _hex64(value: Any, context: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise BoundaryError(f"{context}: expected lowercase SHA-256")
    return value


def _point(value: Any, context: str) -> list[int]:
    if not isinstance(value, list) or len(value) != 2:
        raise BoundaryError(f"{context}: expected [x,y]")
    return [_integer(value[0], f"{context}[0]"), _integer(value[1], f"{context}[1]")]


def _fraction(value: Any, context: str) -> Fraction:
    if isinstance(value, bool):
        raise BoundaryError(f"{context}: expected an exact rational")
    if isinstance(value, int):
        return Fraction(value)
    if not isinstance(value, str) or RATIONAL.fullmatch(value) is None:
        raise BoundaryError(f"{context}: expected a canonical exact rational")
    parsed = Fraction(value)
    canonical = (
        str(parsed.numerator)
        if parsed.denominator == 1
        else f"{parsed.numerator}/{parsed.denominator}"
    )
    if canonical != value:
        raise BoundaryError(f"{context}: rational is not reduced/canonical")
    return parsed


def _fraction_text(value: Fraction) -> str:
    return (
        str(value.numerator)
        if value.denominator == 1
        else f"{value.numerator}/{value.denominator}"
    )


def _prefixes(value: Any, max_r: int, context: str) -> dict[str, dict[str, Any]]:
    expected = {str(r) for r in range(2, max_r + 1)}
    if not isinstance(value, Mapping) or set(value) != expected:
        raise BoundaryError(f"{context}: expected prefixes exactly for r=2..{max_r}")
    full = value[str(max_r)].get("indices") if isinstance(value[str(max_r)], Mapping) else None
    if not isinstance(full, list) or sorted(full) != list(range(max_r)):
        raise BoundaryError(f"{context}: maximum prefix is not a permutation")
    result: dict[str, dict[str, Any]] = {}
    for name in sorted(expected, key=int):
        item = _exact(value[name], {"indices", "target_index"}, f"{context}.{name}")
        indices = item["indices"]
        r = int(name)
        if (
            not isinstance(indices, list)
            or len(indices) != r
            or any(isinstance(x, bool) or not isinstance(x, int) for x in indices)
            or len(set(indices)) != r
            or any(x < 0 or x >= max_r for x in indices)
        ):
            raise BoundaryError(f"{context}.{name}.indices: invalid prefix")
        if item["target_index"] != indices[-1]:
            raise BoundaryError(f"{context}.{name}.target_index: must be final index")
        if indices != full[:r] or item["target_index"] != full[r - 1]:
            raise BoundaryError(f"{context}.{name}: does not follow frozen prefix permutation")
        result[name] = {"indices": list(indices), "target_index": indices[-1]}
    return result


def validate_private_source(source: Any) -> dict[str, Any]:
    """Validate the generated private source's exact structural schema."""
    source = _exact(source, PRIVATE_SOURCE_KEYS, "private source")
    if source["schema"] != PRIVATE_SOURCE_SCHEMA:
        raise BoundaryError("private source: wrong schema")
    if not isinstance(source["master_seed"], str) or not source["master_seed"]:
        raise BoundaryError("private source.master_seed: expected nonempty text")
    _token(source["source_id"], "private source.source_id")
    _integer(source["source_index"], "private source.source_index", 0)
    p = _integer(source["p"], "private source.p", 3)
    if source["bits"] != p.bit_length():
        raise BoundaryError("private source.bits: does not match p")
    if source["family"] not in ("generic", "j0"):
        raise BoundaryError("private source.family: invalid")
    if source["source_id"] != f"p{p}-{source['family']}-{source['source_index']:08d}":
        raise BoundaryError("private source.source_id: does not bind p/family/source_index")
    curve = _exact(source["curve"], {"a", "b", "generation_attempts"}, "private source.curve")
    for name in ("a", "b"):
        value = _integer(curve[name], f"private source.curve.{name}", 0)
        if value >= p:
            raise BoundaryError(f"private source.curve.{name}: not reduced modulo p")
    _integer(curve["generation_attempts"], "private source.curve.generation_attempts", 1)
    cardinality = _integer(source["cardinality"], "private source.cardinality", 1)
    factors = source["cardinality_factors"]
    if not isinstance(factors, list) or not factors:
        raise BoundaryError("private source.cardinality_factors: expected nonempty list")
    product = 1
    previous = 1
    for index, item in enumerate(factors):
        if not isinstance(item, list) or len(item) != 2:
            raise BoundaryError(f"private source.cardinality_factors[{index}]: invalid")
        q = _integer(item[0], f"private source.factor[{index}].q", 2)
        e = _integer(item[1], f"private source.factor[{index}].e", 1)
        if q <= previous or not _is_prime(q):
            raise BoundaryError("private source.cardinality_factors: not strictly ordered")
        product *= q**e
        previous = q
    if product != cardinality:
        raise BoundaryError("private source.cardinality_factors: product mismatch")
    if not isinstance(source["cardinality_backend"], str) or not source["cardinality_backend"]:
        raise BoundaryError("private source.cardinality_backend: invalid")
    # Evidence is private and backend-dependent.  Canonicality is checked, but
    # no member is copied across the public allowlist below.
    _canonical_bytes(source["cardinality_evidence"])
    subgroup = _integer(source["source_subgroup_order"], "private source.source_subgroup_order", 2)
    cofactor = _integer(source["source_cofactor"], "private source.source_cofactor", 1)
    if (
        subgroup * cofactor != cardinality
        or source["base_point_order"] != subgroup
        or not _is_prime(subgroup)
        or subgroup not in {item[0] for item in factors}
    ):
        raise BoundaryError("private source: subgroup/cofactor certificate mismatch")
    base_point = tuple(_point(source["base_point"], "private source.base_point"))
    a, b = curve["a"], curve["b"]
    if not ec_field.on_curve(base_point, a, b, p):
        raise BoundaryError("private source.base_point: off source curve")
    if ec_field.point_mul(subgroup, base_point, a, p) is not None:
        raise BoundaryError("private source.base_point: subgroup order does not annihilate")
    _integer(source["point_sampling_attempts"], "private source.point_sampling_attempts", 0)
    _integer(source["scalar_sampling_attempts"], "private source.scalar_sampling_attempts", 0)
    max_r = _integer(source["max_r"], "private source.max_r", 2)
    if max_r > 9:
        raise BoundaryError("private source.max_r: exceeds 9")
    scalars = source["ordered_scalars"]
    points = source["ordered_points"]
    permutation = source["prefix_permutation"]
    if not isinstance(scalars, list) or len(scalars) != max_r:
        raise BoundaryError("private source.ordered_scalars: wrong length")
    canonical_scalars = []
    for index, scalar in enumerate(scalars):
        scalar = _integer(scalar, f"private source.ordered_scalars[{index}]", 1)
        if scalar >= subgroup:
            raise BoundaryError(f"private source.ordered_scalars[{index}]: out of range")
        canonical_scalars.append(scalar)
    if not isinstance(points, list) or len(points) != max_r:
        raise BoundaryError("private source.ordered_points: wrong length")
    canonical_points = []
    for index, point in enumerate(points):
        parsed = tuple(_point(point, f"private source.ordered_points[{index}]"))
        if not ec_field.on_curve(parsed, a, b, p):
            raise BoundaryError(f"private source.ordered_points[{index}]: off curve")
        if ec_field.point_mul(canonical_scalars[index], base_point, a, p) != parsed:
            raise BoundaryError(
                f"private source.ordered_points[{index}]: scalar replay failed"
            )
        canonical_points.append(parsed)
    signed = set(canonical_points) | {
        ec_field.point_neg(point, p) for point in canonical_points
    }
    if len(signed) != 2 * max_r:
        raise BoundaryError("private source.ordered_points: not distinct up to sign")
    if (
        not isinstance(permutation, list)
        or sorted(permutation) != list(range(max_r))
    ):
        raise BoundaryError("private source.prefix_permutation: invalid")
    checked_prefixes = _prefixes(source["prefixes"], max_r, "private source.prefixes")
    if checked_prefixes[str(max_r)]["indices"] != permutation:
        raise BoundaryError("private source.prefixes: disagree with prefix_permutation")
    # Round-trip canonical JSON to strip Mapping subclasses/references.
    return json.loads(_canonical_bytes(source))


def _public_payload(private: Mapping[str, Any]) -> dict[str, Any]:
    max_r = private["max_r"]
    payload = {
        "schema": PUBLIC_SOURCE_SCHEMA,
        "public_source_id": "pub-" + _sha(
            {
                "p": private["p"],
                "curve": private["curve"],
                "ordered_points": private["ordered_points"],
                "prefixes": private["prefixes"],
            }
        )[:32],
        "p": private["p"],
        "bits": private["bits"],
        "curve": {
            "a": private["curve"]["a"],
            "b": private["curve"]["b"],
        },
        "cardinality": private["cardinality"],
        "cardinality_factors": private["cardinality_factors"],
        "source_subgroup_order": private["source_subgroup_order"],
        "source_cofactor": private["source_cofactor"],
        "base_point": private["base_point"],
        "base_point_order": private["base_point_order"],
        "max_r": max_r,
        "ordered_points": private["ordered_points"],
        "prefixes": _prefixes(private["prefixes"], max_r, "private source.prefixes"),
    }
    return json.loads(_canonical_bytes(payload))


def _link_id(nonce: bytes, private_sha: str, public_payload_sha: str) -> str:
    material = (
        b"XEDNI-PUBLIC-PRIVATE-LINK-V1\0"
        + nonce
        + bytes.fromhex(private_sha)
        + bytes.fromhex(public_payload_sha)
    )
    return hashlib.sha256(material).hexdigest()


def _validate_nonce(nonce: Any) -> bytes:
    if not isinstance(nonce, bytes) or len(nonce) != 32:
        raise BoundaryError("link nonce must be exactly 32 bytes")
    if nonce == b"\x00" * 32 or len(set(nonce)) < 16:
        raise BoundaryError("link nonce is zero or structurally weak")
    return nonce


def _redact_with_nonce(
    private: Mapping[str, Any], nonce: bytes, provenance: str, production_eligible: bool
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build the public/link pair from a validated nonce and provenance."""
    nonce = _validate_nonce(nonce)
    if provenance not in ("os.urandom", "deterministic_test_only"):
        raise BoundaryError("unrecognized nonce provenance")
    if production_eligible != (provenance == "os.urandom"):
        raise BoundaryError("nonce provenance and production eligibility disagree")
    private_sha = _sha(private)
    payload = _public_payload(private)
    payload_sha = _sha(payload)
    link_id = _link_id(nonce, private_sha, payload_sha)
    public = dict(payload)
    public["link_id"] = link_id
    public["public_payload_sha256"] = payload_sha
    public = json.loads(_canonical_bytes(public))
    validate_public_source(public)
    link = {
        "schema": LINK_SCHEMA,
        "link_nonce_hex": nonce.hex(),
        "private_source_sha256": private_sha,
        "public_source_sha256": _sha(public),
        "public_payload_sha256": payload_sha,
        "link_id": link_id,
        "nonce_provenance": provenance,
        "production_eligible": production_eligible,
    }
    validate_link(link)
    return public, link


def redact_private_source(
    source: Mapping[str, Any], *, link_nonce: bytes | None = None, allow_test_nonce: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return a public source and private link, using OS entropy in production."""
    private = validate_private_source(source)
    if link_nonce is None:
        return _redact_with_nonce(private, secrets.token_bytes(32), "os.urandom", True)
    if not allow_test_nonce:
        raise BoundaryError("caller-supplied link nonce is forbidden in production")
    return _redact_with_nonce(
        private, link_nonce, "deterministic_test_only", False
    )


def _public_key_tokens(key: str) -> set[str]:
    return {part for part in re.split(r"[^a-z0-9]+", key.lower()) if part}


def assert_no_forbidden_public_material(value: Any, context: str = "public") -> None:
    """Recursively reject secret/outcome names in an already exact schema."""
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise BoundaryError(f"{context}: public keys must be strings")
            forbidden = _public_key_tokens(key) & FORBIDDEN_PUBLIC_KEY_TOKENS
            if forbidden:
                raise BoundaryError(
                    f"{context}.{key}: forbidden public key token(s) {sorted(forbidden)}"
                )
            assert_no_forbidden_public_material(nested, f"{context}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            assert_no_forbidden_public_material(nested, f"{context}[{index}]")
    elif value is not None and not isinstance(value, (str, int, float, bool)):
        raise BoundaryError(f"{context}: non-JSON public value")
    elif isinstance(value, float) and not (float("-inf") < value < float("inf")):
        raise BoundaryError(f"{context}: non-finite public value")


def validate_public_source(source: Any) -> dict[str, Any]:
    source = _exact(source, PUBLIC_SOURCE_KEYS, "public source")
    if source["schema"] != PUBLIC_SOURCE_SCHEMA:
        raise BoundaryError("public source: wrong schema")
    _token(source["public_source_id"], "public source.public_source_id")
    _hex64(source["link_id"], "public source.link_id")
    p = _integer(source["p"], "public source.p", 3)
    if source["bits"] != p.bit_length():
        raise BoundaryError("public source.bits: mismatch")
    curve = _exact(source["curve"], {"a", "b"}, "public source.curve")
    for name in ("a", "b"):
        value = _integer(curve[name], f"public source.curve.{name}", 0)
        if value >= p:
            raise BoundaryError(f"public source.curve.{name}: not reduced")
    cardinality = _integer(source["cardinality"], "public source.cardinality", 1)
    factors = source["cardinality_factors"]
    if not isinstance(factors, list) or not factors:
        raise BoundaryError("public source.cardinality_factors: invalid")
    product = 1
    factor_primes = []
    previous = 1
    for index, item in enumerate(factors):
        if not isinstance(item, list) or len(item) != 2:
            raise BoundaryError(f"public source.factor[{index}]: invalid")
        q = _integer(item[0], f"public source.factor[{index}].q", 2)
        e = _integer(item[1], f"public source.factor[{index}].e", 1)
        if q <= previous or not _is_prime(q):
            raise BoundaryError("public source.cardinality_factors: invalid prime ordering")
        factor_primes.append(q)
        previous = q
        product *= q**e
    if product != cardinality:
        raise BoundaryError("public source.cardinality_factors: product mismatch")
    subgroup = _integer(source["source_subgroup_order"], "public source.source_subgroup_order", 2)
    cofactor = _integer(source["source_cofactor"], "public source.source_cofactor", 1)
    if (
        subgroup * cofactor != cardinality
        or source["base_point_order"] != subgroup
        or subgroup not in factor_primes
        or not _is_prime(subgroup)
    ):
        raise BoundaryError("public source: subgroup/cofactor mismatch")
    base = tuple(_point(source["base_point"], "public source.base_point"))
    a, b = curve["a"], curve["b"]
    if not ec_field.on_curve(base, a, b, p) or ec_field.point_mul(subgroup, base, a, p) is not None:
        raise BoundaryError("public source.base_point: generator linkage failed")
    max_r = _integer(source["max_r"], "public source.max_r", 2)
    points = source["ordered_points"]
    if not isinstance(points, list) or len(points) != max_r:
        raise BoundaryError("public source.ordered_points: wrong length")
    checked_points = []
    for index, point in enumerate(points):
        parsed = tuple(_point(point, f"public source.ordered_points[{index}]"))
        if not ec_field.on_curve(parsed, a, b, p):
            raise BoundaryError(f"public source.ordered_points[{index}]: off curve")
        if ec_field.point_mul(subgroup, parsed, a, p) is not None:
            raise BoundaryError(f"public source.ordered_points[{index}]: outside subgroup")
        checked_points.append(parsed)
    signed = set(checked_points) | {ec_field.point_neg(point, p) for point in checked_points}
    if len(signed) != 2 * max_r:
        raise BoundaryError("public source.ordered_points: not distinct up to sign")
    _prefixes(source["prefixes"], max_r, "public source.prefixes")
    payload = {key: source[key] for key in PUBLIC_SOURCE_KEYS - {"link_id", "public_payload_sha256"}}
    if _sha(payload) != _hex64(source["public_payload_sha256"], "public source.public_payload_sha256"):
        raise BoundaryError("public source.public_payload_sha256: mismatch")
    assert_no_forbidden_public_material(source)
    return json.loads(_canonical_bytes(source))


def validate_link(link: Any) -> dict[str, Any]:
    link = _exact(link, LINK_KEYS, "private link")
    if link["schema"] != LINK_SCHEMA:
        raise BoundaryError("private link: wrong schema")
    nonce = link["link_nonce_hex"]
    if not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{64}", nonce) is None:
        raise BoundaryError("private link.link_nonce_hex: invalid")
    _validate_nonce(bytes.fromhex(nonce))
    for key in LINK_KEYS - {
        "schema",
        "link_nonce_hex",
        "nonce_provenance",
        "production_eligible",
    }:
        _hex64(link[key], f"private link.{key}")
    if link["nonce_provenance"] not in ("os.urandom", "deterministic_test_only"):
        raise BoundaryError("private link.nonce_provenance: invalid")
    if not isinstance(link["production_eligible"], bool):
        raise BoundaryError("private link.production_eligible: expected boolean")
    if link["production_eligible"] != (link["nonce_provenance"] == "os.urandom"):
        raise BoundaryError("private link: nonce provenance/eligibility mismatch")
    return json.loads(_canonical_bytes(link))


def verify_redaction_link(
    private_source: Mapping[str, Any], public_source: Mapping[str, Any], link: Mapping[str, Any]
) -> dict[str, Any]:
    private = validate_private_source(private_source)
    public = validate_public_source(public_source)
    link = validate_link(link)
    expected_public, expected_link = _redact_with_nonce(
        private,
        bytes.fromhex(link["link_nonce_hex"]),
        link["nonce_provenance"],
        link["production_eligible"],
    )
    if public != expected_public or link != expected_link:
        raise BoundaryError("public/private link does not replay exactly")
    return {
        "private_source_sha256": _sha(private),
        "public_source_sha256": _sha(public),
        "link_id": link["link_id"],
    }


def _reduce_rational_mod(value: Fraction, p: int, context: str) -> int:
    denominator = value.denominator % p
    if denominator == 0:
        raise BoundaryError(f"{context}: denominator is not invertible modulo p")
    return (value.numerator % p) * pow(denominator, -1, p) % p


def _validate_lift_semantics(
    *,
    public_source: Mapping[str, Any],
    r: int,
    selected_indices: Sequence[int],
    ainvs: Sequence[Any],
    selected_points: Sequence[Any],
) -> tuple[list[int], list[list[str]]]:
    source = validate_public_source(public_source)
    p = source["p"]
    if not isinstance(r, int) or isinstance(r, bool) or not 2 <= r <= 6:
        raise BoundaryError("public lift.r: expected 2..6")
    if (
        not isinstance(selected_indices, list)
        or len(selected_indices) != r
        or any(isinstance(i, bool) or not isinstance(i, int) for i in selected_indices)
        or len(set(selected_indices)) != r
        or any(i < 0 or i >= source["max_r"] for i in selected_indices)
    ):
        raise BoundaryError("public lift.selected_indices: invalid")
    expected_indices = source["prefixes"][str(r)]["indices"]
    if selected_indices != expected_indices:
        raise BoundaryError("public lift.selected_indices: does not match redacted source prefix")
    if not isinstance(ainvs, list) or len(ainvs) != 5:
        raise BoundaryError("public lift.ainvs: expected five integers")
    integral_ainvs = [_integer(v, f"public lift.ainvs[{i}]") for i, v in enumerate(ainvs)]
    expected_reduction = [0, 0, 0, source["curve"]["a"], source["curve"]["b"]]
    if [value % p for value in integral_ainvs] != expected_reduction:
        raise BoundaryError("public lift.ainvs: reduction does not match source curve")
    if not isinstance(selected_points, list) or len(selected_points) != r:
        raise BoundaryError("public lift.selected_points: wrong length")
    parsed_points: list[tuple[Fraction, Fraction]] = []
    rendered_points: list[list[str]] = []
    a1, a2, a3, a4, a6 = map(Fraction, integral_ainvs)
    for position, point in enumerate(selected_points):
        if not isinstance(point, list) or len(point) != 2:
            raise BoundaryError(f"public lift.selected_points[{position}]: invalid")
        x = _fraction(point[0], f"public lift.selected_points[{position}][0]")
        y = _fraction(point[1], f"public lift.selected_points[{position}][1]")
        if y * y + a1 * x * y + a3 * y != x**3 + a2 * x * x + a4 * x + a6:
            raise BoundaryError(f"public lift.selected_points[{position}]: off lifted curve")
        source_point = source["ordered_points"][selected_indices[position]]
        reduced = [
            _reduce_rational_mod(x, p, f"public lift point {position}.x"),
            _reduce_rational_mod(y, p, f"public lift point {position}.y"),
        ]
        if reduced != source_point:
            raise BoundaryError(f"public lift.selected_points[{position}]: reduction mismatch")
        parsed_points.append((x, y))
        rendered_points.append([_fraction_text(x), _fraction_text(y)])
    return integral_ainvs, rendered_points


def derive_public_lift(
    private_lift: Mapping[str, Any],
    *,
    private_source: Mapping[str, Any],
    public_source: Mapping[str, Any],
    link: Mapping[str, Any],
) -> dict[str, Any]:
    """Project a certified lift and replay its source reduction before exposure."""
    verify_redaction_link(private_source, public_source, link)
    if not isinstance(private_lift, Mapping):
        raise BoundaryError("private lift: expected an object")
    hashes = private_lift.get("hashes")
    certificate = private_lift.get("certificate")
    if not isinstance(hashes, Mapping) or not isinstance(certificate, Mapping):
        raise BoundaryError("private lift: missing hashes/certificate")
    if hashes.get("source_record_sha256") != _sha(validate_private_source(private_source)):
        raise BoundaryError("private lift: source record hash mismatch")
    if not certificate or any(value is not True for value in certificate.values()):
        raise BoundaryError("private lift: certificate is not all true")
    model_sha = _hex64(hashes.get("model_sha256"), "private lift.model_sha256")
    r = private_lift.get("r")
    indices = private_lift.get("selected_indices")
    ainvs, points = _validate_lift_semantics(
        public_source=public_source,
        r=r,
        selected_indices=indices,
        ainvs=private_lift.get("ainvs"),
        selected_points=private_lift.get("points"),
    )
    payload = {
        "schema": PUBLIC_LIFT_SCHEMA,
        "public_source_sha256": _sha(validate_public_source(public_source)),
        "private_lift_sha256": _sha(private_lift),
        "r": r,
        "selected_indices": list(indices),
        "ainvs": ainvs,
        "selected_points": points,
        "model_sha256": model_sha,
    }
    result = dict(payload)
    result["public_lift_sha256"] = _sha(payload)
    return result


def validate_public_lift(
    public_lift: Any, *, public_source: Mapping[str, Any]
) -> dict[str, Any]:
    public_lift = _exact(public_lift, PUBLIC_LIFT_KEYS, "public lift")
    if public_lift["schema"] != PUBLIC_LIFT_SCHEMA:
        raise BoundaryError("public lift: wrong schema")
    source = validate_public_source(public_source)
    if public_lift["public_source_sha256"] != _sha(source):
        raise BoundaryError("public lift: source hash mismatch")
    _hex64(public_lift["private_lift_sha256"], "public lift.private_lift_sha256")
    _hex64(public_lift["model_sha256"], "public lift.model_sha256")
    ainvs, points = _validate_lift_semantics(
        public_source=source,
        r=public_lift["r"],
        selected_indices=public_lift["selected_indices"],
        ainvs=public_lift["ainvs"],
        selected_points=public_lift["selected_points"],
    )
    payload = {key: public_lift[key] for key in PUBLIC_LIFT_KEYS - {"public_lift_sha256"}}
    if public_lift["public_lift_sha256"] != _sha(payload):
        raise BoundaryError("public lift: projection hash mismatch")
    if ainvs != public_lift["ainvs"] or points != public_lift["selected_points"]:
        raise BoundaryError("public lift: noncanonical coefficients/points")
    return json.loads(_canonical_bytes(public_lift))


def validate_public_candidate(
    candidate: Any,
    *,
    public_source: Mapping[str, Any],
    public_lift: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = _exact(candidate, PUBLIC_CANDIDATE_KEYS, "public candidate")
    if candidate["schema"] != PUBLIC_CANDIDATE_SCHEMA:
        raise BoundaryError("public candidate: wrong schema")
    source = validate_public_source(public_source)
    lift = validate_public_lift(public_lift, public_source=source)
    if candidate["public_source_sha256"] != _sha(source):
        raise BoundaryError("public candidate: source hash mismatch")
    if candidate["public_lift_sha256"] != lift["public_lift_sha256"]:
        raise BoundaryError("public candidate: lift hash mismatch")
    ainvs = candidate["ainvs"]
    if not isinstance(ainvs, list) or len(ainvs) != 5:
        raise BoundaryError("public candidate.ainvs: expected five integers")
    for index, value in enumerate(ainvs):
        _integer(value, f"public candidate.ainvs[{index}]")
    points = candidate["selected_points"]
    if not isinstance(points, list) or len(points) < 2:
        raise BoundaryError("public candidate.selected_points: expected at least two points")
    for i, point in enumerate(points):
        if not isinstance(point, list) or len(point) != 2:
            raise BoundaryError(f"public candidate.selected_points[{i}]: invalid")
        _fraction(point[0], f"public candidate.selected_points[{i}][0]")
        _fraction(point[1], f"public candidate.selected_points[{i}][1]")
    work = _exact(candidate["construction_work"], WORK_KEYS, "public candidate.construction_work")
    for key in WORK_KEYS:
        _integer(work[key], f"public candidate.construction_work.{key}", 0)
    if candidate["ainvs"] != lift["ainvs"] or candidate["selected_points"] != lift["selected_points"]:
        raise BoundaryError("public candidate: curve/points differ from bound public lift")
    assert_no_forbidden_public_material(candidate)
    return json.loads(_canonical_bytes(candidate))


def derive_m3_formula_input(
    candidate: Mapping[str, Any],
    *,
    public_source: Mapping[str, Any],
    public_lift: Mapping[str, Any],
) -> dict[str, Any]:
    """Strip IDs, coefficients, and work counters before selector execution."""
    candidate = validate_public_candidate(
        candidate, public_source=public_source, public_lift=public_lift
    )
    payload = {
        "schema": M3_FORMULA_INPUT_SCHEMA,
        "selected_points": candidate["selected_points"],
    }
    result = dict(payload)
    result["formula_input_sha256"] = _sha(payload)
    return result


def validate_m3_formula_input(value: Any) -> dict[str, Any]:
    value = _exact(value, M3_FORMULA_INPUT_KEYS, "M3 formula input")
    if value["schema"] != M3_FORMULA_INPUT_SCHEMA:
        raise BoundaryError("M3 formula input: wrong schema")
    points = value["selected_points"]
    if not isinstance(points, list) or len(points) < 2:
        raise BoundaryError("M3 formula input.selected_points: invalid")
    for index, point in enumerate(points):
        if not isinstance(point, list) or len(point) != 2:
            raise BoundaryError(f"M3 formula input.selected_points[{index}]: invalid")
        _fraction(point[0], f"M3 formula input.selected_points[{index}][0]")
        _fraction(point[1], f"M3 formula input.selected_points[{index}][1]")
    payload = {"schema": value["schema"], "selected_points": points}
    if value["formula_input_sha256"] != _sha(payload):
        raise BoundaryError("M3 formula input: hash mismatch")
    assert_no_forbidden_public_material(value)
    return json.loads(_canonical_bytes(value))


def bind_candidate_outside_selector(
    candidate: Mapping[str, Any],
    *,
    public_source: Mapping[str, Any],
    public_lift: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive accounting identity without exposing it to the M3 formula process."""
    candidate = validate_public_candidate(
        candidate, public_source=public_source, public_lift=public_lift
    )
    candidate_sha = _sha(candidate)
    semantic_payload = {
        "public_source_sha256": candidate["public_source_sha256"],
        "public_lift_sha256": candidate["public_lift_sha256"],
        "ainvs": candidate["ainvs"],
        "selected_points": candidate["selected_points"],
    }
    semantic_sha = _sha(semantic_payload)
    formula_input = derive_m3_formula_input(
        candidate, public_source=public_source, public_lift=public_lift
    )
    tie_break_key = [semantic_sha, candidate["public_lift_sha256"]]
    payload = {
        "schema": CANDIDATE_BINDING_SCHEMA,
        "candidate_id": "candidate-" + semantic_sha[:32],
        "candidate_sha256": candidate_sha,
        "construction_work_sha256": _sha(candidate["construction_work"]),
        "tie_break_rule": "lexicographic-semantic-hash-v1",
        "tie_break_key": tie_break_key,
        "formula_input_sha256": formula_input["formula_input_sha256"],
    }
    result = dict(payload)
    result["binding_sha256"] = _sha(payload)
    return result


def _m3_coordinate_formula(formula_input: Mapping[str, Any]) -> Fraction:
    """Frozen coefficient-independent nonlinear coordinate formula M3-C1."""
    total = Fraction(0)
    for index, (raw_x, raw_y) in enumerate(formula_input["selected_points"], 1):
        x = _fraction(raw_x, f"selected_points[{index - 1}][0]")
        y = _fraction(raw_y, f"selected_points[{index - 1}][1]")
        total += index * (x * x + x * y + y * y)
    return total


def _m3_ast_replay(formula_input: Mapping[str, Any], ast: Mapping[str, Any]) -> Fraction:
    """Independent replay of the single frozen AST, without `_fraction`."""
    if ast != M3_FORMULA_AST:
        raise BoundaryError("M3 formula AST is not the frozen expression")
    total = Fraction(0)
    for index, point in enumerate(formula_input["selected_points"], 1):
        if not isinstance(point, list) or len(point) != 2:
            raise BoundaryError("M3 AST replay: malformed point")
        values = []
        for raw in point:
            if isinstance(raw, bool) or not isinstance(raw, (int, str)):
                raise BoundaryError("M3 AST replay: malformed rational")
            parsed = Fraction(raw)
            text = (
                str(parsed.numerator)
                if parsed.denominator == 1
                else f"{parsed.numerator}/{parsed.denominator}"
            )
            if text != str(raw):
                raise BoundaryError("M3 AST replay: noncanonical rational")
            values.append(parsed)
        x, y = values
        total += index * (x * x + x * y + y * y)
    return total


def _independent_fraction_text(value: Fraction) -> str:
    numerator = int(value.numerator)
    denominator = int(value.denominator)
    if denominator <= 0 or math.gcd(abs(numerator), denominator) != 1:
        raise BoundaryError("independent fraction formatter received noncanonical value")
    return str(numerator) if denominator == 1 else str(numerator) + "/" + str(denominator)


def m3_implementation_sha256() -> str:
    source = "\n".join(
        inspect.getsource(function)
        for function in (
            _fraction,
            validate_m3_formula_input,
            _m3_coordinate_formula,
            _m3_ast_replay,
            _fraction_text,
            _independent_fraction_text,
        )
    )
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def freeze_m3_formula() -> dict[str, Any]:
    payload = {
        "schema": M3_FORMULA_SPEC_SCHEMA,
        "formula_id": "M3-C1-coordinate-quadratic-v1",
        "implementation_sha256": m3_implementation_sha256(),
        "candidate_schema": PUBLIC_CANDIDATE_SCHEMA,
        "formula_input_schema": M3_FORMULA_INPUT_SCHEMA,
        "formula_ast": M3_FORMULA_AST,
        "formula_ast_sha256": _sha(M3_FORMULA_AST),
    }
    result = dict(payload)
    result["spec_sha256"] = _sha(payload)
    return result


def validate_m3_formula_spec(spec: Any) -> dict[str, Any]:
    spec = _exact(spec, FORMULA_SPEC_KEYS, "M3 formula spec")
    if spec["schema"] != M3_FORMULA_SPEC_SCHEMA:
        raise BoundaryError("M3 formula spec: wrong schema")
    if spec["formula_id"] != "M3-C1-coordinate-quadratic-v1":
        raise BoundaryError("M3 formula spec: unknown formula")
    if spec["candidate_schema"] != PUBLIC_CANDIDATE_SCHEMA:
        raise BoundaryError("M3 formula spec: candidate schema mismatch")
    if spec["formula_input_schema"] != M3_FORMULA_INPUT_SCHEMA:
        raise BoundaryError("M3 formula spec: input schema mismatch")
    if spec["formula_ast"] != M3_FORMULA_AST or spec["formula_ast_sha256"] != _sha(M3_FORMULA_AST):
        raise BoundaryError("M3 formula spec: AST mismatch")
    if spec["implementation_sha256"] != m3_implementation_sha256():
        raise BoundaryError("M3 formula spec: implementation digest mismatch")
    payload = {key: spec[key] for key in FORMULA_SPEC_KEYS - {"spec_sha256"}}
    if spec["spec_sha256"] != _sha(payload):
        raise BoundaryError("M3 formula spec: spec digest mismatch")
    return json.loads(_canonical_bytes(spec))


def compute_m3_feature(formula_input: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    formula_input = validate_m3_formula_input(formula_input)
    spec = validate_m3_formula_spec(spec)
    direct = _m3_coordinate_formula(formula_input)
    replayed = _m3_ast_replay(formula_input, spec["formula_ast"])
    direct_text = _fraction_text(direct)
    replayed_text = _independent_fraction_text(replayed)
    if direct != replayed or direct_text != replayed_text:
        raise BoundaryError("M3 formula implementation disagrees with independent AST replay")
    payload = {
        "schema": M3_FEATURE_SCHEMA,
        "formula_spec_sha256": spec["spec_sha256"],
        "formula_id": spec["formula_id"],
        "formula_implementation_sha256": spec["implementation_sha256"],
        "formula_input_sha256": formula_input["formula_input_sha256"],
        "value": direct_text,
        "executable": "host-python-control-only",
        "executable_sha256": _file_sha(Path(sys.executable)),
        "script_sha256": hashlib.sha256(M3_CONTAINER_SCRIPT.encode()).hexdigest(),
    }
    result = dict(payload)
    result["feature_sha256"] = _sha(payload)
    return result


def validate_m3_feature(
    feature: Any,
    *,
    spec: Mapping[str, Any],
    formula_input: Mapping[str, Any],
    production: bool = True,
) -> dict[str, Any]:
    feature = _exact(feature, M3_FEATURE_KEYS, "M3 feature")
    spec = validate_m3_formula_spec(spec)
    formula_input = validate_m3_formula_input(formula_input)
    if feature["schema"] != M3_FEATURE_SCHEMA:
        raise BoundaryError("M3 feature: wrong schema")
    if feature["formula_spec_sha256"] != spec["spec_sha256"]:
        raise BoundaryError("M3 feature: formula spec hash mismatch")
    if feature["formula_id"] != spec["formula_id"]:
        raise BoundaryError("M3 feature: formula id mismatch")
    if feature["formula_implementation_sha256"] != spec["implementation_sha256"]:
        raise BoundaryError("M3 feature: implementation hash mismatch")
    if feature["formula_input_sha256"] != formula_input["formula_input_sha256"]:
        raise BoundaryError("M3 feature: input hash mismatch")
    _fraction(feature["value"], "M3 feature.value")
    if not isinstance(feature["executable"], str) or not feature["executable"]:
        raise BoundaryError("M3 feature.executable: invalid")
    if production and feature["executable"] == "host-python-control-only":
        raise BoundaryError("M3 feature: host control output is not production eligible")
    for key in ("executable_sha256", "script_sha256", "feature_sha256"):
        _hex64(feature[key], f"M3 feature.{key}")
    if feature["script_sha256"] != hashlib.sha256(M3_CONTAINER_SCRIPT.encode()).hexdigest():
        raise BoundaryError("M3 feature: launcher script hash mismatch")
    payload = {key: feature[key] for key in M3_FEATURE_KEYS - {"feature_sha256"}}
    if feature["feature_sha256"] != _sha(payload):
        raise BoundaryError("M3 feature: feature hash mismatch")
    expected_value = _m3_ast_replay(formula_input, spec["formula_ast"])
    if feature["value"] != _independent_fraction_text(expected_value):
        raise BoundaryError("M3 feature: value does not replay from frozen AST")
    return json.loads(_canonical_bytes(feature))


def freeze_direct_search_adapter(image: str) -> dict[str, Any]:
    if not isinstance(image, str) or PINNED_IMAGE.fullmatch(image.lower()) is None:
        raise BoundaryError("direct search adapter image must be digest pinned")
    payload = {
        "schema": DIRECT_SEARCH_ADAPTER_SPEC_SCHEMA,
        "algorithm": "bsgs-v1",
        "input_schema": PUBLIC_SOURCE_SCHEMA,
        "output_schema": DIRECT_SEARCH_COST_SCHEMA,
        "image": image,
        "script_sha256": hashlib.sha256(DIRECT_SEARCH_ADAPTER_SCRIPT.encode()).hexdigest(),
    }
    result = dict(payload)
    result["spec_sha256"] = _sha(payload)
    return result


def validate_direct_search_adapter_spec(spec: Any) -> dict[str, Any]:
    spec = _exact(spec, DIRECT_ADAPTER_SPEC_KEYS, "direct search adapter spec")
    if spec["schema"] != DIRECT_SEARCH_ADAPTER_SPEC_SCHEMA:
        raise BoundaryError("direct search adapter spec: wrong schema")
    expected = freeze_direct_search_adapter(spec["image"])
    if spec != expected:
        raise BoundaryError("direct search adapter spec: does not replay frozen adapter")
    return expected


def validate_direct_search_cost(
    cost: Any,
    *,
    expected_public_source: Mapping[str, Any],
    expected_adapter_spec: Mapping[str, Any],
) -> dict[str, Any]:
    cost = _exact(cost, DIRECT_SEARCH_COST_KEYS, "direct source search cost")
    if cost["schema"] != DIRECT_SEARCH_COST_SCHEMA:
        raise BoundaryError("direct source search cost: wrong schema")
    if cost["algorithm"] not in ("bsgs-v1", "exhaustive-source-relation-v1"):
        raise BoundaryError("direct source search cost.algorithm: invalid")
    adapter_spec = validate_direct_search_adapter_spec(expected_adapter_spec)
    if cost["algorithm"] != adapter_spec["algorithm"]:
        raise BoundaryError("direct source search cost: adapter algorithm mismatch")
    if cost["adapter_spec_sha256"] != adapter_spec["spec_sha256"]:
        raise BoundaryError("direct source search cost: adapter spec binding mismatch")
    if cost["script_sha256"] != adapter_spec["script_sha256"]:
        raise BoundaryError("direct source search cost: adapter script binding mismatch")
    public_source = validate_public_source(expected_public_source)
    expected_public_source_sha256 = _sha(public_source)
    if cost["public_source_sha256"] != expected_public_source_sha256:
        raise BoundaryError("direct source search cost: public source binding mismatch")
    tool = _exact(cost["tool_identity"], DIRECT_TOOL_KEYS, "direct source search tool")
    _token(tool["name"], "direct source search tool.name")
    if not isinstance(tool["version"], str) or not tool["version"]:
        raise BoundaryError("direct source search tool.version: invalid")
    _hex64(tool["executable_sha256"], "direct source search tool.executable_sha256")
    counters = _exact(cost["counters"], DIRECT_COUNTER_KEYS, "direct source search counters")
    for key in DIRECT_COUNTER_KEYS:
        _integer(counters[key], f"direct source search counters.{key}", 0)
    transcript = _exact(
        cost["transcript"], DIRECT_TRANSCRIPT_KEYS, "direct source search transcript"
    )
    if transcript["schema"] != "xedni-direct-source-search-transcript/v1":
        raise BoundaryError("direct source search transcript: wrong schema")
    if transcript["input_sha256"] != expected_public_source_sha256:
        raise BoundaryError("direct source search transcript: input binding mismatch")
    if transcript["status"] not in ("relation", "no_relation", "failed"):
        raise BoundaryError("direct source search transcript.status: invalid")
    for key in ("candidates_tested", "group_operations"):
        _integer(transcript[key], f"direct source search transcript.{key}", 0)
        if transcript[key] != counters[key]:
            raise BoundaryError(f"direct source search transcript.{key}: counter mismatch")
    coefficients = transcript["result_coefficients"]
    if not isinstance(cost["complete"], bool):
        raise BoundaryError("direct source search cost.complete: expected boolean")
    if coefficients is not None and (
        not isinstance(coefficients, list)
        or not coefficients
        or any(isinstance(v, bool) or not isinstance(v, int) for v in coefficients)
    ):
        raise BoundaryError("direct source search transcript.result_coefficients: invalid")
    if transcript["status"] == "relation" and coefficients is None:
        raise BoundaryError("direct source search transcript: relation requires coefficients")
    if transcript["status"] != "relation" and coefficients is not None:
        raise BoundaryError("direct source search transcript: coefficients require relation status")
    if cost["algorithm"] == "bsgs-v1" and cost["complete"] and transcript["status"] != "relation":
        raise BoundaryError("direct source search transcript: complete BSGS must recover relations")
    if coefficients is not None:
        if len(coefficients) != len(public_source["ordered_points"]):
            raise BoundaryError("direct source search transcript: coefficient count mismatch")
        p = public_source["p"]
        a = public_source["curve"]["a"]
        q = public_source["source_subgroup_order"]
        base = tuple(public_source["base_point"])
        for index, (coefficient, raw_point) in enumerate(
            zip(coefficients, public_source["ordered_points"])
        ):
            if not 0 <= coefficient < q:
                raise BoundaryError(
                    f"direct source search transcript.coefficients[{index}]: out of range"
                )
            if ec_field.point_mul(coefficient, base, a, p) != tuple(raw_point):
                raise BoundaryError(
                    f"direct source search transcript.coefficients[{index}]: DLP replay failed"
                )
    transcript_sha = _sha(transcript)
    if cost["transcript_sha256"] != transcript_sha:
        raise BoundaryError("direct source search cost: transcript hash mismatch")
    if cost["complete"]:
        if transcript["status"] == "failed":
            raise BoundaryError("direct source search cost: failed transcript cannot be complete")
        if any(counters[key] <= 0 for key in DIRECT_COUNTER_KEYS):
            raise BoundaryError("direct source search cost: complete work counters must be positive")
    payload = {key: cost[key] for key in DIRECT_SEARCH_COST_KEYS - {"cost_sha256"}}
    if cost["cost_sha256"] != _sha(payload):
        raise BoundaryError("direct source search cost: record hash mismatch")
    return json.loads(_canonical_bytes(cost))


def _strict_json_loads(text: str) -> Any:
    def reject_constant(value: str) -> None:
        raise BoundaryError(f"non-finite JSON constant {value!r}")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise BoundaryError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    try:
        return json.loads(
            text,
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicates,
        )
    except json.JSONDecodeError as error:
        raise BoundaryError("public tool stdout is not one strict JSON value") from error


@dataclass
class StageLedger:
    """Hash-chained stage order; rank/replay cannot precede public selection."""

    row_id: str
    events: list[dict[str, str]] = dataclass_field(default_factory=list)

    def __post_init__(self) -> None:
        _token(self.row_id, "stage ledger.row_id")

    def _append_hash(self, stage: str, artifact_sha256: str) -> dict[str, Any]:
        expected = STAGES[len(self.events)] if len(self.events) < len(STAGES) else None
        if stage != expected:
            raise BoundaryError(f"stage order: expected {expected!r}, received {stage!r}")
        _hex64(artifact_sha256, "stage artifact_sha256")
        previous = self.events[-1]["event_sha256"] if self.events else "0" * 64
        payload = {
            "index": str(len(self.events)),
            "stage": stage,
            "artifact_sha256": artifact_sha256,
            "previous_event_sha256": previous,
        }
        event = dict(payload)
        event["event_sha256"] = _sha(payload)
        self.events.append(event)
        return event

    def advance(self, stage: str, artifact: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(artifact, Mapping):
            raise BoundaryError("stage artifact must be the actual JSON object, not a supplied hash")
        canonical = json.loads(_canonical_bytes(artifact))
        return self._append_hash(stage, _sha(canonical))

    def snapshot(self) -> dict[str, Any]:
        payload = {
            "schema": STAGE_LEDGER_SCHEMA,
            "row_id": self.row_id,
            "events": json.loads(_canonical_bytes(self.events)),
        }
        result = dict(payload)
        result["chain_sha256"] = _sha(payload)
        return result


def validate_stage_ledger(value: Any) -> dict[str, Any]:
    value = _exact(value, STAGE_KEYS, "stage ledger")
    if value["schema"] != STAGE_LEDGER_SCHEMA:
        raise BoundaryError("stage ledger: wrong schema")
    ledger = StageLedger(_token(value["row_id"], "stage ledger.row_id"))
    if not isinstance(value["events"], list):
        raise BoundaryError("stage ledger.events: expected a list")
    for event in value["events"]:
        event = _exact(
            event,
            {"index", "stage", "artifact_sha256", "previous_event_sha256", "event_sha256"},
            "stage ledger.event",
        )
        replayed = ledger._append_hash(event["stage"], event["artifact_sha256"])
        if replayed != event:
            raise BoundaryError("stage ledger: event chain mismatch")
    expected = ledger.snapshot()
    if expected != value:
        raise BoundaryError("stage ledger: snapshot hash mismatch")
    return expected


def _validate_public_dispatch(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise BoundaryError("public subprocess input must be an object")
    schema = value.get("schema")
    if schema == PUBLIC_SOURCE_SCHEMA:
        return validate_public_source(value)
    if schema == M3_FORMULA_INPUT_SCHEMA:
        return validate_m3_formula_input(value)
    raise BoundaryError(f"public subprocess input has unsupported schema {schema!r}")


def _safe_tool_command(command: Sequence[str]) -> list[str]:
    if not isinstance(command, (list, tuple)) or not command:
        raise BoundaryError("public tool command must be a nonempty token list")
    result = []
    for index, token in enumerate(command):
        if not isinstance(token, str) or not token or "\x00" in token:
            raise BoundaryError(f"public tool command[{index}]: invalid token")
        if "\n" in token and token not in (M3_CONTAINER_SCRIPT, DIRECT_SEARCH_ADAPTER_SCRIPT):
            raise BoundaryError(f"public tool command[{index}]: unbound multiline script")
        if ".." in Path(token).parts or token.startswith("/workspace") or token.startswith("/home"):
            raise BoundaryError(f"public tool command[{index}]: host path is forbidden")
        result.append(token)
    return result


def _bounded_process(
    command: Sequence[str],
    *,
    timeout_seconds: int,
    stdout_limit_bytes: int,
    stderr_limit_bytes: int,
    environment: Mapping[str, str],
) -> tuple[int | None, bytes, bytes, bool, str | None]:
    """Capture a subprocess without permitting unbounded pipe output."""
    process = subprocess.Popen(
        list(command),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        env=dict(environment),
    )
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, ("stdout", stdout_limit_bytes))
    selector.register(process.stderr, selectors.EVENT_READ, ("stderr", stderr_limit_bytes))
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    overflow = None
    while selector.get_map():
        remaining = deadline - time.monotonic()
        if remaining <= 0 and process.poll() is None:
            timed_out = True
            process.kill()
        events = selector.select(max(0.0, min(remaining, 0.1)))
        for key, _ in events:
            name, limit = key.data
            chunk = os.read(key.fileobj.fileno(), 65536)
            if not chunk:
                selector.unregister(key.fileobj)
                continue
            available = max(0, limit - len(buffers[name]))
            buffers[name].extend(chunk[:available])
            if len(chunk) > available and overflow is None:
                overflow = name
                process.kill()
        if process.poll() is not None and not events:
            # A final select/read iteration drains EOF from both pipes.
            continue
    returncode = process.wait()
    selector.close()
    process.stdout.close()
    process.stderr.close()
    return returncode, bytes(buffers["stdout"]), bytes(buffers["stderr"]), timed_out, overflow


def _validate_isolation_canary(value: Any) -> dict[str, Any]:
    value = _exact(value, {"schema", "a", "b", "c", "d"}, "isolation canary")
    if value["schema"] != ISOLATION_CANARY_SCHEMA:
        raise BoundaryError("isolation canary: wrong schema")
    if value["a"] is not None:
        raise BoundaryError("isolation canary: host environment leaked")
    for key in ("b", "c", "d"):
        if value[key] is not False:
            raise BoundaryError(f"isolation canary.{key}: isolation failed")
    return dict(value)


def _validate_image_inspect(value: Any, expected_image_id: str) -> tuple[str, None]:
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        raise BoundaryError("container image inspect: expected one image object")
    record = value[0]
    observed = record.get("Id")
    if not isinstance(observed, str) or observed.lower() != expected_image_id.lower():
        raise BoundaryError("public container image identity does not match its pin")
    config = record.get("Config")
    if not isinstance(config, dict):
        raise BoundaryError("container image inspect: missing Config")
    volumes = config.get("Volumes")
    if volumes not in (None, {}):
        raise BoundaryError("container image declares implicit Config.Volumes")
    return observed, None


def run_public_container(
    public_input: Mapping[str, Any],
    *,
    image: str,
    tool_command: Sequence[str],
    expected_output_schema: str,
    formula_spec: Mapping[str, Any] | None = None,
    direct_adapter_spec: Mapping[str, Any] | None = None,
    runtime: str = "docker",
    timeout_seconds: int = 60,
    stdout_limit_bytes: int = 1 << 20,
    stderr_limit_bytes: int = 1 << 20,
) -> dict[str, Any]:
    """Run a public-only tool with one read-only input mount and no network."""
    public_input = _validate_public_dispatch(public_input)
    if not isinstance(image, str) or PINNED_IMAGE.fullmatch(image.lower()) is None:
        raise BoundaryError("public container image must be pinned by SHA-256")
    command_inside = _safe_tool_command(tool_command)
    if command_inside.count("<PUBLIC_INPUT>") != 1:
        raise BoundaryError("public tool command must contain one <PUBLIC_INPUT> placeholder")
    if timeout_seconds <= 0:
        raise BoundaryError("timeout_seconds must be positive")
    for name, limit in (
        ("stdout_limit_bytes", stdout_limit_bytes),
        ("stderr_limit_bytes", stderr_limit_bytes),
    ):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1 << 20:
            raise BoundaryError(f"{name} must be in 1..1048576")
    resolved = shutil.which(runtime)
    if resolved is None:
        raise BoundaryError(f"container runtime not found: {runtime}")
    inspect_run = subprocess.run(
        [resolved, "image", "inspect", image],
        capture_output=True,
        text=True,
        check=False,
        timeout=min(timeout_seconds, 30),
        close_fds=True,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C", "LC_ALL": "C"},
    )
    expected_id = image.lower().split("@")[-1]
    if inspect_run.returncode != 0:
        raise BoundaryError("public container image inspect failed")
    inspected = _strict_json_loads(inspect_run.stdout)
    observed_image_id, image_config_volumes = _validate_image_inspect(inspected, expected_id)

    with tempfile.TemporaryDirectory(prefix="xedni-public-") as directory:
        input_path = Path(directory) / "public.json"
        input_path.write_bytes(_canonical_bytes(public_input) + b"\n")
        # The pinned image may run as a non-host UID; the bind mount itself is
        # read-only, so world-readable input does not grant mutation.
        input_path.chmod(0o444)
        Path(directory).chmod(0o555)
        docker_command = [
            resolved,
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--user=65534:65534",
            "--pids-limit=64",
            "--memory=512m",
            "--mount",
            f"type=bind,src={directory},dst=/input,readonly",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",
            "--workdir",
            "/tmp",
            "--entrypoint",
            "env",
            image,
            "-i",
            "LANG=C",
            "LC_ALL=C",
            "PYTHONHASHSEED=0",
            *("/input/public.json" if token == "<PUBLIC_INPUT>" else token for token in command_inside),
        ]
        if sum(token == "--mount" for token in docker_command) != 1:
            raise BoundaryError("sandbox audit: expected exactly one read-only host mount")
        if any(token in ("-v", "--volume") for token in docker_command):
            raise BoundaryError("sandbox audit: extra volumes are forbidden")
        started = time.perf_counter_ns()
        returncode, stdout_raw, stderr_raw, timed_out, overflow = _bounded_process(
            docker_command,
            timeout_seconds=timeout_seconds,
            stdout_limit_bytes=stdout_limit_bytes,
            stderr_limit_bytes=stderr_limit_bytes,
            environment={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C", "LC_ALL": "C"},
        )
        stdout = stdout_raw.decode("utf-8", errors="replace")
        stderr = stderr_raw.decode("utf-8", errors="replace")
        wall_ns = time.perf_counter_ns() - started

    output = None
    output_sha = None
    if not timed_out and overflow is None and returncode == 0:
        output = _strict_json_loads(stdout)
        if expected_output_schema == M3_FEATURE_SCHEMA:
            if formula_spec is None or public_input.get("schema") != M3_FORMULA_INPUT_SCHEMA:
                raise BoundaryError("M3 output requires bound formula spec/input")
            output = validate_m3_feature(output, spec=formula_spec, formula_input=public_input)
        elif expected_output_schema == ISOLATION_CANARY_SCHEMA:
            output = _validate_isolation_canary(output)
        elif expected_output_schema == DIRECT_SEARCH_COST_SCHEMA:
            if direct_adapter_spec is None or public_input.get("schema") != PUBLIC_SOURCE_SCHEMA:
                raise BoundaryError("direct search output requires bound adapter/source")
            output = validate_direct_search_cost(
                output,
                expected_public_source=public_input,
                expected_adapter_spec=direct_adapter_spec,
            )
        else:
            raise BoundaryError(f"unsupported exact output schema {expected_output_schema!r}")
        output_sha = _sha(output)
    status = (
        "timeout"
        if timed_out
        else "output_limit"
        if overflow is not None
        else "complete"
        if returncode == 0
        else "nonzero_exit"
    )
    evidence_payload = {
        "schema": PUBLIC_RUN_SCHEMA,
        "status": status,
        "runtime": resolved,
        "runtime_sha256": _file_sha(Path(resolved)),
        "image": image,
        "observed_image_id": observed_image_id,
        "image_config_volumes": image_config_volumes,
        "input_sha256": _sha(public_input),
        "tool_command": command_inside,
        "tool_command_sha256": _sha(command_inside),
        "executed_command": docker_command,
        "executed_command_sha256": _sha(docker_command),
        "expected_output_schema": expected_output_schema,
        "sandbox": {
            "network": "none",
            "rootfs": "read_only",
            "capabilities": "drop_all",
            "no_new_privileges": True,
            "user": "65534:65534",
            "host_mounts": ["public_input_read_only"],
            "extra_volumes": [],
            "environment": ["LANG=C", "LC_ALL=C", "PYTHONHASHSEED=0"],
            "close_fds": True,
        },
        "returncode": returncode,
        "timed_out": timed_out,
        "output_overflow_stream": overflow,
        "timeout_seconds": timeout_seconds,
        "stdout_limit_bytes": stdout_limit_bytes,
        "stderr_limit_bytes": stderr_limit_bytes,
        "wall_ns": wall_ns,
        "stdout": stdout,
        "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "stderr": stderr,
        "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "output": output,
        "output_sha256": output_sha,
    }
    evidence = dict(evidence_payload)
    evidence["evidence_sha256"] = _sha(evidence_payload)
    return evidence


def run_direct_source_search_adapter(
    public_source: Mapping[str, Any],
    *,
    image: str,
    runtime: str = "docker",
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    source = validate_public_source(public_source)
    spec = freeze_direct_search_adapter(image)
    script_sha = spec["script_sha256"]
    execution = run_public_container(
        source,
        image=image,
        tool_command=[
            "python3",
            "-c",
            DIRECT_SEARCH_ADAPTER_SCRIPT,
            "<PUBLIC_INPUT>",
            spec["spec_sha256"],
            script_sha,
        ],
        expected_output_schema=DIRECT_SEARCH_COST_SCHEMA,
        direct_adapter_spec=spec,
        runtime=runtime,
        timeout_seconds=timeout_seconds,
    )
    if execution["status"] != "complete" or execution["output"] is None:
        raise BoundaryError("direct source search adapter did not complete successfully")
    payload = {
        "schema": DIRECT_SEARCH_BUNDLE_SCHEMA,
        "adapter_spec": spec,
        "execution": execution,
        "cost": execution["output"],
    }
    result = dict(payload)
    result["bundle_sha256"] = _sha(payload)
    return result


def validate_direct_search_bundle(
    bundle: Any, *, expected_public_source: Mapping[str, Any]
) -> dict[str, Any]:
    bundle = _exact(bundle, DIRECT_BUNDLE_KEYS, "direct source search bundle")
    if bundle["schema"] != DIRECT_SEARCH_BUNDLE_SCHEMA:
        raise BoundaryError("direct source search bundle: wrong schema")
    spec = validate_direct_search_adapter_spec(bundle["adapter_spec"])
    public_source = validate_public_source(expected_public_source)
    expected_public_source_sha256 = _sha(public_source)
    execution = bundle["execution"]
    if not isinstance(execution, Mapping) or execution.get("schema") != PUBLIC_RUN_SCHEMA:
        raise BoundaryError("direct source search bundle: invalid execution evidence")
    evidence_payload = {key: execution[key] for key in execution if key != "evidence_sha256"}
    if execution.get("evidence_sha256") != _sha(evidence_payload):
        raise BoundaryError("direct source search bundle: execution hash mismatch")
    if (
        execution.get("status") != "complete"
        or execution.get("input_sha256") != expected_public_source_sha256
        or execution.get("image") != spec["image"]
        or execution.get("expected_output_schema") != DIRECT_SEARCH_COST_SCHEMA
        or execution.get("output") != bundle["cost"]
    ):
        raise BoundaryError("direct source search bundle: execution/source/output mismatch")
    stdout = execution.get("stdout")
    stderr = execution.get("stderr")
    if not isinstance(stdout, str) or not isinstance(stderr, str):
        raise BoundaryError("direct source search bundle: retained streams are missing")
    if execution.get("stdout_sha256") != hashlib.sha256(stdout.encode()).hexdigest():
        raise BoundaryError("direct source search bundle: stdout hash mismatch")
    if execution.get("stderr_sha256") != hashlib.sha256(stderr.encode()).hexdigest():
        raise BoundaryError("direct source search bundle: stderr hash mismatch")
    parsed_stdout = _strict_json_loads(stdout)
    if parsed_stdout != execution.get("output") or parsed_stdout != bundle["cost"]:
        raise BoundaryError("direct source search bundle: stdout/output/cost mismatch")
    if execution.get("output_sha256") != _sha(parsed_stdout):
        raise BoundaryError("direct source search bundle: output hash mismatch")
    executed_command = execution.get("executed_command")
    if (
        not isinstance(executed_command, list)
        or execution.get("executed_command_sha256") != _sha(executed_command)
    ):
        raise BoundaryError("direct source search bundle: executed command hash mismatch")
    expected_command = [
        "python3",
        "-c",
        DIRECT_SEARCH_ADAPTER_SCRIPT,
        "<PUBLIC_INPUT>",
        spec["spec_sha256"],
        spec["script_sha256"],
    ]
    if execution.get("tool_command") != expected_command:
        raise BoundaryError("direct source search bundle: adapter command mismatch")
    actual_inside = [
        "/input/public.json" if token == "<PUBLIC_INPUT>" else token
        for token in expected_command
    ]
    if executed_command[-len(actual_inside) :] != actual_inside:
        raise BoundaryError("direct source search bundle: recorded command was not executed")
    cost = validate_direct_search_cost(
        bundle["cost"],
        expected_public_source=public_source,
        expected_adapter_spec=spec,
    )
    if not cost["complete"] or cost["transcript"]["status"] not in ("relation", "no_relation"):
        raise BoundaryError("direct source search bundle: baseline is not complete/successful")
    payload = {key: bundle[key] for key in DIRECT_BUNDLE_KEYS - {"bundle_sha256"}}
    if bundle["bundle_sha256"] != _sha(payload):
        raise BoundaryError("direct source search bundle: bundle hash mismatch")
    return json.loads(_canonical_bytes(bundle))


def run_m3_formula_container(
    formula_input: Mapping[str, Any],
    *,
    formula_spec: Mapping[str, Any],
    direct_source_search_cost: Mapping[str, Any],
    public_source: Mapping[str, Any],
    image: str,
    runtime: str = "docker",
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """Launch only the frozen M3 script and bind its direct-search baseline."""
    formula_input = validate_m3_formula_input(formula_input)
    formula_spec = validate_m3_formula_spec(formula_spec)
    checked_source = validate_public_source(public_source)
    direct_bundle = validate_direct_search_bundle(
        direct_source_search_cost,
        expected_public_source=checked_source,
    )
    direct_cost = direct_bundle["cost"]
    script_sha = hashlib.sha256(M3_CONTAINER_SCRIPT.encode()).hexdigest()
    evidence = run_public_container(
        formula_input,
        image=image,
        tool_command=[
            "python3",
            "-c",
            M3_CONTAINER_SCRIPT,
            "<PUBLIC_INPUT>",
            formula_spec["spec_sha256"],
            formula_spec["implementation_sha256"],
            script_sha,
        ],
        expected_output_schema=M3_FEATURE_SCHEMA,
        formula_spec=formula_spec,
        runtime=runtime,
        timeout_seconds=timeout_seconds,
    )
    payload = dict(evidence)
    payload["m3_binding"] = {
        "executable": "python3",
        "script_sha256": script_sha,
        "formula_spec_sha256": formula_spec["spec_sha256"],
        "formula_ast_sha256": formula_spec["formula_ast_sha256"],
        "direct_source_search_cost": direct_cost,
        "direct_source_search_cost_sha256": direct_cost["cost_sha256"],
        "direct_source_search_bundle_sha256": direct_bundle["bundle_sha256"],
    }
    payload["evidence_sha256"] = _sha(
        {key: payload[key] for key in payload if key != "evidence_sha256"}
    )
    return payload


def verify_private_replay_link(
    private_source: Mapping[str, Any],
    public_source: Mapping[str, Any],
    link: Mapping[str, Any],
    stage_ledger: Mapping[str, Any],
    *,
    selection_artifact: Mapping[str, Any],
    proposal_artifact: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify linkage and that private replay follows public proposal/selection."""
    linkage = verify_redaction_link(private_source, public_source, link)
    checked_link = validate_link(link)
    if checked_link["production_eligible"] is not True:
        raise BoundaryError("private replay requires an OS-entropy production link")
    ledger = validate_stage_ledger(stage_ledger)
    if len(ledger["events"]) != 4 or ledger["events"][-1]["stage"] != "public_relation_proposed":
        raise BoundaryError("private replay requires a completed public proposal stage")
    if not isinstance(selection_artifact, Mapping) or not isinstance(proposal_artifact, Mapping):
        raise BoundaryError("private replay requires actual selection/proposal objects")
    actual_hashes = (
        linkage["private_source_sha256"],
        linkage["public_source_sha256"],
        _sha(selection_artifact),
        _sha(proposal_artifact),
    )
    observed_hashes = tuple(event["artifact_sha256"] for event in ledger["events"])
    if observed_hashes != actual_hashes:
        raise BoundaryError("private replay stage artifacts do not match the supplied objects")
    proposal_sha256 = actual_hashes[-1]
    payload = {
        "schema": PRIVATE_REPLAY_LINK_SCHEMA,
        "row_id": ledger["row_id"],
        "link_id": linkage["link_id"],
        "private_source_sha256": linkage["private_source_sha256"],
        "public_source_sha256": linkage["public_source_sha256"],
        "proposal_sha256": proposal_sha256,
        "stage_chain_sha256": ledger["chain_sha256"],
    }
    result = dict(payload)
    result["replay_link_sha256"] = _sha(payload)
    return result

