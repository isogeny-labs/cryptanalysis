//! Shared scalar/SIMD homogeneous quadratic elimination. No division by D.
use crate::field::F;

pub(super) trait Arithmetic<const B: u32> {
    type V: Copy;
    fn splat(a: u64) -> Self::V;
    fn add(a: Self::V, b: Self::V) -> Self::V;
    fn sub(a: Self::V, b: Self::V) -> Self::V;
    fn mul(a: Self::V, b: Self::V) -> Self::V;
}

pub(super) struct Scalar;
impl<const B: u32> Arithmetic<B> for Scalar {
    type V = u64;
    #[inline(always)]
    fn splat(a: u64) -> u64 {
        a
    }
    #[inline(always)]
    fn add(a: u64, b: u64) -> u64 {
        F::<B>::add(a, b)
    }
    #[inline(always)]
    fn sub(a: u64, b: u64) -> u64 {
        F::<B>::sub(a, b)
    }
    #[inline(always)]
    fn mul(a: u64, b: u64) -> u64 {
        F::<B>::mul(a, b)
    }
}

#[derive(Clone, Copy, Debug)]
pub(super) enum Step {
    Rational { residue: u64, delta: u64 },
    Cube,
    Septic,
    TorusSquare,
}

#[derive(Clone, Copy, Debug)]
pub(super) enum Terminal {
    Split {
        left: u64,
        right: u64,
        left_squared: u64,
        right_squared: u64,
    },
    Linear {
        value: u64,
        squared: u64,
    },
}
impl Terminal {
    pub(super) fn split<const B: u32>(left: u64, right: u64) -> Self {
        Self::Split {
            left,
            right,
            left_squared: F::<B>::sq(left),
            right_squared: F::<B>::sq(right),
        }
    }
}

#[derive(Clone, Debug)]
pub(super) struct Circuit {
    pub first_pole: u64,
    pub steps: Vec<Step>,
    pub terminal: Terminal,
    pub value: u64,
}

// Multiplication by public 0/1 constants should not become field multiplies.
#[inline(always)]
fn scale<const B: u32, O: Arithmetic<B>>(a: u64, v: O::V) -> O::V {
    match a {
        0 => O::splat(0),
        1 => v,
        _ => O::mul(O::splat(a), v),
    }
}

impl Circuit {
    // N=1 scalar or N=3 interleaved packed vectors; the stage loop stays outer.
    #[inline(always)]
    pub(super) fn evaluate<const B: u32, O: Arithmetic<B>, const N: usize>(
        &self,
        d: &mut [O::V; N],
        c: &mut [O::V; N],
        h: &mut [O::V; N],
    ) {
        for step in &self.steps {
            for k in 0..N {
                match *step {
                    Step::Rational { residue, delta } => {
                        let bd = scale::<B, O>(residue, d[k]);
                        let nd = O::mul(h[k], d[k]);
                        let diff = O::sub(h[k], bd);
                        let cc = O::mul(c[k], c[k]);
                        let norm = O::add(O::mul(diff, diff), scale::<B, O>(residue, cc));
                        let cd = O::mul(c[k], O::add(h[k], bd));
                        let t = scale::<B, O>(delta, nd);
                        h[k] = O::add(norm, scale::<B, O>(delta, O::add(cd, t)));
                        c[k] = O::add(cd, O::add(t, t));
                        d[k] = nd;
                    }
                    Step::Cube => {
                        let dh = O::mul(d[k], h[k]);
                        let three_dh = O::add(dh, O::add(dh, dh));
                        c[k] = O::mul(c[k], O::sub(O::mul(c[k], c[k]), three_dh));
                        d[k] = O::mul(O::mul(d[k], d[k]), d[k]);
                        h[k] = O::mul(O::mul(h[k], h[k]), h[k]);
                    }
                    Step::Septic => {
                        let cc = O::mul(c[k], c[k]);
                        let dh = O::mul(d[k], h[k]);
                        let t = O::sub(cc, dh);
                        let t2 = O::mul(t, t);
                        let seven_dh = O::add(
                            O::add(dh, dh),
                            O::add(dh, O::add(O::add(dh, dh), O::add(dh, dh))),
                        );
                        let cc3 = O::mul(O::mul(cc, cc), cc);
                        c[k] = O::mul(c[k], O::sub(cc3, O::mul(seven_dh, t2)));
                        for v in [&mut d[k], &mut h[k]] {
                            let v2 = O::mul(*v, *v);
                            let v3 = O::mul(v2, *v);
                            *v = O::mul(O::mul(v3, v3), *v);
                        }
                    }
                    Step::TorusSquare => {
                        let dd = O::mul(d[k], d[k]);
                        let dh = O::mul(d[k], h[k]);
                        let u = O::sub(O::mul(c[k], c[k]), O::add(dh, dh));
                        let twice_dd = O::add(dd, dd);
                        let four_dd = O::add(twice_dd, twice_dd);
                        c[k] = O::sub(u, four_dd);
                        h[k] = O::add(O::sub(O::mul(h[k], h[k]), O::add(u, u)), four_dd);
                        d[k] = dd;
                    }
                }
            }
        }
        for k in 0..N {
            h[k] = match self.terminal {
                Terminal::Linear { value, squared } => O::add(
                    O::sub(h[k], scale::<B, O>(value, c[k])),
                    scale::<B, O>(squared, d[k]),
                ),
                Terminal::Split {
                    left,
                    right,
                    left_squared,
                    right_squared,
                } => {
                    if left_squared == right_squared {
                        let center = O::add(h[k], scale::<B, O>(left_squared, d[k]));
                        let spread = scale::<B, O>(left, c[k]);
                        O::mul(O::sub(center, spread), O::add(center, spread))
                    } else {
                        let l = O::sub(
                            O::add(h[k], scale::<B, O>(left_squared, d[k])),
                            scale::<B, O>(left, c[k]),
                        );
                        let r = O::sub(
                            O::add(h[k], scale::<B, O>(right_squared, d[k])),
                            scale::<B, O>(right, c[k]),
                        );
                        O::mul(l, r)
                    }
                }
            };
        }
    }
}
