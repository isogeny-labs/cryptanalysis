//! Commit complete workflow artifacts to S3 with a checksummed head written last.

use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
#[cfg(unix)]
use std::os::fd::AsRawFd;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, Instant};

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct Entry {
    bytes: u64,
    blake3: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
struct Head {
    schema: u32,
    params_digest: String,
    generation: u64,
    files: BTreeMap<String, Entry>,
}

pub(super) struct Store {
    dir: PathBuf,
    uri: String,
    head: Head,
    sync_every: Duration,
    last_sync: Instant,
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

fn head_uri(uri: &str) -> String {
    format!("{uri}/_workflow_head.json")
}
fn artifact_uri(uri: &str, head: &Head, name: &str) -> String {
    if head.schema == 1 {
        format!("{uri}/{name}")
    } else {
        format!("{uri}/generations/{}/{name}", head.generation)
    }
}
fn local_head(dir: &Path) -> PathBuf {
    dir.join(".workflow-s3-head.json")
}

fn read_head(bytes: &[u8], digest: &str) -> Result<Head, String> {
    let head: Head =
        serde_json::from_slice(bytes).map_err(|e| format!("invalid workflow S3 head: {e}"))?;
    if !matches!(head.schema, 1 | 2) || head.params_digest != digest {
        return Err("workflow S3 head does not match these parameters".into());
    }
    Ok(head)
}

fn digest(path: &Path) -> Result<Entry, String> {
    if !fs::symlink_metadata(path)
        .map_err(|e| e.to_string())?
        .file_type()
        .is_file()
    {
        return Err(format!(
            "{} is not a regular workflow artifact",
            path.display()
        ));
    }
    let bytes = fs::read(path).map_err(|e| format!("{}: {e}", path.display()))?;
    Ok(Entry {
        bytes: bytes.len() as u64,
        blake3: blake3::hash(&bytes).to_hex().to_string(),
    })
}

fn paths(dir: &Path) -> Result<BTreeMap<String, Entry>, String> {
    let mut found = BTreeMap::new();
    for name in [
        "state.json",
        "factor_base.json",
        "logs.json",
        "solutions.json",
        "baseline.json",
        "result.json",
    ] {
        let path = dir.join(name);
        if path.is_file() {
            found.insert(name.into(), digest(&path)?);
        }
    }
    let relations = dir.join("relations");
    if relations.is_dir() {
        for item in fs::read_dir(&relations).map_err(|e| e.to_string())? {
            let item = item.map_err(|e| e.to_string())?;
            let name = item.file_name().to_string_lossy().to_string();
            if safe_name(&format!("relations/{name}")) {
                found.insert(format!("relations/{name}"), digest(&item.path())?);
            }
        }
    }
    Ok(found)
}

fn local_payload(dir: &Path) -> Result<bool, String> {
    Ok(!paths(dir)?.is_empty() || local_head(dir).exists())
}

fn write_local_head(dir: &Path, head: &Head) -> Result<(), String> {
    let bytes = serde_json::to_vec_pretty(head).map_err(|e| e.to_string())?;
    let tmp = dir.join(".workflow-s3-head.json.tmp");
    fs::write(&tmp, bytes).map_err(|e| e.to_string())?;
    File::open(&tmp)
        .map_err(|e| e.to_string())?
        .sync_all()
        .map_err(|e| e.to_string())?;
    fs::rename(&tmp, local_head(dir)).map_err(|e| e.to_string())
}

fn remote_head(uri: &str, digest: &str) -> Result<Head, String> {
    remote_head_with(uri, digest, &mut aws)
}

fn remote_head_with(
    uri: &str,
    digest: &str,
    run: &mut impl FnMut(&[&str]) -> Result<Vec<u8>, String>,
) -> Result<Head, String> {
    let bytes = run(&["s3", "cp", &head_uri(uri), "-", "--only-show-errors"])?;
    read_head(&bytes, digest)
}

impl Store {
    pub(super) fn prepare(
        dir: &Path,
        uri: &str,
        params_digest: &str,
        resume: bool,
        sync_every: u64,
        verbose: bool,
    ) -> Result<Self, String> {
        if sync_every == 0 {
            return Err("--sync-every must be positive".into());
        }
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
            .open(dir.join(".workflow-s3.lock"))
            .map_err(|e| e.to_string())?;
        #[cfg(unix)]
        if unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } != 0 {
            return Err(format!("{} is already in use", dir.display()));
        }
        #[cfg(not(unix))]
        return Err("workflow state locking is unavailable on this platform".into());
        let head = if resume {
            if local_head(dir).is_file() {
                let head = read_head(
                    &fs::read(local_head(dir)).map_err(|e| e.to_string())?,
                    params_digest,
                )?;
                if remote_head(uri, params_digest)? != head {
                    return Err("S3 workflow state is ahead of or differs from local state; restore into a fresh directory".into());
                }
                if paths(dir)? != head.files {
                    return Err("local workflow artifacts differ from the last S3 commit; restore into a fresh directory".into());
                }
                head
            } else {
                if local_payload(dir)? {
                    return Err("cannot restore S3 workflow state into a nonempty directory".into());
                }
                let head = remote_head(uri, params_digest)?;
                if verbose {
                    eprintln!(
                        "[ic workflow] restoring {} artifact(s) from S3",
                        head.files.len()
                    );
                }
                for (name, expected) in &head.files {
                    // The head is remote input: admit only the artifact names we generate.
                    if !safe_name(name) {
                        return Err("S3 workflow head contains an invalid artifact path".into());
                    }
                    let path = dir.join(name);
                    if let Some(parent) = path.parent() {
                        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
                    }
                    let remote = artifact_uri(uri, &head, name);
                    let local = path
                        .to_str()
                        .ok_or("workflow path must be UTF-8 for AWS CLI")?;
                    aws(&["s3", "cp", &remote, local, "--only-show-errors"])?;
                    if &digest(&path)? != expected {
                        return Err(format!(
                            "S3 workflow artifact {name} failed checksum validation"
                        ));
                    }
                }
                write_local_head(dir, &head)?;
                head
            }
        } else {
            if local_payload(dir)? {
                return Err(
                    "workflow run directory is not empty; use --resume or a fresh directory".into(),
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
                return Err("S3 workflow prefix is not empty; use a new prefix".into());
            }
            let head = Head {
                schema: 2,
                params_digest: params_digest.into(),
                generation: 0,
                files: BTreeMap::new(),
            };
            let bytes = serde_json::to_vec(&head).map_err(|e| e.to_string())?;
            let temp = dir.join(".workflow-s3-head.upload");
            fs::write(&temp, bytes).map_err(|e| e.to_string())?;
            aws(&[
                "s3",
                "cp",
                temp.to_str().ok_or("workflow path must be UTF-8")?,
                &head_uri(uri),
                "--only-show-errors",
            ])?;
            fs::remove_file(&temp).map_err(|e| e.to_string())?;
            write_local_head(dir, &head)?;
            head
        };
        Ok(Store {
            dir: dir.into(),
            uri: uri.into(),
            head,
            sync_every: Duration::from_secs(sync_every),
            last_sync: Instant::now(),
            verbose,
            _lock: lock,
        })
    }

    pub(super) fn sync(&mut self, force: bool) -> Result<(), String> {
        self.sync_with(force, &mut aws)
    }

    fn sync_with(
        &mut self,
        force: bool,
        run: &mut impl FnMut(&[&str]) -> Result<Vec<u8>, String>,
    ) -> Result<(), String> {
        if !force && self.last_sync.elapsed() < self.sync_every {
            return Ok(());
        }
        if remote_head_with(&self.uri, &self.head.params_digest, run)? != self.head {
            return Err(
                "S3 workflow state changed since the last upload; refusing to overwrite it".into(),
            );
        }
        let files = paths(&self.dir)?;
        if files == self.head.files {
            self.last_sync = Instant::now();
            return Ok(());
        }
        if self.verbose {
            eprintln!(
                "[ic workflow] S3 upload started: {} artifact(s)",
                files.len()
            );
        }
        let next = Head {
            schema: 2,
            params_digest: self.head.params_digest.clone(),
            generation: self
                .head
                .generation
                .checked_add(1)
                .ok_or("workflow S3 generation overflow")?,
            files,
        };
        // Every generation is self-contained. Never overwrite objects named
        // by the published head, including when upgrading a legacy head.
        for (name, entry) in &next.files {
            let path = self.dir.join(name);
            let local = path
                .to_str()
                .ok_or("workflow path must be UTF-8 for AWS CLI")?;
            let remote = artifact_uri(&self.uri, &next, name);
            run(&["s3", "cp", local, &remote, "--only-show-errors"])?;
            if &digest(&path)? != entry {
                return Err(format!("workflow artifact {name} changed during S3 upload"));
            }
        }
        let temp = self.dir.join(".workflow-s3-head.upload");
        fs::write(&temp, serde_json::to_vec(&next).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
        run(&[
            "s3",
            "cp",
            temp.to_str().ok_or("workflow path must be UTF-8")?,
            &head_uri(&self.uri),
            "--only-show-errors",
        ])?;
        fs::remove_file(&temp).map_err(|e| e.to_string())?;
        write_local_head(&self.dir, &next)?;
        self.head = next;
        self.last_sync = Instant::now();
        if self.verbose {
            eprintln!(
                "[ic workflow] S3 upload complete (generation {})",
                self.head.generation
            );
        }
        Ok(())
    }
}

fn safe_name(name: &str) -> bool {
    matches!(
        name,
        "state.json"
            | "factor_base.json"
            | "logs.json"
            | "solutions.json"
            | "baseline.json"
            | "result.json"
    ) || name.strip_prefix("relations/unit-").is_some_and(|tail| {
        tail.strip_suffix(".json")
            .is_some_and(|digits| !digits.is_empty() && digits.bytes().all(|b| b.is_ascii_digit()))
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn remote_head_can_only_name_workflow_artifacts() {
        for name in [
            "state.json",
            "factor_base.json",
            "relations/unit-00001.json",
        ] {
            assert!(safe_name(name));
        }
        for name in [
            "../state.json",
            "relations/../secret",
            "relations/unit-x.json",
            "relations/unit-1.json/extra",
            "/tmp/secret",
        ] {
            assert!(!safe_name(name));
        }
    }

    #[test]
    fn snapshot_digest_detects_changed_bytes() {
        let root = std::env::temp_dir().join(format!("workflow-s3-{}", std::process::id()));
        fs::create_dir_all(&root).unwrap();
        let file = root.join("state.json");
        fs::write(&file, b"one").unwrap();
        let first = paths(&root).unwrap();
        fs::write(&file, b"two").unwrap();
        assert_ne!(first, paths(&root).unwrap());
        fs::remove_dir_all(root).unwrap();
    }
    #[test]
    fn interrupted_upload_preserves_committed_generation_and_retries() {
        for schema in [1, 2] {
            let nonce = std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let dir = std::env::temp_dir().join(format!(
                "workflow-interrupt-{}-{nonce}-{schema}",
                std::process::id()
            ));
            fs::create_dir(&dir).unwrap();
            fs::write(dir.join("state.json"), b"old-state").unwrap();
            fs::write(dir.join("factor_base.json"), b"unchanged-factor-base").unwrap();
            let old = Head {
                schema,
                params_digest: "parameters".into(),
                generation: 1,
                files: paths(&dir).unwrap(),
            };
            let uri = "s3://bucket/workflow";
            let mut remote = BTreeMap::<String, Vec<u8>>::new();
            remote.insert(head_uri(uri), serde_json::to_vec(&old).unwrap());
            for name in old.files.keys() {
                remote.insert(
                    artifact_uri(uri, &old, name),
                    fs::read(dir.join(name)).unwrap(),
                );
            }
            write_local_head(&dir, &old).unwrap();
            fs::write(dir.join("state.json"), b"new-state").unwrap();
            let lock = File::create(dir.join(".workflow-s3.lock")).unwrap();
            let mut store = Store {
                dir: dir.clone(),
                uri: uri.into(),
                head: old.clone(),
                sync_every: Duration::from_secs(1),
                last_sync: Instant::now(),
                verbose: false,
                _lock: lock,
            };
            let mut fail_head = true;
            let mut run = |args: &[&str]| -> Result<Vec<u8>, String> {
                assert_eq!(&args[..2], &["s3", "cp"]);
                if args[3] == "-" {
                    return remote.get(args[2]).cloned().ok_or("missing object".into());
                }
                if args[3] == head_uri(uri) && fail_head {
                    fail_head = false;
                    return Err("interrupted before publishing head".into());
                }
                remote.insert(
                    args[3].into(),
                    fs::read(args[2]).map_err(|e| e.to_string())?,
                );
                Ok(Vec::new())
            };
            assert!(store
                .sync_with(true, &mut run)
                .unwrap_err()
                .contains("interrupted"));
            drop(run);
            let published = read_head(&remote[&head_uri(uri)], "parameters").unwrap();
            assert_eq!(published, old);
            for (name, entry) in &published.files {
                let bytes = &remote[&artifact_uri(uri, &published, name)];
                assert_eq!(bytes.len() as u64, entry.bytes);
                assert_eq!(blake3::hash(bytes).to_hex().as_str(), entry.blake3);
            }
            assert_eq!(store.head, old);
            let mut retry = |args: &[&str]| -> Result<Vec<u8>, String> {
                if args[3] == "-" {
                    return remote.get(args[2]).cloned().ok_or("missing object".into());
                }
                remote.insert(
                    args[3].into(),
                    fs::read(args[2]).map_err(|e| e.to_string())?,
                );
                Ok(Vec::new())
            };
            store.sync_with(true, &mut retry).unwrap();
            drop(retry);
            let published = read_head(&remote[&head_uri(uri)], "parameters").unwrap();
            assert_eq!(published.schema, 2);
            assert_eq!(published.generation, 2);
            assert_eq!(published, store.head);
            for (name, entry) in &published.files {
                let bytes = &remote[&artifact_uri(uri, &published, name)];
                assert_eq!(bytes, &fs::read(dir.join(name)).unwrap());
                assert_eq!(blake3::hash(bytes).to_hex().as_str(), entry.blake3);
            }
            assert_eq!(remote[&artifact_uri(uri, &old, "state.json")], b"old-state");
            drop(store);
            fs::remove_dir_all(dir).unwrap();
        }
    }
}
