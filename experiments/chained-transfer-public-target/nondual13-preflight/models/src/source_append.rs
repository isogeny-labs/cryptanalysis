// Constructor appended inside the unchanged original SourceE module.
impl SourceE {
    pub fn second_actual(
        c: &CheckedInstance,
        hop: &chained_n4_nondual13_preflight::SecondHop,
    ) -> Self {
        c.check_field_basis().unwrap();
        let first = OddSourceIsogeny::construct(c);
        assert_eq!(hop.source(), first.target());
        assert_eq!(hop.certificate["field_modulus"], json!([220, 0, 0, 1]));
        assert_eq!(hop.certificate["field_tag"], c.field_tag);
        let generator = hop
            .forward(first.forward(Self::original_generator(c)).unwrap())
            .unwrap();
        let out = Self {
            independent_field: c.independent_field.clone(),
            independent_curve: *hop.target(),
            field_tag: c.field_tag.clone(),
            source_tag: hop.certificate["E2_id"].as_str().unwrap().to_owned(),
            ell: c.inst.ell,
            order: c.inst.order,
            generator,
            reference_quartic: None,
        };
        out.check();
        out
    }
}
