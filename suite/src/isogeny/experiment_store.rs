//! Generation-safe remote custody for isogeny experiment checkpoints.

use serde::{Deserialize, Serialize};
use std::fs::{self, OpenOptions};
use std::path::PathBuf;
use std::process::Command;

const MAX_CHECKPOINT_BYTES: usize = 32 * 1024 * 1024;
const MAX_HEAD_BYTES: usize = 16 * 1024;

#[derive(Clone, Debug, Deserialize, Serialize)]
pub(super) struct RemoteHead {
    pub schema_version: u32,
    pub identity_blake3: String,
    pub generation: usize,
    pub planned_curves: usize,
    pub complete: bool,
    pub checkpoint_blake3: String,
    pub checkpoint_bytes: usize,
}

#[derive(Clone, Debug)]
pub(super) struct ObservedHead {
    pub document: RemoteHead,
    pub etag: String,
}

pub(super) enum RemoteStore {
    S3 { bucket: String, prefix: String },
    File(PathBuf),
}

impl RemoteStore {
    pub(super) fn parse(uri: &str) -> Result<Self, String> {
        if let Some(rest) = uri.strip_prefix("s3://") {
            let (bucket, prefix) = rest
                .split_once('/')
                .ok_or("S3 URI must include a bucket and nonempty prefix")?;
            if bucket.is_empty()
                || prefix.is_empty()
                || prefix.starts_with('/')
                || prefix
                    .split('/')
                    .any(|part| part.is_empty() || part == "." || part == "..")
            {
                return Err("S3 URI has an invalid bucket or prefix".into());
            }
            return Ok(Self::S3 {
                bucket: bucket.to_string(),
                prefix: prefix.to_string(),
            });
        }
        if let Some(path) = uri.strip_prefix("file://") {
            let path = PathBuf::from(path);
            if !path.is_absolute() {
                return Err("file remote must use an absolute path".into());
            }
            return Ok(Self::File(path));
        }
        Err("remote URI must use s3:// or file://".into())
    }

    fn key(&self, suffix: &str) -> String {
        match self {
            Self::S3 { prefix, .. } => format!("{prefix}/{suffix}"),
            Self::File(_) => suffix.to_string(),
        }
    }

    fn aws(&self, args: &[&str]) -> Result<std::process::Output, String> {
        let mut command = Command::new("aws");
        command.args(["--no-cli-pager", "--output", "json", "s3api"]);
        command.args(args);
        command
            .output()
            .map_err(|e| format!("cannot invoke AWS CLI: {e}"))
    }

    fn aws_ok(&self, args: &[&str]) -> Result<String, String> {
        let output = self.aws(args)?;
        if !output.status.success() {
            return Err(format!(
                "AWS S3 operation failed: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            ));
        }
        String::from_utf8(output.stdout).map_err(|e| e.to_string())
    }

    fn object_path(&self, suffix: &str) -> PathBuf {
        match self {
            Self::File(root) => root.join(suffix),
            Self::S3 { .. } => unreachable!(),
        }
    }

    fn get_object(&self, suffix: &str, expected_etag: Option<&str>) -> Result<Vec<u8>, String> {
        match self {
            Self::File(_) => {
                let path = self.object_path(suffix);
                let limit = if suffix == "_isogeny_head.json" {
                    MAX_HEAD_BYTES
                } else {
                    MAX_CHECKPOINT_BYTES
                };
                if fs::metadata(&path).map_err(|e| e.to_string())?.len() > limit as u64 {
                    return Err("remote isogeny object exceeds size limit".into());
                }
                fs::read(path).map_err(|e| e.to_string())
            }
            Self::S3 { bucket, .. } => {
                let key = self.key(suffix);
                let temp = std::env::temp_dir().join(format!(
                    "crax-isogeny-s3-{}-{}",
                    std::process::id(),
                    std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .map_err(|e| e.to_string())?
                        .as_nanos()
                ));
                let path = temp.to_str().ok_or("temporary path is not UTF-8")?;
                let mut args = vec!["get-object", "--bucket", bucket, "--key", &key];
                if let Some(etag) = expected_etag {
                    args.extend(["--if-match", etag]);
                } else {
                    args.extend(["--range", "bytes=0-33554432"]);
                }
                args.push(path);
                let result = self.aws_ok(&args);
                if let Err(error) = result {
                    let _ = fs::remove_file(&temp);
                    return Err(error);
                }
                let bytes = fs::read(&temp).map_err(|e| e.to_string());
                let _ = fs::remove_file(&temp);
                bytes
            }
        }
    }

    fn head_etag(&self) -> Result<Option<String>, String> {
        match self {
            Self::File(_) => {
                let path = self.object_path("_isogeny_head.json");
                match fs::read(path) {
                    Ok(bytes) => Ok(Some(blake3::hash(&bytes).to_hex().to_string())),
                    Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
                    Err(error) => Err(error.to_string()),
                }
            }
            Self::S3 { bucket, .. } => {
                let key = self.key("_isogeny_head.json");
                let output = self.aws(&["head-object", "--bucket", bucket, "--key", &key])?;
                if !output.status.success() {
                    let stderr = String::from_utf8_lossy(&output.stderr);
                    if stderr.contains("(404)") || stderr.contains("Not Found") {
                        return Ok(None);
                    }
                    return Err(format!("AWS S3 HEAD failed: {}", stderr.trim()));
                }
                let value: serde_json::Value =
                    serde_json::from_slice(&output.stdout).map_err(|e| e.to_string())?;
                let size = value["ContentLength"]
                    .as_u64()
                    .ok_or("S3 HEAD has no size")?;
                if size > MAX_HEAD_BYTES as u64 {
                    return Err("remote isogeny head exceeds size limit".into());
                }
                Ok(Some(
                    value["ETag"]
                        .as_str()
                        .ok_or("S3 HEAD has no ETag")?
                        .to_string(),
                ))
            }
        }
    }

    pub(super) fn read_head(&self) -> Result<Option<ObservedHead>, String> {
        let Some(etag) = self.head_etag()? else {
            return Ok(None);
        };
        let bytes = self.get_object("_isogeny_head.json", Some(&etag))?;
        if bytes.len() > MAX_HEAD_BYTES {
            return Err("remote isogeny head exceeds size limit".into());
        }
        if matches!(self, Self::File(_)) && blake3::hash(&bytes).to_hex().to_string() != etag {
            return Err("remote isogeny head changed while being read".into());
        }
        let document: RemoteHead =
            serde_json::from_slice(&bytes).map_err(|e| format!("invalid remote head: {e}"))?;
        if document.schema_version != 1
            || document.identity_blake3.len() != 64
            || document.checkpoint_blake3.len() != 64
            || document.checkpoint_bytes > MAX_CHECKPOINT_BYTES
            || document.planned_curves == 0
            || document.planned_curves > 1_000
            || document.generation > document.planned_curves
            || document.complete != (document.generation == document.planned_curves)
        {
            return Err("remote isogeny head is invalid or outside size limits".into());
        }
        Ok(Some(ObservedHead { document, etag }))
    }

    pub(super) fn read_checkpoint(&self, head: &RemoteHead) -> Result<Vec<u8>, String> {
        let suffix = format!("generations/{:06}/checkpoint.json", head.generation);
        let bytes = self.get_object(&suffix, None)?;
        if bytes.len() != head.checkpoint_bytes
            || blake3::hash(&bytes).to_hex().to_string() != head.checkpoint_blake3
        {
            return Err("remote isogeny checkpoint size or digest differs from head".into());
        }
        Ok(bytes)
    }

    pub(super) fn publish(
        &self,
        checkpoint: &[u8],
        generation: usize,
        planned_curves: usize,
        identity_blake3: &str,
        prior: Option<&ObservedHead>,
    ) -> Result<ObservedHead, String> {
        if checkpoint.len() > MAX_CHECKPOINT_BYTES {
            return Err("isogeny checkpoint exceeds the remote size limit".into());
        }
        if planned_curves == 0 || generation > planned_curves {
            return Err("isogeny checkpoint generation exceeds planned curves".into());
        }
        let checkpoint_blake3 = blake3::hash(checkpoint).to_hex().to_string();
        let document = RemoteHead {
            schema_version: 1,
            identity_blake3: identity_blake3.to_string(),
            generation,
            planned_curves,
            complete: generation == planned_curves,
            checkpoint_blake3,
            checkpoint_bytes: checkpoint.len(),
        };
        let head_bytes = serde_json::to_vec_pretty(&document).map_err(|e| e.to_string())?;
        let generation_key = format!("generations/{generation:06}/checkpoint.json");
        match self {
            Self::File(root) => {
                fs::create_dir_all(root).map_err(|e| e.to_string())?;
                let lock = OpenOptions::new()
                    .write(true)
                    .create(true)
                    .open(root.join(".remote.lock"))
                    .map_err(|e| e.to_string())?;
                lock.try_lock()
                    .map_err(|e| format!("remote isogeny head is being written: {e}"))?;
                let current = self.read_head()?;
                if current.as_ref().map(|h| h.etag.as_str()) != prior.map(|h| h.etag.as_str()) {
                    return Err("remote isogeny head advanced concurrently".into());
                }
                let object = self.object_path(&generation_key);
                fs::create_dir_all(object.parent().unwrap()).map_err(|e| e.to_string())?;
                let temp = object.with_extension(format!(
                    "tmp.{}.{}",
                    std::process::id(),
                    std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .map_err(|e| e.to_string())?
                        .as_nanos()
                ));
                {
                    use std::io::Write;
                    let mut file = OpenOptions::new()
                        .write(true)
                        .create_new(true)
                        .open(&temp)
                        .map_err(|e| e.to_string())?;
                    file.write_all(checkpoint).map_err(|e| e.to_string())?;
                    file.sync_all().map_err(|e| e.to_string())?;
                }
                let linked = fs::hard_link(&temp, &object);
                let _ = fs::remove_file(&temp);
                match linked {
                    Ok(()) => {}
                    Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                        if self.get_object(&generation_key, None)? != checkpoint {
                            return Err("remote immutable checkpoint generation differs".into());
                        }
                    }
                    Err(error) => return Err(error.to_string()),
                }
                #[cfg(unix)]
                fs::File::open(object.parent().unwrap())
                    .and_then(|directory| directory.sync_all())
                    .map_err(|e| e.to_string())?;
                super::experiment::write_atomic_bytes(
                    &root.join("_isogeny_head.json"),
                    &head_bytes,
                )?;
            }
            Self::S3 { bucket, .. } => {
                let temp = std::env::temp_dir().join(format!(
                    "crax-isogeny-put-{}-{}",
                    std::process::id(),
                    std::time::SystemTime::now()
                        .duration_since(std::time::UNIX_EPOCH)
                        .map_err(|e| e.to_string())?
                        .as_nanos()
                ));
                fs::write(&temp, checkpoint).map_err(|e| e.to_string())?;
                let object_key = self.key(&generation_key);
                let body = temp.to_str().ok_or("temporary path is not UTF-8")?;
                let put = self.aws(&[
                    "put-object",
                    "--bucket",
                    bucket,
                    "--key",
                    &object_key,
                    "--body",
                    body,
                    "--if-none-match",
                    "*",
                ]);
                let _ = fs::remove_file(&temp);
                let output = put?;
                if !output.status.success() && self.get_object(&generation_key, None)? != checkpoint
                {
                    return Err(
                        "remote immutable checkpoint generation differs or upload failed".into(),
                    );
                }
                fs::write(&temp, &head_bytes).map_err(|e| e.to_string())?;
                let head_key = self.key("_isogeny_head.json");
                let mut args = vec![
                    "put-object",
                    "--bucket",
                    bucket,
                    "--key",
                    &head_key,
                    "--body",
                    body,
                ];
                if let Some(head) = prior {
                    args.extend(["--if-match", &head.etag]);
                } else {
                    args.extend(["--if-none-match", "*"]);
                }
                let result = self.aws_ok(&args);
                let _ = fs::remove_file(&temp);
                result?;
            }
        }
        let observed = self
            .read_head()?
            .ok_or("remote head vanished after publish")?;
        if observed.document.checkpoint_blake3 != document.checkpoint_blake3
            || observed.document.generation != document.generation
            || observed.document.identity_blake3 != document.identity_blake3
        {
            return Err("remote isogeny head changed after publish".into());
        }
        Ok(observed)
    }
}
