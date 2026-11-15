//! Actual q223 bitangent coordinates. Prospective plan361ee8 precedes code.
//! Only original FpR, polynomial and model engines perform field arithmetic.
#![allow(dead_code, static_mut_refs)]

#[cfg(test)]
mod tests {
    use chained_n4_completed_v2::AdapterV2;
    use chained_n4_public_target::CheckedInstance;
    use ghs_original_engines::{cover, pic};
    use isogeny_algos::{
        field::{Field, Rng},
        fpr::{FpR, ER},
        poly,
    };
    use serde_json::json;
    use std::collections::BTreeMap;

    type P = Vec<ER>;
    type Line = [ER; 3];
    fn k(n: u64) -> ER {
        let mut x = [0; 16];
        x[0] = n % 223;
        x
    }
    fn lift(x: [u64; 3]) -> ER {
        let mut a = [0; 16];
        a[0] = x[0];
        a[2] = x[1];
        a[4] = x[2];
        a
    }
    fn six(x: ER) -> [u64; 6] {
        assert!(x[6..].iter().all(|&a| a == 0));
        x[..6].try_into().unwrap()
    }
    fn add(f: &FpR, a: &P, b: &P) -> P {
        poly::add(f, a, b)
    }
    fn sub(f: &FpR, a: &P, b: &P) -> P {
        poly::sub(f, a, b)
    }
    fn mul(f: &FpR, a: &P, b: &P) -> P {
        poly::mul(f, a, b)
    }
    fn scale(f: &FpR, a: &P, b: ER) -> P {
        poly::scale(f, a, b)
    }
    fn sq(f: &FpR, a: &P) -> P {
        mul(f, a, a)
    }
    fn con(f: &FpR, a: ER) -> P {
        poly::constant(f, a)
    }
    fn eval(f: &FpR, a: &P, x: ER) -> ER {
        a.iter().rev().fold(f.zero(), |v, &c| f.add(f.mul(v, x), c))
    }
    fn roots(f: &FpR, a: &P, rng: &mut Rng) -> Vec<ER> {
        assert!(
            !a.is_empty(),
            "zero elimination polynomial needs another construction"
        );
        let mut r = poly::roots(f, a, rng);
        r.sort();
        r.dedup();
        for &x in &r {
            assert!(f.is_zero(eval(f, a, x)));
        }
        r
    }
    fn square_roots(f: &FpR, x: ER, rng: &mut Rng) -> Vec<ER> {
        roots(f, &vec![f.neg(x), f.zero(), f.one()], rng)
    }
    fn normalized(f: &FpR, l: Line) -> Line {
        let first = l.iter().find(|&&x| !f.is_zero(x)).unwrap();
        l.map(|x| f.mul(x, f.inv(*first)))
    }
    fn restriction(f: &FpR, coefficients: &[ER; 15], p: Line, q: Line) -> P {
        let mut out = vec![];
        for (e, &c) in pic::mons_of_degree(4).into_iter().zip(coefficients) {
            let mut term = con(f, c);
            for (axis, exponent) in [e.0, e.1, e.2].into_iter().enumerate() {
                for _ in 0..exponent {
                    term = mul(f, &term, &vec![p[axis], q[axis]]);
                }
            }
            out = add(f, &out, &term);
        }
        out
    }
    fn chart(f: &FpR, l: Line) -> (Line, Line) {
        let pivot = l.iter().position(|&x| !f.is_zero(x)).unwrap();
        let axes: Vec<_> = (0..3).filter(|&i| i != pivot).collect();
        let mut p = [f.zero(); 3];
        let mut q = p;
        p[axes[0]] = f.one();
        q[axes[1]] = f.one();
        p[pivot] = f.neg(f.mul(l[axes[0]], f.inv(l[pivot])));
        q[pivot] = f.neg(f.mul(l[axes[1]], f.inv(l[pivot])));
        (p, q)
    }
    // A homogeneous binary quartic equals scale * Q^2. Q may vanish at infinity.
    fn square_certificate(f: &FpR, binary: &P) -> (ER, P) {
        let degree = binary.len().checked_sub(1).unwrap();
        assert!(degree <= 4 && degree.is_multiple_of(2));
        let c = binary[degree];
        let mut q = match degree {
            4 => {
                let b = f.mul(binary[3], f.inv(f.mul(k(2), c)));
                let a = f.mul(f.sub(f.mul(binary[2], f.inv(c)), f.mul(b, b)), f.inv(k(2)));
                vec![a, b, f.one()]
            }
            2 => vec![f.mul(binary[1], f.inv(f.mul(k(2), c))), f.one()],
            0 => vec![f.one()],
            _ => unreachable!(),
        };
        poly::trim(f, &mut q);
        assert_eq!(scale(f, &sq(f, &q), c), *binary);
        (c, q)
    }
    fn gradient_restriction(f: &FpR, c: &[ER; 15], axis: usize, p: Line, q: Line) -> P {
        let mut out = vec![];
        for (e, &coefficient) in pic::mons_of_degree(4).into_iter().zip(c) {
            let mut powers = [e.0, e.1, e.2];
            let n = powers[axis];
            if n == 0 {
                continue;
            }
            powers[axis] -= 1;
            let mut term = con(f, f.mul(k(n as u64), coefficient));
            for (i, exponent) in powers.into_iter().enumerate() {
                for _ in 0..exponent {
                    term = mul(f, &term, &vec![p[i], q[i]]);
                }
            }
            out = add(f, &out, &term);
        }
        out
    }
    fn reverse_homogeneous(f: &FpR, a: &P, degree: usize) -> P {
        assert!(a.len() <= degree + 1);
        let mut r = a.clone();
        r.resize(degree + 1, f.zero());
        r.reverse();
        poly::trim(f, &mut r);
        r
    }

    #[test]
    fn all_actual_bitangents_and_their_frobenius_permutation() {
        let checked = CheckedInstance::construct().unwrap();
        let a = AdapterV2::new(&checked).unwrap();
        let f = FpR::from_modulus(223, &[220, 0, 0, 0, 0, 0, 1]);
        let mut rng = Rng::new(0x5902);
        for i in 0..3 {
            let mut e = [0; 3];
            e[i] = 1;
            assert_eq!(f.frobenius(lift(e)), lift(a.field.frob(&e)));
            for j in 0..3 {
                let mut g = [0; 3];
                g[j] = 1;
                assert_eq!(f.mul(lift(e), lift(g)), lift(a.field.mul(&e, &g)));
            }
        }
        for i in 0..6 {
            let mut e = f.zero();
            e[i] = 1;
            let mut g = e;
            for _ in 0..6 {
                g = f.frobenius(g);
            }
            assert_eq!(e, g);
        }
        assert_eq!(f.pow(f.gen(), 6), k(3));
        let r = a.core.rmat;
        let diag = |j: usize| {
            a.field.sub(
                &a.field.mul(&r[1][j], &r[1][j]),
                &a.field.mul(&r[0][j], &r[2][j]),
            )
        };
        let cross = |i: usize, j: usize| {
            a.field.sub(
                &a.field.scale(&a.field.mul(&r[1][i], &r[1][j]), 2),
                &a.field.add(
                    &a.field.mul(&r[0][i], &r[2][j]),
                    &a.field.mul(&r[0][j], &r[2][i]),
                ),
            )
        };
        // Original Core columns are Z^2,X^2,Y^2.
        let coefficients = [
            diag(1),
            diag(2),
            diag(0),
            cross(1, 2),
            cross(2, 0),
            cross(0, 1),
        ];
        let [ca, cb, cc, cd, ce, cf] = coefficients.map(lift);
        let mut full = cover::Poly3::new();
        let linear: Vec<_> = a
            .core
            .omi
            .iter()
            .map(|row| {
                [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
                    .into_iter()
                    .zip(row.iter().copied())
                    .collect::<cover::Poly3>()
            })
            .collect();
        for (exponents, c) in [
            [4, 0, 0],
            [0, 4, 0],
            [0, 0, 4],
            [2, 2, 0],
            [0, 2, 2],
            [2, 0, 2],
        ]
        .into_iter()
        .zip(coefficients)
        {
            let mut term: cover::Poly3 = [((0, 0, 0), c)].into_iter().collect();
            for (axis, n) in exponents.into_iter().enumerate() {
                for _ in 0..n {
                    term = cover::poly3_mul(&a.field, &term, &linear[axis]);
                }
            }
            full = cover::poly3_add(&a.field, &full, &term);
        }
        let mons = pic::mons_of_degree(4);
        let lead = *full.get(&mons[1]).unwrap(); // Original normalized quartic first nonzero is index1.
        assert_eq!(checked.inst.f[0], 0);
        assert_eq!(checked.inst.f[1], 1);
        for (m, &c) in mons.iter().zip(&checked.inst.f) {
            assert_eq!(
                full.get(m).copied().unwrap_or([0; 3]),
                a.field.scale(&lead, c as u64)
            );
        }
        let original = checked.inst.f.map(|x| k(x as u64));
        let mut ciani = vec![];
        // y=v*z, y=u*x and x=w*z: all zero-coefficient families.
        for v2 in roots(
            &f,
            &vec![
                f.sub(f.mul(cf, cf), f.mul(k(4), f.mul(ca, cc))),
                f.sub(f.mul(k(2), f.mul(cd, cf)), f.mul(k(4), f.mul(ca, ce))),
                f.sub(f.mul(cd, cd), f.mul(k(4), f.mul(ca, cb))),
            ],
            &mut rng,
        ) {
            for v in square_roots(&f, v2, &mut rng) {
                ciani.push([f.zero(), f.one(), f.neg(v)]);
            }
        }
        for u2 in roots(
            &f,
            &vec![
                f.sub(f.mul(cf, cf), f.mul(k(4), f.mul(cc, ca))),
                f.sub(f.mul(k(2), f.mul(cf, ce)), f.mul(k(4), f.mul(cc, cd))),
                f.sub(f.mul(ce, ce), f.mul(k(4), f.mul(cc, cb))),
            ],
            &mut rng,
        ) {
            for u in square_roots(&f, u2, &mut rng) {
                ciani.push([f.neg(u), f.one(), f.zero()]);
            }
        }
        for w2 in roots(
            &f,
            &vec![
                f.sub(f.mul(ce, ce), f.mul(k(4), f.mul(cb, cc))),
                f.sub(f.mul(k(2), f.mul(cd, ce)), f.mul(k(4), f.mul(cb, cf))),
                f.sub(f.mul(cd, cd), f.mul(k(4), f.mul(cb, ca))),
            ],
            &mut rng,
        ) {
            for w in square_roots(&f, w2, &mut rng) {
                ciani.push([f.one(), f.zero(), f.neg(w)]);
            }
        }
        let zero_family_count = ciani.len();
        let u = poly::x_poly(&f);
        let big_a = vec![ca, cd, cb];
        let h = vec![cd, f.mul(k(2), cb)];
        let delta = f.sub(f.mul(k(4), f.mul(ca, cb)), f.mul(cd, cd));
        assert!(!f.is_zero(delta));
        let l = scale(&f, &vec![ca, f.zero(), f.neg(cb)], delta);
        let c = mul(
            &f,
            &big_a,
            &vec![
                f.sub(f.mul(k(2), f.mul(ce, ca)), f.mul(cd, cf)),
                f.sub(f.mul(cd, ce), f.mul(k(2), f.mul(cb, cf))),
            ],
        );
        let d = mul(&f, &big_a, &vec![cf, ce]);
        let e = sub(
            &f,
            &mul(&f, &big_a, &vec![cd, f.mul(k(6), cb)]),
            &mul(&f, &u, &sq(&f, &h)),
        );
        let expanded_l = add(
            &f,
            &sub(
                &f,
                &scale(&f, &sq(&f, &big_a), f.mul(k(4), cb)),
                &mul(&f, &mul(&f, &big_a, &h), &vec![cd, f.mul(k(6), cb)]),
            ),
            &mul(&f, &mul(&f, &u, &h), &sq(&f, &h)),
        );
        let expanded_c = sub(
            &f,
            &scale(&f, &sq(&f, &big_a), f.mul(k(2), ce)),
            &mul(&f, &mul(&f, &big_a, &h), &vec![cf, ce]),
        );
        assert_eq!(l, expanded_l);
        assert_eq!(c, expanded_c);
        let a3 = mul(&f, &sq(&f, &big_a), &big_a);
        let resultant = sub(
            &f,
            &scale(
                &f,
                &mul(
                    &f,
                    &a3,
                    &add(
                        &f,
                        &sub(
                            &f,
                            &scale(&f, &sq(&f, &l), cc),
                            &scale(&f, &mul(&f, &c, &l), ce),
                        ),
                        &scale(&f, &sq(&f, &c), cb),
                    ),
                ),
                k(4),
            ),
            &sq(&f, &sub(&f, &mul(&f, &d, &l), &mul(&f, &e, &c))),
        );
        let candidates = roots(&f, &resultant, &mut rng);
        let mut exceptional = 0;
        for uu in &candidates {
            let uu = *uu;
            if f.is_zero(uu) {
                continue;
            }
            let aa = eval(&f, &big_a, uu);
            if f.is_zero(aa) {
                continue;
            }
            let ll = eval(&f, &l, uu);
            let c0 = eval(&f, &c, uu);
            let dd = eval(&f, &d, uu);
            let ee = eval(&f, &e, uu);
            let vv = if !f.is_zero(ll) {
                vec![f.neg(f.mul(c0, f.inv(ll)))]
            } else if f.is_zero(c0) {
                exceptional += 1;
                let four_a3 = f.mul(k(4), f.pow(aa, 3));
                roots(
                    &f,
                    &vec![
                        f.sub(f.mul(four_a3, cc), f.mul(dd, dd)),
                        f.sub(f.mul(four_a3, ce), f.mul(k(2), f.mul(dd, ee))),
                        f.sub(f.mul(four_a3, cb), f.mul(ee, ee)),
                    ],
                    &mut rng,
                )
            } else {
                vec![]
            };
            for vv in vv {
                if f.is_zero(vv) {
                    continue;
                }
                assert!(f.is_zero(f.add(c0, f.mul(ll, vv))));
                let contact = f.sub(
                    f.mul(
                        f.mul(k(4), f.pow(aa, 3)),
                        f.add(cc, f.add(f.mul(ce, vv), f.mul(cb, f.mul(vv, vv)))),
                    ),
                    f.pow(f.add(dd, f.mul(ee, vv)), 2),
                );
                assert!(f.is_zero(contact));
                for root_u in square_roots(&f, uu, &mut rng) {
                    for root_v in square_roots(&f, vv, &mut rng) {
                        ciani.push([f.neg(root_u), f.one(), f.neg(root_v)]);
                    }
                }
            }
        }
        let mut lines = BTreeMap::new();
        for ciani_line in &ciani {
            let mut line = [f.zero(); 3];
            for j in 0..3 {
                for i in 0..3 {
                    line[j] = f.add(line[j], f.mul(ciani_line[i], lift(a.core.omi[i][j])));
                }
            }
            let line = normalized(&f, line);
            let (p, q) = chart(&f, line);
            let binary = restriction(&f, &original, p, q);
            let (scale_value, contact) = square_certificate(&f, &binary);
            let gradients: Vec<_> = (0..3)
                .map(|i| gradient_restriction(&f, &original, i, p, q))
                .collect();
            for i in 0..3 {
                for j in i + 1..3 {
                    let minor = sub(
                        &f,
                        &scale(&f, &gradients[i], line[j]),
                        &scale(&f, &gradients[j], line[i]),
                    );
                    assert!(poly::rem(&f, &minor, &contact).is_empty());
                    assert!(poly::rem(
                        &f,
                        &reverse_homogeneous(&f, &minor, 3),
                        &reverse_homogeneous(&f, &contact, 2)
                    )
                    .is_empty());
                }
            }
            let mut wrong = contact.clone();
            wrong[0] = f.add(wrong[0], f.one());
            assert_ne!(scale(&f, &sq(&f, &wrong), scale_value), binary);
            let value = json!({"W_line":line.map(six),"Ciani_line":ciani_line.map(six),"binary_quartic":binary.iter().copied().map(six).collect::<Vec<_>>(),"scale":six(scale_value),"contact_quadratic":contact.iter().copied().map(six).collect::<Vec<_>>(),"contact_affine_degree":contact.len()-1,"contact_roots_in_L":poly::roots(&f,&contact,&mut rng).len(),"both_chart_gradient_minor_remainders_zero":true,"wrong_contact_certificate_rejected":true});
            if let Some(old) = lines.insert(line, value.clone()) {
                assert_eq!(old, value);
            }
        }
        assert_eq!(zero_family_count, 12);
        assert_eq!(
            lines.len(),
            28,
            "actual distinctbitangent census incomplete"
        );
        let keys: Vec<_> = lines.keys().copied().collect();
        let permutation: Vec<_> = keys
            .iter()
            .map(|l| {
                let next = normalized(&f, l.map(|x| f.frobenius(x)));
                keys.binary_search(&next).expect("actualFrobeniusclosure")
            })
            .collect();
        let mut seen = vec![false; 28];
        let mut orbits = vec![];
        for i in 0..28 {
            if seen[i] {
                continue;
            }
            let mut orbit = vec![];
            let mut at = i;
            while !seen[at] {
                seen[at] = true;
                orbit.push(at);
                at = permutation[at];
            }
            assert_eq!(at, i);
            orbits.push(orbit);
        }
        let mut fixed = BTreeMap::new();
        for power in [1, 2, 3, 6] {
            fixed.insert(
                power,
                (0..28)
                    .filter(|&i| {
                        let mut j = i;
                        for _ in 0..power {
                            j = permutation[j];
                        }
                        j == i
                    })
                    .count(),
            );
        }
        assert_eq!(fixed[&6], 28);
        assert!(fixed[&2] < 28 && fixed[&3] < 28);
        println!(
            "N4_BITANGENT_MODEL {}",
            json!({"q":223,"extension_modulus":f.modulus(),"K_embedding":"z=w^2","Ciani_coefficients_a_b_c_d_e_f":coefficients,"original_quartic":checked.inst.f,"Moore_inverse":a.core.omi,"all15_transport_coefficients_match":true,"elimination_degree":resultant.len()-1,"distinct_U_candidates":candidates.len(),"exceptional_L0C0_candidates":exceptional,"zero_coefficient_lines":zero_family_count,"all_distinct_lines":lines.len()})
        );
        println!(
            "N4_BITANGENT_LINES {}",
            json!({"lines":lines.values().collect::<Vec<_>>(),"original_curve_square_and_gradient_checks_all":28,"wrong_contact_controls_rejected":28})
        );
        println!(
            "N4_BITANGENT_FROBENIUS {}",
            json!({"permutation":permutation,"orbits":orbits,"fixed_by_power":fixed,"minimal_full_line_field_degree":6,"actual_coordinates_not_just_characteristic_polynomial":true})
        );
        println!(
            "N4_BITANGENT_SCOPE {}",
            json!({"complete28_bridge":"standard smoothplanequartic oddtheta/bitangent theorem,char223;not formalizedhere","scope":"actualline/contact/Frobenius data;not a divisorclassbasis,Weilpairing,stablekernelcensus,newnondualmap,codomainorcostcomparison"})
        );
    }
}
