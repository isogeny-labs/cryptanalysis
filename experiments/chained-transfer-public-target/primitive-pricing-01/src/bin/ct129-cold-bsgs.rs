//! CT129: cold (fresh-table) source BSGS vs direct degree-169 isogeny + BSGS.
//! This is a lower-work elliptic proxy, NOT a complete Jacobian ECDLP attack.
//! The known scalar is held only by the fixture/validator; solve() sees G,Q,n.
use chained_n4_beta_rational_lift::{point_json, Rational6};
use chained_n4_fixed_jacobian_chain_evaluator as chain;
use chained_n4_public_target::CheckedInstance;
use isogeny_algos::curve::{self, Curve, Pt};
use isogeny_algos::field::Field;
use serde_json::{json, Value};
use std::collections::HashMap;
use std::hash::Hash;
use std::time::Instant;

fn ns(start: Instant) -> u64 {
    u64::try_from(start.elapsed().as_nanos()).expect("elapsed nanoseconds fit u64")
}

fn ceil_sqrt(n: u64) -> u64 {
    let mut lo = 0u64;
    let mut hi = n.min(1 << 32) + 1;
    while lo + 1 < hi {
        let mid = lo + (hi - lo) / 2;
        if mid <= n / mid {
            lo = mid;
        } else {
            hi = mid;
        }
    }
    if lo * lo == n { lo } else { lo + 1 }
}

/// Deterministic, independently verifiable BSGS. Every invocation allocates
/// a new baby table. No scalar-indexed table, advice, or amortized storage.
fn solve<F: Field>(
    f: &F,
    curve: &Curve<F::E>,
    generator: Pt<F::E>,
    public: Pt<F::E>,
    order: u64,
) -> Result<(u64, u64), String>
where
    F::E: Hash + Eq,
{
    if order < 3 || generator == Pt::Inf {
        return Err("invalid subgroup order or identity generator".into());
    }
    let width = ceil_sqrt(order);
    let mut babies: HashMap<Pt<F::E>, u64> = HashMap::with_capacity(width as usize);
    let mut baby = Pt::Inf;
    for j in 0..width {
        babies.entry(baby).or_insert(j);
        baby = curve::padd(f, curve, &baby, &generator);
    }
    let minus_width = curve::neg(
        f, &curve::pmul(f, curve, &generator, u128::from(width)),
    );
    let mut giant = public;
    for i in 0..=width {
        if let Some(j) = babies.get(&giant) {
            let candidate = i.checked_mul(width).and_then(|x| x.checked_add(*j))
                .ok_or("BSGS index overflow")?;
            if candidate < order
                && curve::pmul(f, curve, &generator, u128::from(candidate)) == public
            {
                return Ok((candidate, babies.len() as u64));
            }
        }
        giant = curve::padd(f, curve, &giant, &minus_width);
    }
    Err("BSGS exhausted: no valid source subgroup logarithm".into())
}

fn main() -> Result<(), String> {
    // Fixed supported alternate instance, not the original 2,773,073-order case.
    let setup_start = Instant::now();
    let checked = CheckedInstance::construct()
        .map_err(|e| format!("checked original-instance constructor: {e}"))?;
    let checked_setup_ns = ns(setup_start);

    let runtime_start = Instant::now();
    let runtime = chain::Runtime::construct(&checked)
        .map_err(|e| format!("three-model geometry constructor: {e}"))?;
    let runtime_setup_ns = ns(runtime_start);
    let source = &runtime.geometry.models[0];
    let target = &runtime.geometry.models[2];
    let sf = source.source.field();
    let sc = source.source.curve();
    let tf = &target.quadratic.f;
    let tc = &target.quadratic.curve;
    let ell = chain::ELL as u64;

    let generator = curve::pmul(sf, sc, &source.source.generator(), 4);
    if generator == Pt::Inf
        || !curve::on_curve(sf, sc, &generator)
        || curve::pmul(sf, sc, &generator, u128::from(ell)) != Pt::Inf
    {
        return Err("fixed source prime-subgroup generator rejected".into());
    }
    let composites = runtime.setup["actual_composite_certificates"].as_array()
        .ok_or("missing composite certificate table")?;
    let cert = composites.iter().find(|c| c["source"] == 0 && c["target"] == 2)
        .ok_or("missing original 0->2 composite")?;
    let map = Rational6::new(&cert["whole_composite"]);

    let mapped_generator = map.eval(&source.quadratic.f, chain::lift(generator));
    if mapped_generator == Pt::Inf
        || target.quadratic.admit(&mapped_generator).is_err()
        || !curve::on_curve(tf, tc, &mapped_generator)
        || curve::pmul(tf, tc, &mapped_generator, u128::from(ell)) != Pt::Inf
    {
        return Err("mapped generator not nonzero ell-torsion".into());
    }

    // Public known-answer vectors, frozen in the protocol. Tests include
    // trivial controls but primary comparisons are the three nontrivial rows.
    let scalars = [1u64, 2, 17, 12_345, ell - 1];
    let mut rows: Vec<Value> = Vec::new();
    for &secret_fixture_only in &scalars {
        let public = curve::pmul(sf, sc, &generator, u128::from(secret_fixture_only));
        if public == Pt::Inf || !curve::on_curve(sf, sc, &public)
            || curve::pmul(sf, sc, &public, u128::from(ell)) != Pt::Inf
        {
            return Err("source public fixture invalid".into());
        }
        let mapped = map.eval(&source.quadratic.f, chain::lift(public));
        if target.quadratic.admit(&mapped).is_err()
            || !curve::on_curve(tf, tc, &mapped)
            || curve::pmul(tf, tc, &mapped, u128::from(ell)) != Pt::Inf
            || curve::pmul(tf, tc, &mapped_generator, u128::from(secret_fixture_only)) != mapped
        {
            return Err("actual isogeny fails public known-answer transport".into());
        }

        // A/A, B/B and alternating ABBA are explicit; every individual solve
        // rebuilds the baby table and independently re-verifies on source.
        let mut blocks: Vec<Value> = Vec::new();
        for block in 0..4u64 {
            let order = if block % 2 == 0 {
                ["source", "target", "target", "source"]
            } else {
                ["target", "source", "source", "target"]
            };
            let mut times_source = Vec::new();
            let mut times_target = Vec::new();
            let mut table_sizes_source = Vec::new();
            let mut table_sizes_target = Vec::new();
            for arm in order {
                let start = Instant::now();
                let (recovered, table_size) = match arm {
                    "source" => solve(sf, sc, generator, public, ell)?,
                    "target" => {
                        // Include the TWO real rational-map calls for every
                        // single-target invocation, not only Q or a reused G.
                        let mg = map.eval(&source.quadratic.f, chain::lift(generator));
                        let mq = map.eval(&source.quadratic.f, chain::lift(public));
                        if mg != mapped_generator || mq != mapped {
                            return Err("mapped point changed across cold runs".into());
                        }
                        solve(tf, tc, mg, mq, ell)?
                    }
                    _ => unreachable!(),
                };
                // Include independent source verification in both timings.
                if recovered != secret_fixture_only
                    || curve::pmul(sf, sc, &generator, u128::from(recovered)) != public
                {
                    return Err(format!("incorrect {arm} recovery on fixture"));
                }
                let elapsed = ns(start);
                if arm == "source" {
                    times_source.push(elapsed);
                    table_sizes_source.push(table_size);
                } else {
                    times_target.push(elapsed);
                    table_sizes_target.push(table_size);
                }
            }
            if times_source.len() != 2 || times_target.len() != 2 {
                return Err("incomplete paired ABBA block".into());
            }
            blocks.push(json!({
                "block":block,
                "order":order,
                "source_ns":times_source,
                "target_ns":times_target,
                "source_table_entries":table_sizes_source,
                "target_table_entries":table_sizes_target
            }));
        }
        rows.push(json!({
            "scalar_fixture_only":secret_fixture_only,
            "primary_nontrivial_cohort": secret_fixture_only != 1 && secret_fixture_only != 2,
            "source_public":point_json(public),
            "destination_public":point_json(mapped),
            "all_source_and_destination_logarithms_verified":true,
            "blocks":blocks
        }));
    }
    let rss_kb = std::fs::read_to_string("/proc/self/status").ok()
        .and_then(|s| s.lines().find(|l| l.starts_with("VmHWM:"))
            .and_then(|l| l.split_whitespace().nth(1))
            .and_then(|l| l.parse::<u64>().ok()));
    if rss_kb.is_none() {
        return Err("Linux peak RSS mandatory for benchmark admission".into());
    }
    println!("{}", json!({
        "schema":"ct129-isogeny-bsgs-screen/v1",
        "standing":"[pcc:unverified]",
        "scope":"elliptic isogeny plus cold BSGS tables; NOT complete Jacobian transfer, optimized rho or IC",
        "source_prime":223,
        "subgroup_prime":ell,
        "full_group_order":chain::ORDER,
        "source_field_degree":3,
        "destination_field_degree":6,
        "original_instance_constructor_ns":checked_setup_ns,
        "full_geometry_runtime_setup_ns":runtime_setup_ns,
        "setup_scope":"once per process; NOT included in per-target paired solver timing",
        "memory_peak_linux_vm_hwm_kb":rss_kb,
        "source_and_target_inputs_identical_before_isogeny":true,
        "blocks_per_target":4,
        "solve_algorithm":"fresh-table deterministic BSGS on source or mapped target; source scalar independently checked",
        "rows":rows,
        "speedup_claim":false
    }));
    Ok(())
}
