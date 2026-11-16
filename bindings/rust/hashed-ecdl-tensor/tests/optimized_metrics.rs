//! Observer compatibility controls, without performance assertions.
use hashed_ecdl_tensor::arithmetic::Seeded;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::optimized::{self, Options, Statistics, WalkOptions};
use hashed_ecdl_tensor::reduction::Config;
use hashed_ecdl_tensor::{Limits, Meter};

#[test]
fn combined_options_preserve_target_boundary_and_complete_step_accounting() {
    let mut setup = Meter::new(Limits::default());
    let curve = Curve::new(
        17u8.into(),
        2u8.into(),
        2u8.into(),
        19u8.into(),
        Point::Affine {
            x: 5u8.into(),
            y: 1u8.into(),
        },
        &mut setup,
    )
    .unwrap();
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut setup)
        .unwrap();
    let options = Options {
        subgroup_provenance: true,
        batch_chunk: 8,
        relation_graph: true,
        extra_scans: 4,
        walk: Some(WalkOptions {
            table_size: 16,
            block_length: 16,
        }),
        ..Options::default()
    };
    let config = Config {
        hash_prime: Some(37u8.into()),
        threshold: Some(37u8.into()),
        slots: 2,
        columns: 64,
        trials: 8,
    };
    let session = hashed_ecdl_tensor::metrics::Session::start().unwrap();
    let mut meter = Meter::new(Limits::default());
    let answer = optimized::solve(
        &curve,
        &target,
        &config,
        &options,
        &mut Seeded(42),
        &mut Statistics::default(),
        &mut meter,
    )
    .unwrap();
    let snapshot = session.finish().unwrap();
    assert_eq!(answer.scalar, 3u8.into());
    assert_eq!(snapshot.online_start_phase, Some("target_validation"));
    assert_eq!(snapshot.phases["target_validation"].scalar_mults, 1);
    assert!(snapshot.phases["factor_base"].meter_steps > 0);
    assert!(snapshot.phases["relation_search"].adds > 0);
    assert_eq!(
        snapshot.phases.values().map(|p| p.meter_steps).sum::<u64>(),
        meter.used
    );
    assert_eq!(
        snapshot.online_phases_ns.values().sum::<u64>(),
        snapshot.online_wall_ns.unwrap()
    );
}
