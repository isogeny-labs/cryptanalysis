use chained_n4_public_target::{solve_public, CheckedInstance, MAX_INPUT_BYTES};
use std::fs::{self, OpenOptions};
use std::io::{Read, Write};
use std::path::Path;

fn output(path: &Path, value: &serde_json::Value) -> Result<(), String> {
    let bytes = serde_json::to_vec_pretty(value).map_err(|e| e.to_string())?;
    let mut f = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|e| e.to_string())?;
    f.write_all(&bytes).map_err(|e| e.to_string())?;
    f.write_all(b"\n").map_err(|e| e.to_string())
}
fn run() -> Result<bool, String> {
    let args: Vec<_> = std::env::args_os().collect();
    match args.get(1).and_then(|s| s.to_str()) {
        Some("describe") if args.len() == 3 => {
            if Path::new(&args[2]).exists() {
                return Err("output already exists".into());
            }
            let checked = CheckedInstance::construct()?;
            output(Path::new(&args[2]), &checked.description())?;
            Ok(true)
        }
        Some("solve") if args.len() == 4 => {
            if Path::new(&args[3]).exists() {
                return Err("output already exists".into());
            }
            let file = fs::File::open(&args[2]).map_err(|e| e.to_string())?;
            let mut input = Vec::new();
            file.take((MAX_INPUT_BYTES + 1) as u64)
                .read_to_end(&mut input)
                .map_err(|e| e.to_string())?;
            if input.len() > MAX_INPUT_BYTES {
                return Err("input exceeds65536 bytes".into());
            }
            let checked = CheckedInstance::construct()?;
            let value = solve_public(&checked, &input)?;
            output(Path::new(&args[3]), &value)?;
            Ok(value["ok"] == true)
        }
        _ => Err("usage: chained-n4-public-target describe OUTPUT | solve INPUT OUTPUT".into()),
    }
}
fn main() {
    match run() {
        Ok(true) => (),
        Ok(false) => std::process::exit(1),
        Err(e) => {
            eprintln!("{e}");
            std::process::exit(2);
        }
    }
}
