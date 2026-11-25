//! Native worker threads compute mathematics; the parent alone writes SQLite.
use crate::field::FieldCache;
use crate::journal;
use crate::search::{search_job, JobResult, Spec};
use crate::verify::RawCache;
use anyhow::{ensure, Context, Result};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{mpsc, Arc};
use std::time::{Duration, Instant};

pub fn run(
    c: &mut Connection,
    workers: usize,
    max_jobs: Option<usize>,
    max_seconds: Option<u64>,
    retry_failed: bool,
    stopping: Arc<AtomicBool>,
) -> Result<Value> {
    journal::guard(c)?;
    ensure!((1..=64).contains(&workers), "workers must be in 1..=64");
    let recovered = journal::recover(c, retry_failed)?;
    if recovered != 0 {
        eprintln!("{}", json!({"event":"jobs_recovered","count":recovered}));
    }
    let began = Instant::now();
    let mut heartbeat = Instant::now();
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(workers)
        .build()?;
    let cache = Arc::new(FieldCache::default());
    let (tx, rx) = mpsc::channel::<(String, std::result::Result<JobResult, String>)>();
    let (mut claimed, mut completed, mut failed, mut active) = (0, 0, 0, 0);
    loop {
        while active < workers
            && !stopping.load(Ordering::Relaxed)
            && max_jobs.is_none_or(|limit| claimed < limit)
            && max_seconds.is_none_or(|limit| began.elapsed() < Duration::from_secs(limit))
        {
            let Some((id, job)) = journal::claim(c)? else {
                break;
            };
            active += 1;
            claimed += 1;
            let tx = tx.clone();
            let cache = Arc::clone(&cache);
            pool.spawn(move || {
                let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                    search_job(&job, &cache)
                }))
                .map_err(|_| "worker panicked".to_owned())
                .and_then(|r| r.map_err(|e| format!("{e:#}")));
                let _ = tx.send((id, result));
            });
        }
        if active == 0 {
            break;
        }
        match rx.recv_timeout(Duration::from_millis(250)) {
            Ok((id, result)) => {
                active -= 1;
                match result {
                    Ok(result) => {
                        journal::complete(c, &id, &result)?;
                        completed += 1;
                        eprintln!(
                            "{}",
                            json!({"event":"job_complete","job_id":id,"completed_this_run":completed,
                            "candidates":result.candidates.len(),"wall_seconds":result.wall_seconds})
                        );
                    }
                    Err(error) => {
                        journal::fail(c, &id, &error)?;
                        failed += 1;
                        eprintln!(
                            "{}",
                            json!({"event":"job_failed","job_id":id,"error":error})
                        );
                    }
                }
            }
            Err(mpsc::RecvTimeoutError::Timeout) => (),
            Err(e) => return Err(e.into()),
        }
        if heartbeat.elapsed() >= Duration::from_secs(20) {
            eprintln!(
                "{}",
                json!({"event":"heartbeat","completed_this_run":completed,"in_flight":active,
                "elapsed_seconds":began.elapsed().as_secs_f64()})
            );
            heartbeat = Instant::now();
        }
    }
    Ok(
        json!({"completed_this_run":completed,"failed_this_run":failed,"interrupted":stopping.load(Ordering::Relaxed),
        "complete_run_wall_seconds":began.elapsed().as_secs_f64(),
        "timing_scope":"search invocation only; not a complete DLP attack or calibrated cost", "status":journal::status(c)?}),
    )
}
pub fn check_candidates(c: &mut Connection, limit: Option<usize>) -> Result<Value> {
    journal::guard(c)?;
    let mut cache = RawCache::default();
    let mut checked = 0;
    for row in journal::candidates(c)?
        .into_iter()
        .filter(|r| !r.raw_verified)
    {
        if limit.is_some_and(|l| checked >= l) {
            break;
        }
        let began = Instant::now();
        crate::verify::verify_candidate(&row.candidate, &mut cache)?;
        let seconds = began.elapsed().as_secs_f64();
        c.execute(
            "UPDATE candidates SET raw_verified=1,verification_seconds=? WHERE spectral_model_id=?",
            params![seconds, row.candidate.spectral_model_id],
        )?;
        checked += 1;
        eprintln!(
            "{}",
            json!({"event":"candidate_counts_checked","spectral_model_id":row.candidate.spectral_model_id,"wall_seconds":seconds})
        );
    }
    Ok(json!({"checked_this_run":checked,"status":journal::status(c)?}))
}
pub fn identify_sources(c: &mut Connection, limit: Option<usize>) -> Result<Value> {
    journal::guard(c)?;
    let rows = journal::candidates(c)?;
    let mut groups: BTreeMap<Spec, BTreeSet<i64>> = BTreeMap::new();
    for row in rows.iter().filter(|r| r.source.is_none()) {
        let m = &row.candidate.model;
        groups
            .entry(Spec {
                base_degree: m.base_degree,
                relative_degree: m.relative_degree,
            })
            .or_default()
            .insert(row.candidate.elliptic_trace);
    }
    let fields = FieldCache::default();
    let mut raw = RawCache::default();
    let mut identified = 0;
    for (spec, traces) in groups {
        let remaining = limit
            .map(|l| l.saturating_sub(identified))
            .unwrap_or(usize::MAX);
        if remaining == 0 {
            break;
        }
        let wanted = traces.into_iter().take(remaining).collect();
        let began = Instant::now();
        let mut sources = crate::source::find_sources(&spec, &wanted, &fields)?;
        for source in sources.values_mut() {
            crate::verify::verify_source(source, &mut raw)?;
            source.order_independently_verified = true;
        }
        let seconds = began.elapsed().as_secs_f64();
        for source in sources.values_mut() {
            source.identification_batch_wall_seconds = Some(seconds);
        }
        let tx = c.transaction()?;
        for row in rows.iter().filter(|r| r.source.is_none()) {
            let model = &row.candidate.model;
            if (model.base_degree, model.relative_degree)
                != (spec.base_degree, spec.relative_degree)
            {
                continue;
            }
            if let Some(source) = sources.get(&row.candidate.elliptic_trace) {
                let mut value = serde_json::to_value(source)?;
                value["explicit_map_to_target_verified"] = json!(false);
                value["timing_scope"] =
                    json!("source identification and independent order checks; not DLP transfer");
                tx.execute(
                    "UPDATE candidates SET source=? WHERE spectral_model_id=?",
                    params![crate::canonical(&value)?, row.candidate.spectral_model_id],
                )?;
            }
        }
        tx.commit()?;
        identified += sources.len();
        eprintln!(
            "{}",
            json!({"event":"sources_identified","base_degree":spec.base_degree,
            "relative_degree":spec.relative_degree,"trace_classes":sources.len(),"wall_seconds":seconds})
        );
    }
    Ok(json!({"trace_classes_identified_this_run":identified,"status":journal::status(c)?}))
}
pub fn export(
    c: &Connection,
    output: &mut dyn std::io::Write,
    csv_format: bool,
    needs_review: bool,
    unseen: bool,
) -> Result<usize> {
    let tx = c.unchecked_transaction()?;
    let mut count = 0;
    let names = [
        "spectral_model_id",
        "candidate_id",
        "curve_id",
        "base_degree",
        "relative_degree",
        "genus",
        "H",
        "R",
        "A",
        "c",
        "elliptic_trace",
        "source_order",
        "point_counts",
        "field_moduli",
        "base_embeddings",
        "stage",
        "source_family_novelty_gate",
        "local_prior_evidence",
        "source",
        "job_id",
        "plan_hash",
        "engine_fingerprint",
        "explicit_map_verified",
        "subgroup_transfer_verified",
        "publication_novelty_established",
        "new_catalogue_entries",
    ];
    let mut writer = csv::Writer::from_writer(Vec::new());
    if csv_format {
        writer.write_record(names)?;
    }
    for row in journal::candidates(&tx)? {
        let record = journal::evidence_record(&tx, &row)?;
        if needs_review && record["source_family_novelty_gate"] != "unreviewed" {
            continue;
        }
        if unseen && record["local_prior_evidence"]["local_source_class_overlap"] == true {
            continue;
        }
        if csv_format {
            writer.write_record(names.iter().map(|&k| match &record[k] {
                Value::String(v) => v.clone(),
                value => crate::canonical(value).unwrap(),
            }))?;
        } else {
            writeln!(output, "{}", crate::canonical(&record)?)?;
        }
        count += 1;
    }
    if csv_format {
        output.write_all(&writer.into_inner().context("CSV flush failed")?)?;
    }
    tx.rollback()?;
    Ok(count)
}
