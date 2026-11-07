//! Strict file/JSON consumer of the structured predicate and prefix APIs.
//! Receipts are producer assertions; replay uses the same native implementation.
use crate::arithmetic::Seeded;
use crate::contraction::Counter;
use crate::curve::{Curve, Point};
use crate::structured::{IsogenyFibres, MembershipMessage, Prepared};
use crate::{integrity, invalid, BigUint, Limits, Meter, Result};
use num_traits::Zero;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{io::Read, sync::Arc};

const REQUEST_SCHEMA: &str = "structured-prime-ic-request/v1";
const RECEIPT_SCHEMA: &str = "structured-prime-ic-receipt/v1";
const POLICY: &str = "ordered_signed_tuples_repetition_and_inverse_pairs_allowed";
const STANDING: &str = "producer_assertion";
const MAX_JSON_BYTES: u64 = 1_048_576;

struct Request {
    schema: String,
    p: String,
    a: String,
    b: String,
    r: String,
    cofactor: String,
    generator: [String; 2],
    kernel_x: String,
    image_x: Vec<String>,
    arity: usize,
    targets: Vec<Option<[String; 2]>>,
    membership: String,
    fixture_seed: u64,
    steps: u64,
    vector: usize,
    bits: usize,
}
json_record!(
    Request,
    required {
        schema,
        p,
        a,
        b,
        r,
        cofactor,
        generator,
        kernel_x,
        image_x,
        arity,
        targets,
        membership,
        fixture_seed,
        steps,
        vector,
        bits
    },
    optional {}
);

struct Answer {
    target: Option<[String; 2]>,
    count: String,
    witness: Option<Vec<[String; 2]>>,
}
json_record!(
    Answer,
    required {
        target,
        count,
        witness
    },
    optional {}
);
struct Semantic {
    request: Request,
    relation_policy: String,
    answers: Vec<Answer>,
}
json_record!(
    Semantic,
    required {
        request,
        relation_policy,
        answers
    },
    optional {}
);
struct Receipt {
    schema: String,
    semantic: Semantic,
    semantic_sha256: String,
    selected_source_pins: Value,
    diagnostics: Value,
    standing: String,
}
json_record!(
    Receipt,
    required {
        schema,
        semantic,
        semantic_sha256,
        selected_source_pins,
        diagnostics,
        standing
    },
    optional {}
);

fn json_error(error: impl std::fmt::Display) -> crate::Error {
    invalid(&format!("structured JSON: {error}"))
}
fn integer(text: &str) -> Result<BigUint> {
    if text.is_empty() || text.len() > 200 || !text.bytes().all(|c| c.is_ascii_digit()) {
        return Err(invalid("integers must be bounded unsigned decimal strings"));
    }
    BigUint::parse_bytes(text.as_bytes(), 10).ok_or_else(|| invalid("decimal integer"))
}
fn point(value: &Option<[String; 2]>) -> Result<Point> {
    match value {
        None => Ok(Point::Infinity),
        Some([x, y]) => Ok(Point::Affine {
            x: integer(x)?,
            y: integer(y)?,
        }),
    }
}
fn coordinates(point: &Point) -> Result<[String; 2]> {
    match point {
        Point::Affine { x, y } => Ok([x.to_string(), y.to_string()]),
        Point::Infinity => Err(integrity("identity structured summand")),
    }
}
fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn value<T: serde::Serialize>(record: &T) -> Result<Value> {
    serde_json::to_value(record).map_err(json_error)
}
fn semantic_digest(semantic: &Semantic) -> Result<String> {
    // Value maps are sorted by key with this crate's serde_json configuration.
    Ok(digest(
        &serde_json::to_vec(&value(semantic)?).map_err(json_error)?,
    ))
}
fn source_pins() -> Value {
    json!({
        "structured.rs": digest(include_bytes!("structured.rs")),
        "structured_runner.rs": digest(include_bytes!("structured_runner.rs")),
        "encoding.rs": digest(include_bytes!("encoding.rs")),
        "contraction.rs": digest(include_bytes!("contraction.rs")),
        "curve.rs": digest(include_bytes!("curve.rs")),
        "arithmetic.rs": digest(include_bytes!("arithmetic.rs"))
    })
}
fn execute(request: Request) -> Result<Receipt> {
    if request.schema != REQUEST_SCHEMA
        || !(2..=8).contains(&request.arity)
        || !(1..=64).contains(&request.targets.len())
        || !(1..=1024).contains(&request.image_x.len())
    {
        return Err(invalid("structured schema, arity, target or image count"));
    }
    if !matches!(request.membership.as_str(), "circuit" | "fibre_message") {
        return Err(invalid("membership must be circuit or fibre_message"));
    }
    let mut meter = Meter::new(Limits {
        steps: request.steps,
        vector: request.vector,
        bits: request.bits,
    });
    let p = integer(&request.p)?;
    meter.bits(p.bits() as usize, "structured modulus")?;
    let curve = Curve::with_cofactor(
        p,
        integer(&request.a)?,
        integer(&request.b)?,
        integer(&request.r)?,
        integer(&request.cofactor)?,
        point(&Some(request.generator.clone()))?,
        &mut meter,
    )?;
    let fibres = IsogenyFibres::new(
        &curve,
        integer(&request.kernel_x)?,
        request
            .image_x
            .iter()
            .map(|s| integer(s))
            .collect::<Result<Vec<_>>>()?,
        &mut meter,
    )?;
    meter.vector(request.targets.len(), "structured query targets")?;
    let targets = request
        .targets
        .iter()
        .map(point)
        .collect::<Result<Vec<_>>>()?;
    for target in &targets {
        if !curve.in_subgroup(target, &mut meter)? {
            return Err(invalid("structured target outside subgroup"));
        }
    }
    let message = if request.membership == "fibre_message" {
        Some(Arc::new(MembershipMessage::from_fibres(
            &curve,
            &fibres,
            &mut Seeded(request.fixture_seed),
            &mut meter,
        )?))
    } else {
        None
    };
    let message_diagnostics=message.as_ref().map(|m|json!({"nonterminal_nodes":m.node_count(),"lift_candidates_checked":m.candidate_points_checked(),"exhaustive_encodings":m.assignments_examined()}));
    let prepared = Prepared::new(&curve, &fibres, request.arity, message, &mut meter)?;
    let setup_steps = meter.used;
    let mut counter = Counter::default();
    let mut answers = Vec::with_capacity(targets.len());
    let mut queries = Vec::with_capacity(targets.len());
    for (input, target) in request.targets.iter().zip(targets) {
        let before = meter.used;
        let count = prepared.count(&target, &mut counter, &mut meter)?;
        let witness = prepared.witness(&target, &mut counter, &mut meter)?;
        if witness.is_none() != count.is_zero() {
            return Err(integrity("structured count/witness disagreement"));
        }
        let witness = witness
            .map(|v| v.iter().map(coordinates).collect::<Result<Vec<_>>>())
            .transpose()?;
        answers.push(Answer {
            target: input.clone(),
            count: count.to_string(),
            witness,
        });
        queries.push(json!({"charged_steps":meter.used-before}));
    }
    let diagnostics = json!({"setup_charged_steps":setup_steps,"query_diagnostics":queries,"total_charged_steps":meter.used,
        "contractions":counter.statistics.contractions,"last_backend":format!("{:?}",counter.statistics.last_backend),
        "graph_edges":prepared.network().edge_count(),"graph_vertices":prepared.network().vertex_count(),
        "maximum_degree":prepared.network().maximum_degree(),"membership_message":message_diagnostics,
        "unit":"uncalibrated native diagnostic steps; not timing or complete bit costs"});
    let semantic = Semantic {
        request,
        relation_policy: POLICY.into(),
        answers,
    };
    Ok(Receipt {
        schema: RECEIPT_SCHEMA.into(),
        semantic_sha256: semantic_digest(&semantic)?,
        semantic,
        selected_source_pins: source_pins(),
        diagnostics,
        standing: STANDING.into(),
    })
}
fn parse<T: serde::de::DeserializeOwned>(text: &str) -> Result<T> {
    if text.len() as u64 > MAX_JSON_BYTES {
        return Err(invalid("structured JSON exceeds one MiB"));
    }
    // Deserialize records directly: a Value intermediary would discard duplicate keys.
    serde_json::from_str(text).map_err(json_error)
}
/// Execute a strict versioned request. One explicit budget spans validation,
/// shared setup, and every count-plus-witness query; failure emits no receipt.
pub fn execute_json(text: &str) -> Result<Value> {
    value(&execute(parse(text)?)?)
}

/// Recompute semantic answers using the same selected source revision. Diagnostic
/// counters are outside the semantic digest. This is not independent attestation.
pub fn replay_json(text: &str) -> Result<Value> {
    let receipt: Receipt = parse(text)?;
    if receipt.schema != RECEIPT_SCHEMA
        || receipt.standing != STANDING
        || receipt.selected_source_pins != source_pins()
        || receipt.semantic.relation_policy != POLICY
        || receipt.semantic_sha256 != semantic_digest(&receipt.semantic)?
    {
        return Err(integrity(
            "structured receipt schema, source, policy or digest",
        ));
    }
    let expected = value(&receipt.semantic)?;
    let actual = execute(receipt.semantic.request)?;
    if value(&actual.semantic)? != expected || actual.semantic_sha256 != receipt.semantic_sha256 {
        return Err(integrity("structured semantic replay differs"));
    }
    Ok(
        json!({"schema":"structured-prime-ic-replay/v1","status":"replayed","semantic_sha256":actual.semantic_sha256,
        "independence":"same_native_implementation","standing":STANDING}),
    )
}
fn read(path: &str) -> Result<String> {
    let input: Box<dyn Read> = if path == "-" {
        Box::new(std::io::stdin())
    } else {
        Box::new(std::fs::File::open(path).map_err(json_error)?)
    };
    let mut bytes = Vec::new();
    input
        .take(MAX_JSON_BYTES + 1)
        .read_to_end(&mut bytes)
        .map_err(json_error)?;
    if bytes.len() as u64 > MAX_JSON_BYTES {
        return Err(invalid("structured JSON exceeds one MiB"));
    }
    String::from_utf8(bytes).map_err(json_error)
}
/// Shared native command front end, reused by both repository consumer paths.
/// Request/receipt paths accept `-` for stdin; successful output is one JSON value.
pub fn command_line() -> Result<()> {
    let args = std::env::args().skip(1).collect::<Vec<_>>();
    let output = match args.as_slice() {
        [help] if help == "--help" => {
            println!("tensor-structured REQUEST\ntensor-structured replay RECEIPT\nUse - for stdin. Exact bounded counts and prefix witnesses; local membership messages are reused.\nA shared work budget covers setup and all queries. Receipts are producer assertions.");
            return Ok(());
        }
        [path] => execute_json(&read(path)?)?,
        [operation, path] if operation == "replay" => replay_json(&read(path)?)?,
        _ => return Err(invalid("usage: tensor-structured REQUEST | replay RECEIPT")),
    };
    println!(
        "{}",
        serde_json::to_string_pretty(&output).map_err(json_error)?
    );
    Ok(())
}
