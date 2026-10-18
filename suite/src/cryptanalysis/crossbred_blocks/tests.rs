//! Differential tests: the block-planned crossbred and block-elimination
//! XL solvers against brute force, against the generic crossbred split
//! (`D = deg`, `k = n_vars / 2`), and against each other, on synthetic
//! block-structured systems and on Weil-descended Semaev chains.

use super::*;
use crate::binary_ecc::BinaryPoint;
use crate::cryptanalysis::koblitz_groebner::{build_decomposition_system, FieldStructure};
use crate::cryptanalysis::koblitz_index_calculus::{
    build_frobenius_factor_base, crossbred_decompose, crossbred_params_for, enumerate_decompose,
    KoblitzCurve,
};
use num_bigint::BigUint;
use rand::{rngs::StdRng, Rng, SeedableRng};

/// Every root by exhaustive evaluation (`n_vars ≤ 20`).
fn brute_force(system: &[F2BoolPoly], n_vars: usize) -> Vec<u64> {
    (0..(1u64 << n_vars))
        .filter(|&x| system.iter().all(|p| p.eval(x) == 0))
        .collect()
}

/// The generic crossbred path: `D = deg`, `k = n_vars / 2` (clamped as
/// the oracle clamps it), default search.  `None` when the extraction is
/// refused or the search is exhausted, i.e. when it does not decide.
fn generic(system: &[F2BoolPoly], n_vars: usize) -> Option<Vec<u64>> {
    let params = crossbred_params_for(system, n_vars);
    let xb = extract_crossbred(system, n_vars, &params)?;
    let (mut roots, st) = solve_crossbred(system, &xb, &SearchOptions::default());
    if st.exhausted {
        return None;
    }
    roots.sort_unstable();
    Some(roots)
}

/// A random system with the chain's block structure: per link, `eqs`
/// equations each of whose monomials takes at most one variable from
/// each of the link's blocks.  Planted at `plant` when given (constant
/// terms fixed so the point is a root).
fn random_chain(
    layout: &SummandBlocks,
    eqs: usize,
    terms: usize,
    rng: &mut StdRng,
    plant: Option<u64>,
) -> Vec<F2BoolPoly> {
    let blocks = layout.blocks();
    let m = layout.m;
    let mut links: Vec<Vec<Block>> = Vec::new();
    if m == 2 {
        links.push(vec![blocks[0], blocks[1]]);
    } else {
        links.push(vec![blocks[0], blocks[1], blocks[m]]);
        for j in 1..m - 2 {
            links.push(vec![blocks[m + j - 1], blocks[j + 1], blocks[m + j]]);
        }
        links.push(vec![blocks[2 * m - 3], blocks[m - 1]]);
    }
    let mut out = Vec::new();
    for link in &links {
        for _ in 0..eqs {
            let mut monos = Vec::new();
            for _ in 0..terms {
                let mut mask = 0u64;
                for b in link {
                    if rng.gen_bool(0.6) {
                        mask |= 1u64 << (b.first + rng.gen_range(0..b.len));
                    }
                }
                monos.push(F2BoolMono::from_mask(mask));
            }
            let mut p = F2BoolPoly::from_monos(monos, layout.n_vars);
            if let Some(x) = plant {
                if p.eval(x) == 1 {
                    p = p.add(&F2BoolPoly::one(layout.n_vars));
                }
            }
            out.push(p);
        }
    }
    out
}

/// Every block solver configuration, enumerating per-point solution
/// spaces up to dimension `kernel_dim`.
fn all_block_solvers(
    system: &[F2BoolPoly],
    layout: &SummandBlocks,
    kernel_dim: u32,
) -> Vec<(&'static str, Vec<u64>, bool)> {
    let wide = SearchOptions {
        max_kernel_dim: kernel_dim,
        ..SearchOptions::default()
    };
    let mut out = Vec::new();
    for (name, opts) in [
        (
            "xb-direct",
            CrossbredBlockOptions {
                search: wide,
                ..CrossbredBlockOptions::default()
            },
        ),
        (
            "xb-macaulay",
            CrossbredBlockOptions {
                preprocess: Preprocess::Macaulay { max_rows: 20_000 },
                search: wide,
                max_outer_bits: 0,
            },
        ),
        (
            "xb-outer",
            CrossbredBlockOptions {
                preprocess: Preprocess::Direct,
                search: SearchOptions {
                    max_enumerated_bits: 2,
                    ..wide
                },
                max_outer_bits: 10,
            },
        ),
        (
            "xb-outer-macaulay",
            CrossbredBlockOptions {
                preprocess: Preprocess::Macaulay { max_rows: 20_000 },
                search: SearchOptions {
                    max_enumerated_bits: 3,
                    ..wide
                },
                max_outer_bits: 9,
            },
        ),
    ] {
        if let Some((roots, st)) = solve_crossbred_blocks(system, layout, &opts) {
            out.push((name, roots, st.search.exhausted));
        }
    }
    let xl = BlockXlOptions {
        max_kernel_dim: kernel_dim,
        max_enumerated_bits: 40,
    };
    if let Some((roots, st)) = solve_block_xl(system, layout, &xl) {
        out.push(("xl", roots, st.exhausted));
    }
    out
}

#[test]
fn layouts_parse_and_reject() {
    let l = SummandBlocks::new(2, 6, 12).unwrap();
    assert_eq!((l.n, l.blocks().len()), (0, 2));
    let l = SummandBlocks::new(3, 4, 27).unwrap();
    assert_eq!(l.n, 15);
    let b = l.blocks();
    assert_eq!(b[3].kind, BlockKind::Intermediate(0));
    assert_eq!((b[3].first, b[3].len), (12, 15));
    let l = SummandBlocks::new(4, 4, 46).unwrap();
    assert_eq!((l.n, l.blocks()[5].first), (15, 31));
    assert!(SummandBlocks::new(2, 6, 13).is_none());
    assert!(SummandBlocks::new(3, 4, 12).is_none());
    assert!(SummandBlocks::new(4, 4, 47).is_none());
    assert!(SummandBlocks::new(1, 4, 4).is_none());
    assert!(SummandBlocks::new(3, 0, 9).is_none());
    assert!(SummandBlocks::new(5, 10, 80).is_none());
}

#[test]
fn plans_follow_the_blocks() {
    // K_0 / F_2^15, divisor 1: ℓ = 4, n = 15.
    let kc = KoblitzCurve::new(0, 15).unwrap();
    let fb = build_frobenius_factor_base(&kc, 1).unwrap();
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let x = kc.mul(kc.generator(), &BigUint::from(77u32));
    let BinaryPoint::Affine { x, .. } = x else {
        panic!("affine")
    };
    for (m, k_xb, solved, k_xl) in [
        (2, 4, 0b10u64, 4),
        (3, 12, 0b1000, 8),
        (4, 27, 0b01_1000, 12),
    ] {
        let sys = build_decomposition_system(&fb.subspace_basis, &x, &kc.curve.b, m, &st).unwrap();
        let layout = SummandBlocks::of_system(&sys).unwrap();
        let plan = plan_crossbred(&sys.equations, &layout).unwrap();
        assert_eq!(plan.enumerated, k_xb, "m = {m}");
        assert_eq!(plan.solved_blocks, solved, "m = {m}");
        assert_eq!(plan.macaulay_degree, if m == 2 { 2 } else { 3 }, "m = {m}");
        for (old, &new) in plan.perm.iter().enumerate() {
            assert_eq!(plan.order[new as usize] as usize, old);
        }
        // Every equation has specialised degree ≤ 1 under the plan.
        let enum_mask = mask_of(plan.enumerated);
        for p in &sys.equations {
            for t in &permute_poly(p, &plan.perm).terms {
                assert!((t.mask & !enum_mask).count_ones() <= 1);
            }
        }
        let xl = plan_block_xl(&sys.equations, &layout).unwrap();
        assert_eq!(xl.enumerated, k_xl, "m = {m}");
        assert_eq!(xl.stages.len(), m - 1);
        let assigned: usize = xl
            .stages
            .iter()
            .map(|s| s.linear.len() + s.filters.len())
            .sum();
        assert_eq!(
            assigned,
            sys.equations.len(),
            "m = {m}: an equation was left over"
        );
    }
}

#[test]
fn degenerate_systems_have_no_plan() {
    let layout = SummandBlocks::new(3, 2, 10).unwrap();
    assert!(plan_crossbred(&[], &layout).is_none());
    assert!(plan_block_xl(&[], &layout).is_none());
    let zero = vec![F2BoolPoly::zero(10); 4];
    assert!(solve_crossbred_blocks(&zero, &layout, &CrossbredBlockOptions::default()).is_none());
    assert!(solve_block_xl(&zero, &layout, &BlockXlOptions::default()).is_none());
    // A variable outside the layout.
    let stray = vec![F2BoolPoly::from_monos(vec![F2BoolMono::var(11)], 12)];
    assert!(block_graph(&stray, &layout.blocks()).is_none());
}

#[test]
fn synthetic_chains_match_brute_force_and_generic() {
    let mut rng = StdRng::seed_from_u64(0x0b10_c4ed);
    let mut decided_generic = 0usize;
    let mut with_roots = 0usize;
    let mut constant_only = 0usize;
    // (m, ℓ, n) small enough to brute-force, including ℓ = 1 and n = 1.
    let shapes = [
        (2, 1, 0),
        (2, 3, 0),
        (2, 6, 0),
        (3, 1, 1),
        (3, 2, 3),
        (3, 2, 6),
        (3, 3, 4),
        (4, 1, 2),
        (4, 2, 3),
        (4, 2, 4),
        (5, 1, 2),
        (5, 2, 2),
    ];
    for (case, &(m, ell, n)) in shapes.iter().cycle().take(shapes.len() * 12).enumerate() {
        let n_vars = m * ell + (m - 2) * n;
        let layout = SummandBlocks::new(m, ell, n_vars).unwrap();
        let eqs = (n.max(ell) + rng.gen_range(0..3)).max(1);
        let terms = rng.gen_range(2..10);
        let plant = match case % 3 {
            0 => None,
            1 => Some(rng.gen_range(0..(1u64 << n_vars))),
            _ => Some(0),
        };
        let mut system = random_chain(&layout, eqs, terms, &mut rng, plant);
        if case % 17 == 5 {
            // Inconsistent: the constant 1.
            system.push(F2BoolPoly::one(n_vars));
        }
        if case % 13 == 7 {
            system.push(F2BoolPoly::zero(n_vars));
        }
        let truth = brute_force(&system, n_vars);
        if let Some(x) = plant {
            if case % 17 != 5 {
                assert!(truth.contains(&x), "case {case}: plant lost");
            }
        }
        with_roots += usize::from(!truth.is_empty());
        let solvers = all_block_solvers(&system, &layout, 20);
        // Every system with a non-constant monomial has a plan (a single
        // block is always independent here); an all-constant one has none.
        let has_plan = solvers.iter().any(|(n, _, _)| *n == "xb-direct");
        assert_eq!(
            has_plan,
            system_degree(&system) > 0,
            "case {case}: crossbred plan for (m, ℓ, n) = ({m}, {ell}, {n})"
        );
        constant_only += usize::from(!has_plan);
        for (name, roots, exhausted) in &solvers {
            if !exhausted {
                assert_eq!(
                    roots, &truth,
                    "case {case} {name} (m, ℓ, n) = ({m}, {ell}, {n})"
                );
            } else {
                assert!(
                    roots.iter().all(|r| truth.contains(r)),
                    "case {case} {name}"
                );
            }
        }
        if let Some(g) = generic(&system, n_vars) {
            decided_generic += 1;
            assert_eq!(g, truth, "case {case}: generic disagrees with brute force");
        }
    }
    assert!(
        decided_generic > 20,
        "generic decided only {decided_generic}"
    );
    assert!(with_roots > 40, "only {with_roots} systems had roots");
    assert!(constant_only < 10, "{constant_only} all-constant systems");
}

/// The decomposition systems of `planted` planted and `random` random
/// targets on `K_a / F_2^n` with factor-base divisor `fi`.
fn semaev_systems(
    a: u8,
    n: u32,
    fi: usize,
    m: usize,
    planted: usize,
    random: u32,
    seed: u64,
) -> Vec<DecompositionSystem> {
    let kc = KoblitzCurve::new(a, n).unwrap();
    let fb = build_frobenius_factor_base(&kc, fi).unwrap();
    let st = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let mut rng = StdRng::seed_from_u64(seed);
    let mut targets = Vec::new();
    let mut draws = 0usize;
    while targets.len() < planted {
        // Bounded: a factor base can have no affine `m`-sum at all (see
        // `planted_targets_can_be_impossible`), and an unbounded retry
        // loop there spins forever.
        draws += 1;
        assert!(
            draws <= 100_000,
            "K{a}/2^{n} divisor {fi}: no affine {m}-sum of factor-base points in {draws} draws"
        );
        let t = (0..m).fold(BinaryPoint::Infinity, |acc, _| {
            kc.add(&acc, &fb.points[rng.gen_range(0..fb.points.len())])
        });
        if matches!(t, BinaryPoint::Affine { .. }) {
            targets.push(t);
        }
    }
    for i in 0..random {
        targets.push(kc.mul(kc.generator(), &BigUint::from(1 + i * 7919)));
    }
    targets
        .iter()
        .filter_map(|t| match t {
            BinaryPoint::Affine { x, .. } => Some(x.clone()),
            BinaryPoint::Infinity => None,
        })
        .map(|x| build_decomposition_system(&fb.subspace_basis, &x, &kc.curve.b, m, &st).unwrap())
        .collect()
}

#[test]
fn semaev_chains_agree_across_solvers() {
    // (a, n, divisor, m, planted, random)
    let cells = [
        (0u8, 9u32, 0usize, 2usize, 6usize, 6u32),
        (1, 11, 0, 2, 4, 4),
        (0, 15, 1, 2, 4, 4),
        (0, 9, 0, 3, 4, 4),
        (0, 15, 1, 3, 4, 4),
        (0, 15, 2, 3, 3, 3),
        (0, 9, 0, 4, 2, 2),
        (0, 15, 1, 4, 3, 3),
        (1, 7, 0, 4, 4, 4),
        (0, 7, 0, 4, 0, 4),
    ];
    let mut compared_generic = 0usize;
    let mut roots_seen = 0usize;
    for (ci, &(a, n, fi, m, planted, random)) in cells.iter().enumerate() {
        for (si, sys) in semaev_systems(a, n, fi, m, planted, random, 0x5e3a + ci as u64)
            .iter()
            .enumerate()
        {
            let layout = SummandBlocks::of_system(sys).unwrap();
            // Small fields (n = 7) give highly degenerate chains whose
            // per-point solution spaces are wide; the default dimension
            // keeps those cells fast (an exhausted solver is skipped).
            let solvers = all_block_solvers(&sys.equations, &layout, 12);
            let decided: Vec<_> = solvers.iter().filter(|s| !s.2).collect();
            assert!(!decided.is_empty(), "cell {ci} sys {si}: nothing decided");
            let reference = &decided[0].1;
            for (name, roots, _) in &decided {
                assert_eq!(
                    roots, reference,
                    "cell {ci} sys {si}: {name} vs {}",
                    decided[0].0
                );
            }
            for r in reference {
                assert!(sys.equations.iter().all(|p| p.eval(*r) == 0));
            }
            if si < planted {
                assert!(
                    !reference.is_empty(),
                    "cell {ci} sys {si}: planted root lost"
                );
            }
            roots_seen += reference.len();
            if sys.n_vars <= 16 {
                assert_eq!(reference, &brute_force(&sys.equations, sys.n_vars));
            }
            if sys.n_vars <= 30 {
                if let Some(g) = generic(&sys.equations, sys.n_vars) {
                    compared_generic += 1;
                    assert_eq!(&g, reference, "cell {ci} sys {si}: generic disagrees");
                }
            }
            // The dispatcher returns what its chosen solver returns.
            let (auto, _, _) = solve_semaev_blocks(sys).unwrap();
            assert_eq!(&auto, reference, "cell {ci} sys {si}: dispatcher");
        }
    }
    assert!(
        compared_generic >= 10,
        "generic decided only {compared_generic}"
    );
    assert!(roots_seen > 0);
}

#[test]
fn generic_order_groups() {
    let mut r = vec![0b1_01u64, 0b0_11, 0b0_01, 0b1_11, 0b10_00];
    order_like_generic(&mut r, 2);
    assert_eq!(r, vec![0b10_00, 0b0_01, 0b1_01, 0b0_11, 0b1_11]);
    let g = generic_groups(&r, 2);
    assert_eq!(g.len(), 3);
    assert_eq!(g[1], &[0b0_01, 0b1_01]);
}

/// `crossbred_decompose` with default parameters (the block path) returns
/// exactly the decomposition the explicit generic parameters return,
/// whenever the generic search decides; and agrees with enumeration on
/// existence.
#[test]
fn block_decompose_matches_generic_decompose() {
    for (a, n, fi, m, step) in [
        (0u8, 9u32, 0usize, 2usize, 1u64),
        (0, 9, 0, 3, 3),
        (0, 15, 1, 2, 211),
        (0, 15, 1, 3, 1499),
        (1, 7, 0, 4, 1),
        (0, 7, 0, 4, 1),
    ] {
        let kc = KoblitzCurve::new(a, n).unwrap();
        let fb = build_frobenius_factor_base(&kc, fi).unwrap();
        let index = fb.index_map();
        let field = FieldStructure::new(kc.n, &kc.curve.irreducible);
        let r = kc.subgroup_order.to_u64_digits()[0];
        let (mut same, mut found) = (0usize, 0usize);
        let mut k = 1u64;
        while k < r {
            let target = kc.mul(kc.generator(), &BigUint::from(k));
            k += step;
            let BinaryPoint::Affine { x, .. } = &target else {
                continue;
            };
            let sys =
                build_decomposition_system(&fb.subspace_basis, x, &kc.curve.b, m, &field).unwrap();
            let gp = crossbred_params_for(&sys.equations, sys.n_vars);
            let (blk, bst) = crossbred_decompose(&kc, &fb, &index, &field, &target, m, None);
            let (gen, gst) = crossbred_decompose(&kc, &fb, &index, &field, &target, m, Some(gp));
            if let Some(idxs) = &blk {
                let sum = idxs
                    .iter()
                    .fold(BinaryPoint::Infinity, |s, &i| kc.add(&s, &fb.points[i]));
                assert_eq!(sum, target, "K{a}/2^{n} m={m} k={k}");
                found += 1;
            }
            if !gst.exhausted {
                assert_eq!(blk, gen, "K{a}/2^{n} m={m} k={k}: block vs generic");
                same += 1;
            }
            if !bst.exhausted && m == 2 {
                let reference = enumerate_decompose(&kc, &fb, &index, &target, m);
                assert_eq!(blk.is_some(), reference.is_some(), "K{a}/2^{n} k={k}");
            }
        }
        assert!(same > 0, "K{a}/2^{n} m={m}: generic never decided");
        let _ = found;
    }
}

/// An exhausted block search skips branches, so its first lift need not be
/// the generic path's.  With `max_kernel_dim` forced tiny the search is
/// exhausted on many targets; `decompose_via_blocks_with` must then defer
/// (`None`) even when some retained root lifts, and whatever it does
/// return must still equal the generic decomposition.
#[test]
fn exhausted_block_search_defers_to_generic() {
    use crate::cryptanalysis::koblitz_index_calculus::lift_candidate;
    let (mut exhausted, mut exhausted_with_lift, mut returned) = (0usize, 0usize, 0usize);
    for (a, n, fi, m, step) in [
        (0u8, 9u32, 0usize, 2usize, 1u64),
        (0, 9, 0, 3, 3),
        (0, 15, 1, 2, 211),
        (0, 15, 1, 3, 1499),
        (1, 7, 0, 4, 1),
        (0, 7, 0, 4, 1),
    ] {
        let kc = KoblitzCurve::new(a, n).unwrap();
        let fb = build_frobenius_factor_base(&kc, fi).unwrap();
        let index = fb.index_map();
        let field = FieldStructure::new(kc.n, &kc.curve.irreducible);
        let r = kc.subgroup_order.to_u64_digits()[0];
        let mut k = 1u64;
        while k < r {
            let target = kc.mul(kc.generator(), &BigUint::from(k));
            k += step;
            let BinaryPoint::Affine { x, .. } = &target else {
                continue;
            };
            let Some(sys) =
                crate::cryptanalysis::polynomial_reuse::build_decomposition_system_reusing(
                    &fb.subspace_basis,
                    x,
                    &kc.curve.b,
                    m,
                    &field,
                )
            else {
                continue;
            };
            let kg = crossbred_params_for(&sys.equations, sys.n_vars).enumerated;
            for dim in [0u32, 1, 2] {
                let mut xb = CrossbredBlockOptions::default();
                xb.search.max_kernel_dim = dim;
                let xl = BlockXlOptions {
                    max_kernel_dim: dim,
                    ..BlockXlOptions::default()
                };
                let Some((roots, st, _)) = solve_semaev_blocks_with(&sys, &xb, &xl) else {
                    continue;
                };
                let got = decompose_via_blocks_with(&kc, &fb, &index, &sys, &target, kg, &xb, &xl);
                if st.exhausted {
                    exhausted += 1;
                    let lifts = roots.iter().any(|&root| {
                        let xs: Vec<_> = (0..sys.m)
                            .map(|i| sys.summand_x(&fb.subspace_basis, root, i, kc.n))
                            .collect();
                        lift_candidate(&kc, &fb, &index, &xs, &target).is_some()
                    });
                    exhausted_with_lift += usize::from(lifts);
                    assert!(
                        got.is_none(),
                        "K{a}/2^{n} m={m} k={k} dim={dim}: exhausted search must defer"
                    );
                } else if let Some((Some(idxs), _)) = got {
                    returned += 1;
                    let gp = crossbred_params_for(&sys.equations, sys.n_vars);
                    let (gen, gst) =
                        crossbred_decompose(&kc, &fb, &index, &field, &target, m, Some(gp));
                    if !gst.exhausted {
                        assert_eq!(Some(idxs), gen, "K{a}/2^{n} m={m} k={k} dim={dim}");
                    }
                }
            }
        }
    }
    assert!(
        exhausted > 0,
        "tiny max_kernel_dim never exhausted a search"
    );
    assert!(
        exhausted_with_lift > 0,
        "no exhausted search kept a liftable root: the old early return is untested"
    );
    let _ = returned;
}

/// The hang seen on `K_0/2^7`, `m = 4` with planted targets was this kind
/// of generator, not a solver: the divisor-0 factor base of `K_0/2^7` is a
/// single point whose 4-fold sum is the point at infinity (checked
/// exhaustively below), so "plant an affine 4-sum" has no answer and an
/// unbounded retry loop never ends.  The generators are now bounded, and
/// the solver is shown to terminate on the same cell's random targets and
/// to agree with the generic path there.
#[test]
fn planted_targets_can_be_impossible() {
    let kc = KoblitzCurve::new(0, 7).unwrap();
    let fb = build_frobenius_factor_base(&kc, 0).unwrap();
    let np = fb.points.len();
    let m = 4usize;
    let mut idx = vec![0usize; m];
    let (mut affine, mut total) = (0u64, 0u64);
    loop {
        let t = idx
            .iter()
            .fold(BinaryPoint::Infinity, |acc, &i| kc.add(&acc, &fb.points[i]));
        affine += u64::from(matches!(t, BinaryPoint::Affine { .. }));
        total += 1;
        let mut j = 0;
        while j < m {
            idx[j] += 1;
            if idx[j] < np {
                break;
            }
            idx[j] = 0;
            j += 1;
        }
        if j == m {
            break;
        }
    }
    assert_eq!(total, (np as u64).pow(m as u32));
    assert_eq!(affine, 0, "K_0/2^7 divisor 0 m=4: planted targets exist");
    let field = FieldStructure::new(kc.n, &kc.curve.irreducible);
    let index = fb.index_map();
    let r = kc.subgroup_order.to_u64_digits()[0];
    for k in 1..r {
        let target = kc.mul(kc.generator(), &BigUint::from(k));
        let sys = match &target {
            BinaryPoint::Affine { x, .. } => {
                build_decomposition_system(&fb.subspace_basis, x, &kc.curve.b, m, &field)
            }
            BinaryPoint::Infinity => continue,
        };
        let Some(sys) = sys else { continue };
        let gp = crossbred_params_for(&sys.equations, sys.n_vars);
        let (blk, _) = crossbred_decompose(&kc, &fb, &index, &field, &target, m, None);
        let (gen, gst) = crossbred_decompose(&kc, &fb, &index, &field, &target, m, Some(gp));
        if !gst.exhausted {
            assert_eq!(blk, gen, "K_0/2^7 m=4 k={k}");
        }
    }
}
