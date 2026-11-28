//! Check one saved M31 certificate with two native arithmetic implementations.
//! Local replay is not a signed independent PCC verdict.
use cryptanalysis_suite::cryptanalysis::ic_boundary::{
    CountedGroup, GroupOps, PrimeCurve, PrimePoint,
};
use prime_field_auxiliary_ic::{
    verify_multi_certificate, Curve, FactorBase, MultiCertificate, MultiRelation,
    MultiSignedRelation, SignedTerm,
};
use serde_json::{json, Value};
use std::{fs::File, io::Read, process::ExitCode};
const P: u64 = 2_147_483_647;
const N: u64 = 2_147_505_293;
const MAX_BYTES: u64 = 64 * 1024 * 1024;
type Check<T> = Result<T, String>;
fn uint(v: &Value) -> Check<u64> {
    v.as_u64()
        .ok_or_else(|| "expected an unsigned integer".into())
}
fn array(v: &Value) -> Check<&Vec<Value>> {
    v.as_array().ok_or_else(|| "expected an array".into())
}
fn coords(v: &Value) -> Check<(u64, u64)> {
    let a = array(v)?;
    if a.len() != 2 {
        return Err("point needs exactly two coordinates".into());
    }
    let (x, y) = (uint(&a[0])?, uint(&a[1])?);
    if x >= P || y >= P {
        return Err("point coordinates are not canonical".into());
    }
    Ok((x, y))
}
fn check(r: &Value, expected: Option<(u64, u64)>) -> Check<Value> {
    if r["schema"] != "m31-e2e-native/v1"
        || r["status"] != "solved"
        || r["p"] != P
        || r["a"] != 2
        || r["b"] != 14
        || r["n"] != N
        || r["G"] != json!([1, 814455902])
    {
        return Err("not a solved report for the fixed M31 lab curve/generator".into());
    }
    let c = Curve::<31>::new(2, 14).map_err(|e| e.to_string())?;
    let g = c.point(1, 814455902).map_err(|e| e.to_string())?;
    let (qx, qy) = coords(&r["Q"])?;
    if expected.is_some_and(|q| q != (qx, qy)) {
        return Err("report target does not match the expected public target".into());
    }
    let q = c.point(qx, qy).map_err(|e| e.to_string())?;
    let proof = &r["certificate"];
    if proof["order"] != N
        || proof["generator"] != r["G"]
        || proof["target"] != r["Q"]
        || proof["summands"] != r["summands"]
        || proof["scalar"] != r["scalar"]
    {
        return Err("certificate is not bound to the reported parameters/scalar".into());
    }
    let m = uint(&proof["summands"])?;
    if !(2..=4).contains(&m) {
        return Err("summands must be 2..=4".into());
    }
    let values = array(&r["base_points"])?;
    if values.is_empty() || values.len() > 2048 || uint(&r["columns"])? != values.len() as u64 {
        return Err("invalid or inconsistent factor-base size".into());
    }
    let mut points = Vec::with_capacity(values.len());
    for v in values {
        let (x, y) = coords(v)?;
        points.push(c.point(x, y).map_err(|e| e.to_string())?);
    }
    let roots: Vec<_> = points.iter().map(|p| p.x()).collect();
    let base = FactorBase::without_maps(c, &roots).map_err(|e| e.to_string())?;
    if base.representatives() != points {
        return Err("factor-base points are not the canonical distinct representatives".into());
    }
    let row_values = array(&proof["relations"])?;
    if row_values.len() > 1_000_000 {
        return Err("certificate exceeds the row bound".into());
    }
    let mut rows = Vec::with_capacity(row_values.len());
    for row in row_values {
        let mut terms = Vec::new();
        for t in array(&row["terms"])? {
            let i = uint(&t["column"])?;
            let sign = t["sign"].as_i64().ok_or("invalid sign")?;
            if i >= points.len() as u64 || (sign != 1 && sign != -1) {
                return Err("invalid signed column".into());
            }
            terms.push(SignedTerm {
                index: i as usize,
                negative: sign == -1,
            });
        }
        if terms.len() != m as usize {
            return Err("row arity does not match the certificate".into());
        }
        rows.push(MultiRelation {
            a: uint(&row["a"])?,
            b: uint(&row["b"])?,
            decomposition: MultiSignedRelation::new(&terms).map_err(|e| e.to_string())?,
        });
    }
    let weights = array(&proof["weights"])?
        .iter()
        .map(uint)
        .collect::<Check<Vec<_>>>()?;
    let cert = MultiCertificate {
        summands: m as u8,
        order: N,
        generator: g,
        target: q,
        scalar: uint(&proof["scalar"])?,
        relations: rows,
        weights,
    };
    verify_multi_certificate(&base, &cert).map_err(|e| e.to_string())?;
    // Distinct PrimeCurve arithmetic also checks every signed row and recovered key.
    let other = PrimeCurve { p: P, a: 2, b: 14 };
    let gg = PrimePoint::affine(1, 814455902);
    let qq = PrimePoint::affine(qx, qy);
    let mut ops = GroupOps::default();
    if other.mul(&mut ops, gg, cert.scalar) != qq {
        return Err("second-arithmetic scalar replay failed".into());
    }
    for row in &cert.relations {
        let ag = other.mul(&mut ops, gg, row.a);
        let bq = other.mul(&mut ops, qq, row.b);
        let lhs = other.add(&mut ops, ag, bq);
        let mut rhs = other.identity();
        for t in row.decomposition.summands() {
            let p = points[t.index];
            let p = PrimePoint::affine(p.x(), p.y());
            rhs = other.add(&mut ops, rhs, if t.negative { other.neg(p) } else { p });
        }
        if lhs != rhs {
            return Err("second-arithmetic signed row replay failed".into());
        }
    }
    Ok(
        json!({"schema":"m31-certificate-check/v1","status":"checked","p":P,"Q":[qx,qy],"scalar":cert.scalar,"rows":cert.relations.len(),"summands":m,"columns":points.len(),"native_full_certificate_replay":true,"second_arithmetic_row_and_scalar_replay":true,"producer_only":true,"independent_signature":false,"standing":"pcc:unverified"}),
    )
}
fn run() -> Check<Value> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    let mut reader = File::open(&args[0])
        .map_err(|e| e.to_string())?
        .take(MAX_BYTES + 1);
    let mut bytes = Vec::new();
    reader.read_to_end(&mut bytes).map_err(|e| e.to_string())?;
    if bytes.len() as u64 > MAX_BYTES {
        return Err("input exceeds 64 MiB".into());
    }
    let expected = if args.len() == 5 && args[1] == "--qx" && args[3] == "--qy" {
        Some((
            args[2].parse().map_err(|_| "invalid expected x")?,
            args[4].parse().map_err(|_| "invalid expected y")?,
        ))
    } else if args.len() == 1 {
        None
    } else {
        return Err("expected --qx X --qy Y together".into());
    };
    let value: Value = serde_json::from_slice(&bytes).map_err(|e| e.to_string())?;
    check(&value, expected)
}
fn main() -> ExitCode {
    let args: Vec<_> = std::env::args().collect();
    if args.len() == 2 && (args[1] == "--help" || args[1] == "-h") {
        println!("Usage: m31-verify report.json [--qx X --qy Y]\nChecks the full signed dependency and scalar through two native arithmetic paths.\nLocal certificate replay does not assert a signed independent PCC verdict.");
        return ExitCode::SUCCESS;
    }
    if args.len() < 2 {
        eprintln!("Usage: m31-verify report.json [--qx X --qy Y]");
        return ExitCode::from(2);
    }
    match run() {
        Ok(r) => {
            println!("{r}");
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("m31-verify: {e}");
            ExitCode::FAILURE
        }
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn fixture() -> Value {
        let c = Curve::<31>::new(2, 14).unwrap();
        let g = c.point(1, 814455902).unwrap();
        let actual: Vec<_> = (1..=3)
            .map(|i| c.mul(Some(g), i).unwrap().unwrap())
            .collect();
        let mut base: Vec<_> = actual
            .iter()
            .map(|p| c.lift_x(p.x()).unwrap().unwrap())
            .collect();
        base.sort_unstable_by_key(|p| p.x());
        let term = |i: usize, negative: bool| {
            let column = base.iter().position(|p| p.x() == actual[i].x()).unwrap();
            json!({"column":column,"sign":if (actual[i]!=base[column]) ^ negative {-1}else{1}})
        };
        let point = |p: prime_field_auxiliary_ic::Point| json!([p.x(), p.y()]);
        json!({"schema":"m31-e2e-native/v1","status":"solved","p":P,"a":2,"b":14,"n":N,"G":point(g),"Q":point(actual[1]),"columns":3,"base_points":base.iter().copied().map(point).collect::<Vec<_>>(),"summands":2,"scalar":2,"certificate":{"order":N,"generator":point(g),"target":point(actual[1]),"summands":2,"scalar":2,"weights":[1,N-1,N-1],"relations":[{"a":3,"b":0,"terms":[term(0,false),term(1,false)]},{"a":5,"b":0,"terms":[term(1,false),term(2,false)]},{"a":N-4,"b":1,"terms":[term(0,false),term(2,true)]}]}})
    }
    #[test]
    fn accepts_complete_three_row_dependency_and_binds_expected_target() {
        let r = fixture();
        let q = coords(&r["Q"]).unwrap();
        check(&r, Some(q)).expect("valid three-row proof");
        assert!(check(&r, Some((1, 814455902))).is_err());
    }
    #[test]
    fn rejects_corrupt_or_truncated_proofs_and_report_substitution() {
        let r = fixture();
        for pointer in [
            "/scalar",
            "/certificate/scalar",
            "/certificate/weights/0",
            "/certificate/relations/0/a",
            "/certificate/relations/0/terms/0/sign",
            "/certificate/relations/0/terms/0/column",
            "/n",
            "/columns",
            "/G/0",
            "/base_points/0/0",
        ] {
            let mut bad = r.clone();
            *bad.pointer_mut(pointer).unwrap() = json!(9999999999u64);
            assert!(check(&bad, None).is_err(), "{pointer}");
        }
        let mut bad = r.clone();
        bad["certificate"]["relations"]
            .as_array_mut()
            .unwrap()
            .pop();
        assert!(check(&bad, None).is_err());
        let mut bad = r.clone();
        bad["certificate"]["relations"][1] = bad["certificate"]["relations"][0].clone();
        assert!(check(&bad, None).is_err());
        let mut bad = r;
        bad["status"] = json!("incomplete");
        assert!(check(&bad, None).is_err());
    }
}
