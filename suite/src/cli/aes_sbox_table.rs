//! Exact AES S-box differential and linear tables for the unified CLI.

use clap::Args;
use serde::Serialize;

use super::output::{CmdResult, Out};
use crate::cryptanalysis::aes::{
    boomerang::aes_sbox_bct,
    differential::aes_sbox_ddt,
    linear::{aes_sbox_dlct, aes_sbox_lat},
};

#[derive(Args, Clone, Debug)]
pub struct AesSboxTableArgs {
    /// `ddt`, `lat`, `bct`, or `dlct` for exact AES S-box analyses.
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
        "bct" => {
            let table = aes_sbox_bct();
            let values = match args.row {
                Some(row) => serde_json::json!(table[row as usize]),
                None => serde_json::json!(table),
            };
            (
                "count of x with inverse(S(x) xor output) xor inverse(S(x xor input) xor output) = input",
                values,
            )
        }
        "dlct" => {
            let table = aes_sbox_dlct();
            let values = match args.row {
                Some(row) => serde_json::json!(table[row as usize]),
                None => serde_json::json!(table),
            };
            (
                "half the signed parity sum of output mask and S(x) xor S(x xor input)",
                values,
            )
        }
        _ => return Err("kind must be ddt, lat, bct, or dlct".into()),
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

    #[test]
    fn bct_and_dlct_rows_match_full_exports_and_walsh_identity() {
        let ddt = aes_sbox_ddt();
        for kind in ["bct", "dlct"] {
            let full = report(&AesSboxTableArgs {
                kind: kind.into(),
                row: None,
            })
            .unwrap();
            let row = report(&AesSboxTableArgs {
                kind: kind.into(),
                row: Some(1),
            })
            .unwrap();
            assert_eq!(full.row_count, 256);
            assert_eq!(row.row_count, 1);
            assert_eq!(row.values, full.values[1]);
            assert_eq!(row.values.as_array().unwrap().len(), 256);
        }
        let bct = report(&AesSboxTableArgs {
            kind: "bct".into(),
            row: Some(1),
        })
        .unwrap();
        assert_eq!(bct.values[0], 256);
        assert_eq!(bct.values[1], 2);
        let dlct = report(&AesSboxTableArgs {
            kind: "dlct".into(),
            row: Some(1),
        })
        .unwrap();
        assert_eq!(dlct.values[0], 128);
        assert_eq!(dlct.values[1], -4);
        for mask in [1u8, 7, 31, 127, 255] {
            let walsh = ddt[1]
                .iter()
                .enumerate()
                .map(|(difference, &count)| {
                    if ((difference as u8 & mask).count_ones() & 1) == 0 {
                        i32::from(count)
                    } else {
                        -i32::from(count)
                    }
                })
                .sum::<i32>()
                / 2;
            assert_eq!(dlct.values[mask as usize], walsh);
        }
    }
}
