//! Bounded AES-128 differential, linear, and integral key recovery.

use clap::{Args, ValueEnum};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::path::{Path, PathBuf};

use super::output::{CmdResult, Out};
use crate::cryptanalysis::aes::{differential, linear, square, ReducedAes128};

#[derive(Clone, Copy, Debug, ValueEnum)]
pub enum Technique {
    Differential,
    Linear,
    Square,
}

#[derive(Args, Clone, Debug)]
pub struct AesAttackArgs {
    /// Differential (2 rounds), linear (1 round), or square integral (4 rounds).
    #[arg(long, value_enum)]
    pub technique: Technique,
    /// AES-128 analysis key as exactly 32 hex digits.
    #[arg(long)]
    pub key_hex: Option<String>,
    /// Chosen pairs for differential or known pairs for linear.
    #[arg(long, conflicts_with = "pairs_file")]
    pub samples: Option<usize>,
    /// JSON corpus of captured reduced-round plaintext/ciphertext pairs.
    #[arg(long)]
    pub pairs_file: Option<PathBuf>,
    /// Write generated pairs as a versioned JSON corpus (file must be new).
    #[arg(long, conflicts_with = "pairs_file")]
    pub export_pairs_file: Option<PathBuf>,
    /// Reproducible pair generation seed.
    #[arg(long, default_value_t = 0xdead_beef_cafe)]
    pub seed: u64,
    /// Nonzero byte difference in the differential experiment.
    #[arg(long, default_value_t = 0x73)]
    pub alpha: u8,
}

const CIPHER_MODEL: &str = "aes128-reduced-final-no-mixcolumns/v1";
const MAX_CORPUS_BYTES: u64 = 64 * 1024 * 1024;

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Corpus<T> {
    schema_version: u32,
    cipher_model: String,
    technique: String,
    rounds: usize,
    pairs: Vec<T>,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct DifferentialPairJson {
    p0: String,
    p1: String,
    c0: String,
    c1: String,
}

#[derive(Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct LinearPairJson {
    plaintext: String,
    ciphertext: String,
}

fn block(hex_text: &str) -> Result<[u8; 16], String> {
    if hex_text.len() != 32 || !hex_text.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("each AES corpus block must be exactly 32 hex digits".into());
    }
    let bytes = hex::decode(hex_text).map_err(|e| e.to_string())?;
    bytes
        .try_into()
        .map_err(|_| "AES corpus block length differs".into())
}

fn analysis_key(args: &AesAttackArgs) -> Result<[u8; 16], String> {
    let value = args
        .key_hex
        .as_deref()
        .unwrap_or("914f6da1c78305bb2957ee104d826cfa");
    block(value).map_err(|_| "AES-128 analysis key must be exactly 32 hex digits".into())
}

fn load_corpus<T: for<'de> Deserialize<'de>>(
    path: &Path,
    technique: &str,
    rounds: usize,
) -> Result<Vec<T>, String> {
    use std::io::Read;
    let resolved = super::digest::resolve_checked_path(path)?;
    let size = std::fs::metadata(&resolved)
        .map_err(|e| format!("cannot stat {}: {e}", path.display()))?
        .len();
    if size > MAX_CORPUS_BYTES {
        return Err("AES corpus exceeds 64 MiB".into());
    }
    let mut bytes = Vec::new();
    std::fs::File::open(&resolved)
        .map_err(|e| format!("cannot read {}: {e}", path.display()))?
        .take(MAX_CORPUS_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| format!("cannot read {}: {e}", path.display()))?;
    if bytes.len() as u64 > MAX_CORPUS_BYTES {
        return Err("AES corpus exceeds 64 MiB".into());
    }
    let corpus: Corpus<T> =
        serde_json::from_slice(&bytes).map_err(|e| format!("invalid AES corpus: {e}"))?;
    if corpus.schema_version != 1
        || corpus.cipher_model != CIPHER_MODEL
        || corpus.technique != technique
        || corpus.rounds != rounds
    {
        return Err("AES corpus schema, model, technique, or round count differs".into());
    }
    if !(1..=1_000_000).contains(&corpus.pairs.len()) {
        return Err("AES corpus must contain 1..=1000000 pairs".into());
    }
    Ok(corpus.pairs)
}

fn write_corpus<T: Serialize>(
    path: &Path,
    technique: &str,
    rounds: usize,
    pairs: Vec<T>,
) -> Result<(), String> {
    use std::io::Write;
    if super::digest::is_store_ref(path) {
        return Err("export pairs to a local file, then publish it with crypto store push".into());
    }
    let bytes = serde_json::to_vec_pretty(&Corpus {
        schema_version: 1,
        cipher_model: CIPHER_MODEL.to_string(),
        technique: technique.to_string(),
        rounds,
        pairs,
    })
    .map_err(|e| e.to_string())?;
    if bytes.len() as u64 > MAX_CORPUS_BYTES {
        return Err("generated AES corpus exceeds 64 MiB".into());
    }
    let mut file = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|e| format!("cannot create {}: {e}", path.display()))?;
    file.write_all(&bytes).map_err(|e| e.to_string())?;
    file.sync_all().map_err(|e| e.to_string())
}

pub fn run(out: Out, args: &AesAttackArgs) -> CmdResult {
    let sample_count = args.samples.unwrap_or(4096);
    if args.pairs_file.is_none() && !(1..=1_000_000).contains(&sample_count) {
        return Err("samples must be in 1..=1000000".into());
    }
    if (args.pairs_file.is_some() || args.export_pairs_file.is_some())
        && matches!(args.technique, Technique::Square)
    {
        return Err("square recovery needs an encryption oracle; pairs files support differential and linear only".into());
    }
    let report = match args.technique {
        Technique::Differential => {
            if args.alpha == 0 {
                return Err("alpha must be nonzero".into());
            }
            let reference_key = args
                .key_hex
                .as_ref()
                .map(|_| analysis_key(args))
                .transpose()?;
            let pairs = if let Some(path) = &args.pairs_file {
                load_corpus::<DifferentialPairJson>(path, "differential", 2)?
                    .into_iter()
                    .map(|pair| {
                        Ok(differential::DiffPair {
                            p0: block(&pair.p0)?,
                            p1: block(&pair.p1)?,
                            c0: block(&pair.c0)?,
                            c1: block(&pair.c1)?,
                        })
                    })
                    .collect::<Result<Vec<_>, String>>()?
            } else {
                let key = analysis_key(args)?;
                let cipher = ReducedAes128::new(&key, 2, false);
                differential::build_pairs(&cipher, args.alpha, sample_count, args.seed)
            };
            if pairs.iter().any(|pair| {
                let mut expected = pair.p0;
                expected[0] ^= args.alpha;
                expected != pair.p1
            }) {
                return Err(
                    "differential corpus has a pair with the wrong plaintext difference".into(),
                );
            }
            if let Some(path) = &args.export_pairs_file {
                write_corpus(
                    path,
                    "differential",
                    2,
                    pairs
                        .iter()
                        .map(|pair| DifferentialPairJson {
                            p0: hex::encode(pair.p0),
                            p1: hex::encode(pair.p1),
                            c0: hex::encode(pair.c0),
                            c1: hex::encode(pair.c1),
                        })
                        .collect(),
                )?;
            }
            let ddt = differential::aes_sbox_ddt();
            let found = differential::key_recovery_two_round(args.alpha, &pairs, &ddt)
                .map_err(|e| format!("bounded differential recovery: {e}"))?;
            let constraints_verified = differential::validate_two_round_key_bytes(
                args.alpha,
                &pairs,
                &found.key_bytes,
                &ddt,
            );
            let reference_verified = if args.pairs_file.is_none() || reference_key.is_some() {
                let key = reference_key.unwrap_or(analysis_key(args)?);
                let cipher = ReducedAes128::new(&key, 2, false);
                Some(
                    pairs.iter().all(|pair| {
                        cipher.encrypt(&pair.p0) == pair.c0 && cipher.encrypt(&pair.p1) == pair.c1
                    }) && found
                        .key_bytes
                        .iter()
                        .all(|&(pos, byte)| cipher.round_key(2)[pos / 4][pos % 4] == byte),
                )
            } else {
                None
            };
            let accepted = constraints_verified && reference_verified.unwrap_or(true);
            json!({
                "status": if !accepted { "verification_failed" } else if reference_verified.is_some() { "solved" } else { "candidate" },
                "technique": "differential",
                "rounds": 2,
                "pairs_used": found.pairs_used,
                "trials": found.trial_count,
                "recovered_last_round_key_bytes": found.key_bytes,
                "recovery_scope": "four_last_round_bytes",
                "source": if args.pairs_file.is_some() { "external_corpus" } else { "generated" },
                "constraints_verified": constraints_verified,
                "verified": reference_verified,
                "accepted": accepted,
            })
        }
        Technique::Linear => {
            let pairs = if let Some(path) = &args.pairs_file {
                load_corpus::<LinearPairJson>(path, "linear", 1)?
                    .into_iter()
                    .map(|pair| Ok((block(&pair.plaintext)?, block(&pair.ciphertext)?)))
                    .collect::<Result<Vec<_>, String>>()?
            } else {
                let key = analysis_key(args)?;
                let cipher = ReducedAes128::new(&key, 1, false);
                linear::known_plaintext_corpus(&cipher, sample_count, args.seed)
            };
            if let Some(path) = &args.export_pairs_file {
                write_corpus(
                    path,
                    "linear",
                    1,
                    pairs
                        .iter()
                        .map(|(p, c)| LinearPairJson {
                            plaintext: hex::encode(p),
                            ciphertext: hex::encode(c),
                        })
                        .collect(),
                )?;
            }
            let lat = linear::aes_sbox_lat();
            let mut recovered = [0u8; 16];
            for c in 0..4 {
                for r in 0..4 {
                    let byte = linear::recover_key_byte_one_round(&pairs, (c, r), &lat)
                        .ok_or_else(|| format!("bounded linear recovery at ({c},{r})"))?;
                    recovered[4 * ((c + r) % 4) + r] = byte;
                }
            }
            let cipher = ReducedAes128::new(&recovered, 1, false);
            let replay_verified = pairs.iter().all(|(p, c)| cipher.encrypt(p) == *c);
            let reference_verified = args
                .key_hex
                .as_ref()
                .map(|_| analysis_key(args))
                .transpose()?
                .map(|key| recovered == key);
            let verified = replay_verified && reference_verified.unwrap_or(true);
            json!({
                "status": if verified { "solved" } else { "verification_failed" },
                "technique": "linear",
                "rounds": 1,
                "pairs_used": pairs.len(),
                "recovered_master_key_hex": hex::encode(recovered),
                "source": if args.pairs_file.is_some() { "external_corpus" } else { "generated" },
                "replay_verified": replay_verified,
                "reference_verified": reference_verified,
                "verified": verified,
                "accepted": verified,
            })
        }
        Technique::Square => {
            let key = analysis_key(args)?;
            let cipher = ReducedAes128::new(&key, 4, false);
            let found = square::key_recovery_four_round(|p| cipher.encrypt(p));
            let verified = found.master_key == key;
            json!({
                "status": if verified { "solved" } else { "verification_failed" },
                "technique": "square",
                "rounds": 4,
                "lambda_sets_used": found.lambda_sets_used,
                "sbox_lookups": found.sbox_lookups,
                "recovered_master_key_hex": hex::encode(found.master_key),
                "verified": verified,
                "accepted": verified,
            })
        }
    };
    let text = format!("{}", serde_json::to_string_pretty(&report).unwrap());
    out.report(&report, text)?;
    if report["accepted"] != true {
        return Err(super::output::Failure::reported(
            "AES recovery failed corpus constraints or key verification",
        ));
    }
    Ok(())
}
