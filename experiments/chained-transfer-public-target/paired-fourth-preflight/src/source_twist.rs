impl SourceE {
    pub fn fixed_twisted(
        c: &CheckedInstance,
        ec: Curve<ER>,
        ell: u64,
        order: u128,
        generator: Pt<ER>,
        tag: &str,
    ) -> Self {
        c.check_field_basis().unwrap();
        // The old check() remains literal and still enforces cofactor4.
        // The separate new certificate keeps smoothness, primality, actual
        // nonzero prime-order point and unique Hasse multiple at any cofactor.
        crate::certify_group(&c.independent_field, &ec, ell, order, generator).unwrap();
        Self {
            independent_field: c.independent_field.clone(),
            independent_curve: ec,
            field_tag: c.field_tag.clone(),
            source_tag: tag.to_owned(),
            ell,
            order,
            generator,
            reference_quartic: None,
        }
    }
}
