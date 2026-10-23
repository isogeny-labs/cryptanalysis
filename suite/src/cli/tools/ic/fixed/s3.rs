//! S3 custody for the fixed campaign's transactionally consistent SQLite snapshots.

use std::fs::{self, File, OpenOptions};
use std::io::Read;
#[cfg(unix)]
use std::os::fd::AsRawFd;
use std::path::{Path, PathBuf};
use std::process::Command;

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct Head {
    schema: u32,
    input_digest: String,
    generation: u64,
    database_blake3: Option<String>,
    report_blake3: Option<String>,
}

pub(super) struct Store {
    dir: PathBuf,
    uri: String,
    head: Head,
    verbose: bool,
    _lock: File,
}

fn aws(args: &[&str]) -> Result<Vec<u8>, String> {
    let output = Command::new("aws")
        .args(args)
        .output()
        .map_err(|e| format!("starting AWS CLI: {e}"))?;
    if !output.status.success() {
        return Err(format!(
            "aws {}: {}",
            args.join(" "),
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    Ok(output.stdout)
}

fn hash(path: &Path) -> Result<String, String> {
    let mut file = File::open(path).map_err(|e| format!("{}: {e}", path.display()))?;
    let mut hasher = blake3::Hasher::new();
    let mut buffer = [0u8; 65536];
    loop {
        let read = file.read(&mut buffer).map_err(|e| e.to_string())?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(hasher.finalize().to_hex().to_string())
}

pub(super) fn input_digest(
    params: &Path,
    selector: Option<&Path>,
    script: &Path,
) -> Result<String, String> {
    let mut hash = blake3::Hasher::new();
    hash.update(b"ic-fixed-input-v2\0");
    let source = script
        .parent()
        .ok_or("fixed script has no parent directory")?;
    for file in [Some(params), selector] {
        if let Some(file) = file {
            let bytes = fs::read(file).map_err(|e| format!("{}: {e}", file.display()))?;
            hash.update(&(bytes.len() as u64).to_le_bytes());
            hash.update(&bytes);
        } else {
            hash.update(&0u64.to_le_bytes());
        }
    }
    for name in [
        "cnf.py",
        "curves.py",
        "decomp.py",
        "field.py",
        "indexcalc_e2e.py",
        "indexcalc_fixed.py",
        "indexcalc_selector.py",
    ] {
        let path = source.join(name);
        hash.update(name.as_bytes());
        hash.update(hash_file(&path)?.as_bytes());
    }
    Ok(hash.finalize().to_hex().to_string())
}

fn hash_file(path: &Path) -> Result<String, String> {
    hash(path)
}

fn head_uri(uri: &str) -> String {
    format!("{uri}/_fixed_head.json")
}
fn artifact_uri(uri: &str, generation: u64, name: &str) -> String {
    format!("{uri}/generations/{generation}/{name}")
}
fn marker(dir: &Path) -> PathBuf {
    dir.join(".fixed-s3-head.json")
}

fn read_head(bytes: &[u8], identity: &str) -> Result<Head, String> {
    let head: Head =
        serde_json::from_slice(bytes).map_err(|e| format!("invalid fixed S3 head: {e}"))?;
    if head.schema != 1 || head.input_digest != identity {
        return Err("fixed S3 state belongs to different inputs or source".into());
    }
    Ok(head)
}

fn verify_local_artifacts(dir: &Path, head: &Head) -> Result<(), String> {
    for (name, expected) in [
        ("campaign.sqlite3", &head.database_blake3),
        ("result.json", &head.report_blake3),
    ] {
        if let Some(expected) = expected {
            let path = dir.join(name);
            if !path.is_file() {
                return Err(format!("local fixed S3 artifact {name} is missing"));
            }
            if &hash(&path)? != expected {
                return Err(format!(
                    "local fixed S3 artifact {name} failed checksum validation"
                ));
            }
        }
    }
    Ok(())
}

fn remote_head(uri: &str, identity: &str) -> Result<Head, String> {
    read_head(
        &aws(&["s3", "cp", &head_uri(uri), "-", "--only-show-errors"])?,
        identity,
    )
}

fn write_marker(dir: &Path, head: &Head) -> Result<(), String> {
    let temp = dir.join(".fixed-s3-head.tmp");
    fs::write(
        &temp,
        serde_json::to_vec_pretty(head).map_err(|e| e.to_string())?,
    )
    .map_err(|e| e.to_string())?;
    File::open(&temp)
        .map_err(|e| e.to_string())?
        .sync_all()
        .map_err(|e| e.to_string())?;
    fs::rename(&temp, marker(dir)).map_err(|e| e.to_string())
}

impl Store {
    pub(super) fn prepare(
        dir: &Path,
        uri: &str,
        identity: &str,
        resume: bool,
        verbose: bool,
    ) -> Result<Self, String> {
        let Some((bucket, prefix)) = uri.strip_prefix("s3://").and_then(|s| s.split_once('/'))
        else {
            return Err("--s3-uri must be s3://BUCKET/PREFIX".into());
        };
        if bucket.is_empty() || prefix.trim_matches('/').is_empty() || uri.ends_with('/') {
            return Err(
                "--s3-uri must name a bucket and nonempty prefix without a trailing slash".into(),
            );
        }
        fs::create_dir_all(dir).map_err(|e| format!("{}: {e}", dir.display()))?;
        let lock = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(dir.join(".fixed-s3.lock"))
            .map_err(|e| e.to_string())?;
        #[cfg(unix)]
        if unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
            return Err(format!("{} is already in use", dir.display()));
        }
        #[cfg(not(unix))]
        return Err("fixed state locking is unavailable on this platform".into());
        let head = if resume {
            if marker(dir).is_file() {
                let local =
                    read_head(&fs::read(marker(dir)).map_err(|e| e.to_string())?, identity)?;
                if remote_head(uri, identity)? != local {
                    return Err("S3 fixed state is ahead of or differs from local state; restore into a fresh directory".into());
                }
                verify_local_artifacts(dir, &local)?;
                local
            } else {
                if dir.join("campaign.sqlite3").exists() || dir.join("result.json").exists() {
                    return Err("cannot restore fixed S3 state into a nonempty directory".into());
                }
                let head = remote_head(uri, identity)?;
                if verbose {
                    eprintln!("[ic fixed] restoring S3 generation {}", head.generation);
                }
                for (name, expected) in [
                    ("campaign.sqlite3", &head.database_blake3),
                    ("result.json", &head.report_blake3),
                ] {
                    if let Some(expected) = expected {
                        let remote = artifact_uri(uri, head.generation, name);
                        let local = dir.join(name);
                        aws(&[
                            "s3",
                            "cp",
                            &remote,
                            local
                                .to_str()
                                .ok_or("fixed path must be UTF-8 for AWS CLI")?,
                            "--only-show-errors",
                        ])?;
                        if &hash(&local)? != expected {
                            return Err(format!(
                                "fixed S3 artifact {name} failed checksum validation"
                            ));
                        }
                    }
                }
                write_marker(dir, &head)?;
                head
            }
        } else {
            if dir.join("campaign.sqlite3").exists()
                || dir.join("result.json").exists()
                || marker(dir).exists()
            {
                return Err(
                    "fixed directory is not empty; use --resume or a fresh directory".into(),
                );
            }
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
                return Err("fixed S3 prefix is not empty; use a new prefix".into());
            }
            let head = Head {
                schema: 1,
                input_digest: identity.into(),
                generation: 0,
                database_blake3: None,
                report_blake3: None,
            };
            let temp = dir.join(".fixed-s3-head.upload");
            fs::write(&temp, serde_json::to_vec(&head).map_err(|e| e.to_string())?)
                .map_err(|e| e.to_string())?;
            aws(&[
                "s3",
                "cp",
                temp.to_str().ok_or("fixed path must be UTF-8")?,
                &head_uri(uri),
                "--only-show-errors",
            ])?;
            fs::remove_file(&temp).map_err(|e| e.to_string())?;
            write_marker(dir, &head)?;
            head
        };
        Ok(Store {
            dir: dir.into(),
            uri: uri.into(),
            head,
            verbose,
            _lock: lock,
        })
    }

    pub(super) fn sync(&mut self, python: &Path) -> Result<(), String> {
        if remote_head(&self.uri, &self.head.input_digest)? != self.head {
            return Err(
                "fixed S3 state changed since the last upload; refusing to overwrite it".into(),
            );
        }
        let database = self.dir.join("campaign.sqlite3");
        if !database.is_file() {
            return Err("fixed campaign database is missing".into());
        }
        if self.verbose {
            eprintln!("[ic fixed] SQLite snapshot and S3 upload started");
        }
        let snapshot = self.dir.join(".fixed-snapshot.tmp");
        if snapshot.exists() {
            fs::remove_file(&snapshot).map_err(|e| e.to_string())?;
        }
        let backup = Command::new(python).arg("-c")
            .arg("import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); check=d.execute('pragma integrity_check').fetchone()[0]; d.close(); s.close(); sys.exit(0 if check=='ok' else 2)")
            .arg(&database).arg(&snapshot).output().map_err(|e| format!("starting SQLite backup: {e}"))?;
        if !backup.status.success() {
            return Err(format!(
                "SQLite backup failed: {}",
                String::from_utf8_lossy(&backup.stderr).trim()
            ));
        }
        let db_hash = hash(&snapshot)?;
        let report = self.dir.join("result.json");
        let report_hash = hash(&report)?;
        let next_generation = self.head.generation + 1;
        aws(&[
            "s3",
            "cp",
            snapshot.to_str().ok_or("fixed path must be UTF-8")?,
            &artifact_uri(&self.uri, next_generation, "campaign.sqlite3"),
            "--only-show-errors",
        ])?;
        aws(&[
            "s3",
            "cp",
            report.to_str().ok_or("fixed path must be UTF-8")?,
            &artifact_uri(&self.uri, next_generation, "result.json"),
            "--only-show-errors",
        ])?;
        let next = Head {
            schema: 1,
            input_digest: self.head.input_digest.clone(),
            generation: next_generation,
            database_blake3: Some(db_hash),
            report_blake3: Some(report_hash),
        };
        let temp = self.dir.join(".fixed-s3-head.upload");
        fs::write(&temp, serde_json::to_vec(&next).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
        aws(&[
            "s3",
            "cp",
            temp.to_str().ok_or("fixed path must be UTF-8")?,
            &head_uri(&self.uri),
            "--only-show-errors",
        ])?;
        fs::remove_file(&temp).map_err(|e| e.to_string())?;
        // The committed checksum covers SQLite's consistent backup, which can
        // differ byte-for-byte from the live database even when logically
        // equivalent. Install that exact published snapshot locally so a
        // same-directory resume can verify it against the head.
        fs::rename(&snapshot, &database).map_err(|e| e.to_string())?;
        write_marker(&self.dir, &next)?;
        self.head = next;
        if self.verbose {
            eprintln!(
                "[ic fixed] S3 upload complete (generation {})",
                self.head.generation
            );
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn same_directory_resume_checks_committed_local_artifacts() {
        let dir = std::env::temp_dir().join(format!("fixed-s3-local-check-{}", std::process::id()));
        fs::create_dir_all(&dir).unwrap();
        let database = dir.join("campaign.sqlite3");
        let report = dir.join("result.json");
        fs::write(&database, b"live sqlite file differs from backup bytes").unwrap();
        fs::write(&report, b"published report").unwrap();
        let snapshot = dir.join(".fixed-snapshot.tmp");
        fs::write(&snapshot, b"published sqlite snapshot").unwrap();
        let head = Head {
            schema: 1,
            input_digest: "input".into(),
            generation: 1,
            database_blake3: Some(hash(&snapshot).unwrap()),
            report_blake3: Some(hash(&report).unwrap()),
        };
        fs::rename(&snapshot, &database).unwrap();
        assert!(verify_local_artifacts(&dir, &head).is_ok());

        fs::write(&database, b"modified local sqlite state").unwrap();
        assert!(verify_local_artifacts(&dir, &head)
            .unwrap_err()
            .contains("campaign.sqlite3 failed checksum validation"));
        fs::write(&database, b"published sqlite snapshot").unwrap();
        fs::write(&report, b"modified local result").unwrap();
        assert!(verify_local_artifacts(&dir, &head)
            .unwrap_err()
            .contains("result.json failed checksum validation"));
        fs::remove_dir_all(dir).unwrap();
    }
}
