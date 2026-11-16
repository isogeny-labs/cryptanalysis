use std::cell::Cell;
struct Fq {
    q: u64,
    quadratic_nu: Option<u32>,
    c_mul: Cell<u64>,
    c_inv: Cell<u64>,
    c_add: Cell<u64>,
}

impl Fq {
    #[inline]
    fn mul(&self, a: u32, b: u32) -> u32 {
        n4_arithmetic_taps::hit("quadratic.Picard.api", self.q, "mul", 1);
        self.c_mul.set(self.c_mul.get() + 1);
        self.mulu(a, b)
    }
    #[inline]
    fn mulu(&self, a: u32, b: u32) -> u32 {
        if let Some(nu) = self.quadratic_nu {
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "mul", 5);
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "add", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "rem_u64", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "decode_rem", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "decode_div", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "pack_mul", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "pack_add", 1);
            let p = self.q;
            let (a0, a1) = (a as u64 % p, a as u64 / p);
            let (b0, b1) = (b as u64 % p, b as u64 / p);
            assert!(a1 < p && b1 < p);
            let real = (a0 * b0 + nu as u64 * a1 * b1) % p;
            let imag = (a0 * b1 + a1 * b0) % p;
            return (real + p * imag) as u32;
        }
        n4_arithmetic_taps::hit("quadratic.Picard.prime", self.q, "mul", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.prime", self.q, "rem_u64", 1);
        ((a as u64 * b as u64) % self.q) as u32
    }
    fn add_nc(&self, a: u32, b: u32) -> u32 {
        if self.quadratic_nu.is_some() {
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "add", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "rem_u64", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "decode_rem", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "decode_div", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "pack_mul", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "pack_add", 1);
            let p = self.q;
            return (((a as u64 % p + b as u64 % p) % p) + p * ((a as u64 / p + b as u64 / p) % p))
                as u32;
        }
        n4_arithmetic_taps::hit("quadratic.Picard.prime", self.q, "add", 1);
        let s = a as u64 + b as u64;
        (if s >= self.q { s - self.q } else { s }) as u32
    }
    #[inline]
    fn add(&self, a: u32, b: u32) -> u32 {
        n4_arithmetic_taps::hit("quadratic.Picard.api", self.q, "add", 1);
        self.c_add.set(self.c_add.get() + 1);
        self.add_nc(a, b)
    }
    #[inline]
    fn sub(&self, a: u32, b: u32) -> u32 {
        n4_arithmetic_taps::hit("quadratic.Picard.api", self.q, "sub", 1);
        self.c_add.set(self.c_add.get() + 1);
        self.sub_nc(a, b)
    }
    #[inline]
    fn neg(&self, a: u32) -> u32 {
        n4_arithmetic_taps::hit("quadratic.Picard.api", self.q, "neg", 1);
        if self.quadratic_nu.is_some() {
            return self.sub_nc(0, a);
        }
        if a != 0 { n4_arithmetic_taps::hit("quadratic.Picard.prime", self.q, "neg", 1); }
        if a == 0 {
            0
        } else {
            (self.q - a as u64) as u32
        }
    }
    fn invu(&self, a: u32) -> u32 {
        n4_arithmetic_taps::hit("quadratic.Picard.api", self.q, "invu", 1);
        if let Some(nu) = self.quadratic_nu {
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "sq", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "mul", 4);
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "sub", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "rem_u64", 4);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "decode_rem", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "decode_div", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "pack_mul", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "pack_add", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "modulus_adjust_add", 1);
            let p = self.q;
            let (a0, a1) = (a as u64 % p, a as u64 / p);
            assert!(a1 < p);
            let norm = (a0 * a0 + p - (nu as u64 * a1 * a1) % p) % p;
            assert!(norm != 0, "quadratic field inversion of zero");
            let inv_norm = self.base_invu(norm as u32) as u64;
            return ((a0 * inv_norm) % p + p * ((p - a1) * inv_norm % p)) as u32;
        }
        self.base_invu(a)
    }
    fn base_invu(&self, a: u32) -> u32 {
        n4_arithmetic_taps::hit("quadratic.Picard.prime", self.q, "inv", 1);
        // extended Euclid on (q, a)
        let (mut r0, mut r1) = (self.q as i64, a as i64);
        let (mut t0, mut t1) = (0i64, 1i64);
        while r1 != 0 {
            let qt = r0 / r1;
            let r2 = r0 - qt * r1;
            r0 = r1;
            r1 = r2;
            let t2 = t0 - qt * t1;
            t0 = t1;
            t1 = t2;
        }
        debug_assert_eq!(r0, 1);
        (((t0 % self.q as i64) + self.q as i64) % self.q as i64) as u32
    }
    fn inv(&self, a: u32) -> u32 {
        n4_arithmetic_taps::hit("quadratic.Picard.api", self.q, "inv", 1);
        assert!(a != 0, "inversion of zero");
        self.c_inv.set(self.c_inv.get() + 1);
        self.invu(a)
    }
    fn powu(&self, mut a: u32, mut e: u64) -> u32 {
        let mut r = 1u32;
        while e > 0 {
            if e & 1 == 1 {
                r = self.mulu(r, a);
            }
            a = self.mulu(a, a);
            e >>= 1;
        }
        r
    }
}

impl Fq {
    fn sub_nc(&self, a: u32, b: u32) -> u32 {
        if self.quadratic_nu.is_some() {
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "sub", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.coefficient", self.q, "rem_u64", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "decode_rem", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "decode_div", 2);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "pack_mul", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "pack_add", 1);
        n4_arithmetic_taps::hit("quadratic.Picard.encoding", self.q, "modulus_adjust_add", 2);
            let p = self.q;
            return (((a as u64 % p + p - b as u64 % p) % p)
                + p * ((a as u64 / p + p - b as u64 / p) % p)) as u32;
        }
        n4_arithmetic_taps::hit("quadratic.Picard.prime", self.q, "sub", 1);
        if a >= b {
            a - b
        } else {
            (a as u64 + self.q - b as u64) as u32
        }
    }
}

#[cfg(feature = "arithmetic-audit-controls")]
#[doc(hidden)]
pub fn norm_arithmetic_quadratic_controls() -> serde_json::Value {
    use isogeny_algos::{arithmetic_audit_original_fpr::FpR, field::Field};
    use n4_arithmetic_taps as tap;
    assert!(
        tap::observer_enabled(),
        "primitive controls require observation"
    );
    let f = Fq {
        q: 223,
        quadratic_nu: Some(3),
        c_mul: Cell::new(0),
        c_inv: Cell::new(0),
        c_add: Cell::new(0),
    };
    let prime = Fq {
        q: 223,
        quadratic_nu: None,
        c_mul: Cell::new(0),
        c_inv: Cell::new(0),
        c_add: Cell::new(0),
    };
    let oracle = FpR::from_modulus(223, &[220, 0, 1]);
    let lift = |a: u32| {
        let mut r = [0; 16];
        r[0] = (a % 223) as u64;
        r[1] = (a / 223) as u64;
        r
    };
    let down = |a: [u64; 16]| {
        assert!(a[2..].iter().all(|x| *x == 0));
        (a[0] + 223 * a[1]) as u32
    };
    let a = 224;
    let b = 671;
    let actual = tap::within("quad-dense-mulu", || f.mulu(a, b));
    let expected = down(oracle.mul(lift(a), lift(b)));
    assert_eq!(actual, expected, "unchanged original FpR algebra reference");
    let observed = tap::count(
        "quad-dense-mulu",
        "quadratic.Picard.coefficient",
        223,
        "mul",
    );
    println!(
        "N4_NORM_QPIC_HOOK_PROBE {}",
        serde_json::json!({"all_algebra_equal":true,"a":a,"b":b,"actual":actual,"original_reference":expected,"observed_coefficient_mul":observed,"expected_coefficient_mul":5,"scope":"original FpR body shares instrumented Zp/fpm dependencies; no execution standing"})
    );
    assert_eq!(
        observed, 5,
        "actual omitted quadratic coefficient hook must reject"
    );
    for (op, n) in [("add", 2), ("rem_u64", 2)] {
        assert_eq!(
            tap::count("quad-dense-mulu", "quadratic.Picard.coefficient", 223, op),
            n
        );
    }
    assert_eq!(f.c_mul.get(), 0, "legacy mulu remains unchanged");
    assert_eq!(tap::within("quad-counted-mul", || f.mul(a, b)), expected);
    assert_eq!(f.c_mul.get(), 1);
    assert_eq!(
        tap::count(
            "quad-counted-mul",
            "quadratic.Picard.coefficient",
            223,
            "mul"
        ),
        5
    );
    let s = tap::within("quad-add", || f.add_nc(a, b));
    assert_eq!(s, down(oracle.add(lift(a), lift(b))));
    assert_eq!(
        tap::count("quad-add", "quadratic.Picard.coefficient", 223, "add"),
        2
    );
    let s = tap::within("quad-sub", || f.sub_nc(a, b));
    assert_eq!(s, down(oracle.sub(lift(a), lift(b))));
    assert_eq!(
        tap::count("quad-sub", "quadratic.Picard.coefficient", 223, "sub"),
        2
    );
    let s = tap::within("quad-neg", || f.neg(a));
    assert_eq!(s, down(oracle.neg(lift(a))));
    assert_eq!(
        tap::count("quad-neg", "quadratic.Picard.coefficient", 223, "sub"),
        2
    );
    let inv = tap::within("quad-inverse-one", || f.invu(a));
    assert_eq!(inv, down(oracle.inv(lift(a))));
    for (op, n) in [("sq", 1), ("mul", 4), ("sub", 2), ("rem_u64", 4)] {
        assert_eq!(
            tap::count("quad-inverse-one", "quadratic.Picard.coefficient", 223, op),
            n
        );
    }
    assert_eq!(
        tap::count("quad-inverse-one", "quadratic.Picard.prime", 223, "inv"),
        1
    );
    assert_eq!(f.c_inv.get(), 0, "legacy invu remains unchanged");
    assert_eq!(f.inv(a), inv);
    assert_eq!(f.c_inv.get(), 1);
    let p = tap::within("quadratic-prime-mul", || prime.mulu(7, 9));
    assert_eq!(p, 63);
    assert_eq!(
        tap::count("quadratic-prime-mul", "quadratic.Picard.prime", 223, "mul"),
        1
    );
    assert_eq!(tap::within("quadratic-prime-inv", || prime.invu(2)), 112);
    assert_eq!(
        tap::count("quadratic-prime-inv", "quadratic.Picard.prime", 223, "inv"),
        1
    );
    let ledger_before_reset = tap::total();
    f.c_mul.set(0);
    f.c_inv.set(0);
    f.c_add.set(0);
    assert_eq!(tap::total(), ledger_before_reset);
    let mut corpus = vec![0, 1, 223, 224, 49728, 17 + 223 * 33];
    let mut rng = isogeny_algos::field::Rng::new(0x75514950);
    for _ in 0..64 {
        corpus.push(rng.below(49729) as u32);
    }
    let mut pairs = Vec::new();
    for &x in &corpus {
        for &y in &corpus {
            let outputs = [f.mulu(x, y), f.add_nc(x, y), f.sub_nc(x, y)];
            let references = [
                down(oracle.mul(lift(x), lift(y))),
                down(oracle.add(lift(x), lift(y))),
                down(oracle.sub(lift(x), lift(y))),
            ];
            assert_eq!(outputs, references);
            pairs.push(serde_json::json!({"a":x,"b":y,"actual":outputs,"original_FpR":references}));
        }
    }
    let mut inverses = Vec::new();
    tap::within("quadratic-all-nonzero-inverses", || {
        for x in 1..49729u32 {
            let y = f.invu(x);
            let reference = down(oracle.inv(lift(x)));
            assert_eq!(y, reference);
            assert_eq!(f.mulu(x, y), 1);
            inverses.push([x, y, reference]);
        }
    });
    assert_eq!(inverses.len(), 49728);
    tap::assert_no_unsupported();
    serde_json::json!({"p":223,"nu":3,"all_dense_sparse_zero_one_and_random_pairs":pairs,"all49728_nonzero_inverse_pairs":inverses,"delegation_and_legacy_reset_controls":true,"ledger":tap::snapshot(),"scope":"finite primitive parity and analytic source counts; original FpR body shares instrumented lower dependencies; no prices"})
}

#[cfg(all(test, feature = "arithmetic-audit-controls"))]
mod norm_arithmetic_primitive_unit {
    #[test]
    fn all_quadratic_leaves_counts_and_nonzero_inverses() {
        println!(
            "N4_NORM_QPIC_PRIMITIVES {}",
            super::norm_arithmetic_quadratic_controls()
        );
    }
}
