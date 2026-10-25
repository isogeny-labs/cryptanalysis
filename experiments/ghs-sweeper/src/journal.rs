//! Single-writer transactional checkpoints and retained-reference triage.
use crate::prior::{self, Snapshot};
use crate::search::{proper_subfield_traces, Candidate, Job, JobResult, Plan, PlannedJob};
use anyhow::{ensure, Context, Result};
use fs2::FileExt;
use rusqlite::{params, Connection, OpenFlags, OptionalExtension};
use serde::{de::DeserializeOwned, Deserialize, Serialize};
use serde_json::{json, Value};
use std::collections::BTreeSet;
use std::fs::{self, File, OpenOptions};
use std::path::{Path, PathBuf};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const SCHEMA: u32 = 1;
pub fn now() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs_f64()
}
pub struct WriterLock(File);
impl WriterLock {
    pub fn acquire(db: &Path) -> Result<Self> {
        if let Some(parent) = db.parent().filter(|p| !p.as_os_str().is_empty()) {
            fs::create_dir_all(parent)?;
        }
        let mut name = db.as_os_str().to_owned();
        name.push(".lock");
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .truncate(false)
            .open(PathBuf::from(name))?;
        FileExt::try_lock_exclusive(&file).context("another writer holds this sweep journal")?;
        Ok(Self(file))
    }
}
impl Drop for WriterLock {
    fn drop(&mut self) {
        let _ = FileExt::unlock(&self.0);
    }
}

pub fn metadata<T: DeserializeOwned>(c: &Connection, key: &str) -> Result<T> {
    let text: String = c.query_row("SELECT value FROM metadata WHERE key=?", [key], |r| {
        r.get(0)
    })?;
    Ok(serde_json::from_str(&text)?)
}
pub fn set_metadata(c: &Connection, key: &str, value: &impl Serialize) -> Result<()> {
    c.execute(
        "INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)",
        params![key, crate::canonical(value)?],
    )?;
    Ok(())
}
pub fn open(db: &Path, readonly: bool) -> Result<Connection> {
    let flags = if readonly {
        OpenFlags::SQLITE_OPEN_READ_ONLY
    } else {
        OpenFlags::SQLITE_OPEN_READ_WRITE
    };
    let c = Connection::open_with_flags(db, flags)
        .with_context(|| format!("open journal {}", db.display()))?;
    c.busy_timeout(Duration::from_secs(10))?;
    c.execute_batch("PRAGMA foreign_keys=ON;")?;
    ensure!(
        metadata::<u32>(&c, "schema")? == SCHEMA,
        "unsupported Rust journal schema"
    );
    Ok(c)
}
pub fn guard(c: &Connection) -> Result<()> {
    ensure!(metadata::<String>(c, "engine_fingerprint")? == crate::engine_fingerprint(),
        "engine differs from journal; use the original binary or create a new journal (old data remains readable)");
    Ok(())
}
pub fn initialize(
    db: &Path,
    plan: &Plan,
    jobs: &[PlannedJob],
    reference_root: &Path,
) -> Result<()> {
    let root = reference_root
        .canonicalize()
        .context("reference root must exist")?;
    let _new_file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(db)
        .context("journal already exists or cannot be created")?;
    let mut c = Connection::open(db)?;
    c.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;
        CREATE TABLE metadata (key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE jobs(job_id TEXT PRIMARY KEY,params TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('pending','running','complete','failed')),
            attempts INTEGER NOT NULL DEFAULT 0,started_at REAL,completed_at REAL,result TEXT,error TEXT);
        CREATE TABLE candidates(spectral_model_id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(job_id),
            model TEXT NOT NULL,raw_verified INTEGER NOT NULL DEFAULT 0,verification_seconds REAL,source TEXT);
        CREATE TABLE reviews(review_id TEXT PRIMARY KEY,spectral_model_id TEXT NOT NULL REFERENCES candidates(spectral_model_id),
            created_at REAL NOT NULL,record TEXT NOT NULL);")?;
    let tx = c.transaction()?;
    set_metadata(&tx, "schema", &SCHEMA)?;
    set_metadata(&tx, "created_at", &now())?;
    set_metadata(&tx, "plan", plan)?;
    set_metadata(&tx, "plan_hash", &crate::identifier(plan)?)?;
    set_metadata(&tx, "engine_fingerprint", &crate::engine_fingerprint())?;
    set_metadata(&tx, "prior_snapshot", &prior::snapshot()?)?;
    set_metadata(&tx, "reference_root", &root)?;
    for job in jobs {
        tx.execute(
            "INSERT INTO jobs(job_id,params,status) VALUES (?,?,'pending')",
            params![job.job_id, crate::canonical(&job.params)?],
        )?;
    }
    tx.commit()?;
    Ok(())
}
pub fn recover(c: &mut Connection, retry_failed: bool) -> Result<usize> {
    let tx = c.transaction()?;
    let mut count = tx.execute(
        "UPDATE jobs SET status='pending',started_at=NULL WHERE status='running'",
        [],
    )?;
    if retry_failed {
        count += tx.execute(
            "UPDATE jobs SET status='pending',error=NULL WHERE status='failed'",
            [],
        )?;
    }
    tx.commit()?;
    Ok(count)
}
pub fn claim(c: &mut Connection) -> Result<Option<(String, Job)>> {
    let tx = c.transaction()?;
    let row = tx
        .prepare("SELECT job_id,params FROM jobs WHERE status='pending' ORDER BY job_id LIMIT 1")?
        .query_map([], |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))?
        .next()
        .transpose()?;
    let result = if let Some((id, text)) = row {
        let job = serde_json::from_str(&text)?;
        tx.execute(
            "UPDATE jobs SET status='running',attempts=attempts+1,started_at=? WHERE job_id=?",
            params![now(), id],
        )?;
        Some((id, job))
    } else {
        None
    };
    tx.commit()?;
    Ok(result)
}
pub fn complete(c: &mut Connection, job_id: &str, result: &JobResult) -> Result<()> {
    complete_origin(c, job_id, result, "rust")
}
fn complete_origin(
    c: &mut Connection,
    job_id: &str,
    result: &JobResult,
    origin: &str,
) -> Result<()> {
    let tx = c.transaction()?;
    for candidate in &result.candidates {
        tx.execute(
            "INSERT INTO candidates(spectral_model_id,job_id,model) VALUES (?,?,?)",
            params![
                candidate.spectral_model_id,
                job_id,
                crate::canonical(candidate)?
            ],
        )?;
    }
    let summary = json!({"normalized_models":result.normalized_models,
        "survivors_by_extension_degree":result.survivors_by_extension_degree,
        "wall_seconds":result.wall_seconds,"candidate_count":result.candidates.len(),"execution_origin":origin});
    let changed = tx.execute("UPDATE jobs SET status='complete',result=?,error=NULL,completed_at=? WHERE job_id=? AND status='running'",
        params![crate::canonical(&summary)?, now(), job_id])?;
    ensure!(changed == 1, "only a running job can complete");
    tx.commit()?;
    Ok(())
}
pub fn fail(c: &Connection, job_id: &str, error: &str) -> Result<()> {
    c.execute(
        "UPDATE jobs SET status='failed',error=?,completed_at=? WHERE job_id=?",
        params![error, now(), job_id],
    )?;
    Ok(())
}

#[derive(Clone, Debug)]
pub struct CandidateRow {
    pub job_id: String,
    pub candidate: Candidate,
    pub raw_verified: bool,
    pub verification_seconds: Option<f64>,
    pub source: Option<Value>,
}
pub fn candidates(c: &Connection) -> Result<Vec<CandidateRow>> {
    let mut stmt = c.prepare("SELECT job_id,model,raw_verified,verification_seconds,source FROM candidates ORDER BY spectral_model_id")?;
    let rows = stmt.query_map([], |r| {
        Ok((
            r.get::<_, String>(0)?,
            r.get::<_, String>(1)?,
            r.get::<_, bool>(2)?,
            r.get::<_, Option<f64>>(3)?,
            r.get::<_, Option<String>>(4)?,
        ))
    })?;
    let mut out = Vec::new();
    for row in rows {
        let (job_id, model, raw_verified, verification_seconds, source) = row?;
        out.push(CandidateRow {
            job_id,
            candidate: serde_json::from_str(&model)?,
            raw_verified,
            verification_seconds,
            source: source.map(|s| serde_json::from_str(&s)).transpose()?,
        });
    }
    Ok(out)
}
pub fn resolve(c: &Connection, prefix: &str) -> Result<String> {
    ensure!(
        (8..=64).contains(&prefix.len())
            && prefix
                .bytes()
                .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)),
        "model ID prefix must contain 8..=64 lowercase hex characters"
    );
    let rows: Vec<String> = c
        .prepare("SELECT spectral_model_id FROM candidates WHERE spectral_model_id LIKE ?")?
        .query_map([format!("{prefix}%")], |r| r.get(0))?
        .collect::<rusqlite::Result<_>>()?;
    ensure!(rows.len() == 1, "model ID prefix is missing or ambiguous");
    Ok(rows[0].clone())
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Reference {
    pub path: String,
    pub section: String,
    pub assessment: String,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Review {
    pub scope: String,
    pub verdict: String,
    pub rationale: String,
    pub references: Vec<Reference>,
}
pub fn add_review(c: &Connection, id: &str, review: Review) -> Result<String> {
    ensure!(
        ["source_family", "map", "criterion"].contains(&review.scope.as_str()),
        "invalid review scope"
    );
    ensure!(
        ["known_overlap", "unresolved", "outside_reviewed_criteria"]
            .contains(&review.verdict.as_str()),
        "reviews cannot certify publication novelty"
    );
    ensure!(
        !review.rationale.trim().is_empty() && !review.references.is_empty(),
        "review needs rationale and retained references"
    );
    let root: PathBuf = metadata(c, "reference_root")?;
    let root = root.canonicalize()?;
    let mut stored = serde_json::to_value(&review)?;
    let mut refs = Vec::new();
    for reference in review.references {
        ensure!(
            !reference.path.trim().is_empty()
                && !reference.section.trim().is_empty()
                && !reference.assessment.trim().is_empty(),
            "reference fields must be nonempty"
        );
        let path = root.join(&reference.path).canonicalize()?;
        ensure!(
            path.starts_with(&root) && path.is_file(),
            "reference must be a retained file within the reference root"
        );
        let mut value = serde_json::to_value(reference)?;
        value["sha256"] = json!(crate::digest(fs::read(path)?));
        refs.push(value);
    }
    stored["references"] = json!(refs);
    let id_hash = crate::identifier(&json!({"spectral_model_id":id,"record":stored}))?;
    c.execute(
        "INSERT OR IGNORE INTO reviews VALUES (?,?,?,?)",
        params![id_hash, id, now(), crate::canonical(&stored)?],
    )?;
    Ok(id_hash)
}
fn references_current(root: &Path, record: &Value) -> bool {
    let Ok(root) = root.canonicalize() else {
        return false;
    };
    record["references"].as_array().is_some_and(|refs| {
        !refs.is_empty()
            && refs.iter().all(|r| {
                let Some(name) = r["path"].as_str() else {
                    return false;
                };
                let Ok(path) = root.join(name).canonicalize() else {
                    return false;
                };
                path.starts_with(&root)
                    && fs::read(path).is_ok_and(|b| r["sha256"] == crate::digest(b))
            })
    })
}
pub fn evidence_record(c: &Connection, row: &CandidateRow) -> Result<Value> {
    let result_text: String = c.query_row(
        "SELECT result FROM jobs WHERE job_id=?",
        [&row.job_id],
        |r| r.get(0),
    )?;
    let result: Value = serde_json::from_str(&result_text)?;
    let saved: Snapshot = metadata(c, "prior_snapshot")?;
    let overlap = prior::overlap(&saved, &row.candidate);
    let root: PathBuf = metadata(c, "reference_root")?;
    let mut reviews = Vec::new();
    let mut source_verdicts = Vec::new();
    for r in c.prepare("SELECT record,created_at FROM reviews WHERE spectral_model_id=? ORDER BY created_at,review_id")?
        .query_map([&row.candidate.spectral_model_id], |r| Ok((r.get::<_,String>(0)?,r.get::<_,f64>(1)?)))? {
        let (record, at) = r?; let mut v: Value = serde_json::from_str(&record)?;
        let current = references_current(&root, &v);
        if current && v["scope"] == "source_family" { source_verdicts.push(v["verdict"].as_str().unwrap().to_owned()); }
        v["retained_references_unchanged"] = json!(current); v["created_at"] = json!(at); reviews.push(v);
    }
    let gate = if source_verdicts.iter().any(|v| v == "known_overlap") {
        "known_overlap"
    } else if overlap["local_source_class_overlap"] == true {
        "local_isogeny_class_overlap"
    } else if !source_verdicts.is_empty() {
        "reviewed_priority_unresolved"
    } else {
        "unreviewed"
    };
    let mut value = serde_json::to_value(&row.candidate)?;
    let object = value.as_object_mut().unwrap();
    let d = row.candidate.model.base_degree * row.candidate.model.relative_degree;
    for (k,v) in json!({"job_id":row.job_id,"plan_hash":metadata::<String>(c,"plan_hash")?,
        "engine_fingerprint":metadata::<String>(c,"engine_fingerprint")?,
        "engine_matches_journal":metadata::<String>(c,"engine_fingerprint")? == crate::engine_fingerprint(),
        "candidate_id":null,"curve_id":null,"spectral_execution_origin":result["execution_origin"],
        "equation":"w^2+w=A*x+c+R(x)/H(x)",
        "coefficient_encoding":"ascending coefficients; binary power basis; see field_moduli and base_embeddings",
        "stage":if row.raw_verified {"independent_counts_checked"} else {"spectral_candidate"},
        "independent_point_counts_verified":row.raw_verified,"verification_wall_seconds":row.verification_seconds,
        "proper_subfield_twist_trace_excluded":!proper_subfield_traces(d).contains(&row.candidate.elliptic_trace),
        "source":row.source,"local_prior_evidence":overlap,"source_family_novelty_gate":gate,"reviews":reviews,
        "explicit_map_verified":false,"subgroup_transfer_verified":false,"planted_log_verified":false,
        "publication_novelty_established":false,"rho_is_acceptance_gate":false,"new_catalogue_entries":0})
        .as_object().unwrap() { object.insert(k.clone(),v.clone()); }
    Ok(value)
}

pub fn status(c: &Connection) -> Result<Value> {
    // The snapshot also applies to callers outside the CLI, including readers
    // observing a writer that commits while this report is being assembled.
    let tx = c.unchecked_transaction()?;
    let plan: Plan = metadata(&tx, "plan")?;
    let imported: Option<String> = tx
        .query_row(
            "SELECT value FROM metadata WHERE key='import_provenance'",
            [],
            |r| r.get(0),
        )
        .optional()?;
    let imported: Option<Value> = imported.map(|v| serde_json::from_str(&v)).transpose()?;
    let saved: Snapshot = metadata(&tx, "prior_snapshot")?;
    let mut searches = Vec::new();
    let mut failures = Vec::new();
    let mut all_complete = true;
    for spec in &plan.searches {
        let mut states = json!({"pending":0,"running":0,"complete":0,"failed":0});
        let mut models = 0_u64;
        let mut count = 0_u64;
        let mut seconds = 0.;
        let mut historical_seconds = 0.;
        let mut survival = vec![0_u64; spec.spec.relative_degree as usize];
        for r in tx
            .prepare("SELECT job_id,params,status,result,error FROM jobs ORDER BY job_id")?
            .query_map([], |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, String>(2)?,
                    r.get::<_, Option<String>>(3)?,
                    r.get::<_, Option<String>>(4)?,
                ))
            })?
        {
            let (id, text, state, result, error) = r?;
            let params: Job = serde_json::from_str(&text)?;
            if params.spec != spec.spec {
                continue;
            }
            states[&state] = json!(states[&state].as_u64().unwrap() + 1);
            if state == "failed" {
                failures.push(json!({"job_id":id,"error":error}));
            }
            if let Some(result) = result {
                let v: Value = serde_json::from_str(&result)?;
                models += v["normalized_models"]
                    .as_u64()
                    .context("missing result model count")?;
                count += v["candidate_count"]
                    .as_u64()
                    .context("missing candidate count")?;
                let wall = v["wall_seconds"].as_f64().context("missing wall time")?;
                if v["execution_origin"] == "python-prototype" {
                    historical_seconds += wall;
                } else {
                    seconds += wall;
                }
                for (out, v) in survival.iter_mut().zip(
                    v["survivors_by_extension_degree"]
                        .as_array()
                        .context("missing survival counts")?,
                ) {
                    *out += v.as_u64().context("invalid survival count")?;
                }
            }
        }
        let complete = states["complete"] == spec.denominator_representatives as u64;
        all_complete &= complete;
        let mut v = serde_json::to_value(spec)?;
        v["jobs"] = states;
        v["complete"] = json!(complete);
        v["models_examined"] = json!(models);
        v["candidates"] = json!(count);
        v["survivors_by_extension_degree"] = json!(survival);
        v["worker_wall_seconds"] = json!(seconds);
        v["historical_worker_wall_seconds"] = json!(historical_seconds);
        searches.push(v);
    }
    let rows = candidates(&tx)?;
    let overlaps: Vec<_> = rows
        .iter()
        .map(|r| prior::overlap(&saved, &r.candidate))
        .collect();
    let reviews: BTreeSet<String> = tx
        .prepare("SELECT spectral_model_id FROM reviews")?
        .query_map([], |r| r.get(0))?
        .collect::<rusqlite::Result<_>>()?;
    let value = json!({"schema_version":1,"engine":plan.engine,"scope":plan.scope,"historical_import":imported,
        "engine_matches_journal":metadata::<String>(&tx,"engine_fingerprint")? == crate::engine_fingerprint(),
        "plan_hash":metadata::<String>(&tx,"plan_hash")?,"searches":searches,"complete":all_complete,
        "total_candidates":rows.len(),"independently_checked_candidates":rows.iter().filter(|r|r.raw_verified).count(),
        "candidates_with_source_models":rows.iter().filter(|r|r.source.is_some()).count(),
        "previously_recorded_local_spectral_candidates":overlaps.iter().filter(|v| !v["previous_local_spectral_record"].is_null()).count(),
        "local_source_isogeny_or_twist_class_overlaps":overlaps.iter().filter(|v|v["local_source_class_overlap"] == true).count(),
        "candidates_with_reviews":reviews.len(),"failures":failures,"new_catalogue_entries":0,
        "publication_novelty_established":false,"rho_is_acceptance_gate":false});
    tx.rollback()?;
    Ok(value)
}

pub fn import_python(
    input: &Path,
    db: &Path,
    reference_root: &Path,
    cache: &crate::field::FieldCache,
) -> Result<Value> {
    ensure!(
        input.canonicalize()? != db.canonicalize().unwrap_or_else(|_| db.to_path_buf()),
        "import needs a new output journal"
    );
    let old = Connection::open_with_flags(input, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
    ensure!(
        metadata::<String>(&old, "schema")? == "1",
        "unsupported Python journal schema"
    );
    let old_plan: Value = metadata(&old, "plan")?;
    let config = serde_json::from_value(old_plan["config"].clone())?;
    let (plan, jobs) = crate::search::make_plan(config, cache)?;
    initialize(db, &plan, &jobs, reference_root)?;
    let mut new = open(db, false)?;
    let mut provenance = json!({"origin":"python-prototype","input_sha256":crate::digest(fs::read(input)?),
        "historical_source_hashes":metadata::<Value>(&old,"source_hashes")?,"imported_complete_jobs":0,
        "policy":"Historical coverage preserved and timed separately; raw checks, source matches and reviews must be redone in Rust. Pending/running/failed historical work becomes pending."});
    set_metadata(&new, "import_provenance", &provenance)?;
    let mut imported = 0;
    for row in old
        .prepare("SELECT job_id,params,result FROM jobs WHERE status='complete' ORDER BY job_id")?
        .query_map([], |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
            ))
        })?
    {
        let (old_id, params, result) = row?;
        let p: Job = serde_json::from_str(&params)?;
        let target = jobs
            .iter()
            .find(|j| {
                j.params.spec == p.spec && j.params.h == p.h && j.params.orbit_size == p.orbit_size
            })
            .context("Python job is outside the Rust plan")?;
        let old_summary: Value = serde_json::from_str(&result)?;
        let mut result: JobResult = serde_json::from_str(&result)?;
        ensure!(
            result.normalized_models == p.spec.models_per_job()
                && result.survivors_by_extension_degree.len() == p.spec.relative_degree as usize,
            "invalid historical coverage"
        );
        for text in old
            .prepare("SELECT model FROM candidates WHERE job_id=? ORDER BY candidate_id")?
            .query_map([&old_id], |r| r.get::<_, String>(0))?
        {
            let candidate: Candidate = serde_json::from_str(&text?)?;
            ensure!(
                candidate.spectral_model_id == crate::identifier(&candidate.model)?,
                "historical model ID mismatch"
            );
            result.candidates.push(candidate);
        }
        ensure!(
            old_summary["candidate_count"] == result.candidates.len() as u64,
            "historical candidate count mismatch"
        );
        new.execute(
            "UPDATE jobs SET status='running',attempts=1 WHERE job_id=?",
            [&target.job_id],
        )?;
        complete_origin(&mut new, &target.job_id, &result, "python-prototype")?;
        imported += 1;
        provenance["imported_complete_jobs"] = json!(imported);
        set_metadata(&new, "import_provenance", &provenance)?;
    }
    Ok(json!({"import":provenance,"status":status(&new)?}))
}
