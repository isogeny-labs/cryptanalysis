//! Whole-input control construction. These functions never relax replay.
use crate::{
    original_sha256::Sha256,
    public_view,
    stream::{self, Case, Record},
};
use chained_transfer_lp_finite_projection_01::Operation;
use std::io::{BufRead, Write};

#[derive(Clone, Copy, Debug)]
pub enum Tamper {
    OperationCoefficient,
    ConstrainedAKernel,
    OmitAKernel,
    OmitZeroProjection,
    ConstrainedFullLift,
}

impl TryFrom<&str> for Tamper {
    type Error = String;
    fn try_from(value: &str) -> Result<Self, Self::Error> {
        match value {
            "operation" => Ok(Self::OperationCoefficient),
            "kernel" => Ok(Self::ConstrainedAKernel),
            "a-basis" => Ok(Self::OmitAKernel),
            "zero-projection" => Ok(Self::OmitZeroProjection),
            "full-lift" => Ok(Self::ConstrainedFullLift),
            _ => Err("unknown certificate tamper control".into()),
        }
    }
}

fn mutate(case: &mut Case, kind: Tamper) -> bool {
    let cert = &mut case.certificate;
    let prime = cert.a.modulus;
    match kind {
        Tamper::OperationCoefficient => {
            for operation in &mut cert.a.operations {
                if let Operation::Add { coefficient, .. } = operation {
                    *coefficient = (*coefficient + 1) % prime;
                    return true;
                }
            }
        }
        Tamper::ConstrainedAKernel => {
            if let (Some(vector), Some(column)) = (
                cert.a.kernel.first_mut(),
                case.presentation
                    .a
                    .rows
                    .iter()
                    .find_map(|row| row.iter().position(|&c| c != 0)),
            ) {
                vector[column] = (vector[column] + 1) % prime;
                return true;
            }
        }
        Tamper::OmitAKernel => return cert.a.kernel.pop().is_some(),
        Tamper::OmitZeroProjection => {
            if let Some(index) = cert
                .p
                .input
                .rows
                .iter()
                .position(|v| v.iter().all(|&c| c == 0))
            {
                cert.p.input.rows.remove(index);
                return true;
            }
        }
        Tamper::ConstrainedFullLift => {
            if let (Some(lift), Some(column)) = (
                cert.constraint_kernel_lifts.first_mut(),
                case.presentation
                    .a
                    .rows
                    .iter()
                    .find_map(|row| row.iter().position(|&c| c != 0)),
            ) {
                lift.full_vector[column] = (lift.full_vector[column] + 1) % prime;
                return true;
            }
        }
    }
    false
}

/// Copies every complete case, mutates one eligible case and rebounds the
/// actual outer body hash. Missing control fixtures leave partial output and
/// return an explicit gap, without a completion record or acceptance waiver.
pub fn certificate<R: BufRead, W: Write>(
    input: &mut R,
    out: &mut W,
    kind: Tamper,
) -> Result<(), String> {
    let (header, _) = stream::read_record(input)?;
    let Record::Header {
        call_count,
        matrix_certificate_count,
        ..
    } = &header
    else {
        return Err("control requires certificate header".into());
    };
    let (count, certificates) = (*call_count, *matrix_certificate_count);
    stream::write_record(out, &header)?;
    let mut original_hash = Sha256::new();
    let mut changed_hash = Sha256::new();
    let mut changed = false;
    for index in 0..count {
        let (mut record, raw) = stream::read_record(input)?;
        let Record::Case { case } = &mut record else {
            return Err("control case order".into());
        };
        if case.index != index {
            return Err("control case index".into());
        }
        original_hash.update(&raw);
        if !changed {
            changed = mutate(case, kind);
        }
        let mut encoded = serde_json::to_vec(&record).map_err(|e| e.to_string())?;
        encoded.push(b'\n');
        changed_hash.update(&encoded);
        out.write_all(&encoded).map_err(|e| e.to_string())?;
    }
    let (original_footer, _) = stream::read_record(input)?;
    if original_footer
        != (Record::Complete {
            call_count: count,
            matrix_certificate_count: certificates,
            case_records_sha256: hex::encode(original_hash.finalize()),
        })
        || !input.fill_buf().map_err(|e| e.to_string())?.is_empty()
    {
        return Err("control original completion/hash/trailing data".into());
    }
    if !changed {
        return Err(format!(
            "missing eligible whole-population control fixture: {kind:?}"
        ));
    }
    stream::write_record(
        out,
        &Record::Complete {
            call_count: count,
            matrix_certificate_count: certificates,
            case_records_sha256: hex::encode(changed_hash.finalize()),
        },
    )?;
    out.flush().map_err(|e| e.to_string())
}

pub fn raw_graph(public: &[u8]) -> Result<Vec<u8>, String> {
    let mut view = public_view::parse(public)?;
    let mut changed = false;
    for call in &mut view.calls {
        let available = &mut call.available;
        let columns = available.columns as u32;
        if let Some(edge) = available.graph.edges.first_mut() {
            edge.2 = (edge.2 + 1) % columns;
            changed = true;
        } else if let Some((_, factors, _)) = available.graph.ground.first_mut() {
            factors[0].0 = (factors[0].0 + 1) % columns;
            changed = true;
        } else if let Some(factors) = available.graph.full.first_mut() {
            factors[0].0 = (factors[0].0 + 1) % columns;
            changed = true;
        }
        if changed {
            call.validate_fixed()?;
            break;
        }
    }
    if !changed {
        return Err("missing raw-relation source-binding control fixture".into());
    }
    // The original source header is deliberately retained, and the public
    // footer is rebound. Actual-source binding, not a stale hash, must reject.
    public_view::encode(&view)
}

pub fn oracle(public: &[u8]) -> Result<Vec<u8>, String> {
    public_view::parse(public)?;
    let lines: Vec<_> = public
        .strip_suffix(b"\n")
        .ok_or("public final newline")?
        .split(|&b| b == b'\n')
        .collect();
    let mut first: serde_json::Value =
        serde_json::from_slice(lines[1]).map_err(|e| e.to_string())?;
    first["call"]
        .as_object_mut()
        .ok_or("public call object")?
        .insert("known_logs".into(), serde_json::json!([17, 23]));
    let mut body = serde_json::to_vec(&first).map_err(|e| e.to_string())?;
    body.push(b'\n');
    for line in &lines[2..61] {
        body.extend_from_slice(line);
        body.push(b'\n');
    }
    let mut footer: serde_json::Value =
        serde_json::from_slice(lines[61]).map_err(|e| e.to_string())?;
    footer["canonical_call_records_sha256"] = public_view::sha256(&body).into();
    let mut output = lines[0].to_vec();
    output.push(b'\n');
    output.extend(body);
    serde_json::to_writer(&mut output, &footer).map_err(|e| e.to_string())?;
    output.push(b'\n');
    Ok(output)
}

pub fn feedback_copy(original: &[u8]) -> Result<Vec<u8>, String> {
    public_view::extract_original(original)?;
    let mut whole: serde_json::Value =
        serde_json::from_slice(original).map_err(|e| e.to_string())?;
    for call in whole["whole_calls"].as_array_mut().ok_or("primary calls")? {
        for (key, value) in call.as_object_mut().ok_or("primary call")? {
            if !["identity", "ell", "available"].contains(&key.as_str()) {
                *value = serde_json::Value::Null;
            }
        }
    }
    let bytes = serde_json::to_vec(&whole).map_err(|e| e.to_string())?;
    public_view::extract_feedback_control(original, &bytes)?;
    Ok(bytes)
}

/// Both inputs still require their respective independent source-bound replay.
/// This separate check permits header source/public bindings only to differ.
pub fn equal_scientific_bodies<A: BufRead, B: BufRead>(a: &mut A, b: &mut B) -> Result<(), String> {
    let (ha, _) = stream::read_record(a)?;
    let (hb, _) = stream::read_record(b)?;
    let (
        Record::Header {
            schema: sa,
            call_count: ca,
            matrix_certificate_count: ma,
            ..
        },
        Record::Header {
            schema: sb,
            call_count: cb,
            matrix_certificate_count: mb,
            ..
        },
    ) = (ha, hb)
    else {
        return Err("feedback comparison headers".into());
    };
    if sa != sb || ca != cb || ma != mb {
        return Err("feedback changed scientific header fields".into());
    }
    for index in 0..ca {
        let (ra, ba) = stream::read_record(a)?;
        let (rb, bb) = stream::read_record(b)?;
        if !matches!(&ra,Record::Case{case}if case.index==index) || ra != rb || ba != bb {
            return Err(format!(
                "private feedback changed complete scientific case {index}"
            ));
        }
    }
    let (fa, ba) = stream::read_record(a)?;
    let (fb, bb) = stream::read_record(b)?;
    if !matches!(fa,Record::Complete{call_count,matrix_certificate_count,..}if call_count==ca && matrix_certificate_count==ma)
        || fa != fb
        || ba != bb
        || !a.fill_buf().map_err(|e| e.to_string())?.is_empty()
        || !b.fill_buf().map_err(|e| e.to_string())?.is_empty()
    {
        return Err("private feedback changed completion/trailing data".into());
    }
    Ok(())
}
