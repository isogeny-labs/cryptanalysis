use prime_field_auxiliary_ic::Curve;
use std::collections::HashSet;

fn main() {
    let c = Curve::<31>::new(2, 14).unwrap();
    let g = c.point(1, 814455902).unwrap();
    let q = c.point(1767503692, 244402461).unwrap();
    let columns: usize = std::env::args().nth(1).unwrap_or("195".into()).parse().unwrap();
    let lanes: usize = std::env::args().nth(2).unwrap_or("1".into()).parse().unwrap();
    let base: Vec<_> = (0..c.modulus()).filter_map(|x| c.lift_x(x).unwrap()).take(columns).collect();
    let mut entries = Vec::new();
    let mut seen = HashSet::new();
    for i in 0..columns {
        for j in i..columns {
            for negative in [false, true] {
                if i == j && negative { continue; }
                let b = if negative { c.negate(base[j]).unwrap() } else { base[j] };
                let sum = c.add(Some(base[i]), Some(b)).unwrap();
                let canon = sum.map(|p| if p.y() > c.modulus()/2 { c.negate(p).unwrap() } else { p });
                let key = canon.map(|p| p.x()).unwrap_or(c.modulus());
                if seen.insert(key) { entries.push(canon); }
            }
        }
    }
    let mut candidates = Vec::new();
    let mut target = q;
    for _ in 0..lanes {
        for point in &entries {
            for negative in [false, true] {
                if point.is_none() && negative { continue; }
                let b = if negative { point.map(|p| c.negate(p).unwrap()) } else { *point };
                candidates.push(c.add(Some(target), b).unwrap());
            }
        }
        target = c.add(Some(target),Some(g)).unwrap().unwrap();
    }
    candidates[0] = c.add(Some(q), Some(c.negate(q).unwrap())).unwrap();
    candidates[1] = c.add(Some(g), Some(g)).unwrap();
    candidates[2] = c.add(None, Some(q)).unwrap();
    candidates[3] = c.add(Some(q), None).unwrap();
    let checksum = candidates.iter().fold(0u64, |a,p| a ^ p.map_or(0, |p| p.x()));
    let digest = candidates.iter().fold(14_695_981_039_346_656_037u64, |mut h,point| {
        for word in [point.map_or(c.modulus(), |p| p.x()), point.map_or(c.modulus(), |p| p.y())] {
            h = (h ^ word).wrapping_mul(1_099_511_628_211);
        }
        h
    });
    println!("{{\"columns\":{columns},\"lanes\":{lanes},\"entries\":{},\"n\":{},\"checksum\":{checksum},\"digest\":{digest}}}",entries.len(),candidates.len());
}
