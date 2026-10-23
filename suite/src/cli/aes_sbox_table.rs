//! Exact AES S-box differential and linear tables for the unified CLI.

use clap::Args;
use serde::Serialize;

use super::output::{CmdResult, Out};
use crate::cryptanalysis::aes::{differential::aes_sbox_ddt, linear::aes_sbox_lat};

#[derive(Args, Clone, Debug)]
pub struct AesSboxTableArgs {
    /// `ddt` for XOR differences or `lat` for linear masks.
    #[arg(long)]
    pub kind: String,
    /// Input difference or input mask in 0..=255; omit for all 256 rows.
    #[arg(long)]
    pub row: Option<u8>,
}

#[derive(Serialize)]
struct TableReport {
    schema_version: u32,
    sbox: &'static str,
    kind: String,
    input_row: Option<u8>,
    row_count: usize,
    column_count: usize,
    definition: &'static str,
    values: serde_json::Value,
}

fn report(args: &AesSboxTableArgs) -> Result<TableReport, String> {
    let (definition, values) = match args.kind.as_str() {
        "ddt" => {
            let table = aes_sbox_ddt();
            let values = match args.row {
                Some(row) => serde_json::json!(table[row as usize]),
                None => serde_json::json!(table),
            };
            ("count of x with S(x) xor S(x xor input) = output", values)
        }
        "lat" => {
            let table = aes_sbox_lat();
            let values = match args.row {
                Some(row) => serde_json::json!(table[row as usize]),
                None => serde_json::json!(table),
            };
            (
                "count of x with parity(input & x) = parity(output & S(x)), minus 128",
                values,
            )
        }
        _ => return Err("kind must be ddt or lat".into()),
    };
    Ok(TableReport {
        schema_version: 1,
        sbox: "aes",
        kind: args.kind.clone(),
        input_row: args.row,
        row_count: if args.row.is_some() { 1 } else { 256 },
        column_count: 256,
        definition,
        values,
    })
}

pub fn run(out: Out, args: &AesSboxTableArgs) -> CmdResult {
    let value = report(args)?;
    out.emit(&value, || {
        serde_json::to_string_pretty(&value).expect("table JSON serializes")
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn row_and_full_tables_have_known_entries_and_shapes() {
        let ddt = report(&AesSboxTableArgs {
            kind: "ddt".into(),
            row: Some(1),
        })
        .unwrap();
        let row = ddt.values.as_array().unwrap();
        assert_eq!(row[1], 2);
        assert_eq!(row.iter().map(|x| x.as_u64().unwrap()).sum::<u64>(), 256);
        let lat = report(&AesSboxTableArgs {
            kind: "lat".into(),
            row: Some(1),
        })
        .unwrap();
        assert_eq!(lat.values[1], 12);
        assert_eq!(
            report(&AesSboxTableArgs {
                kind: "ddt".into(),
                row: None
            })
            .unwrap()
            .values
            .as_array()
            .unwrap()
            .len(),
            256
        );
        assert!(report(&AesSboxTableArgs {
            kind: "unknown".into(),
            row: None
        })
        .is_err());
    }
}
