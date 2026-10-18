//! Run-directory store, archive export and S3 transport for `ca-ic fbkit`
//! (`docs/ic/FBKIT_SPEC.md` sections 2 and 6).
//!
//! # Deviation from the n83 sweep layout
//!
//! The n83 sweep stores `*.jsonl.gz`. The crate has no gzip implementation and
//! no new crates may be added, so every file here is plain `.json` or `.jsonl`
//! (point lists are `points/<cell-id>.jsonl`, one `["x","y"]` pair per line).
//!
//! # Layout of the run directory
//!
//! `manifest.json`, `curve.json`, `cells/<cell-id>.json`,
//! `points/<cell-id>.jsonl`, `ranking.json`, `report.json`, `report.md`,
//! `inventory.json` and `receipts/<kind>-<utc>.json`. Receipts and
//! `inventory.json` are not themselves listed in the inventory.
//!
//! # S3 key layout
//!
//! `s3://<bucket>/<prefix>/fbkit/<curve_id>/<sweep_id>/<relative path>` for
//! every inventoried file, plus `inventory.json`, with `manifest.json`
//! uploaded last: a remote run is complete only once `manifest.json` landed.
//! Each object carries `sha256` user metadata (`aws s3 cp --metadata`).
//!
//! Transport is the `aws` CLI with an argument vector (no shell), null stdin
//! and captured stderr. Credentials and the environment are never logged.

use std::collections::BTreeSet;
use std::fs::{self, File};
use std::io::{Read, Write};
use std::path::{Component, Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};

use super::identity::{blake3_hex, canonical_json, point_set_sha256, sha256_hex, sha256_hex_bytes};
use super::CellRecord;

/// Schema tag of `inventory.json`.
pub const INVENTORY_SCHEMA: &str = "ic-fbkit-inventory/1";
/// Schema tag of receipts.
pub const RECEIPT_SCHEMA: &str = "ic-fbkit-receipt/1";
/// Schema tag of the factor-base archive document.
pub const ARCHIVE_SCHEMA: &str = "ic-factor-base-archive/1";
/// Column order of `experiments/fb-archive/index.csv`.
pub const ARCHIVE_INDEX_COLUMNS: [&str; 18] = [
    "factor_base_sha256",
    "curve_id",
    "n",
    "family",
    "l",
    "seed",
    "fb_points",
    "geometric_points",
    "effective_columns",
    "strict_points",
    "quotient_rule",
    "points_included",
    "path",
    "storage",
    "bytes",
    "file_sha256",
    "content_sha256",
    "enumerated_set_sha256",
];

const MAX_JSON_BYTES: u64 = 64 * 1024 * 1024;

fn io_err(path: &Path, e: impl std::fmt::Display) -> String {
    format!("{}: {e}", path.display())
}

/// Write bytes atomically: temp file next to the target, `sync_all`, rename.
fn write_atomic_bytes(path: &Path, data: &[u8]) -> Result<(), String> {
    let name = path
        .file_name()
        .and_then(|n| n.to_str())
        .ok_or_else(|| io_err(path, "no file name"))?;
    let tmp = path.with_file_name(format!(".{name}.tmp"));
    {
        let mut f = File::create(&tmp).map_err(|e| io_err(&tmp, e))?;
        f.write_all(data).map_err(|e| io_err(&tmp, e))?;
        f.sync_all().map_err(|e| io_err(&tmp, e))?;
    }
    fs::rename(&tmp, path).map_err(|e| io_err(path, e))
}

fn pretty(v: &Value) -> Result<Vec<u8>, String> {
    let mut b = serde_json::to_vec_pretty(v).map_err(|e| e.to_string())?;
    b.push(b'\n');
    Ok(b)
}

fn read_capped(path: &Path) -> Result<Vec<u8>, String> {
    let mut data = Vec::new();
    File::open(path)
        .map_err(|e| io_err(path, e))?
        .take(MAX_JSON_BYTES + 1)
        .read_to_end(&mut data)
        .map_err(|e| io_err(path, e))?;
    if data.len() as u64 > MAX_JSON_BYTES {
        return Err(io_err(path, "file exceeds the 64 MiB JSON cap"));
    }
    Ok(data)
}

fn read_json(path: &Path) -> Result<Value, String> {
    serde_json::from_slice(&read_capped(path)?).map_err(|e| io_err(path, e))
}

/// Compact UTC timestamp `YYYYMMDDTHHMMSSZ` of the current time.
fn utc_compact() -> String {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let (days, rem) = ((secs / 86_400) as i64, secs % 86_400);
    // Civil-from-days (Howard Hinnant).
    let z = days + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = yoe + era * 400 + i64::from(m <= 2);
    format!(
        "{y:04}{m:02}{d:02}T{:02}{:02}{:02}Z",
        rem / 3600,
        rem % 3600 / 60,
        rem % 60
    )
}

fn safe_rel_path(rel: &str) -> Result<(), String> {
    let p = Path::new(rel);
    let ok = !rel.is_empty()
        && !rel.contains('\\')
        && p.components().all(|c| matches!(c, Component::Normal(_)));
    if ok {
        Ok(())
    } else {
        Err(format!("unsafe relative path {rel:?}"))
    }
}

fn safe_id(id: &str) -> Result<(), String> {
    if !id.is_empty()
        && id
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_' || c == '.')
        && !id.starts_with('.')
    {
        Ok(())
    } else {
        Err(format!("unsafe identifier {id:?}"))
    }
}

/// One file of the run directory as listed in `inventory.json`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Entry {
    /// Path relative to the run directory, `/`-separated.
    pub path: String,
    /// File size in bytes.
    pub bytes: u64,
    /// Lowercase hex SHA-256 of the contents.
    pub sha256: String,
    /// Lowercase hex BLAKE3 of the contents.
    pub blake3: String,
}

impl Entry {
    fn of(path: String, data: &[u8]) -> Self {
        Entry {
            path,
            bytes: data.len() as u64,
            sha256: sha256_hex_bytes(data),
            blake3: blake3_hex(data),
        }
    }

    fn check(&self, data: &[u8]) -> Result<(), String> {
        if data.len() as u64 != self.bytes {
            return Err(format!(
                "byte count mismatch (expected {}, found {})",
                self.bytes,
                data.len()
            ));
        }
        if sha256_hex_bytes(data) != self.sha256 {
            return Err("sha256 mismatch".into());
        }
        if blake3_hex(data) != self.blake3 {
            return Err("blake3 mismatch".into());
        }
        Ok(())
    }
}

/// A run directory.
#[derive(Debug, Clone)]
pub struct Store {
    root: PathBuf,
}

impl Store {
    /// Create a run directory; it must not exist or must be empty.
    pub fn create(dir: &Path) -> Result<Store, String> {
        if dir.exists() {
            let mut rd = fs::read_dir(dir).map_err(|e| io_err(dir, e))?;
            if rd.next().is_some() {
                return Err(format!("{}: directory is not empty", dir.display()));
            }
        }
        fs::create_dir_all(dir).map_err(|e| io_err(dir, e))?;
        Ok(Store {
            root: dir.to_path_buf(),
        })
    }

    /// Open an existing run directory.
    pub fn open(dir: &Path) -> Result<Store, String> {
        if !dir.is_dir() {
            return Err(format!("{}: not a directory", dir.display()));
        }
        Ok(Store {
            root: dir.to_path_buf(),
        })
    }

    /// The directory path.
    pub fn root(&self) -> &Path {
        &self.root
    }

    fn put(&self, rel: &str, data: &[u8]) -> Result<PathBuf, String> {
        safe_rel_path(rel)?;
        let path = self.root.join(rel);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| io_err(parent, e))?;
        }
        write_atomic_bytes(&path, data)?;
        Ok(path)
    }

    fn put_json(&self, rel: &str, v: &Value) -> Result<PathBuf, String> {
        self.put(rel, &pretty(v)?)
    }

    /// Write `manifest.json` (should carry `sweep_id`).
    pub fn write_manifest(&self, manifest: &Value) -> Result<(), String> {
        self.put_json("manifest.json", manifest).map(|_| ())
    }

    /// Read `manifest.json`.
    pub fn read_manifest(&self) -> Result<Value, String> {
        read_json(&self.root.join("manifest.json"))
    }

    /// Write `curve.json` (should carry `curve_id`).
    pub fn write_curve(&self, curve: &Value) -> Result<(), String> {
        self.put_json("curve.json", curve).map(|_| ())
    }

    /// Read `curve.json`.
    pub fn read_curve(&self) -> Result<Value, String> {
        read_json(&self.root.join("curve.json"))
    }

    /// Write `cells/<cell_id>.json` atomically.
    pub fn write_cell(&self, cell: &CellRecord) -> Result<(), String> {
        safe_id(&cell.cell_id)?;
        let v = serde_json::to_value(cell).map_err(|e| e.to_string())?;
        self.put_json(&format!("cells/{}.json", cell.cell_id), &v)
            .map(|_| ())
    }

    /// Read every cell file, ordered by file name.
    pub fn read_cells(&self) -> Result<Vec<CellRecord>, String> {
        let dir = self.root.join("cells");
        if !dir.is_dir() {
            return Ok(Vec::new());
        }
        let mut names: Vec<PathBuf> = fs::read_dir(&dir)
            .map_err(|e| io_err(&dir, e))?
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| p.extension().is_some_and(|x| x == "json"))
            .filter(|p| {
                !p.file_name()
                    .and_then(|n| n.to_str())
                    .is_some_and(|n| n.starts_with('.'))
            })
            .collect();
        names.sort();
        names
            .iter()
            .map(|p| serde_json::from_slice(&read_capped(p)?).map_err(|e| io_err(p, e)))
            .collect()
    }

    /// The `status` of a stored cell, or `None` when absent or unreadable
    /// (so `--resume` re-runs it).
    pub fn cell_status(&self, cell_id: &str) -> Option<String> {
        safe_id(cell_id).ok()?;
        let v = read_json(&self.root.join(format!("cells/{cell_id}.json"))).ok()?;
        v.get("status")?.as_str().map(str::to_string)
    }

    /// Write `points/<cell_id>.jsonl`: sorted lowercase `["x","y"]` lines.
    pub fn write_points(&self, cell_id: &str, points: &[(String, String)]) -> Result<(), String> {
        safe_id(cell_id)?;
        let mut pts: Vec<(String, String)> = points
            .iter()
            .map(|(x, y)| (x.to_ascii_lowercase(), y.to_ascii_lowercase()))
            .collect();
        pts.sort();
        let mut out = String::new();
        for (x, y) in pts {
            out.push_str(&json!([x, y]).to_string());
            out.push('\n');
        }
        self.put(&format!("points/{cell_id}.jsonl"), out.as_bytes())
            .map(|_| ())
    }

    /// Read a point list written by [`Store::write_points`].
    pub fn read_points(&self, cell_id: &str) -> Result<Vec<(String, String)>, String> {
        safe_id(cell_id)?;
        let path = self.root.join(format!("points/{cell_id}.jsonl"));
        let text = String::from_utf8(read_capped(&path)?).map_err(|e| io_err(&path, e))?;
        text.lines()
            .filter(|l| !l.is_empty())
            .map(|l| {
                let v: Value = serde_json::from_str(l).map_err(|e| io_err(&path, e))?;
                match (
                    v.get(0).and_then(Value::as_str),
                    v.get(1).and_then(Value::as_str),
                ) {
                    (Some(x), Some(y)) => Ok((x.to_string(), y.to_string())),
                    _ => Err(io_err(&path, "line is not a [x, y] string pair")),
                }
            })
            .collect()
    }

    /// Write `ranking.json`.
    pub fn write_ranking(&self, ranking: &Value) -> Result<(), String> {
        self.put_json("ranking.json", ranking).map(|_| ())
    }

    /// Write `report.json` and `report.md`.
    pub fn write_report(&self, report: &Value, markdown: &str) -> Result<(), String> {
        self.put_json("report.json", report)?;
        self.put("report.md", markdown.as_bytes()).map(|_| ())
    }

    /// Write `receipts/<kind>-<utc compact>.json` (a numeric suffix is added
    /// when the name is taken) and return its path.
    pub fn write_receipt(&self, kind: &str, receipt: &Value) -> Result<PathBuf, String> {
        let kind = super::identity::slug(kind);
        if kind.is_empty() {
            return Err("empty receipt kind".into());
        }
        let stamp = utc_compact();
        let mut rel = format!("receipts/{kind}-{stamp}.json");
        let mut i = 1;
        while self.root.join(&rel).exists() {
            rel = format!("receipts/{kind}-{stamp}-{i}.json");
            i += 1;
        }
        self.put_json(&rel, receipt)
    }

    /// Inventory of every file except `receipts/`, `inventory.json` and
    /// leftover `.tmp` files, ordered by path (byte order).
    pub fn inventory(&self) -> Result<Vec<Entry>, String> {
        let mut out = Vec::new();
        self.walk(&self.root, "", &mut out)?;
        out.sort_by(|a, b| a.path.cmp(&b.path));
        Ok(out)
    }

    fn walk(&self, dir: &Path, rel: &str, out: &mut Vec<Entry>) -> Result<(), String> {
        for e in fs::read_dir(dir).map_err(|e| io_err(dir, e))? {
            let e = e.map_err(|e| io_err(dir, e))?;
            let name = e.file_name().to_string_lossy().into_owned();
            let child_rel = if rel.is_empty() {
                name.clone()
            } else {
                format!("{rel}/{name}")
            };
            let ft = e.file_type().map_err(|e| io_err(&e_path(dir, &name), e))?;
            if ft.is_dir() {
                if child_rel == "receipts" {
                    continue;
                }
                self.walk(&e.path(), &child_rel, out)?;
            } else if ft.is_file() {
                if child_rel == "inventory.json" || name.ends_with(".tmp") {
                    continue;
                }
                let data = fs::read(e.path()).map_err(|e| io_err(&e_path(dir, &name), e))?;
                out.push(Entry::of(child_rel, &data));
            }
        }
        Ok(())
    }

    /// Write `inventory.json` (deterministic: no timestamps) and return the
    /// entries it lists.
    pub fn write_inventory(&self) -> Result<Vec<Entry>, String> {
        let entries = self.inventory()?;
        let v = json!({"schema": INVENTORY_SCHEMA, "files": entries});
        self.put_json("inventory.json", &v)?;
        Ok(entries)
    }

    /// Read the entries listed in `inventory.json`.
    pub fn read_inventory(&self) -> Result<Vec<Entry>, String> {
        let path = self.root.join("inventory.json");
        let v = read_json(&path)?;
        let files = v
            .get("files")
            .cloned()
            .ok_or_else(|| io_err(&path, "missing `files`"))?;
        let entries: Vec<Entry> = serde_json::from_value(files).map_err(|e| io_err(&path, e))?;
        for e in &entries {
            safe_rel_path(&e.path).map_err(|m| io_err(&path, m))?;
        }
        Ok(entries)
    }

    /// Re-verify the directory against its `inventory.json`: every listed file
    /// must exist with the listed size, SHA-256 and BLAKE3, and no unlisted
    /// file may exist. Returns `(path, reason)` for each failure.
    pub fn verify_inventory(&self) -> Result<Vec<(String, String)>, String> {
        let listed = self.read_inventory()?;
        let mut failures = Vec::new();
        let mut seen = BTreeSet::new();
        for e in &listed {
            seen.insert(e.path.clone());
            match fs::read(self.root.join(&e.path)) {
                Ok(data) => {
                    if let Err(r) = e.check(&data) {
                        failures.push((e.path.clone(), r));
                    }
                }
                Err(err) => failures.push((e.path.clone(), format!("unreadable: {err}"))),
            }
        }
        for e in self.inventory()? {
            if !seen.contains(&e.path) {
                failures.push((e.path, "file not listed in inventory.json".into()));
            }
        }
        Ok(failures)
    }
}

fn e_path(dir: &Path, name: &str) -> PathBuf {
    dir.join(name)
}

// ---------------------------------------------------------------- archive export

fn ci(v: &Value, key: &str) -> Value {
    v.get(key).cloned().unwrap_or(Value::Null)
}

/// Build the `ic-factor-base-archive/1` document of one cell.
///
/// `curve` is the run's `curve.json`: an object with `field` and `curve`
/// records (and optionally `curve_id`; otherwise `cell.curve_id` is used).
/// Counts come from `cell.metrics["construction"]`
/// (`dimension`, `geometric_points`, `usable_points`, `strict_points`,
/// `quotient_rule`, `effective_columns`); unknown values are `null`. The
/// `recipe` is `{n, family, l, seed, extra}` where `n` is the field degree,
/// `l` and `seed` come from `cell.recipe` (`l` falling back to the nominal
/// dimension) and `extra` holds the remaining recipe keys.
///
/// Deviations from the Python archive: points are lowercase hex strings (not
/// integers), so `points_encoding` says so and `enumerated_set_sha256` is the
/// hex-pair digest of [`point_set_sha256`]; `point_columns` and
/// `column_representatives` are `null` (not computed by this toolkit). With no
/// `points`, `points` is `null` (unknown, never zero) unless the cell itself
/// supplied a `point_set_sha256`.
pub fn export_archive_document(
    cell: &CellRecord,
    curve: &Value,
    points: &[(String, String)],
    builder: &str,
) -> Result<Value, String> {
    let field = curve
        .get("field")
        .cloned()
        .ok_or("curve.json has no `field` record")?;
    let mut curve_rec = match curve.get("curve") {
        Some(Value::Object(o)) => o.clone(),
        _ => return Err("curve.json has no `curve` record".into()),
    };
    let cid = curve
        .get("curve_id")
        .and_then(Value::as_str)
        .unwrap_or(&cell.curve_id)
        .to_string();
    curve_rec.insert("curve_id".into(), json!(cid));
    let n = field
        .get("degree")
        .cloned()
        .ok_or("field record has no `degree`")?;

    let cons = cell
        .metrics
        .get("construction")
        .cloned()
        .unwrap_or(Value::Null);
    let have_points = !points.is_empty();
    let computed = have_points.then(|| point_set_sha256(points));
    if let (Some(c), Some(s)) = (&computed, &cell.point_set_sha256) {
        if c != s {
            return Err(format!(
                "points digest {c} does not match cell point_set_sha256 {s}"
            ));
        }
    }
    let enumerated = computed.or_else(|| cell.point_set_sha256.clone());

    let recipe = &cell.recipe;
    let mut extra = Map::new();
    if let Value::Object(o) = recipe {
        for (k, v) in o {
            if !["family", "l", "seed", "params", "basis"].contains(&k.as_str()) {
                extra.insert(k.clone(), v.clone());
            }
        }
    }
    let l = recipe
        .get("l")
        .cloned()
        .filter(|v| !v.is_null())
        .unwrap_or_else(|| ci(&cons, "dimension"));
    let factor_base = json!({
        "curve_id": cid,
        "construction": {
            "family": cell.family,
            "basis": ci(recipe, "basis"),
            "params": ci(recipe, "params"),
            "polynomial_constraint": "none",
            "shifted_bases": "none",
        },
        "subgroup_policy": "cofactor_projection",
        "enumerated_set_sha256": enumerated,
        "nominal_dimension": ci(&cons, "dimension"),
        "geometric_point_count": ci(&cons, "geometric_points"),
        "actual_usable_point_count": ci(&cons, "usable_points"),
        "strict_subgroup_point_count": ci(&cons, "strict_points"),
        "quotient_rule": ci(&cons, "quotient_rule"),
        "effective_columns": ci(&cons, "effective_columns"),
    });
    let fb_sha = sha256_hex(&factor_base)?;
    let pts = if have_points {
        let mut p: Vec<(String, String)> = points
            .iter()
            .map(|(x, y)| (x.to_ascii_lowercase(), y.to_ascii_lowercase()))
            .collect();
        p.sort();
        Value::Array(p.into_iter().map(|(x, y)| json!([x, y])).collect())
    } else {
        Value::Null
    };
    let doc = json!({
        "schema": ARCHIVE_SCHEMA,
        "field": field,
        "curve": Value::Object(curve_rec),
        "factor_base": factor_base,
        "factor_base_sha256": fb_sha,
        "points": pts,
        "points_encoding": "[x, y] lowercase hex strings without prefix, sorted",
        "point_columns": Value::Null,
        "column_representatives": Value::Null,
        "builder": builder,
        "recipe": {
            "n": n,
            "family": cell.family,
            "l": l,
            "seed": ci(recipe, "seed"),
            "extra": Value::Object(extra),
        },
    });
    canonical_json(&doc)?;
    Ok(doc)
}

fn csv_cell(v: &Value) -> String {
    match v {
        Value::Null => String::new(),
        Value::String(s) => s.clone(),
        Value::Bool(b) => (if *b { "True" } else { "False" }).into(),
        other => other.to_string(),
    }
}

/// One `index.csv` row for an archive document, in [`ARCHIVE_INDEX_COLUMNS`]
/// order. `storage` is `git`; `content_sha256` is the canonical-JSON digest of
/// the document (empty if the document contains floats).
pub fn archive_index_row(doc: &Value, path: &str, bytes: u64, file_sha256: &str) -> Vec<String> {
    let fb = doc.get("factor_base").cloned().unwrap_or(Value::Null);
    let rec = doc.get("recipe").cloned().unwrap_or(Value::Null);
    let cid = doc
        .get("curve")
        .and_then(|c| c.get("curve_id"))
        .cloned()
        .unwrap_or(Value::Null);
    let included = doc.get("points").is_some_and(|p| !p.is_null());
    vec![
        csv_cell(&ci(doc, "factor_base_sha256")),
        csv_cell(&cid),
        csv_cell(&ci(&rec, "n")),
        csv_cell(&ci(&rec, "family")),
        csv_cell(&ci(&rec, "l")),
        csv_cell(&ci(&rec, "seed")),
        csv_cell(&ci(&fb, "actual_usable_point_count")),
        csv_cell(&ci(&fb, "geometric_point_count")),
        csv_cell(&ci(&fb, "effective_columns")),
        csv_cell(&ci(&fb, "strict_subgroup_point_count")),
        csv_cell(&ci(&fb, "quotient_rule")),
        csv_cell(&json!(included)),
        path.to_string(),
        "git".to_string(),
        bytes.to_string(),
        file_sha256.to_string(),
        sha256_hex(doc).unwrap_or_default(),
        csv_cell(&ci(&fb, "enumerated_set_sha256")),
    ]
}

// ---------------------------------------------------------------- S3

/// A validated `s3://bucket/prefix` destination.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct S3Target {
    /// Bucket name.
    pub bucket: String,
    /// Key prefix without leading or trailing slash.
    pub prefix: String,
}

/// Split `s3://bucket/key` into bucket and key (key may be empty).
fn split_uri(uri: &str) -> Result<(String, String), String> {
    let rest = uri
        .strip_prefix("s3://")
        .ok_or_else(|| format!("not an s3:// URI: {uri}"))?;
    let (bucket, key) = rest.split_once('/').unwrap_or((rest, ""));
    if bucket.is_empty() {
        return Err(format!("empty bucket in {uri}"));
    }
    Ok((bucket.to_string(), key.to_string()))
}

impl S3Target {
    /// Resolve the destination from `explicit`, else `FBKIT_S3_URI`, else
    /// `IC_ARCHIVE_S3_URI`. Blank values count as unset (`Ok(None)`); a set
    /// value must match `^s3://[^/]+/.+`.
    pub fn resolve(explicit: Option<&str>) -> Result<Option<S3Target>, String> {
        let pick = explicit
            .map(str::to_string)
            .or_else(|| std::env::var("FBKIT_S3_URI").ok())
            .or_else(|| std::env::var("IC_ARCHIVE_S3_URI").ok());
        let uri = match pick.as_deref().map(str::trim) {
            None | Some("") => return Ok(None),
            Some(u) => u,
        };
        Self::parse(uri).map(Some)
    }

    /// Parse and validate one URI.
    pub fn parse(uri: &str) -> Result<S3Target, String> {
        let bad = || format!("S3 URI must look like s3://bucket/prefix, got {uri:?}");
        let (bucket, key) = split_uri(uri).map_err(|_| bad())?;
        let prefix = key.trim_matches('/');
        if key.is_empty() || prefix.is_empty() {
            return Err(bad());
        }
        Ok(S3Target {
            bucket,
            prefix: prefix.to_string(),
        })
    }

    /// `s3://bucket/prefix/fbkit/<curve_id>/<sweep_id>`.
    pub fn object_prefix(&self, curve_id: &str, sweep_id: &str) -> String {
        format!(
            "s3://{}/{}/fbkit/{curve_id}/{sweep_id}",
            self.bucket, self.prefix
        )
    }
}

/// What `head-object` reported about a remote object.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Head {
    /// `sha256` user metadata, when present.
    pub sha256: Option<String>,
    /// `ContentLength`.
    pub bytes: u64,
}

/// The `aws` command-line client (binary plus extra environment).
#[derive(Debug, Clone)]
pub struct AwsCli {
    /// Executable to run.
    pub bin: PathBuf,
    /// Extra environment variables for the child (used by tests to point the
    /// stub at a bucket directory without mutating the process environment).
    pub envs: Vec<(String, String)>,
}

impl AwsCli {
    /// Use `bin` with no extra environment.
    pub fn new(bin: impl Into<PathBuf>) -> Self {
        AwsCli {
            bin: bin.into(),
            envs: Vec::new(),
        }
    }

    /// Add one environment variable for the child.
    pub fn with_env(mut self, k: &str, v: &str) -> Self {
        self.envs.push((k.to_string(), v.to_string()));
        self
    }

    /// Binary from `FBKIT_AWS_BIN`, default `aws`.
    pub fn from_env() -> Self {
        Self::new(std::env::var("FBKIT_AWS_BIN").unwrap_or_else(|_| "aws".into()))
    }

    /// Run with an argument vector: no shell, null stdin. Err carries the exit
    /// status and captured stderr (truncated).
    fn run(&self, args: &[&str]) -> Result<Vec<u8>, String> {
        let out = Command::new(&self.bin)
            .args(args)
            .envs(self.envs.iter().map(|(k, v)| (k, v)))
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .output()
            .map_err(|e| format!("cannot run {}: {e}", self.bin.display()))?;
        if out.status.success() {
            return Ok(out.stdout);
        }
        let mut err = String::from_utf8_lossy(&out.stderr).trim().to_string();
        err.truncate(2000);
        let what = args.iter().take(2).copied().collect::<Vec<_>>().join(" ");
        Err(format!("aws {what} failed ({}): {err}", out.status))
    }

    /// Whether credentials work (`sts get-caller-identity`).
    pub fn check_credentials(&self) -> Result<(), String> {
        self.run(&["sts", "get-caller-identity", "--output", "json"])
            .map(|_| ())
    }

    /// Upload `local` to `uri` with `sha256` user metadata.
    pub fn cp(&self, local: &Path, uri: &str, sha256: &str) -> Result<(), String> {
        let l = local.to_string_lossy();
        let meta = format!("sha256={sha256}");
        self.run(&[
            "s3",
            "cp",
            &l,
            uri,
            "--only-show-errors",
            "--metadata",
            &meta,
        ])
        .map(|_| ())
    }

    /// Download `uri` to `local`.
    pub fn cp_down(&self, uri: &str, local: &Path) -> Result<(), String> {
        let l = local.to_string_lossy();
        self.run(&["s3", "cp", uri, &l, "--only-show-errors"])
            .map(|_| ())
    }

    /// `head-object`: `Ok(None)` when the key does not exist.
    pub fn head(&self, uri: &str) -> Result<Option<Head>, String> {
        let (bucket, key) = split_uri(uri)?;
        match self.run(&[
            "s3api",
            "head-object",
            "--bucket",
            &bucket,
            "--key",
            &key,
            "--output",
            "json",
        ]) {
            Ok(out) => {
                let v: Value = serde_json::from_slice(&out)
                    .map_err(|e| format!("head-object output is not JSON: {e}"))?;
                Ok(Some(Head {
                    sha256: v
                        .pointer("/Metadata/sha256")
                        .and_then(Value::as_str)
                        .map(str::to_string),
                    bytes: v.get("ContentLength").and_then(Value::as_u64).unwrap_or(0),
                }))
            }
            Err(e) if e.contains("404") || e.contains("Not Found") || e.contains("NoSuchKey") => {
                Ok(None)
            }
            Err(e) => Err(e),
        }
    }

    /// All keys under the key part of `uri_prefix` (follows continuation tokens).
    pub fn ls(&self, uri_prefix: &str) -> Result<Vec<String>, String> {
        let (bucket, prefix) = split_uri(uri_prefix)?;
        let mut keys = Vec::new();
        let mut token: Option<String> = None;
        loop {
            let mut args = vec![
                "s3api",
                "list-objects-v2",
                "--bucket",
                &bucket,
                "--prefix",
                &prefix,
                "--no-paginate",
                "--output",
                "json",
            ];
            if let Some(t) = token.as_deref() {
                args.extend(["--continuation-token", t]);
            }
            let out = self.run(&args)?;
            if out.iter().all(u8::is_ascii_whitespace) {
                break;
            }
            let v: Value = serde_json::from_slice(&out)
                .map_err(|e| format!("list-objects-v2 output is not JSON: {e}"))?;
            if let Some(items) = v.get("Contents").and_then(Value::as_array) {
                keys.extend(
                    items
                        .iter()
                        .filter_map(|i| i.get("Key").and_then(Value::as_str))
                        .map(str::to_string),
                );
            }
            match v.get("NextContinuationToken").and_then(Value::as_str) {
                Some(t) if !t.is_empty() => token = Some(t.to_string()),
                _ => break,
            }
        }
        Ok(keys)
    }
}

/// Options of [`upload`].
#[derive(Debug, Clone, Copy, Default)]
pub struct UploadOptions {
    /// Plan only: report `would_upload` for every object, no network.
    pub dry_run: bool,
    /// Fail (Err) instead of reporting `skipped` when S3 is unavailable.
    pub require: bool,
}

/// Outcome of one object in an upload.
#[derive(Debug, Clone, Serialize)]
pub struct ObjectOutcome {
    /// Path relative to the run directory.
    pub path: String,
    /// Destination URI.
    pub uri: String,
    /// Size in bytes.
    pub bytes: u64,
    /// SHA-256 of the contents.
    pub sha256: String,
    /// `uploaded` | `skipped` | `would_upload` | `failed` | `not_attempted`.
    pub outcome: String,
    /// Error text for `failed`.
    pub error: Option<String>,
}

/// Result of [`upload`] (also written as the receipt).
#[derive(Debug, Clone, Serialize)]
pub struct UploadReport {
    /// `complete` | `dry_run` | `skipped` | `failed`.
    pub status: String,
    /// Why the upload was skipped, if it was.
    pub reason: Option<String>,
    /// Destination prefix URI (`None` when skipped for lack of a target).
    pub destination: Option<String>,
    /// Per-object outcomes in upload order.
    pub objects: Vec<ObjectOutcome>,
    /// Total bytes of all planned objects.
    pub total_bytes: u64,
    /// Bytes actually transferred.
    pub uploaded_bytes: u64,
    /// Receipt path, when one was written.
    pub receipt: Option<PathBuf>,
}

impl UploadReport {
    /// Count of objects with the given outcome.
    pub fn count(&self, outcome: &str) -> usize {
        self.objects.iter().filter(|o| o.outcome == outcome).count()
    }
}

fn receipt_value(kind: &str, body: &impl Serialize) -> Result<Value, String> {
    let mut v = serde_json::to_value(body).map_err(|e| e.to_string())?;
    if let Value::Object(o) = &mut v {
        o.insert("schema".into(), json!(RECEIPT_SCHEMA));
        o.insert("kind".into(), json!(kind));
        o.insert("utc".into(), json!(utc_compact()));
    }
    Ok(v)
}

/// Upload a run directory.
///
/// Writes `inventory.json` first, then uploads every inventoried file except
/// `manifest.json` (skipping those whose remote `sha256` metadata already
/// matches), then `inventory.json`, then `manifest.json` last. A receipt is
/// written to `receipts/upload-<utc>.json`. With no `target` the status is
/// `skipped` (or Err when `opts.require`); likewise when credentials are
/// unusable. A failed transfer writes the receipt and returns Err without
/// touching `manifest.json`.
pub fn upload(
    store: &Store,
    target: Option<&S3Target>,
    aws: &AwsCli,
    opts: UploadOptions,
) -> Result<UploadReport, String> {
    let skip = |store: &Store, reason: String| -> Result<UploadReport, String> {
        if opts.require {
            return Err(reason);
        }
        let mut rep = UploadReport {
            status: "skipped".into(),
            reason: Some(reason),
            destination: None,
            objects: Vec::new(),
            total_bytes: 0,
            uploaded_bytes: 0,
            receipt: None,
        };
        rep.receipt = Some(store.write_receipt("upload", &receipt_value("upload", &rep)?)?);
        Ok(rep)
    };
    let Some(target) = target else {
        return skip(
            store,
            "no S3 destination (--s3, FBKIT_S3_URI or IC_ARCHIVE_S3_URI)".into(),
        );
    };
    let curve_id = store
        .read_curve()?
        .get("curve_id")
        .and_then(Value::as_str)
        .map(str::to_string)
        .ok_or("curve.json has no curve_id")?;
    let sweep_id = store
        .read_manifest()?
        .get("sweep_id")
        .and_then(Value::as_str)
        .map(str::to_string)
        .ok_or("manifest.json has no sweep_id")?;
    safe_id(&curve_id)?;
    safe_id(&sweep_id)?;
    let dest = target.object_prefix(&curve_id, &sweep_id);

    let mut entries = store.write_inventory()?;
    let manifest_entry = entries
        .iter()
        .position(|e| e.path == "manifest.json")
        .map(|i| entries.remove(i))
        .ok_or("manifest.json is missing")?;
    let inv_bytes = fs::read(store.root.join("inventory.json"))
        .map_err(|e| io_err(&store.root.join("inventory.json"), e))?;
    entries.push(Entry::of("inventory.json".into(), &inv_bytes));
    entries.push(manifest_entry);

    let mut rep = UploadReport {
        status: String::new(),
        reason: None,
        destination: Some(dest.clone()),
        objects: entries
            .iter()
            .map(|e| ObjectOutcome {
                path: e.path.clone(),
                uri: format!("{dest}/{}", e.path),
                bytes: e.bytes,
                sha256: e.sha256.clone(),
                outcome: if opts.dry_run {
                    "would_upload"
                } else {
                    "not_attempted"
                }
                .into(),
                error: None,
            })
            .collect(),
        total_bytes: entries.iter().map(|e| e.bytes).sum(),
        uploaded_bytes: 0,
        receipt: None,
    };
    if opts.dry_run {
        rep.status = "dry_run".into();
        rep.receipt = Some(store.write_receipt("upload", &receipt_value("upload", &rep)?)?);
        return Ok(rep);
    }
    if let Err(e) = aws.check_credentials() {
        return skip(store, format!("S3 unavailable: {e}"));
    }
    let mut failure: Option<String> = None;
    for (i, e) in entries.iter().enumerate() {
        let uri = rep.objects[i].uri.clone();
        let step = (|| -> Result<bool, String> {
            if let Some(h) = aws.head(&uri)? {
                if h.sha256.as_deref() == Some(e.sha256.as_str()) && h.bytes == e.bytes {
                    return Ok(false);
                }
            }
            aws.cp(&store.root.join(&e.path), &uri, &e.sha256)?;
            Ok(true)
        })();
        match step {
            Ok(true) => {
                rep.objects[i].outcome = "uploaded".into();
                rep.uploaded_bytes += e.bytes;
            }
            Ok(false) => rep.objects[i].outcome = "skipped".into(),
            Err(err) => {
                rep.objects[i].outcome = "failed".into();
                rep.objects[i].error = Some(err.clone());
                failure = Some(format!("{}: {err}", e.path));
                break;
            }
        }
    }
    rep.status = if failure.is_some() {
        "failed"
    } else {
        "complete"
    }
    .into();
    let receipt = store.write_receipt("upload", &receipt_value("upload", &rep)?)?;
    rep.receipt = Some(receipt.clone());
    match failure {
        Some(f) => Err(format!(
            "upload failed at {f} (receipt {})",
            receipt.display()
        )),
        None => Ok(rep),
    }
}

/// Options of [`download`].
#[derive(Debug, Clone, Copy, Default)]
pub struct DownloadOptions {
    /// Only re-verify an existing directory against its `inventory.json`
    /// (no network, no writes besides the receipt).
    pub verify_only: bool,
}

/// Result of [`download`].
#[derive(Debug, Clone, Serialize)]
pub struct DownloadReport {
    /// `complete` | `verified` | `failed`.
    pub status: String,
    /// Source prefix URI (`None` for `verify_only`).
    pub source: Option<String>,
    /// Number of inventoried files.
    pub files: usize,
    /// Number that passed size, SHA-256 and BLAKE3 checks.
    pub verified: usize,
    /// Bytes of verified files.
    pub bytes: u64,
    /// `(path, reason)` for each failure.
    pub failures: Vec<(String, String)>,
    /// Remote keys under the prefix that the inventory does not list.
    pub extra_remote: Vec<String>,
    /// Receipt path.
    pub receipt: Option<PathBuf>,
}

fn finish_download(
    store: &Store,
    mut rep: DownloadReport,
    kind: &str,
) -> Result<DownloadReport, String> {
    rep.status = if rep.failures.is_empty() {
        if kind == "verify" {
            "verified"
        } else {
            "complete"
        }
    } else {
        "failed"
    }
    .into();
    let receipt = store.write_receipt(
        if kind == "verify" {
            "verify"
        } else {
            "download"
        },
        &receipt_value(kind, &rep)?,
    )?;
    rep.receipt = Some(receipt.clone());
    if rep.failures.is_empty() {
        Ok(rep)
    } else {
        let paths: Vec<String> = rep
            .failures
            .iter()
            .map(|(p, r)| format!("{p} ({r})"))
            .collect();
        Err(format!(
            "verification failed for {} (receipt {})",
            paths.join(", "),
            receipt.display()
        ))
    }
}

/// Download a run directory from `uri_prefix`
/// (`s3://bucket/prefix/fbkit/<curve_id>/<sweep_id>`) into `dir`, which must
/// be new or empty.
///
/// Fetches `inventory.json` and `manifest.json` first, then each listed file,
/// verifying size, SHA-256 and BLAKE3 of every file. Any mismatch yields an
/// Err naming the path; the partial directory is left in place and a receipt
/// listing the failures is written. With `verify_only` the existing `dir` is
/// checked against its own `inventory.json` and `aws` is not invoked.
pub fn download(
    uri_prefix: &str,
    dir: &Path,
    aws: &AwsCli,
    opts: DownloadOptions,
) -> Result<DownloadReport, String> {
    let mut rep = DownloadReport {
        status: String::new(),
        source: None,
        files: 0,
        verified: 0,
        bytes: 0,
        failures: Vec::new(),
        extra_remote: Vec::new(),
        receipt: None,
    };
    if opts.verify_only {
        let store = Store::open(dir)?;
        let listed = store.read_inventory()?;
        rep.files = listed.len();
        rep.failures = store.verify_inventory()?;
        let bad: BTreeSet<&str> = rep.failures.iter().map(|(p, _)| p.as_str()).collect();
        let good: Vec<&Entry> = listed
            .iter()
            .filter(|e| !bad.contains(e.path.as_str()))
            .collect();
        rep.verified = good.len();
        rep.bytes = good.iter().map(|e| e.bytes).sum();
        return finish_download(&store, rep, "verify");
    }
    let (bucket, key) = split_uri(uri_prefix)?;
    let key = key.trim_end_matches('/');
    if key.is_empty() {
        return Err(format!(
            "download needs a full run prefix, got {uri_prefix:?}"
        ));
    }
    let base = format!("s3://{bucket}/{key}");
    let store = Store::create(dir)?;
    rep.source = Some(base.clone());
    let inv_path = dir.join("inventory.json");
    aws.cp_down(&format!("{base}/inventory.json"), &inv_path)?;
    let listed = store.read_inventory()?;
    rep.files = listed.len();
    let manifest_ok = aws
        .cp_down(&format!("{base}/manifest.json"), &dir.join("manifest.json"))
        .map_err(|e| rep.failures.push(("manifest.json".into(), e)))
        .is_ok();
    for e in &listed {
        let local = dir.join(&e.path);
        if !(e.path == "manifest.json" && manifest_ok) {
            if let Some(parent) = local.parent() {
                fs::create_dir_all(parent).map_err(|er| io_err(parent, er))?;
            }
            if let Err(er) = aws.cp_down(&format!("{base}/{}", e.path), &local) {
                rep.failures.push((e.path.clone(), er));
                continue;
            }
        }
        match fs::read(&local) {
            Ok(data) => match e.check(&data) {
                Ok(()) => {
                    rep.verified += 1;
                    rep.bytes += e.bytes;
                }
                Err(r) => rep.failures.push((e.path.clone(), r)),
            },
            Err(er) => rep
                .failures
                .push((e.path.clone(), format!("unreadable: {er}"))),
        }
    }
    if !listed.iter().any(|e| e.path == "manifest.json") && rep.failures.is_empty() {
        rep.failures.push((
            "manifest.json".into(),
            "not listed in inventory.json".into(),
        ));
    }
    match aws.ls(&format!("s3://{bucket}/{key}/")) {
        Ok(keys) => {
            let known: BTreeSet<String> = listed
                .iter()
                .map(|e| format!("{key}/{}", e.path))
                .chain([format!("{key}/inventory.json")])
                .collect();
            rep.extra_remote = keys.into_iter().filter(|k| !known.contains(k)).collect();
        }
        Err(e) => rep.failures.push(("<listing>".into(), e)),
    }
    finish_download(&store, rep, "download")
}
