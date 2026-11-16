//! Native affine projection of two-summand S3 over word binary fields.
//!
//! This adapts the existing `pdp-degree-heuristics/htsolver.py` construction.
//! A linear Artin–Schreier section covers even and odd extension degrees.
//! The output is abscissa pairs only; a caller must lift and check group sums.
use super::ic_boundary::ArtinSchreier;
use super::semaev_decomp::Gf2;

#[derive(Debug, PartialEq, Eq)]
pub enum ProjectionError {
    ZeroAbscissa,
    OutsideField,
    ResidualCap { dimension: usize, limit: usize },
}

#[derive(Debug)]
pub struct ProjectionRoots {
    pub pairs: Vec<(u64, u64)>,
    pub residual_dimension: usize,
    pub affine_candidates: u64,
}

/// Prepared target-independent subspace data. Its construction is setup work.
pub struct S3AffineProjection {
    gf: Gf2,
    ash: ArtinSchreier,
    b: u64,
    basis: Vec<u64>,
    section_squares: Vec<u64>,
    product_checks: Vec<u64>,
    trace_row: u64,
    trace_one: u64,
    membership: [u64; 64],
    prefix: bool,
    inverse_squares: Option<Vec<u64>>,
}

fn parity(x: u64) -> u64 {
    u64::from(x.count_ones() & 1)
}

fn insert(pivots: &mut [u64; 64], mut value: u64) -> bool {
    while value != 0 {
        let bit = 63 - value.leading_zeros() as usize;
        if pivots[bit] == 0 {
            pivots[bit] = value;
            return true;
        }
        value ^= pivots[bit];
    }
    false
}

/// Highest-bit pivots are triangular; solve from low bits to high bits.
fn affine_space(
    rows: impl IntoIterator<Item = (u64, u64)>,
    nvars: usize,
) -> Option<(u64, Vec<u64>)> {
    let mut pivots = [None; 64];
    for (mut mask, mut rhs) in rows {
        while mask != 0 {
            let bit = 63 - mask.leading_zeros() as usize;
            if let Some((row, value)) = pivots[bit] {
                mask ^= row;
                rhs ^= value;
            } else {
                pivots[bit] = Some((mask, rhs));
                break;
            }
        }
        if mask == 0 && rhs != 0 {
            return None;
        }
    }
    let solve = |mut x: u64, homogeneous: bool| {
        for (bit, row) in pivots.iter().enumerate().take(nvars) {
            if let Some((mask, rhs)) = row {
                let wanted = if homogeneous { 0 } else { *rhs };
                if parity(mask & x) != wanted {
                    x ^= 1 << bit;
                }
            }
        }
        x
    };
    let particular = solve(0, false);
    let free = (0..nvars)
        .filter(|&bit| pivots[bit].is_none())
        .map(|bit| solve(1 << bit, true))
        .collect();
    Some((particular, free))
}

fn linear_combination(basis: &[u64], coefficients: u64) -> u64 {
    basis.iter().enumerate().fold(0, |sum, (i, &v)| {
        if coefficients >> i & 1 != 0 {
            sum ^ v
        } else {
            sum
        }
    })
}

impl S3AffineProjection {
    pub fn new(gf: &Gf2, b: u64, basis: &[u64]) -> Result<Self, &'static str> {
        if basis.is_empty() || basis.len() > 32 {
            return Err("subspace dimension must be in 1..=32");
        }
        if b & !gf.mask != 0 || basis.iter().any(|v| v & !gf.mask != 0) {
            return Err("coefficient outside the word field");
        }
        let mut membership = [0; 64];
        if basis.iter().any(|&v| !insert(&mut membership, v)) {
            return Err("subspace basis is dependent");
        }
        let ash = ArtinSchreier::new(gf);
        let trace_one = (0..gf.n)
            .map(|i| 1 << i)
            .find(|&v| ash.trace(v) == 1)
            .ok_or("field trace has no trace-one element")?;
        let section = |c| {
            ash.solve(c ^ if ash.trace(c) == 1 { trace_one } else { 0 })
                .expect("trace-zero input has an Artin-Schreier preimage")
        };
        let section_squares = basis.iter().map(|&v| section(gf.sqr(v))).collect();
        let mut products = Vec::new();
        for (j, &v) in basis.iter().enumerate() {
            for &w in &basis[..=j] {
                products.push((gf.mul(v, w), 0));
            }
        }
        let (_, product_checks) = affine_space(products, gf.n as usize).unwrap();
        let trace_row = basis
            .iter()
            .enumerate()
            .fold(0, |row, (i, &v)| row | (ash.trace(v) << i));
        let prefix = basis.iter().all(|v| v >> basis.len() == 0);
        Ok(Self {
            gf: gf.clone(),
            ash,
            b,
            basis: basis.to_vec(),
            section_squares,
            product_checks,
            trace_row,
            trace_one,
            membership,
            prefix,
            inverse_squares: None,
        })
    }

    /// Target-independent prefix cache. Its caller must charge this setup.
    /// One batch inversion prepares all nonzero sums; dimension is bounded.
    pub fn prepare_prefix_inverse_cache(&mut self) -> Result<(), &'static str> {
        if !self.prefix || self.basis.len() > 12 {
            return Err("inverse cache requires a prefix subspace of dimension at most12");
        }
        let mut values: Vec<u64> = (0..1u64 << self.basis.len()).collect();
        self.gf.batch_inv(&mut values, &mut Vec::new());
        for v in &mut values {
            *v = self.gf.sqr(*v);
        }
        self.inverse_squares = Some(values);
        Ok(())
    }

    pub fn inverse_cache_bytes(&self) -> usize {
        self.inverse_squares
            .as_ref()
            .map_or(0, |v| v.len() * std::mem::size_of::<u64>())
    }

    fn section(&self, c: u64) -> u64 {
        self.ash
            .solve(
                c ^ if self.ash.trace(c) == 1 {
                    self.trace_one
                } else {
                    0
                },
            )
            .expect("trace-zero input has an Artin-Schreier preimage")
    }

    fn contains(&self, mut x: u64) -> bool {
        if self.prefix {
            return x >> self.basis.len() == 0;
        }
        while x != 0 {
            let bit = 63 - x.leading_zeros() as usize;
            if self.membership[bit] == 0 {
                return false;
            }
            x ^= self.membership[bit];
        }
        true
    }

    /// All unordered subspace pairs satisfying S3(x,y,z)=0 for nonzero z.
    /// A residual cap is an explicit error, never an unsatisfiable verdict.
    pub fn roots(
        &self,
        z: u64,
        max_residual_dimension: usize,
    ) -> Result<ProjectionRoots, ProjectionError> {
        if z == 0 {
            return Err(ProjectionError::ZeroAbscissa);
        }
        if z & !self.gf.mask != 0 {
            return Err(ProjectionError::OutsideField);
        }
        let d = self.basis.len();
        let inverse = self.gf.inv(z);
        let constant = self.gf.mul(self.b, self.gf.sqr(inverse));
        let constant_product = self.gf.mul(z, self.section(constant));
        let mut columns: Vec<u64> = self
            .section_squares
            .iter()
            .map(|&v| self.gf.mul(z, v))
            .collect();
        columns.push(z); // the joint epsilon unknown, instead of two affine solves
        let mut rows: Vec<(u64, u64)> = self
            .product_checks
            .iter()
            .map(|&h| {
                let mask = columns
                    .iter()
                    .enumerate()
                    .fold(0, |row, (i, &v)| row | (parity(h & v) << i));
                (mask, parity(h & constant_product))
            })
            .collect();
        rows.push((self.trace_row, self.ash.trace(constant)));
        let Some((particular, free)) = affine_space(rows, d + 1) else {
            return Ok(ProjectionRoots {
                pairs: Vec::new(),
                residual_dimension: 0,
                affine_candidates: 0,
            });
        };
        if free.len() > max_residual_dimension {
            return Err(ProjectionError::ResidualCap {
                dimension: free.len(),
                limit: max_residual_dimension,
            });
        }
        let directions: Vec<(u64, u64)> = free
            .iter()
            .map(|&v| {
                (
                    linear_combination(&self.basis, v),
                    linear_combination(&columns, v),
                )
            })
            .collect();
        let mut sum = linear_combination(&self.basis, particular);
        let mut product = constant_product ^ linear_combination(&columns, particular);
        let candidates = 1u64 << free.len();
        let mut pairs = Vec::new();
        for i in 0..candidates {
            if i != 0 {
                let (s, p) = directions[i.trailing_zeros() as usize];
                sum ^= s;
                product ^= p;
            }
            let x = if sum == 0 {
                self.gf.sqr_k(product, self.gf.n - 1)
            } else {
                let inverse_square = self.inverse_squares.as_ref().map_or_else(
                    || self.gf.inv(self.gf.sqr(sum)),
                    |cache| cache[sum as usize],
                );
                let c = self.gf.mul(product, inverse_square);
                let Some(root) = self.ash.solve(c) else {
                    continue;
                };
                self.gf.mul(sum, root)
            };
            let y = x ^ sum;
            if self.contains(x) && self.contains(y) {
                pairs.push((x.min(y), x.max(y)));
            }
        }
        pairs.sort_unstable();
        Ok(ProjectionRoots {
            pairs,
            residual_dimension: free.len(),
            affine_candidates: candidates,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::koblitz_index_calculus::find_irreducible_sparse;
    use crate::cryptanalysis::pq_descent_symbolic::semaev_s3_word;

    #[test]
    fn matches_every_subspace_pair_in_even_and_odd_fields() {
        for n in 2..=8 {
            let gf = Gf2::new(&find_irreducible_sparse(n).unwrap());
            for d in 1..=n.min(4) {
                for multiplier in [1, 3] {
                    let basis: Vec<u64> = (0..d).map(|i| gf.mul(multiplier, 1 << i)).collect();
                    let mut elements: Vec<_> = (0..1u64 << d)
                        .map(|mask| linear_combination(&basis, mask))
                        .collect();
                    elements.sort_unstable();
                    for b in [0, 1, gf.mask ^ 1] {
                        let plan = S3AffineProjection::new(&gf, b, &basis).unwrap();
                        for z in 1..=gf.mask {
                            let mut expected = Vec::new();
                            for (i, &x) in elements.iter().enumerate() {
                                for &y in &elements[i..] {
                                    if semaev_s3_word(&gf, b, x, y, z) == 0 {
                                        expected.push((x, y));
                                    }
                                }
                            }
                            let actual = plan.roots(z, 12).unwrap();
                            assert_eq!(
                                actual.pairs, expected,
                                "n={n} d={d} b={b} z={z} multiplier={multiplier}"
                            );
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn matches_dense_subspaces_through_the_word_boundary() {
        for n in [15, 18, 31, 53, 63] {
            let gf = Gf2::new(&find_irreducible_sparse(n).unwrap());
            let multiplier = (gf.mask >> 1) | 1;
            let basis: Vec<u64> = (0..4).map(|i| gf.mul(multiplier, 1 << i)).collect();
            let plan = S3AffineProjection::new(&gf, 0xb, &basis).unwrap();
            let mut elements: Vec<_> = (0..16).map(|m| linear_combination(&basis, m)).collect();
            elements.sort_unstable();
            for fixture in 1..=16u64 {
                let z = (fixture.wrapping_mul(0x9e37_79b9_7f4a_7c15) & gf.mask) | 1;
                let mut expected = Vec::new();
                for (i, &x) in elements.iter().enumerate() {
                    for &y in &elements[i..] {
                        if semaev_s3_word(&gf, 0xb, x, y, z) == 0 {
                            expected.push((x, y));
                        }
                    }
                }
                assert_eq!(
                    plan.roots(z, 12).unwrap().pairs,
                    expected,
                    "n={n} fixture={fixture}"
                );
            }
        }
    }

    #[test]
    fn prefix_inverse_cache_preserves_all_roots() {
        for n in [5, 6, 7, 8] {
            let gf = Gf2::new(&find_irreducible_sparse(n).unwrap());
            let basis = [1, 2, 4];
            let plain = S3AffineProjection::new(&gf, 3, &basis).unwrap();
            let mut cached = S3AffineProjection::new(&gf, 3, &basis).unwrap();
            cached.prepare_prefix_inverse_cache().unwrap();
            assert_eq!(cached.inverse_cache_bytes(), 8 * 8);
            for z in 1..=gf.mask {
                assert_eq!(
                    plain.roots(z, 12).unwrap().pairs,
                    cached.roots(z, 12).unwrap().pairs
                );
            }
            let mut other = S3AffineProjection::new(&gf, 3, &[1, 8]).unwrap();
            assert!(other.prepare_prefix_inverse_cache().is_err());
        }
    }

    #[test]
    fn reports_unsupported_inputs_and_caps_without_a_false_refutation() {
        let gf = Gf2::new(&find_irreducible_sparse(63).unwrap());
        assert!(S3AffineProjection::new(&gf, 1, &[1, 1]).is_err());
        assert!(S3AffineProjection::new(&gf, 1, &[0]).is_err());
        let basis: Vec<u64> = (0..32).map(|i| 1 << i).collect();
        let plan = S3AffineProjection::new(&gf, 1, &basis).unwrap();
        assert_eq!(plan.roots(0, 0).unwrap_err(), ProjectionError::ZeroAbscissa);
        assert_eq!(
            plan.roots(1 << 63, 0).unwrap_err(),
            ProjectionError::OutsideField
        );
        assert!(matches!(
            plan.roots(7, 0),
            Err(ProjectionError::ResidualCap { .. })
        ));
    }
}
