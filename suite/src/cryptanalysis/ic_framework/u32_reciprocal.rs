//! Exact reciprocal reduction for any u64 numerator and a fixed 32-bit modulus.
//! Opt-in exact arithmetic for canonical small-modulus matrix rows.
#[derive(Clone, Copy, Debug)]
pub struct U32Reciprocal {
    modulus: u64,
    reciprocal: u64,
}

impl U32Reciprocal {
    pub fn new(modulus: u64) -> Option<Self> {
        if !(2..=u32::MAX as u64).contains(&modulus) {
            return None;
        }
        Some(Self {
            modulus,
            reciprocal: ((1u128 << 64) / modulus as u128) as u64,
        })
    }

    /// With mu=floor(2^64/m), floor(x*mu/2^64) underestimates floor(x/m)
    /// by at most one for every x<2^64. Thus q*m<=x, and r=x-q*m<2m.
    /// One correction produces x mod m, without runtime integer division.
    #[inline(always)]
    pub fn reduce(self, x: u64) -> u64 {
        let q = ((x as u128 * self.reciprocal as u128) >> 64) as u64;
        let r = x - q * self.modulus;
        if r >= self.modulus {
            r - self.modulus
        } else {
            r
        }
    }

    /// Every u32 product fits in u64, even when operands are unreduced.
    #[inline(always)]
    pub fn mul(self, a: u32, b: u32) -> u64 {
        self.reduce(a as u64 * b as u64)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exhaustive_small_numerators_and_moduli() {
        for m in 2..=255 {
            let reducer = U32Reciprocal::new(m).unwrap();
            for x in 0..=u16::MAX as u64 {
                assert_eq!(reducer.reduce(x), x % m, "m={m}, x={x}");
            }
        }
    }
    #[test]
    fn boundary_and_random_full_width_numerators() {
        let mut state = 0x9e3779b97f4a7c15u64;
        for m in [
            2,
            3,
            5,
            7,
            17,
            257,
            65521,
            65536,
            1047281,
            2097533,
            22367531,
            1 << 31,
            (1 << 31) + 1,
            4294967291,
            u32::MAX as u64,
        ] {
            let reducer = U32Reciprocal::new(m).unwrap();
            for x in [
                0,
                1,
                m - 1,
                m,
                m + 1,
                m * m - 1,
                m * m,
                u64::MAX - m,
                u64::MAX - 1,
                u64::MAX,
            ] {
                assert_eq!(reducer.reduce(x), x % m, "m={m}, x={x}");
            }
            for _ in 0..100_000 {
                state ^= state << 13;
                state ^= state >> 7;
                state ^= state << 17;
                assert_eq!(reducer.reduce(state), state % m, "m={m}, x={state}");
                let a = state as u32;
                let b = (state >> 32) as u32;
                assert_eq!(
                    reducer.mul(a, b),
                    (a as u128 * b as u128 % m as u128) as u64
                );
            }
        }
        for m in [0, 1, 1 << 32, u64::MAX] {
            assert!(U32Reciprocal::new(m).is_none());
        }
    }
}
