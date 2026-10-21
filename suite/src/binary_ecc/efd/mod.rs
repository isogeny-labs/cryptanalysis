//! The linked EFD binary-field catalogue: 135 programs, 19 representations.
//!
//! These are opt-in reference operations over the existing polynomial-basis
//! field. They do not replace the affine implementation or a rho walk. A
//! formula's mixed-input restrictions and cached-parameter assumptions are
//! checked; callers of the low-level evaluator still supply valid model points
//! and, for differential operations, the stated point difference.
//!
//! See `docs/efd/README.md` for sources, charts, exceptional cases and coverage.
use super::f2m::{F2mElement, IrreduciblePoly};
use serde::Deserialize;
use std::collections::BTreeMap;
use std::sync::OnceLock;

mod checked;
mod formats;
mod program;
#[cfg(test)]
mod tests;

pub use checked::{weierstrass_operation, CheckedPoint, ExecutionPath};
pub use formats::Projection;
pub use program::{OperationCounts, Program};

pub type Bindings = BTreeMap<String, F2mElement>;
pub type Result<T> = std::result::Result<T, EfdError>;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EfdError {
    Syntax(String),
    MissingInput(String),
    Assumption(String),
    FieldMismatch,
    ZeroDenominator,
    OutsideChart,
    InvalidPoint,
    Unsupported(String),
}
impl std::fmt::Display for EfdError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for EfdError {}

#[derive(Debug, Deserialize)]
pub struct Source {
    pub url: String,
    pub sha256: String,
    pub text: String,
}
#[derive(Debug, Deserialize)]
pub struct Model {
    pub id: String,
    pub source: Source,
}
#[derive(Debug, Deserialize)]
pub struct Representation {
    pub id: String,
    pub page_url: String,
    pub variables: Vec<String>,
    pub relations: Vec<String>,
    pub assumptions: Vec<String>,
    pub source: Source,
}
#[derive(Debug, Deserialize)]
pub struct Formula {
    pub id: String,
    pub representation: String,
    pub operation: String,
    pub name: String,
    pub assumptions: Vec<String>,
    pub record: Source,
    pub program: Source,
    pub upstream_verification_url: String,
}
#[derive(Debug, Deserialize)]
pub struct Catalogue {
    pub schema: String,
    pub source_url: String,
    pub characteristic: u32,
    pub models: Vec<Model>,
    pub representations: Vec<Representation>,
    pub formulas: Vec<Formula>,
}
impl Catalogue {
    pub fn formula(&self, id: &str) -> Option<&Formula> {
        self.formulas.iter().find(|f| f.id == id)
    }
    pub fn representation(&self, id: &str) -> Option<&Representation> {
        self.representations.iter().find(|r| r.id == id)
    }
}

/// Pinned mathematical records and three-operand code, with per-source hashes.
pub fn catalogue() -> &'static Catalogue {
    static C: OnceLock<Catalogue> = OnceLock::new();
    C.get_or_init(|| {
        serde_json::from_str(include_str!("catalogue.json")).expect("checked EFD catalogue")
    })
}

impl Formula {
    pub fn compile(&self) -> Result<Program> {
        Program::compile(self)
    }
    /// Evaluate a reference program. No strings are evaluated as Rust or shell.
    /// Cache parameters with defining assumptions are derived if absent and
    /// verified if supplied. Point and differential-relation validity are the
    /// caller's responsibility. Use `weierstrass_operation` for checked ADD/DBL.
    pub fn evaluate(&self, field: &IrreduciblePoly, inputs: &Bindings) -> Result<Bindings> {
        self.compile()?.evaluate(field, inputs)
    }
}

pub(super) fn check_field(field: &IrreduciblePoly, inputs: &Bindings) -> Result<()> {
    if field.degree < 2
        || field.low_terms.iter().any(|&i| i >= field.degree)
        || inputs.values().any(|v| v.m_value() != field.degree)
    {
        return Err(EfdError::FieldMismatch);
    }
    // Like the existing field API, this trusts the supplied polynomial to be
    // irreducible. It does not infer field identity from degree alone.
    Ok(())
}
