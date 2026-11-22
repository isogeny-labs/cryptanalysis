//! Internal subgroup provenance for checked relation-target construction.
//!
//! A point enters this module through subgroup validation, the certified
//! generator, or checked operations on already admitted points. The types do
//! not deserialize, expose mutable points, or accept an unchecked raw point.

use crate::curve::{Curve, Point};
use crate::joint::JointTable;
use crate::{invalid, BigUint, Meter, Result};
use std::sync::Arc;

/// One opaque construction context for a certified curve and subgroup.
#[derive(Clone, Debug)]
pub(crate) struct SubgroupContext {
    curve: Arc<Curve>,
}

/// A point admitted to a specific opaque subgroup construction context.
#[derive(Clone, Debug)]
pub(crate) struct SubgroupPoint {
    curve: Arc<Curve>,
    point: Point,
}

/// Shared public-coefficient arithmetic preserving subgroup provenance.
pub(crate) struct SubgroupJointTable {
    curve: Arc<Curve>,
    table: JointTable,
}

// Compare the complete mathematical curve/subgroup identity. Primality proof
// caches do not change that identity: every Curve has already checked them.
// Exact values, rather than a hash, bind a prepared table's owned Curve clone.
fn same_domain(left: &Curve, right: &Curve) -> bool {
    left.modulus() == right.modulus()
        && left.a() == right.a()
        && left.b() == right.b()
        && left.order() == right.order()
        && left.cofactor() == right.cofactor()
        && left.generator() == right.generator()
}

impl SubgroupContext {
    /// Retain an already certified curve. No point is admitted by this call.
    pub(crate) fn new(curve: &Curve) -> Self {
        Self {
            curve: Arc::new(curve.clone()),
        }
    }

    /// Borrow the immutable certified curve retained by this context.
    pub(crate) fn curve(&self) -> &Curve {
        &self.curve
    }

    /// Admit the generator whose nonzero prime order Curve already certified.
    pub(crate) fn generator(&self) -> SubgroupPoint {
        self.wrap(self.curve.generator().clone())
    }

    /// Validate an untrusted point before it acquires provenance.
    pub(crate) fn validate(&self, point: &Point, meter: &mut Meter) -> Result<SubgroupPoint> {
        if !self.curve.in_subgroup(point, meter)? {
            return Err(invalid("provenance point outside the certified subgroup"));
        }
        Ok(self.wrap(point.clone()))
    }

    /// Add two admitted points using the original checked affine arithmetic.
    pub(crate) fn add(
        &self,
        left: &SubgroupPoint,
        right: &SubgroupPoint,
        meter: &mut Meter,
    ) -> Result<SubgroupPoint> {
        self.require_context(left)?;
        self.require_context(right)?;
        Ok(self.wrap(self.curve.add(&left.point, &right.point, meter)?))
    }

    /// Multiply an admitted point without scalar reduction or weaker limits.
    pub(crate) fn mul(
        &self,
        point: &SubgroupPoint,
        scalar: &BigUint,
        meter: &mut Meter,
    ) -> Result<SubgroupPoint> {
        self.require_context(point)?;
        Ok(self.wrap(self.curve.mul(&point.point, scalar, meter)?))
    }

    /// Prepare existing joint arithmetic using admitted points from this context.
    pub(crate) fn joint_table(
        &self,
        left: &SubgroupPoint,
        right: &SubgroupPoint,
        meter: &mut Meter,
    ) -> Result<SubgroupJointTable> {
        self.require_context(left)?;
        self.require_context(right)?;
        Ok(SubgroupJointTable {
            curve: Arc::clone(&self.curve),
            table: JointTable::from_subgroup_points(&self.curve, &left.point, &right.point, meter)?,
        })
    }

    fn require_context(&self, point: &SubgroupPoint) -> Result<()> {
        // Equal lifetimes or equal field moduli cannot make different opaque
        // contexts interchangeable. Clones intentionally share this identity.
        if !Arc::ptr_eq(&self.curve, &point.curve) {
            return Err(invalid("subgroup provenance context mismatch"));
        }
        Ok(())
    }

    // This is private to the module. Sibling modules cannot mint provenance
    // for a Point merely by claiming to have performed a validation earlier.
    fn wrap(&self, point: Point) -> SubgroupPoint {
        SubgroupPoint {
            curve: Arc::clone(&self.curve),
            point,
        }
    }
}

impl SubgroupPoint {
    /// Borrow the immutable admitted point for existing replay/oracle interfaces.
    pub(crate) fn point(&self) -> &Point {
        &self.point
    }

    /// Bind an owned prepared Curve clone to the full admitted domain.
    /// This check performs exact parameter equality, not a subgroup multiplication.
    pub(crate) fn for_curve(&self, curve: &Curve) -> Result<&Point> {
        if !same_domain(&self.curve, curve) {
            return Err(invalid(
                "prepared query subgroup provenance domain mismatch",
            ));
        }
        Ok(&self.point)
    }
}

impl SubgroupJointTable {
    /// Evaluate public coefficients using the unchanged checked shared chain.
    pub(crate) fn evaluate(
        &self,
        u: &BigUint,
        v: &BigUint,
        meter: &mut Meter,
    ) -> Result<SubgroupPoint> {
        Ok(SubgroupPoint {
            curve: Arc::clone(&self.curve),
            point: self.table.evaluate(u, v, meter)?,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{Error, Limits};

    fn curve(meter: &mut Meter) -> Curve {
        Curve::new(
            17u8.into(),
            2u8.into(),
            2u8.into(),
            19u8.into(),
            Point::Affine {
                x: 5u8.into(),
                y: 1u8.into(),
            },
            meter,
        )
        .unwrap()
    }

    #[test]
    fn context_identity_rejects_even_equal_curve_objects() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let left = SubgroupContext::new(&curve);
        let right = SubgroupContext::new(&curve);
        let g = left.generator();
        assert!(matches!(
            right.mul(&g, &1u8.into(), &mut meter),
            Err(Error::Invalid(_))
        ));
        assert!(matches!(
            right.add(&right.generator(), &g, &mut meter),
            Err(Error::Invalid(_))
        ));
        assert!(matches!(
            right.joint_table(&g, &g, &mut meter),
            Err(Error::Invalid(_))
        ));
        assert_eq!(
            left.clone()
                .mul(&g, &1u8.into(), &mut meter)
                .unwrap()
                .point(),
            g.point()
        );
    }

    #[test]
    fn full_domain_binding_includes_generator_and_curve_coefficients() {
        let mut meter = Meter::new(Limits::default());
        let original = curve(&mut meter);
        let context = SubgroupContext::new(&original);
        let g = context.generator();
        assert_eq!(context.curve().generator(), original.generator());
        assert_eq!(
            g.for_curve(&original.clone()).unwrap(),
            original.generator()
        );
        let other_generator = original
            .mul(original.generator(), &2u8.into(), &mut meter)
            .unwrap();
        let reoriented = Curve::new(
            original.modulus().clone(),
            original.a().clone(),
            original.b().clone(),
            original.order().clone(),
            other_generator,
            &mut meter,
        )
        .unwrap();
        assert!(matches!(g.for_curve(&reoriented), Err(Error::Invalid(_))));
        let isomorphic = Curve::new(
            17u8.into(),
            15u8.into(),
            9u8.into(),
            19u8.into(),
            Point::Affine {
                x: 3u8.into(),
                y: 8u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        assert!(matches!(g.for_curve(&isomorphic), Err(Error::Invalid(_))));
    }

    #[test]
    fn untrusted_outside_subgroup_and_noncanonical_points_cannot_enter() {
        let mut meter = Meter::new(Limits::default());
        let curve = Curve::with_cofactor(
            5u8.into(),
            0u8.into(),
            1u8.into(),
            3u8.into(),
            2u8.into(),
            Point::Affine {
                x: 0u8.into(),
                y: 1u8.into(),
            },
            &mut meter,
        )
        .unwrap();
        let context = SubgroupContext::new(&curve);
        for point in [
            Point::Affine {
                x: 4u8.into(),
                y: 0u8.into(),
            },
            Point::Affine {
                x: 5u8.into(),
                y: 1u8.into(),
            },
            Point::Affine {
                x: 1u8.into(),
                y: 1u8.into(),
            },
        ] {
            assert!(matches!(
                context.validate(&point, &mut meter),
                Err(Error::Invalid(_))
            ));
        }
        assert_eq!(
            context
                .validate(&Point::Infinity, &mut meter)
                .unwrap()
                .point(),
            &Point::Infinity
        );
    }

    #[test]
    fn checked_closure_and_joint_arithmetic_keep_exact_points_and_limits() {
        let mut meter = Meter::new(Limits::default());
        let curve = curve(&mut meter);
        let context = SubgroupContext::new(&curve);
        let g = context.generator();
        let q_raw = curve
            .mul(curve.generator(), &7u8.into(), &mut meter)
            .unwrap();
        let q = context.validate(&q_raw, &mut meter).unwrap();
        let table = context.joint_table(&g, &q, &mut meter).unwrap();
        for u in 0..20u8 {
            for v in 0..20u8 {
                let left = context.mul(&g, &u.into(), &mut meter).unwrap();
                let right = context.mul(&q, &v.into(), &mut meter).unwrap();
                let separate = context.add(&left, &right, &mut meter).unwrap();
                let joint = table.evaluate(&u.into(), &v.into(), &mut meter).unwrap();
                assert_eq!(joint.point(), separate.point());
                assert!(curve.in_subgroup(joint.point(), &mut meter).unwrap());
            }
        }
        let opposite = context.mul(&g, &18u8.into(), &mut meter).unwrap();
        assert_eq!(
            context.add(&g, &opposite, &mut meter).unwrap().point(),
            &Point::Infinity
        );
        let mut limited = Meter::new(Limits {
            steps: 0,
            ..Limits::default()
        });
        assert!(matches!(
            context.mul(&g, &2u8.into(), &mut limited),
            Err(Error::Limit(_))
        ));
        assert!(matches!(
            table.evaluate(&2u8.into(), &1u8.into(), &mut limited),
            Err(Error::Limit(_))
        ));
    }
}
