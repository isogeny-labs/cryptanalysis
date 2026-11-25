use prime_field_auxiliary_ic::{BatchScratch, Curve, Point};
use std::{env, fs, time::Instant};

struct FlatIndex {
    slots: Vec<(u32, u32)>,
    len: usize,
}
impl FlatIndex {
    fn new(bound: usize) -> Self {
        Self {
            slots: vec![(u32::MAX, 0); (2 * bound).next_power_of_two()],
            len: 0,
        }
    }
    fn slot(&self, key: u32) -> usize {
        let mut h = u64::from(key).wrapping_add(0x9e3779b97f4a7c15);
        h = (h ^ (h >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        h = (h ^ (h >> 27)).wrapping_mul(0x94d049bb133111eb);
        h ^= h >> 31;
        let mask = self.slots.len() - 1;
        let mut i = h as usize & mask;
        while self.slots[i].0 != u32::MAX && self.slots[i].0 != key {
            i = (i + 1) & mask;
        }
        i
    }
    fn insert(&mut self, key: u32, value: u32) {
        let i = self.slot(key);
        if self.slots[i].0 == u32::MAX {
            self.slots[i] = (key, value);
            self.len += 1;
        }
    }
    fn visit(&mut self, i: usize, j: usize, point: Option<Point>) {
        if let Some(p) = point {
            if p.y() & 1 == 0 {
                self.insert(p.x() as u32, ((i as u32) << 16) | j as u32);
            }
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = env::args().collect();
    if args.len() != 4 || !["flat", "reflected"].contains(&args[2].as_str()) {
        return Err("expected POINTS flat|reflected REFERENCE".into());
    }
    let curve = Curve::<31>::new(2, 14)?;
    let input = fs::read_to_string(&args[1])?;
    let values: Vec<u64> = input
        .split_whitespace()
        .map(str::parse)
        .collect::<Result<_, _>>()?;
    if values.len() != 1000 {
        return Err("expected 500 point representatives".into());
    }
    let start = Instant::now();
    let mut signed = Vec::with_capacity(1000);
    for xy in values.chunks_exact(2) {
        let p = curve.point(xy[0], xy[1])?;
        signed.push(Some(p));
        signed.push(Some(curve.negate(p)?));
    }
    let mut table = FlatIndex::new(250000);
    let mut scratch = BatchScratch::default();
    let reflected = args[2] == "reflected";
    let stride = if reflected { 2 } else { 1 };
    for i in (0..signed.len()).step_by(stride) {
        let steps = &signed[i..];
        let mut sums = vec![signed[i]; steps.len()];
        curve.batch_add(&mut sums, steps, &mut scratch)?;
        for (off, &sum) in sums.iter().enumerate() {
            table.visit(i, i + off, sum);
        }
        if reflected {
            for j in i + 1..signed.len() {
                let sum = sums[(j ^ 1) - i].map(|p| curve.negate(p)).transpose()?;
                table.visit(i + 1, j, sum);
            }
        }
    }
    let elapsed = start.elapsed().as_nanos();
    let reference = fs::read(&args[3])?;
    if reference.len() % 8 != 0 || reference.len() / 8 != table.len {
        return Err("reference cardinality mismatch".into());
    }
    for record in reference.chunks_exact(8) {
        let key = u32::from_le_bytes(record[..4].try_into()?);
        let value = u32::from_le_bytes(record[4..].try_into()?);
        if table.slots[table.slot(key)] != (key, value) {
            return Err("reference key or payload mismatch".into());
        }
    }
    println!("{elapsed}");
    Ok(())
}
