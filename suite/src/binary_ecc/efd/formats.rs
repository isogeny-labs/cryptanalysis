use super::*;

/// Quotient-only formats deliberately return only x or x+y; they do not
/// reconstruct an affine point or provide ordinary arbitrary point addition.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Projection {
    Full { x: F2mElement, y: F2mElement },
    X(F2mElement),
    W(F2mElement),
}

impl Representation {
    /// Encode a finite affine point with nonzero projective scale. The caller
    /// supplies a point on this representation's curve model. Model changes
    /// are not implicit. Lambda's x=0 point is outside this affine chart.
    pub fn encode_affine(
        &self,
        field: &IrreduciblePoly,
        x: &F2mElement,
        y: &F2mElement,
        z: &F2mElement,
    ) -> Result<Bindings> {
        let mut v = Bindings::from([
            ("x".into(), x.clone()),
            ("y".into(), y.clone()),
            ("z".into(), z.clone()),
        ]);
        check_field(field, &v)?;
        if z.is_zero() {
            return Err(EfdError::OutsideChart);
        }
        v.clear();
        let mut put = |name: &str, value: F2mElement| {
            v.insert(name.into(), value);
        };
        let z2 = z.square(field);
        match self.id.as_str() {
            "shortw/affine" | "edwards/xy" | "edwards/xy-1" => {
                put("X", x.clone());
                put("Y", y.clone());
            }
            "edwards/w" | "edwards/w-1" => put("w", x.add(y)),
            "edwards/wz" | "edwards/wz-1" => {
                put("W", x.add(y).mul(z, field));
                put("Z", z.clone());
            }
            "shortw/xz" => {
                put("X", x.mul(z, field));
                put("Z", z.clone());
            }
            "shortw/jacobian" => {
                put("X", x.mul(&z2, field));
                put("Y", y.mul(&z2.mul(z, field), field));
                put("Z", z.clone());
            }
            "shortw/lambda" => {
                let xi = x.flt_inverse(field).ok_or(EfdError::OutsideChart)?;
                put("X", x.mul(z, field));
                put("L", x.add(&y.mul(&xi, field)).mul(z, field));
                put("Z", z.clone());
            }
            "shortw/lopezdahab"
            | "shortw/lopezdahab-0"
            | "shortw/lopezdahab-1"
            | "shortw/extended-0"
            | "shortw/extended-1" => {
                let xz = x.mul(z, field);
                put("X", xz.clone());
                put("Y", y.mul(&z2, field));
                put("Z", z.clone());
                if self.variables.iter().any(|s| s == "ZZ") {
                    put("ZZ", z2);
                }
                if self.variables.iter().any(|s| s == "XZ") {
                    put("XZ", xz.mul(z, field));
                }
            }
            "shortw/projective" | "hessian/standard" | "edwards/xyz" | "edwards/xyz-1" => {
                put("X", x.mul(z, field));
                put("Y", y.mul(z, field));
                put("Z", z.clone());
            }
            _ => return Err(EfdError::Unsupported(self.id.clone())),
        }
        Ok(v)
    }

    /// Add an EFD point suffix (1,2,3) to encoded coordinates.
    pub fn bind_point(&self, values: &Bindings, index: u32) -> Bindings {
        values
            .iter()
            .map(|(k, v)| (format!("{k}{index}"), v.clone()))
            .collect()
    }

    /// Normalize an EFD output (3 for ADD/DBL/SCALE, 5 for DADD, and
    /// 4/5 for the doubled/summed points of a ladder step).
    pub fn project(
        &self,
        field: &IrreduciblePoly,
        values: &Bindings,
        index: u32,
    ) -> Result<Projection> {
        check_field(field, values)?;
        let get = |s: &str| {
            values
                .get(&format!("{s}{index}"))
                .cloned()
                .ok_or_else(|| EfdError::MissingInput(format!("{s}{index}")))
        };
        if self.variables == ["w"] {
            return Ok(Projection::W(get("w")?));
        }
        let zi = if self.variables.iter().any(|v| v == "Z") {
            get("Z")?.flt_inverse(field).ok_or(EfdError::OutsideChart)?
        } else {
            F2mElement::one(field.degree)
        };
        if self.variables.iter().any(|v| v == "W") {
            return Ok(Projection::W(get("W")?.mul(&zi, field)));
        }
        if self.id == "shortw/xz" {
            return Ok(Projection::X(get("X")?.mul(&zi, field)));
        }
        let (x, y) = if self.id == "shortw/jacobian" {
            let z2 = zi.square(field);
            (
                get("X")?.mul(&z2, field),
                get("Y")?.mul(&z2.mul(&zi, field), field),
            )
        } else if self.id == "shortw/lambda" {
            let x = get("X")?.mul(&zi, field);
            let l = get("L")?.mul(&zi, field);
            let y = x.mul(&l.add(&x), field);
            (x, y)
        } else if self.id.starts_with("shortw/lopezdahab") || self.id.starts_with("shortw/extended")
        {
            (
                get("X")?.mul(&zi, field),
                get("Y")?.mul(&zi.square(field), field),
            )
        } else {
            (get("X")?.mul(&zi, field), get("Y")?.mul(&zi, field))
        };
        Ok(Projection::Full { x, y })
    }
}
