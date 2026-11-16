//! Synthetic fixtures, declared algebraic predictions and complete unit controls.
//! They contain no historical trace/answer. This module is separate from the
//! certificate producer and the independent row replayer.
use crate::{projection, Matrix, Operation, ProjectionCertificate};
use serde::{Deserialize, Serialize};

pub const PRIME: u64 = 101;

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Case {
    pub name: String,
    pub lp_columns: usize,
    pub full: Matrix,
    pub baseline: Matrix,
    pub uncapped: Matrix,
    pub expected_full_nullity: usize,
    pub expected_projection_dimension: usize,
    pub expected_zero_projections: usize,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Record {
    pub schema: String,
    pub case: Case,
    pub certificate: ProjectionCertificate,
}

fn edges(nlp: usize, ends: &[(usize, usize)]) -> Matrix {
    let ncols = nlp + ends.len();
    let mut rows = Vec::new();
    for (i, &(a, b)) in ends.iter().enumerate() {
        assert!(a < nlp && b < nlp);
        let mut row = vec![0; ncols];
        row[a] += 1;
        row[b] += 1;
        row[nlp + i] = 1;
        rows.push(row);
    }
    Matrix { ncols, rows }
}

fn literal(ncols: usize, rows: &[&[i64]]) -> Matrix {
    Matrix {
        ncols,
        rows: rows
            .iter()
            .map(|r| {
                r.iter()
                    .map(|x| x.rem_euclid(PRIME as i64) as u64)
                    .collect()
            })
            .collect(),
    }
}

fn case(
    name: &str,
    lp_columns: usize,
    full: Matrix,
    baseline: Matrix,
    full_nullity: usize,
    dimension: usize,
    zeros: usize,
) -> Case {
    Case {
        name: name.into(),
        lp_columns,
        full,
        uncapped: baseline.clone(),
        baseline,
        expected_full_nullity: full_nullity,
        expected_projection_dimension: dimension,
        expected_zero_projections: zeros,
    }
}

pub fn cases() -> Vec<Case> {
    let empty = |ncols| Matrix {
        ncols,
        rows: Vec::new(),
    };
    vec![
        case(
            "ungrounded_even_four_cycle",
            4,
            edges(4, &[(0, 1), (1, 2), (2, 3), (3, 0)]),
            empty(4),
            4,
            3,
            1,
        ),
        case(
            "lone_odd_triangle",
            3,
            edges(3, &[(0, 1), (1, 2), (2, 0)]),
            empty(3),
            3,
            3,
            0,
        ),
        case(
            "two_odd_triangles_same_component",
            5,
            edges(5, &[(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]),
            empty(6),
            5,
            5,
            0,
        ),
        case(
            "two_odd_triangles_disconnected",
            6,
            edges(6, &[(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)]),
            empty(6),
            6,
            6,
            0,
        ),
        case(
            "grounded_chain",
            2,
            literal(5, &[&[1, 0, 1, 0, 0], &[1, 1, 0, 1, 0], &[0, 1, 0, 0, 1]]),
            literal(3, &[&[1, -1, 1]]),
            2,
            2,
            0,
        ),
        case(
            "half_grounded_chain",
            2,
            literal(5, &[&[2, 0, 1, 0, 0], &[1, 1, 0, 1, 0], &[0, 2, 0, 0, 1]]),
            literal(3, &[&[1, -2, 1]]),
            2,
            2,
            0,
        ),
        case(
            "repeated_vertex_occurrence",
            1,
            edges(1, &[(0, 0)]),
            empty(1),
            1,
            1,
            0,
        ),
        case(
            "duplicate_complete_rows",
            2,
            literal(3, &[&[1, 1, 1], &[1, 1, 1]]),
            empty(1),
            2,
            1,
            1,
        ),
        case(
            "disconnected_isolated_vertex",
            3,
            edges(3, &[(0, 1)]),
            empty(1),
            3,
            1,
            2,
        ),
        case("empty_rows", 2, empty(5), empty(3), 5, 3, 2),
        case("no_FB_columns", 2, empty(2), empty(0), 2, 0, 2),
        case(
            "zero_width_zero_row",
            0,
            literal(0, &[&[]]),
            empty(0),
            0,
            0,
            0,
        ),
        case(
            "pure_FB_constraint",
            0,
            literal(2, &[&[1, -1]]),
            literal(2, &[&[1, -1]]),
            1,
            1,
            0,
        ),
        case(
            "parallel_edges_distinct_payloads",
            2,
            edges(2, &[(0, 1), (0, 1)]),
            empty(2),
            2,
            1,
            1,
        ),
    ]
}

pub fn record(case: Case) -> Result<Record, String> {
    let certificate = projection::produce(
        PRIME,
        &case.full,
        case.lp_columns,
        &case.baseline,
        &case.uncapped,
    )?;
    let result = Record {
        schema: "chained.lp.synthetic-projection/v1".into(),
        case,
        certificate,
    };
    verify_record(&result)?;
    Ok(result)
}

pub fn verify_record(record: &Record) -> Result<(), String> {
    if record.schema != "chained.lp.synthetic-projection/v1" {
        return Err("development schema mismatch".into());
    }
    let expected = cases()
        .into_iter()
        .find(|c| c.name == record.case.name)
        .ok_or("unknown synthetic case")?;
    if record.case != expected {
        return Err("synthetic source fixture binding mismatch".into());
    }
    projection::verify(
        PRIME,
        &expected.full,
        expected.lp_columns,
        &expected.baseline,
        &expected.uncapped,
        &record.certificate,
    )?;
    let c = &record.certificate;
    let zeros =
        c.p.input
            .rows
            .iter()
            .filter(|r| r.iter().all(|&x| x == 0))
            .count();
    if c.a.kernel.len() != expected.expected_full_nullity
        || c.p.pivots.len() != expected.expected_projection_dimension
        || zeros != expected.expected_zero_projections
    {
        return Err(
            "independently replayed output disagrees with declared synthetic algebraic prediction"
                .into(),
        );
    }
    Ok(())
}

pub fn whole_negative_records() -> Result<Vec<(String, serde_json::Value)>, String> {
    let all = cases();
    let even = record(all[0].clone())?;
    let isolated = record(all[8].clone())?;
    let mut output = Vec::new();
    let mut changed = even.clone();
    let Operation::Scale { coefficient, .. } = changed
        .certificate
        .a
        .operations
        .iter_mut()
        .find(|o| matches!(o, Operation::Scale { .. }))
        .ok_or("no scale in even fixture")?
    else {
        unreachable!()
    };
    *coefficient = 0;
    output.push((
        "row_operation_coefficient".into(),
        serde_json::to_value(changed).map_err(|e| e.to_string())?,
    ));
    let mut changed = even.clone();
    let pivot = changed.certificate.c.pivots[0];
    changed.certificate.c.kernel[0][pivot] = (changed.certificate.c.kernel[0][pivot] + 1) % PRIME;
    output.push((
        "constrained_kernel_coordinate".into(),
        serde_json::to_value(changed).map_err(|e| e.to_string())?,
    ));
    let zero = isolated
        .certificate
        .p
        .input
        .rows
        .iter()
        .position(|v| v.iter().all(|&x| x == 0))
        .ok_or("no zero projection in isolated fixture")?;
    let mut changed = isolated.clone();
    changed.certificate.a.kernel.remove(zero);
    output.push((
        "missing_full_basis_vector".into(),
        serde_json::to_value(changed).map_err(|e| e.to_string())?,
    ));
    let mut changed = isolated;
    changed.certificate.p.input.rows.remove(zero);
    output.push((
        "missing_zero_projection".into(),
        serde_json::to_value(changed).map_err(|e| e.to_string())?,
    ));
    let mut changed = even.clone();
    changed.certificate.constraint_kernel_lifts[0].full_vector[0] =
        (changed.certificate.constraint_kernel_lifts[0].full_vector[0] + 1) % PRIME;
    output.push((
        "constrained_full_lift_coordinate".into(),
        serde_json::to_value(changed).map_err(|e| e.to_string())?,
    ));
    let mut changed = even.clone();
    changed.certificate.a.input.rows[0][0] = (changed.certificate.a.input.rows[0][0] + 1) % PRIME;
    output.push((
        "raw_coefficient_source_binding".into(),
        serde_json::to_value(changed).map_err(|e| e.to_string())?,
    ));
    let mut changed = serde_json::to_value(even).map_err(|e| e.to_string())?;
    changed["known_log"] = serde_json::json!(37);
    output.push(("unexpected_oracle_field".into(), changed));
    Ok(output)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn every_declared_graph_replays_with_complete_bases_and_lifts() {
        for case in cases() {
            record(case).unwrap();
        }
    }

    #[test]
    fn every_whole_negative_is_rejected() {
        for (name, value) in whole_negative_records().unwrap() {
            match serde_json::from_value::<Record>(value) {
                Ok(record) => assert!(verify_record(&record).is_err(), "accepted {name}"),
                Err(_) => assert_eq!(name, "unexpected_oracle_field"),
            }
        }
    }

    #[test]
    fn inconsistent_baseline_is_an_implementation_rejection() {
        let c = cases().remove(0);
        let wrong = literal(4, &[&[1, 0, 0, 0]]);
        assert!(
            projection::produce(PRIME, &c.full, c.lp_columns, &wrong, &wrong)
                .unwrap_err()
                .contains("inclusion residual")
        );
    }

    #[test]
    fn uncapped_arm_must_retain_the_entire_baseline_prefix() {
        let c = cases().remove(4);
        assert!(projection::produce(
            PRIME,
            &c.full,
            c.lp_columns,
            &c.baseline,
            &Matrix {
                ncols: 3,
                rows: vec![]
            }
        )
        .is_err());
    }

    #[test]
    fn duplicate_source_rows_and_vertex_occurrences_remain_literal() {
        let all = cases();
        let repeated = record(all[6].clone()).unwrap();
        assert_eq!(repeated.certificate.a.input.rows[0][0], 2);
        let duplicate = record(all[7].clone()).unwrap();
        assert_eq!(duplicate.certificate.a.input.rows.len(), 2);
        assert_eq!(
            duplicate.certificate.p.input.rows.len(),
            duplicate.certificate.a.kernel.len()
        );
    }

    #[test]
    fn ragged_noncanonical_and_undeclared_field_inputs_are_rejected() {
        for input in [
            literal(2, &[&[1]]),
            Matrix {
                ncols: 1,
                rows: vec![vec![101]],
            },
        ] {
            assert!(crate::producer::produce(PRIME, &input).is_err());
        }
        assert!(crate::producer::produce(15, &literal(1, &[&[1]])).is_err());
    }
}
