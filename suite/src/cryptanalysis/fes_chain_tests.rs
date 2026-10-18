//! Differential tests: the specialised Gray-code chain search against the
//! generic Weil-descended system (`build_decomposition_system`), solved
//! by exhaustive evaluation of its own equations, and against the
//! generic decomposition oracles.

use super::*;
use crate::cryptanalysis::koblitz_groebner::{build_decomposition_system, DecompositionSystem};
use crate::cryptanalysis::koblitz_index_calculus::{
    build_frobenius_factor_base, find_irreducible_sparse, point_key, sat_decompose,
};
use rand::{rngs::StdRng, Rng, SeedableRng};
use std::collections::BTreeSet;

fn elem(v: u64, n: u32) -> F2mElement {
    F2mElement::from_biguint(&BigUint::from(v), n)
}

/// Every root of the generic system, by exhaustive evaluation of its
/// equations, block by block: `(x₀, x₁, u₀)` against the first link's `n`
/// equations, then `(x_{k+1}, u_k)` against link `k + 1`'s, then `x_{m−1}`
/// against the last link's.  Each link's equations only involve the
/// blocks enumerated so far (asserted), so this is plain exhaustive
/// search over the generic system, pruned link by link.
fn generic_roots(sys: &DecompositionSystem, n: usize) -> Vec<u64> {
    let (m, ell) = (sys.m, sys.ell);
    assert_eq!(sys.equations.len(), (m - 1) * n);
    let xmask = |i: usize| ((1u64 << ell) - 1) << (i * ell);
    let umask = |k: usize| ((1u64 << n) - 1) << (m * ell + k * n);
    // Blocks and the variables visible after each.
    let mut blocks = vec![xmask(0) | xmask(1) | umask(0)];
    for k in 1..m - 2 {
        blocks.push(xmask(k + 1) | umask(k));
    }
    blocks.push(xmask(m - 1));
    let mut seen = 0u64;
    for (k, &blk) in blocks.iter().enumerate() {
        seen |= blk;
        for e in &sys.equations[k * n..(k + 1) * n] {
            for t in &e.terms {
                assert_eq!(t.mask & !seen, 0, "link {k} uses a later block");
            }
        }
    }
    let mut out = Vec::new();
    fn rec(
        sys: &DecompositionSystem,
        blocks: &[u64],
        n: usize,
        k: usize,
        point: u64,
        out: &mut Vec<u64>,
    ) {
        if k == blocks.len() {
            out.push(point);
            return;
        }
        let blk = blocks[k];
        let eqs = &sys.equations[k * n..(k + 1) * n];
        // Enumerate the sub-masks of `blk`.
        let mut sub = 0u64;
        loop {
            let p = point | sub;
            if eqs.iter().all(|e| e.eval(p) == 0) {
                rec(sys, blocks, n, k + 1, p, out);
            }
            if sub == blk {
                break;
            }
            sub = (sub.wrapping_sub(blk)) & blk;
        }
    }
    rec(sys, &blocks, n, 0, 0, &mut out);
    out
}

fn unpack(root: u64, m: usize, ell: usize, n: usize) -> ChainRoot {
    ChainRoot {
        coords: (0..m)
            .map(|i| (root >> (i * ell)) & ((1u64 << ell) - 1))
            .collect(),
        inter: (0..m - 2)
            .map(|k| (root >> (m * ell + k * n)) & ((1u64 << n) - 1))
            .collect(),
    }
}

/// The documented enumeration key `(r₀, r₁, u₀, r₂, u₁, …, c_{m−1})`.
fn order_key(r: &ChainRoot) -> Vec<u64> {
    let m = r.coords.len();
    let mut key = vec![gray_rank(r.coords[0])];
    for k in 1..m - 1 {
        key.push(gray_rank(r.coords[k]));
        key.push(r.inter[k - 1]);
    }
    key.push(r.coords[m - 1]);
    key
}

fn sorted_ranks(r: &ChainRoot) -> bool {
    r.coords
        .windows(2)
        .all(|p| gray_rank(p[0]) <= gray_rank(p[1]))
}

/// A random instance: irreducible of degree `n`, `ell` independent basis
/// elements, non-zero `b`.
fn random_instance(
    rng: &mut StdRng,
    n: u32,
    ell: usize,
) -> (IrreduciblePoly, Vec<F2mElement>, u64) {
    let irr = find_irreducible_sparse(n).expect("irreducible");
    let mask = (1u64 << n) - 1;
    loop {
        let basis: Vec<u64> = (0..ell).map(|_| rng.gen::<u64>() & mask).collect();
        let (_, rank) = preimage_map(&basis, n as usize);
        if rank == ell {
            let b = loop {
                let b = rng.gen::<u64>() & mask;
                if b != 0 {
                    break b;
                }
            };
            return (irr, basis.iter().map(|&v| elem(v, n)).collect(), b);
        }
    }
}

fn assert_leaves(visited: u64, bound: u128, m: usize) {
    if m == 3 {
        assert_eq!(u128::from(visited), bound);
    } else {
        // Each earlier intermediate link forks into at most two roots.
        let bound = bound << (m - 3);
        assert!(u128::from(visited) <= bound, "{visited} > {bound}");
    }
}

/// Spec (both modes) against generic roots on one instance; returns the
/// number of generic roots.
fn check_instance(
    irr: &IrreduciblePoly,
    basis: &[F2mElement],
    b: u64,
    m: usize,
    x_r: u64,
) -> usize {
    let n = irr.degree;
    let st = FieldStructure::new(n, irr);
    let be = elem(b, n);
    let sys = build_decomposition_system(basis, &elem(x_r, n), &be, m, &st).expect("system");
    let ell = basis.len();
    let nn = n as usize;
    let fes = ChainFes::new(basis, &be, m, irr).expect("applies");
    let mut generic: Vec<ChainRoot> = generic_roots(&sys, nn)
        .into_iter()
        .map(|r| unpack(r, m, ell, nn))
        .collect();
    generic.sort_by_key(order_key);

    let (full, cf) = fes.roots(x_r, Symmetry::Full);
    assert_eq!(cf.roots as usize, full.len());
    // Every leaf is reached once for m = 3; deeper chains prune tuples
    // whose intermediate link has no root and fork on two-root links.
    assert_leaves(cf.leaves, fes.leaves(Symmetry::Full), m);
    assert_eq!(
        full, generic,
        "Full roots differ from generic: n={n} ell={ell} m={m} x_r={x_r:#x} b={b:#x}"
    );
    // Every spec root satisfies the generic equations (packed layout).
    for r in &full {
        let p = r.pack(ell, nn).expect("fits");
        assert!(sys.equations.iter().all(|e| e.eval(p) == 0));
    }
    let (sorted, cs) = fes.roots(x_r, Symmetry::Sorted);
    assert_leaves(cs.leaves, fes.leaves(Symmetry::Sorted), m);
    let want: Vec<ChainRoot> = generic
        .iter()
        .filter(|r| sorted_ranks(r))
        .cloned()
        .collect();
    assert_eq!(sorted, want, "Sorted roots differ: n={n} ell={ell} m={m}");
    generic.len()
}

#[test]
fn quadratic_solver_matches_brute_force() {
    let mut rng = StdRng::seed_from_u64(0x51);
    for n in 2..=9u32 {
        let (irr, basis, b) = random_instance(&mut rng, n, 1);
        let be = elem(b, n);
        let fes = ChainFes::new(&basis, &be, 3, &irr).unwrap();
        let mask = (1u64 << n) - 1;
        for trial in 0..200 {
            let a = if trial % 7 == 0 {
                0
            } else {
                rng.gen::<u64>() & mask
            };
            let bb = if trial % 5 == 0 {
                0
            } else {
                rng.gen::<u64>() & mask
            };
            let c = fes.gf.sqr(bb) ^ b;
            let (roots, k) = fes.solve(a, bb, c);
            let want: Vec<u64> = (0..=mask)
                .filter(|&y| fes.gf.mul(a, fes.gf.sqr(y)) ^ fes.gf.mul(bb, y) ^ c == 0)
                .collect();
            assert_eq!(&roots[..k], &want[..], "n={n} a={a:#x} b={bb:#x}");
        }
    }
}

#[test]
fn coordinates_recognise_exactly_the_span() {
    let mut rng = StdRng::seed_from_u64(0x52);
    for n in [3u32, 6, 9, 12] {
        for ell in 1..=(n as usize).min(5) {
            let (irr, basis, b) = random_instance(&mut rng, n, ell);
            let fes = ChainFes::new(&basis, &elem(b, n), 3, &irr).unwrap();
            let span: BTreeSet<u64> = (0..1u64 << ell).map(|c| fes.span(c)).collect();
            for y in 0..1u64 << n {
                match fes.coordinates(y) {
                    Some(c) => assert_eq!(fes.span(c), y),
                    None => assert!(!span.contains(&y)),
                }
            }
        }
    }
}

#[test]
fn full_roots_equal_generic_roots_m3_random_instances() {
    let mut rng = StdRng::seed_from_u64(0x53);
    let mut total = 0;
    for (n, ell) in [
        (3u32, 1usize),
        (3, 2),
        (4, 2),
        (5, 2),
        (5, 3),
        (6, 2),
        (7, 3),
        (8, 2),
        (9, 3),
    ] {
        for _ in 0..6 {
            let (irr, basis, b) = random_instance(&mut rng, n, ell);
            let mask = (1u64 << n) - 1;
            for x_r in [0u64, 1, rng.gen::<u64>() & mask, rng.gen::<u64>() & mask] {
                total += check_instance(&irr, &basis, b, 3, x_r);
            }
            // A target inside the span (boundary: x_R ∈ V).
            let x_r = basis[0].raw_bits()[0];
            total += check_instance(&irr, &basis, b, 3, x_r);
        }
    }
    assert!(total > 50, "too few roots to be a test: {total}");
}

#[test]
fn full_roots_equal_generic_roots_m4_m5_random_instances() {
    let mut rng = StdRng::seed_from_u64(0x54);
    let mut total = 0;
    for (n, ell, m) in [
        (3u32, 1usize, 4usize),
        (4, 1, 4),
        (4, 2, 4),
        (5, 2, 4),
        (3, 1, 5),
        (3, 2, 5),
        (4, 1, 5),
    ] {
        for _ in 0..4 {
            let (irr, basis, b) = random_instance(&mut rng, n, ell);
            let mask = (1u64 << n) - 1;
            for x_r in [0u64, rng.gen::<u64>() & mask, rng.gen::<u64>() & mask] {
                total += check_instance(&irr, &basis, b, m, x_r);
            }
        }
    }
    assert!(total > 50, "too few roots to be a test: {total}");
}

#[test]
fn full_ell_equals_n_boundary() {
    // ℓ = n: the span is the whole field (the ambient-basis case).
    let mut rng = StdRng::seed_from_u64(0x55);
    for n in [2u32, 3, 4] {
        let (irr, basis, b) = random_instance(&mut rng, n, n as usize);
        for x_r in 0..1u64 << n {
            check_instance(&irr, &basis, b, 3, x_r);
        }
    }
}

/// A planted root at large `n` (past the generic 64-unknown cap): pick
/// summands, run the chain forward, set `x_R` from the last link.
#[test]
fn planted_roots_are_found_past_the_generic_cap() {
    let mut rng = StdRng::seed_from_u64(0x56);
    for (n, ell, m) in [
        (31u32, 6usize, 3usize),
        (47, 5, 3),
        (63, 4, 3),
        (40, 4, 4),
        (29, 3, 5),
    ] {
        let (irr, basis, b) = random_instance(&mut rng, n, ell);
        let be = elem(b, n);
        let fes = ChainFes::new(&basis, &be, m, &irr).unwrap();
        let mut planted = 0;
        let mut attempts = 0;
        while planted < 3 && attempts < 400 {
            attempts += 1;
            let coords: Vec<u64> = (0..m)
                .map(|_| rng.gen::<u64>() & ((1 << ell) - 1))
                .collect();
            let xs: Vec<u64> = coords.iter().map(|&c| fes.span(c)).collect();
            let mut w = xs[0];
            let mut inter = Vec::new();
            let mut ok = true;
            for &x in &xs[1..m - 1] {
                let bb = fes.gf.mul(w, x);
                let (us, k) = fes.solve(fes.gf.sqr(w ^ x), bb, fes.gf.sqr(bb) ^ b);
                if k == 0 {
                    ok = false;
                    break;
                }
                w = us[rng.gen_range(0..k)];
                inter.push(w);
            }
            if !ok {
                continue;
            }
            let y = xs[m - 1];
            let bb = fes.gf.mul(w, y);
            let (zs, k) = fes.solve(fes.gf.sqr(w ^ y), bb, fes.gf.sqr(bb) ^ b);
            if k == 0 {
                continue;
            }
            let x_r = zs[0];
            assert_eq!(fes.s3(w, y, x_r), 0);
            let want = ChainRoot {
                coords: coords.clone(),
                inter: inter.clone(),
            };
            let mut hit = false;
            fes.for_each_root(x_r, Symmetry::Full, |r| {
                if *r == want {
                    hit = true;
                    return ControlFlow::Break(());
                }
                ControlFlow::Continue(())
            });
            assert!(hit, "planted root missed: n={n} ell={ell} m={m}");
            // Every root returned satisfies every link.
            let (roots, _) = fes.roots(x_r, Symmetry::Sorted);
            for r in &roots {
                let xs: Vec<u64> = r.coords.iter().map(|&c| fes.span(c)).collect();
                let mut w = xs[0];
                for k in 1..m - 1 {
                    assert_eq!(fes.s3(w, xs[k], r.inter[k - 1]), 0);
                    w = r.inter[k - 1];
                }
                assert_eq!(fes.s3(w, xs[m - 1], x_r), 0);
            }
            planted += 1;
        }
        assert_eq!(planted, 3, "could not plant: n={n}");
    }
}

#[test]
fn refuses_outside_its_domain() {
    let irr = find_irreducible_sparse(7).unwrap();
    let v = |x: u64| elem(x, 7);
    // b = 0 (singular curve).
    assert!(ChainFes::new(&[v(1), v(2)], &v(0), 3, &irr).is_none());
    // Dependent basis.
    assert!(ChainFes::new(&[v(3), v(5), v(6)], &v(1), 3, &irr).is_none());
    // m < 3 and an empty basis.
    assert!(ChainFes::new(&[v(1)], &v(1), 2, &irr).is_none());
    assert!(ChainFes::new(&[], &v(1), 3, &irr).is_none());
    assert!(ChainFes::new(&[v(1)], &v(1), 3, &irr).is_some());
}

// ── Decompositions on Koblitz factor bases ─────────────────────────

struct Kob {
    kc: KoblitzCurve,
    fb: FrobeniusFactorBase,
    index_of: HashMap<(BigUint, BigUint), usize>,
    st: FieldStructure,
}

fn kob(a: u8, n: u32, which: usize) -> Option<Kob> {
    let kc = KoblitzCurve::new(a, n)?;
    let fb = build_frobenius_factor_base(&kc, which)?;
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let index_of = fb
        .points
        .iter()
        .enumerate()
        .map(|(i, p)| (point_key(p), i))
        .collect();
    Some(Kob {
        kc,
        fb,
        index_of,
        st,
    })
}

/// Every decomposition a root's abscissae admit (all sign choices), as
/// sorted index multisets.
fn all_lifts(k: &Kob, xs: &[F2mElement], target: &BinaryPoint, out: &mut BTreeSet<Vec<usize>>) {
    fn walk(
        k: &Kob,
        xs: &[F2mElement],
        acc: &BinaryPoint,
        chosen: &mut Vec<usize>,
        target: &BinaryPoint,
        out: &mut BTreeSet<Vec<usize>>,
    ) {
        if chosen.len() == xs.len() {
            if acc == target {
                let mut c = chosen.clone();
                c.sort_unstable();
                out.insert(c);
            }
            return;
        }
        for p in crate::cryptanalysis::koblitz_index_calculus::points_with_x(
            &k.kc.curve,
            &xs[chosen.len()],
        ) {
            let Some(&i) = k.index_of.get(&point_key(&p)) else {
                continue;
            };
            chosen.push(i);
            let next = k.kc.add(acc, &k.fb.points[i]);
            walk(k, xs, &next, chosen, target, out);
            chosen.pop();
        }
    }
    walk(k, xs, &BinaryPoint::Infinity, &mut Vec::new(), target, out);
}

/// A decomposition is degenerate when a non-empty proper sub-multiset of
/// its points sums to `O`.
fn degenerate(k: &Kob, d: &[usize]) -> bool {
    let m = d.len();
    (1u32..(1 << m) - 1).any(|mask| {
        let s = (0..m)
            .filter(|i| mask >> i & 1 == 1)
            .fold(BinaryPoint::Infinity, |acc, i| {
                k.kc.add(&acc, &k.fb.points[d[i]])
            });
        s == BinaryPoint::Infinity
    })
}

fn x_bits(p: &BinaryPoint) -> u64 {
    match p {
        BinaryPoint::Affine { x, .. } => bits(x),
        BinaryPoint::Infinity => unreachable!(),
    }
}

fn targets(k: &Kob, m: usize, planted: usize, random: usize, seed: u64) -> Vec<BinaryPoint> {
    let mut rng = StdRng::seed_from_u64(seed);
    let mut out = Vec::new();
    while out.len() < planted {
        let t = (0..m).fold(BinaryPoint::Infinity, |acc, _| {
            k.kc.add(&acc, &k.fb.points[rng.gen_range(0..k.fb.points.len())])
        });
        if matches!(t, BinaryPoint::Affine { .. }) {
            out.push(t);
        }
    }
    let mut tries = 0;
    while out.len() < planted + random && tries < 10 * (random + 1) {
        tries += 1;
        let s = BigUint::from(rng.gen_range(1u64..u64::MAX));
        let t = k.kc.mul(k.kc.generator(), &s);
        if matches!(t, BinaryPoint::Affine { .. }) {
            out.push(t);
        }
    }
    out
}

/// Spec decompositions against the generic system's, on one target.
fn check_decompositions(k: &Kob, m: usize, target: &BinaryPoint) -> bool {
    let n = k.kc.n;
    let ell = k.fb.subspace_basis.len();
    let x_r = x_bits(target);
    let sys =
        build_decomposition_system(&k.fb.subspace_basis, &elem(x_r, n), &k.kc.curve.b, m, &k.st)
            .expect("system");
    let mut generic: Vec<ChainRoot> = generic_roots(&sys, n as usize)
        .into_iter()
        .map(|r| unpack(r, m, ell, n as usize))
        .collect();
    generic.sort_by_key(order_key);
    let fes = ChainFes::new(
        &k.fb.subspace_basis,
        &k.kc.curve.b,
        m,
        &k.kc.curve.irreducible,
    )
    .expect("applies");
    let xs_of = |r: &ChainRoot| -> Vec<F2mElement> {
        r.coords.iter().map(|&c| elem(fes.span(c), n)).collect()
    };
    let lifts = |roots: &[ChainRoot]| {
        let mut set = BTreeSet::new();
        for r in roots {
            all_lifts(k, &xs_of(r), target, &mut set);
        }
        set
    };
    let generic_set = lifts(&generic);
    let (full, _) = fes.roots(x_r, Symmetry::Full);
    assert_eq!(full, generic);
    assert_eq!(lifts(&full), generic_set);
    let (sorted, _) = fes.roots(x_r, Symmetry::Sorted);
    let sorted_set = lifts(&sorted);
    assert!(sorted_set.is_subset(&generic_set));
    for d in &generic_set {
        if !degenerate(k, d) {
            assert!(sorted_set.contains(d), "Sorted missed non-degenerate {d:?}");
        }
    }
    // The dispatched oracle: first lift (lift_candidate) of the generic
    // roots in the documented order, restricted to sorted ranks.
    let want = generic
        .iter()
        .filter(|r| sorted_ranks(r))
        .find_map(|r| lift_candidate(&k.kc, &k.fb, &k.index_of, &xs_of(r), target));
    let (got, stats) =
        fes_chain_decompose(&k.kc, &k.fb, &k.index_of, &k.st, target, m).expect("applies");
    assert_eq!(got, want);
    assert_eq!(stats.refuted, got.is_none());
    // Full mode's first lift is the generic order's first lift.
    let want_full = generic
        .iter()
        .find_map(|r| lift_candidate(&k.kc, &k.fb, &k.index_of, &xs_of(r), target));
    let (got_full, _, _) =
        fes_chain_decompose_with(&k.kc, &k.fb, &k.index_of, target, m, Symmetry::Full)
            .expect("applies");
    assert_eq!(got_full, want_full);
    // mq_fes dispatches m ≥ 3 here.
    let (via_mq, _) =
        crate::cryptanalysis::mq_fes::mq_fes_decompose(&k.kc, &k.fb, &k.index_of, &k.st, target, m);
    assert_eq!(via_mq, got);
    if let Some(d) = &got {
        assert!(generic_set.contains(d));
    }
    got.is_some()
}

#[test]
fn decompositions_match_generic_on_koblitz_bases_m3() {
    let mut found = 0;
    let mut checked = 0;
    for (a, n) in [(0u8, 5u32), (1, 5), (0, 7), (1, 7), (1, 9)] {
        for which in 0..3 {
            let Some(k) = kob(a, n, which) else { continue };
            let ell = k.fb.subspace_basis.len();
            if 3 * ell + n as usize > 22 || k.fb.points.is_empty() {
                continue;
            }
            for t in targets(&k, 3, 4, 4, 0x60 ^ u64::from(n) ^ which as u64) {
                checked += 1;
                found += usize::from(check_decompositions(&k, 3, &t));
            }
        }
    }
    assert!(checked >= 24, "checked {checked}");
    assert!(found > 0, "no planted decomposition found");
}

#[test]
fn decompositions_match_generic_on_koblitz_bases_m4() {
    let mut checked = 0;
    let mut found = 0;
    for (a, n) in [(0u8, 3u32), (1, 3), (0, 5), (1, 5)] {
        for which in 0..3 {
            let Some(k) = kob(a, n, which) else { continue };
            let ell = k.fb.subspace_basis.len();
            if 4 * ell + 2 * n as usize > 22 || k.fb.points.is_empty() {
                continue;
            }
            for t in targets(&k, 4, 4, 4, 0x61 ^ u64::from(n) ^ which as u64) {
                checked += 1;
                found += usize::from(check_decompositions(&k, 4, &t));
            }
        }
    }
    assert!(checked >= 8, "checked {checked}");
    assert!(found > 0, "no planted decomposition found");
}

/// Against the generic SAT oracle on cells too large for exhaustive
/// evaluation: when SAT returns a non-degenerate decomposition the
/// specialised path finds one too; when SAT refutes, so does it; and
/// whatever the specialised path returns is a valid decomposition.
#[test]
fn agrees_with_generic_sat_m3() {
    for (a, n, which) in [(1u8, 11u32, 0usize), (0, 11, 1), (1, 13, 0)] {
        let Some(k) = kob(a, n, which) else { continue };
        for t in targets(&k, 3, 3, 3, 0x62 ^ u64::from(n)) {
            let (sat, sstats) = sat_decompose(&k.kc, &k.fb, &k.index_of, &k.st, &t, 3, 64, Some(2));
            let (spec, _) =
                fes_chain_decompose(&k.kc, &k.fb, &k.index_of, &k.st, &t, 3).expect("applies");
            if let Some(d) = &spec {
                let sum = d.iter().fold(BinaryPoint::Infinity, |acc, &i| {
                    k.kc.add(&acc, &k.fb.points[i])
                });
                assert_eq!(sum, t);
            }
            if let Some(d) = &sat {
                if !degenerate(&k, d) {
                    assert!(spec.is_some(), "spec missed SAT's {d:?}");
                }
            }
            if sstats.refuted {
                assert!(spec.is_none());
            }
        }
    }
}

// ── Work budget ────────────────────────────────────────────────────

#[test]
fn max_leaves_env_parsing() {
    assert_eq!(parse_max_leaves(None), DEFAULT_MAX_LEAVES);
    assert_eq!(parse_max_leaves(Some("")), DEFAULT_MAX_LEAVES);
    assert_eq!(parse_max_leaves(Some("lots")), DEFAULT_MAX_LEAVES);
    assert_eq!(parse_max_leaves(Some("-3")), DEFAULT_MAX_LEAVES);
    assert_eq!(parse_max_leaves(Some(" 12345 ")), 12345);
    assert_eq!(parse_max_leaves(Some("0")), 0);
    // Clamped to the hard ceiling.
    assert_eq!(parse_max_leaves(Some("999999999999999999999")), MAX_LEAVES);
    assert_eq!(parse_max_leaves(Some(&u128::MAX.to_string())), MAX_LEAVES);
}

/// An explicit cap below the cell's leaf count refuses at once and never
/// claims a refutation; a cap at the leaf count runs the walk.
#[test]
fn explicit_cap_refuses_without_refuting() {
    let k = kob(1, 11, 0).expect("curve");
    let ell = k.fb.subspace_basis.len();
    let t = targets(&k, 3, 2, 2, 0x70).remove(0);
    let fes = ChainFes::new(
        &k.fb.subspace_basis,
        &k.kc.curve.b,
        3,
        &k.kc.curve.irreducible,
    )
    .expect("applies");
    let leaves = fes.leaves(Symmetry::Sorted);
    assert!(leaves > 1, "ell={ell}");
    for cap in [0, 1, leaves - 1] {
        let out =
            fes_chain_decompose_capped(&k.kc, &k.fb, &k.index_of, &t, 3, Symmetry::Sorted, cap);
        assert!(out.is_none(), "cap {cap} must refuse");
    }
    let (found, stats, extra) =
        fes_chain_decompose_capped(&k.kc, &k.fb, &k.index_of, &t, 3, Symmetry::Sorted, leaves)
            .expect("cap == leaves runs");
    assert_eq!(stats.refuted, found.is_none());
    assert!(extra.counters.leaves > 0);
}

/// A cell far past the default budget (`ℓ = 20`, `m = 3`: about `2^39`
/// sorted leaves) is reported exhausted and not refuted, promptly, by
/// both the chain entry point and `mq_fes_decompose`.
#[test]
fn over_budget_cell_is_exhausted_not_refuted() {
    use crate::cryptanalysis::mq_fes::mq_fes_decompose;
    let mut k = kob(1, 23, 0).expect("curve");
    // Swap in 20 independent basis elements; the budget check runs before
    // anything touches the factor base's points.
    let mut rng = StdRng::seed_from_u64(0x71);
    let n = k.kc.n;
    let basis = loop {
        let cand: Vec<u64> = (0..20).map(|_| rng.gen::<u64>() & ((1 << n) - 1)).collect();
        if preimage_map(&cand, n as usize).1 == 20 {
            break cand;
        }
    };
    k.fb.subspace_basis = basis.iter().map(|&v| elem(v, n)).collect();
    let fes = ChainFes::new(
        &k.fb.subspace_basis,
        &k.kc.curve.b,
        3,
        &k.kc.curve.irreducible,
    )
    .expect("applies");
    assert!(fes.leaves(Symmetry::Sorted) > 1u128 << 38);
    if max_leaves() >= fes.leaves(Symmetry::Sorted) {
        return; // someone raised IC_FES_CHAIN_MAX_LEAVES past this cell
    }
    let t = k.kc.mul(k.kc.generator(), &BigUint::from(12345u32));
    let start = std::time::Instant::now();
    assert!(fes_chain_decompose(&k.kc, &k.fb, &k.index_of, &k.st, &t, 3).is_none());
    let (d, stats) = mq_fes_decompose(&k.kc, &k.fb, &k.index_of, &k.st, &t, 3);
    assert!(d.is_none());
    assert!(stats.exhausted, "over-budget must report exhausted");
    assert!(!stats.refuted, "over-budget must never claim refuted");
    assert!(
        start.elapsed() < std::time::Duration::from_secs(5),
        "took {:?}",
        start.elapsed()
    );
}
