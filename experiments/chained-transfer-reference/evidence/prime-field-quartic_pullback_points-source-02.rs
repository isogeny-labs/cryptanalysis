// Existing seven.rs point enumeration,body byte-exact;visibility only.
use isogeny_algos::curve::{self, Curve, Pt};
use isogeny_algos::field::Zp;
pub(super) fn points(f: &Zp, e: &Curve<u64>) -> Vec<Pt<u64>> {
    let mut out = vec![Pt::Inf];
    for x in 0..f.p {
        for y in 0..f.p {
            if curve::on_curve(f, e, &Pt::Aff(x, y)) {
                out.push(Pt::Aff(x, y));
            }
        }
    }
    out
}
