//! Complete finite matrices and projection certificates. No curve/field engine,
//! target character, historical solver output or recovered scalar is imported.
pub mod development;
pub mod producer;
pub mod projection;
pub mod replay;

use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Matrix {
    pub ncols: usize,
    pub rows: Vec<Vec<u64>>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "op", rename_all = "snake_case", deny_unknown_fields)]
pub enum Operation {
    Swap {
        a: usize,
        b: usize,
    },
    Scale {
        row: usize,
        coefficient: u64,
        inverse: u64,
    },
    Add {
        dst: usize,
        src: usize,
        coefficient: u64,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Certificate {
    pub modulus: u64,
    pub input: Matrix,
    pub operations: Vec<Operation>,
    pub rref: Matrix,
    pub pivots: Vec<usize>,
    pub kernel: Vec<Vec<u64>>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Lift {
    pub vector: Vec<u64>,
    pub image_coefficients: Vec<u64>,
    pub full_vector: Vec<u64>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProjectionCertificate {
    pub lp_columns: usize,
    pub a: Certificate,
    pub p: Certificate,
    pub c: Certificate,
    pub u: Certificate,
    /// All transformed A-kernel rows, including those whose projection is zero.
    pub transformed_full_lifts: Vec<Vec<u64>>,
    /// One full lift for every vector in the complete C-kernel basis, in order.
    pub constraint_kernel_lifts: Vec<Lift>,
}
