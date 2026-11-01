//! Direct hash and extendable-output computation for the unified CLI.

use clap::Args;
use serde::Serialize;
use std::{
    fs::File,
    io::Read,
    path::{Path, PathBuf},
    process::Command,
};

use super::output::{CmdResult, Out};
use crate::hash;

#[derive(Args, Clone, Debug)]
pub struct DigestArgs {
    /// Digest name: md4, md5, sha1, sha224, sha256, sha384, sha512,
    /// sha512-224, sha512-256, sha3-224, sha3-256, sha3-384, sha3-512,
    /// shake128, shake256, blake3, blake2b, blake2s, cshake128, cshake256,
    /// sm3, ripemd160, streebog-256/512, whirlpool, tiger, tiger2, or skein256/512/1024.
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
    /// Required for SHAKE/cSHAKE; optional for BLAKE2 and Skein.
    #[arg(long)]
    pub output_bytes: Option<usize>,
    /// cSHAKE customization bytes in hexadecimal.
    #[arg(long)]
    pub custom_hex: Option<String>,
    /// cSHAKE function-name bytes in hexadecimal.
    #[arg(long)]
    pub function_name_hex: Option<String>,
}

#[derive(Serialize)]
struct DigestReport {
    status: &'static str,
    algorithm: String,
    input_bytes: u64,
    output_bytes: usize,
    digest_hex: String,
}

pub fn run(out: Out, args: &DigestArgs) -> CmdResult {
    let algorithm = args.algorithm.to_ascii_lowercase().replace('_', "-");
    let xof = matches!(
        algorithm.as_str(),
        "shake128" | "shake-128" | "shake256" | "shake-256" | "cshake128" | "cshake256"
    );
    if xof && !matches!(args.output_bytes, Some(1..=1_048_576)) {
        return Err("SHAKE/cSHAKE requires --output-bytes in 1..=1048576".into());
    }
    let variable = xof
        || matches!(
            algorithm.as_str(),
            "blake2b" | "blake2s" | "skein256" | "skein512" | "skein1024"
        );
    if !variable && args.output_bytes.is_some() {
        return Err("--output-bytes applies only to SHAKE, cSHAKE, BLAKE2, and Skein".into());
    }
    let cshake = matches!(algorithm.as_str(), "cshake128" | "cshake256");
    if !cshake && (args.custom_hex.is_some() || args.function_name_hex.is_some()) {
        return Err("--custom-hex and --function-name-hex apply only to cSHAKE".into());
    }
    if is_sibling_hash(&algorithm) {
        let (digest, input_bytes) = sibling_digest(args, &algorithm)?;
        let report = DigestReport {
            status: "ok",
            algorithm,
            input_bytes,
            output_bytes: digest.len(),
            digest_hex: hex::encode(digest),
        };
        return out.emit(&report, || report.digest_hex.clone());
    }
    let (digest, input_bytes) = match (&args.text, &args.hex, &args.file) {
        (Some(text), None, None) => (
            digest_one_shot(&algorithm, text.as_bytes(), args.output_bytes)?,
            text.len() as u64,
        ),
        (None, Some(hex), None) => {
            let message = hex::decode(hex).map_err(|e| format!("invalid --hex input: {e}"))?;
            let digest = digest_one_shot(&algorithm, &message, args.output_bytes)?;
            (digest, message.len() as u64)
        }
        (None, None, Some(path)) => stream_file_input(path, &algorithm, args.output_bytes)?,
        _ => return Err("provide exactly one of --text, --hex, or --file".into()),
    };
    let report = DigestReport {
        status: "ok",
        algorithm,
        input_bytes,
        output_bytes: digest.len(),
        digest_hex: hex::encode(digest),
    };
    out.emit(&report, || report.digest_hex.clone())
}

fn is_sibling_hash(algorithm: &str) -> bool {
    matches!(
        algorithm,
        "blake2b"
            | "blake2s"
            | "cshake128"
            | "cshake256"
            | "sm3"
            | "ripemd160"
            | "streebog-256"
            | "streebog-512"
            | "whirlpool"
            | "tiger"
            | "tiger2"
            | "skein256"
            | "skein512"
            | "skein1024"
    )
}

/// The sibling crypto CLI owns these extra hash engines and their bounded
/// file path. Pass arguments directly, without a shell or whole-file buffer.
fn sibling_digest(args: &DigestArgs, algorithm: &str) -> Result<(Vec<u8>, u64), String> {
    let binary = super::sibling_binary("CRAX_CRYPTO_BIN", "crypto");
    let mut command = Command::new(&binary);
    command.args(["hash", algorithm, "--color", "never"]);
    let input_bytes = match (&args.text, &args.hex, &args.file) {
        (Some(text), None, None) => {
            command.args(["--hex", &hex::encode(text.as_bytes())]);
            text.len() as u64
        }
        (None, Some(encoded), None) => {
            let bytes = hex::decode(encoded).map_err(|e| format!("invalid --hex input: {e}"))?;
            command.args(["--hex", &hex::encode(&bytes)]);
            bytes.len() as u64
        }
        (None, None, Some(path)) => {
            let resolved = resolve_checked_path(path)?;
            let count = std::fs::metadata(&resolved)
                .map_err(|e| format!("reading {}: {e}", path.display()))?
                .len();
            command.arg("--file").arg(resolved);
            count
        }
        _ => return Err("provide exactly one of --text, --hex, or --file".into()),
    };
    if let Some(length) = args.output_bytes {
        command.args(["--output-bytes", &length.to_string()]);
    }
    if let Some(custom) = &args.custom_hex {
        hex::decode(custom).map_err(|e| format!("invalid --custom-hex: {e}"))?;
        command.args(["--custom-hex", custom]);
    }
    if let Some(name) = &args.function_name_hex {
        hex::decode(name).map_err(|e| format!("invalid --function-name-hex: {e}"))?;
        command.args(["--function-name-hex", name]);
    }
    let output = command
        .output()
        .map_err(|e| format!("starting {} for {algorithm}: {e}", binary.to_string_lossy()))?;
    if !output.status.success() {
        return Err(format!(
            "{algorithm}: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    let stdout = String::from_utf8(output.stdout)
        .map_err(|e| format!("{algorithm} returned non-UTF-8 output: {e}"))?;
    let digest = stdout.trim();
    if digest.is_empty() || digest.contains(char::is_whitespace) {
        return Err(format!("{algorithm} returned an invalid digest"));
    }
    let bytes = hex::decode(digest)
        .map_err(|e| format!("{algorithm} returned an invalid hex digest: {e}"))?;
    Ok((bytes, input_bytes))
}

fn digest_one_shot(
    algorithm: &str,
    message: &[u8],
    output_bytes: Option<usize>,
) -> Result<Vec<u8>, String> {
    let digest: Vec<u8> = match algorithm {
        "md4" => hash::md4(message).to_vec(),
        "md5" => hash::md5(message).to_vec(),
        "sha1" | "sha-1" => hash::sha1(message).to_vec(),
        "sha224" | "sha-224" => hash::sha224(message).to_vec(),
        "sha256" | "sha-256" => hash::sha256(message).to_vec(),
        "sha384" | "sha-384" => hash::sha384(message).to_vec(),
        "sha512" | "sha-512" => hash::sha512(message).to_vec(),
        "sha512-224" | "sha-512-224" => hash::sha512_224(message).to_vec(),
        "sha512-256" | "sha-512-256" => hash::sha512_256(message).to_vec(),
        "sha3-224" | "sha-3-224" => hash::sha3_224(message).to_vec(),
        "sha3-256" | "sha-3-256" | "sha3" | "sha-3" => hash::sha3_256(message).to_vec(),
        "sha3-384" | "sha-3-384" => hash::sha3_384(message).to_vec(),
        "sha3-512" | "sha-3-512" => hash::sha3_512(message).to_vec(),
        "shake128" | "shake-128" => hash::shake128(message, output_bytes.unwrap()),
        "shake256" | "shake-256" => hash::shake256(message, output_bytes.unwrap()),
        "blake3" => hash::blake3_hash(message).to_vec(),
        _ => return Err(format!("unsupported hash algorithm: {algorithm}")),
    };
    Ok(digest)
}

/// MD4 and MD5 share block size, byte order, padding, and initial state.
struct Merkle64 {
    md5: bool,
    state: [u32; 4],
    block: [u8; 64],
    filled: usize,
    length: u64,
}

impl Merkle64 {
    fn new(md5: bool) -> Self {
        Self {
            md5,
            state: crate::cryptanalysis::md5_differential::MD5_IV,
            block: [0; 64],
            filled: 0,
            length: 0,
        }
    }

    fn compress(&mut self, block: &[u8; 64]) {
        if self.md5 {
            crate::cryptanalysis::md5_differential::md5_compress(&mut self.state, block, 64);
        } else {
            hash::md4_compress(&mut self.state, block);
        }
    }

    fn update(&mut self, mut data: &[u8]) {
        self.length = self.length.wrapping_add(data.len() as u64);
        if self.filled > 0 {
            let take = data.len().min(64 - self.filled);
            self.block[self.filled..self.filled + take].copy_from_slice(&data[..take]);
            self.filled += take;
            data = &data[take..];
            if self.filled < 64 {
                return;
            }
            let block = self.block;
            self.compress(&block);
            self.filled = 0;
        }
        for chunk in data.chunks_exact(64) {
            let mut block = [0u8; 64];
            block.copy_from_slice(chunk);
            self.compress(&block);
        }
        let whole = data.len() - data.len() % 64;
        self.filled = data.len() - whole;
        self.block[..self.filled].copy_from_slice(&data[whole..]);
    }

    fn finalize(mut self) -> [u8; 16] {
        let mut tail = [0u8; 128];
        tail[..self.filled].copy_from_slice(&self.block[..self.filled]);
        tail[self.filled] = 0x80;
        let end = if self.filled < 56 { 64 } else { 128 };
        tail[end - 8..end].copy_from_slice(&self.length.wrapping_mul(8).to_le_bytes());
        for chunk in tail[..end].chunks_exact(64) {
            let mut block = [0u8; 64];
            block.copy_from_slice(chunk);
            self.compress(&block);
        }
        let mut out = [0u8; 16];
        for (i, word) in self.state.iter().enumerate() {
            out[i * 4..i * 4 + 4].copy_from_slice(&word.to_le_bytes());
        }
        out
    }
}

enum StreamingDigest {
    Md(Merkle64),
    Fixed(Box<dyn sha1::digest::DynDigest>),
    Shake128(sha3::Shake128, usize),
    Shake256(sha3::Shake256, usize),
    Blake3(Box<blake3::Hasher>),
}

impl StreamingDigest {
    fn for_algorithm(algorithm: &str, output_bytes: Option<usize>) -> Result<Self, String> {
        if algorithm == "md4" {
            return Ok(Self::Md(Merkle64::new(false)));
        }
        if algorithm == "md5" {
            return Ok(Self::Md(Merkle64::new(true)));
        }
        let fixed: Option<Box<dyn sha1::digest::DynDigest>> = match algorithm {
            "sha1" | "sha-1" => Some(Box::new(sha1::Sha1::default())),
            "sha224" | "sha-224" => Some(Box::new(sha2::Sha224::default())),
            "sha256" | "sha-256" => Some(Box::new(sha2::Sha256::default())),
            "sha384" | "sha-384" => Some(Box::new(sha2::Sha384::default())),
            "sha512" | "sha-512" => Some(Box::new(sha2::Sha512::default())),
            "sha512-224" | "sha-512-224" => Some(Box::new(sha2::Sha512_224::default())),
            "sha512-256" | "sha-512-256" => Some(Box::new(sha2::Sha512_256::default())),
            "sha3-224" | "sha-3-224" => Some(Box::new(sha3::Sha3_224::default())),
            "sha3-256" | "sha-3-256" | "sha3" | "sha-3" => {
                Some(Box::new(sha3::Sha3_256::default()))
            }
            "sha3-384" | "sha-3-384" => Some(Box::new(sha3::Sha3_384::default())),
            "sha3-512" | "sha-3-512" => Some(Box::new(sha3::Sha3_512::default())),
            _ => None,
        };
        if let Some(fixed) = fixed {
            return Ok(Self::Fixed(fixed));
        }
        match algorithm {
            "shake128" | "shake-128" => Ok(Self::Shake128(
                sha3::Shake128::default(),
                output_bytes.unwrap(),
            )),
            "shake256" | "shake-256" => Ok(Self::Shake256(
                sha3::Shake256::default(),
                output_bytes.unwrap(),
            )),
            "blake3" => Ok(Self::Blake3(Box::new(blake3::Hasher::new()))),
            _ => Err(format!("unsupported hash algorithm: {algorithm}")),
        }
    }

    fn update(&mut self, bytes: &[u8]) {
        match self {
            Self::Md(state) => state.update(bytes),
            Self::Fixed(state) => state.update(bytes),
            Self::Shake128(state, _) => sha3::digest::Update::update(state, bytes),
            Self::Shake256(state, _) => sha3::digest::Update::update(state, bytes),
            Self::Blake3(state) => {
                state.update(bytes);
            }
        }
    }

    fn finalize(self) -> Vec<u8> {
        match self {
            Self::Md(state) => state.finalize().to_vec(),
            Self::Fixed(state) => state.finalize().to_vec(),
            Self::Shake128(state, length) => {
                let mut out = vec![0; length];
                let mut reader = sha3::digest::ExtendableOutput::finalize_xof(state);
                sha3::digest::XofReader::read(&mut reader, &mut out);
                out
            }
            Self::Shake256(state, length) => {
                let mut out = vec![0; length];
                let mut reader = sha3::digest::ExtendableOutput::finalize_xof(state);
                sha3::digest::XofReader::read(&mut reader, &mut out);
                out
            }
            Self::Blake3(state) => state.finalize().as_bytes().to_vec(),
        }
    }
}

fn stream_file_input(
    path: &Path,
    algorithm: &str,
    output_bytes: Option<usize>,
) -> Result<(Vec<u8>, u64), String> {
    let mut state = StreamingDigest::for_algorithm(algorithm, output_bytes)?;
    let resolved = resolve_checked_path(path)?;
    let mut file = File::open(&resolved).map_err(|e| format!("reading {}: {e}", path.display()))?;
    let mut buffer = [0u8; 64 * 1024];
    let mut input_bytes = 0u64;
    loop {
        let count = file
            .read(&mut buffer)
            .map_err(|e| format!("reading {}: {e}", path.display()))?;
        if count == 0 {
            break;
        }
        input_bytes = input_bytes
            .checked_add(count as u64)
            .ok_or("input byte count overflow")?;
        state.update(&buffer[..count]);
    }
    Ok((state.finalize(), input_bytes))
}

pub(crate) fn is_store_ref(path: &Path) -> bool {
    path.to_str()
        .is_some_and(|s| s.starts_with("store:") || s.starts_with("sha256:"))
}

pub(crate) fn resolve_checked_path(path: &Path) -> Result<PathBuf, String> {
    let spec = path.to_str().filter(|_| is_store_ref(path));
    let resolved = if let Some(spec) = spec {
        let binary = super::sibling_binary("CRAX_CRYPTO_BIN", "crypto");
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
    Ok(resolved)
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

    #[test]
    fn streamed_file_matches_native_hashes_at_block_boundaries() {
        let path = std::env::temp_dir().join(format!(
            "crax-hash-stream-{}-{}.bin",
            std::process::id(),
            std::thread::current().name().unwrap_or("test")
        ));
        for size in [0, 1, 55, 56, 63, 64, 65, 111, 112, 127, 128, 129, 65_537] {
            let bytes: Vec<u8> = (0..size).map(|i| (i * 37 + size) as u8).collect();
            std::fs::write(&path, &bytes).unwrap();
            for name in [
                "md4",
                "md5",
                "sha1",
                "sha224",
                "sha256",
                "sha384",
                "sha512",
                "sha512-224",
                "sha512-256",
                "sha3-224",
                "sha3-256",
                "sha3-384",
                "sha3-512",
                "shake128",
                "shake256",
                "blake3",
            ] {
                let output_bytes = name.starts_with("shake").then_some(97);
                let (got, count) = stream_file_input(&path, name, output_bytes).unwrap();
                assert_eq!(count, size as u64);
                assert_eq!(
                    got,
                    digest_one_shot(name, &bytes, output_bytes).unwrap(),
                    "size={size} algorithm={name}"
                );
            }
        }
        std::fs::remove_file(path).unwrap();
    }
}
