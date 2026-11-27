use prime_field_auxiliary_ic::*;
use std::collections::BTreeSet;

fn reachable<const B: u32>(base: &FactorBase<B>, m: usize) -> BTreeSet<(u64, u64)> {
    fn walk<const B: u32>(
        base: &FactorBase<B>,
        m: usize,
        terms: &mut Vec<SignedTerm>,
        sum: Option<Point>,
        out: &mut BTreeSet<(u64, u64)>,
    ) {
        if m == 0 {
            if let Some(p) = sum {
                out.insert(p.coordinates());
            }
            return;
        }
        let c = base.curve();
        for (i, p) in base.representatives().iter().enumerate() {
            for negative in [false, true] {
                if terms.iter().any(|t| t.index == i && t.negative != negative) {
                    continue;
                }
                let p = if negative { c.negate(*p).unwrap() } else { *p };
                terms.push(SignedTerm { index: i, negative });
                walk(base, m - 1, terms, c.add(sum, Some(p)).unwrap(), out);
                terms.pop();
            }
        }
    }
    let mut out = BTreeSet::new();
    walk(base, m, &mut Vec::new(), None, &mut out);
    out
}

#[test]
fn indexed_pairs_match_full_signed_finite_domain_with_exceptional_sums() {
    for (a, b) in [(1, 0), (2, 14)] {
        let c = Curve::<5>::new(a, b).unwrap();
        let roots: Vec<u64> = (0..31)
            .filter(|x| c.lift_x(*x).unwrap().is_some())
            .take(4)
            .collect();
        let base = FactorBase::without_maps(c, &roots).unwrap();
        let index = PairIndex::new(&base, 100, 3).unwrap();
        assert_eq!(
            index.stats().constructed_pairs,
            (base.representatives().len() * base.representatives().len()) as u64
        );
        for m in 2..=4 {
            let truth = reachable(&base, m);
            let mut w = index.workspace();
            for x in 0..31 {
                if let Some(p) = c.lift_x(x).unwrap() {
                    for target in [p, c.negate(p).unwrap()] {
                        let found = index.decompose(m as u8, target, &mut w).unwrap();
                        assert_eq!(
                            found.is_some(),
                            truth.contains(&target.coordinates()),
                            "a={a} b={b} m={m} target={target:?}"
                        );
                        if let Some(row) = found {
                            let sum = row.summands().iter().fold(None, |acc, t| {
                                c.add(
                                    acc,
                                    Some(if t.negative {
                                        c.negate(base.representatives()[t.index]).unwrap()
                                    } else {
                                        base.representatives()[t.index]
                                    }),
                                )
                                .unwrap()
                            });
                            assert_eq!(sum, Some(target));
                        }
                    }
                }
            }
        }
    }
}

#[test]
fn bounded_memory_foreign_scratch_and_wrong_base_are_rejected() {
    let c = Curve::<7>::new(2, 51).unwrap();
    let base = FactorBase::without_maps(c, &[3, 6, 7, 8, 9, 10, 11, 12]).unwrap();
    assert!(matches!(
        PairIndex::new(&base, 0, 16),
        Err(Error::ResourceLimit(_))
    ));
    assert!(PairIndex::new(&base, 1000, 0).is_err());
    let a = PairIndex::new(&base, 1000, 16).unwrap();
    let b = PairIndex::new(&base, 1000, 16).unwrap();
    let mut scratch = a.workspace();
    assert!(b
        .decompose(4, c.point(3, 46).unwrap(), &mut scratch)
        .is_err());
    let other = FactorBase::without_maps(c, &[3]).unwrap();
    let prepared = PreparedSolver::new(&other, 109, c.point(3, 46).unwrap()).unwrap();
    assert!(prepared
        .solve_multi_indexed(4, c.point(6, 122).unwrap(), &Config::default(), &a)
        .is_err());
}

#[test]
fn indexed_end_to_end_recovers_every_nonzero_finite_control_target() {
    let c = Curve::<7>::new(2, 51).unwrap();
    let g = c.point(3, 46).unwrap();
    let roots: Vec<u64> = (0..127)
        .filter(|x| c.lift_x(*x).unwrap().is_some())
        .take(6)
        .collect();
    let base = FactorBase::without_maps(c, &roots).unwrap();
    let index = PairIndex::new(&base, 1000, 8).unwrap();
    let prepared = PreparedSolver::new(&base, 109, g).unwrap();
    for m in [2, 3, 4] {
        for scalar in 1..109 {
            let target = c.mul(Some(g), scalar).unwrap().unwrap();
            let cfg = Config {
                seed: 71,
                max_queries: 5000,
                walk_lanes: 8,
                ..Config::default()
            };
            let (outcome, _) = prepared
                .solve_multi_indexed(m, target, &cfg, &index)
                .unwrap();
            let MultiSolveOutcome::Solved { certificate, .. } = outcome else {
                panic!("finite control incomplete m={m},scalar={scalar}")
            };
            assert_eq!(certificate.scalar, scalar);
            verify_multi_certificate(&base, &certificate).unwrap();
            let mut forged = certificate.clone();
            forged.scalar = (forged.scalar + 1) % 109;
            assert!(verify_multi_certificate(&base, &forged).is_err());
        }
    }
}

#[test]
fn mersenne31_pair_witness_sign_cache_and_local_replay() {
    let c = Curve::<31>::new(2, 14).unwrap();
    let roots: Vec<_> = (0..100)
        .filter(|x| c.lift_x(*x).unwrap().is_some())
        .take(8)
        .collect();
    let base = FactorBase::without_maps(c, &roots).unwrap();
    let index = PairIndex::new(&base, 1000, 7).unwrap();
    for m in [3, 4] {
        let target = base
            .representatives()
            .iter()
            .take(m as usize)
            .fold(None, |a, p| c.add(a, Some(*p)).unwrap())
            .unwrap();
        let mut w = index.workspace();
        let first = index.decompose(m, target, &mut w).unwrap().unwrap();
        let second = index
            .decompose(m, c.negate(target).unwrap(), &mut w)
            .unwrap()
            .unwrap();
        assert_eq!(w.stats().cache_hits, 1);
        assert_eq!(first.summands().len(), second.summands().len());
        for (a, b) in first.summands().iter().zip(second.summands()) {
            assert_eq!(a.index, b.index);
            assert_ne!(a.negative, b.negative);
        }
    }
}
