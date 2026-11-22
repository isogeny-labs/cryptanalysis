//! Prepare the frozen public known-answer panel, without running a solver.
//!
//! The tiny-field oracle deliberately uses neither the tensor implementation
//! nor its curve arithmetic. Expected answers go only into the separate manifest.

use serde_json::{json, Value};
use std::collections::BTreeSet;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;

type Point = Option<(u64, u64)>;
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

#[derive(Clone, Copy)]
struct TinyCurve {
    p: u64,
    a: u64,
    b: u64,
    r: u64,
    generator: Point,
}

const CURVES: [TinyCurve; 3] = [
    TinyCurve {
        p: 5,
        a: 2,
        b: 1,
        r: 7,
        generator: Some((0, 1)),
    },
    TinyCurve {
        p: 7,
        a: 0,
        b: 3,
        r: 13,
        generator: Some((1, 2)),
    },
    TinyCurve {
        p: 17,
        a: 2,
        b: 2,
        r: 19,
        generator: Some((5, 1)),
    },
];

impl TinyCurve {
    fn contains(self, point: Point) -> bool {
        point.map_or(true, |(x, y)| {
            x < self.p && y < self.p && y * y % self.p == (x * x * x + self.a * x + self.b) % self.p
        })
    }

    // Only the fixed fields p <= 17 reach this oracle. Inversion is an
    // independent exhaustive search, not the library's extended-gcd routine.
    fn add(self, left: Point, right: Point) -> Result<Point> {
        let (Some((x, y)), Some((u, v))) = (left, right) else {
            return Ok(left.or(right));
        };
        if x == u && (y + v) % self.p == 0 {
            return Ok(None);
        }
        let (numerator, denominator) = if x == u {
            ((3 * x * x + self.a) % self.p, 2 * y % self.p)
        } else {
            ((v + self.p - y) % self.p, (u + self.p - x) % self.p)
        };
        let inverse = (1..self.p)
            .find(|i| i * denominator % self.p == 1)
            .ok_or("tiny oracle: noninvertible slope")?;
        let slope = numerator * inverse % self.p;
        let rx = (slope * slope + 2 * self.p - x - u) % self.p;
        let ry = (slope * (x + self.p - rx) + self.p - y) % self.p;
        Ok(Some((rx, ry)))
    }

    fn validate(self) -> Result<Vec<Point>> {
        // This is a bounded fixture oracle, not a general curve validator.
        let prime = |n: u64| n >= 2 && (2..n).all(|d| n % d != 0);
        if self.p > 17
            || self.p < 5
            || self.r > 19
            || !prime(self.p)
            || !prime(self.r)
            || self.a >= self.p
            || self.b >= self.p
            || self.generator.is_none()
            || !self.contains(self.generator)
            || (4 * self.a.pow(3) + 27 * self.b.pow(2)) % self.p == 0
        {
            return Err("tiny oracle: invalid curve parameters".into());
        }
        let mut points = BTreeSet::from([None]);
        for x in 0..self.p {
            for y in 0..self.p {
                if self.contains(Some((x, y))) {
                    points.insert(Some((x, y)));
                }
            }
        }
        if points.len() as u64 != self.r {
            return Err("tiny oracle: full cardinality mismatch".into());
        }
        let mut orbit = vec![None];
        for _ in 1..=self.r {
            orbit.push(self.add(*orbit.last().unwrap(), self.generator)?);
        }
        if orbit[self.r as usize].is_some()
            || orbit[..self.r as usize]
                .iter()
                .copied()
                .collect::<BTreeSet<_>>()
                != points
        {
            return Err("tiny oracle: generator orbit mismatch".into());
        }
        Ok(orbit)
    }
}

struct Case {
    id: String,
    split: &'static str,
    curve: TinyCurve,
    seed: u64,
    scalar: u64,
    target: Point,
}

impl Case {
    fn problem(&self) -> Value {
        let pair = |point: Point| point.map(|(x, y)| [x.to_string(), y.to_string()]);
        json!({
            "p": self.curve.p.to_string(), "a": self.curve.a.to_string(),
            "b": self.curve.b.to_string(), "r": self.curve.r.to_string(),
            "cofactor": "1", "generator": pair(self.curve.generator),
            "target": pair(self.target), "fixture_seed": self.seed,
            "slots": 2, "trials": 16, "columns": 4096,
            "steps": 2_000_000_000u64, "vector": 2_000_000, "bits": 1_000_000,
        })
    }

    fn relative_path(&self) -> String {
        format!("problems/{}.json", self.id)
    }
}

fn panel() -> Result<Vec<Case>> {
    let mut cases = Vec::new();
    for curve in CURVES {
        let orbit = curve.validate()?;
        for (split, seeds) in [("development", 1..=10), ("holdout", 101..=104)] {
            for seed in seeds {
                for (target_index, scalar) in [1, curve.r - 2].into_iter().enumerate() {
                    cases.push(Case {
                        // No scalar appears in a solver's input filename.
                        id: format!("p{}-{split}-s{seed:03}-t{target_index}", curve.p),
                        split,
                        curve,
                        seed,
                        scalar,
                        target: orbit[scalar as usize],
                    });
                }
            }
        }
    }
    Ok(cases)
}

fn write_new(path: &Path, value: &Value) -> Result<()> {
    let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
    serde_json::to_writer_pretty(&mut file, value)?;
    file.write_all(b"\n")?;
    file.sync_all()?;
    Ok(())
}

fn prepare(output: &Path) -> Result<()> {
    // Validate every curve and target before creating any output. Refuse an
    // existing directory, including a partial earlier preparation attempt.
    let cases = panel()?;
    fs::create_dir(output)?;
    fs::create_dir(output.join("problems"))?;
    for case in &cases {
        write_new(&output.join(case.relative_path()), &case.problem())?;
    }
    let entries: Vec<_> = cases
        .iter()
        .map(|case| {
            json!({
                "id": case.id, "split": case.split, "problem": case.relative_path(),
                "expected_scalar": case.scalar.to_string(), "full_cardinality": case.curve.r,
            })
        })
        .collect();
    // Write this last. Require a successful command, not just this file's
    // presence: a failed write can leave partial evidence. Preparation does not
    // attest execution, certificate replay, or benchmark admission.
    write_new(
        &output.join("manifest.json"),
        &json!({
            "schema": "hashed-ecdl-panel/v1", "status": "prepared",
            "protocol": "crypto:research/hashed_ecdl_speed_20261029/PROTOCOL.md",
            "baseline": "d188c5a6775dff07129084ab2f3f7ae39547c9fc",
            "paired_baseline": "1caa747d9bb888e0b98c739a59b17fbb1bd92e99",
            "development_inputs": 60, "holdout_inputs": 24,
            "repetitions": 3, "required_aa_rounds": 5, "required_ab_rounds": 5,
            "execution": "not_run", "measurements": null, "cases": entries,
        }),
    )?;
    Ok(())
}

fn run() -> Result<()> {
    let mut args = std::env::args_os().skip(1);
    let command = args.next();
    let output = args.next();
    if command.as_deref() != Some(std::ffi::OsStr::new("prepare"))
        || output.is_none()
        || args.next().is_some()
    {
        return Err("usage: hashed-ecdl-panel prepare NEW_DIRECTORY".into());
    }
    prepare(Path::new(&output.unwrap()))?;
    println!("Prepared 60 development and 24 holdout problems; no solver or benchmark ran.");
    Ok(())
}

fn main() {
    if let Err(error) = run() {
        eprintln!("{error}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use hashed_ecdl_tensor::curve::{Curve, Point as NativePoint};
    use hashed_ecdl_tensor::{Limits, Meter};

    #[test]
    fn oracle_checks_full_cardinality_and_all_native_multiples() {
        for spec in CURVES {
            let orbit = spec.validate().unwrap();
            let mut meter = Meter::new(Limits::default());
            let native = |point: Point| match point {
                None => NativePoint::Infinity,
                Some((x, y)) => NativePoint::Affine {
                    x: x.into(),
                    y: y.into(),
                },
            };
            let curve = Curve::new(
                spec.p.into(),
                spec.a.into(),
                spec.b.into(),
                spec.r.into(),
                native(spec.generator),
                &mut meter,
            )
            .unwrap();
            for (k, point) in orbit.into_iter().enumerate() {
                assert_eq!(
                    curve.mul(curve.generator(), &k.into(), &mut meter).unwrap(),
                    native(point)
                );
            }
            assert!(TinyCurve { r: 11, ..spec }.validate().is_err());
            assert!(TinyCurve {
                generator: None,
                ..spec
            }
            .validate()
            .is_err());
            assert!(TinyCurve {
                generator: Some((spec.p, 0)),
                ..spec
            }
            .validate()
            .is_err());
        }
    }

    #[test]
    fn panel_preserves_every_frozen_case_and_separates_answers() {
        let cases = panel().unwrap();
        assert_eq!(cases.len(), 84);
        assert_eq!(
            cases.iter().filter(|c| c.split == "development").count(),
            60
        );
        assert_eq!(cases.iter().filter(|c| c.split == "holdout").count(), 24);
        assert_eq!(
            cases
                .iter()
                .map(Case::relative_path)
                .collect::<BTreeSet<_>>()
                .len(),
            84
        );
        for spec in CURVES {
            for seed in (1..=10).chain(101..=104) {
                let selected: Vec<_> = cases
                    .iter()
                    .filter(|c| c.curve.p == spec.p && c.seed == seed)
                    .collect();
                assert_eq!(selected.len(), 2);
                assert_eq!(
                    selected.iter().map(|c| c.scalar).collect::<BTreeSet<_>>(),
                    BTreeSet::from([1, spec.r - 2])
                );
            }
        }
        for case in &cases {
            let problem = case.problem();
            let mut keys: Vec<_> = problem
                .as_object()
                .unwrap()
                .keys()
                .map(String::as_str)
                .collect();
            keys.sort_unstable();
            assert_eq!(
                keys,
                [
                    "a",
                    "b",
                    "bits",
                    "cofactor",
                    "columns",
                    "fixture_seed",
                    "generator",
                    "p",
                    "r",
                    "slots",
                    "steps",
                    "target",
                    "trials",
                    "vector"
                ]
            );
            assert_eq!(problem["steps"], 2_000_000_000u64);
            assert_eq!(problem["slots"], 2);
            assert!(case.target.is_some());
        }
    }

    #[test]
    fn preparation_is_complete_and_existing_evidence_is_never_replaced() {
        let dir =
            std::env::temp_dir().join(format!("hashed-ecdl-panel-test-{}", std::process::id()));
        // Exclusive creation also prevents a test from deleting an old fixture.
        fs::create_dir(&dir).unwrap();
        let output = dir.join("panel");
        prepare(&output).unwrap();
        let manifest_bytes = fs::read(output.join("manifest.json")).unwrap();
        let manifest: Value = serde_json::from_slice(&manifest_bytes).unwrap();
        assert_eq!(manifest["execution"], "not_run");
        assert!(manifest["measurements"].is_null());
        let cases = panel().unwrap();
        for case in &cases {
            let actual: Value =
                serde_json::from_slice(&fs::read(output.join(case.relative_path())).unwrap())
                    .unwrap();
            assert_eq!(actual, case.problem());
        }
        assert_eq!(manifest["cases"].as_array().unwrap().len(), cases.len());
        assert!(prepare(&output).is_err());
        assert_eq!(
            fs::read(output.join("manifest.json")).unwrap(),
            manifest_bytes
        );
        let existing = output.join(cases[0].relative_path());
        let before = fs::read(&existing).unwrap();
        assert!(write_new(&existing, &json!({"replaced": true})).is_err());
        assert_eq!(fs::read(existing).unwrap(), before);
        fs::remove_dir_all(dir).unwrap();
    }
}
