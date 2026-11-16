pub fn halving_quartic(f: &FpR, e: &Curve<ER>, u: ER) -> Vec<ER> {
    vec![
        f.sub(f.sq(e.a), f.mul(f.from_u64(4), f.mul(e.b, u))),
        f.neg(f.mul(
            f.from_u64(4),
            f.add(f.mul(e.a, u), f.mul(f.from_u64(2), e.b)),
        )),
        f.neg(f.mul(f.from_u64(2), e.a)),
        f.neg(f.mul(f.from_u64(4), u)),
        f.one(),
    ]
}

/// Fast ordinate recovery, followed by actual on-curve and full doubling checks.
/// Infinity and v=0 have separate complete branches and are rejected here.
pub fn generic_half(f: &FpR, e: &Curve<ER>, q: Pt<ER>, x: ER) -> Result<Pt<ER>> {
    let Pt::Aff(u, v) = q else {
        return Err("generic ordinate requires finite non-two-torsion Q".into());
    };
    let denominator = f.mul(f.from_u64(2), v);
    if f.is_zero(denominator) {
        return Err("zero generic ordinate denominator".into());
    }
    let t = f.sub(
        f.sub(
            f.sub(
                f.sub(f.mul(f.sq(x), x), f.mul(f.from_u64(3), f.mul(u, f.sq(x)))),
                f.mul(e.a, x),
            ),
            f.mul(e.a, u),
        ),
        f.mul(f.from_u64(2), e.b),
    );
    let p = Pt::Aff(x, f.div(t, denominator));
    if !curve::on_curve(f, e, &p) || curve::pmul(f, e, &p, 2) != q {
        return Err("ordinate did not give an actual half".into());
    }
    Ok(p)
}

