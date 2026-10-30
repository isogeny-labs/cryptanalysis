use anyhow::Result;
use clap::{Parser, Subcommand};
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::PathBuf;
#[derive(Parser)]
#[command(about = "Binary transfer audit with replayable, explicitly scoped coverage certificates")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    /// Classify the supplied curve within implemented families; never asserts universal exclusion.
    Audit {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    /// Recompute every field of a certificate. Same implementation replay, not independent geometry proof.
    Verify {
        #[arg(long)]
        certificate: PathBuf,
    },
}
fn main() -> Result<()> {
    match Cli::parse().command {
        Command::Audit { input, output } => {
            let input = serde_json::from_slice(&fs::read(input)?)?;
            let c = transfer_audit::audit(&input)?;
            let data = serde_json::to_vec_pretty(&c)?;
            if let Some(p) = output {
                let mut f = OpenOptions::new().write(true).create_new(true).open(p)?;
                f.write_all(&data)?;
                f.write_all(b"\n")?;
                f.sync_all()?;
            } else {
                println!("{}", String::from_utf8(data)?);
            }
        }
        Command::Verify { certificate } => {
            transfer_audit::verify(&serde_json::from_slice(&fs::read(certificate)?)?)?;
            println!("certificate replay passed");
        }
    }
    Ok(())
}
