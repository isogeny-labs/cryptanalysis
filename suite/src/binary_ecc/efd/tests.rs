use super::super::curve::{point_add, point_double, BinaryCurve, BinaryPoint};
use super::program::{equality, Expr};
use super::*;
use num_bigint::BigUint;
use std::collections::BTreeSet;

type Affine = (F2mElement, F2mElement);
fn element(n: u32, m: u32) -> F2mElement {
    F2mElement::from_biguint(&BigUint::from(n), m)
}
fn field(m: u32) -> IrreduciblePoly {
    IrreduciblePoly {
        degree: m,
        low_terms: if m == 5 { vec![0, 2] } else { vec![0, 1] },
    }
}
fn parameters(model: &str, special: bool, m: u32) -> Bindings {
    let pairs: Vec<(&str, u32)> = match model {
        "shortw" => vec![("a2", if special { 1 } else { 0 }), ("a6", 3)],
        "edwards" => vec![("d1", if special { 1 } else { 2 }), ("d2", 1)],
        "hessian" => vec![("d", 2)],
        _ => unreachable!(),
    };
    pairs
        .into_iter()
        .map(|(k, v)| (k.into(), element(v, m)))
        .collect()
}
fn oracle(
    model: &Model,
    operation: &str,
    field: &IrreduciblePoly,
    params: &Bindings,
    p: &Affine,
    q: Option<&Affine>,
) -> Result<Affine> {
    let mut values = params.clone();
    values.insert("x1".into(), p.0.clone());
    values.insert("y1".into(), p.1.clone());
    if let Some(q) = q {
        values.insert("x2".into(), q.0.clone());
        values.insert("y2".into(), q.1.clone());
    }
    let mut out = Bindings::new();
    for line in model
        .source
        .text
        .lines()
        .filter_map(|s| s.strip_prefix(&format!("{operation} ")))
    {
        let (name, e) = line.split_once('=').unwrap();
        out.insert(name.trim().into(), Expr::parse(e)?.eval(field, &values)?);
    }
    Ok((
        out.remove("x")
            .ok_or_else(|| EfdError::Unsupported(operation.into()))?,
        out.remove("y").unwrap(),
    ))
}
fn points(model: &Model, field: &IrreduciblePoly, params: &Bindings) -> Vec<Affine> {
    let relation = model
        .source
        .text
        .lines()
        .find_map(|s| s.strip_prefix("satisfying "))
        .unwrap();
    let (a, b) = equality(relation).unwrap();
    let mut out = Vec::new();
    for x in 0..1 << field.degree {
        for y in 0..1 << field.degree {
            let mut v = params.clone();
            let p = (element(x, field.degree), element(y, field.degree));
            v.insert("x".into(), p.0.clone());
            v.insert("y".into(), p.1.clone());
            if a.eval(field, &v).unwrap() == b.eval(field, &v).unwrap() {
                out.push(p);
            }
        }
    }
    out
}
fn projection(rep: &Representation, p: &Affine) -> Projection {
    if rep.variables == ["w"] || rep.variables.iter().any(|s| s == "W") {
        Projection::W(p.0.add(&p.1))
    } else if rep.id == "shortw/xz" {
        Projection::X(p.0.clone())
    } else {
        Projection::Full {
            x: p.0.clone(),
            y: p.1.clone(),
        }
    }
}
fn source_digest(s: &Source) {
    let h = crate::hash::sha256::sha256(s.text.as_bytes());
    let hex: String = h.iter().map(|b| format!("{b:02x}")).collect();
    assert_eq!(s.sha256, hex, "{}", s.url);
}

#[test]
fn complete_pinned_catalogue_and_source_hashes() {
    let c = catalogue();
    assert_eq!(c.characteristic, 2);
    assert_eq!(c.formulas.len(), 135);
    assert_eq!(c.representations.len(), 19);
    assert_eq!(c.models.len(), 3);
    let mut ids = BTreeSet::new();
    for model in &c.models {
        source_digest(&model.source);
    }
    for rep in &c.representations {
        source_digest(&rep.source);
    }
    for f in &c.formulas {
        assert!(ids.insert(&f.id));
        source_digest(&f.record);
        source_digest(&f.program);
        f.compile().unwrap_or_else(|e| panic!("{}: {e}", f.id));
    }
}

#[test]
fn all_nineteen_formats_roundtrip_scaled_finite_points() {
    let field = field(5);
    let x = element(7, 5);
    let y = element(9, 5);
    for rep in &catalogue().representations {
        for z in [1, 2, 5, 19] {
            let v = rep.encode_affine(&field, &x, &y, &element(z, 5)).unwrap();
            assert_eq!(
                rep.project(&field, &rep.bind_point(&v, 3), 3).unwrap(),
                projection(rep, &(x.clone(), y.clone())),
                "{}",
                rep.id
            );
        }
    }
}

/// Compare every optimized SLP with the independent, unoptimized affine group
/// law in the model record. Exercise both unit and nonunit projective scales.
/// Singular affine charts and vanishing denominators are explicitly skipped;
/// every formula must have at least 16 successful comparisons in EACH field.
#[test]
fn all_135_formulas_match_affine_model_laws() {
    let mut coverage = Vec::new();
    for m in [4, 5] {
        let field = field(m);
        for rep in &catalogue().representations {
            let model = catalogue()
                .models
                .iter()
                .find(|s| rep.id.starts_with(&format!("{}/", s.id)))
                .unwrap();
            let special = rep.id.ends_with("-1");
            let params = parameters(&model.id, special, m);
            let pts = points(model, &field, &params);
            assert!(pts.len() > 8, "{}", rep.id);
            for formula in catalogue()
                .formulas
                .iter()
                .filter(|f| f.representation == rep.id)
            {
                let program = formula.compile().unwrap();
                let mut passed = 0;
                let mut attempted = 0;
                for k in 0..pts.len() * pts.len() * 2 {
                    attempted += 1;
                    let p = &pts[k % pts.len()];
                    let q = &pts[(k / pts.len() + k + 3) % pts.len()];
                    let mut inputs = params.clone();
                    let attempt = (|| -> Result<()> {
                        let mut inputs_points = vec![(1, p.clone())];
                        let expected = match formula.operation.as_str() {
                            "addition" => {
                                inputs_points.push((2, q.clone()));
                                vec![(3, oracle(model, "addition", &field, &params, p, Some(q))?)]
                            }
                            "doubling" => {
                                vec![(3, oracle(model, "doubling", &field, &params, p, None)?)]
                            }
                            "tripling" => {
                                let d = oracle(model, "doubling", &field, &params, p, None)?;
                                vec![(3, oracle(model, "addition", &field, &params, p, Some(&d))?)]
                            }
                            "scaling" => vec![(3, p.clone())],
                            "diffadd" | "ladder" => {
                                let neg = oracle(model, "negation", &field, &params, p, None)?;
                                let difference =
                                    oracle(model, "addition", &field, &params, q, Some(&neg))?;
                                inputs_points =
                                    vec![(1, difference), (2, p.clone()), (3, q.clone())];
                                let sum = oracle(model, "addition", &field, &params, p, Some(q))?;
                                if formula.operation == "diffadd" {
                                    vec![(5, sum)]
                                } else {
                                    vec![
                                        (4, oracle(model, "doubling", &field, &params, p, None)?),
                                        (5, sum),
                                    ]
                                }
                            }
                            _ => panic!("uncovered operation {}", formula.operation),
                        };
                        for (index, p) in inputs_points {
                            let forced = formula
                                .assumptions
                                .iter()
                                .any(|s| s.replace(' ', "") == format!("Z{index}=1"));
                            let scale = if forced || k % 2 == 0 { 1 } else { index + 2 };
                            inputs.extend(rep.bind_point(
                                &rep.encode_affine(&field, &p.0, &p.1, &element(scale, m))?,
                                index,
                            ));
                        }
                        let output = program.evaluate(&field, &inputs)?;
                        for (index, p) in expected {
                            assert_eq!(
                                rep.project(&field, &output, index)?,
                                projection(rep, &p),
                                "{} over GF(2^{m}), k={k}",
                                formula.id
                            );
                        }
                        Ok(())
                    })();
                    match attempt {
                        Ok(()) => passed += 1,
                        Err(EfdError::ZeroDenominator | EfdError::OutsideChart) => {}
                        Err(e) => panic!("{} GF(2^{m}) k={k}: {e}", formula.id),
                    }
                    if passed == 32 {
                        break;
                    }
                }
                assert!(
                    passed >= 16,
                    "{} over GF(2^{m}): only {passed} comparable cases",
                    formula.id
                );
                coverage.push(serde_json::json!({"formula":formula.id,
                    "field_degree":m,"modulus_low_terms":field.low_terms,
                    "passed":passed,"attempted":attempted,
                    "excluded_singular_affine_charts":attempted-passed}));
            }
        }
    }
    if let Some(path) = std::env::var_os("EFD_COVERAGE_OUT") {
        std::fs::write(path, serde_json::to_vec_pretty(&coverage).unwrap()).unwrap();
    }
}

fn binary_curve(m: u32, a: u32) -> BinaryCurve {
    BinaryCurve {
        m,
        irreducible: field(m),
        a: element(a, m),
        b: element(3, m),
        generator: BinaryPoint::Infinity,
        order: BigUint::from(0u32),
        cofactor: BigUint::from(0u32),
    }
}
fn binary(p: &Affine) -> BinaryPoint {
    BinaryPoint::Affine {
        x: p.0.clone(),
        y: p.1.clone(),
    }
}

#[test]
fn checked_weierstrass_formulas_match_existing_independent_arithmetic() {
    for a in [0, 1, 2] {
        let curve = binary_curve(5, a);
        let model = catalogue()
            .models
            .iter()
            .find(|m| m.id == "shortw")
            .unwrap();
        let params = Bindings::from([
            ("a2".into(), curve.a.clone()),
            ("a6".into(), curve.b.clone()),
        ]);
        let ps = points(model, &curve.irreducible, &params);
        for formula in catalogue().formulas.iter().filter(|f| {
            f.representation.starts_with("shortw/")
                && f.representation != "shortw/xz"
                && matches!(f.operation.as_str(), "addition" | "doubling")
        }) {
            if (formula.representation.ends_with("-0") && a != 0)
                || (formula.representation.ends_with("-1") && a != 1)
            {
                continue;
            }
            let mut actual_formula = 0;
            for i in 0..ps.len() {
                let p = binary(&ps[i]);
                let q = binary(&ps[(i + 5) % ps.len()]);
                let result = weierstrass_operation(
                    &curve,
                    &formula.id,
                    &p,
                    if formula.operation == "addition" {
                        Some(&q)
                    } else {
                        None
                    },
                )
                .unwrap();
                let expected = if formula.operation == "addition" {
                    point_add(&curve, &p, &q)
                } else {
                    point_double(&curve, &p)
                };
                assert_eq!(result.point, expected, "{} a={a}", formula.id);
                actual_formula += usize::from(result.path == ExecutionPath::Formula);
            }
            assert!(
                actual_formula >= 8,
                "{}: did not exercise formula",
                formula.id
            );
        }
    }
}

#[test]
fn large_field_planted_points_match_existing_arithmetic() {
    // Public generators, with known small scalar multiples; no imported target.
    for curve in [
        BinaryCurve::sect113r1(),
        BinaryCurve::sect131r1(),
        BinaryCurve::sect163k1(),
    ] {
        let p = point_double(&curve, &curve.generator);
        let q = point_add(&curve, &p, &curve.generator);
        for formula in catalogue().formulas.iter().filter(|f| {
            f.representation.starts_with("shortw/")
                && f.representation != "shortw/xz"
                && matches!(f.operation.as_str(), "addition" | "doubling")
        }) {
            if (formula.representation.ends_with("-0") && !curve.a.is_zero())
                || (formula.representation.ends_with("-1") && curve.a != F2mElement::one(curve.m))
            {
                continue;
            }
            let addition = formula.operation == "addition";
            let result = weierstrass_operation(
                &curve,
                &formula.id,
                &p,
                if addition { Some(&q) } else { None },
            )
            .unwrap();
            assert_eq!(
                result.path,
                ExecutionPath::Formula,
                "{} m={}",
                formula.id,
                curve.m
            );
            assert_eq!(
                result.point,
                if addition {
                    point_add(&curve, &p, &q)
                } else {
                    point_double(&curve, &p)
                },
                "{} m={}",
                formula.id,
                curve.m
            );
        }
    }
}

#[test]
fn rejects_mixed_specialization_cache_and_field_mismatches() {
    let c = catalogue();
    let field = field(5);
    let rep = c.representation("shortw/extended-0").unwrap();
    let mut v = Bindings::from([("a2".into(), element(0, 5)), ("a6".into(), element(3, 5))]);
    v.extend(
        rep.bind_point(
            &rep.encode_affine(&field, &element(2, 5), &element(3, 5), &element(2, 5))
                .unwrap(),
            1,
        ),
    );
    v.extend(
        rep.bind_point(
            &rep.encode_affine(&field, &element(4, 5), &element(5, 5), &element(3, 5))
                .unwrap(),
            2,
        ),
    );
    let mixed = c
        .formula("shortw/extended-0/addition/madd-2005-dl")
        .unwrap();
    assert!(matches!(
        mixed.evaluate(&field, &v),
        Err(EfdError::Assumption(_))
    ));
    v.insert("Z2".into(), element(1, 5));
    v.insert("ZZ1".into(), element(1, 5));
    assert!(matches!(
        mixed.evaluate(&field, &v),
        Err(EfdError::Assumption(_))
    ));
    v.insert("a2".into(), element(1, 5));
    assert!(matches!(
        mixed.evaluate(&field, &v),
        Err(EfdError::Assumption(_))
    ));
    v.insert("a2".into(), element(1, 4));
    assert_eq!(mixed.evaluate(&field, &v), Err(EfdError::FieldMismatch));
    assert!(Expr::parse("a; panic!()").is_err());
    assert!(Expr::parse("a ^ 100000000").is_err());
}

#[test]
fn handles_zero_inversion_infinity_opposites_and_lambda_chart() {
    let curve = binary_curve(5, 0);
    let field = &curve.irreducible;
    assert_eq!(
        Expr::parse("1/0").unwrap().eval(field, &Bindings::new()),
        Err(EfdError::ZeroDenominator)
    );
    let id = "shortw/lambda/addition/add-2013-olar";
    let model = catalogue()
        .models
        .iter()
        .find(|m| m.id == "shortw")
        .unwrap();
    let params = Bindings::from([
        ("a2".into(), curve.a.clone()),
        ("a6".into(), curve.b.clone()),
    ]);
    let ps = points(model, field, &params);
    let p = binary(&ps[3]);
    let neg = super::super::curve::point_neg(&p);
    for q in [&p, &neg, &BinaryPoint::Infinity] {
        let r = weierstrass_operation(&curve, id, &p, Some(q)).unwrap();
        assert_eq!(r.point, point_add(&curve, &p, q));
        assert_eq!(r.path, ExecutionPath::AffineExceptional);
    }
    let zero = ps.iter().find(|p| p.0.is_zero()).unwrap();
    assert_eq!(
        catalogue()
            .representation("shortw/lambda")
            .unwrap()
            .encode_affine(field, &zero.0, &zero.1, &element(1, 5)),
        Err(EfdError::OutsideChart)
    );
    assert!(matches!(
        weierstrass_operation(&curve, id, &binary(zero), Some(&p))
            .unwrap()
            .path,
        ExecutionPath::AffineExceptional
    ));
    let invalid = BinaryPoint::Affine {
        x: element(0, 5),
        y: element(0, 5),
    };
    assert_eq!(
        weierstrass_operation(&curve, id, &invalid, Some(&p)),
        Err(EfdError::InvalidPoint)
    );
}

#[test]
fn preserves_lambda_costs_and_parameter_checks() {
    let f = catalogue()
        .formula("shortw/lambda/addition/add-2013-olar")
        .unwrap();
    assert_eq!(
        f.compile().unwrap().operation_counts(),
        OperationCounts {
            multiplications: 11,
            squarings: 2,
            inversions: 0,
            additions: 5
        }
    );
    let f = catalogue()
        .formula("shortw/lambda/doubling/dbl-2013-olar-2")
        .unwrap();
    let curve = binary_curve(5, 0);
    let field = &curve.irreducible;
    let mut inputs = Bindings::from([
        ("a2".into(), curve.a.clone()),
        ("a6".into(), curve.b.clone()),
        ("X1".into(), element(2, 5)),
        ("L1".into(), element(3, 5)),
        ("Z1".into(), element(1, 5)),
    ]);
    let derived = f.evaluate(field, &inputs).unwrap();
    assert_eq!(derived["a21"], element(1, 5));
    inputs.insert("a21".into(), element(0, 5));
    assert!(matches!(
        f.evaluate(field, &inputs),
        Err(EfdError::Assumption(_))
    ));
}
