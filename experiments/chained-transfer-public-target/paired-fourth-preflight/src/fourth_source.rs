impl SourceE {
    pub fn paired_source(
        c: &CheckedInstance,
        ec: Curve<ER>,
        ell: u64,
        order: u128,
        generator: Pt<ER>,
        tag: &str,
    ) -> Self {
        c.check_field_basis().unwrap();
        crate::certify_group(&c.independent_field, &ec, ell, order, generator).unwrap();
        let out = Self {
            independent_field: c.independent_field.clone(),
            independent_curve: ec,
            field_tag: c.field_tag.clone(),
            source_tag: tag.to_owned(),
            ell,
            order,
            generator,
            reference_quartic: None,
        };
        // Both explicitly fixed instances have cofactor4; retain the original check.
        out.check();
        out
    }
}
