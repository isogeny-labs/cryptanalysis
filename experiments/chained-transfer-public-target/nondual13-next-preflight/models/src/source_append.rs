impl SourceE {
    pub fn third_actual(
        c: &CheckedInstance,
        hop: &chained_n4_nondual13_next_preflight::ThirdHop,
    ) -> Self {
        c.check_field_basis().unwrap();
        assert_eq!(hop.certificate["field_modulus"], json!([220, 0, 0, 1]));
        assert_eq!(hop.certificate["field_tag"], c.field_tag);
        let generator = hop
            .forward(hop.original_to_source(Self::original_generator(c)).unwrap())
            .unwrap();
        let out = Self {
            independent_field: c.independent_field.clone(),
            independent_curve: *hop.target(),
            field_tag: c.field_tag.clone(),
            source_tag: hop.certificate["E3_id"].as_str().unwrap().to_owned(),
            ell: c.inst.ell,
            order: c.inst.order,
            generator,
            reference_quartic: None,
        };
        out.check();
        out
    }
}
