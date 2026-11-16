use chained_n4_original_relation_whole_audit::{compare, controls, fixture_bundle, Result};
use std::{env, path::Path, process::ExitCode};
fn run() -> Result<()> {
    let a: Vec<_> = env::args().collect();
    match (a.get(1).map(String::as_str),a.len()) {
        (Some("--compare"),7)=>compare(Path::new(&a[2]),Path::new(&a[3]),Path::new(&a[4]),Path::new(&a[5]),Path::new(&a[6])),
        (Some("--fixture-bundle"),6)=>fixture_bundle(Path::new(&a[2]),Path::new(&a[3]),Path::new(&a[4]),Path::new(&a[5])),
        (Some("--controls"),4)=>controls(Path::new(&a[2]),Path::new(&a[3])),
        _=>Err("--compare PINS DOCS HIST_CAPTURE FRESH_DIR OUT | --fixture-bundle PINS DOCS HIST_CAPTURE NEW_DIR | --controls POSITIVE_FRESH_DIR NEW_DIR".into()),
    }
}
fn main() -> ExitCode {
    match std::panic::catch_unwind(run) {
        Ok(Ok(())) => ExitCode::SUCCESS,
        Ok(Err(e)) => {
            eprintln!("whole original relation comparison rejected: {e}");
            ExitCode::from(1)
        }
        Err(_) => {
            eprintln!("whole original relation comparison rejected; original assertion diagnostic retained above");
            ExitCode::from(1)
        }
    }
}
