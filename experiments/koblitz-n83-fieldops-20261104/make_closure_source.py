#!/usr/bin/env python3
"""Derive the closure n=83 producer from the rank-probe producer, exactly.

Input: `snapshots/r770/examples/koblitz_orbit_dlp_fast_online_logcache.rs`
(crypto 770f6a69 plus B's `ic_log_cache.patch`, restored and digest-checked
by `restore.py`).

1. `make_rankprobe_source.py` is `koblitz-n83-rankprobe-20261019`'s
   `make_online_source.py` (PR #980), verbatim, with its verbatim parents
   (`make_rankcut_source.py`, `make_stacked_source.py`,
   `make_tablefilter_source.py`, `make_probepipe_source.py`,
   `make_combined_source.py`). Its derived text must hash to the rank-probe
   protocol's frozen `online_source_sha256` (`RANKPROBE_SHA256` below,
   d4394df3...). That is the rank-probe producer (arms cP / kP of run
   39214027289, the current n = 83 baseline).
2. `closure_edits`: four counted, exact replacements in the wide module.
   A retained base header without `orbit_representatives` (B's K600 header,
   the baseline arms) runs exactly the rank-probe code path: the index is
   built from `factor_base_representatives`, one per column, as before.

   * **Index over orbits, logs over columns.** A `Z[tau]`-closure header
     (`make_closure_base.py`) lists one representative per *orbit*
     (`orbit_representatives`, about 600) apart from one per *column*
     (`factor_base_representatives`, K' = 600 / M). The root index is built
     from the orbit representatives (the same 83 N^2 regular states as K600
     at N = 600 orbits); the columns, the guided rank stage
     (`[a]G - R_c` for the first pivotless column), the linear algebra and
     the `[L_c]G = R_c` check of every log stay on the column
     representatives. Each orbit representative must be a base point.
     The labels already carry a coefficient: member `+-phi^k(alpha(R_c))`
     has label `(c, +-(a + b lambda) lambda^k mod r)`, so `relation_row128`
     and the descent need no change.
   * The summary records `index_orbits` (orbits in the root index) and the
     header's `closure` block (null for B's header).
   * One test module: in the producer's own arithmetic, `alpha(P) =
     [a]P + [b]phi(P)` equals `[(a + b lambda) mod r]P` for every norm <= 64
     multiplier on constructed subgroup points, so every closure label is
     the log of its point relative to its column's representative.

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_rankprobe_source as rankprobe  # noqa: E402  (koblitz-n83-rankprobe-20261019, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_closure.rs"
# protocol.json "sources.online_source_sha256" of koblitz-n83-rankprobe-20261019 (PR #980).
RANKPROBE_SHA256 = "d4394df35d065afbfb05022eac3006492239cc64b94de16fba501322cb578bb5"
WIDE_START = rankprobe.WIDE_START
WIDE_END = rankprobe.WIDE_END
replace = rankprobe.replace

HEAD_OLD = """// rank-cut loop in the target's Frobenius frame, exact to the rank-cut loop.
"""
HEAD_NEW = HEAD_OLD + """// koblitz-n83-closure-20261019: derived from the rank-probe producer by
// make_online_source.py; a Z[tau]-closure base header builds the root index
// from one representative per orbit, apart from the K' log columns.
"""

REPS_OLD = """        let reps: Vec<u128> = representatives
            .iter()
            .map(|p| p.expect("affine representative")[0])
            .collect();
"""
REPS_NEW = """        // koblitz-n83-closure-20261019: a Z[tau]-closure header lists one
        // representative per orbit (the root index) apart from one per
        // column (the logs, the guided rank stage and the log check).
        let orbit_representatives: Option<Vec<Option<[u128; 2]>>> = match constructed {
            Some(_) => None,
            None => header.get("orbit_representatives").map(decode_point_list128),
        };
        let reps: Vec<u128> = orbit_representatives
            .as_ref()
            .unwrap_or(&representatives)
            .iter()
            .map(|p| p.expect("affine representative")[0])
            .collect();
        for x in &reps {
            assert!(base.by_x.contains_key(x), "every orbit representative must be a base point");
        }
"""

SUMMARY_OLD = """            "orbit_columns":base.columns,
            "factor_base_points":base.points.len(),
            "regular_states":index.logical_states,
"""
SUMMARY_NEW = """            "orbit_columns":base.columns,
            "factor_base_points":base.points.len(),
            "index_orbits":reps.len(),
            "closure":header.get("closure").cloned(),
            "regular_states":index.logical_states,
"""

TEST_OLD = """    #[cfg(test)]
    mod rankprobe_tests {
"""
TEST_NEW = """    #[cfg(test)]
    mod closure_tests {
        use super::*;

        /// alpha(P) = [a]P + [b]phi(P) is [(a + b lambda) mod r]P for every
        /// norm <= 64 multiplier (a odd, a > 0), in the producer's arithmetic.
        #[test]
        fn closure_multiplier_is_its_label() {
            let curve = KoblitzCurve::new(1, 83).unwrap();
            let fast = FastBinaryCurve128::new(&curve.curve.irreducible, 1).unwrap();
            let gf = Gf2_128::new(&curve.curve.irreducible);
            let b = gf.from_element(&curve.curve.b);
            let r = curve.subgroup_order.to_u64().unwrap();
            let lambda = curve.lambda.to_u64().unwrap();
            let (_, _, reps, _) = construct_base128(&fast, &curve, b, 3, r);
            let mut checked = 0;
            for rep in reps {
                let p: FastPoint128 = rep.map(|[x, y]| (x, y));
                let phi = p.map(|(x, y)| (gf.sqr(x), gf.sqr(y)));
                for a in (1i64..=7).step_by(2) {
                    for bb in -6i64..=6 {
                        if a * a + a * bb + 2 * bb * bb > 64 {
                            continue;
                        }
                        let pa = fast.scalar_mul(p, &BigUint::from(a as u64));
                        let pb = fast.scalar_mul(phi, &BigUint::from(bb.unsigned_abs()));
                        let pb = if bb < 0 { FastBinaryCurve128::neg(pb) } else { pb };
                        let image = fast.add(pa, pb);
                        let weight = ((a as i128 + bb as i128 * lambda as i128).rem_euclid(r as i128)) as u64;
                        assert_eq!(image, fast.scalar_mul(p, &BigUint::from(weight)), "a={a} b={bb}");
                        checked += 1;
                    }
                }
            }
            assert_eq!(checked, 3 * 38);
        }
    }

    #[cfg(test)]
    mod rankprobe_tests {
"""


def closure_edits(head, wide):
    head = replace(head, HEAD_OLD, HEAD_NEW)
    wide = replace(wide, REPS_OLD, REPS_NEW)
    wide = replace(wide, SUMMARY_OLD, SUMMARY_NEW)
    wide = replace(wide, TEST_OLD, TEST_NEW)
    return head, wide


def rankprobe_text():
    text = rankprobe.derive(rankprobe.rankcut_text())
    digest = hashlib.sha256(text.encode()).hexdigest()
    if digest != RANKPROBE_SHA256:
        raise ValueError("rank-probe derivation differs from koblitz-n83-rankprobe-20261019's frozen producer: "
                         + digest)
    return text


def derive(text):
    head, rest = text.split(WIDE_START, 1)
    wide, tail = rest.split(WIDE_END, 1)
    head, wide = closure_edits(head, wide)
    return head + WIDE_START + wide + WIDE_END + tail


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = derive(rankprobe_text())
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit("derived online source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("online_source_sha256=" + hashlib.sha256(text.encode()).hexdigest())


if __name__ == "__main__":
    sys.exit(main())
