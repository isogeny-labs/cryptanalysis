//! Post-generation finite character audit. This executable is separate from
//! the public producer and imports no field engine or BSGS implementation.
use chained_transfer_lp_finite_projection_01::{projection, Matrix};
use chained_transfer_lp_historical_01::{
    original_sha256::Sha256,
    public_view::{self, SourceBinding},
    reconstruct,
    stream::{self, Record},
    types::{Available, Point},
};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    error::Error,
    fs::{self, File, OpenOptions},
    io::{BufReader, BufWriter, Read, Write},
    path::Path,
};

const ELL: u64 = 2_773_073;
const PINS: &[u8] = include_bytes!("../../historical-whole-fixture-pins-01.json");

fn digest(hash: Sha256) -> String {
    hash.finalize().iter().map(|b| format!("{b:02x}")).collect()
}

fn pinned_json(name: &str, bytes: &[u8]) -> Result<Value, String> {
    let pins: Value = serde_json::from_slice(PINS).map_err(|e| e.to_string())?;
    let pin = pins["fixtures"]
        .as_array()
        .ok_or("fixture pins")?
        .iter()
        .find(|p| p["name"] == name)
        .ok_or("unknown whole fixture")?;
    if pin["decoded_bytes"].as_u64() != Some(bytes.len() as u64)
        || pin["decoded_sha256"].as_str() != Some(&public_view::sha256(bytes))
    {
        return Err(format!("entire original {name} size/SHA pin mismatch"));
    }
    if name.ends_with(".jsonl.xz") {
        let body = bytes
            .strip_suffix(b"\n")
            .ok_or("original witness final newline")?;
        let records = body
            .split(|&b| b == b'\n')
            .map(|line| serde_json::from_slice(line).map_err(|e| e.to_string()))
            .collect::<Result<Vec<Value>, String>>()?;
        Ok(Value::Array(records))
    } else {
        serde_json::from_slice(bytes).map_err(|e| e.to_string())
    }
}

fn scalar(value: &Value) -> Result<u64, String> {
    value
        .as_u64()
        .filter(|&v| v < ELL)
        .ok_or("noncanonical original character scalar".into())
}

fn dot(row: &[u64], vector: &[u64], prime: u64) -> Result<u64, String> {
    if row.len() != vector.len() || row.iter().chain(vector).any(|&v| v >= prime) {
        return Err("post-character row/vector shape or coefficient".into());
    }
    let sum: i128 = row
        .iter()
        .zip(vector)
        .map(|(&a, &b)| i128::from(a) * i128::from(b))
        .sum();
    Ok(sum.rem_euclid(i128::from(prime)) as u64)
}

fn all_residuals(matrix: &Matrix, vector: &[u64]) -> Result<Vec<u64>, String> {
    if matrix.ncols != vector.len() {
        return Err("post-character matrix width".into());
    }
    matrix
        .rows
        .iter()
        .map(|row| dot(row, vector, ELL))
        .collect()
}

fn raw_residuals(
    available: &Available,
    fb: &[u64],
    lp: &[u64],
    eta: u64,
    prime: u64,
) -> Result<Vec<u64>, String> {
    if fb.len() != available.factor_base.len()
        || lp.len() != available.graph.vertex_points.len()
        || fb.iter().chain(lp).any(|&v| v >= prime)
        || eta >= prime
        || fb[0] != 0
    {
        return Err("post raw character width/basepoint/canonical scalar".into());
    }
    let mut output = Vec::new();
    let factor = |part: &[(u32, u8)]| -> i128 {
        part.iter()
            .map(|&(i, m)| i128::from(fb[i as usize]) * i128::from(m))
            .sum()
    };
    for row in &available.graph.full {
        output.push((factor(row) - i128::from(eta)).rem_euclid(i128::from(prime)) as u64);
    }
    for (vertex, part, half) in &available.graph.ground {
        let sum = factor(part) + i128::from(lp[*vertex as usize]) * if *half { 2 } else { 1 }
            - i128::from(eta);
        output.push(sum.rem_euclid(i128::from(prime)) as u64);
    }
    for &(x, y, a, b) in &available.graph.edges {
        let sum = i128::from(lp[x as usize])
            + i128::from(lp[y as usize])
            + i128::from(fb[a as usize])
            + i128::from(fb[b as usize])
            - i128::from(eta);
        output.push(sum.rem_euclid(i128::from(prime)) as u64);
    }
    Ok(output)
}

fn combination(rows: &[Vec<u64>], coefficients: &[u64], width: usize) -> Result<Vec<u64>, String> {
    if rows.len() != coefficients.len() || rows.iter().any(|r| r.len() != width) {
        return Err("post-character basis combination shape".into());
    }
    (0..width)
        .map(|column| {
            let values: Vec<_> = rows.iter().map(|row| row[column]).collect();
            dot(&values, coefficients, ELL)
        })
        .collect()
}

fn hash_file(path: &Path) -> Result<SourceBinding, Box<dyn Error>> {
    let mut input = File::open(path)?;
    let mut buffer = [0u8; 65536];
    let mut hash = Sha256::new();
    let mut bytes = 0usize;
    loop {
        let count = input.read(&mut buffer)?;
        if count == 0 {
            break;
        }
        bytes = bytes.checked_add(count).ok_or("file byte count overflow")?;
        hash.update(&buffer[..count]);
    }
    Ok(SourceBinding {
        bytes,
        sha256: digest(hash),
    })
}

fn emit<W: Write>(out: &mut W, value: &Value) -> Result<(), String> {
    serde_json::to_writer(&mut *out, value).map_err(|e| e.to_string())?;
    out.write_all(b"\n").map_err(|e| e.to_string())?;
    out.flush().map_err(|e| e.to_string())
}

fn check_fixtures(
    directory: &Path,
    capture: &Path,
    out: &mut impl Write,
) -> Result<(), Box<dyn Error>> {
    let pins: Value = serde_json::from_slice(PINS)?;
    let mut records = Vec::new();
    for pin in pins["fixtures"].as_array().ok_or("whole fixture pins")? {
        let name = pin["name"].as_str().ok_or("fixture name")?;
        let decoded = name.strip_suffix(".xz").ok_or("declared XZ fixture")?;
        let compressed_binding = hash_file(&directory.join(name))?;
        let decoded_binding = hash_file(&directory.join(decoded))?;
        if pin["compressed_bytes"] != compressed_binding.bytes
            || pin["sha256"] != compressed_binding.sha256
            || pin["decoded_bytes"] != decoded_binding.bytes
            || pin["decoded_sha256"] != decoded_binding.sha256
        {
            return Err(format!("entire compressed/decoded fixture mismatch: {name}").into());
        }
        records.push(json!({"name":name,"entire_compressed":compressed_binding,"entire_decoded":decoded_binding}));
    }
    if records.len() != 6 {
        return Err("complete six original fixtures required".into());
    }
    let capture_binding = hash_file(capture)?;
    if pins["passive_acceptance"]["bytes"] != capture_binding.bytes
        || pins["passive_acceptance"]["sha256"] != capture_binding.sha256
    {
        return Err("entire original passive capture acceptance pin mismatch".into());
    }
    emit(
        out,
        &json!({"record":"complete","schema":"entire-original-LP-input-pin-replay/v1",
        "all_six_compressed_and_decoded_fixtures":records,"entire_passive_acceptance":capture_binding,
        "scope":"complete file byte/SHA binding only; no mathematical or runtime assertion"}),
    )?;
    Ok(())
}

fn audit(
    original: &[u8],
    public: &[u8],
    certificate_path: &Path,
    witness_bytes: &[u8],
    rank_bytes: &[u8],
    character_bytes: &[u8],
    out: &mut impl Write,
) -> Result<(), Box<dyn Error>> {
    let view = public_view::bind_original(original, public)?;
    let witnesses = pinned_json("source-character-whole60-witnesses.jsonl.xz", witness_bytes)?;
    let rank = pinned_json("relation-whole60-verdict.json.xz", rank_bytes)?;
    let character = pinned_json("source-character-whole60-verdict.json.xz", character_bytes)?;
    let witness_records = witnesses.as_array().ok_or("whole witness records")?;
    if witness_records.len() != 65
        || witness_records[0]["kind"] != "header"
        || witness_records[64]["kind"] != "complete"
        || witness_records[64]["whole_calls"] != 60
        || witness_records[64]["whole_witness_failures"] != 0
        || rank["whole_calls"] != 60
        || rank["complete_matrix_certificates"] != 360
        || character["whole_calls"] != 60
        || character["whole_witnesses_sha256"] != public_view::sha256(witness_bytes)
        || rank["whole_trace_sha256"] != view.source.sha256
        || character["whole_trace_sha256"] != view.source.sha256
    {
        return Err("whole original rank/character/witness linkage".into());
    }
    let certificate_binding = hash_file(certificate_path)?;
    let mut input = BufReader::new(File::open(certificate_path)?);
    let mut whole_hash = Sha256::new();
    let mut body_hash = Sha256::new();
    let mut read_bytes = 0usize;
    let (header, raw) = stream::read_record(&mut input)?;
    whole_hash.update(&raw);
    read_bytes += raw.len();
    let expected = Record::Header {
        schema: "complete-lp-projection-certificates/v1".into(),
        source: view.source.clone(),
        public_view: stream::binding(public),
        call_count: 60,
        matrix_certificate_count: 240,
    };
    if header != expected {
        return Err("post-audit complete certificate/source header binding".into());
    }
    emit(
        out,
        &json!({"record":"header","schema":"complete-lp-finite-character-post-audit/v1",
        "source":view.source,"public_view":stream::binding(public),"certificate_file":certificate_binding,
        "whole_original_witnesses":stream::binding(witness_bytes),"whole_original_rank_verdict":stream::binding(rank_bytes),
        "whole_original_character_verdict":stream::binding(character_bytes),
        "scope":"post-generation finite scalar relation checks; unchanged original actual-norm/witness auditor and360 replayer required separately; no field engine, BSGS, global character or execution proof"}),
    )?;
    let mut failures = 0usize;
    for (index, call) in view.calls.iter().enumerate() {
        let (record, raw) = stream::read_record(&mut input)?;
        let Record::Case { case } = record else {
            return Err("post-audit missing complete case".into());
        };
        if case.index != index || case.identity != call.identity {
            return Err("post-audit case order".into());
        }
        let expected = reconstruct::reconstruct(&call.available, ELL)?;
        if case.presentation != expected {
            return Err("post-audit raw-source reconstruction mismatch".into());
        }
        projection::verify(
            ELL,
            &expected.a,
            expected.lp_columns,
            &expected.baseline,
            &expected.uncapped,
            &case.certificate,
        )?;
        let witness = &witness_records[4 + index];
        let prior = &character["all60_call_results"][index];
        let old_rank = &rank["all60_call_summary"][index];
        if witness["kind"] != "call"
            || witness["identity"] != json!(call.identity)
            || prior["identity"] != json!(call.identity)
            || old_rank["identity"] != json!(call.identity)
        {
            return Err("post-audit original call order".into());
        }
        let mut values = BTreeMap::<Point, u64>::new();
        for row in witness["entire_point_witnesses"]
            .as_array()
            .ok_or("entire point witnesses")?
        {
            let point: Point = serde_json::from_value(row["point"].clone())?;
            if row["witness"]["status"] != "witness"
                || values
                    .insert(point, scalar(&row["witness"]["scalar"])?)
                    .is_some()
            {
                return Err("post-audit duplicate/missing original point witness".into());
            }
        }
        let lookup = |points: &[Point]| -> Result<Vec<u64>, String> {
            points
                .iter()
                .map(|point| {
                    values
                        .get(point)
                        .copied()
                        .ok_or("missing required FB/LP witness".into())
                })
                .collect()
        };
        let fb = lookup(&call.available.factor_base)?;
        let lp = lookup(&call.available.graph.vertex_points)?;
        let eta = scalar(&witness["eta_witness"]["scalar"])?;
        let mut projected = fb[1..].to_vec();
        projected.push(eta);
        if fb[0] != 0
            || prior["source_character_vector"] != json!(projected)
            || projected.iter().all(|&v| v == 0)
        {
            return Err("post-audit basepoint/actual nonzero character binding".into());
        }
        let mut full = lp.clone();
        full.extend_from_slice(&projected);
        let raw_residuals = raw_residuals(&call.available, &fb, &lp, eta, ELL)?;
        let a_residuals = all_residuals(&expected.a, &full)?;
        if raw_residuals != a_residuals {
            return Err("separate raw-occurrence/dense residual disagreement".into());
        }
        let cert = &case.certificate;
        let old = old_rank["certificates"]
            .as_array()
            .ok_or("old rank certificates")?
            .iter()
            .find(|c| c["family"] == "all_available" && c["restriction"] == "full")
            .ok_or("old complete baseline rank")?;
        if old["columns"] != expected.baseline.ncols || old["rows"] != expected.baseline.rows.len()
        {
            return Err("original baseline dimensions/row count binding".into());
        }
        let groups = [
            ("A_raw", raw_residuals),
            ("A_rref", all_residuals(&cert.a.rref, &full)?),
            (
                "captured_baseline",
                all_residuals(&expected.baseline, &projected)?,
            ),
            ("C_constraints", all_residuals(&cert.c.input, &projected)?),
            ("C_rref", all_residuals(&cert.c.rref, &projected)?),
            ("U_constraints", all_residuals(&cert.u.input, &projected)?),
            ("U_rref", all_residuals(&cert.u.rref, &projected)?),
        ];
        let mut residual_tables = BTreeMap::new();
        let mut bad = 0usize;
        for (name, rows) in groups {
            bad += rows.iter().filter(|&&v| v != 0).count();
            residual_tables.insert(name, rows);
        }
        let free: Vec<_> = (0..expected.a.ncols)
            .filter(|col| cert.a.pivots.binary_search(col).is_err())
            .collect();
        let a_coefficients: Vec<_> = free.iter().map(|&col| full[col]).collect();
        let reconstructed_character =
            combination(&cert.a.kernel, &a_coefficients, expected.a.ncols)?;
        let character_in_a = reconstructed_character == full;
        let image_coefficients: Vec<_> = cert.p.pivots.iter().map(|&col| projected[col]).collect();
        let section = combination(
            &cert.transformed_full_lifts[..cert.p.pivots.len()],
            &image_coefficients,
            expected.a.ncols,
        )?;
        let section_residuals = all_residuals(&expected.a, &section)?;
        let section_projects = section[expected.lp_columns..] == projected;
        bad += section_residuals.iter().filter(|&&v| v != 0).count();
        bad += usize::from(!character_in_a) + usize::from(!section_projects);
        failures += bad;
        emit(
            out,
            &json!({"record":"call","index":index,"identity":call.identity,
            "original_baseline_nullity":old["nullity"],"rooted_uncapped_nullity":cert.u.kernel.len(),
            "complete_projected_image_dimension":cert.p.pivots.len(),"actual_nonzero_FB_eta_character":projected,
            "actual_complete_LP_FB_eta_character":full,"all_original_point_witness_count":values.len(),
            "all_raw_and_derived_constraint_residuals":residual_tables,
            "A_basis_character_coefficients":a_coefficients,"A_basis_reconstructed_character":reconstructed_character,
            "character_in_A_kernel":character_in_a,"image_basis_coefficients":image_coefficients,
            "complete_image_section_lift":section,"section_projects_to_actual_character":section_projects,
            "all_section_original_A_residuals":section_residuals,"nonzero_residual_or_lift_failures":bad}),
        )?;
        body_hash.update(&raw);
        whole_hash.update(&raw);
        read_bytes += raw.len();
    }
    let (footer, raw) = stream::read_record(&mut input)?;
    if footer
        != (Record::Complete {
            call_count: 60,
            matrix_certificate_count: 240,
            case_records_sha256: digest(body_hash),
        })
    {
        return Err("post-audit whole case completion/hash".into());
    }
    whole_hash.update(&raw);
    read_bytes += raw.len();
    let mut trailing = [0u8; 1];
    if input.read(&mut trailing)? != 0
        || certificate_binding.bytes != read_bytes
        || certificate_binding.sha256 != digest(whole_hash)
    {
        return Err("post-audit changed/trailing whole certificate bytes".into());
    }
    if failures != 0 {
        emit(
            out,
            &json!({"record":"rejected","call_count":60,"nonzero_residual_or_lift_failures":failures}),
        )?;
        return Err("whole finite character post-audit has nonzero residual/lift failures; all cases retained".into());
    }
    emit(
        out,
        &json!({"record":"complete","call_count":60,"matrix_certificate_count":240,
        "nonzero_residual_or_lift_failures":0,"actual_nonzero_character_in_every_projected_image":true,
        "scope":"finite post-generation checked character/lifts only; original actual norm/direct source witness audit and360 replay remain separate required executions"}),
    )?;
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    if let [_, mode, directory, capture, destination] = args.as_slice() {
        if mode == "--check-fixtures" {
            let mut out = BufWriter::new(
                OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(destination)?,
            );
            check_fixtures(Path::new(directory), Path::new(capture), &mut out)?;
            out.flush()?;
            out.get_ref().sync_all()?;
            return Ok(());
        }
    }
    let [_, original, public, certificate, witnesses, rank, character, destination] =
        args.as_slice()
    else {
        return Err("usage: lp-post-character ORIGINAL PUBLIC CERT WITNESSES OLD_RANK_VERDICT OLD_CHARACTER_VERDICT OUT".into());
    };
    let mut out = BufWriter::new(
        OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(destination)?,
    );
    audit(
        &fs::read(original)?,
        &fs::read(public)?,
        Path::new(certificate),
        &fs::read(witnesses)?,
        &fs::read(rank)?,
        &fs::read(character)?,
        &mut out,
    )?;
    out.flush()?;
    out.get_ref().sync_all()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use chained_transfer_lp_historical_01::types::Graph;
    #[test]
    fn raw_character_checks_keep_half_ground_repeated_endpoint_and_basepoint() {
        let mut a = Available {
            factor_base: vec![[1, 0, 0], [1, 1, 0]],
            full_rows: vec![],
            combined_lp_cycle_rows: vec![],
            columns: 2,
            eta_column: 1,
            graph: Graph {
                full: vec![],
                ground: vec![(0, vec![(1, 2)], true)],
                edges: vec![(0, 0, 1, 1)],
                vertex_points: vec![[1, 80, 0]],
                pairs: 0,
                no_roots: 0,
            },
        };
        a.validate(101).unwrap();
        assert_eq!(
            raw_residuals(&a, &[0, 7], &[5], 24, 101).unwrap(),
            vec![0, 0]
        );
        assert_eq!(
            raw_residuals(&a, &[0, 7], &[5], 25, 101).unwrap(),
            vec![100, 100]
        );
        assert!(raw_residuals(&a, &[1, 7], &[5], 24, 101).is_err());
        a.graph.ground[0].2 = false;
        a.graph.ground[0].1.push((0, 1));
        a.validate(101).unwrap();
        assert_eq!(
            raw_residuals(&a, &[0, 7], &[5], 24, 101).unwrap(),
            vec![96, 0]
        );
    }
    #[test]
    fn whole_original_pins_refuse_header_or_json_shape_as_substitute() {
        for name in [
            "source-character-whole60-witnesses.jsonl.xz",
            "relation-whole60-verdict.json.xz",
            "source-character-whole60-verdict.json.xz",
        ] {
            assert!(pinned_json(name, b"{\"whole_calls\":60}\n")
                .unwrap_err()
                .contains("size/SHA pin mismatch"));
        }
    }
}
