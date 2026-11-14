//! Fixed odd-prime symplectic-module controls. No geometric torsion points
//! or isogeny are constructed; coprime-factor geometry is a written input.
use crate::reference::FpPoly;
use num_bigint::BigUint;
use num_traits::Zero;
use std::collections::BTreeSet;

type Vector = [u64; 4];
type Plane = [Vector; 2];

fn planes(ell: u64) -> Vec<Plane> {
    assert!([3, 5, 7].contains(&ell));
    let mut out = vec![];
    for first in 0..4 {
        for second in first + 1..4 {
            let slots = (0..2)
                .flat_map(|row| {
                    (0..4)
                        .filter(move |col| {
                            *col > [first, second][row] && *col != first && *col != second
                        })
                        .map(move |col| (row, col))
                })
                .collect::<Vec<_>>();
            for mut encoding in 0..ell.pow(slots.len() as u32) {
                let mut plane = [[0_u64; 4]; 2];
                plane[0][first] = 1;
                plane[1][second] = 1;
                for (row, col) in &slots {
                    plane[*row][*col] = encoding % ell;
                    encoding /= ell;
                }
                out.push(plane);
            }
        }
    }
    assert_eq!(
        out.iter().copied().collect::<BTreeSet<_>>().len(),
        out.len()
    );
    out
}

fn contains(plane: &Plane, mut vector: Vector, ell: u64) -> bool {
    for row in plane {
        let pivot = row.iter().position(|c| *c != 0).unwrap();
        assert_eq!(row[pivot], 1);
        let scale = vector[pivot];
        for (c, r) in vector.iter_mut().zip(row) {
            *c = (*c + ell - scale * r % ell) % ell;
        }
    }
    vector == [0; 4]
}

fn pairing(a: &Vector, b: &Vector, ell: u64, ratio: u64) -> u64 {
    let first = (a[0] * b[1] + ell - a[1] * b[0] % ell) % ell;
    let second = (a[2] * b[3] + ell - a[3] * b[2] % ell) % ell;
    (first + ratio * second) % ell
}

fn frobenius(v: &Vector, p: u64, traces: [i64; 2], ell: u64) -> Vector {
    let mut out = [0; 4];
    for (i, trace) in traces.iter().enumerate() {
        let t = trace.rem_euclid(ell as i64) as u64;
        out[2 * i] = (ell - p % ell * v[2 * i + 1] % ell) % ell;
        out[2 * i + 1] = (v[2 * i] + t * v[2 * i + 1]) % ell;
    }
    out
}

#[test]
fn fixed_odd_prime_invariant_isotropic_planes() {
    for (p, traces, orders) in [(17, [-1, 3], [19, 15]), (101, [-7, -11], [109, 113])] {
        for (trace, order) in traces.iter().zip(orders) {
            assert_eq!(p as i64 + 1 - order as i64, *trace);
        }
        for (ell, all_count, isotropic_count) in [(3, 130, 40), (5, 806, 156), (7, 2850, 400)] {
            let q = BigUint::from(ell);
            let polynomials = traces.map(|t| {
                FpPoly::from_coeffs(
                    [p % ell, (-t).rem_euclid(ell as i64) as u64, 1]
                        .into_iter()
                        .map(BigUint::from)
                        .collect(),
                    q.clone(),
                )
            });
            let roots = polynomials.each_ref().map(|f| {
                (0..ell)
                    .filter(|x| f.eval(&BigUint::from(*x)).is_zero())
                    .collect::<Vec<_>>()
            });
            assert_eq!(polynomials[0].gcd(&polynomials[1]), FpPoly::one(q));
            let all = planes(ell);
            assert_eq!(all.len(), all_count);
            let expected = if roots.iter().any(Vec::is_empty) {
                0
            } else {
                assert!(
                    roots.iter().all(|r| r.len() == 2),
                    "positive control must be squarefree"
                );
                roots[0].len() * roots[1].len()
            };
            assert_eq!(expected, if p == 101 && ell == 7 { 4 } else { 0 });
            let mut actual = None;
            for ratio in 1..ell {
                let isotropic = all
                    .iter()
                    .filter(|plane| pairing(&plane[0], &plane[1], ell, ratio) == 0)
                    .collect::<Vec<_>>();
                assert_eq!(isotropic.len(), isotropic_count);
                let stable = isotropic
                    .iter()
                    .filter(|plane| {
                        plane
                            .iter()
                            .all(|v| contains(plane, frobenius(v, p, traces, ell), ell))
                    })
                    .count();
                assert_eq!(stable, expected);
                actual = Some(stable);
                for i in 0..4 {
                    for j in 0..4 {
                        let mut a = [0; 4];
                        let mut b = [0; 4];
                        a[i] = 1;
                        b[j] = 1;
                        assert_eq!(
                            pairing(
                                &frobenius(&a, p, traces, ell),
                                &frobenius(&b, p, traces, ell),
                                ell,
                                ratio
                            ),
                            p % ell * pairing(&a, &b, ell, ratio) % ell
                        );
                    }
                }
            }
            println!("F{p},ell{ell}: coprime factors{:?}/{:?},roots{roots:?},all2-planes{all_count},maximal-isotropic{isotropic_count},stable{} across all{} nonzero pairing-scale ratios; companion is a finite model,actual repeated Jordan type not assumed",polynomials[0].coeffs,polynomials[1].coeffs,actual.unwrap(),ell-1);
        }
    }
}
