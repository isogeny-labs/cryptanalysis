#!/usr/bin/env python3
"""Guarded sibling derivative: implement norm-point reuse, never edit the original.

The source blob, the two replaced blocks, original diagnostics, and independent
final actual-norm checks are pinned. This is implementation, NOT native proof,
a benchmark, or an ECDLP advantage. See NORM_POINT_REUSE_PROTOCOL_01.md.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

LIB_BLOB = "8016634385d76207b23a3eb3a4dae9b0366ac68d"
COUNTER_OLD = "    pub degree169_elliptic_evaluation: u64,\n"
COUNTER_NEW = COUNTER_OLD + "    pub norm_point_doubling: u64,\n"
ANCHOR = "    fn corrected_lift(&self, input: &Entry, to: usize, p: Pt<ER>) -> Result<(Pt<ER>, Value)> {\n"
HELPER = """    /// Compute the transported norm from the actual final elliptic point Z:
    /// N(Phi(Z))=[2]Z, rather than re-evaluating the isogeny at the source norm.
    /// check_final() retains its independent actual Jacobian norm comparison.
    fn norm_from_target_point(&self, to: usize, z: Pt<ER>) -> Result<Pt<ER>> {
        let target = &self.geometry.models[to].quadratic;
        target.admit(&z)?;
        let doubled = curve::padd(&target.f, &target.curve, &z, &z);
        target.admit(&doubled)?;
        let rational = descend_point(doubled);
        let source = &self.geometry.models[to].source;
        if !curve::on_curve(source.field(), source.curve(), &rational) {
            return Err("reused norm did not descend to the target prime field".into());
        }
        self.bump(|c| c.norm_point_doubling += 1);
        Ok(rational)
    }
"""
DIRECT_OLD = """        let class = self.target_phi(to, self.gamma(input.domain, to, lifted)?)?;
        let norm = descend_point(self.gamma(input.domain, to, lift(input.norm))?);
"""
DIRECT_NEW = """        let z = self.gamma(input.domain, to, lifted)?;
        let class = self.target_phi(to, z)?;
        let norm = self.norm_from_target_point(to, z)?;
"""
RETAINED_OLD = """        let point = self.gamma(1, to, self.gamma(input.domain, 1, lifted)?)?;
        let class = self.target_phi(to, point)?;
        let norm =
            descend_point(self.gamma(1, to, self.gamma(input.domain, 1, lift(input.norm))?)?);
"""
RETAINED_NEW = """        let point = self.gamma(1, to, self.gamma(input.domain, 1, lifted)?)?;
        let class = self.target_phi(to, point)?;
        let norm = self.norm_from_target_point(to, point)?;
"""

def git_blob(content):
    payload = content.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise ValueError(f"{label}: expected one exact original block, found {count}")
    return text.replace(old, new, 1)

def transform(original, *, pinned=True):
    if pinned and git_blob(original) != LIB_BLOB:
        raise ValueError("original lib.rs blob changed: refuse to patch a different program")
    result = original
    for label, old, new in (
        ("counter", COUNTER_OLD, COUNTER_NEW),
        ("helper", ANCHOR, HELPER + ANCHOR),
        ("direct route", DIRECT_OLD, DIRECT_NEW),
        ("retained route", RETAINED_OLD, RETAINED_NEW),
    ):
        result = replace_once(result, old, new, label)
    if result.count("norm_from_target_point(to, ") != 2:
        raise ValueError("unexpected number of reused route calls")
    if result.count("norm_point_doubling += 1") != 1:
        raise ValueError("counter instrumentation changed")
    if "self.transfer_entry(&self.transfer_entry(input, 1)?, to)" not in result:
        raise ValueError("literal sequential route changed")
    if "let norm = descend_point(self.gamma(from, to, lift(input.norm))?);" not in result:
        raise ValueError("diagnose_half control changed")
    if "if ep(n.norm(&entry.class)?) != entry.norm {" not in result:
        raise ValueError("actual independent final norm validation changed")
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--original", type=Path, required=True,
                    help="fixed-jacobian-chain-evaluator-01")
    ap.add_argument("--out", type=Path, required=True,
                    help="new sibling fixed-jacobian-chain-reuse-01")
    args = ap.parse_args()
    original, out = args.original.resolve(), args.out.resolve()
    if original.name != "fixed-jacobian-chain-evaluator-01":
        ap.error("wrong original package")
    if out.name != "fixed-jacobian-chain-reuse-01" or out.parent != original.parent:
        ap.error("out must be a new sibling with exact declared name")
    if out.exists():
        ap.error("refuse to overwrite an existing derivative")
    old = (original / "src/lib.rs").read_text("utf-8")
    new = transform(old)
    shutil.copytree(original, out, symlinks=True,
                    ignore=shutil.ignore_patterns("target", "*.tmp", "__pycache__"))
    (out / "src/lib.rs").write_text(new, "utf-8")
    receipt = {
        "protocol": "NORM_POINT_REUSE_PROTOCOL_01.md",
        "original_git_blob": git_blob(old),
        "derivative_git_blob": git_blob(new),
        "original_path": "fixed-jacobian-chain-evaluator-01/src/lib.rs",
        "derivative_path": "fixed-jacobian-chain-reuse-01/src/lib.rs",
        "replacements": [
            "one extra counted doubling field",
            "checked target-point doubling with prime-field descent",
            "direct: C169 2->1, doubling 0->1",
            "retained: C13 4->2, doubling 0->1",
            "literal: inherited sequential double transfer C13 4->2, doubling 0->2",
        ],
        "preserved": [
            "diagnose_half", "check_final actual norm", "all fixed models",
            "public/cofactor/exceptional tests", "full source algebraic scalar",
        ],
        "status": "[pcc:unverified]; derivative not yet compiled or timed",
    }
    (out / "NORM_REUSE_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(receipt, sort_keys=True))

if __name__ == "__main__":
    main()
