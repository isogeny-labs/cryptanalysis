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
