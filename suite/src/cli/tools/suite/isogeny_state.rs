//! Completed-curve custody for the isogeny experiment CLI.

use crate::isogeny::experiment::{ExperimentConfig, ExperimentReport, PerCurveResult};
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
    input_digest: String,
    curves: Vec<String>,
    result_blake3: Option<String>,
}

pub(super) struct State {
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
    dir.join(".isogeny-experiment-head.json")
}
fn remote_head_uri(uri: &str) -> String {
    format!("{uri}/_experiment_head.json")
}
fn curve_name(idx: usize) -> String {
    format!("curves/{idx:08}.json")
}

fn read_head(bytes: &[u8], identity: &str) -> Result<Head, String> {
    let head: Head =
        serde_json::from_slice(bytes).map_err(|e| format!("invalid isogeny head: {e}"))?;
    if head.schema != 1
        || head.input_digest != identity
        || head.curves.iter().any(|h| h.len() != 64)
    {
        return Err("isogeny state belongs to different inputs or source".into());
    }
    Ok(head)
}

fn remote_head(uri: &str, identity: &str) -> Result<Head, String> {
    read_head(
        &aws(&["s3", "cp", &remote_head_uri(uri), "-", "--only-show-errors"])?,
        identity,
    )
}

fn write_head_local(dir: &Path, head: &Head) -> Result<(), String> {
    atomic(
        &marker(dir),
        &serde_json::to_vec_pretty(head).map_err(|e| e.to_string())?,
    )
}

fn write_head_remote(dir: &Path, uri: &str, head: &Head) -> Result<(), String> {
    let path = dir.join(".isogeny-head-upload.json");
    atomic(&path, &serde_json::to_vec(head).map_err(|e| e.to_string())?)?;
    aws(&[
        "s3",
        "cp",
        path.to_str().ok_or("state path must be UTF-8")?,
        &remote_head_uri(uri),
        "--only-show-errors",
    ])?;
    fs::remove_file(path).map_err(|e| e.to_string())
}

fn input_digest(cfg: &ExperimentConfig) -> Result<String, String> {
    let mut hash = blake3::Hasher::new();
    hash.update(b"crax-isogeny-experiment-v1\0");
    hash.update(&serde_json::to_vec(cfg).map_err(|e| e.to_string())?);
    hash.update(env!("CARGO_PKG_VERSION").as_bytes());
    for source in [
        include_str!("../../../isogeny/experiment.rs"),
        include_str!("../../../isogeny/attack.rs"),
        include_str!("../../../isogeny/cm.rs"),
        include_str!("../../../isogeny/graph.rs"),
    ] {
        hash.update(source.as_bytes());
    }
    Ok(hash.finalize().to_hex().to_string())
}

impl State {
    pub(super) fn prepare(
        dir: &Path,
        uri: Option<&str>,
        cfg: &ExperimentConfig,
        resume: bool,
    ) -> Result<Self, String> {
        let identity = input_digest(cfg)?;
        let parsed_uri = if let Some(uri) = uri {
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
        fs::create_dir_all(dir.join("curves")).map_err(|e| e.to_string())?;
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(dir.join(".isogeny-experiment.lock"))
            .map_err(|e| e.to_string())?;
        #[cfg(unix)]
        if unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
            return Err(format!("{} is already in use", dir.display()));
        }
        #[cfg(not(unix))]
        return Err("isogeny state locking is unavailable on this platform".into());
        let head = if resume {
            if marker(dir).is_file() {
                let local = read_head(
                    &fs::read(marker(dir)).map_err(|e| e.to_string())?,
                    &identity,
                )?;
                if let Some((uri, _, _)) = &parsed_uri {
                    if remote_head(uri, &identity)? != local {
                        return Err("S3 isogeny state is ahead of or differs from local state; restore into a fresh directory".into());
                    }
                }
                local
            } else {
                if fs::read_dir(dir.join("curves"))
                    .map_err(|e| e.to_string())?
                    .next()
                    .is_some()
                    || dir.join("result.json").exists()
                {
                    return Err("cannot restore isogeny state into a nonempty directory".into());
                }
                let (uri, _, _) = parsed_uri
                    .as_ref()
                    .ok_or("no local isogeny state to resume")?;
                let head = remote_head(uri, &identity)?;
                eprintln!(
                    "[isogeny experiment] restoring {} completed curves from S3",
                    head.curves.len()
                );
                for (idx, expected) in head.curves.iter().enumerate() {
                    let name = curve_name(idx);
                    let path = dir.join(&name);
                    aws(&[
                        "s3",
                        "cp",
                        &format!("{uri}/{name}"),
                        path.to_str().ok_or("state path must be UTF-8")?,
                        "--only-show-errors",
                    ])?;
                    if hash(&path)? != *expected {
                        return Err(format!(
                            "isogeny S3 artifact {name} failed checksum validation"
                        ));
                    }
                    eprintln!(
                        "[isogeny experiment] restored curve {}/{}",
                        idx + 1,
                        head.curves.len()
                    );
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
                        return Err("isogeny S3 result failed checksum validation".into());
                    }
                }
                write_head_local(dir, &head)?;
                head
            }
        } else {
            if marker(dir).exists()
                || dir.join("result.json").exists()
                || fs::read_dir(dir.join("curves"))
                    .map_err(|e| e.to_string())?
                    .next()
                    .is_some()
            {
                return Err(
                    "isogeny state directory is not empty; use --resume or a fresh directory"
                        .into(),
                );
            }
            if let Some((_, bucket, prefix)) = &parsed_uri {
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
                    return Err("isogeny S3 prefix is not empty; use a new prefix".into());
                }
            }
            let head = Head {
                schema: 1,
                input_digest: identity,
                curves: Vec::new(),
                result_blake3: None,
            };
            if let Some((uri, _, _)) = &parsed_uri {
                write_head_remote(dir, uri, &head)?;
            }
            write_head_local(dir, &head)?;
            head
        };
        let state = State {
            dir: dir.into(),
            uri: parsed_uri.map(|v| v.0),
            head,
            _lock: lock,
        };
        state.verify_local()?;
        Ok(state)
    }

    fn verify_local(&self) -> Result<(), String> {
        for (idx, expected) in self.head.curves.iter().enumerate() {
            let name = curve_name(idx);
            if hash(&self.dir.join(&name))? != *expected {
                return Err(format!(
                    "local isogeny artifact {name} failed checksum validation"
                ));
            }
        }
        if let Some(expected) = &self.head.result_blake3 {
            if hash(&self.dir.join("result.json"))? != *expected {
                return Err("local isogeny result failed checksum validation".into());
            }
        }
        Ok(())
    }

    pub(super) fn completed(&self) -> Result<Vec<PerCurveResult>, String> {
        self.head
            .curves
            .iter()
            .enumerate()
            .map(|(idx, _)| {
                serde_json::from_slice(
                    &fs::read(self.dir.join(curve_name(idx))).map_err(|e| e.to_string())?,
                )
                .map_err(|e| format!("invalid saved isogeny curve {idx}: {e}"))
            })
            .collect()
    }

    pub(super) fn commit_curve(
        &mut self,
        idx: usize,
        curve: &PerCurveResult,
    ) -> Result<(), String> {
        if idx != self.head.curves.len() {
            return Err("isogeny curve checkpoint is out of order".into());
        }
        if let Some(uri) = &self.uri {
            if remote_head(uri, &self.head.input_digest)? != self.head {
                return Err("S3 isogeny state changed since the last upload".into());
            }
        }
        let name = curve_name(idx);
        let path = self.dir.join(&name);
        atomic(
            &path,
            &serde_json::to_vec_pretty(curve).map_err(|e| e.to_string())?,
        )?;
        let mut next = self.head.clone();
        next.curves.push(hash(&path)?);
        if let Some(uri) = &self.uri {
            eprintln!("[isogeny experiment] uploading completed curve {}", idx + 1);
            aws(&[
                "s3",
                "cp",
                path.to_str().ok_or("state path must be UTF-8")?,
                &format!("{uri}/{name}"),
                "--only-show-errors",
            ])?;
            write_head_remote(&self.dir, uri, &next)?;
        }
        write_head_local(&self.dir, &next)?;
        self.head = next;
        Ok(())
    }

    pub(super) fn finish(&mut self, report: &ExperimentReport) -> Result<(), String> {
        if report.per_curve.len() != self.head.curves.len() {
            return Err("isogeny report is missing completed curves".into());
        }
        let path = self.dir.join("result.json");
        let bytes = serde_json::to_vec_pretty(report).map_err(|e| e.to_string())?;
        if let Some(expected) = &self.head.result_blake3 {
            if hash(&path)? != *expected || blake3::hash(&bytes).to_hex().to_string() != *expected {
                return Err("saved isogeny result differs from its checkpoint".into());
            }
            return Ok(());
        }
        atomic(&path, &bytes)?;
        let mut next = self.head.clone();
        next.result_blake3 = Some(hash(&path)?);
        if let Some(uri) = &self.uri {
            if remote_head(uri, &self.head.input_digest)? != self.head {
                return Err("S3 isogeny state changed since the last upload".into());
            }
            eprintln!("[isogeny experiment] uploading final report");
            aws(&[
                "s3",
                "cp",
                path.to_str().ok_or("state path must be UTF-8")?,
                &format!("{uri}/result.json"),
                "--only-show-errors",
            ])?;
            write_head_remote(&self.dir, uri, &next)?;
        }
        write_head_local(&self.dir, &next)?;
        self.head = next;
        Ok(())
    }
}
