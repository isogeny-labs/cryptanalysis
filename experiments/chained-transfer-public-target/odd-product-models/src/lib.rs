//! Fresh typed source and all actual HLP models. Protocol56fbbb precedes code.
//! Original field, polynomial, elliptic and plane-Picard engines are dependencies.
#![allow(dead_code, static_mut_refs)]
use chained_n4_completed_v2::AdapterV2;
pub mod source;
use chained_original_smith_engine::original;
use ghs_original_engines::{cover, pic};
use isogeny_algos::{
    curve::{self, Pt},
    field::{Field, Rng},
    fpr::{FpR, ER},
    poly,
};
use serde_json::{json, Value};
pub use source::SourceE;
use std::collections::BTreeSet;
pub mod even;

pub type Matrix = [[ER; 3]; 3];
pub fn k(n: u64) -> ER {
    let mut x = [0; 16];
    x[0] = n % 223;
    x
}
pub fn er(x: [u64; 3]) -> ER {
    let mut a = [0; 16];
    a[..3].copy_from_slice(&x);
    a
}
pub fn three(x: ER) -> [u64; 3] {
    assert!(x[3..].iter().all(|&v| v == 0));
    x[..3].try_into().unwrap()
}
pub fn six(x: ER) -> [u64; 6] {
    assert!(x[6..].iter().all(|&v| v == 0));
    x[..6].try_into().unwrap()
}
fn pairing(a: u8, b: u8) -> u32 {
    ((((a & 0x15) << 1) | ((a & 0x2a) >> 1)) & b).count_ones() & 1
}
fn frob_vector(x: u8) -> u8 {
    ((x << 2) & 63) | (x >> 4)
}
fn bits(v: &[u8]) -> u64 {
    v.iter().fold(0, |a, &v| a | (1u64 << v))
}
fn space_vectors(x: u64) -> Vec<u8> {
    (0..64).filter(|&i| x & (1u64 << i) != 0).collect()
}
fn span(g: [u8; 3]) -> u64 {
    bits(
        &(0..8)
            .map(|x| {
                g.iter()
                    .enumerate()
                    .fold(0, |a, (i, &b)| a ^ if x & (1 << i) != 0 { b } else { 0 })
            })
            .collect::<Vec<_>>(),
    )
}
pub fn det(f: &FpR, m: &Matrix) -> ER {
    let a = f.mul(
        m[0][0],
        f.sub(f.mul(m[1][1], m[2][2]), f.mul(m[1][2], m[2][1])),
    );
    let b = f.mul(
        m[0][1],
        f.sub(f.mul(m[1][0], m[2][2]), f.mul(m[1][2], m[2][0])),
    );
    let c = f.mul(
        m[0][2],
        f.sub(f.mul(m[1][0], m[2][1]), f.mul(m[1][1], m[2][0])),
    );
    f.add(f.sub(a, b), c)
}
pub fn adj(f: &FpR, m: &Matrix) -> Matrix {
    std::array::from_fn(|i| {
        std::array::from_fn(|j| {
            let rows: Vec<_> = (0..3).filter(|&x| x != j).collect();
            let cols: Vec<_> = (0..3).filter(|&x| x != i).collect();
            let v = f.sub(
                f.mul(m[rows[0]][cols[0]], m[rows[1]][cols[1]]),
                f.mul(m[rows[0]][cols[1]], m[rows[1]][cols[0]]),
            );
            if (i + j) % 2 == 0 {
                v
            } else {
                f.neg(v)
            }
        })
    })
}
fn audit_adjugate(f: &FpR, m: &Matrix, q: &Matrix) {
    let d = det(f, m);
    for i in 0..3 {
        for j in 0..3 {
            let v = (0..3).fold(f.zero(), |v, k| f.add(v, f.mul(m[i][k], q[k][j])));
            assert_eq!(v, if i == j { d } else { f.zero() });
        }
    }
}
pub fn coefficients(f: &FpR, q: &Matrix) -> [ER; 6] {
    [
        q[0][0],
        q[1][1],
        q[2][2],
        f.mul(k(2), q[0][1]),
        f.mul(k(2), q[1][2]),
        f.mul(k(2), q[0][2]),
    ]
}
fn all_lagrangians() -> Vec<u64> {
    let basis = [3u8, 5, 15, 23, 63, 95];
    let mask = |v: u8| {
        basis.iter().enumerate().fold(0u8, |out, (i, &b)| {
            out ^ if v & (1 << i) != 0 { b } else { 0 }
        })
    };
    let mut inv = [255u8; 128];
    for v in 0..64 {
        assert_eq!(inv[mask(v) as usize], 255);
        inv[mask(v) as usize] = v;
    }
    for a in 0..64 {
        for b in 0..64 {
            assert_eq!(pairing(a, b), (mask(a) & mask(b)).count_ones() & 1);
        }
    }
    let mut out = BTreeSet::new();
    for (vs, _) in original::lagrangians() {
        let mut v: Vec<_> = vs
            .iter()
            .map(|&x| {
                let y = inv[x as usize];
                assert!(y < 64 && y != 0);
                y
            })
            .collect();
        v.push(0);
        v.sort();
        v.dedup();
        assert_eq!(v.len(), 8);
        for &x in &v {
            for &y in &v {
                assert_eq!(pairing(x, y), 0);
                assert!(v.contains(&(x ^ y)));
            }
        }
        assert!(out.insert(bits(&v)));
    }
    assert_eq!(out.len(), 135);
    out.into_iter().collect()
}
pub struct GluingModel {
    pub root_index: usize,
    pub sign_index: usize,
    pub root: ER,
    pub source_a: [ER; 3],
    pub source_b: [ER; 3],
    pub h: [ER; 3],
    pub d: [ER; 3],
    pub h_matrix: Matrix,
    pub q_matrix: Matrix,
    pub determinant: ER,
    pub factor: ER,
    pub square_root: Option<ER>,
    pub kernel_mask: u64,
    pub full_coefficients: [[u64; 3]; 15],
    pub normalized: [u32; 15],
    pub coefficient_scale: [u64; 3],
    pub p0: Option<[u32; 3]>,
    pub row: Value,
}
fn descend(a: &AdapterV2, q: &Matrix) -> ([[u64; 3]; 15], [u32; 15], [u64; 3]) {
    let f = &a.field;
    let ff = FpR::from_modulus(223, &[220, 0, 0, 1]);
    let cs = coefficients(&ff, q).map(three);
    let linear: Vec<cover::Poly3> = a
        .core
        .omi
        .iter()
        .map(|row| {
            [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
                .into_iter()
                .zip(row.iter().copied())
                .collect()
        })
        .collect();
    let mut full = cover::Poly3::new();
    for (ex, c) in [
        [4, 0, 0],
        [0, 4, 0],
        [0, 0, 4],
        [2, 2, 0],
        [0, 2, 2],
        [2, 0, 2],
    ]
    .into_iter()
    .zip(cs)
    {
        let mut term: cover::Poly3 = [((0, 0, 0), c)].into_iter().collect();
        for (axis, n) in ex.into_iter().enumerate() {
            for _ in 0..n {
                term = cover::poly3_mul(f, &term, &linear[axis]);
            }
        }
        full = cover::poly3_add(f, &full, &term);
    }
    let all: [_; 15] = pic::mons_of_degree(4)
        .iter()
        .map(|m| full.get(m).copied().unwrap_or([0; 3]))
        .collect::<Vec<_>>()
        .try_into()
        .unwrap();
    let scale = *all.iter().find(|&&x| x != [0; 3]).unwrap();
    let inverse = f.inv(&scale);
    let out = all.map(|x| {
        let y = f.mul(&x, &inverse);
        assert!(f.in_fq(&y), "full15coefficient descent failed");
        y[0] as u32
    });
    (all, out, scale)
}
fn eval(f: &FpR, cs: &[u32; 15], p: [u32; 3]) -> ER {
    pic::mons_of_degree(4)
        .iter()
        .zip(cs)
        .fold(f.zero(), |v, (&(x, y, z), &c)| {
            f.add(
                v,
                f.mul(
                    k(c as u64),
                    f.mul(
                        f.pow(k(p[0] as u64), x as u128),
                        f.mul(
                            f.pow(k(p[1] as u64), y as u128),
                            f.pow(k(p[2] as u64), z as u128),
                        ),
                    ),
                ),
            )
        })
}
fn canonical_point(cs: &[u32; 15]) -> Option<[u32; 3]> {
    let f = FpR::new(223, 1);
    for x in 0..223 {
        for y in 0..223 {
            if f.is_zero(eval(&f, cs, [1, x, y])) {
                return Some([1, x, y]);
            }
        }
    }
    for y in 0..223 {
        if f.is_zero(eval(&f, cs, [0, 1, y])) {
            return Some([0, 1, y]);
        }
    }
    f.is_zero(eval(&f, cs, [0, 0, 1])).then_some([0, 0, 1])
}
fn ciani_value(f: &FpR, q: &Matrix, p: [ER; 3]) -> ER {
    let x = p.map(|x| f.mul(x, x));
    (0..3).fold(f.zero(), |v, i| {
        (0..3).fold(v, |v, j| f.add(v, f.mul(q[i][j], f.mul(x[i], x[j]))))
    })
}
fn moore_point(f: &FpR, a: &AdapterV2, p: [u32; 3]) -> [ER; 3] {
    std::array::from_fn(|i| {
        (0..3).fold(f.zero(), |v, j| {
            f.add(v, f.mul(er(a.core.omi[i][j]), k(p[j] as u64)))
        })
    })
}
fn quotient(f: &FpR, q: &Matrix, i: usize) -> (ER, ER, ER, ER, ER) {
    let j = (i + 1) % 3;
    let l = (i + 2) % 3;
    let a = q[i][i];
    let b = q[j][j];
    let c = q[l][l];
    let d = f.mul(k(2), q[i][j]);
    let e = f.mul(k(2), q[j][l]);
    let g = f.mul(k(2), q[i][l]);
    let alpha = f.sub(f.mul(d, d), f.mul(k(4), f.mul(a, b)));
    let beta = f.sub(f.mul(k(2), f.mul(d, g)), f.mul(k(4), f.mul(a, e)));
    let gamma = f.sub(f.mul(g, g), f.mul(k(4), f.mul(a, c)));
    let ax = f.neg(f.mul(k(2), beta));
    let bx = f.sub(f.mul(beta, beta), f.mul(k(4), f.mul(alpha, gamma)));
    assert_eq!(
        ax,
        f.sub(f.mul(k(8), f.mul(a, e)), f.mul(k(4), f.mul(d, g)))
    );
    assert_eq!(bx, f.neg(f.mul(k(64), f.mul(a, det(f, q)))));
    (alpha, beta, gamma, ax, bx)
}
fn point_index(roots: &[ER], x: ER) -> u8 {
    roots.iter().position(|&r| r == x).unwrap() as u8 + 1
}
pub fn construct_all(checked: &SourceE, a: &AdapterV2) -> (Vec<GluingModel>, Value) {
    let f = &checked.independent_field;
    let f6 = FpR::from_modulus(223, &[220, 0, 0, 0, 0, 0, 1]);
    assert_eq!(f6.mul(f6.gen(), f6.gen()), even::lift6(f.gen()));
    for x in [f.one(), f.gen(), f.mul(f.gen(), f.gen())] {
        assert_eq!(f6.frobenius(even::lift6(x)), even::lift6(f.frobenius(x)));
    }
    let ec = &checked.independent_curve;
    let mut rng = Rng::new(0x6011);
    let mut roots = poly::roots(f, &vec![ec.b, ec.a, f.zero(), f.one()], &mut rng);
    roots.sort();
    roots.dedup();
    assert_eq!(roots.len(), 3);
    let source: Vec<_> = std::iter::once(Pt::Inf)
        .chain(roots.iter().map(|&x| Pt::Aff(x, f.zero())))
        .collect();
    let mut source_table = vec![];
    for p in &source {
        assert!(curve::on_curve(f, ec, p));
        assert_eq!(curve::pmul(f, ec, p, 2), Pt::Inf);
        source_table.push(
            source
                .iter()
                .map(|q| {
                    source
                        .iter()
                        .position(|x| *x == curve::padd(f, ec, p, q))
                        .unwrap()
                })
                .collect::<Vec<_>>(),
        );
    }
    assert_eq!(
        source_table,
        vec![
            vec![0, 1, 2, 3],
            vec![1, 0, 3, 2],
            vec![2, 3, 0, 1],
            vec![3, 2, 1, 0]
        ]
    );
    let lags = all_lagrangians();
    let stable: Vec<_> = lags
        .iter()
        .copied()
        .filter(|&lag| {
            space_vectors(lag)
                .iter()
                .all(|&v| lag & (1u64 << frob_vector(v)) != 0)
        })
        .collect();
    let transvection = |v: u8| v ^ if pairing(v, 1) != 0 { 1 } else { 0 };
    let transvection_count = lags
        .iter()
        .filter(|&&lag| {
            space_vectors(lag)
                .iter()
                .all(|&v| lag & (1u64 << transvection(v)) != 0)
        })
        .count();
    assert_eq!(transvection_count, 15);
    let product: BTreeSet<_> = (1..4).map(|q| span([q, q << 2, q << 4])).collect();
    let mut split = 0;
    let mut all_rows = vec![];
    for &lag in &lags {
        let vs = space_vectors(lag);
        let intersections: [Vec<_>; 3] = std::array::from_fn(|i| {
            vs.iter()
                .copied()
                .filter(|&v| v != 0 && v & !(3 << (2 * i)) == 0)
                .collect()
        });
        let is_split = intersections.iter().any(|x| !x.is_empty());
        if is_split {
            split += 1;
        }
        let is_stable = stable.contains(&lag);
        let tuples: Vec<_> = vs
            .iter()
            .map(|&v| {
                std::array::from_fn::<_, 3, _>(|i| {
                    let id = (v >> (2 * i)) & 3;
                    if id == 0 {
                        None
                    } else {
                        let mut x = roots[id as usize - 1];
                        for _ in 0..i {
                            x = f.frobenius(x);
                        }
                        Some(three(x))
                    }
                })
            })
            .collect();
        all_rows.push(json!({"mask":lag,"vectors":vs,"stable":is_stable,"has_single_factor_subspace":is_split,"block_intersections":intersections,"actual_three_factor_2torsion_x_coordinates":tuples}));
    }
    assert_eq!(split, 81);
    assert!(product.iter().all(|x| stable.contains(x)));
    let mut models = vec![];
    let mut gluing = BTreeSet::new();
    for (ri, &root) in roots.iter().enumerate() {
        let aa = f.mul(k(3), root);
        let bb = f.add(f.mul(k(3), f.mul(root, root)), ec.a);
        let av = [aa, f.frobenius(aa), f.frobenius(f.frobenius(aa))];
        let bv = [bb, f.frobenius(bb), f.frobenius(f.frobenius(bb))];
        let delta: [ER; 3] =
            std::array::from_fn(|i| f.sub(f.mul(av[i], av[i]), f.mul(k(4), bv[i])));
        assert!(delta.iter().all(|&x| !f.is_zero(x)));
        let target = f.div(f.mul(delta[1], delta[2]), delta[0]);
        let mut signs = poly::roots(f, &vec![f.neg(target), f.zero(), f.one()], &mut rng);
        signs.sort();
        signs.dedup();
        assert_eq!(signs.len(), 2);
        for (si, &h1) in signs.iter().enumerate() {
            eprintln!("gluing candidate root={ri} sign={si} h1={:?}", three(h1));
            let h = [h1, f.div(delta[2], h1), f.div(delta[1], h1)];
            for i in 0..3 {
                assert_eq!(f.mul(h[(i + 1) % 3], h[(i + 2) % 3]), delta[i]);
                assert_eq!(f.frobenius(h[i]), h[(i + 1) % 3]);
            }
            let hmat = [
                [h[0], f.neg(av[2]), f.neg(av[1])],
                [f.neg(av[2]), h[1], f.neg(av[0])],
                [f.neg(av[1]), f.neg(av[0]), h[2]],
            ];
            let q = adj(f, &hmat);
            let determinant = det(f, &hmat);
            audit_adjugate(f, &hmat, &q);
            assert_eq!(det(f, &q), f.mul(determinant, determinant));
            assert_eq!(
                adj(f, &q),
                hmat.map(|row| row.map(|x| f.mul(determinant, x)))
            );
            let hp = f.mul(h[0], f.mul(h[1], h[2]));
            let r = f.neg(hp);
            let mut ds = poly::roots(f, &vec![f.neg(delta[0]), f.zero(), f.one()], &mut rng);
            ds.sort();
            assert_eq!(ds.len(), 2);
            let d1 = *ds
                .iter()
                .find(|&&d| f.mul(d, f.mul(f.frobenius(d), f.frobenius(f.frobenius(d)))) == r)
                .unwrap();
            let d = [d1, f.frobenius(d1), f.frobenius(f.frobenius(d1))];
            for i in 0..3 {
                assert_eq!(f.mul(d[i], d[i]), delta[i]);
                assert_eq!(q[i][i], f.neg(f.mul(k(4), bv[i])));
            }
            let sum = (0..3).fold(f.neg(f.one()), |x, i| {
                f.add(x, f.div(f.mul(av[i], av[i]), delta[i]))
            });
            let twist = f.sub(
                f.mul(r, sum),
                f.mul(k(2), f.mul(av[0], f.mul(av[1], av[2]))),
            );
            assert_eq!(twist, determinant);
            assert_eq!(f.frobenius(determinant), determinant);
            assert!(three(determinant)[1..].iter().all(|&x| x == 0));
            let hlp_diag = bv;
            let mut hlp = [[f.zero(); 3]; 3];
            for i in 0..3 {
                hlp[i][i] = hlp_diag[i];
            }
            for i in 0..3 {
                for j in i + 1..3 {
                    let l = 3 - i - j;
                    let cross = f.div(
                        f.add(f.neg(f.mul(av[i], av[j])), f.div(f.mul(av[l], r), delta[l])),
                        k(2),
                    );
                    hlp[i][j] = f.div(cross, k(2));
                    hlp[j][i] = hlp[i][j];
                }
            }
            assert_eq!(hlp, q.map(|row| row.map(|x| f.div(f.neg(x), k(4)))));
            let qid = ri as u8 + 1;
            let px = f.add(root, f.div(f.neg(f.add(av[0], d[0])), k(2)));
            let pid = point_index(&roots, px);
            assert_ne!(qid, pid);
            let rid = qid ^ pid;
            assert_eq!(
                curve::padd(f, ec, &source[qid as usize], &source[pid as usize]),
                source[rid as usize]
            );
            let kernel = bits(&[
                0,
                (qid << 2) | (qid << 4),
                qid | (qid << 4),
                qid | (qid << 2),
                pid | (pid << 2) | (pid << 4),
                pid | (rid << 2) | (rid << 4),
                rid | (pid << 2) | (rid << 4),
                rid | (rid << 2) | (pid << 4),
            ]);
            assert_eq!(space_vectors(kernel).len(), 8);
            assert!(stable.contains(&kernel));
            assert!(gluing.insert(kernel));
            assert!(!product.contains(&kernel));
            let factor = f.mul(k(16), determinant);
            let square_root = if f.is_zero(factor) {
                None
            } else {
                let mut rs = poly::roots(f, &vec![f.neg(factor), f.zero(), f.one()], &mut rng);
                rs.sort();
                rs.first().copied()
            };
            let fp = FpR::new(223, 1);
            let is_square_fp = f.is_zero(factor) || fp.pow(k(three(factor)[0]), 111) == fp.one();
            assert_eq!(square_root.is_some(), is_square_fp && !f.is_zero(factor));
            let cs = coefficients(f, &q);
            let mut factors = cs[..3].to_vec();
            for i in 0..3 {
                let j = (i + 1) % 3;
                let l = (i + 2) % 3;
                let cross = f.mul(k(2), q[i][j]);
                let disc = f.sub(f.mul(cross, cross), f.mul(k(4), f.mul(q[i][i], q[j][j])));
                assert_eq!(disc, f.neg(f.mul(k(4), f.mul(determinant, h[l]))));
                factors.push(disc);
            }
            factors.push(det(f, &q));
            let smooth = factors.iter().all(|&x| !f.is_zero(x));
            let (full, normalized, coefficient_scale) = descend(a, &q);
            assert_eq!(pic::smoothness_certificate(223, &normalized), smooth);
            let mut points = vec![];
            let mut quotient_rows = vec![];
            let mut p0 = None;
            if smooth {
                let base = canonical_point(&normalized).unwrap();
                let picard = pic::PlaneQuartic::new(223, normalized, base).unwrap();
                points = picard.rational_points_bruteforce();
                assert_eq!(points.first(), Some(&base));
                p0 = Some(base);
                let origin = picard.point_class(base);
                assert!(picard.is_zero(&origin));
                assert!(picard.is_zero(&picard.add(&origin, &origin)));
                for &w in &points {
                    let p = moore_point(f, a, w);
                    assert!(f.is_zero(ciani_value(f, &q, p)));
                    assert!(p.iter().all(|&x| !f.is_zero(x)));
                }
            }
            for i in 0..3 {
                let (alpha, beta, gamma, ax, bx) = quotient(f, &q, i);
                assert_eq!(ax, f.mul(factor, av[i]));
                assert_eq!(bx, f.mul(f.mul(factor, factor), bv[i]));
                for &w in &points {
                    let p = moore_point(f, a, w);
                    let j = (i + 1) % 3;
                    let l = (i + 2) % 3;
                    let t = f.div(p[j], p[l]);
                    let u = f.div(p[i], p[l]);
                    let v = f.add(
                        f.mul(k(2), f.mul(q[i][i], f.mul(u, u))),
                        f.add(
                            f.mul(k(2), f.mul(q[i][j], f.mul(t, t))),
                            f.mul(k(2), q[i][l]),
                        ),
                    );
                    assert_eq!(
                        f.mul(v, v),
                        f.add(
                            f.mul(alpha, f.pow(t, 4)),
                            f.add(f.mul(beta, f.mul(t, t)), gamma)
                        )
                    );
                }
                let coordinate_controls = if smooth {
                    even::audit_quotient(
                        f,
                        &f6,
                        a,
                        checked,
                        &q,
                        &points,
                        p0.unwrap(),
                        factor,
                        square_root,
                        root,
                        i,
                        (alpha, beta, gamma, ax, bx),
                        &mut rng,
                    )
                } else {
                    json!(null)
                };
                quotient_rows.push(json!({"factor":i,"alpha_beta_gamma":[three(alpha),three(beta),three(gamma)],"jacobian_AX_BX":[three(ax),three(bx)],"D_times_original_A_Dsquare_times_B":true,"all_rational_point_doublecover_equations":points.len(),"Fp6_coordinate_controls":coordinate_controls}));
            }
            let row = json!({"root_index":ri,"sign_index":si,"original_root":three(root),"original_A":av.map(three),"original_B":bv.map(three),"Delta":delta.map(three),"h":h.map(three),"d":d.map(three),"R":three(r),"H":hmat.map(|row|row.map(three)),"Q":q.map(|row|row.map(three)),"T_equals_detH":three(determinant),"D":three(factor),"D_square_in_Fp_and_K":is_square_fp,"sqrt_D_in_K":square_root.map(three),"kernel_mask":kernel,"actual_local_Q_P_R_indices":[qid,pid,rid],"full15_K_coefficients":full,"coefficient_scale":coefficient_scale,"normalized_Fp_coefficients":normalized,"smooth":smooth,"seven_smoothness_factors":factors.into_iter().map(three).collect::<Vec<_>>(),"original_smoothness_certificate_agrees":true,"P0":p0,"all_rational_points":points,"quotients":quotient_rows,"eligible_for_supplied_source_maps":smooth&&square_root.is_some(),"status":if f.is_zero(determinant){"Tzero;hyperellipticmodelrequired"}else if square_root.is_none(){"nonsquaretwist;notsuppliedsource"}else{"smoothsquarecandidate;actualmapsrequired"},"same_normalized_array_as_original":checked.reference_quartic.map(|old|normalized==old),"endpoint_isomorphism_distinctness":"not established by coefficient arrays"});
            models.push(GluingModel {
                root_index: ri,
                sign_index: si,
                root,
                source_a: av,
                source_b: bv,
                h,
                d,
                h_matrix: hmat,
                q_matrix: q,
                determinant,
                factor,
                square_root,
                kernel_mask: kernel,
                full_coefficients: full,
                normalized,
                coefficient_scale,
                p0,
                row,
            });
        }
    }
    let combined: BTreeSet<_> = product.union(&gluing).copied().collect();
    assert_eq!(combined, stable.iter().copied().collect());
    assert_eq!(models.len(), 6);
    let unique: BTreeSet<_> = models.iter().map(|m| m.normalized).collect();
    let summary = json!({"actual_source_2torsion_roots":roots.into_iter().map(three).collect::<Vec<_>>(),"actual_source_addition_table":source_table,"all135_kernels":all_rows,"original_total_kernels":lags.len(),"original_split_kernels":split,"original_non_split_kernels":135-split,"stable_count":stable.len(),"stable_product_masks":product,"stable_gluing_masks":gluing,"all_stable_equal_whole_explicit_product_and_HLP_sets":true,"identity_control":135,"transvection_control":transvection_count,"all4096_pairings":true,"Frobenius_action":"cyclicthree2blocks;actualconjugatecoordinates","models":models.len(),"distinct_normalized_coefficient_arrays":unique.len(),"scope":"producttorsionandclassicalmodels;notactualnewJacobianhomomorphism/endpointdistinction/advantage"});
    (models, summary)
}

#[cfg(test)]
mod tests;
