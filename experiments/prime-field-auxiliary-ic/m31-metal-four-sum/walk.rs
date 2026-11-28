// Exact first 64-lane walk round copied from solve.rs for admission inputs.
use prime_field_auxiliary_ic::Curve;
struct SplitMix64(u64);
impl SplitMix64 {
    fn next(&mut self) -> u64 {
        self.0=self.0.wrapping_add(0x9e3779b97f4a7c15);
        let mut z=self.0;
        z=(z^(z>>30)).wrapping_mul(0xbf58476d1ce4e5b9);
        z=(z^(z>>27)).wrapping_mul(0x94d049bb133111eb);
        z^(z>>31)
    }
    fn below(&mut self, modulus:u64)->u64 {
        let threshold=modulus.wrapping_neg()%modulus;
        loop { let value=self.next(); if value>=threshold { return value%modulus } }
    }
}
fn main() {
    let c=Curve::<31>::new(2,14).unwrap();
    let g=c.point(1,814455902).unwrap();
    let q=c.point(1767503692,244402461).unwrap();
    let n=2_147_505_293;
    let mut rng=SplitMix64(2_911_332_506_172_719_186);
    let mut jumps=[None;32];
    for j in &mut jumps {
        let a=rng.below(n); let b=rng.below(n);
        *j=c.add(c.mul(Some(g),a).unwrap(),c.mul(Some(q),b).unwrap()).unwrap();
    }
    let mut points=Vec::new();
    for _ in 0..64 {
        let a=rng.below(n); let b=rng.below(n);
        points.push(c.add(c.mul(Some(g),a).unwrap(),c.mul(Some(q),b).unwrap()).unwrap());
    }
    for p in &mut points {
        let jump=(rng.next()&31) as usize;
        *p=c.add(*p,jumps[jump]).unwrap();
        let point=p.unwrap();
        println!("{},{}",point.x(),point.y());
    }
}
