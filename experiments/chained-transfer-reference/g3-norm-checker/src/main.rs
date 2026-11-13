use chained_g3_canonical_norm::{parse_request, Norm, MAX_INPUT_BYTES};
use std::io::{Read, Write};
fn run() -> Result<(), String> {
    let mut args = std::env::args().skip(1);
    let input = args
        .next()
        .ok_or("usage:chained-g3-canonical-norm INPUT OUTPUT")?;
    let output = args.next().ok_or("missing output")?;
    if args.next().is_some() {
        return Err("extra argument".into());
    }
    let mut bytes = vec![];
    std::fs::File::open(input)
        .map_err(|e| e.to_string())?
        .take(MAX_INPUT_BYTES as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    let req = parse_request(&bytes)?;
    let n = Norm::new(req.q)?;
    let points = req
        .classes
        .iter()
        .map(|p| n.evaluate(p))
        .collect::<Result<Vec<_>, _>>()?;
    let body = serde_json::json!({"schema":"g3-canonical-norm-result/v1","q":req.q,"points":points,"count":points.len()});
    let mut out = std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(output)
        .map_err(|e| e.to_string())?;
    serde_json::to_writer_pretty(&mut out, &body).map_err(|e| e.to_string())?;
    out.write_all(b"\n").map_err(|e| e.to_string())?;
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("{e}");
        std::process::exit(2);
    }
}
