use anyhow::{ensure, Context, Result};
use clap::{Parser, Subcommand, ValueEnum};
use ghs_sweeper::{field::FieldCache, journal, runner, search};
use std::fs::{self, OpenOptions};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

#[derive(Parser)]
#[command(
    version,
    about = "Native Rust binary cover-candidate sweeper; spectral matches do not certify attacks or novelty"
)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}
#[derive(Subcommand)]
enum Command {
    /// Enumerate deterministic denominator jobs and exact planned coverage.
    Plan {
        #[arg(long)]
        config: PathBuf,
    },
    /// Create a new Rust SQLite journal, refusing to overwrite existing data.
    Init {
        #[arg(long)]
        config: PathBuf,
        #[arg(long)]
        db: PathBuf,
        #[arg(long, default_value = ".")]
        reference_root: PathBuf,
    },
    /// Resume pending jobs. A soft time limit finishes in-flight denominators.
    Run {
        #[arg(long)]
        db: PathBuf,
        #[arg(long,default_value_t=1,value_parser=clap::value_parser!(u32).range(1..=64))]
        workers: u32,
        #[arg(long)]
        max_jobs: Option<usize>,
        #[arg(long,value_parser=clap::value_parser!(u64).range(1..))]
        max_seconds: Option<u64>,
        #[arg(long)]
        retry_failed: bool,
    },
    /// Inspect a consistent committed snapshot, including partial coverage.
    Status {
        #[arg(long)]
        db: PathBuf,
    },
    /// Recheck positives with separate raw polynomial arithmetic.
    Verify {
        #[arg(long)]
        db: PathBuf,
        #[arg(long)]
        limit: Option<usize>,
    },
    /// Match elliptic source models and independently verify their orders.
    Sources {
        #[arg(long)]
        db: PathBuf,
        #[arg(long)]
        limit: Option<usize>,
    },
    /// Export provisional spectral models; never modifies the curve catalogue.
    Export {
        #[arg(long)]
        db: PathBuf,
        #[arg(long,value_enum,default_value_t=Format::Jsonl)]
        format: Format,
        #[arg(long)]
        output: Option<PathBuf>,
        #[arg(long)]
        needs_review: bool,
        #[arg(long)]
        unseen_source_classes: bool,
    },
    /// Attach a retained-reference assessment; does not certify novelty.
    Review {
        #[arg(long)]
        db: PathBuf,
        #[arg(long, visible_alias = "candidate")]
        model: String,
        #[arg(long)]
        record: PathBuf,
    },
    /// Report all divisors and write only engine-supported subfield choices.
    Subfields {
        #[arg(long)]
        absolute_degree: u32,
        #[arg(long)]
        output: Option<PathBuf>,
    },
    /// Preserve historical completed coverage from the earlier Python journal.
    /// Independent verification, source matching and reviews are reset for Rust.
    ImportPython {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        db: PathBuf,
        #[arg(long, default_value = ".")]
        reference_root: PathBuf,
    },
}
#[derive(Copy, Clone, ValueEnum)]
enum Format {
    Jsonl,
    Csv,
}
fn read<T: serde::de::DeserializeOwned>(path: &Path) -> Result<T> {
    serde_json::from_slice(&fs::read(path)?).with_context(|| format!("parse {}", path.display()))
}
fn print(value: &impl serde::Serialize) -> Result<()> {
    println!("{}", serde_json::to_string_pretty(value)?);
    Ok(())
}

fn execute() -> Result<i32> {
    let cli = Cli::parse();
    let fields = FieldCache::default();
    match cli.command {
        Command::Plan { config } => {
            let (plan, _) = search::make_plan(read(&config)?, &fields)?;
            print(&plan)?;
        }
        Command::Init {
            config,
            db,
            reference_root,
        } => {
            ensure!(
                !db.exists(),
                "journal already exists; use run to resume or choose another path"
            );
            let (plan, jobs) = search::make_plan(read(&config)?, &fields)?;
            let _lock = journal::WriterLock::acquire(&db)?;
            journal::initialize(&db, &plan, &jobs, &reference_root)?;
            print(&plan)?;
        }
        Command::Run {
            db,
            workers,
            max_jobs,
            max_seconds,
            retry_failed,
        } => {
            let _lock = journal::WriterLock::acquire(&db)?;
            let mut c = journal::open(&db, false)?;
            let stop = Arc::new(AtomicBool::new(false));
            let control = Arc::clone(&stop);
            ctrlc::set_handler(move || {
                if control.swap(true, Ordering::Relaxed) {
                    std::process::exit(130);
                }
                eprintln!("stopping after in-flight jobs; interrupt again to abort");
            })?;
            let result = runner::run(
                &mut c,
                workers as usize,
                max_jobs,
                max_seconds,
                retry_failed,
                stop,
            )?;
            let failed = !result["status"]["failures"].as_array().unwrap().is_empty();
            print(&result)?;
            if failed {
                return Ok(1);
            }
        }
        Command::Status { db } => {
            let c = journal::open(&db, true)?;
            print(&journal::status(&c)?)?;
        }
        Command::Verify { db, limit } => {
            let _lock = journal::WriterLock::acquire(&db)?;
            let mut c = journal::open(&db, false)?;
            print(&runner::check_candidates(&mut c, limit)?)?;
        }
        Command::Sources { db, limit } => {
            let _lock = journal::WriterLock::acquire(&db)?;
            let mut c = journal::open(&db, false)?;
            print(&runner::identify_sources(&mut c, limit)?)?;
        }
        Command::Export {
            db,
            format,
            output,
            needs_review,
            unseen_source_classes,
        } => {
            let c = journal::open(&db, true)?;
            if let Some(path) = output {
                let mut file = OpenOptions::new().write(true).create_new(true).open(path)?;
                runner::export(
                    &c,
                    &mut file,
                    matches!(format, Format::Csv),
                    needs_review,
                    unseen_source_classes,
                )?;
                file.sync_all()?;
            } else {
                runner::export(
                    &c,
                    &mut std::io::stdout().lock(),
                    matches!(format, Format::Csv),
                    needs_review,
                    unseen_source_classes,
                )?;
            }
        }
        Command::Review { db, model, record } => {
            let _lock = journal::WriterLock::acquire(&db)?;
            let c = journal::open(&db, false)?;
            journal::guard(&c)?;
            let id = journal::resolve(&c, &model)?;
            let review_id = journal::add_review(&c, &id, read(&record)?)?;
            print(
                &serde_json::json!({"spectral_model_id":id,"review_id":review_id,"publication_novelty_established":false}),
            )?;
        }
        Command::Subfields {
            absolute_degree,
            output,
        } => {
            let report = search::subfield_config(absolute_degree)?;
            if let Some(path) = output {
                ensure!(
                    !report["config"]["searches"].as_array().unwrap().is_empty(),
                    "no supported subfield; no config written"
                );
                let file = OpenOptions::new().write(true).create_new(true).open(path)?;
                serde_json::to_writer_pretty(&file, &report["config"])?;
                file.sync_all()?;
            }
            print(&report)?;
        }
        Command::ImportPython {
            input,
            db,
            reference_root,
        } => {
            ensure!(!db.exists(), "import needs a new output journal");
            let _lock = journal::WriterLock::acquire(&db)?;
            print(&journal::import_python(
                &input,
                &db,
                &reference_root,
                &fields,
            )?)?;
        }
    }
    Ok(0)
}
fn main() {
    match execute() {
        Ok(code) => std::process::exit(code),
        Err(error) => {
            eprintln!("ghs-sweeper: {error:#}");
            std::process::exit(2);
        }
    }
}
