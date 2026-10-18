//! **Five summands by meet in the middle**: the `m = 5` arm of
//! [`PairSumTable::witnesses_fast`].
//!
//! A sorted witness `i ≤ j ≤ k ≤ l ≤ t` of `R = P_i + … + P_t` splits
//! into a stored pair `P_i + P_j` and an enumerated triple
//! `P_k + P_l + P_t`: the scan walks every triple `k ≤ l ≤ t` and asks
//! the table for the pairs summing to `R − P_t − P_l − P_k`, keeping
//! the ones with `j ≤ k`.  That is `|F|³/6` lookups a target against
//! the `|F|⁴/24` group operations of exhaustive enumeration, and it is
//! exact and complete for the same reason the `m = 4` arm is: every
//! sorted witness has exactly one such split, and the table answers
//! every pair it holds on every tier.
//!
//! **Batched rows, nested.**  The `m = 4` arm forms each row's pair
//! sums `P_l + P_k` with one batched addition and the rests with a
//! second.  Here the prefix is shared instead: `R − P_t` for every `t`
//! is one batched row up front, `R − P_t − P_l` for every `l ≤ t` is one
//! batched row per `t`, and the rests `R − P_t − P_l − P_k` for every
//! `k ≤ l` are one batched row per `(l, t)`.  Each rest is then a single
//! addition of a pre-negated base point, with Montgomery's trick
//! amortising one field inversion over the row — no negation pass and
//! no second slice per row.  Short rows (`l + 1` rests each) are grouped
//! up to [`ROW_GROUP`] rests and added pairwise with one inversion for
//! the group.
//!
//! **Frobenius folding where `m = 3` uses it.**  On a folded table the
//! key reads only the abscissa, so a full-length innermost row is formed
//! with [`FastCurve::add_many_lazy`] and only the rests the presence
//! filter admits are completed, exactly as the `m = 3` arm does (a group
//! of short rows is added in full: there is no lazy pairwise addition).  The two
//! outer rows need their ordinates and are always formed in full.
//!
//! **Order.**  Rows are visited with `t` ascending, then `l ≤ t`
//! ascending, then `k ≤ l` ascending; within a rest the pairs come in
//! the table's own order.  In sorted mode every sorted witness is
//! reported exactly once, so the set reported equals the set of
//! non-decreasing 5-tuples exhaustive enumeration
//! ([`super::enumerate_decompose`]) ranges over.  The single
//! decomposition [`PairSumTable::decompose`] returns is the first one in
//! that row order, sorted — in general not the lexicographically first
//! tuple that enumeration returns, which is the same contract the
//! `m = 3` and `m = 4` arms have.

use super::{prefetch, BatchScratch, FastCurve, FastPoint, PairSumTable};

impl PairSumTable {
    /// The `m = 5` arm of [`Self::witnesses_fast_inner`]; see the module
    /// documentation.  `sorted` keeps only `j ≤ k`, so that each sorted
    /// witness comes back once; unsorted, a 5-tuple may come back up to
    /// as many times as it has splits with `k ≤ l ≤ t`.
    pub(super) fn witnesses_five(
        &self,
        target: FastPoint,
        sorted: bool,
        sink: &mut dyn FnMut(&[usize]) -> bool,
    ) {
        self.witnesses_five_grouped(target, sorted, ROW_GROUP, sink)
    }

    /// [`Self::witnesses_five`] with short rows grouped up to `row_group`
    /// rests (`1`: every row on its own).  The grouping changes only the
    /// batching, never which witnesses come back or in what order.
    fn witnesses_five_grouped(
        &self,
        target: FastPoint,
        sorted: bool,
        row_group: usize,
        sink: &mut dyn FnMut(&[usize]) -> bool,
    ) {
        let base = self.points.len();
        if base == 0 {
            return;
        }
        let curve: &FastCurve = &self.curve;
        let mut scratch = BatchScratch::default();
        // `R − P_t` for every `t`.
        let mut firsts = Vec::with_capacity(base);
        curve.add_many(target, &self.negated, &mut firsts, &mut scratch);
        let mut seconds = Vec::with_capacity(base);
        let mut group = RowGroup::default();
        for (t, &first) in firsts.iter().enumerate() {
            // `R − P_t − P_l` for every `l ≤ t`; `add_many` appends.
            seconds.clear();
            curve.add_many(first, &self.negated[..=t], &mut seconds, &mut scratch);
            // Rows `l` are gathered until they hold `row_group` rests
            // between them, and a group of several short rows shares one
            // inversion; see [`ROW_GROUP`].
            let mut l0 = 0;
            let mut width = 0;
            for l in 0..=t {
                width += l + 1;
                if width >= row_group || l == t {
                    if !self.scan_rows(
                        &seconds,
                        l0..l + 1,
                        t,
                        sorted,
                        &mut group,
                        &mut scratch,
                        sink,
                    ) {
                        return;
                    }
                    l0 = l + 1;
                    width = 0;
                }
            }
        }
    }

    /// Probe the rests `R − P_t − P_l − P_k`, `k ≤ l`, for every row `l`
    /// in `rows`, `seconds[l]` being `R − P_t − P_l`.  Returns `false`
    /// when the sink asked to stop.
    #[allow(clippy::too_many_arguments)]
    fn scan_rows(
        &self,
        seconds: &[FastPoint],
        rows: std::ops::Range<usize>,
        t: usize,
        sorted: bool,
        group: &mut RowGroup,
        scratch: &mut BatchScratch,
        sink: &mut dyn FnMut(&[usize]) -> bool,
    ) -> bool {
        const LOOKAHEAD: usize = 32;
        let curve = &self.curve;
        let RowGroup {
            ps,
            qs,
            rests,
            lambdas,
            keys,
            pairs,
        } = group;
        rests.clear();
        lambdas.clear();
        if rows.len() == 1 {
            // One row: one `add_many`, lazily on a folded table.
            let l = rows.start;
            let addends = &self.negated[..=l];
            if self.fold {
                curve.add_many_lazy(seconds[l], addends, rests, lambdas, scratch);
            } else {
                curve.add_many(seconds[l], addends, rests, scratch);
            }
        } else {
            ps.clear();
            qs.clear();
            for l in rows.clone() {
                ps.extend(std::iter::repeat_n(seconds[l], l + 1));
                qs.extend_from_slice(&self.negated[..=l]);
            }
            curve.add_pairwise(ps, qs, rests, scratch);
        }
        self.keys_of(rests, keys);
        for &key in keys.iter().take(LOOKAHEAD) {
            prefetch(&self.present[self.filter_word(key)]);
        }
        let (mut l, mut k) = (rows.start, 0);
        for (offset, rest) in rests.iter().enumerate() {
            if k > l {
                l += 1;
                k = 0;
            }
            let kk = k;
            k += 1;
            if let Some(&ahead) = keys.get(offset + LOOKAHEAD) {
                prefetch(&self.present[self.filter_word(ahead)]);
            }
            if !self.admitted(keys[offset]) {
                continue;
            }
            let rest = match lambdas.get(offset) {
                Some(&lambda) => curve.finish_lazy(seconds[l], *rest, lambda),
                None => *rest,
            };
            self.pairs_for_key(rest, keys[offset], pairs);
            for &(i, j) in pairs.iter() {
                if (!sorted || j as usize <= kk) && !sink(&[i as usize, j as usize, kk, l, t]) {
                    return false;
                }
            }
        }
        true
    }
}

/// Rests a batched group of short rows aims for.  Row `l` of a fixed
/// `t` holds only `l + 1` rests, so on a base of a few dozen points one
/// inversion per row is most of the scan (callgrind on
/// `pdp/spec_mitm_m5_n31`, row at a time: `Gf2::batch_inv` and
/// `Gf2::inv` 43 % of instructions, exclusive).  Consecutive short rows
/// are therefore added pairwise in one slice with one inversion; a row
/// as long as this on its own keeps its single `add_many`, lazily on a
/// folded table.  A group therefore holds fewer than `ROW_GROUP` rests
/// plus one row.
const ROW_GROUP: usize = 1024;

/// The scan's reusable buffers.
#[derive(Default)]
struct RowGroup {
    ps: Vec<FastPoint>,
    qs: Vec<FastPoint>,
    rests: Vec<FastPoint>,
    lambdas: Vec<u64>,
    keys: Vec<u64>,
    pairs: Vec<(u32, u32)>,
}

#[cfg(test)]
mod tests {
    use super::super::{
        build_frobenius_factor_base, build_frobenius_factor_base_from_divisor, enumerate_decompose,
        invariant_factors, point_neg, BinaryPoint, FrobeniusFactorBase, KoblitzCurve,
    };
    use super::*;
    use num_bigint::BigUint;
    use rand::rngs::StdRng;
    use rand::{Rng, SeedableRng};
    use std::collections::HashMap;

    /// Every sorted 5-tuple of base indices summing to `target`, by
    /// exhaustive search over `i ≤ j ≤ k ≤ l` and a lookup of the fifth
    /// — independent of the pair table, sorted lexicographically.
    fn all_sorted_witnesses(
        fc: &FastCurve,
        points: &[FastPoint],
        target: FastPoint,
    ) -> Vec<Vec<usize>> {
        let mut at: HashMap<u64, Vec<usize>> = HashMap::new();
        for (i, p) in points.iter().enumerate() {
            at.entry(p.pack()).or_default().push(i);
        }
        let neg: Vec<FastPoint> = points.iter().map(|&p| fc.neg(p)).collect();
        let n = points.len();
        let mut out = Vec::new();
        for i in 0..n {
            let r1 = fc.add(target, neg[i]);
            for j in i..n {
                let r2 = fc.add(r1, neg[j]);
                for k in j..n {
                    let r3 = fc.add(r2, neg[k]);
                    for l in k..n {
                        let r4 = fc.add(r3, neg[l]);
                        if let Some(ts) = at.get(&r4.pack()) {
                            for &t in ts.iter().filter(|&&t| t >= l) {
                                out.push(vec![i, j, k, l, t]);
                            }
                        }
                    }
                }
            }
        }
        out.sort_unstable();
        out
    }

    /// Every tier this base can be built in.
    fn tiers(kc: &KoblitzCurve, fb: &FrobeniusFactorBase) -> Vec<PairSumTable> {
        let budget = PairSumTable::DEFAULT_BYTE_BUDGET;
        let tables: Vec<PairSumTable> = [
            PairSumTable::build_full_within(kc, fb, budget),
            PairSumTable::build_compact_within(kc, fb, budget),
            PairSumTable::build_folded_within(kc, fb, budget),
        ]
        .into_iter()
        .flatten()
        .collect();
        assert!(
            tables.iter().any(|t| t.tier() == "full"),
            "the full tier always builds"
        );
        tables
    }

    /// Targets of every kind the oracle must answer: planted sums of
    /// five base points (with repeats and with `P + (−P)` cancellations),
    /// subgroup multiples (mostly refuted), base points, small sums, the
    /// point at infinity and the two-torsion point `(0, √b)`.
    fn targets(
        kc: &KoblitzCurve,
        fb: &FrobeniusFactorBase,
        seed: u64,
        planted: usize,
        random: usize,
    ) -> Vec<BinaryPoint> {
        let mut rng = StdRng::seed_from_u64(seed);
        let n = fb.points.len();
        let mut out = vec![
            BinaryPoint::Infinity,
            fb.points[0].clone(),
            fb.points[n - 1].clone(),
        ];
        out.push(kc.add(&fb.points[0], &fb.points[n / 2]));
        for _ in 0..planted {
            let mut idx: Vec<usize> = (0..5).map(|_| rng.gen_range(0..n)).collect();
            match rng.gen_range(0..4) {
                0 => idx[1] = idx[0],
                1 => {
                    idx[2] = idx[0];
                    idx[3] = idx[0];
                    idx[4] = idx[0];
                }
                _ => {}
            }
            let mut sum = idx
                .iter()
                .fold(BinaryPoint::Infinity, |s, &i| kc.add(&s, &fb.points[i]));
            if rng.gen_range(0..4) == 0 {
                // A planted cancellation: a sum of three base points is a
                // sum of five through `P + (−P)`, the base being
                // negation-closed.
                sum = idx[2..]
                    .iter()
                    .fold(BinaryPoint::Infinity, |s, &i| kc.add(&s, &fb.points[i]));
                debug_assert!(fb.points.contains(&point_neg(&fb.points[idx[0]])));
            }
            out.push(sum);
        }
        let r = kc.subgroup_order.to_u64_digits()[0].max(2);
        for _ in 0..random {
            out.push(kc.mul(kc.generator(), &BigUint::from(rng.gen_range(1..r))));
        }
        // The two-torsion point (0, √b) is on every curve here.
        if let Some(p) =
            super::super::points_with_x(&kc.curve, &crate::binary_ecc::F2mElement::zero(kc.n))
                .into_iter()
                .next()
        {
            out.push(p);
        }
        out
    }

    /// The differential check on one base: on every tier, the table's
    /// sorted witnesses are exactly the exhaustive search's, each once;
    /// `decompose` finds one exactly when `enumerate_decompose` (the
    /// generic oracle) does, and what it returns is one of them.
    fn agree_on(
        kc: &KoblitzCurve,
        fb: &FrobeniusFactorBase,
        seed: u64,
        planted: usize,
        random: usize,
    ) -> (usize, usize, Vec<&'static str>) {
        let index = fb.index_map();
        let tables = tiers(kc, fb);
        let names = tables.iter().map(|t| t.tier()).collect();
        let fc = tables[0].curve();
        let points: Vec<FastPoint> = fb.points.iter().map(|p| fc.lift(p)).collect();
        let (mut decomposed, mut refuted) = (0, 0);
        for target in targets(kc, fb, seed, planted, random) {
            let lifted = fc.lift(&target);
            let reference = all_sorted_witnesses(fc, &points, lifted);
            let generic = enumerate_decompose(kc, fb, &index, &target, 5);
            assert_eq!(
                generic.is_some(),
                !reference.is_empty(),
                "the brute force agrees with enumerate_decompose"
            );
            if let Some(g) = &generic {
                assert_eq!(
                    Some(g),
                    reference.first(),
                    "enumeration returns the lexicographically first witness"
                );
                decomposed += 1;
            } else {
                refuted += 1;
            }
            for table in &tables {
                let tier = table.tier();
                let mut seen = Vec::new();
                table.witnesses(kc, fb, &target, 5, &mut |w| {
                    assert!(
                        w.windows(2).all(|p| p[0] <= p[1]),
                        "{tier}: unsorted witness {w:?}"
                    );
                    seen.push(w.to_vec());
                    true
                });
                for row_group in [1usize, 3, 8, ROW_GROUP] {
                    let mut grouped = Vec::new();
                    table.witnesses_five_grouped(lifted, true, row_group, &mut |w| {
                        grouped.push(w.to_vec());
                        true
                    });
                    assert_eq!(
                        grouped, seen,
                        "{tier}: row group {row_group} changed the scan"
                    );
                }
                let reported = seen.len();
                seen.sort_unstable();
                seen.dedup();
                assert_eq!(seen.len(), reported, "{tier}: a witness reported twice");
                assert_eq!(
                    seen, reference,
                    "{tier}: witness set differs from exhaustive search"
                );

                let found = table.decompose(kc, fb, &target, 5);
                assert_eq!(
                    found.is_some(),
                    generic.is_some(),
                    "{tier}: decompose disagrees with enumerate_decompose"
                );
                if let Some(idxs) = &found {
                    assert!(
                        reference.binary_search(idxs).is_ok(),
                        "{tier}: {idxs:?} is not a witness"
                    );
                }
                // The first sorted witness in row order is what an early
                // stop sees: the least `(t, l, k)` among the reference.
                let mut first = None;
                table.witnesses(kc, fb, &target, 5, &mut |w| {
                    first = Some(w.to_vec());
                    false
                });
                let least = reference.iter().map(|w| (w[4], w[3], w[2])).min();
                assert_eq!(
                    first.as_ref().map(|w| (w[4], w[3], w[2])),
                    least,
                    "{tier}: row order"
                );
                // The fast unsorted path agrees on existence too.
                let fast = table.decompose_fast(lifted, 5);
                assert_eq!(fast.is_some(), generic.is_some(), "{tier}: decompose_fast");
            }
        }
        (decomposed, refuted, names)
    }

    /// Up to `limit` Frobenius-invariant bases of `kc` from subsets of
    /// its invariant factors, each of between 4 and `max` points.
    fn small_bases(kc: &KoblitzCurve, max: usize, limit: usize) -> Vec<FrobeniusFactorBase> {
        let k = invariant_factors(kc).len().min(8);
        let mut out = Vec::new();
        for mask in 1u32..1 << k {
            let idx: Vec<usize> = (0..k).filter(|&i| mask >> i & 1 == 1).collect();
            if let Some(fb) = build_frobenius_factor_base_from_divisor(kc, &idx) {
                if (4..=max).contains(&fb.points.len()) {
                    out.push(fb);
                }
            }
            if out.len() == limit {
                break;
            }
        }
        out
    }

    #[test]
    fn five_summand_witnesses_match_exhaustive_search_on_koblitz_bases() {
        let mut decomposed = 0;
        let mut refuted = 0;
        let mut seen_tiers = std::collections::HashSet::new();
        for (a, n) in [
            (0u8, 7u32),
            (1, 7),
            (0, 9),
            (1, 9),
            (0, 11),
            (1, 11),
            (0, 13),
        ] {
            let Some(kc) = KoblitzCurve::new(a, n) else {
                continue;
            };
            for (idx, fb) in small_bases(&kc, 40, 3).iter().enumerate() {
                let (d, r, names) =
                    agree_on(&kc, fb, 0x3535 ^ (u64::from(n) << 8) ^ idx as u64, 6, 6);
                decomposed += d;
                refuted += r;
                seen_tiers.extend(names);
            }
        }
        assert!(
            decomposed > 20,
            "too few decomposable targets exercised: {decomposed}"
        );
        for tier in ["full", "compact", "folded"] {
            assert!(
                seen_tiers.contains(tier),
                "the {tier} tier was never exercised"
            );
        }
        assert!(refuted > 5, "too few refuted targets exercised: {refuted}");
    }

    #[test]
    fn five_summand_witnesses_match_on_unions_and_inadmissible_bases() {
        // K_1/F_2^7 (cofactor 2): no base point lies in ⟨G⟩, so odd m
        // decomposes no subgroup target — the "no solution" edge — while
        // planted sums of five base points still decompose.
        let kc = KoblitzCurve::new(1, 7).unwrap();
        for divisor in [vec![1usize], vec![1, 2]] {
            let fb = build_frobenius_factor_base_from_divisor(&kc, &divisor).unwrap();
            assert!(!fb.m_can_decompose(&kc, 5));
            agree_on(&kc, &fb, 0x7007, 4, 8);
        }
        let kc = KoblitzCurve::new(0, 9).unwrap();
        let fb = build_frobenius_factor_base_from_divisor(&kc, &[0, 1]).unwrap();
        agree_on(&kc, &fb, 0x0909, 8, 4);
    }

    #[test]
    fn five_summand_witnesses_match_on_subfield_curves() {
        let mut checked = 0;
        for (k, n, a, b) in [(2u32, 6u32, 1u64, 1u64), (3, 9, 0, 3), (2, 10, 2, 3)] {
            let Some(kc) = KoblitzCurve::subfield(k, n, a, b) else {
                continue;
            };
            for fb in small_bases(&kc, 40, 3) {
                agree_on(&kc, &fb, 0x5f5f ^ u64::from(n), 4, 4);
                checked += 1;
            }
        }
        assert!(checked > 0, "no subfield base was exercised");
    }

    #[test]
    fn five_summand_scan_on_an_empty_base_reports_nothing() {
        let kc = KoblitzCurve::new(0, 9).unwrap();
        let fb = build_frobenius_factor_base(&kc, 0).unwrap();
        let table = PairSumTable::build_full(&kc, &fb).unwrap();
        // Same table, no summands: an empty scan, not a panic.
        let empty = PairSumTable {
            points: Vec::new(),
            negated: Vec::new(),
            ..table
        };
        let mut calls = 0;
        empty.witnesses_five(empty.curve().lift(kc.generator()), true, &mut |_| {
            calls += 1;
            true
        });
        assert_eq!(calls, 0);
    }
}
