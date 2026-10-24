//! Bounded AES-128 differential, linear, and integral key recovery.

use clap::{Args, ValueEnum};
use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::{BTreeMap, HashSet};
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
    /// Separate held-out four-round Square corpus for independent replay.
    #[arg(long, requires = "pairs_file")]
    pub verification_file: Option<PathBuf>,
    /// Export a separate held-out Square lambda set (file must be new).
    #[arg(long, requires = "export_pairs_file", conflicts_with = "pairs_file")]
    pub export_verification_file: Option<PathBuf>,
    /// Complete Square training lambda sets to generate (1..=6).
    #[arg(long, default_value_t = 3)]
    pub square_sets: usize,
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

fn square_pairs_from_file(path: &Path) -> Result<Vec<([u8; 16], [u8; 16])>, String> {
    load_corpus::<LinearPairJson>(path, "square", 4)?
        .into_iter()
        .map(|pair| Ok((block(&pair.plaintext)?, block(&pair.ciphertext)?)))
        .collect()
}

fn square_generated_pairs(
    cipher: &ReducedAes128,
    seed: u64,
    first_set: usize,
    count: usize,
) -> Vec<([u8; 16], [u8; 16])> {
    (first_set..first_set + count)
        .flat_map(|index| {
            let base = [seed.wrapping_add(index as u64) as u8; 16];
            square::lambda_set(&base, 0)
                .into_iter()
                .map(|plaintext| {
                    let ciphertext = cipher.encrypt(&plaintext);
                    (plaintext, ciphertext)
                })
                .collect::<Vec<_>>()
        })
        .collect()
}

fn square_pair_json(pairs: &[([u8; 16], [u8; 16])]) -> Vec<LinearPairJson> {
    pairs
        .iter()
        .map(|(plaintext, ciphertext)| LinearPairJson {
            plaintext: hex::encode(plaintext),
            ciphertext: hex::encode(ciphertext),
        })
        .collect()
}

fn square_ciphertext_sets(pairs: &[([u8; 16], [u8; 16])]) -> Result<Vec<Vec<[u8; 16]>>, String> {
    if !(256..=1536).contains(&pairs.len()) || pairs.len() % 256 != 0 {
        return Err("Square recovery needs 1..=6 complete lambda sets".into());
    }
    let mut grouped: BTreeMap<[u8; 15], Vec<Option<[u8; 16]>>> = BTreeMap::new();
    for (plaintext, ciphertext) in pairs {
        let fixed: [u8; 15] = plaintext[1..].try_into().expect("AES block length");
        let slots = grouped.entry(fixed).or_insert_with(|| vec![None; 256]);
        if slots[plaintext[0] as usize].replace(*ciphertext).is_some() {
            return Err("Square training plaintexts must be distinct".into());
        }
    }
    if grouped.len() != pairs.len() / 256
        || grouped.values().any(|set| set.iter().any(Option::is_none))
    {
        return Err("each Square lambda set must cover all 256 values of plaintext byte 0".into());
    }
    Ok(grouped
        .into_values()
        .map(|slots| slots.into_iter().map(Option::unwrap).collect())
        .collect())
}

pub fn run(out: Out, args: &AesAttackArgs) -> CmdResult {
    let sample_count = args.samples.unwrap_or(4096);
    if args.pairs_file.is_none() && !(1..=1_000_000).contains(&sample_count) {
        return Err("samples must be in 1..=1000000".into());
    }
    if !matches!(args.technique, Technique::Square)
        && (args.verification_file.is_some() || args.export_verification_file.is_some())
    {
        return Err("separate verification files currently require --technique square".into());
    }
    if args.export_pairs_file.is_some() && args.export_pairs_file == args.export_verification_file {
        return Err("training and verification export paths must differ".into());
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
            if !(1..=6).contains(&args.square_sets) {
                return Err("square-sets must be in 1..=6".into());
            }
            let reference_key = args
                .key_hex
                .as_ref()
                .map(|_| analysis_key(args))
                .transpose()?;
            let source_key = if args.pairs_file.is_none() {
                Some(analysis_key(args)?)
            } else {
                None
            };
            let pairs = if let Some(path) = &args.pairs_file {
                square_pairs_from_file(path)?
            } else {
                let cipher = ReducedAes128::new(&source_key.expect("generated key"), 4, false);
                square_generated_pairs(&cipher, args.seed, 0, args.square_sets)
            };
            if let Some(path) = &args.export_pairs_file {
                write_corpus(path, "square", 4, square_pair_json(&pairs))?;
            }
            let sets = square_ciphertext_sets(&pairs)?;
            let found = square::key_recovery_four_round_from_captured(&sets)?;
            let recovered_cipher = ReducedAes128::new(&found.master_key, 4, false);
            let training_matches = pairs
                .iter()
                .filter(|(p, c)| recovered_cipher.encrypt(p) == *c)
                .count();
            let verification_pairs = if let Some(path) = &args.verification_file {
                square_pairs_from_file(path)?
            } else if args.export_verification_file.is_some() {
                let cipher = ReducedAes128::new(&source_key.expect("generated key"), 4, false);
                square_generated_pairs(&cipher, args.seed, args.square_sets, 1)
            } else {
                Vec::new()
            };
            if verification_pairs.len() > 100_000 {
                return Err("Square verification corpus exceeds 100000 pairs".into());
            }
            if let Some(path) = &args.export_verification_file {
                write_corpus(path, "square", 4, square_pair_json(&verification_pairs))?;
            }
            let mut seen = HashSet::new();
            for (p, _) in pairs.iter().chain(&verification_pairs) {
                if !seen.insert(*p) {
                    return Err("Square verification plaintexts must be distinct from training and each other".into());
                }
            }
            let verification_matches = verification_pairs
                .iter()
                .filter(|(p, c)| recovered_cipher.encrypt(p) == *c)
                .count();
            let reference_verified = reference_key
                .or(source_key)
                .map(|key| key == found.master_key);
            let accepted = training_matches == pairs.len()
                && verification_matches == verification_pairs.len()
                && reference_verified.unwrap_or(true);
            json!({
                "status": if !accepted { "verification_failed" } else if !verification_pairs.is_empty() { "verified" } else if args.pairs_file.is_some() { "candidate" } else { "solved" },
                "technique": "square",
                "rounds": 4,
                "lambda_sets_used": found.lambda_sets_used,
                "sbox_lookups": found.sbox_lookups,
                "recovered_master_key_hex": hex::encode(found.master_key),
                "recovered_last_round_key_hex":hex::encode(found.last_round_key.concat()),
                "source":if args.pairs_file.is_some() {"external_corpus"} else {"generated"},
                "training_pairs":pairs.len(),
                "training_matches":training_matches,
                "verification_pairs":verification_pairs.len(),
                "verification_matches":verification_matches,
                "replay_verified":training_matches == pairs.len(),
                "reference_verified":reference_verified,
                "verified":if args.pairs_file.is_some() && verification_pairs.is_empty() && reference_verified.is_none() {None} else {Some(accepted)},
                "accepted": accepted,
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn captured_square_sets_recover_key_and_reject_incomplete_or_corrupt_sets() {
        let key = [0x5bu8; 16];
        let cipher = ReducedAes128::new(&key, 4, false);
        let mut pairs = square_generated_pairs(&cipher, 0x25, 0, 3);
        let sets = square_ciphertext_sets(&pairs).unwrap();
        let found = square::key_recovery_four_round_from_captured(&sets).unwrap();
        assert_eq!(found.master_key, key);
        assert_eq!(found.lambda_sets_used, 3);
        assert!(pairs.iter().all(|(p, c)| cipher.encrypt(p) == *c));

        pairs.pop();
        assert!(square_ciphertext_sets(&pairs)
            .unwrap_err()
            .contains("complete"));
        pairs = square_generated_pairs(&cipher, 0x25, 0, 3);
        pairs[1].0 = pairs[0].0;
        assert!(square_ciphertext_sets(&pairs)
            .unwrap_err()
            .contains("distinct"));
        pairs = square_generated_pairs(&cipher, 0x25, 0, 3);
        pairs[0].1 = [0u8; 16];
        assert!(square::key_recovery_four_round_from_captured(
            &square_ciphertext_sets(&pairs).unwrap()
        )
        .is_err());
    }
}
