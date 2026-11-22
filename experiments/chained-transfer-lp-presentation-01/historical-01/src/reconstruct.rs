//! Independent raw-row reconstruction for replay. Signed integer sums are
//! reduced only after complete rows; producer arithmetic/maps are not called.
use crate::{
    assembly::{Column, Origin, Presentation, RawRowMap, Term},
    rooted_uncapped,
    types::{Available, Sparse},
};
use chained_transfer_lp_finite_projection_01::Matrix;

fn add_occurrence(
    row: &mut [i128],
    terms: &mut Vec<Term>,
    pos: Option<usize>,
    coefficient: i128,
    modulus: i128,
) {
    if let Some(index) = pos {
        row[index] += coefficient;
    }
    terms.push(Term {
        column: pos,
        coefficient: coefficient.rem_euclid(modulus) as u64,
    });
}

fn captured_rows(rows: &[Sparse], width: usize, modulus: i128) -> Matrix {
    let mut output = Vec::new();
    for sparse in rows {
        let mut sums = vec![0i128; width];
        for &(index, coefficient) in sparse {
            sums[index as usize] += i128::from(coefficient);
        }
        output.push(
            sums.into_iter()
                .map(|value| value.rem_euclid(modulus) as u64)
                .collect(),
        );
    }
    Matrix {
        ncols: width,
        rows: output,
    }
}

pub fn reconstruct(available: &Available, prime: u64) -> Result<Presentation, String> {
    // Shared validation is representational and rejects rather than filters.
    // All mathematical row/column construction below is separate code.
    available.validate(prime)?;
    let modulus = i128::from(prime);
    let graph = &available.graph;
    let lp_columns = graph.vertex_points.len();
    let width = lp_columns
        .checked_add(available.columns)
        .ok_or("replay width overflow")?;
    let mut columns = Vec::new();
    for (vertex, &point) in graph.vertex_points.iter().enumerate() {
        columns.push(Column::LargePrime { vertex, point });
    }
    // Build the FB-index address table from emitted column positions, rather
    // than the producer's direct offset formula. Index zero has no variable.
    let mut fb_address = vec![None; available.factor_base.len()];
    for (index, (&point, address)) in available
        .factor_base
        .iter()
        .zip(&mut fb_address)
        .enumerate()
        .skip(1)
    {
        *address = Some(columns.len());
        columns.push(Column::FactorBase { index, point });
    }
    let eta_address = columns.len();
    columns.push(Column::Eta);
    if columns.len() != width {
        return Err("replay column width mismatch".into());
    }

    let mut a_rows = Vec::new();
    let mut row_map = Vec::new();
    let origins = (0..graph.full.len())
        .map(|index| Origin::Full { index })
        .chain((0..graph.ground.len()).map(|index| Origin::Ground { index }))
        .chain((0..graph.edges.len()).map(|index| Origin::Edge { index }));
    for origin in origins {
        let mut row = vec![0i128; width];
        let mut terms = Vec::new();
        match origin {
            Origin::Full { index } => {
                for &(fb, multiplicity) in &graph.full[index] {
                    add_occurrence(
                        &mut row,
                        &mut terms,
                        fb_address[fb as usize],
                        i128::from(multiplicity),
                        modulus,
                    );
                }
            }
            Origin::Ground { index } => {
                let (vertex, factors, half) = &graph.ground[index];
                for &(fb, multiplicity) in factors {
                    add_occurrence(
                        &mut row,
                        &mut terms,
                        fb_address[fb as usize],
                        i128::from(multiplicity),
                        modulus,
                    );
                }
                add_occurrence(
                    &mut row,
                    &mut terms,
                    Some(*vertex as usize),
                    if *half { 2 } else { 1 },
                    modulus,
                );
            }
            Origin::Edge { index } => {
                let (x, y, first, second) = graph.edges[index];
                for fb in [first, second] {
                    add_occurrence(&mut row, &mut terms, fb_address[fb as usize], 1, modulus);
                }
                for vertex in [x, y] {
                    add_occurrence(&mut row, &mut terms, Some(vertex as usize), 1, modulus);
                }
            }
        }
        add_occurrence(&mut row, &mut terms, Some(eta_address), -1, modulus);
        a_rows.push(
            row.into_iter()
                .map(|sum| sum.rem_euclid(modulus) as u64)
                .collect::<Vec<_>>(),
        );
        row_map.push(RawRowMap { origin, terms });
    }
    let captured_full = captured_rows(&available.full_rows, available.columns, modulus);
    if captured_full.rows.len() != graph.full.len() {
        return Err("replay missing raw full occurrence".into());
    }
    for (raw, captured) in a_rows.iter().zip(&captured_full.rows) {
        if raw[lp_columns..] != captured[..] {
            return Err("replay raw/captured full row disagreement".into());
        }
    }
    let mut baseline = captured_full;
    let combined = captured_rows(
        &available.combined_lp_cycle_rows,
        available.columns,
        modulus,
    );
    baseline.rows.extend(combined.rows);
    // The protocol requires this literal original routine in both arms. It is
    // recomputed from source-bound raw records, never trusted from a certificate.
    let (original_rooted_rows, original_rooted_receipt) =
        rooted_uncapped(graph, prime, available.eta_column);
    let mut uncapped = baseline.clone();
    uncapped
        .rows
        .extend(captured_rows(&original_rooted_rows, available.columns, modulus).rows);
    Ok(Presentation {
        lp_columns,
        omitted_basepoint: available.factor_base[0],
        columns,
        row_map,
        a: Matrix {
            ncols: width,
            rows: a_rows,
        },
        baseline,
        uncapped,
        original_rooted_rows,
        original_rooted_receipt,
    })
}
