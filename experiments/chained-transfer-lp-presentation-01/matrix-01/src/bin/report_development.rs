//! Render already recorded native synthetic observations; no historical input.
use chained_transfer_lp_finite_projection_01::development;
use serde::Deserialize;
use std::{error::Error, fs, path::Path};

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Observation {
    name: String,
    full_nullity: usize,
    projected_dimension: usize,
    zero_projections_retained: usize,
    all_four_certificates_replayed: bool,
    all_constraint_kernel_full_lifts_replayed: bool,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Input {
    schema: String,
    prime: u64,
    observations: Vec<Observation>,
    scope: String,
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 3 {
        return Err(
            "usage: report_development NATIVE_OBSERVATIONS EXISTING_REPORT_DIRECTORY".into(),
        );
    }
    let input: Input = serde_json::from_slice(&fs::read(&args[1])?)?;
    let cases = development::cases();
    if input.schema != "chained.lp.synthetic-development/v1"
        || input.prime != 101
        || input.observations.len() != cases.len()
        || !input.scope.starts_with("synthetic development only")
    {
        return Err("unexpected observation source/scope".into());
    }
    let mut markdown = String::from("# Native synthetic projection observations\n\nGenerated directly from the retained native observations, checked against the declared synthetic fixtures. PCC-20261115-c07ee3; unsigned F101 development only, not fixed-q223 results. [pcc:unverified]\n\n| Synthetic graph | Full nullity | Projection dimension | Zero projections retained |\n| --- | ---: | ---: | ---: |\n");
    let mut typst = String::from("#table(columns:(2.9fr,1fr,1fr,1fr),stroke:0.4pt,align:(left,center,center,center),[Synthetic graph],[Full nullity],[Projection dimension],[Zero images],\n");
    for (o, expected) in input.observations.iter().zip(cases) {
        if o.name != expected.name
            || o.full_nullity != expected.expected_full_nullity
            || o.projected_dimension != expected.expected_projection_dimension
            || o.zero_projections_retained != expected.expected_zero_projections
            || !o.all_four_certificates_replayed
            || !o.all_constraint_kernel_full_lifts_replayed
        {
            return Err("observation differs from the declared synthetic fixture".into());
        }
        markdown.push_str(&format!(
            "| {} | {} | {} | {} |\n",
            o.name, o.full_nullity, o.projected_dimension, o.zero_projections_retained
        ));
        typst.push_str(&format!(
            "[{}],[{}],[{}],[{}],\n",
            o.name.replace('_', " "),
            o.full_nullity,
            o.projected_dimension,
            o.zero_projections_retained
        ));
    }
    typst.push_str(")\n");
    let out = Path::new(&args[2]);
    fs::write(out.join("generated-results.md"), markdown)?;
    fs::write(out.join("generated-table.typ"), typst)?;
    println!("rendered all14 native observation rows; no new mathematical computation");
    Ok(())
}
