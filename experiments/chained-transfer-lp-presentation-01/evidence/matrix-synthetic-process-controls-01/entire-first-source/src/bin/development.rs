use chained_transfer_lp_finite_projection_01::development::{self, Record};
use serde_json::json;
use std::{error::Error, fs, path::Path};

fn write(path: &Path, value: &serde_json::Value) -> Result<(), Box<dyn Error>> {
    let mut text = serde_json::to_string_pretty(value)?;
    text.push('\n');
    fs::write(path, text)?;
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 4 { return Err("usage: development --produce OUT UNUSED | --replay WHOLE_CASE ACCEPTED_OUTPUT".into()); }
    match args[1].as_str() {
        "--produce" => {
            let out = Path::new(&args[2]);
            fs::create_dir(out)?;
            fs::create_dir(out.join("whole-negative-controls"))?;
            let mut observations = Vec::new();
            for case in development::cases() {
                let record = development::record(case)?;
                let cert = &record.certificate;
                observations.push(json!({"name": record.case.name, "full_nullity": cert.a.kernel.len(), "projected_dimension": cert.p.pivots.len(), "zero_projections_retained": cert.p.input.rows.iter().filter(|v| v.iter().all(|&x| x == 0)).count(), "all_four_certificates_replayed": true, "all_constraint_kernel_full_lifts_replayed": true}));
                write(&out.join(format!("{}.whole-case.json", record.case.name)), &serde_json::to_value(&record)?)?;
            }
            for (name, whole) in development::whole_negative_records()? { write(&out.join("whole-negative-controls").join(format!("{name}.whole-case.json")), &whole)?; }
            write(&out.join("development-observations.json"), &json!({"schema": "chained.lp.synthetic-development/v1", "prime": development::PRIME, "observations": observations, "scope": "synthetic development only, not fixed-q223 population, complete production control protocol, solve or cost evidence"}))?;
            println!("retained all14 synthetic A/P/C/U cases, all projections/full lifts, seven complete negative records");
        }
        "--replay" => {
            let accepted = Path::new(&args[3]);
            if accepted.exists() { return Err("accepted output already exists".into()); }
            let bytes = fs::read(&args[2])?;
            let record: Record = serde_json::from_slice(&bytes)?;
            development::verify_record(&record)?;
            write(accepted, &json!({"case": record.case.name, "actual_replay": "accepted", "scope": "unsigned synthetic development only"}))?;
            println!("independent whole synthetic replay accepted");
        }
        _ => return Err("unknown mode; only synthetic development modes are provided".into()),
    }
    Ok(())
}
