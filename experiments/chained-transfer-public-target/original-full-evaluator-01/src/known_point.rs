/// Actual cubic-field presentation; no norm recovery, halving or scalar witness.
impl Runtime {
    pub fn encode_known_point(
        &self,
        side: usize,
        point: Point,
    ) -> chained_n4_original_full_geometry::adapter::EncodedPoint {
        self.geometry.models[side].prime.a.encode(point)
    }
    fn known_gamma(&self, from: usize, to: usize, point: Pt<ER>) -> Pt<ER> {
        self.bump(|c| {
            if degree(from, to) == 13 {
                c.degree13_elliptic_evaluation += 1;
            } else {
                c.degree169_elliptic_evaluation += 1;
            }
        });
        self.known_maps.eval(&self.geometry, from, to, point)
    }
    pub fn evaluate_known_point(
        &self,
        from: usize,
        to: usize,
        input: &chained_n4_original_full_geometry::adapter::EncodedPoint,
        factored: bool,
    ) -> Result<EncodedClass> {
        if from >= 3 || to >= 3 || from == to {
            return Err("unknown known-point map direction".into());
        }
        self.bump(|c| c.external_point_parse += 1);
        let source = &self.geometry.models[from].source;
        let point = ep(self.geometry.models[from].prime.a.decode(input)?);
        self.bump(|c| c.external_point_full_order += 1);
        if curve::pmul(source.field(), source.curve(), &point, ORDER) != Pt::Inf {
            return Err("known point outside declared full source order".into());
        }
        let image = if factored && from.abs_diff(to) == 2 {
            let middle = self.known_gamma(from, 1, point);
            self.known_gamma(1, to, middle)
        } else {
            self.known_gamma(from, to, point)
        };
        let target = &self.geometry.models[to];
        self.bump(|c| c.target_prime_phi += 1);
        let class = target.prime.a.transfer_point(&kp(image))?;
        self.bump(|c| c.transported_norm_doubling += 1);
        let norm = curve::pmul(target.source.field(), target.source.curve(), &image, 2);
        let entry = Entry {
            domain: to,
            class,
            norm,
        };
        self.check_final(&entry)?;
        Ok(self.encode(to, &entry.class))
    }
}
