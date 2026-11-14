//! Original FpR6 coordinate checks, including the actual affine origin.
use super::*;
pub fn lift6(x: ER) -> ER {
    let x = three(x);
    let mut out = [0; 16];
    out[0] = x[0];
    out[2] = x[1];
    out[4] = x[2];
    out
}
pub fn back6(x: ER) -> ER {
    assert!(
        x.iter()
            .enumerate()
            .all(|(i, &v)| i == 0 || i == 2 || i == 4 || v == 0),
        "actual-origin translation did not descend to K"
    );
    er([x[0], x[2], x[4]])
}
pub fn short_curve(f: &FpR, a2: ER, a4: ER) -> curve::Curve<ER> {
    curve::Curve::new(
        f.sub(a4, f.div(f.mul(a2, a2), k(3))),
        f.sub(
            f.div(f.mul(k(2), f.pow(a2, 3)), k(27)),
            f.div(f.mul(a2, a4), k(3)),
        ),
    )
}
#[allow(clippy::too_many_arguments)]
pub fn audit_quotient(
    f: &FpR,
    f6: &FpR,
    a: &AdapterV2,
    checked: &SourceE,
    q: &Matrix,
    points: &[[u32; 3]],
    p0: [u32; 3],
    factor: ER,
    square_root: Option<ER>,
    root: ER,
    i: usize,
    data: (ER, ER, ER, ER, ER),
    rng: &mut Rng,
) -> Value {
    let (alpha, beta, _gamma, ax, bx) = data;
    let mut roots6 = poly::roots(f6, &vec![f6.neg(lift6(alpha)), f6.zero(), f6.one()], rng);
    roots6.sort();
    assert_eq!(roots6.len(), 2);
    assert_eq!(roots6[0], f6.neg(roots6[1]));
    let ax6 = lift6(ax);
    let bx6 = lift6(bx);
    let ec6 = short_curve(f6, ax6, bx6);
    let shift = f6.div(ax6, k(3));
    let coords = |w| {
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
        (lift6(t), lift6(v))
    };
    let kappa = |s, t, v| {
        let x = f6.add(
            f6.mul(k(2), f6.mul(s, v)),
            f6.add(
                f6.mul(k(2), f6.mul(lift6(alpha), f6.mul(t, t))),
                lift6(beta),
            ),
        );
        assert!(!f6.is_zero(x));
        let y = f6.mul(k(2), f6.mul(s, f6.mul(x, t)));
        let p = Pt::Aff(f6.add(x, shift), y);
        assert!(curve::on_curve(f6, &ec6, &p));
        p
    };
    let (t0, v0) = coords(p0);
    let origins = roots6.iter().map(|&s| kappa(s, t0, v0)).collect::<Vec<_>>();
    let two = Pt::Aff(shift, f6.zero());
    assert_eq!(curve::pmul(f6, &ec6, &two, 2), Pt::Inf);
    let mut source_inverse_points = vec![];
    for &w in points {
        let (t, v) = coords(w);
        let raw = roots6.iter().map(|&s| kappa(s, t, v)).collect::<Vec<_>>();
        assert_eq!(curve::padd(f6, &ec6, &raw[0], &two), raw[1]);
        let based: Vec<_> = (0..2)
            .map(|j| curve::padd(f6, &ec6, &raw[j], &curve::neg(f6, &origins[j])))
            .collect();
        assert_eq!(based[0], based[1]);
        let source_point = match based[0] {
            Pt::Inf => None,
            Pt::Aff(x, y) => {
                let xk = back6(f6.sub(x, shift));
                let yk = back6(y);
                if let Some(sqrt_d) = square_root {
                    let mut ri = root;
                    let mut ca = checked.independent_curve.a;
                    let mut cb = checked.independent_curve.b;
                    for _ in 0..i {
                        ri = f.frobenius(ri);
                        ca = f.frobenius(ca);
                        cb = f.frobenius(cb);
                    }
                    let x = f.add(f.div(xk, factor), ri);
                    let y = f.div(yk, f.pow(sqrt_d, 3));
                    assert!(curve::on_curve(
                        f,
                        &curve::Curve::new(ca, cb),
                        &Pt::Aff(x, y)
                    ));
                    Some([three(x), three(y)])
                } else {
                    None
                }
            }
        };
        if square_root.is_some() {
            source_inverse_points
                .push(json!({"P":w,"original_source_quotient_with_actual_origin":source_point}));
        }
    }
    json!({"roots_and_actual_origins":roots6.iter().enumerate().map(|(j,&s)|json!({"s":six(s),"s_in_original_K":s.iter().enumerate().all(|(i,&v)|i==0||i==2||i==4||v==0),"actual_P0_kappa_short":match origins[j]{Pt::Inf=>None,Pt::Aff(x,y)=>Some([six(x),six(y)])}})).collect::<Vec<_>>(),"all_finite_curve_points_both_signs_on_EN":points.len(),"sign_change_equals_translation_by_actual_2torsion":true,"subtract_actual_origin_descends_K_and_sign_independent":true,"eligible_source_inverse_checked":square_root.is_some(),"all_actual_source_inverse_points":source_inverse_points,"scope":"rationalcurvepointquotientmapswithactualorigin;notgeneralJacobiannormortracepullback"})
}
