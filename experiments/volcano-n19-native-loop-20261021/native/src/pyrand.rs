//! CPython's `random.Random` (Mersenne Twister MT19937) for the calls
//! tau.sage makes: `Random(str)` (seed version 2), `randrange(start, stop)`
//! and `shuffle(list)`, exactly as CPython 3.12 (the pinned Sage image's
//! Python 3.12.3) defines them:
//!
//! * `seed(str)`: `a = int.from_bytes(s.encode() + sha512(s.encode()).digest(), 'big')`,
//!   then `init_by_array` with the 32-bit words of `a`, least significant first.
//! * `getrandbits(k)`, `k <= 32`: `genrand_uint32() >> (32 - k)`; larger `k` is
//!   never needed here and is refused.
//! * `_randbelow(n)`: `k = n.bit_length()`, draw `getrandbits(k)` until `< n`.
//! * `randrange(a, b)` = `a + _randbelow(b - a)`;
//!   `shuffle(x)`: for i = len-1 down to 1, `j = _randbelow(i + 1)`, swap.
//!
//! The pure-Python test (`tests/test_pyrand.py`) compares every one of these
//! with the interpreter's own `random` module through the C ABI.

const N: usize = 624;
const M: usize = 397;

pub struct PyRandom {
    mt: [u32; N],
    mti: usize,
}

impl PyRandom {
    fn init_genrand(s: u32) -> PyRandom {
        let mut mt = [0u32; N];
        mt[0] = s;
        for i in 1..N {
            mt[i] = 1812433253u32.wrapping_mul(mt[i - 1] ^ (mt[i - 1] >> 30)).wrapping_add(i as u32);
        }
        PyRandom { mt, mti: N }
    }

    pub fn from_key(key: &[u32]) -> PyRandom {
        let mut r = PyRandom::init_genrand(19650218);
        let mt = &mut r.mt;
        let mut i = 1usize;
        let mut j = 0usize;
        let kl = key.len();
        let mut k = if N > kl { N } else { kl };
        while k > 0 {
            mt[i] = (mt[i] ^ (mt[i - 1] ^ (mt[i - 1] >> 30)).wrapping_mul(1664525))
                .wrapping_add(key[j])
                .wrapping_add(j as u32);
            i += 1;
            j += 1;
            if i >= N {
                mt[0] = mt[N - 1];
                i = 1;
            }
            if j >= kl {
                j = 0;
            }
            k -= 1;
        }
        k = N - 1;
        while k > 0 {
            mt[i] = (mt[i] ^ (mt[i - 1] ^ (mt[i - 1] >> 30)).wrapping_mul(1566083941)).wrapping_sub(i as u32);
            i += 1;
            if i >= N {
                mt[0] = mt[N - 1];
                i = 1;
            }
            k -= 1;
        }
        mt[0] = 0x8000_0000;
        r
    }

    /// `random.Random(s)` for a str seed (version 2).
    pub fn from_str_seed(s: &str) -> PyRandom {
        let mut bytes = s.as_bytes().to_vec();
        bytes.extend_from_slice(&crate::util::sha512(s.as_bytes()));
        // big-endian integer -> little-endian 32-bit words, without leading zero bytes
        let first = bytes.iter().position(|&b| b != 0);
        let key: Vec<u32> = match first {
            None => vec![0u32],
            Some(f) => {
                let be = &bytes[f..];
                let le: Vec<u8> = be.iter().rev().cloned().collect();
                le.chunks(4)
                    .map(|c| {
                        let mut w = [0u8; 4];
                        w[..c.len()].copy_from_slice(c);
                        u32::from_le_bytes(w)
                    })
                    .collect()
            }
        };
        PyRandom::from_key(&key)
    }

    pub fn genrand_uint32(&mut self) -> u32 {
        const MAG01: [u32; 2] = [0, 0x9908_b0df];
        if self.mti >= N {
            let mt = &mut self.mt;
            let mut kk = 0;
            while kk < N - M {
                let y = (mt[kk] & 0x8000_0000) | (mt[kk + 1] & 0x7fff_ffff);
                mt[kk] = mt[kk + M] ^ (y >> 1) ^ MAG01[(y & 1) as usize];
                kk += 1;
            }
            while kk < N - 1 {
                let y = (mt[kk] & 0x8000_0000) | (mt[kk + 1] & 0x7fff_ffff);
                mt[kk] = mt[kk + M - N] ^ (y >> 1) ^ MAG01[(y & 1) as usize];
                kk += 1;
            }
            let y = (mt[N - 1] & 0x8000_0000) | (mt[0] & 0x7fff_ffff);
            mt[N - 1] = mt[M - 1] ^ (y >> 1) ^ MAG01[(y & 1) as usize];
            self.mti = 0;
        }
        let mut y = self.mt[self.mti];
        self.mti += 1;
        y ^= y >> 11;
        y ^= (y << 7) & 0x9d2c_5680;
        y ^= (y << 15) & 0xefc6_0000;
        y ^= y >> 18;
        y
    }

    /// `getrandbits(k)` for 0 <= k <= 32.
    pub fn getrandbits(&mut self, k: u32) -> u64 {
        assert!(k <= 32, "getrandbits above 32 bits is not used here");
        if k == 0 {
            return 0;
        }
        (self.genrand_uint32() >> (32 - k)) as u64
    }

    /// `_randbelow_with_getrandbits(n)`, n >= 1.
    pub fn randbelow(&mut self, n: u64) -> u64 {
        assert!(n >= 1 && n < (1u64 << 32));
        let k = 64 - n.leading_zeros();
        let mut r = self.getrandbits(k);
        while r >= n {
            r = self.getrandbits(k);
        }
        r
    }

    /// `randrange(start, stop)` with step 1, start < stop.
    pub fn randrange(&mut self, start: u64, stop: u64) -> u64 {
        assert!(stop > start);
        start + self.randbelow(stop - start)
    }

    /// `shuffle(x)` (CPython 3.11+: no `random` argument).
    pub fn shuffle<T>(&mut self, x: &mut [T]) {
        let n = x.len();
        if n < 2 {
            return;
        }
        for i in (1..n).rev() {
            let j = self.randbelow(i as u64 + 1) as usize;
            x.swap(i, j);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mt19937_reference_vector() {
        // init_by_array({0x123, 0x234, 0x345, 0x456}): first outputs of the reference mt19937ar.c.
        let mut r = PyRandom::from_key(&[0x123, 0x234, 0x345, 0x456]);
        let want = [1067595299u32, 955945823, 477289528, 4107218783, 4228976476];
        for w in want {
            assert_eq!(r.genrand_uint32(), w);
        }
    }

    #[test]
    fn python_str_seed_vectors() {
        // python3 -c "import random; r=random.Random('gen:E0'); print([r.getrandbits(32) for _ in range(3)])"
        // and the same for the archived tau6 seed 'tau:tau6:0' (CPython 3.12 / 3.13 agree).
        let mut r = PyRandom::from_str_seed("gen:E0");
        let got: Vec<u64> = (0..3).map(|_| r.getrandbits(32)).collect();
        assert_eq!(got, crate::testvec::GEN_E0_BITS32.to_vec());
        let mut r = PyRandom::from_str_seed("tau:tau6:0");
        let got: Vec<u64> = (0..3).map(|_| r.randrange(1, 130873)).collect();
        assert_eq!(got, crate::testvec::TAU6_0_RANDRANGE.to_vec());
        let mut r = PyRandom::from_str_seed("tau:tau6:0");
        let mut v: Vec<u32> = (0..19).collect();
        r.shuffle(&mut v);
        assert_eq!(v, crate::testvec::TAU6_0_SHUFFLE19.to_vec());
    }
}
