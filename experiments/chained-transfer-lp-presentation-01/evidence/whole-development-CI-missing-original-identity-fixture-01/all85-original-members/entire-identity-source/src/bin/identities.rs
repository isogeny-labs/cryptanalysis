use chained_transfer_lp_presentation_01::{
    foundation_statements,
    hash::sha256::sha256,
    identity_certificate::{check_with_extra, issue, Expr, IssueError, ProofRef, Verdict},
};
use serde_json::{json, Value};
use std::{error::Error, fs, path::Path};

fn write(path: &Path, value: &Value) -> Result<(), Box<dyn Error>> {
    let mut text = serde_json::to_string_pretty(value)?;
    text.push('\n');
    fs::write(path, text)?;
    Ok(())
}

fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<_> = std::env::args().collect();
    if args.len() != 3 {
        return Err("usage: lp-foundation-identities OUTPUT_DIR LEAN_SOURCE".into());
    }
    let out = Path::new(&args[1]);
    fs::create_dir(out)?;
    let proof_bytes = fs::read(&args[2])?;
    let proof_sha: String = sha256(&proof_bytes)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    let mut receipts = Vec::new();
    for statement in foundation_statements() {
        let name = statement.name.clone();
        let proof = ProofRef {
            kind: "lean4".into(),
            path: "experiments/chained-transfer-lp-presentation-01/lean/LPProjection.lean".into(),
            sha256: proof_sha.clone(),
        };
        let cert = issue(statement.clone(), 0x4c50_3031, 32, "Unchanged original identity module invoked by producing developer; unsigned deterministic development checks. Proof is only a pointer; separate original Lean gates must be inspected.", Some(proof))?;
        let verdict = check_with_extra(&cert, Some((0x6c69_6674, 32)))?;
        let Verdict::Accept {
            points,
            extra_points,
            false_accept_log2,
        } = verdict
        else {
            return Err(format!("unexpected positive rejection: {verdict:?}").into());
        };
        write(
            &out.join(format!("{name}.certificate.json")),
            &serde_json::to_value(&cert)?,
        )?;
        let mut wrong = statement;
        wrong.name = format!("negative_{name}_plus_one");
        wrong.rhs = Expr::plus(wrong.rhs, Expr::Const(1));
        let negative = match issue(
            wrong.clone(),
            0x4c50_3031,
            32,
            "whole false identity control; no certificate on rejection",
            None,
        ) {
            Err(IssueError::False(c)) => {
                json!({"statement": wrong, "actual_original_issuer": "False", "certificate_issued": false, "counterexample": {"index": c.index, "assignment": c.assignment, "lhs": c.lhs, "rhs": c.rhs}})
            }
            other => {
                return Err(
                    format!("negative was not a false-identity rejection: {other:?}").into(),
                )
            }
        };
        write(&out.join(format!("{name}.whole-negative.json")), &negative)?;
        receipts.push(json!({"name": name, "points": points, "extra_points": extra_points, "false_accept_log2": false_accept_log2, "original_checker": "Accept", "original_false_identity_control": "False"}));
    }
    write(
        &out.join("development-receipt.json"),
        &json!({"schema": "chained.lp.foundation/v1", "identities": receipts, "proof_source_sha256": proof_sha, "scope": "known identities over original checker's modulus2^61-1; Lean source separately audited; no fixed-q223 run or numerical/global-character/novelty/cost claim", "standing": "unsigned producer data"}),
    )?;
    println!("four known identities, 32 original and 32 extra checker points each; four whole false controls rejected");
    Ok(())
}
