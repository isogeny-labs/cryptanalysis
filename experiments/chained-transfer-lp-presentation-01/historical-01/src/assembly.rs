use crate::{
    rooted_uncapped,
    types::{Available, Point, Sparse},
    RootedReceipt,
};
use chained_transfer_lp_finite_projection_01::Matrix;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "role", rename_all = "snake_case", deny_unknown_fields)]
pub enum Column {
    LargePrime { vertex: usize, point: Point },
    FactorBase { index: usize, point: Point },
    Eta,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Term {
    /// None records an original basepoint-index-zero occurrence, not a column.
    pub column: Option<usize>,
    pub coefficient: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Origin {
    Full { index: usize },
    Ground { index: usize },
    Edge { index: usize },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RawRowMap {
    pub origin: Origin,
    pub terms: Vec<Term>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Presentation {
    pub lp_columns: usize,
    pub omitted_basepoint: Point,
    pub columns: Vec<Column>,
    pub row_map: Vec<RawRowMap>,
    pub a: Matrix,
    pub baseline: Matrix,
    pub uncapped: Matrix,
    pub original_rooted_rows: Vec<Sparse>,
    pub original_rooted_receipt: RootedReceipt,
}

#[derive(Clone, Copy)]
struct Sum(u64);
impl Sum {
    fn add(self, a: u64, b: u64) -> u64 {
        ((u128::from(a) + u128::from(b)) % u128::from(self.0)) as u64
    }
}

fn dense_sparse(width: usize, rows: &[Sparse], f: Sum) -> Matrix {
    let rows = rows
        .iter()
        .map(|sparse| {
            let mut row = vec![0; width];
            for &(c, a) in sparse {
                row[c as usize] = f.add(row[c as usize], a);
            }
            row
        })
        .collect();
    Matrix { ncols: width, rows }
}

pub fn assemble(available: &Available, prime: u64) -> Result<Presentation, String> {
    available.validate(prime)?;
    let f = Sum(prime);
    let nv = available.graph.vertex_points.len();
    let width = nv
        .checked_add(available.columns)
        .ok_or("full width overflow")?;
    let factor = |i: u32, mu: u64| Term {
        column: if i == 0 {
            None
        } else {
            Some(nv + i as usize - 1)
        },
        coefficient: mu,
    };
    let lp = |vertex: u32, coefficient| Term {
        column: Some(vertex as usize),
        coefficient,
    };
    let eta = Term {
        column: Some(nv + available.eta_column as usize),
        coefficient: prime - 1,
    };
    let mut row_map = Vec::new();
    for (index, part) in available.graph.full.iter().enumerate() {
        let mut terms: Vec<_> = part
            .iter()
            .map(|&(i, mu)| factor(i, u64::from(mu)))
            .collect();
        terms.push(eta.clone());
        row_map.push(RawRowMap {
            origin: Origin::Full { index },
            terms,
        });
    }
    for (index, (vertex, part, half)) in available.graph.ground.iter().enumerate() {
        let mut terms: Vec<_> = part
            .iter()
            .map(|&(i, mu)| factor(i, u64::from(mu)))
            .collect();
        terms.push(lp(*vertex, if *half { 2 } else { 1 }));
        terms.push(eta.clone());
        row_map.push(RawRowMap {
            origin: Origin::Ground { index },
            terms,
        });
    }
    for (index, &(x, y, a, b)) in available.graph.edges.iter().enumerate() {
        row_map.push(RawRowMap {
            origin: Origin::Edge { index },
            terms: vec![factor(a, 1), factor(b, 1), lp(x, 1), lp(y, 1), eta.clone()],
        });
    }
    let rows: Vec<Vec<u64>> = row_map
        .iter()
        .map(|map| {
            let mut row = vec![0; width];
            for term in &map.terms {
                if let Some(c) = term.column {
                    row[c] = f.add(row[c], term.coefficient);
                }
            }
            row
        })
        .collect();
    let mut columns = Vec::new();
    for (vertex, point) in available.graph.vertex_points.iter().enumerate() {
        columns.push(Column::LargePrime {
            vertex,
            point: *point,
        });
    }
    for (index, point) in available.factor_base.iter().enumerate().skip(1) {
        columns.push(Column::FactorBase {
            index,
            point: *point,
        });
    }
    columns.push(Column::Eta);
    assert_eq!(columns.len(), width);
    let captured_full = dense_sparse(available.columns, &available.full_rows, f);
    let reconstructed_full: Vec<_> = rows
        .iter()
        .take(available.graph.full.len())
        .map(|r| r[nv..].to_vec())
        .collect();
    if captured_full.rows != reconstructed_full {
        return Err("captured full rows do not match every raw full occurrence".into());
    }
    let mut baseline = captured_full;
    baseline
        .rows
        .extend(dense_sparse(available.columns, &available.combined_lp_cycle_rows, f).rows);
    let (original_rooted_rows, original_rooted_receipt) =
        rooted_uncapped(&available.graph, prime, available.eta_column);
    let mut uncapped = baseline.clone();
    uncapped
        .rows
        .extend(dense_sparse(available.columns, &original_rooted_rows, f).rows);
    Ok(Presentation {
        lp_columns: nv,
        omitted_basepoint: available.factor_base[0],
        columns,
        row_map,
        a: Matrix { ncols: width, rows },
        baseline,
        uncapped,
        original_rooted_rows,
        original_rooted_receipt,
    })
}
