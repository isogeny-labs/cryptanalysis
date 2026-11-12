//! Independently encoded recomputation of the fixed public kernel record.
//! Existing arithmetic engines only; no producer constructors/Chart/pull/psi49.
use isogeny_algos::bigint::Big;
use isogeny_algos::curve::{self, Curve, Isogeny, Pt, RatIsogeny};
use isogeny_algos::field::{Field, Zp};
use isogeny_algos::find::divpoly::division_poly;
use isogeny_algos::fpr::{FpR, ER};
use isogeny_algos::kernel::kohel::kohel;
use isogeny_algos::poly;
use serde_json::Value;
use std::collections::{HashMap, HashSet};

#[allow(dead_code)]
#[path = "../../../../../crypto/research/chained_jacobian_transfers_20261110/successor-preflight/src/legacy_jacobian.rs"]
mod legacy;

type Check<T> = Result<T, String>;
fn require(condition: bool, message: &str) -> Check<()> {
    if condition {
        Ok(())
    } else {
        Err(message.to_owned())
    }
}
fn array(v: &Value, size: usize) -> Check<&Vec<Value>> {
    let a = v.as_array().ok_or("expected array")?;
    require(a.len() == size, "array length")?;
    Ok(a)
}
fn number(v: &Value) -> Check<u64> {
    v.as_u64()
        .ok_or_else(|| "expected unsigned integer".to_owned())
}
fn fp(v: &Value) -> Check<u64> {
    let x = number(v)?;
    require(x < 101, "noncanonical coefficient")?;
    Ok(x)
}
fn polynomial(v: &Value, max: usize) -> Check<Vec<u64>> {
    let a = v.as_array().ok_or("expected polynomial")?;
    require(a.len() <= max, "polynomial size")?;
    let out = a.iter().map(fp).collect::<Check<Vec<_>>>()?;
    require(out.last() != Some(&0), "trailing zero coefficient")?;
    Ok(out)
}
fn er(v: &Value) -> Check<ER> {
    let a = array(v, 16)?;
    let mut out = [0; 16];
    for (i, v) in a.iter().enumerate() {
        out[i] = fp(v)?;
    }
    require(out[12..].iter().all(|&v| v == 0), "extension padding")?;
    Ok(out)
}
fn er_poly(v: &Value, max: usize) -> Check<Vec<ER>> {
    let a = v.as_array().ok_or("extension polynomial")?;
    require(a.len() <= max, "extension polynomial size")?;
    let out = a.iter().map(er).collect::<Check<Vec<_>>>()?;
    require(out.last() != Some(&[0; 16]), "extension trailing zero")?;
    Ok(out)
}
fn point(v: &Value) -> Check<Pt<ER>> {
    if v.is_null() {
        return Ok(Pt::Inf);
    }
    let o = v.as_object().ok_or("point object")?;
    require(
        o.len() == 2 && o.contains_key("x") && o.contains_key("y"),
        "point fields",
    )?;
    Ok(Pt::Aff(er(&v["x"])?, er(&v["y"])?))
}

// Homogeneous Horner evaluation; producer assembles explicit cubic powers.
fn homogeneous<F: Field>(f: &F, coefficients: &[F::E], n: &Vec<F::E>, d: &Vec<F::E>) -> Vec<F::E> {
    let mut out = vec![*coefficients.last().expect("nonempty fixed polynomial")];
    let mut denominator_power = vec![f.one()];
    for &c in coefficients[..coefficients.len() - 1].iter().rev() {
        denominator_power = poly::mul(f, &denominator_power, d);
        out = poly::add(
            f,
            &poly::mul(f, &out, n),
            &poly::scale(f, &denominator_power, c),
        );
    }
    out
}
fn cube<F: Field>(f: &F, p: &Vec<F::E>) -> Vec<F::E> {
    poly::mul(f, p, &poly::mul(f, p, p))
}
fn exact_map(f: &Zp, map: &RatIsogeny<Zp>) -> Check<()> {
    require(map.deg == 7 && map.ker.len() == 4, "degree7 map")?;
    require(
        curve::is_smooth(f, &map.dom) && curve::is_smooth(f, &map.cod),
        "smooth elliptic models",
    )?;
    require(
        map.den == poly::mul(f, &map.ker, &map.ker),
        "squared kernel denominator",
    )?;
    require(
        poly::gcd(f, &map.ker, &poly::derivative(f, &map.ker)) == vec![1],
        "squarefree degree7 kernel",
    )?;
    let source = vec![map.dom.b, map.dom.a, 0, 1];
    require(
        poly::gcd(f, &source, &map.ker) == vec![1],
        "kernel versus cubic",
    )?;
    require(
        poly::rem(f, &division_poly(f, &map.dom, 7), &map.ker).is_empty(),
        "kernel divides psi7",
    )?;
    let derivative = poly::sub(
        f,
        &poly::mul(f, &poly::derivative(f, &map.num), &map.den),
        &poly::mul(f, &map.num, &poly::derivative(f, &map.den)),
    );
    let target = poly::add(
        f,
        &poly::add(
            f,
            &cube(f, &map.num),
            &poly::scale(
                f,
                &poly::mul(f, &map.num, &poly::mul(f, &map.den, &map.den)),
                map.cod.a,
            ),
        ),
        &poly::scale(f, &cube(f, &map.den), map.cod.b),
    );
    require(
        poly::mul(f, &source, &poly::mul(f, &derivative, &derivative))
            == poly::mul(f, &map.den, &target),
        "exact normalized curve identity",
    )
}
fn polynomial_checks(j: &Value) -> Check<RatIsogeny<Zp>> {
    let f = Zp::new(101);
    require(
        j["elliptic_models"] == serde_json::json!([[1, 46], [26, 58], [59, 27]]),
        "public elliptic models",
    )?;
    let first = kohel(&f, &Curve::new(1, 46), &vec![72, 100, 35, 1], 7);
    let second = kohel(&f, &first.cod, &vec![99, 94, 75, 1], 7);
    require(
        first.cod == Curve::new(26, 58) && second.cod == Curve::new(59, 27),
        "actual Kohel targets",
    )?;
    exact_map(&f, &first)?;
    exact_map(&f, &second)?;
    for (key, p) in [
        ("h1", &first.ker),
        ("h2", &second.ker),
        ("N", &first.num),
        ("D", &first.den),
        ("second_N", &second.num),
        ("second_D", &second.den),
    ] {
        require(polynomial(&j[key], 8)? == *p, "map coefficient mismatch")?;
    }
    let p7 = division_poly(&f, &first.dom, 7);
    let p7sq = poly::mul(&f, &p7, &p7);
    let cubic = vec![46, 1, 0, 1];
    let p6p8 = poly::mul(
        &f,
        &division_poly(&f, &first.dom, 6),
        &division_poly(&f, &first.dom, 8),
    );
    let x7 = poly::sub(
        &f,
        &poly::mul(&f, &vec![0, 1], &p7sq),
        &poly::scale(&f, &poly::mul(&f, &cubic, &p6p8), 4),
    );
    require(
        x7.len() == 50 && x7.last() == Some(&1),
        "multiplication7 numerator",
    )?;
    let p49 = poly::mul(&f, &p7, &homogeneous(&f, &p7, &x7, &p7sq));
    require(
        p49.len() == 1201 && p49.last() == Some(&49),
        "composition psi49 degree/leading",
    )?;
    require(
        polynomial(&j["psi7"], 25)? == p7 && polynomial(&j["psi49"], 1201)? == p49,
        "independent psi49 composition",
    )?;
    let composed_num = homogeneous(&f, &second.num, &first.num, &first.den);
    let composed_den = poly::mul(
        &f,
        &first.den,
        &homogeneous(&f, &second.den, &first.num, &first.den),
    );
    let h = polynomial(&j["h49"], 25)?;
    require(h.len() == 25 && h.last() == Some(&1), "monic degree24 h49")?;
    require(
        poly::mul(&f, &h, &h) == composed_den,
        "composed denominator equals h49 square",
    )?;
    require(
        poly::gcd(&f, &composed_num, &composed_den) == vec![1],
        "composed map no cancellation",
    )?;
    require(
        poly::gcd(&f, &h, &poly::derivative(&f, &h)) == vec![1]
            && poly::gcd(&f, &h, &cubic) == vec![1],
        "squarefree and cubic-coprime h49",
    )?;
    let (quotient, remainder) = poly::divrem(&f, &p49, &h);
    require(
        remainder.is_empty() && quotient == polynomial(&j["quotient"], 1177)?,
        "exact independent psi49 quotient",
    )?;
    require(
        poly::gcd(&f, &h, &p7) == first.ker,
        "intersection with seven torsion",
    )?;
    let rows = array(&j["frobenius_gcds"], 4)?;
    // Binary big-exponent evaluation, separate from producer's iterated p powers.
    for (row, degree) in rows.iter().zip([1, 3, 7, 21]) {
        require(number(&row["degree"])? == degree, "Frobenius gcd degree")?;
        let mut exponent = Big::from_u64(1);
        for _ in 0..degree {
            exponent = exponent.mul_small(101);
        }
        let x = vec![0, 1];
        let gcd = poly::gcd(
            &f,
            &h,
            &poly::sub(&f, &poly::powmod_big(&f, &x, &exponent, &h), &x),
        );
        let expected = match degree {
            3 => first.ker.clone(),
            21 => h.clone(),
            _ => vec![1],
        };
        require(
            gcd == expected && polynomial(&row["gcd"], 25)? == gcd,
            "exact Frobenius gcd",
        )?;
    }
    Ok(first)
}

struct Flat<'a>(&'a FpR);
impl legacy::Fld for Flat<'_> {
    type E = ER;
    fn zero(&self) -> ER {
        self.0.zero()
    }
    fn one(&self) -> ER {
        self.0.one()
    }
    fn add(&self, a: &ER, b: &ER) -> ER {
        self.0.add(*a, *b)
    }
    fn sub(&self, a: &ER, b: &ER) -> ER {
        self.0.sub(*a, *b)
    }
    fn neg(&self, a: &ER) -> ER {
        self.0.neg(*a)
    }
    fn mul(&self, a: &ER, b: &ER) -> ER {
        self.0.mul(*a, *b)
    }
    fn inv(&self, a: &ER) -> ER {
        self.0.inv(*a)
    }
}
fn lifted(f: &FpR, p: &[u64]) -> Vec<ER> {
    p.iter().map(|&v| f.from_u64(v)).collect()
}
fn pull(
    f: &FpR,
    jac: &legacy::Hyp<'_, Flat<'_>>,
    a: ER,
    l: ER,
    p: Pt<ER>,
) -> Check<legacy::Div<ER>> {
    let Pt::Aff(x, y) = p else {
        return Ok(jac.identity());
    };
    let lead = f.add(f.sub(f.sq(a), x), f.from_u64(2));
    require(lead != f.zero(), "odd7 pull avoids branch corner")?;
    let u = poly::monic(f, &vec![f.sq(l), f.mul(f.from_u64(2), f.mul(a, l)), lead]);
    let v = poly::rem(f, &vec![f.zero(), f.zero(), f.zero(), f.div(y, l)], &u);
    let out = legacy::Div { u, v };
    require(jac.is_valid(&out), "independent pull valid")?;
    Ok(jac.reduce(out))
}
fn geometric_checks(j: &Value, first: &RatIsogeny<Zp>) -> Check<()> {
    let modulus = polynomial(&j["field_modulus"], 13)?;
    require(
        modulus.len() == 13 && modulus.last() == Some(&1),
        "degree12 modulus",
    )?;
    let f = FpR::from_modulus(101, &modulus);
    require(
        j["source_sextic"] == serde_json::json!([56, 0, 13, 0, 6, 0, 1])
            && j["target_sextic"] == serde_json::json!([89, 0, 93, 0, 8, 0, 61]),
        "raw sextic models",
    )?;
    let sextic = lifted(&f, &[56, 0, 13, 0, 6, 0, 1]);
    let a = er(&j["chart_a"])?;
    let l = er(&j["chart_l"])?;
    require(
        poly::eval(&f, &sextic, a) == f.zero()
            && l != f.zero()
            && l == poly::eval(&f, &poly::derivative(&f, &sextic), a),
        "actual chart anchor and derivative",
    )?;
    let quintic = poly::scale(
        &f,
        &homogeneous(&f, &sextic, &vec![l, a], &vec![f.zero(), f.one()]),
        f.inv(f.sq(l)),
    );
    require(
        quintic.len() == 6
            && quintic.last() == Some(&f.one())
            && quintic == er_poly(&j["chart_quintic"], 6)?,
        "independent chart substitution",
    )?;
    let flat = Flat(&f);
    let jac = legacy::Hyp {
        f: &flat,
        h: quintic,
        g: 2,
    };
    let alpha = RatIsogeny {
        dom: Curve::new(f.from_u64(1), f.from_u64(46)),
        cod: Curve::new(f.from_u64(26), f.from_u64(58)),
        deg: 7,
        ker: lifted(&f, &first.ker),
        num: lifted(&f, &first.num),
        den: lifted(&f, &first.den),
    };
    let points = array(&j["E7_points"], 49)?
        .iter()
        .map(point)
        .collect::<Check<Vec<_>>>()?;
    let images = array(&j["alpha_points"], 49)?
        .iter()
        .map(point)
        .collect::<Check<Vec<_>>>()?;
    require(
        points[0] == Pt::Inf && points.iter().copied().collect::<HashSet<_>>().len() == 49,
        "49 distinct seven points",
    )?;
    let indices = points
        .iter()
        .copied()
        .enumerate()
        .map(|(i, p)| (p, i))
        .collect::<HashMap<_, _>>();
    let mut pulls = vec![];
    let mut kernel = vec![];
    let mut different = 0;
    let mut equal = 0;
    for (i, &p) in points.iter().enumerate() {
        require(
            curve::on_curve(&f, &alpha.dom, &p) && curve::pmul(&f, &alpha.dom, &p, 7) == Pt::Inf,
            "actual geometric seven torsion",
        )?;
        let image = alpha.eval(&f, &p);
        require(image == images[i], "actual alpha image")?;
        let d = pull(&f, &jac, a, l, p)?;
        require(jac.mul(&d, 7) == jac.identity(), "pull killed by7")?;
        if image == Pt::Inf {
            kernel.push(i);
        }
        let twice = curve::pmul(&f, &alpha.cod, &image, 2);
        require(
            curve::pmul(&f, &alpha.cod, &twice, 4) == image,
            "correct geometric half",
        )?;
        if curve::pmul(&f, &alpha.cod, &twice, 55) == image {
            equal += 1;
        } else {
            different += 1;
        }
        pulls.push(d);
    }
    require(
        pulls
            .iter()
            .map(|d| (d.u.clone(), d.v.clone()))
            .collect::<HashSet<_>>()
            .len()
            == 49,
        "49 distinct actual pulls",
    )?;
    require(
        kernel.len() == 7 && different == 42 && equal == 7,
        "kernel and wrong-half counts",
    )?;
    require(
        number(&j["correct_half_mod7"])? == 4
            && number(&j["wrong_half"])? == 55
            && number(&j["wrong_different"])? == different
            && number(&j["wrong_equal"])? == equal,
        "recorded counts recomputed",
    )?;
    let frobenius = array(&j["frobenius_indices"], 49)?;
    for (i, &p) in points.iter().enumerate() {
        let pi = match p {
            Pt::Inf => Pt::Inf,
            Pt::Aff(x, y) => Pt::Aff(f.frobenius(x), f.frobenius(y)),
        };
        let next = *indices.get(&pi).ok_or("Frobenius outside seven group")?;
        require(
            number(&frobenius[i])? == next as u64,
            "actual Frobenius index",
        )?;
        if kernel.contains(&i) {
            require(
                pi == curve::pmul(&f, &alpha.dom, &p, 5) && pulls[next] == jac.mul(&pulls[i], 5),
                "actual kernel Frobenius5",
            )?;
        }
        for (k, &q) in points.iter().enumerate() {
            let sum = curve::padd(&f, &alpha.dom, &p, &q);
            let next = *indices.get(&sum).ok_or("seven group not closed")?;
            require(
                jac.add(&pulls[i], &pulls[k]) == pulls[next],
                "all2401 independent pull additions",
            )?;
        }
    }
    let records = array(&j["kernel_divisors"], 7)?;
    let mut row_indices = vec![];
    for row in records {
        let i =
            usize::try_from(number(&row["point_index"])?).map_err(|_| "point index overflow")?;
        require(kernel.contains(&i), "kernel record index")?;
        require(
            er_poly(&row["u"], 3)? == pulls[i].u && er_poly(&row["v"], 2)? == pulls[i].v,
            "actual independent kernel Mumford coordinates",
        )?;
        row_indices.push(i);
    }
    require(
        row_indices.iter().copied().collect::<HashSet<_>>() == kernel.iter().copied().collect(),
        "complete seven kernel records",
    )?;
    let sums = array(&j["kernel_sum_indices"], 7)?;
    for (i, &p) in row_indices.iter().enumerate() {
        let row = array(&sums[i], 7)?;
        for (k, &q) in row_indices.iter().enumerate() {
            let next = number(&row[k])? as usize;
            // The wire table stores indices into all49 E7 points, not7 rows.
            require(next < 49 && kernel.contains(&next), "kernel sum index")?;
            require(
                jac.add(&pulls[p], &pulls[q]) == pulls[next],
                "all49 native kernel table entries",
            )?;
        }
    }
    Ok(())
}
fn verify(j: &Value) -> Check<()> {
    require(
        j["schema"] == "chained-even-kernel/v1"
            && number(&j["p"])? == 101
            && number(&j["extension_degree"])? == 12,
        "schema/field",
    )?;
    let first = polynomial_checks(j)?;
    geometric_checks(j, &first)
}
fn checked(j: &Value) -> Check<()> {
    std::panic::catch_unwind(|| verify(j)).map_err(|_| "invalid arithmetic input".to_owned())?
}
fn main() {
    let outcome = (|| -> Check<()> {
        let args = std::env::args().collect::<Vec<_>>();
        require(args.len() == 2, "usage:checker kernel-certificate.json")?;
        let bytes = std::fs::read(&args[1]).map_err(|e| e.to_string())?;
        require(bytes.len() <= 1_048_576, "input size")?;
        let value: Value = serde_json::from_slice(&bytes).map_err(|e| e.to_string())?;
        checked(&value)?;
        println!("PASS independent kernel:psi49degree1200 reconstructed through6,7,8;composeddenominator=h49square;exactquotient/gcd/DDF3+21;49actualsevenpoints/independentC0pulls/all2401adds/7actualkernelMumfordrecords/49tableentries/Frobenius5/wronghalf42vs7;existingengines;unsigned");
        Ok(())
    })();
    if let Err(e) = outcome {
        eprintln!("REJECT {e}");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn original() -> Value {
        serde_json::from_slice(include_bytes!("../../../../../crypto/research/chained_jacobian_transfers_20261110/evidence/kernel-full-03/kernel-certificate.json")).unwrap()
    }
    fn bump(v: &mut Value) {
        let n = v.as_u64().unwrap();
        *v = Value::from((n + 1) % 101);
    }
    #[test]
    fn complete_certificate() {
        checked(&original()).unwrap();
    }
    #[test]
    fn polynomial_tampering() {
        for field in ["h49", "psi49", "quotient", "N", "second_D"] {
            let mut j = original();
            bump(&mut j[field][0]);
            assert!(checked(&j).is_err(), "{field}");
        }
    }
    #[test]
    fn geometric_tampering() {
        for path in [
            "/E7_points/1/x/0",
            "/alpha_points/7/y/0",
            "/kernel_divisors/1/v/0/0",
            "/frobenius_indices/1",
            "/kernel_sum_indices/1/1",
        ] {
            let mut j = original();
            bump(j.pointer_mut(path).unwrap());
            assert!(checked(&j).is_err(), "{path}");
        }
    }
    #[test]
    fn malformed_inputs() {
        let mut rows = vec![];
        let mut j = original();
        j["schema"] = Value::from("forged/v1");
        rows.push(j);
        let mut j = original();
        j["elliptic_models"][0][0] = Value::from(2);
        rows.push(j);
        let mut j = original();
        j["field_modulus"] = serde_json::json!([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]);
        rows.push(j);
        let mut j = original();
        j["E7_points"][1]["x"][0] = Value::from(101);
        rows.push(j);
        let mut j = original();
        j["E7_points"].as_array_mut().unwrap().pop();
        rows.push(j);
        let mut j = original();
        j["chart_a"][15] = Value::from(1);
        rows.push(j);
        for (i, j) in rows.iter().enumerate() {
            assert!(checked(j).is_err(), "malformed{i}");
        }
    }
}
