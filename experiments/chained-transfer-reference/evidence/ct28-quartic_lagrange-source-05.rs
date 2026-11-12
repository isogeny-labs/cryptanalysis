// Byte-exact extraction from existing find/sutherland.rs; only visibility is added.
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::poly;
pub(super) fn lagrange(fp: &Zp, xs: &[u64], ys: &[u64]) -> Vec<u64> {
    let n = xs.len();
    let mut acc = vec![0u64];
    for k in 0..n {
        // basis L_k(Y) = prod_{m!=k} (Y - xs[m]) / (xs[k] - xs[m])
        let mut num = vec![fp.one()];
        let mut den = fp.one();
        for (m, &xm) in xs.iter().enumerate() {
            if m == k {
                continue;
            }
            num = poly::mul(fp, &num, &vec![fp.neg(xm), fp.one()]);
            den = fp.mul(den, fp.sub(xs[k], xm));
        }
        let scale = fp.mul(ys[k], fp.inv(den));
        let term = poly::scale(fp, &num, scale);
        acc = poly::add(fp, &acc, &term);
    }
    // pad/truncate to length n
    acc.resize(n, 0);
    acc
}
