use chained_n4_public_target::{CheckedInstance, MAX_INPUT_BYTES};
use std::fs::{File, OpenOptions};
use std::io::{Read, Write};
use std::path::Path;

fn run() -> Result<bool, String> {
    let args: Vec<_> = std::env::args_os().collect();
    if args.len() != 4 || args[1] != "solve" {
        return Err("usage: chained-n4-rho-accessor solve INPUT OUTPUT".into());
    }
    let path = Path::new(&args[3]);
    if path.exists() {
        return Err("output already exists".into());
    }
    let file = File::open(&args[2]).map_err(|e| e.to_string())?;
    let mut bytes = Vec::new();
    file.take((MAX_INPUT_BYTES + 1) as u64)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() > MAX_INPUT_BYTES {
        return Err("input exceeds65536 bytes".into());
    }
    let checked = CheckedInstance::construct()?;
    let result = chained_n4_rho_accessor::solve(&checked, &bytes)?;
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|e| e.to_string())?;
    file.write_all(&serde_json::to_vec_pretty(&result).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    file.write_all(b"\n").map_err(|e| e.to_string())?;
    Ok(result["ok"] == true)
}
fn main() {
    match run() {
        Ok(true) => (),
        Ok(false) => std::process::exit(1),
        Err(error) => {
            eprintln!("{error}");
            std::process::exit(2);
        }
    }
}
