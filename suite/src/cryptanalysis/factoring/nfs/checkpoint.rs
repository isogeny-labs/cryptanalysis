//! Atomic, input-bound snapshots of completed NFS sieve batches.

use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;

use serde::{Deserialize, Serialize};

use super::sieve::Relation;

const MAGIC: &str = "NFSCKPT1 ";

#[derive(Serialize)]
pub(super) struct Snapshot<'a> {
    pub fingerprint: &'a str,
    pub next_b: u64,
    pub next_seg_lo: i64,
    pub lines_sieved: u64,
    pub cells_sieved: u64,
    pub candidates: u64,
    pub sieve_seconds: f64,
    pub next_check: usize,
    pub sieve_complete: bool,
    pub relations: &'a [Relation],
}

#[derive(Deserialize)]
pub(super) struct Loaded {
    pub fingerprint: String,
    pub next_b: u64,
    pub next_seg_lo: i64,
    pub lines_sieved: u64,
    pub cells_sieved: u64,
    pub candidates: u64,
    pub sieve_seconds: f64,
    pub next_check: usize,
    pub sieve_complete: bool,
    pub relations: Vec<Relation>,
}

pub(super) fn save(path: &Path, state: &Snapshot<'_>) -> Result<(), String> {
    let payload =
        serde_json::to_vec(state).map_err(|e| format!("serializing NFS checkpoint: {e}"))?;
    let checksum = blake3::hash(&payload).to_hex();
    let temporary = path.with_extension("ckpt.tmp");
    if temporary.exists() || temporary.is_symlink() {
        fs::remove_file(&temporary)
            .map_err(|e| format!("removing stale {}: {e}", temporary.display()))?;
    }
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&temporary)
        .map_err(|e| format!("creating {}: {e}", temporary.display()))?;
    file.write_all(format!("{MAGIC}{checksum}\n").as_bytes())
        .and_then(|_| file.write_all(&payload))
        .and_then(|_| file.sync_all())
        .map_err(|e| format!("writing {}: {e}", temporary.display()))?;
    fs::rename(&temporary, path).map_err(|e| format!("publishing {}: {e}", path.display()))?;
    Ok(())
}

pub(super) fn load(path: &Path, fingerprint: &str) -> Result<Loaded, String> {
    let bytes = fs::read(path).map_err(|e| format!("reading {}: {e}", path.display()))?;
    let newline = bytes
        .iter()
        .position(|&b| b == b'\n')
        .ok_or_else(|| format!("{}: missing NFS checkpoint header", path.display()))?;
    let (header, body) = bytes.split_at(newline);
    let payload = &body[1..];
    let expected = std::str::from_utf8(header)
        .ok()
        .and_then(|s| s.strip_prefix(MAGIC))
        .ok_or_else(|| format!("{}: invalid NFS checkpoint version", path.display()))?;
    if expected != blake3::hash(payload).to_hex().as_str() {
        return Err(format!(
            "{}: NFS checkpoint checksum mismatch",
            path.display()
        ));
    }
    let state: Loaded = serde_json::from_slice(payload)
        .map_err(|e| format!("{}: invalid NFS checkpoint: {e}", path.display()))?;
    if state.fingerprint != fingerprint {
        return Err(format!(
            "{}: NFS checkpoint parameters differ",
            path.display()
        ));
    }
    Ok(state)
}
