//! Differential tests: every specialised affine route against the
//! explicit-point enumeration and the generic hull path.

use super::*;
use crate::binary_ecc::{BinaryCurve, BinaryPoint, F2mElement};
use crate::cryptanalysis::koblitz_index_calculus::{
    find_irreducible_sparse, invariant_factors, points_with_x, subspace_basis_for_factors,
};
use num_bigint::BigUint;
use num_traits::{One, Zero};
use rand::rngs::StdRng;
use rand::{Rng, SeedableRng};

fn generic_curve(n: u32, a: u64, b: u64) -> BinaryCurve {
    let irreducible = find_irreducible_sparse(n).unwrap();
    BinaryCurve {
        m: n,
        a: F2mElement::from_biguint(&BigUint::from(a), n),
        b: F2mElement::from_biguint(&BigUint::from(b), n),
        irreducible,
        generator: BinaryPoint::Infinity,
        order: BigUint::zero(),
        cofactor: BigUint::one(),
    }
}

fn gf_of(curve: &BinaryCurve) -> Gf2 {
    Gf2::new(&curve.irreducible)
}

fn word(gf: &Gf2, x: &F2mElement) -> u64 {
    gf.from_element(x)
}

fn random_independent(rng: &mut StdRng, n: u32, l: u32) -> Vec<u64> {
    let mask = if n == 64 { u64::MAX } else { (1u64 << n) - 1 };
    loop {
        let basis: Vec<u64> = (0..l).map(|_| rng.gen::<u64>() & mask).collect();
        if AffineSubspace::new(&basis, 0).is_some() {
            return basis;
        }
    }
}

fn add_all(curve: &BinaryCurve, points: &[BinaryPoint], idxs: &[usize]) -> BinaryPoint {
    let fc = FastCurve::new(curve).unwrap();
    let s = idxs
        .iter()
        .fold(FastPoint::INFINITY, |s, &i| fc.add(s, fc.lift(&points[i])));
    fc.lower(s)
}

/// A random affine point of the curve (any coset of the group).
fn random_curve_point(curve: &BinaryCurve, rng: &mut StdRng) -> BinaryPoint {
    let mask = (1u64 << curve.m) - 1;
    loop {
        let x = F2mElement::from_biguint(&BigUint::from(rng.gen::<u64>() & mask), curve.m);
        let ps = points_with_x(curve, &x);
        if let Some(p) = ps.into_iter().next() {
            return p;
        }
    }
}

/// Targets: planted sums of `m` base points (with repeats and an
/// opposite pair when possible), base points, random curve points, the
/// 2-torsion point and `O`.
fn targets(
    curve: &BinaryCurve,
    points: &[BinaryPoint],
    m: usize,
    rng: &mut StdRng,
    count: usize,
) -> Vec<BinaryPoint> {
    let mut out = Vec::new();
    let len = points.len();
    for k in 0..count {
        let idxs: Vec<usize> = match k % 4 {
            // A repeated summand.
            1 => {
                let i = rng.gen_range(0..len);
                let mut v = vec![i; 2];
                v.extend((2..m).map(|_| rng.gen_range(0..len)));
                v
            }
            _ => (0..m).map(|_| rng.gen_range(0..len)).collect(),
        };
        out.push(add_all(curve, points, &idxs[..m.min(idxs.len())]));
        out.push(random_curve_point(curve, rng));
    }
    out.push(points[rng.gen_range(0..len)].clone());
    out.extend(points_with_x(curve, &F2mElement::zero(curve.m)));
    out.push(BinaryPoint::Infinity);
    out
}

/// Check every route on one base and target set.
fn check_routes(
    curve: &BinaryCurve,
    coset: &AffineSubspace,
    points: &[BinaryPoint],
    dec: &AffineDecomposer,
    targets: &[BinaryPoint],
    m: usize,
    algebraic: bool,
    label: &str,
) -> (usize, usize) {
    let engine = SolverEngine::default();
    let (mut nonempty, mut total) = (0, 0);
    for t in targets {
        let reference = dec.decompositions(t, m, AffineRoute::Enumerate);
        assert!(reference.stats.complete);
        for d in &reference.decompositions {
            assert_eq!(add_all(curve, points, d), *t, "{label}: reference sum");
            assert!(d.windows(2).all(|w| w[0] <= w[1]));
        }
        total += 1;
        nonempty += usize::from(!reference.decompositions.is_empty());
        let specialised = match m {
            2 => Some(AffineRoute::S3Solve),
            3 => Some(AffineRoute::S4PairsAndSolve),
            _ => None,
        };
        if let Some(route) = specialised {
            let got = dec.decompositions(t, m, route);
            let auto = dec.decompositions(t, m, AffineRoute::Auto);
            assert!(got.stats.complete);
            assert_eq!(
                got.decompositions, reference.decompositions,
                "{label}: {route:?} m={m} t={t:?}"
            );
            assert_eq!(
                auto.decompositions, reference.decompositions,
                "{label}: Auto"
            );
            assert_eq!(
                dec.decompose(t, m, route).as_ref(),
                reference.first(),
                "{label}: canonical first"
            );
        }
        if algebraic {
            let representable: Vec<Vec<usize>> = reference
                .decompositions
                .iter()
                .filter(|d| chain_representable(curve, points, d))
                .cloned()
                .collect();
            if m <= 3 && !coset.is_linear() {
                assert_eq!(
                    representable, reference.decompositions,
                    "{label}: m ≤ 3 coset tuples are all representable"
                );
            }
            for route in [
                AffineRoute::Algebraic {
                    engine,
                    node_budget: usize::MAX,
                },
                AffineRoute::Sat {
                    conflict_budget: u64::MAX,
                },
                AffineRoute::GenericAlgebraic {
                    engine,
                    node_budget: usize::MAX,
                },
            ] {
                let got = dec.decompositions(t, m, route);
                assert!(got.stats.complete, "{label}: {route:?} incomplete");
                assert_eq!(
                    got.decompositions, representable,
                    "{label}: {route:?} m={m} t={t:?}"
                );
            }
        }
    }
    (nonempty, total)
}

#[test]
fn affine_subspace_is_canonical_and_exact() {
    let mut rng = StdRng::seed_from_u64(0xAFF1);
    for n in [4u32, 10, 17, 40, 62] {
        for l in [0u32, 1, 3] {
            let basis = random_independent(&mut rng, n, l);
            let shift = rng.gen::<u64>() & ((1u64 << n) - 1);
            let c = AffineSubspace::new(&basis, shift).unwrap();
            let elements = c.elements();
            let set: std::collections::HashSet<u64> = elements.iter().copied().collect();
            assert_eq!(set.len(), 1 << l);
            assert!(set.contains(&shift));
            for &e in &elements {
                assert!(c.contains(e));
                // Every representative names the same canonical coset.
                assert_eq!(AffineSubspace::new(&basis, e).unwrap(), c);
            }
            for _ in 0..200 {
                let x = rng.gen::<u64>() & ((1u64 << n) - 1);
                assert_eq!(c.contains(x), set.contains(&x));
            }
            assert_eq!(c.is_linear(), set.contains(&0));
            assert_eq!(c.hull_basis().is_none(), c.is_linear());
        }
    }
    // Dependent bases are refused.
    assert!(AffineSubspace::new(&[3, 5, 6], 1).is_none());
    assert!(AffineSubspace::new(&[0], 1).is_none());
}

#[test]
fn artin_schreier_and_affine_points_match_the_general_routines() {
    for n in [3u32, 4, 5, 6, 8, 9, 12] {
        let curve = generic_curve(n, (n % 2) as u64, 3);
        let gf = gf_of(&curve);
        let solver = ArtinSchreier::new(&gf);
        for a in 0..1u64 << n {
            let brute = (0..1u64 << n).find(|&z| gf.sqr(z) ^ z == a);
            match solver.solve(a) {
                Some(z) => assert_eq!(gf.sqr(z) ^ z, a),
                None => assert!(brute.is_none(), "n={n} a={a}"),
            }
            assert_eq!(brute.is_some(), !trace_bit(a, &gf));
        }
        let all = AffineSubspace::new(&(0..n).map(|i| 1u64 << i).collect::<Vec<_>>(), 0).unwrap();
        let mine: std::collections::BTreeSet<(u64, u64)> = affine_points(&curve, &all)
            .unwrap()
            .iter()
            .map(|p| {
                let q = FastCurve::new(&curve).unwrap().lift(p);
                (q.x, q.y)
            })
            .collect();
        let mut want = std::collections::BTreeSet::new();
        for x in 0..1u64 << n {
            for p in points_with_x(&curve, &F2mElement::from_biguint(&BigUint::from(x), n)) {
                let q = FastCurve::new(&curve).unwrap().lift(&p);
                want.insert((q.x, q.y));
            }
        }
        assert_eq!(mine, want, "n={n}");
    }
}

/// Invariant cosets of every invariant subspace, against a brute-force
/// scan of all cosets, on Koblitz curves and a subfield curve.
#[test]
fn frobenius_invariant_shifts_match_brute_force() {
    let mut curves = Vec::new();
    for (a, n) in [(0u8, 7u32), (1, 9), (0, 15), (1, 11)] {
        curves.push(KoblitzCurve::new(a, n).unwrap());
    }
    curves.extend(KoblitzCurve::subfield(2, 10, 1, 1));
    curves.extend(KoblitzCurve::subfield(2, 6, 0, 2));
    let mut checked = 0;
    let mut nontrivial = 0;
    for kc in &curves {
        let gf = Gf2::new(&kc.curve.irreducible);
        let factors = invariant_factors(kc).len();
        for idx in 0..factors {
            let Some((basis, _)) = subspace_basis_for_factors(kc, &[idx]) else {
                continue;
            };
            let words: Vec<u64> = basis.iter().map(|e| word(&gf, e)).collect();
            let v = AffineSubspace::new(&words, 0).unwrap();
            let got: Vec<u64> = frobenius_invariant_shifts(kc, &basis)
                .iter()
                .map(|e| word(&gf, e))
                .collect();
            let mut want = std::collections::BTreeSet::new();
            for x in 0..1u64 << kc.n {
                let c = v.reduce(x);
                if c == 0 {
                    continue;
                }
                let coset = AffineSubspace::new(&words, c).unwrap();
                let set: std::collections::HashSet<u64> = coset.elements().into_iter().collect();
                if coset
                    .elements()
                    .iter()
                    .all(|&e| set.contains(&gf.sqr_k(e, kc.k)))
                {
                    want.insert(c);
                }
            }
            assert_eq!(
                got,
                want.into_iter().collect::<Vec<_>>(),
                "{} factor {idx}",
                kc.label()
            );
            checked += 1;
            nontrivial += usize::from(!got.is_empty());
            for c in &got {
                let afb = build_affine_frobenius_factor_base(kc, &basis, &gf.to_element(*c));
                if let Some(afb) = afb {
                    assert_eq!(afb.fb.subspace.len(), 1 << basis.len());
                    assert!(afb.fb.points.iter().all(|p| match p {
                        BinaryPoint::Affine { x, .. } => afb.coset.contains(word(&gf, x)),
                        BinaryPoint::Infinity => false,
                    }));
                }
            }
            // A non-invariant shift and the trivial one are refused.
            assert!(
                build_affine_frobenius_factor_base(kc, &basis, &F2mElement::zero(kc.n)).is_none()
            );
        }
    }
    assert!(
        checked >= 8 && nontrivial >= 4,
        "checked {checked}, nontrivial {nontrivial}"
    );
}

/// The invariant affine bases of small Koblitz curves: every route against
/// the enumeration, the existing oracles on the hull-based base, and the
/// dispatch.
#[test]
fn koblitz_affine_routes_return_the_enumerated_decompositions() {
    let mut rng = StdRng::seed_from_u64(0x5EED_AFF1);
    let mut bases = 0;
    let mut nonempty = 0;
    let mut total = 0;
    for (a, n) in [
        (0u8, 7u32),
        (1, 7),
        (0, 9),
        (1, 9),
        (0, 11),
        (1, 13),
        (0, 15),
        (1, 15),
    ] {
        let Some(kc) = KoblitzCurve::new(a, n) else {
            continue;
        };
        let gf = Gf2::new(&kc.curve.irreducible);
        let factors = invariant_factors(&kc).len();
        let mut divisors: Vec<Vec<usize>> = (0..factors).map(|i| vec![i]).collect();
        divisors.extend((0..factors).flat_map(|i| (i + 1..factors).map(move |j| vec![i, j])));
        for divisor in divisors {
            let Some((basis, _)) = subspace_basis_for_factors(&kc, &divisor) else {
                continue;
            };
            let l = basis.len() as u32;
            if !(2..=7).contains(&l) {
                continue;
            }
            for shift in frobenius_invariant_shifts(&kc, &basis) {
                let Some(afb) = build_affine_frobenius_factor_base(&kc, &basis, &shift) else {
                    continue;
                };
                bases += 1;
                let dec = affine_koblitz_decomposer(&kc, &afb).unwrap();
                assert_eq!(dec.len(), afb.fb.points.len());
                let index_of = afb.fb.index_map();
                let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
                let pair = PairSumTable::build(&kc, &afb.fb).unwrap();
                let label = format!("{} l={l} c={:#x}", kc.label(), word(&gf, &shift));
                let mut ts = targets(&kc.curve, &afb.fb.points, 3, &mut rng, 4);
                // Subgroup targets, as relation collection draws them.
                for _ in 0..4 {
                    let k = BigUint::from(rng.gen::<u64>()) % &kc.subgroup_order;
                    ts.push(kc.mul(kc.generator(), &k));
                }
                for m in [2usize, 3, 4] {
                    if m == 4 && afb.fb.points.len() > 40 {
                        continue;
                    }
                    let vars = m * l as usize + (m - 2) * kc.n as usize;
                    let algebraic = m == 2 || vars <= 22;
                    let (ne, t) = check_routes(
                        &kc.curve,
                        &afb.coset,
                        &afb.fb.points,
                        &dec,
                        &ts,
                        m,
                        algebraic,
                        &label,
                    );
                    nonempty += ne;
                    total += t;
                    for target in &ts {
                        let all = dec.decompositions(target, m, AffineRoute::Enumerate);
                        // Point-based oracles take the affine base as it is.
                        let mut witnesses = Vec::new();
                        if !matches!(target, BinaryPoint::Infinity) {
                            pair.witnesses(&kc, &afb.fb, target, m, &mut |w| {
                                witnesses.push(w.to_vec());
                                true
                            });
                        }
                        witnesses.sort();
                        witnesses.dedup();
                        assert_eq!(witnesses, all.decompositions, "{label}: pair table m={m}");
                        // The existing enumeration returns the canonical one.
                        if !matches!(target, BinaryPoint::Infinity) {
                            assert_eq!(
                                enumerate_decompose(&kc, &afb.fb, &index_of, target, m).as_ref(),
                                all.first(),
                                "{label}: enumerate_decompose m={m}"
                            );
                        }
                        // Dispatch: specialised and generic enumeration agree.
                        if m <= 3 {
                            let spec = affine_koblitz_decompose(
                                &kc,
                                &afb,
                                &dec,
                                target,
                                m,
                                AffineDispatch::Specialised(AffineRoute::Auto),
                            );
                            assert_eq!(spec.as_ref(), all.first());
                            if !matches!(target, BinaryPoint::Infinity) {
                                let generic = affine_koblitz_decompose(
                                    &kc,
                                    &afb,
                                    &dec,
                                    target,
                                    m,
                                    AffineDispatch::Generic(DecompositionStrategy::Enumerate),
                                );
                                assert_eq!(generic, spec);
                            }
                        }
                        // The existing algebraic oracles on the hull base find
                        // a member of the set, and only fail when it is empty.
                        if m == 2 {
                            let g = groebner_decompose(
                                &kc,
                                &afb.fb,
                                &index_of,
                                &st,
                                target,
                                m,
                                SolverEngine::default(),
                                usize::MAX,
                            )
                            .0;
                            let s = sat_decompose(
                                &kc,
                                &afb.fb,
                                &index_of,
                                &st,
                                target,
                                m,
                                usize::MAX,
                                None,
                            )
                            .0;
                            for (name, got) in [("groebner", g), ("sat", s)] {
                                match got {
                                    Some(d) => {
                                        assert!(all.decompositions.contains(&d), "{label}: {name}")
                                    }
                                    None => assert!(
                                        all.decompositions.is_empty()
                                            || matches!(target, BinaryPoint::Infinity),
                                        "{label}: {name} missed a decomposition"
                                    ),
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    assert!(bases >= 6, "only {bases} affine bases exercised");
    assert!(
        nonempty * 5 >= total,
        "too few decomposable targets: {nonempty}/{total}"
    );
}

/// Random binary curves (odd and even `n`, `a ∈ {0, 1}`, random `b`),
/// random subspaces and shifts, every point over the coset.
#[test]
fn generic_binary_curve_affine_routes_return_the_enumerated_decompositions() {
    let mut rng = StdRng::seed_from_u64(0xB1A5_AFF1);
    let mut nonempty = 0;
    let mut total = 0;
    for (n, l, rounds) in [
        (6u32, 2u32, 3),
        (8, 3, 3),
        (10, 4, 2),
        (11, 4, 2),
        (12, 4, 2),
        (13, 5, 2),
    ] {
        for _ in 0..rounds {
            let mask = (1u64 << n) - 1;
            let curve = generic_curve(n, rng.gen_range(0..2), (rng.gen::<u64>() & mask).max(1));
            let basis = random_independent(&mut rng, n, l);
            let shift = rng.gen::<u64>() & mask;
            let coset = AffineSubspace::new(&basis, shift).unwrap();
            let points = affine_points(&curve, &coset).unwrap();
            if points.is_empty() {
                continue;
            }
            let dec = AffineDecomposer::new(&curve, &coset, &points).unwrap();
            let label = format!("n={n} l={l} c={shift:#x} b={:?}", curve.b);
            let ts = targets(&curve, &points, 3, &mut rng, 5);
            for m in [2usize, 3] {
                let algebraic = m == 2 || 3 * l + n <= 26;
                let (ne, t) =
                    check_routes(&curve, &coset, &points, &dec, &ts, m, algebraic, &label);
                nonempty += ne;
                total += t;
            }
        }
    }
    assert!(
        nonempty * 5 >= total,
        "too few decomposable targets: {nonempty}/{total}"
    );
}

/// A linear coset (`c ∈ V`) through the same decomposer: the base then
/// holds the 2-torsion point, and three copies of it are a decomposition
/// of itself that no chain ordering represents.
#[test]
fn linear_coset_and_unrepresentable_tuples() {
    let mut rng = StdRng::seed_from_u64(0x0717);
    for (n, l) in [(7u32, 3u32), (9, 3), (10, 3)] {
        let curve = generic_curve(n, 1, 1);
        let basis = random_independent(&mut rng, n, l);
        let coset = AffineSubspace::new(&basis, basis[0] ^ basis[1]).unwrap();
        assert!(coset.is_linear());
        let points = affine_points(&curve, &coset).unwrap();
        let dec = AffineDecomposer::new(&curve, &coset, &points).unwrap();
        let ts = targets(&curve, &points, 3, &mut rng, 4);
        for m in [2usize, 3] {
            check_routes(
                &curve,
                &coset,
                &points,
                &dec,
                &ts,
                m,
                true,
                &format!("linear n={n}"),
            );
        }
        let t_idx = points
            .iter()
            .position(|p| matches!(p, BinaryPoint::Affine { x, .. } if x.is_zero()))
            .unwrap();
        let triple = vec![t_idx; 3];
        assert!(!chain_representable(&curve, &points, &triple));
        let t = points[t_idx].clone();
        let reference = dec.decompositions(&t, 3, AffineRoute::Enumerate);
        assert!(reference.decompositions.contains(&triple));
        assert!(dec
            .decompositions(&t, 3, AffineRoute::S4PairsAndSolve)
            .decompositions
            .contains(&triple));
        let algebraic = dec.decompositions(
            &t,
            3,
            AffineRoute::Algebraic {
                engine: SolverEngine::default(),
                node_budget: usize::MAX,
            },
        );
        assert!(!algebraic.decompositions.contains(&triple));
    }
}

/// Boundary fields: the smallest and the largest single-word degrees,
/// `O` and the misuse cases.
#[test]
fn boundary_fields_and_degenerate_inputs() {
    let mut rng = StdRng::seed_from_u64(0xB0D1);
    for (n, l) in [(3u32, 1u32), (4, 2), (61, 3), (62, 3)] {
        let mask = (1u64 << n) - 1;
        let curve = generic_curve(n, 1, (rng.gen::<u64>() & mask).max(1));
        let basis = random_independent(&mut rng, n, l);
        let coset = AffineSubspace::new(&basis, rng.gen::<u64>() & mask).unwrap();
        let points = affine_points(&curve, &coset).unwrap();
        if points.is_empty() {
            continue;
        }
        let dec = AffineDecomposer::new(&curve, &coset, &points).unwrap();
        let ts = targets(&curve, &points, 2, &mut rng, 3);
        check_routes(
            &curve,
            &coset,
            &points,
            &dec,
            &ts,
            2,
            n <= 4,
            &format!("n={n}"),
        );
        check_routes(
            &curve,
            &coset,
            &points,
            &dec,
            &ts,
            3,
            false,
            &format!("n={n}"),
        );
        for route in [
            AffineRoute::Auto,
            AffineRoute::S3Solve,
            AffineRoute::S4PairsAndSolve,
            AffineRoute::Enumerate,
        ] {
            let r = dec.decompositions(&BinaryPoint::Infinity, 2, route);
            assert!(r.decompositions.is_empty());
        }
        // A route used off its `m` reports itself incomplete.
        let p = &points[0];
        assert!(
            !dec.decompositions(p, 3, AffineRoute::S3Solve)
                .stats
                .complete
        );
        assert!(
            !dec.decompositions(p, 2, AffineRoute::S4PairsAndSolve)
                .stats
                .complete
        );
        // m = 1: membership.
        assert_eq!(dec.decompose(p, 1, AffineRoute::Enumerate), Some(vec![0]));
    }
    // Points off the coset, repeated points and O are refused.
    let curve = generic_curve(9, 0, 5);
    let coset = AffineSubspace::new(&[1, 2, 4], 8).unwrap();
    let points = affine_points(&curve, &coset).unwrap();
    let mut dup = points.clone();
    dup.push(points[0].clone());
    assert!(AffineDecomposer::new(&curve, &coset, &dup).is_none());
    let mut with_o = points.clone();
    with_o.push(BinaryPoint::Infinity);
    assert!(AffineDecomposer::new(&curve, &coset, &with_o).is_none());
    let other = AffineSubspace::new(&[1, 2, 4], 16).unwrap();
    assert!(AffineDecomposer::new(&curve, &other, &points).is_none());
}

/// The affine descent and the hull descent share their equations up to
/// the substitution `t_{i,ℓ} = 1`: a root of one is a root of the other.
#[test]
fn affine_system_is_the_hull_system_at_shift_one() {
    let mut rng = StdRng::seed_from_u64(0x5157);
    for (n, l) in [(9u32, 3u32), (11, 4), (13, 5)] {
        let curve = generic_curve(n, 1, 1);
        let gf = gf_of(&curve);
        let basis = random_independent(&mut rng, n, l);
        let coset = AffineSubspace::new(&basis, rng.gen::<u64>() & ((1u64 << n) - 1)).unwrap();
        if coset.is_linear() {
            continue;
        }
        let st = FieldStructure::new(n, &curve.irreducible);
        let basis_el: Vec<F2mElement> = basis.iter().map(|&w| gf.to_element(w)).collect();
        let hull_el: Vec<F2mElement> = coset
            .hull_basis()
            .unwrap()
            .iter()
            .map(|&w| gf.to_element(w))
            .collect();
        let xr = gf.to_element(rng.gen::<u64>() & ((1u64 << n) - 1));
        let aff = build_affine_decomposition_system(
            &basis_el,
            &gf.to_element(coset.shift()),
            &xr,
            &curve.b,
            2,
            &st,
        )
        .unwrap();
        let hull = build_decomposition_system(&hull_el, &xr, &curve.b, 2, &st).unwrap();
        assert_eq!(aff.n_vars, 2 * l as usize);
        assert_eq!(hull.n_vars, 2 * (l as usize + 1));
        for root in 0..1u64 << (2 * l) {
            let lo = root & ((1 << l) - 1);
            let hi = root >> l;
            let hroot = lo | (1 << l) | (hi << (l + 1)) | (1 << (2 * l + 1));
            let a_ok = aff.equations.iter().all(|e| e.eval(root) == 0);
            let h_ok = hull.equations.iter().all(|e| e.eval(hroot) == 0);
            assert_eq!(a_ok, h_ok, "n={n} root={root:#x}");
            assert_eq!(
                affine_summand_word(&coset, l as usize, root, 1),
                gf.from_element(&hull.summand_x(&hull_el, hroot, 1, n))
            );
        }
    }
}

/// Second, independent stress seed for the cheap specialised routes
/// (`S3Solve`, `S4PairsAndSolve`, `Auto`) against the enumerated reference:
/// many more random curves, subspaces of every dimension from 0, shifts
/// inside and outside `V`, and `n` up to 16.
#[test]
fn specialised_routes_stress_against_enumeration() {
    let mut rng = StdRng::seed_from_u64(0x57E5_AFF2);
    let (mut nonempty, mut total) = (0, 0);
    for n in 4u32..=16 {
        for l in 0..=n.min(5) {
            for _ in 0..3 {
                let mask = (1u64 << n) - 1;
                let curve = generic_curve(n, rng.gen_range(0..2), (rng.gen::<u64>() & mask).max(1));
                let basis = random_independent(&mut rng, n, l);
                let shift = if rng.gen_bool(0.2) && !basis.is_empty() {
                    basis[0]
                } else {
                    rng.gen::<u64>() & mask
                };
                let coset = AffineSubspace::new(&basis, shift).unwrap();
                let points = affine_points(&curve, &coset).unwrap();
                if points.is_empty() {
                    continue;
                }
                let dec = AffineDecomposer::new(&curve, &coset, &points).unwrap();
                let label = format!("stress n={n} l={l} c={shift:#x}");
                let ts = targets(&curve, &points, 3, &mut rng, 4);
                for m in [2usize, 3] {
                    let (ne, t) =
                        check_routes(&curve, &coset, &points, &dec, &ts, m, false, &label);
                    nonempty += ne;
                    total += t;
                }
            }
        }
    }
    assert!(total > 300, "stress covered too few targets: {total}");
    assert!(
        nonempty * 5 >= total,
        "too few decomposable targets: {nonempty}/{total}"
    );
}

/// Adversarial-review differential tests (round 2 reviewer): inputs the
/// implementer's tests do not use — exhaustive tiny fields, a uniformly
/// random `a` (both trace classes at every `n`), shuffled and partial
/// (subset) point lists, empty and zero-dimensional bases, `n` near the
/// single-word limit, and the generic Koblitz dispatch at `m = 3`.
mod review {
    use super::*;

    fn all_points(curve: &BinaryCurve) -> Vec<BinaryPoint> {
        let mut out = vec![BinaryPoint::Infinity];
        for x in 0..1u64 << curve.m {
            let xe = F2mElement::from_biguint(&BigUint::from(x), curve.m);
            out.extend(points_with_x(curve, &xe));
        }
        out
    }

    /// Specialised routes vs the enumerated reference on every target.
    fn check_cheap(
        dec: &AffineDecomposer,
        points: &[BinaryPoint],
        curve: &BinaryCurve,
        targets: &[BinaryPoint],
        label: &str,
    ) -> (usize, usize) {
        let (mut ne, mut tot) = (0, 0);
        for t in targets {
            for m in [2usize, 3] {
                let reference = dec.decompositions(t, m, AffineRoute::Enumerate);
                assert!(reference.stats.complete);
                for d in &reference.decompositions {
                    assert_eq!(add_all(curve, points, d), *t, "{label}: ref sum");
                }
                let route = if m == 2 {
                    AffineRoute::S3Solve
                } else {
                    AffineRoute::S4PairsAndSolve
                };
                for r in [route, AffineRoute::Auto] {
                    let got = dec.decompositions(t, m, r);
                    assert!(got.stats.complete, "{label}: incomplete");
                    assert_eq!(
                        got.decompositions, reference.decompositions,
                        "{label}: {r:?} m={m} t={t:?}"
                    );
                }
                tot += 1;
                ne += usize::from(!reference.decompositions.is_empty());
            }
        }
        (ne, tot)
    }

    fn rand_subset(
        points: &[BinaryPoint],
        rng: &mut StdRng,
        keep: f64,
        shuffle: bool,
    ) -> Vec<BinaryPoint> {
        let mut v: Vec<BinaryPoint> = points
            .iter()
            .filter(|_| rng.gen_bool(keep))
            .cloned()
            .collect();
        if v.is_empty() {
            v.push(points[0].clone());
        }
        if shuffle {
            for i in (1..v.len()).rev() {
                v.swap(i, rng.gen_range(0..=i));
            }
        }
        v
    }

    /// Every curve `(a, b ≠ 0)` over `GF(2^n)`, `n = 2..=4`, a few
    /// subspaces per dimension, **every** shift, **every** curve point
    /// and `O` as target, `m = 2, 3`: cheap routes against enumeration
    /// (full point lists), plus the three algebraic routes on a thinned
    /// subset of the configurations.
    #[test]
    fn exhaustive_tiny_fields_all_curves_all_shifts_all_targets() {
        let mut rng = StdRng::seed_from_u64(0xEE71_0001);
        let (mut ne, mut tot, mut cfgs, mut alg_cfgs) = (0, 0, 0usize, 0usize);
        for n in 2u32..=4 {
            for a in 0..1u64 << n {
                for b in 1..1u64 << n {
                    let curve = generic_curve(n, a, b);
                    let targets = all_points(&curve);
                    for l in 0..=n.min(3) {
                        for _ in 0..2 {
                            let basis = random_independent(&mut rng, n, l);
                            for shift in 0..1u64 << n {
                                let coset = AffineSubspace::new(&basis, shift).unwrap();
                                let points = affine_points(&curve, &coset).unwrap();
                                if points.is_empty() {
                                    continue;
                                }
                                let dec = AffineDecomposer::new(&curve, &coset, &points)
                                    .expect("decomposer");
                                cfgs += 1;
                                let label = format!(
                                    "tiny n={n} a={a:#x} b={b:#x} basis={basis:?} c={shift:#x}"
                                );
                                let (x, y) = check_cheap(&dec, &points, &curve, &targets, &label);
                                ne += x;
                                tot += y;
                                if cfgs % 23 == 0 {
                                    alg_cfgs += 1;
                                    for m in [2usize, 3] {
                                        check_routes(
                                            &curve, &coset, &points, &dec, &targets, m, true,
                                            &label,
                                        );
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        assert!(cfgs > 5000 && alg_cfgs > 200, "cfgs={cfgs} alg={alg_cfgs}");
        assert!(ne * 5 >= tot, "too few decomposable targets {ne}/{tot}");
    }

    /// Uniformly random `a`, `n = 5..=20`, dimensions `0..=6`, shifts in
    /// and out of `V`, shuffled partial point lists (so `±P` are often
    /// split) and planted/base/2-torsion/`O` targets.
    #[test]
    fn random_a_shuffled_subset_bases_match_enumeration() {
        let mut rng = StdRng::seed_from_u64(0xEE71_0002);
        let (mut ne, mut tot) = (0, 0);
        for n in 5u32..=20 {
            for l in 0..=n.min(6) {
                for rep in 0..3 {
                    let mask = (1u64 << n) - 1;
                    let curve =
                        generic_curve(n, rng.gen::<u64>() & mask, (rng.gen::<u64>() & mask).max(1));
                    let basis = random_independent(&mut rng, n, l);
                    let shift = if rep == 2 && l > 0 {
                        basis[0] ^ basis[l as usize - 1]
                    } else {
                        rng.gen::<u64>() & mask
                    };
                    let coset = AffineSubspace::new(&basis, shift).unwrap();
                    let full = affine_points(&curve, &coset).unwrap();
                    if full.is_empty() {
                        continue;
                    }
                    for (keep, shuffle) in [(1.0, true), (0.6, true), (0.3, false)] {
                        let points = rand_subset(&full, &mut rng, keep, shuffle);
                        let dec = AffineDecomposer::new(&curve, &coset, &points).unwrap();
                        let ts = targets(&curve, &points, 3, &mut rng, 4);
                        let label = format!("rand n={n} l={l} keep={keep} c={shift:#x}");
                        let (x, y) = check_cheap(&dec, &points, &curve, &ts, &label);
                        ne += x;
                        tot += y;
                    }
                }
            }
        }
        assert!(tot > 1500, "{tot}");
        assert!(ne * 6 >= tot, "too few decomposable targets {ne}/{tot}");
    }

    /// Algebraic / SAT / hull routes on small random-`a` fields with
    /// partial shuffled point lists: they must equal the chain-
    /// representable part of the enumerated reference.
    #[test]
    fn algebraic_and_sat_routes_on_subset_bases_random_a() {
        let mut rng = StdRng::seed_from_u64(0xEE71_0003);
        for n in 5u32..=9 {
            for l in 0..=3u32.min(n) {
                for rep in 0..2 {
                    let mask = (1u64 << n) - 1;
                    let curve =
                        generic_curve(n, rng.gen::<u64>() & mask, (rng.gen::<u64>() & mask).max(1));
                    let basis = random_independent(&mut rng, n, l);
                    let shift = rng.gen::<u64>() & mask;
                    let coset = AffineSubspace::new(&basis, shift).unwrap();
                    let full = affine_points(&curve, &coset).unwrap();
                    if full.is_empty() {
                        continue;
                    }
                    let points =
                        rand_subset(&full, &mut rng, if rep == 0 { 1.0 } else { 0.5 }, true);
                    let dec = AffineDecomposer::new(&curve, &coset, &points).unwrap();
                    let ts = targets(&curve, &points, 3, &mut rng, 3);
                    let label = format!("alg n={n} l={l} c={shift:#x}");
                    check_routes(&curve, &coset, &points, &dec, &ts, 2, true, &label);
                    if 3 * l + n <= 22 {
                        check_routes(&curve, &coset, &points, &dec, &ts, 3, true, &label);
                    }
                    // m = 4 (Auto resolves to the algebraic chain): the
                    // chain-representable subset of the reference.
                    if 4 * l + 2 * n <= 24 && points.len() <= 24 {
                        for t in &ts {
                            let reference = dec.decompositions(t, 4, AffineRoute::Enumerate);
                            let rep4: Vec<_> = reference
                                .decompositions
                                .iter()
                                .filter(|d| chain_representable(&curve, &points, d))
                                .cloned()
                                .collect();
                            let got = dec.decompositions(t, 4, AffineRoute::Auto);
                            assert!(got.stats.complete);
                            assert_eq!(got.decompositions, rep4, "{label}: m=4 Auto");
                        }
                    }
                }
            }
        }
    }

    /// Fields near the single-word limit, odd and even `n`, both trace
    /// classes of `a`, cheap routes only.
    #[test]
    fn large_n_random_a_cheap_routes() {
        let mut rng = StdRng::seed_from_u64(0xEE71_0004);
        let (mut ne, mut tot) = (0, 0);
        for n in [30u32, 31, 32, 33, 47, 53, 58, 59, 60, 61, 62] {
            for l in [1u32, 2, 3, 4] {
                for _ in 0..2 {
                    let mask = (1u64 << n) - 1;
                    let curve =
                        generic_curve(n, rng.gen::<u64>() & mask, (rng.gen::<u64>() & mask).max(1));
                    let basis = random_independent(&mut rng, n, l);
                    let coset = AffineSubspace::new(&basis, rng.gen::<u64>() & mask).unwrap();
                    let points = affine_points(&curve, &coset).unwrap();
                    if points.is_empty() {
                        continue;
                    }
                    let dec = AffineDecomposer::new(&curve, &coset, &points).unwrap();
                    let ts = targets(&curve, &points, 3, &mut rng, 4);
                    let (x, y) =
                        check_cheap(&dec, &points, &curve, &ts, &format!("big n={n} l={l}"));
                    ne += x;
                    tot += y;
                }
            }
        }
        assert!(ne * 6 >= tot, "too few decomposable targets {ne}/{tot}");
        // Beyond the single-word range everything refuses cleanly.
        let c63 = BinaryCurve {
            m: 63,
            ..generic_curve(62, 1, 1)
        };
        assert!(affine_points(&c63, &AffineSubspace::new(&[1], 2).unwrap()).is_none());
    }

    /// Empty point lists, zero-dimensional cosets and misuse: every route
    /// returns cleanly (no panic) and agrees with the reference.
    #[test]
    fn empty_and_zero_dimensional_bases_every_route() {
        let mut rng = StdRng::seed_from_u64(0xEE71_0005);
        let engine = SolverEngine::default();
        let routes = [
            AffineRoute::Auto,
            AffineRoute::S3Solve,
            AffineRoute::S4PairsAndSolve,
            AffineRoute::Enumerate,
            AffineRoute::Algebraic {
                engine,
                node_budget: usize::MAX,
            },
            AffineRoute::Sat {
                conflict_budget: u64::MAX,
            },
            AffineRoute::GenericAlgebraic {
                engine,
                node_budget: usize::MAX,
            },
        ];
        for n in [3u32, 5, 8, 13] {
            let mask = (1u64 << n) - 1;
            let curve = generic_curve(n, rng.gen::<u64>() & mask, (rng.gen::<u64>() & mask).max(1));
            let ts = all_points(&curve);
            // Empty base on a coset.
            let coset = AffineSubspace::new(&[1, 2], 4).unwrap();
            let dec = AffineDecomposer::new(&curve, &coset, &[]).unwrap();
            assert!(dec.is_empty());
            for t in ts.iter().take(12) {
                for m in 0..=4usize {
                    for r in routes {
                        let got = dec.decompositions(t, m, r);
                        assert!(
                            got.decompositions.is_empty(),
                            "empty base n={n} m={m} {r:?}"
                        );
                    }
                }
            }
            // Zero-dimensional coset {c}: at most one abscissa.
            for shift in [0u64, 1, 5 & mask, mask] {
                let coset = AffineSubspace::new(&[], shift).unwrap();
                let pts = affine_points(&curve, &coset).unwrap();
                if pts.is_empty() {
                    continue;
                }
                let dec = AffineDecomposer::new(&curve, &coset, &pts).unwrap();
                for t in &ts {
                    for m in 2..=3usize {
                        let reference = dec.decompositions(t, m, AffineRoute::Enumerate);
                        let rep: Vec<_> = reference
                            .decompositions
                            .iter()
                            .filter(|d| chain_representable(&curve, &pts, d))
                            .cloned()
                            .collect();
                        for r in routes {
                            // A route used off its `m` is documented to
                            // return nothing, incomplete.
                            if matches!(
                                (r, m),
                                (AffineRoute::S3Solve, 3) | (AffineRoute::S4PairsAndSolve, 2)
                            ) {
                                let off = dec.decompositions(t, m, r);
                                assert!(off.decompositions.is_empty());
                                // `O` is refused before the route is looked at.
                                assert_eq!(off.stats.complete, matches!(t, BinaryPoint::Infinity));
                                continue;
                            }
                            let got = dec.decompositions(t, m, r);
                            let want = match r {
                                AffineRoute::Algebraic { .. }
                                | AffineRoute::Sat { .. }
                                | AffineRoute::GenericAlgebraic { .. } => &rep,
                                _ => &reference.decompositions,
                            };
                            assert_eq!(
                                &got.decompositions, want,
                                "dim0 n={n} c={shift:#x} m={m} {r:?} t={t:?}"
                            );
                        }
                    }
                }
            }
        }
    }

    /// Generic Koblitz dispatch at `m = 3` on every small affine base
    /// that fits the chained system: the existing hull-based Gröbner /
    /// SAT / Crossbred / pair-table entry points return a member of the
    /// specialised set, and `None` only when it is empty.
    #[test]
    fn koblitz_generic_dispatch_m3_returns_members_of_the_specialised_set() {
        let mut rng = StdRng::seed_from_u64(0xEE71_0006);
        let mut bases = 0;
        for (a, n) in [(0u8, 7u32), (1, 7), (0, 9), (1, 9), (1, 5), (0, 5)] {
            let Some(kc) = KoblitzCurve::new(a, n) else {
                continue;
            };
            let factors = invariant_factors(&kc).len();
            let mut divisors: Vec<Vec<usize>> = (0..factors).map(|i| vec![i]).collect();
            divisors.extend((0..factors).flat_map(|i| (i + 1..factors).map(move |j| vec![i, j])));
            for divisor in divisors {
                let Some((basis, _)) = subspace_basis_for_factors(&kc, &divisor) else {
                    continue;
                };
                let l = basis.len();
                if !(1..=3).contains(&l) {
                    continue;
                }
                for shift in frobenius_invariant_shifts(&kc, &basis) {
                    let Some(afb) = build_affine_frobenius_factor_base(&kc, &basis, &shift) else {
                        continue;
                    };
                    bases += 1;
                    let dec = affine_koblitz_decomposer(&kc, &afb).unwrap();
                    let mut ts = targets(&kc.curve, &afb.fb.points, 3, &mut rng, 4);
                    for _ in 0..3 {
                        let k = BigUint::from(rng.gen::<u64>()) % &kc.subgroup_order;
                        ts.push(kc.mul(kc.generator(), &k));
                    }
                    for t in ts.iter().filter(|t| !matches!(t, BinaryPoint::Infinity)) {
                        for m in [2usize, 3] {
                            let all = dec.decompositions(t, m, AffineRoute::Enumerate);
                            for strat in [
                                DecompositionStrategy::Groebner,
                                DecompositionStrategy::Sat,
                                DecompositionStrategy::Crossbred,
                                DecompositionStrategy::PairTable,
                                DecompositionStrategy::Enumerate,
                            ] {
                                if m == 3 && 3 * l + n as usize > 26 {
                                    continue;
                                }
                                let got = affine_koblitz_decompose(
                                    &kc,
                                    &afb,
                                    &dec,
                                    t,
                                    m,
                                    AffineDispatch::Generic(strat),
                                );
                                match got {
                                    Some(d) => assert!(
                                        all.decompositions.contains(&d),
                                        "{} l={l} m={m} {strat:?}: {d:?} not in set",
                                        kc.label()
                                    ),
                                    None => assert!(
                                        all.decompositions.is_empty(),
                                        "{} l={l} m={m} {strat:?} missed {:?}",
                                        kc.label(),
                                        all.decompositions
                                    ),
                                }
                            }
                            // Specialised canonical == enumerate_decompose.
                            let spec = affine_koblitz_decompose(
                                &kc,
                                &afb,
                                &dec,
                                t,
                                m,
                                AffineDispatch::Specialised(AffineRoute::Auto),
                            );
                            assert_eq!(spec.as_ref(), all.first());
                        }
                    }
                }
            }
        }
        assert!(bases >= 3, "only {bases} bases");
    }
}
