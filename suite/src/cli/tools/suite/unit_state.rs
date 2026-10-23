//! Sequential work-unit checkpoints with local and S3 custody.

use serde::{Deserialize, Serialize};
use std::fs::{self, File, OpenOptions};
use std::io::Read;
#[cfg(unix)]
use std::os::fd::AsRawFd;
use std::path::{Path, PathBuf};
use std::process::Command;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct Head {
    schema: u32,
    kind: String,
    input_digest: String,
    units: Vec<String>,
    result_blake3: Option<String>,
}

pub(super) struct UnitState {
    dir: PathBuf,
    uri: Option<String>,
    head: Head,
    _lock: File,
}

fn hash(path: &Path) -> Result<String, String> {
    let mut file = File::open(path).map_err(|e| format!("{}: {e}", path.display()))?;
    let mut hasher = blake3::Hasher::new();
    let mut buf = [0u8; 65536];
    loop {
        let n = file.read(&mut buf).map_err(|e| e.to_string())?;
        if n == 0 {
            break;
        }
        hasher.update(&buf[..n]);
    }
    Ok(hasher.finalize().to_hex().to_string())
}

fn aws(args: &[&str]) -> Result<Vec<u8>, String> {
    let out = Command::new("aws")
        .args(args)
        .output()
        .map_err(|e| format!("starting AWS CLI: {e}"))?;
    if !out.status.success() {
        return Err(format!(
            "aws {}: {}",
            args.join(" "),
            String::from_utf8_lossy(&out.stderr).trim()
        ));
    }
    Ok(out.stdout)
}

fn atomic(path: &Path, bytes: &[u8]) -> Result<(), String> {
    let temp = path.with_extension("tmp");
    fs::write(&temp, bytes).map_err(|e| e.to_string())?;
    File::open(&temp)
        .map_err(|e| e.to_string())?
        .sync_all()
        .map_err(|e| e.to_string())?;
    fs::rename(&temp, path).map_err(|e| e.to_string())
}

fn marker(dir: &Path) -> PathBuf {
    dir.join(".unit-head.json")
}
fn head_uri(uri: &str) -> String {
    format!("{uri}/_unit_head.json")
}
fn unit_name(idx: usize) -> String {
    format!("units/{idx:08}.json")
}

fn read_head(bytes: &[u8], kind: &str, identity: &str) -> Result<Head, String> {
    let head: Head =
        serde_json::from_slice(bytes).map_err(|e| format!("invalid unit head: {e}"))?;
    if head.schema != 1
        || head.kind != kind
        || head.input_digest != identity
        || head.units.iter().any(|h| h.len() != 64)
    {
        return Err("checkpoint belongs to different inputs or source".into());
    }
    Ok(head)
}

fn remote_head(uri: &str, kind: &str, identity: &str) -> Result<Head, String> {
    read_head(
        &aws(&["s3", "cp", &head_uri(uri), "-", "--only-show-errors"])?,
        kind,
        identity,
    )
}

fn publish_head(dir: &Path, uri: &str, head: &Head) -> Result<(), String> {
    let path = dir.join(".unit-head-upload.json");
    atomic(&path, &serde_json::to_vec(head).map_err(|e| e.to_string())?)?;
    aws(&[
        "s3",
        "cp",
        path.to_str().ok_or("state path must be UTF-8")?,
        &head_uri(uri),
        "--only-show-errors",
    ])?;
    fs::remove_file(path).map_err(|e| e.to_string())
}

fn save_head(dir: &Path, head: &Head) -> Result<(), String> {
    atomic(
        &marker(dir),
        &serde_json::to_vec_pretty(head).map_err(|e| e.to_string())?,
    )
}

impl UnitState {
    pub(super) fn prepare(
        dir: &Path,
        uri: Option<&str>,
        kind: &str,
        identity: &str,
        resume: bool,
    ) -> Result<Self, String> {
        let parsed = if let Some(uri) = uri {
            let Some((bucket, prefix)) = uri.strip_prefix("s3://").and_then(|s| s.split_once('/'))
            else {
                return Err("--s3-uri must be s3://BUCKET/PREFIX".into());
            };
            if bucket.is_empty() || prefix.trim_matches('/').is_empty() || uri.ends_with('/') {
                return Err(
                    "--s3-uri must name a bucket and nonempty prefix without a trailing slash"
                        .into(),
                );
            }
            Some((uri.to_string(), bucket.to_string(), prefix.to_string()))
        } else {
            None
        };
        fs::create_dir_all(dir.join("units")).map_err(|e| e.to_string())?;
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(dir.join(".unit.lock"))
            .map_err(|e| e.to_string())?;
        #[cfg(unix)]
        if unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
            return Err(format!("{} is already in use", dir.display()));
        }
        #[cfg(not(unix))]
        return Err("state locking is unavailable on this platform".into());
        let head = if resume {
            if marker(dir).is_file() {
                let local = read_head(
                    &fs::read(marker(dir)).map_err(|e| e.to_string())?,
                    kind,
                    identity,
                )?;
                if let Some((uri, _, _)) = &parsed {
                    if remote_head(uri, kind, identity)? != local {
                        return Err("S3 state is ahead of or differs from local state; restore into a fresh directory".into());
                    }
                }
                local
            } else {
                if fs::read_dir(dir.join("units"))
                    .map_err(|e| e.to_string())?
                    .next()
                    .is_some()
                    || dir.join("result.json").exists()
                {
                    return Err("cannot restore state into a nonempty directory".into());
                }
                let (uri, _, _) = parsed.as_ref().ok_or("no local state to resume")?;
                let head = remote_head(uri, kind, identity)?;
                eprintln!(
                    "[{kind}] restoring {} completed units from S3",
                    head.units.len()
                );
                for (idx, expected) in head.units.iter().enumerate() {
                    let name = unit_name(idx);
                    let path = dir.join(&name);
                    aws(&[
                        "s3",
                        "cp",
                        &format!("{uri}/{name}"),
                        path.to_str().ok_or("state path must be UTF-8")?,
                        "--only-show-errors",
                    ])?;
                    if hash(&path)? != *expected {
                        return Err(format!("S3 artifact {name} failed checksum validation"));
                    }
                    eprintln!("[{kind}] restored unit {}/{}", idx + 1, head.units.len());
                }
                if let Some(expected) = &head.result_blake3 {
                    let path = dir.join("result.json");
                    aws(&[
                        "s3",
                        "cp",
                        &format!("{uri}/result.json"),
                        path.to_str().ok_or("state path must be UTF-8")?,
                        "--only-show-errors",
                    ])?;
                    if hash(&path)? != *expected {
                        return Err("S3 result failed checksum validation".into());
                    }
                }
                save_head(dir, &head)?;
                head
            }
        } else {
            if marker(dir).exists()
                || dir.join("result.json").exists()
                || fs::read_dir(dir.join("units"))
                    .map_err(|e| e.to_string())?
                    .next()
                    .is_some()
            {
                return Err(
                    "state directory is not empty; use --resume or a fresh directory".into(),
                );
            }
            if let Some((_, bucket, prefix)) = &parsed {
                let listing = aws(&[
                    "s3api",
                    "list-objects-v2",
                    "--bucket",
                    bucket,
                    "--prefix",
                    &format!("{prefix}/"),
                    "--max-items",
                    "1",
                    "--query",
                    "Contents[].Key",
                    "--output",
                    "json",
                ])?;
                let keys: Option<Vec<String>> = serde_json::from_slice(&listing)
                    .map_err(|e| format!("invalid S3 prefix listing: {e}"))?;
                if keys.is_some_and(|keys| !keys.is_empty()) {
                    return Err("S3 prefix is not empty; use a new prefix".into());
                }
            }
            let head = Head {
                schema: 1,
                kind: kind.into(),
                input_digest: identity.into(),
                units: Vec::new(),
                result_blake3: None,
            };
            if let Some((uri, _, _)) = &parsed {
                publish_head(dir, uri, &head)?;
            }
            save_head(dir, &head)?;
            head
        };
        let state = UnitState {
            dir: dir.into(),
            uri: parsed.map(|v| v.0),
            head,
            _lock: lock,
        };
        state.verify_local()?;
        Ok(state)
    }

    fn verify_local(&self) -> Result<(), String> {
        for (idx, expected) in self.head.units.iter().enumerate() {
            let name = unit_name(idx);
            if hash(&self.dir.join(&name))? != *expected {
                return Err(format!("local artifact {name} failed checksum validation"));
            }
        }
        if let Some(expected) = &self.head.result_blake3 {
            if hash(&self.dir.join("result.json"))? != *expected {
                return Err("local result failed checksum validation".into());
            }
        }
        Ok(())
    }

    pub(super) fn completed(&self) -> Result<Vec<Vec<u8>>, String> {
        self.head
            .units
            .iter()
            .enumerate()
            .map(|(idx, _)| fs::read(self.dir.join(unit_name(idx))).map_err(|e| e.to_string()))
            .collect()
    }

    pub(super) fn commit(&mut self, idx: usize, bytes: &[u8]) -> Result<(), String> {
        if idx != self.head.units.len() {
            return Err("unit checkpoint is out of order".into());
        }
        if let Some(uri) = &self.uri {
            if remote_head(uri, &self.head.kind, &self.head.input_digest)? != self.head {
                return Err("S3 state changed since the last upload".into());
            }
        }
        let name = unit_name(idx);
        let path = self.dir.join(&name);
        atomic(&path, bytes)?;
        let mut next = self.head.clone();
        next.units.push(hash(&path)?);
        if let Some(uri) = &self.uri {
            eprintln!("[{}] uploading completed unit {}", self.head.kind, idx + 1);
            aws(&[
                "s3",
                "cp",
                path.to_str().ok_or("state path must be UTF-8")?,
                &format!("{uri}/{name}"),
                "--only-show-errors",
            ])?;
            publish_head(&self.dir, uri, &next)?;
        }
        save_head(&self.dir, &next)?;
        self.head = next;
        Ok(())
    }

    pub(super) fn finish(&mut self, bytes: &[u8]) -> Result<(), String> {
        if let Some(expected) = &self.head.result_blake3 {
            if blake3::hash(bytes).to_hex().to_string() != *expected {
                return Err("saved result differs from its checkpoint".into());
            }
            return Ok(());
        }
        let path = self.dir.join("result.json");
        atomic(&path, bytes)?;
        let mut next = self.head.clone();
        next.result_blake3 = Some(hash(&path)?);
        if let Some(uri) = &self.uri {
            if remote_head(uri, &self.head.kind, &self.head.input_digest)? != self.head {
                return Err("S3 state changed since the last upload".into());
            }
            eprintln!("[{}] uploading final report", self.head.kind);
            aws(&[
                "s3",
                "cp",
                path.to_str().ok_or("state path must be UTF-8")?,
                &format!("{uri}/result.json"),
                "--only-show-errors",
            ])?;
            publish_head(&self.dir, uri, &next)?;
        }
        save_head(&self.dir, &next)?;
        self.head = next;
        Ok(())
    }
}
