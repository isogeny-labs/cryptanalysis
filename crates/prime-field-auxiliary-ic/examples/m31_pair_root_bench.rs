use prime_field_auxiliary_ic::{Backend, Curve, FactorBase};
use std::time::Instant;

const N: u64 = 2_147_505_293;

fn splitmix(state: &mut u64) -> u64 {
    *state = state.wrapping_add(0x9e3779b97f4a7c15);
    let mut value = *state;
    value = (value ^ (value >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
    value = (value ^ (value >> 27)).wrapping_mul(0x94d049bb133111eb);
    value ^ (value >> 31)
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let summands: u8 = args.get(1).expect("summands").parse().unwrap();
    let queries: u64 = args.get(2).expect("queries").parse().unwrap();
    let mut seed: u64 = args.get(3).expect("seed").parse().unwrap();
    let target_index: usize = args.get(4).expect("target index").parse().unwrap();
    assert!((3..=4).contains(&summands));
    let curve = Curve::<31>::new(2, 14).unwrap();
    let generator = curve.point(1, 814_455_902).unwrap();
    let targets = [
        curve.point(2_144_058_214, 807_222_724).unwrap(),
        curve.point(1_764_015_007, 688_050_509).unwrap(),
    ];
    let target = targets[target_index];
    let setup = Instant::now();
    let base = FactorBase::torus(curve, 7, None, Backend::Scalar)
        .unwrap()
        .direct_control()
        .unwrap();
    assert!(base
        .representatives()
        .iter()
        .all(|point| curve.mul(Some(*point), N).unwrap().is_none()));
    let mut workspace = base.workspace();
    let setup_ns = setup.elapsed().as_nanos();
    let online = Instant::now();
    let mut relations = 0u64;
    let mut digest = 0u64;
    for _ in 0..queries {
        let a = splitmix(&mut seed) % N;
        let b = splitmix(&mut seed) % N;
        let query = curve
            .add(
                curve.mul(Some(generator), a).unwrap(),
                curve.mul(Some(target), b).unwrap(),
            )
            .unwrap();
        let Some(query) = query else { continue };
        if let Some(row) = base
            .decompose_multi(summands, query, &mut workspace)
            .unwrap()
        {
            assert!(base.check_multi_relation(Some(query), row));
            relations += 1;
            for term in row.summands() {
                digest = digest
                    .wrapping_mul(0x9e3779b97f4a7c15)
                    .wrapping_add(term.index as u64 * 2 + u64::from(term.negative));
            }
        }
    }
    let online_ns = online.elapsed().as_nanos();
    println!(
        "{{\"schema\":\"m31-pair-root-bench/v1\",\"summands\":{summands},\"queries\":{queries},\"target_index\":{target_index},\"relations\":{relations},\"digest\":{digest},\"setup_ns\":{setup_ns},\"online_ns\":{online_ns},\"cold_ns\":{}}}",
        setup_ns + online_ns
    );
}
