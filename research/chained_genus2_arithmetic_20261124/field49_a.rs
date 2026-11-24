use crate::field_d::{add, inv, mul, sub};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct K(pub [u8; 2]);

#[derive(Clone, Copy, Debug)]
pub struct Quadratic {
    pub u0: u8,
    pub u1: u8,
}

impl Quadratic {
    pub fn validate(self) {
        assert!(self.u0 < 7 && self.u1 < 7);
        assert!((0..7).all(|x| add(add(mul(x, x), mul(self.u1, x)), self.u0) != 0));
        for a in 0..7 {
            for b in 0..7 {
                let x = K([a, b]);
                assert_eq!(self.pow(x, 49), x);
                if x != self.base(0) {
                    assert_eq!(self.mul(x, self.inv(x)), self.base(1));
                }
            }
        }
    }
    pub fn base(self, x: u8) -> K {
        assert!(x < 7);
        K([x, 0])
    }
    pub fn add(self, a: K, b: K) -> K {
        K([add(a.0[0], b.0[0]), add(a.0[1], b.0[1])])
    }
    pub fn scale(self, a: K, b: u8) -> K {
        K([mul(a.0[0], b), mul(a.0[1], b)])
    }
    pub fn neg(self, a: K) -> K {
        self.scale(a, 6)
    }
    pub fn sub(self, a: K, b: K) -> K {
        self.add(a, self.neg(b))
    }
    pub fn mul(self, a: K, b: K) -> K {
        let bb = mul(a.0[1], b.0[1]);
        K([
            sub(mul(a.0[0], b.0[0]), mul(self.u0, bb)),
            sub(
                add(mul(a.0[0], b.0[1]), mul(a.0[1], b.0[0])),
                mul(self.u1, bb),
            ),
        ])
    }
    pub fn conjugate(self, a: K) -> K {
        K([sub(a.0[0], mul(self.u1, a.0[1])), mul(6, a.0[1])])
    }
    pub fn pow(self, a: K, n: usize) -> K {
        (0..n).fold(self.base(1), |r, _| self.mul(r, a))
    }
    pub fn inv(self, a: K) -> K {
        assert_ne!(a, self.base(0));
        let norm = self.mul(a, self.conjugate(a));
        assert_eq!(norm.0[1], 0);
        assert_ne!(norm.0[0], 0);
        self.scale(self.conjugate(a), inv(norm.0[0]))
    }
}

pub const BASE: Quadratic = Quadratic { u0: 1, u1: 0 };
