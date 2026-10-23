//! Direct hash and extendable-output computation for the unified CLI.

use clap::Args;
use serde::Serialize;
use std::{
    path::{Path, PathBuf},
    process::Command,
};

use super::output::{CmdResult, Out};
use crate::hash;

#[derive(Args, Clone, Debug)]
pub struct DigestArgs {
    /// Digest name: md4, md5, sha1, sha224, sha256, sha384, sha512,
    /// sha512-224, sha512-256, sha3-224, sha3-256, sha3-384, sha3-512,
    /// shake128, or shake256. SHA-3 and SHAKE also accept hyphenated names.
    #[arg(long)]
    pub algorithm: String,
    /// UTF-8 text to hash.
    #[arg(long, conflicts_with_all = ["hex", "file"])]
    pub text: Option<String>,
    /// Hex-encoded bytes to hash.
    #[arg(long, conflicts_with_all = ["text", "file"])]
    pub hex: Option<String>,
    /// File or checked store:NAME/sha256:DIGEST reference to hash.
    #[arg(long, conflicts_with_all = ["text", "hex"])]
    pub file: Option<PathBuf>,
    /// Required output length in bytes for SHAKE128 or SHAKE256.
    #[arg(long)]
    pub output_bytes: Option<usize>,
}

#[derive(Serialize)]
struct DigestReport {
    status: &'static str,
    algorithm: String,
    input_bytes: usize,
    output_bytes: usize,
    digest_hex: String,
}

pub fn run(out: Out, args: &DigestArgs) -> CmdResult {
    let message = match (&args.text, &args.hex, &args.file) {
        (Some(text), None, None) => text.as_bytes().to_vec(),
        (None, Some(hex), None) => {
            hex::decode(hex).map_err(|e| format!("invalid --hex input: {e}"))?
        }
        (None, None, Some(path)) => read_file_input(path)?,
        _ => return Err("provide exactly one of --text, --hex, or --file".into()),
    };
    let algorithm = args.algorithm.to_ascii_lowercase().replace('_', "-");
    let xof = matches!(
        algorithm.as_str(),
        "shake128" | "shake-128" | "shake256" | "shake-256"
    );
    if xof && !matches!(args.output_bytes, Some(1..=1_048_576)) {
        return Err("SHAKE requires --output-bytes in 1..=1048576".into());
    }
    if !xof && args.output_bytes.is_some() {
        return Err("--output-bytes applies only to SHAKE128 and SHAKE256".into());
    }
    let digest: Vec<u8> = match algorithm.as_str() {
        "md4" => hash::md4(&message).to_vec(),
        "md5" => hash::md5(&message).to_vec(),
        "sha1" | "sha-1" => hash::sha1(&message).to_vec(),
        "sha224" | "sha-224" => hash::sha224(&message).to_vec(),
        "sha256" | "sha-256" => hash::sha256(&message).to_vec(),
        "sha384" | "sha-384" => hash::sha384(&message).to_vec(),
        "sha512" | "sha-512" => hash::sha512(&message).to_vec(),
        "sha512-224" | "sha-512-224" => hash::sha512_224(&message).to_vec(),
        "sha512-256" | "sha-512-256" => hash::sha512_256(&message).to_vec(),
        "sha3-224" | "sha-3-224" => hash::sha3_224(&message).to_vec(),
        "sha3-256" | "sha-3-256" | "sha3" | "sha-3" => hash::sha3_256(&message).to_vec(),
        "sha3-384" | "sha-3-384" => hash::sha3_384(&message).to_vec(),
        "sha3-512" | "sha-3-512" => hash::sha3_512(&message).to_vec(),
        "shake128" | "shake-128" => hash::shake128(&message, args.output_bytes.unwrap()),
        "shake256" | "shake-256" => hash::shake256(&message, args.output_bytes.unwrap()),
        _ => return Err(format!("unsupported hash algorithm: {}", args.algorithm).into()),
    };
    let report = DigestReport {
        status: "ok",
        algorithm,
        input_bytes: message.len(),
        output_bytes: digest.len(),
        digest_hex: hex::encode(digest),
    };
    out.emit(&report, || report.digest_hex.clone())
}

fn read_file_input(path: &Path) -> Result<Vec<u8>, String> {
    let spec = path
        .to_str()
        .filter(|s| s.starts_with("store:") || s.starts_with("sha256:"));
    let resolved = if let Some(spec) = spec {
        let binary = std::env::var_os("CRAX_CRYPTO_BIN").unwrap_or_else(|| "crypto".into());
        let output = Command::new(&binary)
            .args(["store", "pull", spec])
            .output()
            .map_err(|e| format!("starting {} for {spec}: {e}", binary.to_string_lossy()))?;
        if !output.status.success() {
            return Err(format!(
                "resolving {spec}: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            ));
        }
        let stdout = String::from_utf8(output.stdout)
            .map_err(|e| format!("store pull returned a non-UTF-8 path: {e}"))?;
        let cached = stdout.trim_end_matches(['\r', '\n']);
        if cached.is_empty() || cached.contains('\r') || cached.contains('\n') {
            return Err("store pull returned an invalid cache path".into());
        }
        PathBuf::from(cached)
    } else {
        path.to_path_buf()
    };
    std::fs::read(&resolved).map_err(|e| format!("reading {}: {e}", path.display()))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sha_family_known_answers() {
        assert_eq!(
            hex::encode(hash::sha256(b"abc")),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
        assert_eq!(
            hex::encode(hash::sha3_256(b"abc")),
            "3a985da74fe225b2045c172d6bd390bd855f086e3e9d525b46bfe24511431532"
        );
    }
}
