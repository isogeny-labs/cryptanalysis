use super::super::curve::{point_add, point_double, BinaryCurve, BinaryPoint};
use super::*;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ExecutionPath {
    Formula,
    AffineExceptional,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CheckedPoint {
    pub point: BinaryPoint,
    pub path: ExecutionPath,
}

/// Interoperable, checked, finite-chart EFD ADD/DBL. Conversion and validation
/// are charged to this API; it is a reference adapter, not a faster walk.
/// Infinity, equal/opposite inputs and lambda-chart exceptions use the existing
/// complete affine law and expose that fallback in `path`.
pub fn weierstrass_operation(
    curve: &BinaryCurve,
    id: &str,
    p: &BinaryPoint,
    q: Option<&BinaryPoint>,
) -> Result<CheckedPoint> {
    let formula = catalogue()
        .formula(id)
        .ok_or_else(|| EfdError::Unsupported(id.into()))?;
    if !formula.representation.starts_with("shortw/")
        || formula.representation == "shortw/xz"
        || !matches!(formula.operation.as_str(), "addition" | "doubling")
    {
        return Err(EfdError::Unsupported(id.into()));
    }
    if (formula.operation == "addition") != q.is_some() {
        return Err(EfdError::Unsupported(
            "ADD takes two points, DBL one".into(),
        ));
    }
    let field = &curve.irreducible;
    let mut inputs = Bindings::from([
        ("a2".into(), curve.a.clone()),
        ("a6".into(), curve.b.clone()),
    ]);
    check_field(field, &inputs)?;
    if curve.m != field.degree || curve.b.is_zero() {
        return Err(EfdError::InvalidPoint);
    }
    for point in std::iter::once(p).chain(q) {
        if let BinaryPoint::Affine { x, y } = point {
            if x.m_value() != curve.m || y.m_value() != curve.m || !curve.is_on_curve(point) {
                return Err(EfdError::InvalidPoint);
            }
        }
    }
    let rep = catalogue().representation(&formula.representation).unwrap();
    // Do not allow an exceptional-case fallback to bypass specialization checks.
    for assumption in &rep.assumptions {
        let (a, b) = program::equality(assumption)?;
        if a.eval(field, &inputs)? != b.eval(field, &inputs)? {
            return Err(EfdError::Assumption(assumption.clone()));
        }
    }
    let fallback = || CheckedPoint {
        point: if let Some(q) = q {
            point_add(curve, p, q)
        } else {
            point_double(curve, p)
        },
        path: ExecutionPath::AffineExceptional,
    };
    let BinaryPoint::Affine { x, y } = p else {
        return Ok(fallback());
    };
    if x.is_zero() {
        return Ok(fallback());
    }
    if let Some(other) = q {
        let BinaryPoint::Affine { x: qx, .. } = other else {
            return Ok(fallback());
        };
        if qx == x || qx.is_zero() {
            return Ok(fallback());
        }
    }
    inputs.extend(rep.bind_point(
        &rep.encode_affine(field, x, y, &F2mElement::one(curve.m))?,
        1,
    ));
    if let Some(BinaryPoint::Affine { x, y }) = q {
        inputs.extend(rep.bind_point(
            &rep.encode_affine(field, x, y, &F2mElement::one(curve.m))?,
            2,
        ));
    }
    let output = match formula.evaluate(field, &inputs) {
        Ok(v) => v,
        Err(EfdError::ZeroDenominator) => return Ok(fallback()),
        Err(e) => return Err(e),
    };
    let (x, y) = match rep.project(field, &output, 3) {
        Ok(Projection::Full { x, y }) => (x, y),
        Err(EfdError::OutsideChart) => return Ok(fallback()),
        Err(e) => return Err(e),
        _ => return Err(EfdError::Unsupported(id.into())),
    };
    let point = BinaryPoint::Affine { x, y };
    if !curve.is_on_curve(&point) {
        return Err(EfdError::InvalidPoint);
    }
    Ok(CheckedPoint {
        point,
        path: ExecutionPath::Formula,
    })
}
