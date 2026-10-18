//! Differential tests of the `m = 4` linearised oracle against the
//! generic chained system, a brute force over the whole field, and its
//! own reference routes.

use super::*;
use crate::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse;

fn xorshift(state: &mut u64) -> u64 {
    *state ^= *state >> 12;
    *state ^= *state << 25;
    *state ^= *state >> 27;
    state.wrapping_mul(0x2545_F491_4F6C_DD1D)
}

fn field(n: u32, portable: bool) -> Gf2 {
    let mut gf = Gf2::new(&find_irreducible_sparse(n).expect("irreducible"));
    if portable {
        gf.has_clmul = false;
    }
    gf
}

/// A random independent `l`-element basis of `F_{2ⁿ}`.
fn random_basis(l: u32, gf: &Gf2, s: &mut u64) -> Vec<u64> {
    loop {
        let basis: Vec<u64> = (0..l).map(|_| xorshift(s) & gf.mask).collect();
        let mut span: Vec<u64> = (0..1u64 << l)
            .map(|idx| {
                (0..l as usize)
                    .filter(|&j| (idx >> j) & 1 == 1)
                    .fold(0, |a, j| a ^ basis[j])
            })
            .collect();
        span.sort_unstable();
        span.dedup();
        if span.len() == 1 << l {
            return basis;
        }
    }
}

/// A root of `S₃(x₁, x₂, ·)`, if it has one.
fn s3_root(x1: u64, x2: u64, b: u64, gf: &Gf2, pick: u64) -> Option<u64> {
    let as_ = ArtinSchreier::new(gf);
    let (r, k) = s3_roots(x1, x2, b, gf, &as_);
    (k > 0).then(|| r[(pick as usize) % k])
}

/// The resultant `R(x)` for the triple, straight from the table.
fn resultant(x1: u64, x2: u64, x3: u64, xr: u64, b: u64, gf: &Gf2) -> P9 {
    let q = quartic_general_with(x1, x2, &GeneralTargetPowers::new(x3, b, gf), gf);
    let a = [q.c[0], q.c[1], q.c[2], q.c[3], q.c[4]];
    ResultantTable::new(xr, b, gf).apply(&a, gf)
}

/// Completeness rests on this: whenever a chain is rational,
/// `R(X₄) = 0`.  Random full-field chains, even and odd `n`.
#[test]
fn resultant_vanishes_on_every_rational_chain() {
    let mut s = 0x0C71_C5E5_0000_0001u64;
    let mut checked = 0;
    for n in [5u32, 8, 11, 12, 17, 24, 31, 53] {
        for portable in [false, true] {
            let gf = field(n, portable);
            for _ in 0..300 {
                let b = (xorshift(&mut s) & gf.mask).max(1);
                let (x1, x2, x3, x4) = (
                    xorshift(&mut s) & gf.mask,
                    xorshift(&mut s) & gf.mask,
                    xorshift(&mut s) & gf.mask,
                    xorshift(&mut s) & gf.mask,
                );
                let Some(e1) = s3_root(x1, x2, b, &gf, xorshift(&mut s)) else {
                    continue;
                };
                let Some(e2) = s3_root(e1, x3, b, &gf, xorshift(&mut s)) else {
                    continue;
                };
                let Some(xr) = s3_root(e2, x4, b, &gf, xorshift(&mut s)) else {
                    continue;
                };
                assert_eq!(s3(e2, x4, xr, b, &gf), 0);
                let r = resultant(x1, x2, x3, xr, b, &gf);
                assert_eq!(eval(&r, x4, &gf), 0, "n={n} portable={portable}");
                // And symmetric in the triple, as S₄ is.
                assert_eq!(r, resultant(x3, x1, x2, xr, b, &gf));
                checked += 1;
            }
        }
    }
    assert!(checked > 500, "only {checked} chains planted");
}

/// The table is the formal resultant: compare with `β₂⁴ A(u₁)A(u₂)`
/// computed from the roots of `B` where `B` splits over the field.
#[test]
fn resultant_matches_the_product_over_the_roots() {
    let mut s = 0xA11C_E0F0_0000_0002u64;
    let mut checked = 0;
    for n in [7u32, 10, 13, 20] {
        let gf = field(n, false);
        let as_ = ArtinSchreier::new(&gf);
        for _ in 0..400 {
            let b = (xorshift(&mut s) & gf.mask).max(1);
            let (x1, x2, x3, x, xr) = (
                xorshift(&mut s) & gf.mask,
                xorshift(&mut s) & gf.mask,
                xorshift(&mut s) & gf.mask,
                xorshift(&mut s) & gf.mask,
                xorshift(&mut s) & gf.mask,
            );
            let q = quartic_general_with(x1, x2, &GeneralTargetPowers::new(x3, b, &gf), &gf);
            let beta2 = gf.sqr(x ^ xr);
            let p = gf.mul(x, xr);
            let (u, k) = quadratic_roots(beta2, p, gf.sqr(p) ^ b, &gf, &as_);
            if k != 2 {
                continue;
            }
            let av = |t: u64| eval(&q.c[..5], t, &gf);
            let want = gf.mul(gf.sqr(gf.sqr(beta2)), gf.mul(av(u[0]), av(u[1])));
            assert_eq!(eval(&resultant(x1, x2, x3, xr, b, &gf), x, &gf), want);
            checked += 1;
        }
    }
    assert!(checked > 300);
}

/// `z² + z = δ` is solved exactly when it is solvable (trace zero), for
/// even and odd `n`.
#[test]
fn artin_schreier_solves_exactly_the_trace_zero_targets() {
    let mut s = 0x7EA5_0000_0000_0003u64;
    for n in [2u32, 3, 4, 8, 9, 16, 33, 62, 63] {
        let gf = field(n, false);
        let as_ = ArtinSchreier::new(&gf);
        let trace = |d: u64| (0..n).fold(0u64, |acc, k| acc ^ gf.sqr_k(d, k));
        for _ in 0..200 {
            let z = xorshift(&mut s) & gf.mask;
            let d = gf.sqr(z) ^ z;
            let got = as_.solve(d).expect("an image is solvable");
            assert_eq!(gf.sqr(got) ^ got, d);
            let d = xorshift(&mut s) & gf.mask;
            assert_eq!(as_.solve(d).is_some(), trace(d) == 0, "n={n}");
        }
    }
}

/// The octic route returns exactly the generic remainder, for subspace
/// polynomials and arbitrary coefficient vectors, on random octics and
/// octics with planted subspace roots, with and without the carry-less
/// multiply; and the gcd's roots are exactly the planted subspace
/// roots.
#[test]
fn octic_route_matches_the_generic_remainder() {
    let mut s = 0x0C71_C000_0000_0004u64;
    for (n, l) in [
        (5u32, 2u32),
        (8, 3),
        (13, 1),
        (13, 4),
        (20, 7),
        (31, 9),
        (53, 12),
    ] {
        for portable in [false, true] {
            let gf = field(n, portable);
            let basis = random_basis(l, &gf, &mut s);
            let oracle = TripleOracle::new(&basis, 1, &gf);
            let random_lv: Vec<Vec<u64>> = (1..=8)
                .map(|len| (0..len).map(|_| xorshift(&mut s) & gf.mask).collect())
                .collect();
            for lv in std::iter::once(&oracle.lv).chain(&random_lv) {
                let horner = Horner::new(lv, &gf);
                for trial in 0..200 {
                    let planted = trial % 9;
                    // Π (t + r_i), eight roots, `planted` of them in V.
                    let mut f = vec![1u64];
                    let mut in_v = Vec::new();
                    for i in 0..8 {
                        let r = if i < planted {
                            let v =
                                oracle.span[(xorshift(&mut s) >> 9) as usize % oracle.span.len()];
                            in_v.push(v);
                            v
                        } else {
                            xorshift(&mut s) & gf.mask
                        };
                        f = pmul(&f, &[r, 1], &gf);
                    }
                    if planted == 0 && trial % 2 == 1 {
                        for c in f.iter_mut().take(8) {
                            *c = xorshift(&mut s) & gf.mask;
                        }
                    }
                    let low: [u64; OCT] = f[..OCT].try_into().unwrap();
                    let want = lv_mod_generic(&f, OCT, lv, &gf);
                    let got = lv_mod_octic(&low, &horner, &gf);
                    assert_eq!(&want[..OCT], &got[..], "n={n} l={l} portable={portable}");
                    assert_eq!(want[OCT], 0);
                    if std::ptr::eq(lv, &oracle.lv) {
                        let mut fp = [0u64; OCT + 1];
                        fp.copy_from_slice(&f);
                        let g = gcd9(&fp, &want, &gf);
                        let mut roots: Vec<u64> = oracle
                            .span
                            .iter()
                            .copied()
                            .filter(|&t| eval(&g, t, &gf) == 0)
                            .collect();
                        in_v.sort_unstable();
                        in_v.dedup();
                        // Random roots may land in V by chance.
                        for r in &in_v {
                            assert!(roots.contains(r));
                        }
                        roots.retain(|r| eval(&f, *r, &gf) == 0);
                        assert_eq!(
                            deg_of(&g),
                            Some(roots.len()),
                            "gcd degree = #subspace roots"
                        );
                    }
                }
            }
        }
    }
}

/// Every element of `V`, as the oracle enumerates it.
fn span(basis: &[u64]) -> Vec<u64> {
    (0..1u64 << basis.len())
        .map(|idx| {
            (0..basis.len())
                .filter(|&j| (idx >> j) & 1 == 1)
                .fold(0, |a, j| a ^ basis[j])
        })
        .collect()
}

/// The generic definition with nothing clever: every ordered 4-tuple
/// of `V` and every `e₁, e₂` in the whole field, found by scanning the
/// field (no quadratic solving).  Tiny fields only.
fn brute_force(basis: &[u64], xr: u64, b: u64, gf: &Gf2) -> Vec<[u64; 4]> {
    let v = span(basis);
    let size = 1u64 << gf.n;
    let scan = |x1: u64, x2: u64| -> Vec<u64> {
        (0..size).filter(|&e| s3(x1, x2, e, b, gf) == 0).collect()
    };
    let mut memo: std::collections::HashMap<(u64, u64), Vec<u64>> = Default::default();
    let mut out = BTreeSet::new();
    for &o1 in &v {
        for &o2 in &v {
            let e1s = memo.entry((o1, o2)).or_insert_with(|| scan(o1, o2)).clone();
            for &o3 in &v {
                for &e1 in &e1s {
                    let e2s = memo.entry((e1, o3)).or_insert_with(|| scan(e1, o3)).clone();
                    for &o4 in &v {
                        if e2s.iter().any(|&e2| s3(e2, o4, xr, b, gf) == 0) {
                            let mut m = [o1, o2, o3, o4];
                            m.sort_unstable();
                            out.insert(m);
                        }
                    }
                }
            }
        }
    }
    out.into_iter().collect()
}

/// A target with a planted decomposition: four random subspace
/// abscissae pushed through a rational chain, retried until one exists.
fn planted_target(v: &[u64], b: u64, gf: &Gf2, s: &mut u64) -> Option<(u64, [u64; 4])> {
    for _ in 0..200 {
        let o: Vec<u64> = (0..4)
            .map(|_| v[(xorshift(s) >> 11) as usize % v.len()])
            .collect();
        let Some(e1) = s3_root(o[0], o[1], b, gf, xorshift(s)) else {
            continue;
        };
        let Some(e2) = s3_root(e1, o[2], b, gf, xorshift(s)) else {
            continue;
        };
        let Some(xr) = s3_root(e2, o[3], b, gf, xorshift(s)) else {
            continue;
        };
        let mut m = [o[0], o[1], o[2], o[3]];
        m.sort_unstable();
        return Some((xr, m));
    }
    None
}

/// Every candidate the oracle considers is the chain check's to accept,
/// so on tiny fields compare against the definition itself, with both
/// the carry-less and portable multiplies: random, planted, zero and
/// in-subspace targets, random and low-order bases, several `b`.
#[test]
fn linearised_matches_brute_force_on_tiny_fields() {
    let mut s = 0xB0F0_0000_0000_0005u64;
    let mut planted_hits = 0;
    let mut nonempty = 0;
    for (n, l) in [
        (3u32, 1u32),
        (3, 2),
        (4, 2),
        (5, 1),
        (5, 2),
        (6, 2),
        (6, 3),
        (7, 2),
    ] {
        for portable in [false, true] {
            let gf = field(n, portable);
            for round in 0..4 {
                let b = if round == 0 {
                    1
                } else {
                    (xorshift(&mut s) & gf.mask).max(1)
                };
                let basis = if round % 2 == 0 {
                    (0..l).map(|i| 1u64 << i).collect()
                } else {
                    random_basis(l, &gf, &mut s)
                };
                let oracle = TripleOracle::new(&basis, b, &gf);
                let mut targets = vec![0, 1, gf.mask, oracle.span[oracle.span.len() - 1]];
                targets.extend((0..3).map(|_| xorshift(&mut s) & gf.mask));
                let planted = planted_target(&oracle.span, b, &gf, &mut s);
                targets.extend(planted.map(|(xr, _)| xr));
                for xr in targets {
                    let want = brute_force(&basis, xr, b, &gf);
                    let (got, ctr) = oracle.decompose_all(xr, &gf);
                    assert_eq!(got, want, "n={n} l={l} b={b} xr={xr} portable={portable}");
                    let c = 1u64 << l;
                    assert_eq!(ctr.triples, c * (c + 1) * (c + 2) / 6);
                    assert_eq!(ctr.candidates - ctr.chain_rejected, got.len() as u64);
                    nonempty += usize::from(!got.is_empty());
                    if let Some((pxr, m)) = planted {
                        if pxr == xr {
                            assert!(got.contains(&m));
                            planted_hits += 1;
                        }
                    }
                    let (first, triples) = oracle.decompose(xr, &gf);
                    assert_eq!(first.is_some(), !got.is_empty());
                    if let Some(w) = first {
                        assert!(got.contains(&w));
                        assert!(triples <= ctr.triples);
                    } else {
                        assert_eq!(triples, ctr.triples);
                    }
                }
            }
        }
    }
    assert!(planted_hits > 20, "{planted_hits}");
    assert!(nonempty > 40, "{nonempty}");
}

/// **The differential test against the generic `m = 4` path**: the
/// chained `S₃` system solved for every root by the Boolean solver,
/// projected to the summands.  Same list, element for element and in
/// the same order, on random and planted targets, refuted targets,
/// `x_R = 0` and `x_R ∈ V`, random and low-order bases, boundary `l`
/// (1 and the largest the generic solve finishes quickly at), several
/// `b`.
#[test]
fn linearised_matches_the_generic_chain() {
    let mut s = 0x6E4E_0000_0000_0006u64;
    let mut nonempty = 0;
    let mut empty = 0;
    let mut cases = 0;
    for (n, l) in [
        (5u32, 1u32),
        (5, 2),
        (6, 2),
        (7, 1),
        (7, 2),
        (8, 2),
        (9, 2),
        (9, 3),
        (10, 2),
    ] {
        let gf = field(n, false);
        for round in 0..3 {
            let b = if round == 0 {
                1
            } else {
                (xorshift(&mut s) & gf.mask).max(1)
            };
            let basis = if round == 1 {
                (0..l).map(|i| 1u64 << i).collect()
            } else {
                random_basis(l, &gf, &mut s)
            };
            let oracle = TripleOracle::new(&basis, b, &gf);
            let mut targets = vec![0, oracle.span[1]];
            targets.extend((0..2).map(|_| xorshift(&mut s) & gf.mask));
            if let Some((xr, _)) = planted_target(&oracle.span, b, &gf, &mut s) {
                targets.push(xr);
            }
            for xr in targets {
                let (want, _) = decompose_all_generic(&basis, xr, b, &gf, usize::MAX)
                    .expect("the generic system builds and finishes");
                let (got, _) = oracle.decompose_all(xr, &gf);
                assert_eq!(got, want, "n={n} l={l} b={b} xr={xr}");
                if got.is_empty() {
                    empty += 1;
                } else {
                    nonempty += 1;
                }
                cases += 1;
                // Explicit dispatch: every route agrees.
                for path in [M4Path::Auto, M4Path::Linearised, M4Path::Generic] {
                    let o = decompose_all_m4(&basis, xr, b, &gf, path, usize::MAX);
                    assert_eq!(o.decompositions.as_ref(), Some(&want), "{path:?}");
                    let ran = if path == M4Path::Generic {
                        M4Path::Generic
                    } else {
                        M4Path::Linearised
                    };
                    assert_eq!(o.path, ran);
                }
            }
        }
    }
    assert!(
        nonempty >= 15 && empty >= 15,
        "{nonempty} decomposable, {empty} refuted of {cases}"
    );
}

/// The resultant degenerates (degree below 8, or vanishing) on some
/// triples; those take the generic remainder route.  Make sure the
/// tiny-field tests actually exercised it, and that it agrees with
/// enumeration of the fourth summand on every triple of a small field.
#[test]
fn low_degree_resultants_are_covered_and_exact() {
    let mut s = 0x10DE_6000_0000_0007u64;
    let mut low = 0u64;
    for n in [3u32, 4, 5, 6, 7] {
        let gf = field(n, false);
        for _ in 0..4 {
            let b = (xorshift(&mut s) & gf.mask).max(1);
            let l = 2.min(n - 1);
            let basis = random_basis(l, &gf, &mut s);
            let oracle = TripleOracle::new(&basis, b, &gf);
            for xr in 0..=gf.mask {
                let (_, ctr) = oracle.decompose_all(xr, &gf);
                low += ctr.low_degree;
                // Per triple: the candidates are the subspace roots of R.
                for (i1, &x1) in oracle.span.iter().enumerate() {
                    for (i2, &x2) in oracle.span.iter().enumerate().skip(i1) {
                        for &x3 in oracle.span.iter().skip(i2) {
                            let r = resultant(x1, x2, x3, xr, b, &gf);
                            let Some(d) = deg_of(&r) else { continue };
                            if d == 0 {
                                continue;
                            }
                            let inv = gf.inv(r[d]);
                            let f: Vec<u64> = r[..=d].iter().map(|&c| gf.mul(c, inv)).collect();
                            let mut fp = [0u64; OCT + 1];
                            fp[..=d].copy_from_slice(&f);
                            let g = gcd9(&fp, &lv_mod_generic(&f, d, &oracle.lv, &gf), &gf);
                            let by_gcd: Vec<u64> = oracle
                                .span
                                .iter()
                                .copied()
                                .filter(|&t| deg_of(&g).unwrap_or(0) > 0 && eval(&g, t, &gf) == 0)
                                .collect();
                            let by_eval: Vec<u64> = oracle
                                .span
                                .iter()
                                .copied()
                                .filter(|&t| eval(&r, t, &gf) == 0)
                                .collect();
                            assert_eq!(by_gcd, by_eval, "n={n} xr={xr} triple=({x1},{x2},{x3})");
                        }
                    }
                }
            }
        }
    }
    assert!(low > 0, "no degenerate resultant was exercised");
}

/// Portable and carry-less builds return the same decompositions and
/// counters at a size the generic chain cannot reach (`4l + 2n > 64`).
#[test]
fn dispatched_and_portable_triple_loops_agree() {
    let mut s = 0xD15B_0000_0000_0008u64;
    for (n, l) in [(16u32, 4u32), (23, 5)] {
        let fast = field(n, false);
        let slow = field(n, true);
        let basis = random_basis(l, &fast, &mut s);
        let b = (xorshift(&mut s) & fast.mask).max(1);
        let a = TripleOracle::new(&basis, b, &fast);
        let c = TripleOracle::new(&basis, b, &slow);
        for _ in 0..3 {
            let xr = xorshift(&mut s) & fast.mask;
            assert_eq!(a.decompose_all(xr, &fast), c.decompose_all(xr, &slow));
            assert_eq!(a.decompose(xr, &fast), c.decompose(xr, &slow));
        }
        assert!(decompose_all_generic(&basis, 0, b, &fast, 1).is_none() || 4 * l + 2 * n <= 64);
    }
}

/// `Auto` takes the linearised route only where it is safe and bounded:
/// a dependent basis (which [`TripleOracle::new`] rejects) goes to the
/// generic chain and returns its answer, and so does a factor base past
/// [`AUTO_LINEARISED_MAX_DIM`].
#[test]
fn auto_declines_dependent_and_oversized_bases() {
    let gf = field(7, false);
    for basis in [vec![3u64, 5, 6], vec![1, 1], vec![0, 2]] {
        let want = decompose_all_m4(&basis, 1, 1, &gf, M4Path::Generic, usize::MAX);
        assert!(want.decompositions.is_some(), "{basis:?}");
        let got = decompose_all_m4(&basis, 1, 1, &gf, M4Path::Auto, usize::MAX);
        assert_eq!(got.path, M4Path::Generic, "{basis:?}");
        assert_eq!(got.decompositions, want.decompositions, "{basis:?}");
    }
    let gf = field(13, false);
    let mut s = 0xCA90_0000_0000_0009u64;
    let l = AUTO_LINEARISED_MAX_DIM as u32 + 1;
    let basis = random_basis(l, &gf, &mut s);
    let o = decompose_all_m4(&basis, 1, 1, &gf, M4Path::Auto, usize::MAX);
    assert_eq!(o.path, M4Path::Generic);
    assert!(
        o.decompositions.is_none(),
        "4l + 2n is past the solver's cap"
    );
}
