#!/usr/bin/env python3
"""CT192 guarded source derivative and frozen public 48-vector admission.

Producer/source-only: no Rust execution, independent replay or PCC.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent.parent
ORIGINAL = STUDY / "fixed-jacobian-chain-evaluator-02/derived/lib.rs"
FROZEN = STUDY / "evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json"
GENERATED = HERE / "derived/lib.rs"
ORIGINAL_BLOB = "b80eb91a39ae1e87f0fcde95e52ea3d3634558bc"
FROZEN_BLOB = "9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3"
SCALARS = (0, 1, 2, 17, 12345, 2771710)
ROUTES = ("direct_composite", "literal_sequential_Jacobian_maps", "strongest_retained_lift_chain")
COUNTERS = frozenset((
    "external_packet_parse", "external_norm_and_geometry", "external_full_order",
    "infinity_halves", "two_torsion_halves", "generic_halving_factorization",
    "generic_ordinate", "explicit_half_check", "quadratic_source_phi",
    "correction_difference", "correction_dictionary_lookup",
    "matching_corrections_checked", "source_lift_addition",
    "degree13_elliptic_evaluation", "degree169_elliptic_evaluation",
    "transported_norm_doubling", "quadratic_target_phi",
    "target_correction_addition", "final_actual_norm", "final_full_order",
    "inverse_full_group_scalar",
))
ROW_FIELDS = frozenset(("from", "to", "sector", "scalar_OUTSIDE_runtime",
                        "input", "whole_outputs_equal", *ROUTES))
NORM_ANCHOR = """    fn norm_point(&self, to: usize, point: Pt<ER>) -> Pt<ER> {
        self.bump(|c| c.transported_norm_doubling += 1);
        let target = &self.geometry.models[to].quadratic;
        descend_point(curve::pmul(&target.f, &target.curve, &point, 2))
    }
"""
PROBE = """
    /// CT192 diagnostic-only: actual pre-norm operand reconstructed from a
    /// fully admitted PUBLIC packet. No external scalar is provided or used.
    pub fn ct192_pre_norm_operand(
        &self, from: usize, to: usize, public: &EncodedClass, arm: &str
    ) -> Result<Pt<ER>> {
        if !matches!((from, to), (0, 2) | (2, 0)) {
            return Err("CT192 invalid direction".into());
        }
        if !matches!(arm, "direct_composite" | "strongest_retained_lift_chain") {
            return Err("CT192 invalid route".into());
        }
        let input = self.admit(from, public)?;
        let half = self.halves(from, input.norm)?[0];
        let (lifted, _) = self.corrected_lift(&input, to, half)?;
        let operand = if arm == "direct_composite" {
            self.gamma(from, to, lifted)?
        } else {
            self.gamma(1, to, self.gamma(from, 1, lifted)?)?
        };
        let result = if arm == "direct_composite" {
            self.transfer_entry(&input, to)?
        } else {
            self.retained_lift_entry(&input, to)?
        };
        if result.norm != self.norm_point(to, operand) {
            return Err("CT192 pre-norm point differs from native route norm".into());
        }
        // CT193: doubling has an E[2] kernel, so matching the norm alone
        // does not bind the candidate to the native target Jacobian class.
        if self.target_phi(to, operand)? != result.class {
            return Err("CT193 pre-norm point differs from native target class".into());
        }
        self.check_final(&result)?;
        Ok(operand)
    }

    /// CT192 calls CT125's actual norm function, including its counter bump.
    pub fn ct192_actual_norm(&self, to: usize, point: Pt<ER>) -> Pt<ER> {
        self.norm_point(to, point)
    }
"""

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()

def replace_once(s: str, a: str, b: str) -> str:
    if s.count(a) != 1:
        raise ValueError("CT192 source anchor not unique: " + a[:70])
    return s.replace(a, b)

def derivative(original: bytes) -> bytes:
    if blob(original) != ORIGINAL_BLOB:
        raise ValueError("CT125 Rust source blob mismatch")
    s = original.decode("utf-8")
    # Keep original modules and generated source bytes at their pinned paths.
    for old, new in (
        ('#[path = "../generated/literal_halves.rs"]',
         '#[path = "../../../fixed-jacobian-chain-evaluator-02/generated/literal_halves.rs"]'),
        ('mod rational;',
         '#[path = "../../../fixed-jacobian-chain-evaluator-02/derived/rational.rs"]\nmod rational;'),
        ('include!("../generated/halving.rs");',
         'include!("../../../fixed-jacobian-chain-evaluator-02/generated/halving.rs");'),
        ('include!("../generated/parse_packet.rs");',
         'include!("../../../fixed-jacobian-chain-evaluator-02/generated/parse_packet.rs");'),
        (NORM_ANCHOR, NORM_ANCHOR + PROBE),
        ('#[cfg(test)]\nmod tests;',
         '#[cfg(test)]\n#[path = "../../../fixed-jacobian-chain-evaluator-02/derived/tests.rs"]\nmod tests;'),
    ):
        s = replace_once(s, old, new)
    return s.encode("utf-8")

def validate_class_binding(derived: bytes) -> None:
    """Fail closed if the public pre-norm probe matches only the doubled norm."""
    s = derived.decode("utf-8")
    start = s.find("    pub fn ct192_pre_norm_operand(")
    end = s.find("    pub fn ct192_actual_norm(", start)
    if start < 0 or end < 0:
        raise ValueError("CT193 diagnostic method boundaries missing")
    probe = s[start:end]
    required = (
        "if result.norm != self.norm_point(to, operand) {",
        "if self.target_phi(to, operand)? != result.class {",
        "self.check_final(&result)?;",
    )
    positions = [probe.find(fragment) for fragment in required]
    if any(probe.count(fragment) != 1 for fragment in required) or positions != sorted(positions):
        raise ValueError("CT193 full-class pre-norm validation missing or reordered")

def exact_key(v):
    if type(v) is not list or len(v) != 19 or any(type(x) is not int or x < 0 or x >= (1 << 32) for x in v):
        raise ValueError("canonical key must be exactly 19 u32 words")
    return tuple(v)

def validate_fixture(data: bytes) -> dict:
    if blob(data) != FROZEN_BLOB:
        raise ValueError("frozen 48-vector Git blob changed")
    f = json.loads(data)
    if type(f) is not dict or set(f) != {"all48", "scope"}:
        raise ValueError("top-level fixture schema")
    rows = f["all48"]
    if type(rows) is not list or len(rows) != 48:
        raise ValueError("requires exact 48-row fixture")
    seen, public, exceptional = set(), set(), 0
    for row in rows:
        if type(row) is not dict or set(row) != ROW_FIELDS:
            raise ValueError("unexpected row fields")
        a, b, sector, label = (row[k] for k in ("from", "to", "sector", "scalar_OUTSIDE_runtime"))
        if any(type(x) is not int for x in (a, b, sector, label)):
            raise ValueError("typed cohort metadata")
        if (a, b) not in ((0, 2), (2, 0)) or sector not in range(4) or label not in SCALARS:
            raise ValueError("cohort outside frozen grid")
        k = (a, b, sector, label)
        if k in seen:
            raise ValueError("duplicate cohort")
        seen.add(k)
        packet = (a, b, exact_key(row["input"]))
        if packet in public:
            raise ValueError("duplicate source packet")
        public.add(packet)
        exact_key(row["whole_outputs_equal"])
        if label == 0:
            exceptional += 1
        for arm in ROUTES:
            c = row[arm]
            if type(c) is not dict or set(c) != COUNTERS:
                raise ValueError("counter field set altered")
            if any(type(x) is not int or x < 0 for x in c.values()):
                raise ValueError("nonnegative integer counters required")
    expected = {(a,b,s,label) for a,b in ((0,2),(2,0)) for s in range(4) for label in SCALARS}
    if seen != expected or exceptional != 8:
        raise ValueError("incomplete public cohort grid")
    return {"packets":48, "directions":2, "sectors":4, "exceptional":8,
            "nonexceptional":40, "pre_norm_route_operands":96, "original_blob":ORIGINAL_BLOB,
            "fixture_blob":FROZEN_BLOB, "native_executed":False, "standing":"[pcc:unverified]"}

def source_audit(main_rs: bytes, manifest: bytes) -> None:
    s = main_rs.decode("utf-8")
    c = manifest.decode("utf-8")
    for item in ("ct192_pre_norm_operand", "ct192_actual_norm", "strongest_retained_lift_chain",
                 "direct_composite", "black_box", "D_padd", "N2_actual", "raw_slot_ns_decimal"):
        if item not in s:
            raise ValueError("CT192 Rust driver required symbol missing: " + item)
    if "generator()" in s or "curve::pmul(" in s:
        raise ValueError("driver must never build a pre-norm operand from a known scalar")
    if 'scalar_OUTSIDE_runtime' not in s:
        raise ValueError("cohort scalar label metadata not retained")
    if c.count('name = "chained-n4-fixed-jacobian-chain-norm-reuse-ct192"') != 1:
        raise ValueError("CT192 package identity changed")
    for dep in ("chained-n4-fixed-jacobian-chain", "chained-n4-public-target",
                "ghs-original-engines", "isogeny_algos", "serde_json"):
        if c.count(dep + " =") != 1:
            raise ValueError("required dependency missing: " + dep)

def audit() -> dict:
    original, frozen = ORIGINAL.read_bytes(), FROZEN.read_bytes()
    d = derivative(original)
    validate_class_binding(d)
    f = validate_fixture(frozen)
    source_audit((HERE/"src/main.rs").read_bytes(), (HERE/"Cargo.toml").read_bytes())
    if GENERATED.exists() and GENERATED.read_bytes() != d:
        raise ValueError("materialized CT192 derivative is not exactly the guarded source")
    f["derived_sha256"] = hashlib.sha256(d).hexdigest()
    f["source_audit_passed"] = True
    return f

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialize", action="store_true",
                        help="write derivative only after exact source+fixture checks; not a native run")
    args = parser.parse_args()
    result = audit()
    if args.materialize:
        GENERATED.parent.mkdir(parents=True, exist_ok=True)
        GENERATED.write_bytes(derivative(ORIGINAL.read_bytes()))
        result["derived_materialized"] = True
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__":
    main()
