//! Whole-population certificates, streamed one call at a time. Production
//! accepts only the strict public view; replay binds the actual original.
use crate::{
    assembly::{self, Presentation},
    original_sha256::Sha256,
    public_view::{self, PublicView, SourceBinding},
    reconstruct,
};
use chained_transfer_lp_finite_projection_01::{projection, ProjectionCertificate};
use serde::{Deserialize, Serialize};
use std::io::{BufRead, Write};

const SCHEMA: &str = "complete-lp-projection-certificates/v1";

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Case {
    pub index: usize,
    pub identity: [usize; 3],
    pub presentation: Presentation,
    pub certificate: ProjectionCertificate,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "record", rename_all = "snake_case", deny_unknown_fields)]
pub enum Record {
    Header {
        schema: String,
        source: SourceBinding,
        public_view: SourceBinding,
        call_count: usize,
        matrix_certificate_count: usize,
    },
    Case {
        case: Box<Case>,
    },
    Complete {
        call_count: usize,
        matrix_certificate_count: usize,
        case_records_sha256: String,
    },
}

struct HashingWriter<'a, W> {
    writer: &'a mut W,
    hash: &'a mut Sha256,
}
impl<W: Write> Write for HashingWriter<'_, W> {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        let count = self.writer.write(bytes)?;
        self.hash.update(&bytes[..count]);
        Ok(count)
    }
    fn flush(&mut self) -> std::io::Result<()> {
        self.writer.flush()
    }
}

fn digest(hash: Sha256) -> String {
    hex::encode(hash.finalize())
}

pub fn binding(bytes: &[u8]) -> SourceBinding {
    SourceBinding {
        bytes: bytes.len(),
        sha256: public_view::sha256(bytes),
    }
}

pub fn write_record<W: Write>(writer: &mut W, record: &Record) -> Result<(), String> {
    serde_json::to_writer(&mut *writer, record).map_err(|e| e.to_string())?;
    writer.write_all(b"\n").map_err(|e| e.to_string())
}

pub fn read_record<R: BufRead>(reader: &mut R) -> Result<(Record, Vec<u8>), String> {
    let mut line = Vec::new();
    reader
        .read_until(b'\n', &mut line)
        .map_err(|e| e.to_string())?;
    if line.last() != Some(&b'\n') || line.len() == 1 {
        return Err("missing/incomplete certificate record or final newline".into());
    }
    let record = serde_json::from_slice(&line).map_err(|e| e.to_string())?;
    Ok((record, line))
}

fn header(view: &PublicView, public: SourceBinding) -> Record {
    Record::Header {
        schema: SCHEMA.into(),
        source: view.source.clone(),
        public_view: public,
        call_count: view.calls.len(),
        matrix_certificate_count: 4 * view.calls.len(),
    }
}

fn produce_view<W: Write>(
    view: &PublicView,
    public: SourceBinding,
    out: &mut W,
) -> Result<(), String> {
    write_record(out, &header(view, public))?;
    let mut hash = Sha256::new();
    for (index, call) in view.calls.iter().enumerate() {
        let presentation = assembly::assemble(&call.available, call.ell)
            .map_err(|e| format!("call {index} assembly: {e}"))?;
        let certificate = projection::produce(
            call.ell,
            &presentation.a,
            presentation.lp_columns,
            &presentation.baseline,
            &presentation.uncapped,
        )
        .map_err(|e| format!("call {index} projection: {e}"))?;
        write_record(
            &mut HashingWriter {
                writer: out,
                hash: &mut hash,
            },
            &Record::Case {
                case: Box::new(Case {
                    index,
                    identity: call.identity,
                    presentation,
                    certificate,
                }),
            },
        )?;
        out.flush().map_err(|e| e.to_string())?;
    }
    write_record(
        out,
        &Record::Complete {
            call_count: view.calls.len(),
            matrix_certificate_count: 4 * view.calls.len(),
            case_records_sha256: digest(hash),
        },
    )?;
    out.flush().map_err(|e| e.to_string())
}

/// No original/private trace or character is accepted by the producer API.
pub fn produce_public<W: Write>(public: &[u8], out: &mut W) -> Result<(), String> {
    let view = public_view::parse(public)?;
    produce_view(&view, binding(public), out)
}

fn verify_view<R: BufRead, W: Write>(
    view: &PublicView,
    public: SourceBinding,
    input: &mut R,
    observations: &mut W,
) -> Result<(), String> {
    let (actual_header, _) = read_record(input)?;
    if actual_header != header(view, public) {
        return Err("certificate header differs from actual bound public/source bytes".into());
    }
    serde_json::to_writer(&mut *observations, &serde_json::json!({
        "record":"header", "schema":"independent-lp-projection-replay/v1",
        "source":view.source, "call_count":view.calls.len(),
        "scope":"finite raw-source reconstruction and Euclidean replay; no character or geometric assertion"
    })).map_err(|e| e.to_string())?;
    observations.write_all(b"\n").map_err(|e| e.to_string())?;
    let mut hash = Sha256::new();
    for (index, call) in view.calls.iter().enumerate() {
        let (record, raw) = read_record(input)?;
        let Record::Case { case } = record else {
            return Err(format!("missing or misplaced complete case {index}"));
        };
        if case.index != index || case.identity != call.identity {
            return Err(format!("call {index} identity/order binding"));
        }
        let expected = reconstruct::reconstruct(&call.available, call.ell)
            .map_err(|e| format!("call {index} independent raw reconstruction: {e}"))?;
        if expected != case.presentation {
            return Err(format!(
                "call {index} complete raw occurrence/column/row/rooted binding"
            ));
        }
        projection::verify(
            call.ell,
            &expected.a,
            expected.lp_columns,
            &expected.baseline,
            &expected.uncapped,
            &case.certificate,
        )
        .map_err(|e| format!("call {index} independent Euclidean replay: {e}"))?;
        hash.update(&raw);
        serde_json::to_writer(&mut *observations, &serde_json::json!({
            "record":"call", "index":index, "identity":call.identity,
            "full_lp_columns":expected.lp_columns, "original_columns":expected.baseline.ncols,
            "raw_rows":expected.a.rows.len(), "baseline_rows":expected.baseline.rows.len(),
            "uncapped_rows":expected.uncapped.rows.len(),
            "a_kernel_dimension":case.certificate.a.kernel.len(),
            "projected_image_dimension":case.certificate.p.pivots.len(),
            "constraint_kernel_dimension":case.certificate.c.kernel.len(),
            "uncapped_kernel_dimension":case.certificate.u.kernel.len(),
            "projected_rows_including_zero_duplicates":case.certificate.p.input.rows.len(),
            "zero_projected_rows":case.certificate.p.input.rows.iter().filter(|v|v.iter().all(|&c|c==0)).count(),
            "original_rooted_receipt":expected.original_rooted_receipt,
            "replay":"complete"
        })).map_err(|e| e.to_string())?;
        observations.write_all(b"\n").map_err(|e| e.to_string())?;
        observations.flush().map_err(|e| e.to_string())?;
    }
    let (footer, _) = read_record(input)?;
    let expected = Record::Complete {
        call_count: view.calls.len(),
        matrix_certificate_count: 4 * view.calls.len(),
        case_records_sha256: digest(hash),
    };
    if footer != expected {
        return Err("missing or incorrect whole certificate completion/count/hash".into());
    }
    if !input.fill_buf().map_err(|e| e.to_string())?.is_empty() {
        return Err("unexpected trailing certificate bytes".into());
    }
    serde_json::to_writer(
        &mut *observations,
        &serde_json::json!({
            "record":"complete", "call_count":view.calls.len(),
            "matrix_certificate_count":4*view.calls.len(), "replay":"complete"
        }),
    )
    .map_err(|e| e.to_string())?;
    observations.write_all(b"\n").map_err(|e| e.to_string())?;
    observations.flush().map_err(|e| e.to_string())
}

/// Source binding requires the actual complete immutable primary trace.
pub fn verify_primary<R: BufRead, W: Write>(
    original: &[u8],
    public: &[u8],
    input: &mut R,
    observations: &mut W,
) -> Result<(), String> {
    let view = public_view::bind_original(original, public)?;
    verify_view(&view, binding(public), input, observations)
}

/// The fixed private-field canary is allowed only with its pinned primary.
pub fn verify_feedback<R: BufRead, W: Write>(
    original: &[u8],
    control: &[u8],
    public: &[u8],
    input: &mut R,
    observations: &mut W,
) -> Result<(), String> {
    let expected = public_view::extract_feedback_control(original, control)?;
    let actual = public_view::parse(public)?;
    if expected != actual {
        return Err("feedback public view differs from actual complete canary source".into());
    }
    verify_view(&actual, binding(public), input, observations)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{
        controls,
        types::{Available, Graph, PublicCall},
    };
    use std::io::Cursor;

    fn synthetic_view() -> PublicView {
        PublicView {
            source: binding(b"one synthetic F101 graph; not a historical source"),
            calls: vec![PublicCall {
                identity: [0, 0, 0],
                ell: 101,
                available: Available {
                    factor_base: vec![[1, 0, 0], [1, 1, 0], [1, 2, 0]],
                    full_rows: vec![],
                    combined_lp_cycle_rows: vec![],
                    columns: 3,
                    eta_column: 2,
                    graph: Graph {
                        full: vec![],
                        ground: vec![],
                        edges: vec![(0, 1, 0, 1), (1, 2, 0, 2), (2, 3, 0, 1), (3, 0, 1, 1)],
                        vertex_points: (0..5).map(|i| [1, 80 + i, 0]).collect(),
                        pairs: 0,
                        no_roots: 0,
                    },
                },
            }],
        }
    }

    #[test]
    fn complete_synthetic_stream_and_whole_rebound_tamper_controls() {
        let view = synthetic_view();
        let public = binding(b"synthetic public bytes");
        let mut positive = Vec::new();
        produce_view(&view, public.clone(), &mut positive).unwrap();
        let mut observation = Vec::new();
        verify_view(
            &view,
            public.clone(),
            &mut Cursor::new(&positive),
            &mut observation,
        )
        .unwrap();
        assert_eq!(positive.iter().filter(|&&b| b == b'\n').count(), 3);
        assert_eq!(observation.iter().filter(|&&b| b == b'\n').count(), 3);
        let mut fixtures = vec![
            ("entire-positive.jsonl".to_owned(), positive.clone()),
            ("entire-positive-replay.jsonl".to_owned(), observation),
        ];
        let mut diagnostics = Vec::new();
        for (name, kind) in [
            ("operation", controls::Tamper::OperationCoefficient),
            ("constrained-kernel", controls::Tamper::ConstrainedAKernel),
            ("missing-A-basis", controls::Tamper::OmitAKernel),
            (
                "missing-zero-projection",
                controls::Tamper::OmitZeroProjection,
            ),
            (
                "constrained-full-lift",
                controls::Tamper::ConstrainedFullLift,
            ),
        ] {
            let mut changed = Vec::new();
            controls::certificate(&mut Cursor::new(&positive), &mut changed, kind).unwrap();
            let mut partial = Vec::new();
            let error = verify_view(
                &view,
                public.clone(),
                &mut Cursor::new(&changed),
                &mut partial,
            )
            .unwrap_err();
            assert!(
                !error.contains("completion/count/hash"),
                "control must fail mathematical replay before footer: {error}"
            );
            assert!(!partial
                .windows(b"\"record\":\"complete\"".len())
                .any(|w| w == b"\"record\":\"complete\""));
            diagnostics.push(serde_json::json!({"control":name,"replay_error":error,"scope":"one complete synthetic F101 file; in-process unit rejection, not historical process control"}));
            fixtures.push((format!("entire-{name}.jsonl"), changed));
            fixtures.push((format!("entire-{name}-partial-replay.jsonl"), partial));
        }
        let mut truncated = positive.clone();
        truncated.truncate(truncated.len() - 1);
        let mut trailing = positive.clone();
        trailing.extend_from_slice(b"{}\n");
        let wrong_public = binding(b"different actual public bytes");
        assert!(verify_view(
            &view,
            wrong_public,
            &mut Cursor::new(&positive),
            &mut Vec::new()
        )
        .is_err());
        for (name, bytes) in [
            ("missing-final-newline", truncated),
            ("trailing-record", trailing),
        ] {
            let error = verify_view(
                &view,
                public.clone(),
                &mut Cursor::new(&bytes),
                &mut Vec::new(),
            )
            .unwrap_err();
            diagnostics.push(serde_json::json!({"control":name,"replay_error":error}));
            fixtures.push((format!("entire-{name}.jsonl"), bytes));
        }
        controls::equal_scientific_bodies(&mut Cursor::new(&positive), &mut Cursor::new(&positive))
            .unwrap();
        if let Some(root) = std::env::var_os("LP_HISTORICAL_DEVELOPMENT_OUT") {
            let out =
                std::path::PathBuf::from(root).with_file_name("complete-stream-unit-controls");
            std::fs::create_dir(&out).unwrap();
            fixtures.push((
                "entire-source-view.json".into(),
                serde_json::to_vec(&serde_json::json!({"source":view.source,"calls":view.calls}))
                    .unwrap(),
            ));
            fixtures.push((
                "all-unit-rejection-diagnostics.json".into(),
                serde_json::to_vec(&diagnostics).unwrap(),
            ));
            for (name, bytes) in fixtures {
                std::fs::write(out.join(name), bytes).unwrap();
            }
        }
    }

    #[test]
    fn missing_zero_projection_fixture_is_explicit_incomplete_control() {
        let mut view = synthetic_view();
        view.calls[0].available.graph.vertex_points.pop();
        view.calls[0]
            .available
            .graph
            .ground
            .push((0, vec![(0, 3)], false));
        let mut positive = Vec::new();
        produce_view(&view, binding(b"no isolated LP"), &mut positive).unwrap();
        let mut changed = Vec::new();
        let error = controls::certificate(
            &mut Cursor::new(&positive),
            &mut changed,
            controls::Tamper::OmitZeroProjection,
        )
        .unwrap_err();
        assert!(error.contains("missing eligible"));
        assert!(!changed
            .windows(b"\"record\":\"complete\"".len())
            .any(|w| w == b"\"record\":\"complete\""));
    }
}
