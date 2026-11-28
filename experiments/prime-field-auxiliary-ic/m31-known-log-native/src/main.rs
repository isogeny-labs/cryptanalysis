use prime_field_auxiliary_ic::{Curve, FactorBase, PairIndex};
use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::time::{Duration, Instant};

const N: u64 = 2_147_505_293;
const BASE_SEED: u64 = 20_261_128;

struct SplitMix64(u64);
impl SplitMix64 {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9e3779b97f4a7c15);
        let mut x = self.0;
        x = (x ^ (x >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
        x = (x ^ (x >> 27)).wrapping_mul(0x94d049bb133111eb);
        x ^ (x >> 31)
    }
}
fn add(a: u64, b: u64) -> u64 {
    ((u128::from(a) + u128::from(b)) % u128::from(N)) as u64
}
fn sub(a: u64, b: u64) -> u64 {
    ((u128::from(a) + u128::from(N) - u128::from(b)) % u128::from(N)) as u64
}
fn arg(args: &[String], flag: &str) -> Result<u64, Box<dyn std::error::Error>> {
    let pos = args.iter().position(|x| x == flag).ok_or("missing flag")?;
    Ok(args.get(pos + 1).ok_or("missing flag value")?.parse()?)
}
fn run() -> Result<(), Box<dyn std::error::Error>> {
    let started = Instant::now();
    let args: Vec<String> = env::args().collect();
    let qx = arg(&args, "--qx")?;
    let qy = arg(&args, "--qy")?;
    let seed = arg(&args, "--seed")?;
    let columns = usize::try_from(arg(&args, "--columns")?)?;
    if !(1..=2048).contains(&columns) {
        return Err("columns must be 1..=2048".into());
    }
    let curve = Curve::<31>::new(2, 14)?;
    let g = curve.point(1, 814455902)?;
    let q = curve.point(qx, qy)?;
    if curve.mul(Some(g), N)?.is_some() || curve.mul(Some(q), N)?.is_some() {
        return Err("point outside declared prime-order group".into());
    }
    let base_started = Instant::now();
    let mut rng = SplitMix64(BASE_SEED);
    let mut seen = BTreeSet::new();
    let mut sampled = BTreeMap::new();
    let mut roots = Vec::with_capacity(columns);
    while roots.len() < columns {
        let scalar = rng.next() % N;
        if scalar == 0 || !seen.insert(scalar.min(N - scalar)) {
            continue;
        }
        let point = curve
            .mul(Some(g), scalar)?
            .ok_or("zero sampled base point")?;
        if sampled.insert(point.x(), (point, scalar)).is_some() {
            return Err("distinct signed scalars collided in x".into());
        }
        roots.push(point.x());
    }
    let base = FactorBase::without_maps(curve, &roots)?;
    if base.representatives().len() != columns {
        return Err("factor base lost a sampled point".into());
    }
    let mut labels = Vec::with_capacity(columns);
    for &point in base.representatives() {
        let (sampled_point, sampled_scalar) =
            sampled.get(&point.x()).ok_or("missing sampled point")?;
        let label = if point == *sampled_point {
            *sampled_scalar
        } else if point == curve.negate(*sampled_point)? {
            N - sampled_scalar
        } else {
            return Err("factor-base lift changed sampled point".into());
        };
        labels.push(label);
    }
    let base_ns = base_started.elapsed().as_nanos();
    let index_started = Instant::now();
    let index = PairIndex::new(&base, 4_194_304, 64)?;
    let index_ns = index_started.elapsed().as_nanos();
    let mut workspace = index.workspace();
    let mut search_rng = SplitMix64(20_261_129 ^ seed);
    let mut a = search_rng.next() % N;
    let mut point = curve.add(Some(q), curve.mul(Some(g), a)?)?;
    let online_started = Instant::now();
    for query in 1..=1_000_000u64 {
        if let Some(p) = point {
            if let Some(row) = index.decompose(2, p, &mut workspace)? {
                let mut sum = 0;
                let mut check = None;
                for term in row.summands() {
                    let label = labels[term.index];
                    sum = add(sum, if term.negative { N - label } else { label });
                    let summand = if term.negative {
                        curve.negate(base.representatives()[term.index])?
                    } else {
                        base.representatives()[term.index]
                    };
                    check = curve.add(check, Some(summand))?;
                }
                if check != point {
                    return Err("known-log witness replay failed".into());
                }
                let scalar = sub(sum, a);
                if curve.mul(Some(g), scalar)? != Some(q) {
                    return Err("known-log answer verification failed".into());
                }
                let online_ns = online_started.elapsed().as_nanos();
                let cold_ns = started.elapsed().as_nanos();
                let points: Vec<_> = base
                    .representatives()
                    .iter()
                    .map(|p| [p.x(), p.y()])
                    .collect();
                let terms: Vec<_> = row
                    .summands()
                    .iter()
                    .map(|t| [t.index as u64, u64::from(t.negative)])
                    .collect();
                println!("{{\"schema\":\"m31-known-log-control/v1\",\"Q\":[{qx},{qy}],\"G\":[1,814455902],\"n\":{N},\"columns\":{columns},\"seed\":{seed},\"base_seed\":{BASE_SEED},\"status\":\"solved\",\"scalar\":{scalar},\"offset\":{a},\"terms\":{terms:?},\"base_points\":{points:?},\"base_labels\":{labels:?},\"queries\":{query},\"entries\":{},\"base_ns\":{base_ns},\"index_ns\":{index_ns},\"online_ns\":{online_ns},\"cold_to_report_ns\":{cold_ns}}}",index.stats().entries);
                return Ok(());
            }
        }
        a = add(a, 1);
        point = curve.add(point, Some(g))?;
        if online_started.elapsed() >= Duration::from_secs(5) {
            break;
        }
    }
    println!("{{\"schema\":\"m31-known-log-control/v1\",\"Q\":[{qx},{qy}],\"columns\":{columns},\"seed\":{seed},\"status\":\"incomplete\",\"scalar\":null,\"base_ns\":{base_ns},\"index_ns\":{index_ns},\"online_ns\":{},\"cold_to_report_ns\":{}}}",online_started.elapsed().as_nanos(),started.elapsed().as_nanos());
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("m31-known-log-control: {error}");
        std::process::exit(2);
    }
}
