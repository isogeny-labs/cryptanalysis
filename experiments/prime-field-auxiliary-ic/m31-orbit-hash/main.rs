use prime_field_auxiliary_ic::{BatchScratch, Curve, Point};
use std::{env, fs, time::Instant};

const N: u64 = 2_147_505_293;
const PACKED_SIGN: bool = option_env!("M31_PACKED_SIGN").is_some();
const ORBIT_INDEX: bool = option_env!("M31_ORBIT_INDEX").is_some();
const NATIVE_SCAN: bool = option_env!("M31_NATIVE_SCAN").is_some();
const AUDIT_NATIVE: bool = option_env!("M31_AUDIT_NATIVE").is_some();
#[link(name = "m31scan", kind = "static")]
unsafe extern "C" {
    fn m31_scan_pairs(left_x: u32, left_y: u32, base_x: *const u32, base_y: *const u32,
        bitmap: *const u64, out_index: *mut u32, out_key: *mut u32, pairs: usize) -> usize;
}
const BLOOM_BITS: usize = if option_env!("M31_BLOOM_18").is_some() {
    18
} else if option_env!("M31_BLOOM_19").is_some() {
    19
} else if option_env!("M31_BLOOM_21").is_some() {
    21
} else if option_env!("M31_BLOOM_22").is_some() {
    22
} else {
    20
};
fn bloom_bit(x: u64) -> usize {
    if option_env!("M31_BLOOM_HASH_HIGH").is_some() {
        (x as usize) >> (31 - BLOOM_BITS)
    } else if option_env!("M31_BLOOM_HASH_LOW").is_some() {
        (x as usize) & ((1 << BLOOM_BITS) - 1)
    } else {
        (x.wrapping_mul(0x9e3779b97f4a7c15) >> (64 - BLOOM_BITS)) as usize
    }
}
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
    let stride = if reflected || ORBIT_INDEX { 2 } else { 1 };
    for i in (0..signed.len()).step_by(stride) {
        let mut sums = vec![signed[i]; signed.len() - i];
        curve.batch_add(&mut sums, &signed[i..], &mut scratch)?;
        for (off, &point) in sums.iter().enumerate() {
            if point.is_some() {
                if ORBIT_INDEX && point.unwrap().y() == 0 {
                    return Err("unexpected finite two-torsion in prime-order basis".into());
                }
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
    sign_slots: Vec<(u32, u32, u32)>,
    x_bitmap: Vec<u64>,
    len: usize,
}
impl FlatIndex {
    fn new() -> Self {
        Self {
            slots: if ORBIT_INDEX {
                vec![(u32::MAX, 0); 1 << 19]
            } else if PACKED_SIGN {
                Vec::new()
            } else {
                vec![(u32::MAX, 0); 1 << 20]
            },
            sign_slots: if PACKED_SIGN && !ORBIT_INDEX {
                vec![(u32::MAX, u32::MAX, u32::MAX); 1 << 19]
            } else {
                Vec::new()
            },
            x_bitmap: if option_env!("M31_X_BLOOM").is_some() {
                vec![0; 1 << (BLOOM_BITS - 6)]
            } else {
                Vec::new()
            },
            len: 0,
        }
    }
    fn slot(&self, key: u32) -> usize {
        let mask = if PACKED_SIGN && !ORBIT_INDEX {
            self.sign_slots.len() - 1
        } else {
            self.slots.len() - 1
        };
        let mut i = if option_env!("M31_FAST_HASH").is_some() {
            (u64::from(key).wrapping_mul(0x9e3779b97f4a7c15) >> if PACKED_SIGN || ORBIT_INDEX { 45 } else { 44 })
                as usize
        } else {
            let mut h = u64::from(key).wrapping_add(0x9e3779b97f4a7c15);
            h = (h ^ (h >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
            h = (h ^ (h >> 27)).wrapping_mul(0x94d049bb133111eb);
            h ^= h >> 31;
            h as usize & mask
        };
        while if PACKED_SIGN && !ORBIT_INDEX {
            self.sign_slots[i].0 != u32::MAX && self.sign_slots[i].0 != key
        } else {
            self.slots[i].0 != u32::MAX && self.slots[i].0 != key
        } {
            i = (i + 1) & mask;
        }
        i
    }
    fn entry(&mut self, key: u64, payload: u32) {
        let key = u32::try_from(key).expect("finite M31 key fits in u32");
        if ORBIT_INDEX {
            let x = key >> 1;
            let i = self.slot(x);
            if self.slots[i].0 == u32::MAX {
                self.slots[i] = (x, payload | ((key & 1) << 31));
                self.len += 2;
                let bit = bloom_bit(u64::from(x));
                self.x_bitmap[bit >> 6] |= 1u64 << (bit & 63);
            }
        } else if PACKED_SIGN {
            let x = key >> 1;
            let i = self.slot(x);
            let slot = &mut self.sign_slots[i];
            let new_x = slot.0 == u32::MAX;
            if new_x {
                slot.0 = x;
            }
            let value = if key & 1 == 0 {
                &mut slot.1
            } else {
                &mut slot.2
            };
            if *value == u32::MAX {
                *value = payload;
                self.len += 1;
            }
            if new_x && !self.x_bitmap.is_empty() {
                let bit = bloom_bit(u64::from(x));
                self.x_bitmap[bit >> 6] |= 1u64 << (bit & 63);
            }
        } else {
            let i = self.slot(key);
            if self.slots[i].0 == u32::MAX {
                self.slots[i] = (key, payload);
                self.len += 1;
            }
        }
    }
    fn get(&self, key: u64) -> Option<u32> {
        let key = u32::try_from(key).ok()?;
        if ORBIT_INDEX {
            let x = key >> 1;
            let slot = self.slots[self.slot(x)];
            if slot.0 != x { return None; }
            let payload = slot.1 & 0x7fff_ffff;
            if (slot.1 >> 31) == (key & 1) {
                Some(payload)
            } else {
                Some((((payload >> 16) ^ 1) << 16) | ((payload & 65535) ^ 1))
            }
        } else if PACKED_SIGN {
            let x = key >> 1;
            let slot = self.sign_slots[self.slot(x)];
            let payload = if key & 1 == 0 { slot.1 } else { slot.2 };
            (slot.0 == x && payload != u32::MAX).then_some(payload)
        } else {
            let slot = self.slots[self.slot(key)];
            (slot.0 == key).then_some(slot.1)
        }
    }
    fn len(&self) -> usize {
        self.len
    }
    fn contains_x(&self, x: u64) -> bool {
        let Ok(x) = u32::try_from(x) else {
            return false;
        };
        if ORBIT_INDEX { self.slots[self.slot(x)].0 == x }
        else { PACKED_SIGN && self.sign_slots[self.slot(x)].0 == x }
    }
    fn may_contain_x_bitmap(&self, x: u64) -> bool {
        let bit = bloom_bit(x);
        self.x_bitmap[bit >> 6] & (1u64 << (bit & 63)) != 0
    }
    fn dump_sorted(&self, path: &str) -> std::io::Result<()> {
        if ORBIT_INDEX {
            for &(x, _) in &self.slots {
                if x != u32::MAX { assert!(self.may_contain_x_bitmap(u64::from(x))); }
            }
        } else if !self.x_bitmap.is_empty() {
            for &(x, _, _) in &self.sign_slots {
                if x != u32::MAX {
                    assert!(self.may_contain_x_bitmap(u64::from(x)));
                }
            }
        }
        let mut pairs = Vec::with_capacity(self.len);
        if ORBIT_INDEX {
            for &(x, stored) in &self.slots {
                if x != u32::MAX {
                    let sign = stored >> 31;
                    let payload = stored & 0x7fff_ffff;
                    pairs.push(((x << 1) | sign, payload));
                    pairs.push(((x << 1) | (sign ^ 1),
                        ((((payload >> 16) ^ 1) << 16) | ((payload & 65535) ^ 1))));
                }
            }
        } else if PACKED_SIGN {
            for &(x, even, odd) in &self.sign_slots {
                if x != u32::MAX {
                    if even != u32::MAX {
                        pairs.push((x << 1, even));
                    }
                    if odd != u32::MAX {
                        pairs.push(((x << 1) | 1, odd));
                    }
                }
            }
        } else {
            pairs.extend(
                self.slots
                    .iter()
                    .copied()
                    .filter(|&(key, _)| key != u32::MAX),
            );
        }
        assert_eq!(pairs.len(), self.len);
        pairs.sort_unstable_by_key(|&(key, _)| key);
        let mut bytes = Vec::with_capacity(pairs.len() * 8);
        for (key, payload) in pairs {
            bytes.extend_from_slice(&key.to_le_bytes());
            bytes.extend_from_slice(&payload.to_le_bytes());
        }
        fs::write(path, bytes)
    }
}

struct Pivot {
    row: Vec<u64>,
}
fn rust_find(curve: Curve<31>, point: Option<Point>, minus: &[Option<Point>],
    table: &FlatIndex, scratch: &mut BatchScratch) -> Result<Option<(usize, u32)>, Box<dyn std::error::Error>> {
    let mut differences = vec![point; minus.len()];
    if option_env!("M31_X_BLOOM").is_some() {
        curve.batch_add_paired_x_filtered_assume_valid(point, minus, &mut differences, scratch,
            |x| table.may_contain_x_bitmap(x))?;
    } else if option_env!("M31_X_FILTER").is_some() {
        curve.batch_add_paired_x_filtered_assume_valid(point, minus, &mut differences, scratch,
            |x| table.contains_x(x))?;
    } else if option_env!("M31_PAIR_BATCH").is_some() {
        curve.batch_add_paired_x_assume_valid(point, minus, &mut differences, scratch)?;
    } else if option_env!("M31_TRUSTED_BATCH").is_some() {
        curve.batch_add_assume_valid(&mut differences, minus, scratch)?;
    } else {
        curve.batch_add(&mut differences, minus, scratch)?;
    }
    Ok(differences.iter().enumerate().find_map(|(k, &p)| table.get(key(p)).map(|v| (k, v))))
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
    if ORBIT_INDEX && option_env!("M31_AUDIT_ORBIT").is_some() {
        let mut checked = 0usize;
        for &(x, stored) in &table.slots {
            if x == u32::MAX { continue; }
            let sign = stored >> 31;
            let payload = stored & 0x7fff_ffff;
            let i = (payload >> 16) as usize;
            let j = (payload & 65535) as usize;
            if i >= signed.len() || j >= signed.len() {
                return Err("orbit payload out of range".into());
            }
            let direct = curve.add(signed[i], signed[j])?;
            let reflected = curve.add(signed[i ^ 1], signed[j ^ 1])?;
            if key(direct) != (((x as u64) << 1) | sign as u64) ||
                key(reflected) != (((x as u64) << 1) | (sign ^ 1) as u64) {
                return Err("orbit payload failed exact group-law audit".into());
            }
            checked += 1;
        }
        if checked * 2 != table.len() { return Err("orbit audit entry count mismatch".into()); }
    }
    if let Ok(path) = env::var("M31_DUMP_INDEX") {
        table.dump_sorted(&path)?;
    }
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
    let base_x: Vec<u32> = if NATIVE_SCAN { minus.iter().map(|p| p.unwrap().x() as u32).collect() } else { Vec::new() };
    let base_y: Vec<u32> = if NATIVE_SCAN { minus.iter().map(|p| p.unwrap().y() as u32).collect() } else { Vec::new() };
    let mut out_index = if NATIVE_SCAN { vec![0u32; minus.len()] } else { Vec::new() };
    let mut out_key = if NATIVE_SCAN { vec![0u32; minus.len()] } else { Vec::new() };
    let mut native_calls = 0u64;
    let mut native_fallbacks = 0u64;
    let mut native_candidates = 0u64;
    let mut pivots: Vec<Option<Pivot>> = (0..500).map(|_| None).collect();
    let mut scratch = BatchScratch::default();
    let mut relations = 0;
    let mut elimination_ns = 0;
    let trace_path = env::var("M31_TRACE_HITS").ok();
    let mut trace = Vec::<u8>::new();
    for trial in 1..=1_000_000 {
        let (da, db, dp) = steps[(next(&mut rng) % 32) as usize];
        a = (a + da) % N;
        b = (b + db) % N;
        point = curve.add(point, dp)?;
        let hit = if NATIVE_SCAN {
            if let Some(p) = point {
                native_calls += 1;
                let count = unsafe { m31_scan_pairs(p.x() as u32, p.y() as u32, base_x.as_ptr(),
                    base_y.as_ptr(), table.x_bitmap.as_ptr(), out_index.as_mut_ptr(),
                    out_key.as_mut_ptr(), 500) };
                if count == usize::MAX {
                    native_fallbacks += 1;
                    rust_find(curve, point, &minus, &table, &mut scratch)?
                } else {
                    if count > minus.len() { return Err("native scan output overflow".into()); }
                    native_candidates += count as u64;
                    let mut previous = None;
                    for &index in &out_index[..count] {
                        if index as usize >= minus.len() || previous.is_some_and(|v| index <= v) {
                            return Err("native scan indices out of order".into());
                        }
                        previous = Some(index);
                    }
                    out_index[..count].iter().zip(&out_key[..count]).find_map(|(&k, &key)|
                        table.get(key as u64).map(|payload| (k as usize, payload)))
                }
            } else {
                native_fallbacks += 1;
                rust_find(curve, point, &minus, &table, &mut scratch)?
            }
        } else {
            rust_find(curve, point, &minus, &table, &mut scratch)?
        };
        if AUDIT_NATIVE {
            let reference = rust_find(curve, point, &minus, &table, &mut scratch)?;
            if hit != reference { return Err(format!("native first-hit mismatch on trial {trial}: {hit:?} != {reference:?}").into()); }
        }
        if trace_path.is_some() {
            trace.extend_from_slice(&hit.map_or(u32::MAX, |(k, _)| k as u32).to_le_bytes());
        }
        let Some((k, payload)) = hit
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
        if let Some(path) = &trace_path { fs::write(path, &trace)?; }
        println!("{{\"mode\":\"{}\",\"seed\":{},\"scalar\":{},\"trials\":{},\"relations\":{},\"entries\":{},\"setup_ns\":{},\"table_ns\":{},\"elimination_ns\":{},\"total_ns\":{},\"native_calls\":{},\"native_fallbacks\":{},\"native_candidates\":{}}}", args[2], args[3], scalar, trial, relations, table.len(), setup.as_nanos(), table_time.as_nanos(), elimination_ns, started.elapsed().as_nanos(), native_calls, native_fallbacks, native_candidates);
        return Ok(());
    }
    Err("relation limit exhausted".into())
}
