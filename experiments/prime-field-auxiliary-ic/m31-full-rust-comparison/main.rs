use prime_field_auxiliary_ic::{BatchScratch, Curve, Point};
use std::{env, fs, time::Instant};

const N: u64 = 2_147_505_293;
fn mul(a: u64, b: u64) -> u64 {
    ((a as u128 * b as u128) % N as u128) as u64
}
fn pow(mut a: u64, mut e: u64) -> u64 {
    let mut r = 1;
    while e > 0 {
        if e & 1 != 0 {
            r = mul(r, a);
        }
        a = mul(a, a);
        e >>= 1;
    }
    r
}
fn key(point: Option<Point>) -> u64 {
    point.map_or(u64::MAX, |p| (p.x() << 1) | (p.y() & 1))
}
fn next(state: &mut u64) -> u64 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    *state
}
fn build(
    curve: Curve<31>,
    signed: &[Option<Point>],
    reflected: bool,
) -> Result<FlatIndex, Box<dyn std::error::Error>> {
    let mut table = FlatIndex::new();
    let mut scratch = BatchScratch::default();
    let stride = if reflected { 2 } else { 1 };
    for i in (0..signed.len()).step_by(stride) {
        let mut sums = vec![signed[i]; signed.len() - i];
        curve.batch_add(&mut sums, &signed[i..], &mut scratch)?;
        for (off, &point) in sums.iter().enumerate() {
            if point.is_some() {
                table.entry(key(point), ((i as u32) << 16) | (i + off) as u32);
            }
        }
        if reflected {
            for j in i + 1..signed.len() {
                let point = sums[(j ^ 1) - i].map(|p| curve.negate(p)).transpose()?;
                if point.is_some() {
                    table.entry(key(point), (((i + 1) as u32) << 16) | j as u32);
                }
            }
        }
    }
    Ok(table)
}
struct FlatIndex {
    slots: Vec<(u32, u32)>,
    len: usize,
}
impl FlatIndex {
    fn new() -> Self {
        Self {
            slots: vec![(u32::MAX, 0); 1 << 20],
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
    fn entry(&mut self, key: u64, payload: u32) {
        let key = u32::try_from(key).expect("finite M31 key fits in u32");
        let i = self.slot(key);
        if self.slots[i].0 == u32::MAX {
            self.slots[i] = (key, payload);
            self.len += 1;
        }
    }
    fn get(&self, key: u64) -> Option<u32> {
        let key = u32::try_from(key).ok()?;
        let slot = self.slots[self.slot(key)];
        (slot.0 == key).then_some(slot.1)
    }
    fn len(&self) -> usize {
        self.len
    }
}

struct Pivot {
    row: Vec<u64>,
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = env::args().collect();
    if args.len() != 4 || !["flat", "reflected"].contains(&args[2].as_str()) {
        return Err("usage: full PUBLIC.txt flat|reflected SEED".into());
    }
    let started = Instant::now();
    let raw = fs::read_to_string(&args[1])?;
    let values: Vec<u64> = raw
        .split_whitespace()
        .map(str::parse)
        .collect::<Result<_, _>>()?;
    if values.len() != 9 + 2 * 500
        || values[0] != (1 << 31) - 1
        || values[1] != N
        || values[2..4] != [2, 14]
        || values[8] != 500
    {
        return Err("unexpected frozen fixture identity".into());
    }
    let curve = Curve::<31>::new(values[2], values[3])?;
    let generator = curve.point(values[4], values[5])?;
    let target = curve.point(values[6], values[7])?;
    let mut signed = Vec::with_capacity(1000);
    for xy in values[9..].chunks_exact(2) {
        let p = curve.point(xy[0], xy[1])?;
        signed.push(Some(p));
        signed.push(Some(curve.negate(p)?));
    }
    let setup = started.elapsed();
    let table = build(curve, &signed, args[2] == "reflected")?;
    let table_time = started.elapsed() - setup;
    let mut rng = 20261114 + args[3].parse::<u64>()?;
    let mut steps = Vec::new();
    for _ in 0..32 {
        let a = next(&mut rng) % N;
        let b = next(&mut rng) % N;
        let p = curve.add(curve.mul(Some(generator), a)?, curve.mul(Some(target), b)?)?;
        steps.push((a, b, p));
    }
    let mut a = next(&mut rng) % N;
    let mut b = next(&mut rng) % N;
    let mut point = curve.add(curve.mul(Some(generator), a)?, curve.mul(Some(target), b)?)?;
    let minus: Vec<_> = signed
        .iter()
        .map(|p| p.map(|q| curve.negate(q)).transpose())
        .collect::<Result<_, _>>()?;
    let mut pivots: Vec<Option<Pivot>> = (0..500).map(|_| None).collect();
    let mut scratch = BatchScratch::default();
    let mut relations = 0;
    let mut elimination_ns = 0;
    for trial in 1..=1_000_000 {
        let (da, db, dp) = steps[(next(&mut rng) % 32) as usize];
        a = (a + da) % N;
        b = (b + db) % N;
        point = curve.add(point, dp)?;
        let mut differences = vec![point; minus.len()];
        curve.batch_add(&mut differences, &minus, &mut scratch)?;
        let Some((k, payload)) = differences
            .iter()
            .enumerate()
            .find_map(|(k, &p)| table.get(key(p)).map(|v| (k, v)))
        else {
            continue;
        };
        let i = (payload >> 16) as usize;
        let j = (payload & 65535) as usize;
        if curve.add(curve.add(signed[i], signed[j])?, signed[k])? != point {
            return Err("relation check failed".into());
        }
        relations += 1;
        let elim_started = Instant::now();
        let mut row = vec![0u64; 502];
        for code in [i, j, k] {
            let col = code / 2;
            row[col] = (row[col] + if code & 1 == 0 { 1 } else { N - 1 }) % N;
        }
        row[500] = (N - a) % N;
        row[501] = (N - b) % N;
        let mut stored = false;
        for col in 0..500 {
            let v = row[col];
            if v == 0 {
                continue;
            }
            if let Some(pivot) = &pivots[col] {
                row[col] = 0;
                for c in col + 1..502 {
                    row[c] = (row[c] + N - mul(v, pivot.row[c])) % N;
                }
            } else {
                let inv = pow(v, N - 2);
                for x in &mut row[col..] {
                    *x = mul(*x, inv);
                }
                pivots[col] = Some(Pivot { row: row.clone() });
                stored = true;
                break;
            }
        }
        elimination_ns += elim_started.elapsed().as_nanos();
        if stored || row[501] == 0 {
            continue;
        }
        let scalar = mul(N - row[500], pow(row[501], N - 2));
        if curve.mul(Some(generator), scalar)? != Some(target) {
            return Err("answer check failed".into());
        }
        println!("{{\"mode\":\"{}\",\"seed\":{},\"scalar\":{},\"trials\":{},\"relations\":{},\"entries\":{},\"setup_ns\":{},\"table_ns\":{},\"elimination_ns\":{},\"total_ns\":{}}}", args[2], args[3], scalar, trial, relations, table.len(), setup.as_nanos(), table_time.as_nanos(), elimination_ns, started.elapsed().as_nanos());
        return Ok(());
    }
    Err("relation limit exhausted".into())
}
