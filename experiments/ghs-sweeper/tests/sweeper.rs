use anyhow::Result;
use ghs_sweeper::{
    field::{self, Field, FieldCache},
    journal, prior, runner, search, source, verify,
};
use rusqlite::{params, Connection};
use serde_json::{json, Value};
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;
use std::sync::{atomic::AtomicBool, Arc};
use tempfile::TempDir;

fn config(pairs: &[(u32, u32)]) -> search::Config {
    search::Config {
        schema_version: 1,
        searches: pairs
            .iter()
            .map(|&(d, n)| search::Spec {
                base_degree: d,
                relative_degree: n,
            })
            .collect(),
    }
}
fn setup() -> Result<(TempDir, Connection, Vec<search::PlannedJob>)> {
    let dir = tempfile::tempdir()?;
    let path = dir.path().join("sweep.sqlite");
    let (plan, jobs) = search::make_plan(config(&[(1, 5)]), &FieldCache::default())?;
    journal::initialize(&path, &plan, &jobs, dir.path())?;
    let c = journal::open(&path, false)?;
    Ok((dir, c, jobs))
}
fn finish_all(c: &mut Connection) -> Result<()> {
    let cache = FieldCache::default();
    while let Some((id, job)) = journal::claim(c)? {
        journal::complete(c, &id, &search::search_job(&job, &cache)?)?;
    }
    Ok(())
}
fn unseen(c: &Connection) -> Result<journal::CandidateRow> {
    Ok(journal::candidates(c)?
        .into_iter()
        .find(|r| r.candidate.elliptic_trace.abs() == 3)
        .unwrap())
}

#[test]
fn fast_fields_equal_independent_raw_fields() -> Result<()> {
    for n in 1..=8 {
        let f = Field::new(n)?;
        let raw = verify::RawField::new(n, f.modulus)?;
        assert_eq!(f.trace, raw.traces);
        for a in 1..f.size {
            assert_eq!(f.inv(a), raw.inverses[a as usize]);
            for b in 0..16.min(f.size) {
                assert_eq!(f.mul(a, b), raw.mul(a, b));
            }
        }
    }
    assert_eq!(Field::new(1)?.modulus, 3);
    assert!(verify::RawField::new(3, 0).is_err());
    Ok(())
}
#[test]
fn embeddings_preserve_subfield_products() -> Result<()> {
    for d in 1..=4 {
        let base = Field::new(d)?;
        let f = Field::new(3 * d)?;
        let embed = f.embedding(&base)?;
        for a in 0..base.size {
            for b in 0..base.size {
                assert_eq!(
                    embed[base.mul(a, b) as usize],
                    f.mul(embed[a as usize], embed[b as usize])
                );
                assert_eq!(
                    embed[(a ^ b) as usize],
                    embed[a as usize] ^ embed[b as usize]
                );
            }
        }
    }
    Ok(())
}
#[test]
fn nonfree_affine_orbits_cover_all_irreducibles() -> Result<()> {
    let f = Field::new(2)?;
    let spec = search::Spec {
        base_degree: 2,
        relative_degree: 3,
    };
    let (reps, count) = search::denominators(&spec, &f)?;
    assert_eq!(count, 20);
    assert_eq!(reps.len(), 3);
    assert_eq!(
        reps.iter().map(|(_, s)| *s).collect::<BTreeSet<_>>(),
        BTreeSet::from([4, 12])
    );
    let mut all = BTreeSet::new();
    for (h, size) in reps {
        let mut orbit = BTreeSet::new();
        for a in 1..4 {
            for b in 0..4 {
                orbit.insert(field::encode(&field::affine(&h, a, b, &f), 2));
            }
        }
        assert_eq!(orbit.len(), size);
        assert!(all.is_disjoint(&orbit));
        all.extend(orbit);
    }
    let brute: BTreeSet<_> = (0..64)
        .filter_map(|v| {
            let mut h = field::decode(v, 3, 2);
            h.push(1);
            field::irreducible(&h, &f).then_some(v | 64)
        })
        .collect();
    assert_eq!(all, brute);
    Ok(())
}
#[test]
fn walsh_matches_defining_character_sum() {
    let mut values = vec![2, -3, 1, 0, 5, 7, -2, 4];
    let expected: Vec<i64> = (0..8_u32)
        .map(|x| {
            values
                .iter()
                .enumerate()
                .map(|(j, &v)| {
                    if (x & j as u32).count_ones().is_multiple_of(2) {
                        v
                    } else {
                        -v
                    }
                })
                .sum()
        })
        .collect();
    field::walsh(&mut values);
    assert_eq!(values, expected);
}
#[test]
fn configs_and_subfields_fail_closed() -> Result<()> {
    for pairs in [
        &[(0, 5)][..],
        &[(1, 2)],
        &[(2, 11)],
        &[(1, 5), (1, 5)],
        &[(4, u32::MAX)],
        &[],
    ] {
        assert!(config(pairs).validate().is_err());
    }
    assert!(serde_json::from_value::<search::Config>(
        json!({"schema_version":1,"searches":[{"base_degree":1,"relative_degree":5}],"typo":true})
    )
    .is_err());
    let report = search::subfield_config(15)?;
    assert_eq!(
        report["config"],
        serde_json::to_value(config(&[(1, 15), (3, 5)]))?
    );
    assert_eq!(report["excluded_divisors"].as_array().unwrap().len(), 2);
    assert!(search::subfield_config(1)?["config"]["searches"]
        .as_array()
        .unwrap()
        .is_empty());
    Ok(())
}

#[test]
fn complete_saved_censuses_match_candidates_counts_and_survival() -> Result<()> {
    // These are fixed regression fixtures, not a search campaign or novelty claim.
    let cache = FieldCache::default();
    let cases: [(u32, u32, &str); 4] = [
        (1, 5, include_str!("../reference/f2-genus5.json")),
        (1, 11, include_str!("../reference/f2-genus11.json")),
        (1, 13, include_str!("../reference/f2-genus13.json")),
        (2, 5, include_str!("../reference/f4-genus5.json")),
    ];
    for (d, n, text) in cases {
        let old: Value = serde_json::from_str(text)?;
        let (plan, jobs) = search::make_plan(config(&[(d, n)]), &cache)?;
        let mut actual = BTreeSet::new();
        let mut survival = vec![0_u64; n as usize];
        let mut count = 0;
        for job in jobs {
            let result = search::search_job(&job.params, &cache)?;
            count += result.normalized_models;
            for (a, b) in survival
                .iter_mut()
                .zip(result.survivors_by_extension_degree)
            {
                *a += b;
            }
            for c in result.candidates {
                actual.insert((
                    c.h_encoding,
                    c.r_encoding,
                    c.model.a,
                    c.model.c,
                    c.elliptic_trace,
                ));
                assert_eq!(c.spectral_model_id, ghs_sweeper::identifier(&c.model)?);
            }
        }
        let expected: BTreeSet<_> = old["candidates"]
            .as_array()
            .unwrap()
            .iter()
            .map(|c| {
                if d == 1 {
                    (
                        c["H"].as_u64().unwrap() as u32,
                        c["R"].as_u64().unwrap() as u32,
                        1,
                        c["c"].as_u64().unwrap() as u32,
                        c["elliptic_trace"].as_i64().unwrap(),
                    )
                } else {
                    (
                        c["H_encoding"].as_u64().unwrap() as u32,
                        c["numerator_encoding"].as_u64().unwrap() as u32,
                        c["leading"].as_u64().unwrap() as u32,
                        c["constant"].as_u64().unwrap() as u32,
                        c["elliptic_trace"].as_i64().unwrap(),
                    )
                }
            })
            .collect();
        assert_eq!(actual, expected, "q={}, N={n}", 1 << d);
        assert_eq!(count, plan.normalized_models);
        if d == 1 {
            assert_eq!(json!(count), old["normalized_models"]);
            assert_eq!(json!(survival), old["survivors_by_extension_degree"]);
        } else {
            assert_eq!(json!(count), old["normalized_models_examined"]);
        }
    }
    Ok(())
}
#[test]
fn positives_and_elliptic_models_have_independent_counts() -> Result<()> {
    let cache = FieldCache::default();
    let (_, jobs) = search::make_plan(config(&[(3, 3)]), &cache)?;
    let result = search::search_job(&jobs[0].params, &cache)?;
    assert!(!result.candidates.is_empty());
    let mut raw = verify::RawCache::default();
    for c in result.candidates.iter().take(6) {
        assert_eq!(verify::verify_candidate(c, &mut raw)?, c.point_counts);
    }
    let traces = result.candidates.iter().map(|c| c.elliptic_trace).collect();
    let sources = source::find_sources(&jobs[0].params.spec, &traces, &cache)?;
    for s in sources.values() {
        assert_eq!(verify::verify_source(s, &mut raw)?, s.order);
    }
    let mut bad = result.candidates[0].clone();
    bad.point_counts[0] += 2;
    assert!(verify::verify_candidate(&bad, &mut raw).is_err());
    bad = result.candidates[0].clone();
    bad.model.r[0] ^= 1;
    bad.spectral_model_id = ghs_sweeper::identifier(&bad.model)?;
    assert!(verify::verify_candidate(&bad, &mut raw).is_err());
    Ok(())
}
#[test]
fn canonical_comparison_keeps_lift_condition_and_koblitz_control() -> Result<()> {
    let audit: Value =
        serde_json::from_str(include_str!("../reference/prototype-hess-audit.json"))?;
    let member = audit["classes"]
        .as_array()
        .unwrap()
        .iter()
        .flat_map(|c| c["members"].as_array().unwrap())
        .find(|m| m["canonical_GHS_Frobenius_lift_exists"] == false)
        .unwrap();
    let f = Field::new(10)?;
    let spec = search::Spec {
        base_degree: 2,
        relative_degree: 5,
    };
    let value = source::canonical_baseline(
        member["b"].as_u64().unwrap() as u32,
        member["a"].as_u64().unwrap() as u32,
        &spec,
        &f,
    )?;
    assert!(!value.canonical_frobenius_lift_exists);
    assert_eq!(
        json!(value.formal_canonical_ghs_genus),
        member["canonical_formal_compositum_genus"]
    );
    let f = Field::new(5)?;
    let control = source::canonical_baseline(
        1,
        0,
        &search::Spec {
            base_degree: 1,
            relative_degree: 5,
        },
        &f,
    )?;
    assert_eq!(control.formal_canonical_ghs_genus, 1);
    assert_eq!(control.augmented_frobenius_rank, 1);
    Ok(())
}

#[test]
fn candidate_insertion_and_checkpoint_roll_back_together() -> Result<()> {
    let (_dir, mut c, _) = setup()?;
    let (id, job) = journal::claim(&mut c)?.unwrap();
    let mut result = search::search_job(&job, &FieldCache::default())?;
    result.candidates.push(result.candidates[0].clone());
    assert!(journal::complete(&mut c, &id, &result).is_err());
    assert!(journal::candidates(&c)?.is_empty());
    assert_eq!(journal::status(&c)?["searches"][0]["jobs"]["running"], 1);
    Ok(())
}
#[test]
fn abandoned_claim_is_recovered_without_duplicate_models() -> Result<()> {
    let (dir, mut c, _) = setup()?;
    let original = journal::claim(&mut c)?.unwrap();
    drop(c);
    let mut c = journal::open(&dir.path().join("sweep.sqlite"), false)?;
    assert_eq!(journal::recover(&mut c, false)?, 1);
    let retry = journal::claim(&mut c)?.unwrap();
    assert_eq!(original.0, retry.0);
    journal::complete(
        &mut c,
        &retry.0,
        &search::search_job(&retry.1, &FieldCache::default())?,
    )?;
    finish_all(&mut c)?;
    let s = journal::status(&c)?;
    assert_eq!(s["total_candidates"], 6);
    assert_eq!(s["searches"][0]["models_examined"], 186);
    assert_eq!(s["complete"], true);
    Ok(())
}
#[test]
fn failed_jobs_require_explicit_retry() -> Result<()> {
    let (_dir, mut c, _) = setup()?;
    let (id, _) = journal::claim(&mut c)?.unwrap();
    journal::fail(&c, &id, "intentional fixture failure")?;
    assert_eq!(journal::recover(&mut c, false)?, 0);
    assert_eq!(
        journal::status(&c)?["failures"].as_array().unwrap().len(),
        1
    );
    assert_eq!(journal::recover(&mut c, true)?, 1);
    assert!(journal::status(&c)?["failures"]
        .as_array()
        .unwrap()
        .is_empty());
    Ok(())
}
#[test]
fn exclusive_writer_and_existing_file_are_protected() -> Result<()> {
    let (dir, _c, jobs) = setup()?;
    let path = dir.path().join("sweep.sqlite");
    let lock = journal::WriterLock::acquire(&path)?;
    assert!(journal::WriterLock::acquire(&path).is_err());
    drop(lock);
    assert!(journal::WriterLock::acquire(&path).is_ok());
    let (plan, _) = search::make_plan(config(&[(1, 5)]), &FieldCache::default())?;
    assert!(journal::initialize(&path, &plan, &jobs, dir.path()).is_err());
    Ok(())
}
#[test]
fn changed_engine_is_readable_but_cannot_extend_old_run() -> Result<()> {
    let (_dir, c, _) = setup()?;
    journal::set_metadata(&c, "engine_fingerprint", &"changed")?;
    assert!(journal::guard(&c).is_err());
    assert_eq!(journal::status(&c)?["engine_matches_journal"], false);
    Ok(())
}
#[test]
fn parallel_resume_limits_and_cancellation_preserve_coverage() -> Result<()> {
    let (_dir, mut c, _) = setup()?;
    let stop = Arc::new(AtomicBool::new(false));
    let first = runner::run(&mut c, 2, Some(1), None, false, Arc::clone(&stop))?;
    assert_eq!(first["completed_this_run"], 1);
    assert_eq!(first["status"]["complete"], false);
    let rest = runner::run(&mut c, 2, None, None, false, Arc::clone(&stop))?;
    assert_eq!(rest["status"]["complete"], true);
    assert_eq!(
        runner::run(&mut c, 1, None, None, false, stop)?["completed_this_run"],
        0
    );
    let (_dir, mut c, _) = setup()?;
    let cancelled = runner::run(
        &mut c,
        2,
        None,
        None,
        false,
        Arc::new(AtomicBool::new(true)),
    )?;
    assert_eq!(cancelled["completed_this_run"], 0);
    assert_eq!(cancelled["interrupted"], true);
    assert_eq!(cancelled["status"]["searches"][0]["jobs"]["pending"], 3);
    Ok(())
}
#[test]
fn worker_failures_are_retained_as_failed_jobs() -> Result<()> {
    let (_dir, mut c, jobs) = setup()?;
    for j in &jobs {
        let mut bad = j.params.clone();
        bad.h = vec![0];
        c.execute(
            "UPDATE jobs SET params=? WHERE job_id=?",
            params![ghs_sweeper::canonical(&bad)?, j.job_id],
        )?;
    }
    let result = runner::run(
        &mut c,
        2,
        None,
        None,
        false,
        Arc::new(AtomicBool::new(false)),
    )?;
    assert_eq!(result["failed_this_run"], 3);
    assert_eq!(result["status"]["complete"], false);
    Ok(())
}
#[test]
fn source_matching_and_checks_resume_monotonically() -> Result<()> {
    let (_dir, mut c, _) = setup()?;
    finish_all(&mut c)?;
    assert_eq!(
        runner::check_candidates(&mut c, Some(1))?["checked_this_run"],
        1
    );
    assert_eq!(
        runner::check_candidates(&mut c, None)?["checked_this_run"],
        5
    );
    assert_eq!(
        runner::check_candidates(&mut c, None)?["checked_this_run"],
        0
    );
    assert_eq!(
        runner::identify_sources(&mut c, Some(1))?["trace_classes_identified_this_run"],
        1
    );
    let status = runner::identify_sources(&mut c, None)?["status"].clone();
    assert_eq!(status["candidates_with_source_models"], 6);
    assert_eq!(status["independently_checked_candidates"], 6);
    Ok(())
}
#[test]
fn local_history_flags_controls_isogeny_classes_and_twists() -> Result<()> {
    let (_dir, mut c, _) = setup()?;
    finish_all(&mut c)?;
    assert_eq!(prior::snapshot()?.spectral_controls.len(), 244);
    for row in journal::candidates(&c)? {
        let v = journal::evidence_record(&c, &row)?;
        assert!(!v["local_prior_evidence"]["previous_local_spectral_record"].is_null());
        if row.candidate.elliptic_trace.abs() == 1 {
            assert_eq!(
                v["source_family_novelty_gate"],
                "local_isogeny_class_overlap"
            );
        }
        assert!(v["candidate_id"].is_null());
        assert!(v["curve_id"].is_null());
        assert_eq!(v["publication_novelty_established"], false);
        assert_eq!(v["subgroup_transfer_verified"], false);
    }
    let mut out = Vec::new();
    runner::export(&c, &mut out, false, false, true)?;
    for line in String::from_utf8(out)?.lines() {
        let v: Value = serde_json::from_str(line)?;
        assert_ne!(v["elliptic_trace"].as_i64().unwrap().abs(), 1);
    }
    Ok(())
}
fn review(path: &str, verdict: &str) -> journal::Review {
    journal::Review {
        scope: "source_family".into(),
        verdict: verdict.into(),
        rationale: "test fixture, not a literature claim".into(),
        references: vec![journal::Reference {
            path: path.into(),
            section: "1".into(),
            assessment: "test fixture".into(),
        }],
    }
}
#[test]
fn review_gates_reject_novelty_shortcuts_and_escaping_references() -> Result<()> {
    let (dir, mut c, _) = setup()?;
    finish_all(&mut c)?;
    let row = unseen(&c)?;
    fs::write(dir.path().join("ref.txt"), "retained test reference")?;
    let id = &row.candidate.spectral_model_id;
    assert_eq!(
        journal::evidence_record(&c, &row)?["source_family_novelty_gate"],
        "unreviewed"
    );
    journal::add_review(&c, id, review("ref.txt", "known_overlap"))?;
    journal::add_review(&c, id, review("ref.txt", "outside_reviewed_criteria"))?;
    assert_eq!(
        journal::evidence_record(&c, &row)?["source_family_novelty_gate"],
        "known_overlap"
    );
    assert!(journal::add_review(&c, id, review("ref.txt", "novel")).is_err());
    let outside = tempfile::NamedTempFile::new()?;
    assert!(journal::add_review(
        &c,
        id,
        review(outside.path().to_str().unwrap(), "unresolved")
    )
    .is_err());
    assert!(journal::resolve(&c, "%%%%%%%%").is_err());
    assert_eq!(journal::resolve(&c, &id[..12])?, *id);
    Ok(())
}
#[test]
fn stale_retained_reference_reopens_review_gate() -> Result<()> {
    let (dir, mut c, _) = setup()?;
    finish_all(&mut c)?;
    let row = unseen(&c)?;
    let path = dir.path().join("ref.txt");
    fs::write(&path, "original")?;
    journal::add_review(
        &c,
        &row.candidate.spectral_model_id,
        review("ref.txt", "known_overlap"),
    )?;
    fs::write(path, "changed")?;
    let v = journal::evidence_record(&c, &row)?;
    assert_eq!(v["source_family_novelty_gate"], "unreviewed");
    assert_eq!(v["reviews"][0]["retained_references_unchanged"], false);
    Ok(())
}

fn invoke(args: &[&str], cwd: &Path, success: bool) -> Result<Value> {
    let output = std::process::Command::new(env!("CARGO_BIN_EXE_ghs-sweeper"))
        .args(args)
        .env("PATH", "")
        .current_dir(cwd)
        .output()?;
    assert_eq!(
        output.status.success(),
        success,
        "stdout={} stderr={}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    if success && !output.stdout.is_empty() {
        Ok(serde_json::from_slice(&output.stdout)?)
    } else {
        Ok(Value::Null)
    }
}
#[test]
fn native_cli_runs_without_python_and_refuses_clobbers() -> Result<()> {
    let dir = tempfile::tempdir()?;
    fs::write(
        dir.path().join("config.json"),
        serde_json::to_vec(&config(&[(1, 5)]))?,
    )?;
    invoke(
        &["init", "--config", "config.json", "--db", "run.sqlite"],
        dir.path(),
        true,
    )?;
    let first = invoke(
        &[
            "run",
            "--db",
            "run.sqlite",
            "--workers",
            "2",
            "--max-jobs",
            "1",
        ],
        dir.path(),
        true,
    )?;
    assert_eq!(first["completed_this_run"], 1);
    let status = invoke(&["status", "--db", "run.sqlite"], dir.path(), true)?;
    assert_eq!(status, first["status"]);
    assert_eq!(
        invoke(
            &["run", "--db", "run.sqlite", "--workers", "2"],
            dir.path(),
            true
        )?["status"]["complete"],
        true
    );
    invoke(&["verify", "--db", "run.sqlite"], dir.path(), true)?;
    invoke(&["sources", "--db", "run.sqlite"], dir.path(), true)?;
    invoke(
        &[
            "export",
            "--db",
            "run.sqlite",
            "--format",
            "csv",
            "--output",
            "out.csv",
        ],
        dir.path(),
        true,
    )?;
    assert!(fs::metadata(dir.path().join("out.csv"))?.len() > 100);
    invoke(
        &["export", "--db", "run.sqlite", "--output", "out.csv"],
        dir.path(),
        false,
    )?;
    invoke(
        &["init", "--config", "config.json", "--db", "run.sqlite"],
        dir.path(),
        false,
    )?;
    Ok(())
}
#[test]
fn python_journal_import_preserves_coverage_but_resets_verification() -> Result<()> {
    // Construct the historical SQLite schema in Rust; Python is not a test dependency.
    let dir = tempfile::tempdir()?;
    let path = dir.path().join("python.sqlite");
    let old = Connection::open(&path)?;
    old.execute_batch("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE jobs(job_id TEXT PRIMARY KEY,params TEXT,status TEXT,result TEXT);
        CREATE TABLE candidates(candidate_id TEXT PRIMARY KEY,job_id TEXT,model TEXT,raw_verified INTEGER);")?;
    let cache = FieldCache::default();
    let (plan, jobs) = search::make_plan(config(&[(1, 5)]), &cache)?;
    journal::set_metadata(&old, "schema", &"1")?;
    journal::set_metadata(&old, "plan", &plan)?;
    journal::set_metadata(&old, "source_hashes", &json!({"prototype.py":"fixture"}))?;
    let job = &jobs[0];
    let result = search::search_job(&job.params, &cache)?;
    let summary = json!({"normalized_models":result.normalized_models,"survivors_by_extension_degree":result.survivors_by_extension_degree,
        "wall_seconds":1.5,"candidate_count":result.candidates.len()});
    old.execute(
        "INSERT INTO jobs VALUES (?,?,?,?)",
        params![
            job.job_id,
            ghs_sweeper::canonical(&job.params)?,
            "complete",
            ghs_sweeper::canonical(&summary)?
        ],
    )?;
    for candidate in result.candidates {
        let mut v = serde_json::to_value(&candidate)?;
        let id = v
            .as_object_mut()
            .unwrap()
            .remove("spectral_model_id")
            .unwrap();
        v["candidate_id"] = id;
        old.execute(
            "INSERT INTO candidates VALUES (?,?,?,1)",
            params![
                candidate.spectral_model_id,
                job.job_id,
                ghs_sweeper::canonical(&v)?
            ],
        )?;
    }
    drop(old);
    let target = dir.path().join("rust.sqlite");
    let report = journal::import_python(&path, &target, dir.path(), &cache)?;
    assert_eq!(report["import"]["imported_complete_jobs"], 1);
    assert_eq!(report["status"]["independently_checked_candidates"], 0);
    assert_eq!(
        report["status"]["searches"][0]["historical_worker_wall_seconds"],
        1.5
    );
    assert_eq!(report["status"]["searches"][0]["worker_wall_seconds"], 0.0);
    let mut c = journal::open(&target, false)?;
    finish_all(&mut c)?;
    runner::check_candidates(&mut c, None)?;
    assert_eq!(journal::status(&c)?["independently_checked_candidates"], 6);
    Ok(())
}
