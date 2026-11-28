//! Off-panel exactness controls for bit-sampling factor-base buckets.
use hashed_ecdl_tensor::arithmetic::Seeded;
use hashed_ecdl_tensor::curve::{Curve, Point};
use hashed_ecdl_tensor::prepared::{self, PairTable, Statistics};
use hashed_ecdl_tensor::reduction::{self, Config, FactorBase, HashSeed};
use hashed_ecdl_tensor::{Limits, Meter};

fn curve(meter: &mut Meter) -> Curve {
    Curve::new(
        17u8.into(),
        2u8.into(),
        2u8.into(),
        19u8.into(),
        Point::Affine {
            x: 5u8.into(),
            y: 1u8.into(),
        },
        meter,
    )
    .unwrap()
}

fn bases(curve: &Curve, thresholds: [u8; 2], meter: &mut Meter) -> Vec<FactorBase> {
    thresholds
        .into_iter()
        .enumerate()
        .map(|(slot, threshold)| {
            FactorBase::new(
                curve,
                37u8.into(),
                threshold.into(),
                HashSeed {
                    alpha: (1 + 2 * slot as u8).into(),
                    beta: 4u8.into(),
                },
                meter,
            )
            .unwrap()
        })
        .collect()
}

#[test]
fn every_public_query_matches_exact_hash_lookup() {
    for thresholds in [[12, 24], [24, 12], [12, 12]] {
        let mut work = Meter::new(Limits::default());
        let curve = curve(&mut work);
        let bases = bases(&curve, thresholds, &mut work);
        let control =
            PairTable::new(&curve, &bases, &mut Statistics::default(), &mut work).unwrap();
        for bits in [1, 4, 8] {
            for seed in [0, 17, 918] {
                let mut index =
                    PairTable::new(&curve, &bases, &mut Statistics::default(), &mut work).unwrap();
                index.enable_lsh(bits, seed, &mut work).unwrap();
                for smallest_first in [false, true] {
                    for scalar in 0..19u8 {
                        let target = curve
                            .mul(curve.generator(), &scalar.into(), &mut work)
                            .unwrap();
                        let mut exact_stats = Statistics::default();
                        let mut lsh_stats = Statistics::default();
                        let expected = control
                            .decompose(&target, smallest_first, &mut exact_stats, &mut work)
                            .unwrap();
                        let actual = index
                            .decompose(&target, smallest_first, &mut lsh_stats, &mut work)
                            .unwrap();
                        assert_eq!(
                            actual, expected,
                            "{thresholds:?}, bits={bits}, seed={seed}, scalar={scalar}"
                        );
                        assert_eq!(lsh_stats.lookups, exact_stats.lookups);
                        assert_eq!(lsh_stats.lsh_probes, lsh_stats.lookups);
                    }
                }
            }
        }
    }
}

#[test]
fn invalid_configuration_does_not_poison_the_prepared_pair() {
    let mut work = Meter::new(Limits::default());
    let curve = curve(&mut work);
    let bases = bases(&curve, [12, 24], &mut work);
    let mut table = PairTable::new(&curve, &bases, &mut Statistics::default(), &mut work).unwrap();
    assert!(table.enable_lsh(11, 7, &mut work).is_err());
    table.enable_lsh(1, 7, &mut work).unwrap();
    assert!(table.enable_lsh(1, 8, &mut work).is_err());
}

#[test]
fn seeded_relation_certificate_and_label_rng_match_control() {
    let mut setup = Meter::new(Limits::default());
    let curve = curve(&mut setup);
    let target = curve
        .mul(curve.generator(), &3u8.into(), &mut setup)
        .unwrap();
    let config = Config {
        hash_prime: Some(37u8.into()),
        threshold: Some(12u8.into()),
        slots: 2,
        trials: 32,
        columns: 64,
    };
    for seed in [1, 42, 83] {
        let mut control_rng = Seeded(seed);
        let mut lsh_rng = Seeded(seed);
        let mut control_work = Meter::new(Limits::default());
        let mut lsh_work = Meter::new(Limits::default());
        let control = prepared::solve_joint(
            &curve,
            &target,
            &config,
            &mut control_rng,
            true,
            &mut Statistics::default(),
            &mut control_work,
        )
        .unwrap();
        let mut statistics = Statistics::default();
        let candidate = prepared::solve_joint_lsh(
            &curve,
            &target,
            &config,
            &mut lsh_rng,
            true,
            4,
            901,
            &mut statistics,
            &mut lsh_work,
        )
        .unwrap();
        assert_eq!(
            serde_json::to_value(&candidate).unwrap(),
            serde_json::to_value(&control).unwrap()
        );
        assert_eq!(control_rng.0, lsh_rng.0);
        assert!(statistics.lsh_probes > 0);
        reduction::verify(&curve, &target, &candidate, &mut lsh_work).unwrap();
    }
}
