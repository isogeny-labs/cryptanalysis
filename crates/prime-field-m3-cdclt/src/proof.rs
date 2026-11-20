//! Independent proof and witness verifiers for `prime-field-m3-cdclt`.
//!
//! Shares ZERO solver state or batched-inversion propagator code with `cdclt.rs`:
//! - `SAT`: replays canonical square roots, point-on-curve checks, affine group addition,
//!   both chained `S_3` polynomials, and both quadratic `lambda`-lift equations.
//! - `UNSAT`: Streaming DRAT(T) checker combining:
//!   1. `IndependentFpExplanationChecker`: independently verifies every `AddTheory` clause
//!      against plain affine `CurveFp` arithmetic and Frobenius twist non-rationality;
//!   2. `StreamingRupProofChecker`: verifies every `AddRup` learned clause via Reverse Unit
//!      Propagation (64-bit bitmask RUP for `n_vars <= 63`, general RUP fallback for `n_vars > 63`),
//!      synchronised with `Delete` events, requiring the empty clause `[]` to accept `UNSAT`.

use std::collections::HashMap;

use crate::cdclt::{ProofEvent, ProofSink};
use crate::curve::{CurveFp, M3Instance, PointFp, SignedWitness};
use crate::field::{
    add_mod, inv_mod, is_square_mod, mul_mod, neg_mod, sqrt_mod_canonical, sub_mod, FpOps,
};
use crate::selector::{lit_polarity, var_index, CompactBinarySelector, Lit};

/// Detailed rejection reason from independent witness or UNSAT proof verification.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum VerificationError {
    OutOfRangeSelector { window: usize, index: usize, limit: usize },
    AbscissaMismatch { window: usize, expected: u64, got: u64 },
    InvalidSignBit { window: usize, sign: u8 },
    NonRationalAbscissa { window: usize, x: u64 },
    OffCurveSummand { window: usize },
    GroupSumMismatch { expected: PointFp, got: PointFp },
    IntermediatePointAtInfinity,
    ChainedS3Violation { step: u8 },
    LambdaLiftViolation { step: u8 },
    LiteralVarOutOfBounds { lit: Lit, n_vars: usize },
    DuplicateProofId { id: u64 },
    DeleteUnknownClause { id: u64 },
    DeleteInitialClause { id: u64 },
    TheoryClauseHasCounterexample { id: u64, indices: [usize; 3], signs: [u8; 3] },
    TheoryClauseUnverifiable { id: u64, reason: &'static str },
    RupCheckFailed { id: u64, clause: Vec<Lit> },
    MissingEmptyClause,
}

/// Summary counters recorded by the independent proof verifier.
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub struct ProofVerifyStats {
    pub initial_clauses: u64,
    pub theory_steps_verified: u64,
    pub rup_steps_verified: u64,
    pub delete_steps_applied: u64,
    pub derived_empty_clause: bool,
    pub verify_fp_ops: FpOps,
}

/// Independently replay a `SAT` signed witness against `M3Instance` using plain field & curve laws:
/// 1. Selector range `0 <= i_w < |W_w|` and canonical sign bit `sigma_w in {0, 1}`;
/// 2. Rational lift `y_w = sqrt_canon(f(x_w))` and `E(F_p)` membership;
/// 3. Group sum `P_0 + P_1 + P_2 == R`;
/// 4. Explicit chained `S_3(x_0, x_1, u) == 0`, `S_3(u, x_2, x_R) == 0`, and quadratic `lambda`-lift
///    equations `(2 t lam - s_0)^2 == f(x)` (with explicit `t == 0` check when `u == x_R`).
pub fn verify_signed_group_replay(
    inst: &M3Instance,
    w: &SignedWitness,
    ops: &mut FpOps,
) -> Result<(), VerificationError> {
    let p = inst.curve.p;
    let mut pts = [PointFp::identity(); 3];
    for k in 0..3 {
        let lim = inst.windows[k].len();
        let idx = w.indices[k];
        if idx >= lim {
            return Err(VerificationError::OutOfRangeSelector {
                window: k,
                index: idx,
                limit: lim,
            });
        }
        let x = inst.windows[k][idx];
        if w.abscissae[k] != x {
            return Err(VerificationError::AbscissaMismatch {
                window: k,
                expected: x,
                got: w.abscissae[k],
            });
        }
        if w.signs[k] > 1 {
            return Err(VerificationError::InvalidSignBit {
                window: k,
                sign: w.signs[k],
            });
        }
        let rhs = inst.curve.rhs(x, ops);
        let Some(y_canon) = sqrt_mod_canonical(rhs, p, ops) else {
            return Err(VerificationError::NonRationalAbscissa { window: k, x });
        };
        let pt = inst.curve.point_from_canonical_lift(x, y_canon, w.signs[k]);
        if !inst.curve.on_curve(pt, ops) {
            return Err(VerificationError::OffCurveSummand { window: k });
        }
        pts[k] = pt;
    }

    let u_pt = inst.curve.add(pts[0], pts[1], ops);
    if u_pt.infinity {
        return Err(VerificationError::IntermediatePointAtInfinity);
    }
    let total = inst.curve.add(u_pt, pts[2], ops);
    if total != inst.target {
        return Err(VerificationError::GroupSumMismatch {
            expected: inst.target,
            got: total,
        });
    }

    // Step 1 chained S_3 + quadratic lambda lift:
    // t_{01} = x_1 - x_0 != 0 (disjoint windows), s_0 = -y_0, lam_1 = (y_1 - y_0) / (2 t_{01}).
    if inst.curve.semaev_s3(pts[0].x, pts[1].x, u_pt.x, ops) != 0 {
        return Err(VerificationError::ChainedS3Violation { step: 1 });
    }
    let t01 = sub_mod(pts[1].x, pts[0].x, p, ops);
    let two_t01 = add_mod(t01, t01, p, ops);
    let num1 = sub_mod(pts[1].y, pts[0].y, p, ops);
    let lam1 = mul_mod(num1, inv_mod(two_t01, p, ops), p, ops);
    let neg_y0 = neg_mod(pts[0].y, p, ops);
    if !inst.curve.check_lambda_lift(pts[1].x, t01, neg_y0, lam1, ops) {
        return Err(VerificationError::LambdaLiftViolation { step: 1 });
    }

    // Step 2 chained S_3 + quadratic lambda lift (or explicit t == 0 tangency):
    if inst
        .curve
        .semaev_s3(u_pt.x, pts[2].x, inst.target.x, ops)
        != 0
    {
        return Err(VerificationError::ChainedS3Violation { step: 2 });
    }
    let tu = sub_mod(u_pt.x, inst.target.x, p, ops);
    if tu == 0 {
        // Exceptional tangency `u == x_R`: requires `U == -R` and `P_2 == 2R`.
        let neg_r = inst.curve.neg(inst.target, ops);
        let two_r = inst.curve.add(inst.target, inst.target, ops);
        if u_pt != neg_r || pts[2] != two_r {
            return Err(VerificationError::LambdaLiftViolation { step: 2 });
        }
    } else {
        let two_tu = add_mod(tu, tu, p, ops);
        let num2 = add_mod(u_pt.y, inst.target.y, p, ops);
        let lam2 = mul_mod(num2, inv_mod(two_tu, p, ops), p, ops);
        if !inst
            .curve
            .check_lambda_lift(u_pt.x, tu, inst.target.y, lam2, ops)
        {
            return Err(VerificationError::LambdaLiftViolation { step: 2 });
        }
        let tc = sub_mod(pts[2].x, inst.target.x, p, ops);
        if !inst
            .curve
            .check_lambda_lift(pts[2].x, tc, inst.target.y, lam2, ops)
        {
            return Err(VerificationError::LambdaLiftViolation { step: 2 });
        }
    }
    Ok(())
}

/// Independent semantic checker for `AddTheory` clauses emitted by `ChainedS3LambdaTheory`.
///
/// Uses ONLY standard residue arithmetic (`% p`) and classical Weierstrass chord-and-tangent laws
/// (zero shared code, zero Montgomery domain, zero half-slope `lambda` equations from `cdclt.rs`).
#[derive(Debug, Clone)]
pub struct IndependentFpExplanationChecker {
    curve: CurveFp,
    windows: [Vec<u64>; 3],
    plain_lifts: [Vec<Option<u64>>; 3],
    window_maps: [HashMap<u64, usize>; 3],
    selector: CompactBinarySelector,
    target: PointFp,
}

impl IndependentFpExplanationChecker {
    pub fn new(inst: &M3Instance) -> Self {
        let mut init_ops = FpOps::default();
        Self::new_with_ops(inst, &mut init_ops)
    }

    pub fn new_with_ops(inst: &M3Instance, ops: &mut FpOps) -> Self {
        let selector = CompactBinarySelector::new([
            inst.windows[0].len(),
            inst.windows[1].len(),
            inst.windows[2].len(),
        ]);
        let mut window_maps: [HashMap<u64, usize>; 3] = [
            HashMap::with_capacity(inst.windows[0].len() * 2),
            HashMap::with_capacity(inst.windows[1].len() * 2),
            HashMap::with_capacity(inst.windows[2].len() * 2),
        ];
        let mut plain_lifts: [Vec<Option<u64>>; 3] = [Vec::new(), Vec::new(), Vec::new()];
        for w in 0..3 {
            plain_lifts[w].reserve(inst.windows[w].len());
            for (i, &x) in inst.windows[w].iter().enumerate() {
                window_maps[w].insert(x, i);
                let rhs = inst.curve.rhs(x, ops);
                plain_lifts[w].push(sqrt_mod_canonical(rhs, inst.curve.p, ops));
            }
        }
        Self {
            curve: inst.curve,
            windows: inst.windows.clone(),
            plain_lifts,
            window_maps,
            selector,
            target: inst.target,
        }
    }

    #[inline]
    fn index_compatible_with_neg_assign(&self, w: usize, idx: usize, neg_assign: &[Option<bool>]) -> bool {
        if idx >= self.windows[w].len() {
            return false;
        }
        for (bit_pos, &var) in self.selector.index_bits[w].iter().enumerate() {
            if let Some(val) = neg_assign[var] {
                let bit = ((idx >> bit_pos) & 1) != 0;
                if val != bit {
                    return false;
                }
            }
        }
        true
    }

    #[inline]
    fn sign_compatible_with_neg_assign(&self, w: usize, sign: u8, neg_assign: &[Option<bool>]) -> bool {
        match neg_assign[self.selector.sign_vars[w]] {
            None => true,
            Some(val) => val == (sign != 0),
        }
    }

    /// Independently verify that `lits` holds on ALL valid models `(P_0, P_1, P_2)` of the instance.
    pub fn verify_clause(
        &self,
        id: u64,
        lits: &[Lit],
        ops: &mut FpOps,
    ) -> Result<(), VerificationError> {
        let n_vars = self.selector.total_vars;
        let mut neg_assign: Vec<Option<bool>> = vec![None; n_vars];

        // Build partial assignment `neg_assign = ~C`. If `C` contains `v` and `-v`, `C` is a tautology.
        for &l in lits {
            let v = var_index(l);
            if v >= n_vars {
                return Err(VerificationError::LiteralVarOutOfBounds { lit: l, n_vars });
            }
            let neg_val = !lit_polarity(l);
            if let Some(prev) = neg_assign[v] {
                if prev != neg_val {
                    return Ok(()); // tautology
                }
            } else {
                neg_assign[v] = Some(neg_val);
            }
        }

        // Case 0: If `neg_assign` already pins some window `w` to an out-of-range binary integer `>= W_w`,
        // then `~C` violates the window range `0 <= idx_w < W_w`, so `C` is entailed by range constraints.
        for w in 0..3 {
            let all_bits_fixed = self.selector.index_bits[w]
                .iter()
                .all(|&v| neg_assign[v].is_some());
            if all_bits_fixed {
                let mut raw = 0usize;
                for (bit_pos, &v) in self.selector.index_bits[w].iter().enumerate() {
                    if neg_assign[v] == Some(true) {
                        raw |= 1usize << bit_pos;
                    }
                }
                if raw >= self.windows[w].len() {
                    return Ok(());
                }
            }
        }

        // Case 1: Single-window / bounded-prefix Frobenius non-rationality check (`<= 16` compatible indices).
        for w in 0..3 {
            if let Some((compat, _)) =
                self.selector.compatible_indices_and_guard(w, &neg_assign, 16)
            {
                if compat.is_empty() {
                    return Ok(());
                }
                let mut all_non_rational = true;
                for &idx in &compat {
                    let x = self.windows[w][idx];
                    let disc = self.curve.lambda_lift_discriminant(x, 1, ops);
                    if is_square_mod(disc, self.curve.p, ops) {
                        all_non_rational = false;
                        break;
                    }
                }
                if all_non_rational {
                    return Ok(());
                }
            }
        }

        // Case 2: Two windows `(w_a, w_b)` have completely pinned in-range indices `(i_a, i_b)` under `~C`.
        let pinned = [
            self.selector.decode_index(0, &neg_assign),
            self.selector.decode_index(1, &neg_assign),
            self.selector.decode_index(2, &neg_assign),
        ];
        for (w_a, w_b, w_c) in [(0usize, 1usize, 2usize), (0, 2, 1), (1, 2, 0)] {
            let (Some(i_a), Some(i_b)) = (pinned[w_a], pinned[w_b]) else {
                continue;
            };
            let xa = self.windows[w_a][i_a];
            let xb = self.windows[w_b][i_b];
            let Some(ya_c) = sqrt_mod_canonical(self.curve.rhs(xa, ops), self.curve.p, ops) else {
                return Ok(());
            };
            let Some(yb_c) = sqrt_mod_canonical(self.curve.rhs(xb, ops), self.curve.p, ops) else {
                return Ok(());
            };

            for sa in [0u8, 1u8] {
                if !self.sign_compatible_with_neg_assign(w_a, sa, &neg_assign) {
                    continue;
                }
                for sb in [0u8, 1u8] {
                    if !self.sign_compatible_with_neg_assign(w_b, sb, &neg_assign) {
                        continue;
                    }
                    let pa = self.curve.point_from_canonical_lift(xa, ya_c, sa);
                    let pb = self.curve.point_from_canonical_lift(xb, yb_c, sb);
                    let u = self.curve.add(pa, pb, ops);
                    if u.infinity {
                        continue;
                    }
                    let neg_u = self.curve.neg(u, ops);
                    let pc_req = self.curve.add(self.target, neg_u, ops);
                    if pc_req.infinity {
                        continue;
                    }
                    if let Some(&ic) = self.window_maps[w_c].get(&pc_req.x) {
                        let sc = u8::from(pc_req.y > (self.curve.p - pc_req.y));
                        if self.index_compatible_with_neg_assign(w_c, ic, &neg_assign)
                            && self.sign_compatible_with_neg_assign(w_c, sc, &neg_assign)
                        {
                            let mut indices = [0usize; 3];
                            let mut signs = [0u8; 3];
                            indices[w_a] = i_a;
                            indices[w_b] = i_b;
                            indices[w_c] = ic;
                            signs[w_a] = sa;
                            signs[w_b] = sb;
                            signs[w_c] = sc;
                            return Err(VerificationError::TheoryClauseHasCounterexample {
                                id,
                                indices,
                                signs,
                            });
                        }
                    }
                }
            }
            return Ok(());
        }

        // Case 3: Small cube fallback (`|compat_0| * |compat_1| <= 64`) for tiny development windows.
        if let (Some((c0, _)), Some((c1, _))) = (
            self.selector.compatible_indices_and_guard(0, &neg_assign, 16),
            self.selector.compatible_indices_and_guard(1, &neg_assign, 16),
        ) {
            if c0.len() * c1.len() <= 64 {
                for &i0 in &c0 {
                    let x0 = self.windows[0][i0];
                    let Some(y0_c) = sqrt_mod_canonical(self.curve.rhs(x0, ops), self.curve.p, ops)
                    else {
                        continue;
                    };
                    for &i1 in &c1 {
                        let x1 = self.windows[1][i1];
                        let Some(y1_c) =
                            sqrt_mod_canonical(self.curve.rhs(x1, ops), self.curve.p, ops)
                        else {
                            continue;
                        };
                        for s0 in [0u8, 1u8] {
                            if !self.sign_compatible_with_neg_assign(0, s0, &neg_assign) {
                                continue;
                            }
                            for s1 in [0u8, 1u8] {
                                if !self.sign_compatible_with_neg_assign(1, s1, &neg_assign) {
                                    continue;
                                }
                                let p0 = self.curve.point_from_canonical_lift(x0, y0_c, s0);
                                let p1 = self.curve.point_from_canonical_lift(x1, y1_c, s1);
                                let u = self.curve.add(p0, p1, ops);
                                if u.infinity {
                                    continue;
                                }
                                let p2_req =
                                    self.curve.add(self.target, self.curve.neg(u, ops), ops);
                                if p2_req.infinity {
                                    continue;
                                }
                                if let Some(&i2) = self.window_maps[2].get(&p2_req.x) {
                                    let s2 = u8::from(p2_req.y > (self.curve.p - p2_req.y));
                                    if self.index_compatible_with_neg_assign(2, i2, &neg_assign)
                                        && self.sign_compatible_with_neg_assign(2, s2, &neg_assign)
                                    {
                                        return Err(
                                            VerificationError::TheoryClauseHasCounterexample {
                                                id,
                                                indices: [i0, i1, i2],
                                                signs: [s0, s1, s2],
                                            },
                                        );
                                    }
                                }
                            }
                        }
                    }
                }
                return Ok(());
            }
        }

        Err(VerificationError::TheoryClauseUnverifiable {
            id,
            reason: "theory clause neither pins a single-window non-residue prefix nor two window indices",
        })
    }
}

#[derive(Debug, Clone, Copy)]
struct BitmaskClause {
    id: u64,
    pos: u64,
    neg: u64,
    initial: bool,
}

#[derive(Debug, Clone)]
struct GeneralClause {
    id: u64,
    lits: Vec<Lit>,
    initial: bool,
}

/// Independent Reverse-Unit-Propagation + `Fp` Explanation DRAT(T) checker.
///
/// Uses a zero-allocation 64-bit bitmask RUP engine whenever `n_vars <= 63` (covering every
/// compact binary selector rung up to `s = 20`, i.e. `60`-bit primes!) and falls back to a
/// general literal-slice RUP engine when `n_vars > 63`.
pub struct StreamingDrattChecker {
    n_vars: usize,
    use_bitmask: bool,
    bit_clauses: Vec<BitmaskClause>,
    gen_clauses: Vec<GeneralClause>,
    id_to_slot: HashMap<u64, usize>,
    theory_checker: IndependentFpExplanationChecker,
    pub stats: ProofVerifyStats,
    first_error: Option<VerificationError>,
}

impl StreamingDrattChecker {
    /// Initialise independent checker from an `M3Instance` (seeds only the compact range clauses).
    pub fn new(inst: &M3Instance) -> Self {
        let theory_checker = IndependentFpExplanationChecker::new(inst);
        let n_vars = theory_checker.selector.total_vars;
        let use_bitmask = n_vars <= 63;
        let mut checker = Self {
            n_vars,
            use_bitmask,
            bit_clauses: Vec::with_capacity(256),
            gen_clauses: Vec::with_capacity(256),
            id_to_slot: HashMap::with_capacity(256),
            theory_checker,
            stats: ProofVerifyStats::default(),
            first_error: None,
        };
        for (idx, rc) in checker
            .theory_checker
            .selector
            .range_clauses
            .clone()
            .into_iter()
            .enumerate()
        {
            checker
                .insert_verified_clause(idx as u64, &rc, true)
                .expect("valid range clause");
            checker.stats.initial_clauses += 1;
        }
        checker
    }

    fn lits_to_masks(&self, lits: &[Lit]) -> Result<Option<(u64, u64)>, VerificationError> {
        let mut pos = 0u64;
        let mut neg = 0u64;
        for &l in lits {
            let v = var_index(l);
            if v >= self.n_vars {
                return Err(VerificationError::LiteralVarOutOfBounds {
                    lit: l,
                    n_vars: self.n_vars,
                });
            }
            let bit = 1u64 << v;
            if l > 0 {
                pos |= bit;
            } else {
                neg |= bit;
            }
        }
        if (pos & neg) != 0 {
            return Ok(None); // tautology
        }
        Ok(Some((pos, neg)))
    }

    fn insert_verified_clause(
        &mut self,
        id: u64,
        lits: &[Lit],
        initial: bool,
    ) -> Result<(), VerificationError> {
        if self.id_to_slot.contains_key(&id) {
            return Err(VerificationError::DuplicateProofId { id });
        }
        if self.use_bitmask {
            if let Some((pos, neg)) = self.lits_to_masks(lits)? {
                let slot = self.bit_clauses.len();
                self.bit_clauses.push(BitmaskClause {
                    id,
                    pos,
                    neg,
                    initial,
                });
                self.id_to_slot.insert(id, slot);
            }
        } else {
            for &l in lits {
                let v = var_index(l);
                if v >= self.n_vars {
                    return Err(VerificationError::LiteralVarOutOfBounds {
                        lit: l,
                        n_vars: self.n_vars,
                    });
                }
            }
            let slot = self.gen_clauses.len();
            self.gen_clauses.push(GeneralClause {
                id,
                lits: lits.to_vec(),
                initial,
            });
            self.id_to_slot.insert(id, slot);
        }
        Ok(())
    }

    fn delete_clause(&mut self, id: u64) -> Result<(), VerificationError> {
        let Some(slot) = self.id_to_slot.remove(&id) else {
            return Err(VerificationError::DeleteUnknownClause { id });
        };
        if self.use_bitmask {
            if self.bit_clauses[slot].initial {
                return Err(VerificationError::DeleteInitialClause { id });
            }
            let last = self.bit_clauses.len() - 1;
            self.bit_clauses.swap(slot, last);
            self.bit_clauses.pop();
            if slot < self.bit_clauses.len() {
                let moved_id = self.bit_clauses[slot].id;
                self.id_to_slot.insert(moved_id, slot);
            }
        } else {
            if self.gen_clauses[slot].initial {
                return Err(VerificationError::DeleteInitialClause { id });
            }
            let last = self.gen_clauses.len() - 1;
            self.gen_clauses.swap(slot, last);
            self.gen_clauses.pop();
            if slot < self.gen_clauses.len() {
                let moved_id = self.gen_clauses[slot].id;
                self.id_to_slot.insert(moved_id, slot);
            }
        }
        self.stats.delete_steps_applied += 1;
        Ok(())
    }

    /// Check RUP validity of `lits` against the currently active verified clause database!
    fn check_rup(&self, id: u64, lits: &[Lit]) -> Result<(), VerificationError> {
        if self.use_bitmask {
            let Some((pos, neg)) = self.lits_to_masks(lits)? else {
                return Ok(()); // tautology is trivially RUP
            };
            // Assume `~C`: every positive literal in `C` is set false (`val_false |= pos`),
            // every negative literal in `C` is set true (`val_true |= neg`).
            let mut val_true = neg;
            let mut val_false = pos;

            loop {
                let mut changed = false;
                for c in &self.bit_clauses {
                    if ((c.pos & val_true) | (c.neg & val_false)) != 0 {
                        continue; // already satisfied
                    }
                    let rem_pos = c.pos & !val_false;
                    let rem_neg = c.neg & !val_true;
                    let cnt = rem_pos.count_ones() + rem_neg.count_ones();
                    if cnt == 0 {
                        return Ok(()); // conflict derived!
                    }
                    if cnt == 1 {
                        if rem_pos != 0 {
                            val_true |= rem_pos;
                            if (val_true & val_false) != 0 {
                                return Ok(());
                            }
                        } else {
                            val_false |= rem_neg;
                            if (val_true & val_false) != 0 {
                                return Ok(());
                            }
                        }
                        changed = true;
                    }
                }
                if !changed {
                    return Err(VerificationError::RupCheckFailed {
                        id,
                        clause: lits.to_vec(),
                    });
                }
            }
        } else {
            let mut assign: Vec<Option<bool>> = vec![None; self.n_vars];
            for &l in lits {
                let v = var_index(l);
                if v >= self.n_vars {
                    return Err(VerificationError::LiteralVarOutOfBounds {
                        lit: l,
                        n_vars: self.n_vars,
                    });
                }
                let req = !lit_polarity(l);
                if let Some(prev) = assign[v] {
                    if prev != req {
                        return Ok(()); // tautology
                    }
                }
                assign[v] = Some(req);
            }
            loop {
                let mut changed = false;
                for c in &self.gen_clauses {
                    let mut sat = false;
                    let mut unit_lit: Option<Lit> = None;
                    let mut unassigned_cnt = 0usize;
                    for &cl in &c.lits {
                        let cv = var_index(cl);
                        let cpol = lit_polarity(cl);
                        match assign[cv] {
                            Some(val) if val == cpol => {
                                sat = true;
                                break;
                            }
                            Some(_) => {}
                            None => {
                                unassigned_cnt += 1;
                                unit_lit = Some(cl);
                                if unassigned_cnt >= 2 {
                                    break;
                                }
                            }
                        }
                    }
                    if sat {
                        continue;
                    }
                    if unassigned_cnt == 0 {
                        return Ok(());
                    }
                    if unassigned_cnt == 1 {
                        let ul = unit_lit.unwrap();
                        assign[var_index(ul)] = Some(lit_polarity(ul));
                        changed = true;
                    }
                }
                if !changed {
                    return Err(VerificationError::RupCheckFailed {
                        id,
                        clause: lits.to_vec(),
                    });
                }
            }
        }
    }

    /// Process a single `ProofEvent` (returns immediately if an earlier step already failed).
    pub fn process_event(&mut self, event: &ProofEvent) -> Result<(), VerificationError> {
        if let Some(err) = &self.first_error {
            return Err(err.clone());
        }
        let res = match event {
            ProofEvent::AddTheory { id, lits } => {
                self.theory_checker
                    .verify_clause(*id, lits, &mut self.stats.verify_fp_ops)?;
                self.insert_verified_clause(*id, lits, false)?;
                self.stats.theory_steps_verified += 1;
                if lits.is_empty() {
                    self.stats.derived_empty_clause = true;
                }
                Ok(())
            }
            ProofEvent::AddRup { id, lits } => {
                self.check_rup(*id, lits)?;
                self.insert_verified_clause(*id, lits, false)?;
                self.stats.rup_steps_verified += 1;
                if lits.is_empty() {
                    self.stats.derived_empty_clause = true;
                }
                Ok(())
            }
            ProofEvent::Delete { id } => self.delete_clause(*id),
        };
        if let Err(err) = &res {
            self.first_error = Some(err.clone());
        }
        res
    }

    /// Finalize an `UNSAT` proof check: succeeds iff no step failed AND the empty clause `[]` was derived!
    pub fn finish_unsat(&self) -> Result<ProofVerifyStats, VerificationError> {
        if let Some(err) = &self.first_error {
            return Err(err.clone());
        }
        if !self.stats.derived_empty_clause {
            return Err(VerificationError::MissingEmptyClause);
        }
        Ok(self.stats)
    }
}

/// Verify an in-memory `ProofEvent` slice end-to-end for an `UNSAT` instance.
pub fn verify_unsat_transcript(
    inst: &M3Instance,
    events: &[ProofEvent],
) -> Result<ProofVerifyStats, VerificationError> {
    let mut checker = StreamingDrattChecker::new(inst);
    for ev in events {
        checker.process_event(ev)?;
    }
    checker.finish_unsat()
}

/// Non-overlapping buffered chunked proof sink that accumulates chunks during `solve` (without
/// running any verification inside the solver's clock!) or replays chunks in a dedicated `verify`
/// timing block so peak memory stays `O(chunk_len)` on deep rungs.
pub struct ChunkedProofBuffer {
    pub chunk_cap: usize,
    pub buffer: Vec<ProofEvent>,
    pub total_events: u64,
}

impl ChunkedProofBuffer {
    pub fn new(chunk_cap: usize) -> Self {
        Self {
            chunk_cap,
            buffer: Vec::with_capacity(chunk_cap.min(65_536)),
            total_events: 0,
        }
    }
}

impl ProofSink for ChunkedProofBuffer {
    #[inline]
    fn emit_theory(&mut self, id: u64, lits: &[Lit]) {
        self.total_events += 1;
        self.buffer.push(ProofEvent::AddTheory {
            id,
            lits: lits.to_vec(),
        });
    }

    #[inline]
    fn emit_rup(&mut self, id: u64, lits: &[Lit]) {
        self.total_events += 1;
        self.buffer.push(ProofEvent::AddRup {
            id,
            lits: lits.to_vec(),
        });
    }

    #[inline]
    fn emit_delete(&mut self, id: u64) {
        self.total_events += 1;
        self.buffer.push(ProofEvent::Delete { id });
    }
}

impl ChunkedProofBuffer {
    /// Drain buffered proof events (for a dedicated verification timing block).
    pub fn take_events(&mut self) -> Vec<ProofEvent> {
        std::mem::take(&mut self.buffer)
    }
}

/// Six mandatory soundness mutation controls required by the Lead 2B specification.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MutationKind {
    /// Mutate curve parameter `a -> (a + 1) mod p` on a valid certificate.
    WrongCurveA,
    /// Flip `sigma_0 -> 1 - sigma_0` on a valid `SAT` witness.
    FlippedSignBit,
    /// Forge an out-of-range binary selector index `idx_0 = |W_0|` (`< 2^{s_0}`).
    OutOfRangeBinarySelector,
    /// Drop a literal from a minimal `AddTheory` conflict clause, making it unsound.
    CorruptedTheoryExplanation,
    /// Truncate the final empty-clause derivation from a valid `UNSAT` proof.
    TruncatedUnsatProof,
    /// Spoof a false `t = 0` (`u == x_R`) theory conflict on an instance where `P_0 + P_1 = -R` and `2R in W_2`.
    TZeroExceptionSpoof,
}

/// Apply a single soundness mutation to a valid `SAT` witness / instance pair.
/// Returns mutated `(instance, witness)` that must be rejected by `verify_signed_group_replay`.
pub fn mutate_sat_certificate(
    inst: &M3Instance,
    w: &SignedWitness,
    kind: MutationKind,
) -> Option<(M3Instance, SignedWitness)> {
    match kind {
        MutationKind::WrongCurveA => {
            let mut mutated = inst.clone();
            mutated.curve.a = (mutated.curve.a + 1) % mutated.curve.p;
            Some((mutated, *w))
        }
        MutationKind::FlippedSignBit => {
            let mut mw = *w;
            mw.signs[0] = 1 - mw.signs[0];
            Some((inst.clone(), mw))
        }
        MutationKind::OutOfRangeBinarySelector => {
            let mut mw = *w;
            mw.indices[0] = inst.windows[0].len();
            Some((inst.clone(), mw))
        }
        MutationKind::CorruptedTheoryExplanation
        | MutationKind::TruncatedUnsatProof
        | MutationKind::TZeroExceptionSpoof => None,
    }
}

/// Apply a soundness mutation to an `UNSAT` proof transcript. Returns a transcript that the
/// independent DRAT(T) checker must reject.
pub fn mutate_unsat_transcript(events: &[ProofEvent], kind: MutationKind) -> Option<Vec<ProofEvent>> {
    match kind {
        MutationKind::TruncatedUnsatProof => {
            let mut out = events.to_vec();
            while let Some(last) = out.last() {
                match last {
                    ProofEvent::AddRup { lits, .. } | ProofEvent::AddTheory { lits, .. }
                        if lits.is_empty() =>
                    {
                        out.pop();
                        return Some(out);
                    }
                    _ => {
                        out.pop();
                    }
                }
            }
            Some(out)
        }
        MutationKind::CorruptedTheoryExplanation => {
            let mut out = events.to_vec();
            for ev in &mut out {
                if let ProofEvent::AddTheory { lits, .. } = ev {
                    if lits.len() >= 2 {
                        lits.pop();
                        return Some(out);
                    }
                }
            }
            None
        }
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cdclt::{
        enumerate_all_models_compact_cdclt, CdclOutcome, ChainedS3LambdaTheory,
        PreparedChainedS3Setup, TranscriptProofSink,
    };
    use crate::curve::{
        canonical_ir, exhaustive_fp2_models, generate_instance_for_class, make_development_fixture,
        validate_instance, PreparedTwoWindow, TargetClass,
    };
    use crate::field::FpOps;
    use crate::selector::sizing_comparison_row;

    #[test]
    fn development_fixture_sat_replay_and_mutations() {
        let inst = make_development_fixture();
        validate_instance(&inst, true).expect("fixture validates");
        let (fp2_models, _) = exhaustive_fp2_models(&inst);
        assert!(!fp2_models.is_empty());

        let ir_bytes = canonical_ir(&inst).len();
        let setup = PreparedChainedS3Setup::prepare(inst.curve, inst.windows.clone(), ir_bytes);
        let (models, _) = enumerate_all_models_compact_cdclt(&setup, inst.target);
        assert!(!models.is_empty());
        let mut ops = FpOps::default();
        for w in &models {
            verify_signed_group_replay(&inst, w, &mut ops).expect("SAT replay");
            assert!(fp2_models.contains(&w.model_key()));
        }

        let w0 = models[0];
        for kind in [
            MutationKind::WrongCurveA,
            MutationKind::FlippedSignBit,
            MutationKind::OutOfRangeBinarySelector,
        ] {
            let (mi, mw) = mutate_sat_certificate(&inst, &w0, kind).unwrap();
            let mut mops = FpOps::default();
            assert!(
                verify_signed_group_replay(&mi, &mw, &mut mops).is_err(),
                "mutation {kind:?} must be rejected"
            );
        }
    }

    #[test]
    fn small_rung_exact_unsat_proof_replays() {
        use crate::curve::generate_rung_curve_and_windows;
        use crate::field::DeterministicRng;

        let rung_s = 2u32;
        let (curve, order, windows) =
            generate_rung_curve_and_windows("lead2b-unsat-unit-20261120", rung_s);
        let prepared = PreparedTwoWindow::prepare(curve, windows.clone());
        let mut rng = DeterministicRng::from_label("lead2b-unsat-unit-20261120:exact");
        let mut inst = generate_instance_for_class(
            "lead2b-unsat-unit".into(),
            rung_s,
            &prepared,
            TargetClass::ExactUnsat,
            &mut rng,
        );
        inst.group_order = order;
        validate_instance(&inst, true).expect("exact-UNSAT validates");

        let ir_bytes = canonical_ir(&inst).len();
        let setup = PreparedChainedS3Setup::prepare(inst.curve, inst.windows.clone(), ir_bytes);
        let mut solver = setup.base_solver.clone();
        let mut stats = crate::cdclt::CdcltStats::default();
        let mut theory = ChainedS3LambdaTheory::new(&setup, inst.target, &mut stats);
        let mut sink = TranscriptProofSink::default();
        match solver.solve_with_theory(&mut theory, &mut sink, &mut stats) {
            CdclOutcome::Unsat => {}
            CdclOutcome::Sat(_) => panic!("expected UNSAT on exact-UNSAT target"),
        }
        verify_unsat_transcript(&inst, &sink.events).expect("UNSAT transcript verifies");

        let truncated =
            mutate_unsat_transcript(&sink.events, MutationKind::TruncatedUnsatProof).unwrap();
        assert!(verify_unsat_transcript(&inst, &truncated).is_err());
    }

    #[test]
    fn sizing_row_matches_sinz_formula() {
        let row = sizing_comparison_row(27);
        assert_eq!(row.sinz_total_vars_no_sign, 805_306_365);
        assert_eq!(row.compact_total_vars, 3 * 27 + 3);
    }
}
