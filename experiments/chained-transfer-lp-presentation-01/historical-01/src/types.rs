use serde::{Deserialize, Serialize};
use std::collections::HashSet;

pub type Point = [u64; 3];
pub type Sparse = Vec<(u32, u64)>;
pub type FactorPart = Vec<(u32, u8)>;
pub type Ground = (u32, FactorPart, bool);

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Graph {
    pub full: Vec<FactorPart>,
    pub ground: Vec<Ground>,
    pub edges: Vec<(u32, u32, u32, u32)>,
    pub vertex_points: Vec<Point>,
    pub pairs: u64,
    pub no_roots: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Available {
    pub factor_base: Vec<Point>,
    pub full_rows: Vec<Sparse>,
    pub combined_lp_cycle_rows: Vec<Sparse>,
    pub graph: Graph,
    pub columns: usize,
    pub eta_column: u32,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PublicCall {
    pub identity: [usize; 3],
    pub ell: u64,
    pub available: Available,
}

impl Available {
    /// Representation checks only: this does not assert points lie on a curve.
    pub fn validate(&self, prime: u64) -> Result<(), String> {
        if ![101, 2_773_073].contains(&prime) {
            return Err("undeclared scalar modulus".into());
        }
        if self.columns == 0
            || self.columns > 64
            || self.factor_base.len() != self.columns
            || self.eta_column as usize != self.columns - 1
        {
            return Err("factor-base width or eta position".into());
        }
        let mut seen = HashSet::new();
        for point in self.factor_base.iter().chain(&self.graph.vertex_points) {
            if point.iter().any(|&c| c >= 223)
                || point.iter().find(|&&c| c != 0) != Some(&1)
                || !seen.insert(*point)
            {
                return Err("noncanonical or repeated public point".into());
            }
        }
        let factor = |part: &[(u32, u8)], total: u64| -> Result<(), String> {
            if part
                .iter()
                .any(|&(i, mu)| i as usize >= self.columns || mu == 0)
                || part.iter().map(|&(_, mu)| u64::from(mu)).sum::<u64>() != total
            {
                return Err("raw factor-base index/multiplicity".into());
            }
            Ok(())
        };
        for row in &self.graph.full {
            factor(row, 4)?;
        }
        let vertices = self.graph.vertex_points.len();
        for (vertex, part, half) in &self.graph.ground {
            if *vertex as usize >= vertices {
                return Err("ground LP index".into());
            }
            factor(part, if *half { 2 } else { 3 })?;
        }
        for &(x, y, a, b) in &self.graph.edges {
            if x as usize >= vertices
                || y as usize >= vertices
                || a as usize >= self.columns
                || b as usize >= self.columns
            {
                return Err("edge LP/factor-base index".into());
            }
        }
        for row in self.full_rows.iter().chain(&self.combined_lp_cycle_rows) {
            if row
                .iter()
                .any(|&(c, a)| c as usize >= self.columns || a == 0 || a >= prime)
            {
                return Err("captured sparse coordinate/coefficient".into());
            }
        }
        Ok(())
    }
}

impl PublicCall {
    pub fn validate_fixed(&self) -> Result<(), String> {
        let [side, target, attempt] = self.identity;
        if side >= 3
            || target >= 5
            || attempt >= 4
            || self.ell != 2_773_073
            || self.available.columns != [30, 36, 48, 64][attempt]
        {
            return Err("fixed-population public identity/modulus/width".into());
        }
        self.available.validate(self.ell)
    }
}
