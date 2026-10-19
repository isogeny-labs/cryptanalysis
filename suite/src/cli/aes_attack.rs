//! Bounded AES-128 differential, linear, and integral key recovery.

use clap::{Args, ValueEnum};
use serde_json::json;

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
    #[arg(long, default_value = "914f6da1c78305bb2957ee104d826cfa")]
    pub key_hex: String,
    /// Chosen pairs for differential or known pairs for linear.
    #[arg(long, default_value_t = 4096)]
    pub samples: usize,
    /// Reproducible pair generation seed.
    #[arg(long, default_value_t = 0xdead_beef_cafe)]
    pub seed: u64,
    /// Nonzero byte difference in the differential experiment.
    #[arg(long, default_value_t = 0x73)]
    pub alpha: u8,
}

pub fn run(out: Out, args: &AesAttackArgs) -> CmdResult {
    let key_bytes = hex::decode(&args.key_hex).map_err(|e| format!("invalid AES key hex: {e}"))?;
    let key: [u8; 16] = key_bytes
        .try_into()
        .map_err(|_| "AES-128 key must be exactly 16 bytes")?;
    if !(1..=1_000_000).contains(&args.samples) {
        return Err("samples must be in 1..=1000000".into());
    }
    let report = match args.technique {
        Technique::Differential => {
            if args.alpha == 0 {
                return Err("alpha must be nonzero".into());
            }
            let cipher = ReducedAes128::new(&key, 2, false);
            let pairs = differential::build_pairs(&cipher, args.alpha, args.samples, args.seed);
            let ddt = differential::aes_sbox_ddt();
            let found = differential::key_recovery_two_round(args.alpha, &pairs, &ddt)
                .map_err(|e| format!("bounded differential recovery: {e}"))?;
            let actual = cipher.round_key(2);
            let verified = found
                .key_bytes
                .iter()
                .all(|&(pos, byte)| actual[pos / 4][pos % 4] == byte);
            json!({
                "status": if verified { "solved" } else { "verification_failed" },
                "technique": "differential",
                "rounds": 2,
                "pairs_used": found.pairs_used,
                "trials": found.trial_count,
                "recovered_last_round_key_bytes": found.key_bytes,
                "verified": verified,
            })
        }
        Technique::Linear => {
            let cipher = ReducedAes128::new(&key, 1, false);
            let pairs = linear::known_plaintext_corpus(&cipher, args.samples, args.seed);
            let lat = linear::aes_sbox_lat();
            let mut recovered = [0u8; 16];
            for c in 0..4 {
                for r in 0..4 {
                    let byte = linear::recover_key_byte_one_round(&pairs, (c, r), &lat)
                        .ok_or_else(|| format!("bounded linear recovery at ({c},{r})"))?;
                    recovered[4 * ((c + r) % 4) + r] = byte;
                }
            }
            let verified = recovered == key;
            json!({
                "status": if verified { "solved" } else { "verification_failed" },
                "technique": "linear",
                "rounds": 1,
                "pairs_used": args.samples,
                "recovered_master_key_hex": hex::encode(recovered),
                "verified": verified,
            })
        }
        Technique::Square => {
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
            })
        }
    };
    let text = format!("{}", serde_json::to_string_pretty(&report).unwrap());
    out.report(&report, text)?;
    if report["verified"] != true {
        return Err(super::output::Failure::reported(
            "AES recovery failed independent key verification",
        ));
    }
    Ok(())
}
