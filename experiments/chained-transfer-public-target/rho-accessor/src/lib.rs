//! Versioned output accessor for the original rho; no walk or arithmetic change.
#![allow(dead_code, static_mut_refs)]
use chained_n4_public_target::CheckedInstance;
pub use chained_n4_public_target::{common, ghs, ic, pic};
use serde_json::{json, Value};

#[cfg(test)]
#[path = "../../native/original/solver.rs"]
mod legacy;
#[path = "../derived/public_solver_with_answer.rs"]
pub mod solver;

pub fn counters(c: &common::Cnt) -> [u64; 7] {
    [c.mul, c.inv, c.add, c.lmul, c.ladd, c.hash, c.cmp]
}

pub fn solve(checked: &CheckedInstance, input: &[u8]) -> Result<Value, String> {
    let targets = checked.parse(input)?;
    let mut rows = Vec::new();
    for (i, target) in targets.into_iter().enumerate() {
        let seed = 0x58a1 + i as u64;
        let result = solver::rho_target(&checked.inst, target, seed);
        let check = result
            .k_found
            .is_some_and(|k| checked.verify_recovered(target, k));
        rows.push(json!({"target_index":i,"target":checked.encode(target),"seed":seed,
            "ok":result.ok && check,"original_ok":result.ok,"k_found":result.k_found,
            "steps":result.steps,"distinguished_points":result.dps,"counters":counters(&result.cnt),
            "original_wall_s_correctness_only":result.wall,"independent_original_source_check":check}));
    }
    Ok(
        json!({"ok":rows.iter().all(|x|x["ok"]==true),"results":rows,
        "scope":"five separate original rho tables;public Q only;correctness not performance"}),
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn five_original_rho_answers_and_both_literal_controls() {
        let checked = CheckedInstance::construct().unwrap();
        let targets = checked
            .parse(include_bytes!("../../fixtures/public-five.json"))
            .unwrap();
        let answers: Vec<Value> =
            serde_json::from_slice(include_bytes!("../../fixtures/expected-OUTSIDE-input.json"))
                .unwrap();
        assert_eq!(targets.len(), 5);
        for (i, target) in targets.into_iter().enumerate() {
            let witness = answers[i]["original_native_recovered_scalar"]
                .as_u64()
                .unwrap();
            let seed = 0x58a1 + i as u64;
            let before_target = common::snap();
            assert_eq!(
                checked.inst.ec.mul(&checked.inst.g, witness as u128),
                target
            );
            let target_construction = counters(&common::snap().since(&before_target));
            let old = legacy::rho(&checked.inst, witness, seed);
            let public =
                chained_n4_public_target::public_solver::rho_target(&checked.inst, target, seed);
            let new = solver::rho_target(&checked.inst, target, seed);
            assert_eq!(
                (old.ok, old.steps, old.dps),
                (public.ok, public.steps, public.dps)
            );
            assert_eq!(
                (public.ok, public.steps, public.dps, counters(&public.cnt)),
                (new.ok, new.steps, new.dps, counters(&new.cnt))
            );
            assert_eq!(
                counters(&old.cnt),
                std::array::from_fn(|j| { counters(&public.cnt)[j] + target_construction[j] })
            );
            assert!(old.ok && public.ok && new.ok);
            assert_eq!(new.k_found, Some(witness));
            assert!(checked.verify_recovered(target, new.k_found.unwrap()));
            println!(
                "N4_RHO_ANSWER {}",
                json!({"target_index":i,"target":checked.encode(target),
                "seed":seed,"k_found":new.k_found,"steps":new.steps,"distinguished_points":new.dps,
                "counters":counters(&new.cnt),"legacy_and_frozen_public_match":true,
                "legacy_counters_include_exact_target_construction":target_construction,
                "independent_original_source_check":true,"scope":"unsigned correctness only"})
            );
        }
    }
}
