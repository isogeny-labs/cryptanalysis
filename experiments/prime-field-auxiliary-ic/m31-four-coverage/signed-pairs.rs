// Arithmetic specialization for the 71-representative timing fixture.
pub(super) fn signed_batch(
    curve: Curve<31>,
    left: Option<Point>,
    reps: &[Point; 71],
    out: &mut [Option<Point>],
) {
    type Field = F<31>;
    assert_eq!(out.len(), 2 * reps.len());
    let Some(p) = left else {
        for (pair, &q) in out.chunks_exact_mut(2).zip(reps) {
            pair.copy_from_slice(&[Some(q), Some(curve.neg_inner(q))]);
        }
        return;
    };
    #[cfg(all(target_arch = "aarch64", target_feature = "neon", neon_products))]
    let inverses = {
        let mut den = [0u32; 72];
        for (slot, q) in den.iter_mut().zip(reps) {
            *slot = Field::sub(q.x, p.x) as u32;
        }
        #[cfg(neon_eight)]
        const V: usize = 2;
        #[cfg(not(neon_eight))]
        const V: usize = 1;
        neon_products_kernel::reciprocals::<V>(&den)
    };
    #[cfg(not(all(target_arch = "aarch64", target_feature = "neon", neon_products)))]
    let (mut products, prefix) = {
        let mut prefix = [0; 71];
        let mut products = [1; 4];
        for (i, q) in reps.iter().enumerate() {
            let d = Field::sub(q.x, p.x);
            prefix[i] = products[i % 4];
            if d != 0 {
                products[i % 4] = Field::mul(products[i % 4], d);
            }
        }
        let mut prior = [1; 4];
        let mut total = 1;
        for i in 0..4 {
            prior[i] = total;
            total = Field::mul(total, products[i]);
        }
        let mut carry = Field::inv(total);
        for i in (0..4).rev() {
            let prod = products[i];
            products[i] = Field::mul(carry, prior[i]);
            carry = Field::mul(carry, prod);
        }
        (products, prefix)
    };
    #[cfg(all(
        target_arch = "aarch64",
        target_feature = "neon",
        neon_products,
        neon_finish
    ))]
    neon_products_kernel::finish(curve, p, reps, &inverses, out);
    #[cfg(not(all(
        target_arch = "aarch64",
        target_feature = "neon",
        neon_products,
        neon_finish
    )))]
    for (i, (pair, &q)) in out.chunks_exact_mut(2).zip(reps).enumerate().rev() {
        let neg = curve.neg_inner(q);
        let d = Field::sub(q.x, p.x);
        if d == 0 {
            pair[0] = curve.add_inner(left, Some(q));
            pair[1] = curve.add_inner(left, Some(neg));
        } else {
            #[cfg(all(target_arch = "aarch64", target_feature = "neon", neon_products))]
            let reciprocal = u64::from(inverses[i]);
            #[cfg(not(all(target_arch = "aarch64", target_feature = "neon", neon_products)))]
            let reciprocal = {
                let r = Field::mul(products[i % 4], prefix[i]);
                products[i % 4] = Field::mul(products[i % 4], d);
                r
            };
            for (slot, r) in pair.iter_mut().zip([q, neg]) {
                let slope = Field::mul(Field::sub(r.y, p.y), reciprocal);
                *slot = Some(curve.finish_add(p, r, slope));
            }
        }
    }
}

include!("neon-products.rs");
