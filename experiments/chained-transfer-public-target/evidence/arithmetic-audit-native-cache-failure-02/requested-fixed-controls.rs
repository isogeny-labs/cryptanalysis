//! Analytic primitive controls and comparisons with the untouched original FpR body.
use chained_n4_public_target::{common, ic};
use ghs_original_engines::{cover, pic};
use isogeny_algos::{
    arithmetic_audit_original_fpr as original,
    field::{Field, Zp},
    fpr::{FpR, ER},
};
use n4_arithmetic_taps as tap;
use serde_json::json;

pub fn strip_scalar_taps(source: &str) -> String {
    let inserts: Vec<String> =
        serde_json::from_str(include_str!("scalar-insertions.json")).unwrap();
    assert_eq!(inserts.len(), 2);
    let mut out = source.to_owned();
    for insert in inserts {
        assert_eq!(out.matches(&insert).count(), 1);
        out = out.replace(&insert, "");
    }
    out
}
fn counts(label: &str, backend: &str, p: u64, expected: &[(&str, u64)]) {
    for &(op, n) in expected {
        assert_eq!(
            tap::count(label, backend, p, op),
            n,
            "{label}/{backend}/{p}/{op}"
        );
    }
}
fn dense(r: usize) -> ER {
    let mut a = [0; 16];
    a[..r].fill(1);
    a
}
fn compare_field(field: &FpR, reference: &original::FpR, label: &str) {
    assert_eq!(field.modulus(), reference.modulus());
    assert_eq!(field.r, reference.r);
    assert_eq!(field.p, reference.p);
    let mut rng = common::Rng::new(0xC072_A817 ^ field.p ^ field.r as u64);
    let mut corpus = vec![field.zero(), field.one(), dense(field.r)];
    for i in 0..field.r {
        let mut a = [0; 16];
        a[i] = field.p - 1;
        corpus.push(a);
    }
    for _ in 0..64 {
        let mut a = [0; 16];
        for x in a.iter_mut().take(field.r) {
            *x = rng.below(field.p)
        }
        corpus.push(a);
    }
    for (i, &a) in corpus.iter().enumerate() {
        let b = corpus[(17 * i + 3) % corpus.len()];
        let observed = tap::within(format!("corpus-{label}-derived"), || {
            (
                field.add(a, b),
                field.sub(a, b),
                field.neg(a),
                field.mul(a, b),
                field.sq(a),
            )
        });
        let expected = tap::within(format!("corpus-{label}-reference-shared-Zp-fpm"), || {
            (
                reference.add(a, b),
                reference.sub(a, b),
                reference.neg(a),
                reference.mul(a, b),
                reference.sq(a),
            )
        });
        assert_eq!(observed, expected, "{label}/{i}");
        if field.r > 1 {
            assert_eq!(
                tap::within(format!("corpus-{label}-derived"), || field.frobenius(a)),
                tap::within(format!("corpus-{label}-reference-shared-Zp-fpm"), || {
                    reference.frobenius(a)
                })
            );
        }
        if !field.is_zero(a) {
            let inverse = tap::within(format!("corpus-{label}-derived"), || field.inv(a));
            let original_inverse =
                tap::within(format!("corpus-{label}-reference-shared-Zp-fpm"), || {
                    reference.inv(a)
                });
            assert_eq!(inverse, original_inverse);
            assert_eq!(field.mul(a, inverse), field.one());
        }
    }
    println!(
        "N4_ARITHMETIC_FIELD_CONTROL {}",
        json!({"label":label,"modulus":field.modulus(),"p":field.p,"r":field.r,"inputs":corpus.len(),"full_reference_debug":format!("{reference:?}"),"full_derived_debug":format!("{field:?}"),"all_results_equal":true,"reference_scope":"untouched original FpR body; instrumented Zp/fpm dependencies shared and disclosed"})
    );
}

pub fn run() {
    let _scope = tap::scope("primitive-controls-and-constructors");
    let f = FpR::from_modulus(223, &[220, 0, 0, 1]);
    let old = original::FpR::from_modulus(223, &[220, 0, 0, 1]);
    let a = dense(3);
    let actual = tap::within("primitive-fpr3-mul", || f.mul(a, a));
    assert_eq!(actual, old.mul(a, a));
    counts(
        "primitive-fpr3-mul",
        "FpR.coefficient",
        223,
        &[("mul", 11), ("sq", 0), ("add", 11), ("rem_u128", 5)],
    );
    let actual = tap::within("primitive-fpr3-sq", || f.sq(a));
    assert_eq!(actual, old.sq(a));
    counts(
        "primitive-fpr3-sq",
        "FpR.coefficient",
        223,
        &[
            ("mul", 5),
            ("sq", 3),
            ("const_two", 3),
            ("add", 8),
            ("rem_u128", 5),
        ],
    );
    let actual = tap::within("primitive-fpr3-frobenius", || f.frobenius(a));
    assert_eq!(actual, old.frobenius(a));
    counts(
        "primitive-fpr3-frobenius",
        "FpR.coefficient",
        223,
        &[("mul", 9), ("add", 9), ("rem_u128", 3)],
    );
    let actual = tap::within("primitive-fpr3-inverse", || f.inv(a));
    assert_eq!(actual, old.inv(a));
    counts("primitive-fpr3-inverse", "FpR.api", 223, &[("inv", 1)]);
    counts("primitive-fpr3-inverse", "fpm.base", 223, &[("inv", 1)]);
    compare_field(&f, &old, "q223-r3");

    let linear = FpR::new(223, 1);
    let old_linear = original::FpR::new(223, 1);
    let x = linear.from_u64(7);
    assert_eq!(
        tap::within("primitive-fpr1-mul", || linear.mul(x, x)),
        old_linear.mul(x, x)
    );
    counts(
        "primitive-fpr1-mul",
        "FpR.coefficient",
        223,
        &[("mul", 1), ("add", 0), ("rem_u128", 1)],
    );
    assert_eq!(
        tap::within("primitive-fpr1-sq", || linear.sq(x)),
        old_linear.sq(x)
    );
    counts(
        "primitive-fpr1-sq",
        "FpR.coefficient",
        223,
        &[("mul", 1), ("sq", 0), ("rem_u128", 1)],
    );
    counts(
        "primitive-fpr1-sq",
        "FpR.api",
        223,
        &[("sq", 1), ("mul", 1)],
    );
    compare_field(&linear, &old_linear, "q223-r1");
    let six = FpR::new(223, 6);
    let old_six = original::FpR::new(223, 6);
    compare_field(&six, &old_six, "q223-r6");

    // Original contract rejection is an observed negative, not a bypass.
    let proposed = 9223372036854775783u64;
    let rejected_original =
        std::panic::catch_unwind(|| original::FpR::from_modulus(proposed, &[1, 0, 1])).is_err();
    let rejected_derived =
        std::panic::catch_unwind(|| FpR::from_modulus(proposed, &[1, 0, 1])).is_err();
    assert!(rejected_original && rejected_derived);
    println!(
        "N4_ARITHMETIC_CONSTRUCTOR_REJECTION {}",
        json!({"p":proposed,"r":2,"original_rejected":rejected_original,"derived_rejected":rejected_derived,"reason_from_original_source":"Zp::new requires p<2^62","prospective_addendum":"cda454/584ba997 BEFORE this code and native execution","not_an_impossibility_claim":true})
    );
    let p = 4611686018427387847u64;
    let nonlazy = FpR::new(p, 3);
    let old_nonlazy = original::FpR::new(p, 3);
    assert!(format!("{nonlazy:?}").contains("lazy: false"));
    assert!(format!("{old_nonlazy:?}").contains("lazy: false"));
    let modulus = nonlazy.modulus();
    assert_eq!(
        modulus[..3].iter().filter(|&&x| x != 0).count(),
        1,
        "expected one-term original search tail"
    );
    let actual = tap::within("primitive-fpr-nonlazy-mul", || nonlazy.mul(a, a));
    assert_eq!(actual, old_nonlazy.mul(a, a));
    counts(
        "primitive-fpr-nonlazy-mul",
        "FpR.coefficient",
        p,
        &[("mul", 11), ("add", 11), ("rem_u128", 29)],
    );
    let actual = tap::within("primitive-fpr-nonlazy-sq", || nonlazy.sq(a));
    assert_eq!(actual, old_nonlazy.sq(a));
    counts(
        "primitive-fpr-nonlazy-sq",
        "FpR.coefficient",
        p,
        &[("mul", 11), ("sq", 0), ("add", 11), ("rem_u128", 29)],
    );
    counts(
        "primitive-fpr-nonlazy-sq",
        "FpR.api",
        p,
        &[("sq", 1), ("mul", 1)],
    );
    compare_field(&nonlazy, &old_nonlazy, "q62-r3-nonlazy");

    let zp = Zp::new(223);
    assert_eq!(tap::within("primitive-zp-mul", || zp.mul(7, 9)), 63);
    counts("primitive-zp-mul", "Zp", 223, &[("mul", 1)]);
    counts(
        "primitive-zp-mul",
        "Red128.api",
        223,
        &[("reduce", 1), ("redc", 2), ("mod_word", 2)],
    );
    assert_eq!(tap::within("primitive-zp-inv", || zp.inv(2)), 112);
    counts("primitive-zp-inv", "Zp", 223, &[("inv_api", 1), ("inv", 0)]);
    counts("primitive-zp-inv", "fpm.base", 223, &[("inv", 1)]);
    assert_eq!(
        tap::within("primitive-zp-conv", || zp.conv(&[1, 1, 1], &[1, 1, 1])),
        vec![1, 2, 3, 2, 1]
    );
    counts(
        "primitive-zp-conv",
        "Zp.lazy",
        223,
        &[("mul", 9), ("add", 9)],
    );
    assert_eq!(
        tap::within("primitive-zp-conv-sq", || zp.conv_sq(&[1, 1, 1])),
        vec![1, 2, 3, 2, 1]
    );
    counts(
        "primitive-zp-conv-sq",
        "Zp.lazy",
        223,
        &[("mul", 3), ("sq", 5), ("const_two", 5), ("add", 8)],
    );
    assert_eq!(
        tap::within("primitive-zp-dot", || zp.dot_rev(&[1, 2, 3], &[4, 5, 6])),
        28
    );
    counts(
        "primitive-zp-dot",
        "Zp.lazy",
        223,
        &[("mul", 3), ("add", 3)],
    );

    let fp = common::Fp { q: 223 };
    assert_eq!(tap::within("primitive-native-mul", || fp.mul(7, 9)), 63);
    counts(
        "primitive-native-mul",
        "native.Fp",
        223,
        &[("mul", 1), ("rem_u64", 1)],
    );
    assert_eq!(tap::within("primitive-native-inv", || fp.inv(2)), 112);
    counts("primitive-native-inv", "native.Fp", 223, &[("inv", 1)]);
    assert_eq!(
        tap::within("primitive-scalar-mul", || ic::lm(3, 4, 2773073)),
        12
    );
    counts(
        "primitive-scalar-mul",
        "native.scalar",
        2773073,
        &[("mul", 1), ("rem_u128", 1)],
    );
    assert_eq!(
        tap::within("primitive-scalar-add", || ic::la(2773072, 2, 2773073)),
        1
    );
    assert_eq!(
        tap::within("primitive-scalar-sub", || ic::ls(1, 2, 2773073)),
        2773072
    );
    counts(
        "primitive-scalar-add",
        "native.scalar",
        2773073,
        &[("add", 1)],
    );
    counts(
        "primitive-scalar-sub",
        "native.scalar",
        2773073,
        &[("sub", 1)],
    );
    let k = common::Kf::new(223);
    let before = common::snap();
    let product = tap::within("primitive-native-K-mul", || k.mul(&[1, 1, 1], &[1, 1, 1]));
    let legacy = common::snap().since(&before);
    assert_eq!(product, [7, 5, 3]);
    counts(
        "primitive-native-K-mul",
        "native.K.coefficient",
        223,
        &[("mul", 11), ("add", 6), ("rem_u64", 7)],
    );
    assert_eq!((legacy.mul, legacy.add), (11, 8));
    let before = common::snap();
    let inverse = tap::within("primitive-native-K-inverse", || k.inv(&[1, 1, 1]));
    let legacy_inverse = common::snap().since(&before);
    assert_eq!(k.mul(&inverse, &[1, 1, 1]), [1, 0, 0]);
    counts(
        "primitive-native-K-inverse",
        "native.K.coefficient",
        223,
        &[("mul", 15), ("add", 8), ("rem_u64", 10)],
    );
    counts(
        "primitive-native-K-inverse",
        "native.Fp",
        223,
        &[("mul", 7), ("inv", 1)],
    );
    assert_eq!(legacy_inverse.mul, 23);

    let cover = cover::Fq::new(223);
    assert_eq!(tap::within("primitive-cover-mul", || cover.mul(7, 9)), 63);
    assert_eq!(tap::within("primitive-cover-inv", || cover.inv(2)), 112);
    counts(
        "primitive-cover-mul",
        "cover.Fq",
        223,
        &[("mul", 1), ("rem_u64", 1)],
    );
    counts("primitive-cover-inv", "cover.Fq", 223, &[("inv", 1)]);
    let mont = cover::Mont::new(2773073);
    let two = mont.to(2);
    let three = mont.to(3);
    let six = tap::within("primitive-mont-mul", || mont.mul(two, three));
    assert_eq!(mont.from(six), 6);
    counts(
        "primitive-mont-mul",
        "cover.Mont",
        2773073,
        &[("mul", 1), ("redc_api", 1)],
    );
    let inverse = tap::within("primitive-mont-inverse", || mont.inv(two));
    assert_eq!(mont.from(inverse), 1386537);
    counts(
        "primitive-mont-inverse",
        "cover.Mont",
        2773073,
        &[("inv_api", 1), ("inv", 0)],
    );
    assert!(tap::count("primitive-mont-inverse", "cover.Mont", 2773073, "mul") > 0);

    pic::arithmetic_audit_private_controls();
    for label in ["primitive-pic-mul", "primitive-pic-mulu"] {
        counts(label, "Picard.Fq", 223, &[("mul", 1), ("rem_u64", 1)]);
    }
    for (label, op) in [
        ("primitive-pic-add", "add"),
        ("primitive-pic-sub", "sub"),
        ("primitive-pic-subnc", "sub"),
        ("primitive-pic-neg", "neg"),
        ("primitive-pic-invu", "inv"),
        ("primitive-pic-inv", "inv"),
    ] {
        counts(label, "Picard.Fq", 223, &[(op, 1)]);
    }
    let curve = pic::PlaneQuartic::new(
        223,
        [
            1, 121, 174, 193, 172, 175, 11, 124, 77, 78, 48, 58, 89, 63, 164,
        ],
        [1, 0, 84],
    )
    .unwrap();
    let product = curve.mul_forms(1, &[1, 1, 1], 1, &[1, 1, 1]);
    assert_eq!(product.len(), 6);
    let before = tap::total();
    assert!(curve.counter().mul > 0);
    curve.reset_counter();
    assert_eq!(curve.counter(), pic::FqCounter::default());
    assert_eq!(tap::total(), before);
    println!(
        "N4_ARITHMETIC_PRIMITIVES {}",
        json!({"all_analytic_counts_checked":true,"legacy_Picard_mulu_invu_subnc_bypass_retained":true,"legacy_reset_cannot_reset_new_ledger":true,"native_K_dense_legacy_add":8,"native_K_dense_actual_add":6,"native_K_inverse_legacy_mul":23,"native_K_inverse_actual_mul":22,"constructor_63bit_rejection_retained":true,"nonlazy_actual_modulus":modulus,"no_price_or_speed_claim":true})
    );
}
