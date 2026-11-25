//! Signed gain graph with symbolic offsets in G and Q and a proof DAG.
//!
//! Potentials encode F_i = sign*F_root + a*G + b*Q. A component can
//! additionally anchor its root to a*G+b*Q. Every operation retains its
//! original-row linear combination; only the final dependency is expanded.
use crate::field::{add_mod, mul_mod, pow_mod, sub_mod};
use crate::{Error, MultiSignedRelation, Result, SignedRelation};

#[derive(Clone, Copy, Debug, Default)]
struct Potential {
    negative: bool,
    a: u64,
    b: u64,
    proof: usize,
}

#[derive(Clone, Copy, Debug)]
struct Anchor {
    a: u64,
    b: u64,
    proof: usize,
}

#[derive(Clone, Copy, Debug)]
enum Proof {
    Zero,
    Input(usize),
    Add {
        left: usize,
        right: usize,
        scale: u64,
    },
}

pub(crate) struct GainGraph {
    modulus: u64,
    parent: Vec<usize>,
    size: Vec<usize>,
    potential: Vec<Potential>,
    anchor: Vec<Option<Anchor>>,
    proofs: Vec<Proof>,
    max_proofs: usize,
    rank: usize,
}

pub(crate) struct Dependency {
    pub(crate) scalar: u64,
    pub(crate) weights: Vec<u64>,
}

impl GainGraph {
    pub(crate) fn new(columns: usize, modulus: u64, max_proofs: usize) -> Self {
        Self {
            modulus,
            parent: (0..columns).collect(),
            size: vec![1; columns],
            potential: vec![Potential::default(); columns],
            anchor: vec![None; columns],
            proofs: vec![Proof::Zero],
            max_proofs,
            rank: 0,
        }
    }
    fn signed(&self, value: u64, negative: bool) -> u64 {
        if negative && value != 0 {
            self.modulus - value
        } else {
            value
        }
    }
    fn sign(&self, negative: bool) -> u64 {
        if negative {
            self.modulus - 1
        } else {
            1
        }
    }
    fn node(&mut self, proof: Proof) -> Result<usize> {
        if self.proofs.len() >= self.max_proofs {
            return Err(Error::ResourceLimit("proof arena"));
        }
        let id = self.proofs.len();
        self.proofs.push(proof);
        Ok(id)
    }
    fn linear(&mut self, left: usize, right: usize, scale: u64) -> Result<usize> {
        if right == 0 || scale == 0 {
            return Ok(left);
        }
        if left == 0 && scale == 1 {
            return Ok(right);
        }
        self.node(Proof::Add { left, right, scale })
    }
    fn scale(&mut self, proof: usize, value: u64) -> Result<usize> {
        self.linear(0, proof, value)
    }
    fn find(&mut self, index: usize) -> Result<(usize, Potential)> {
        let parent = self.parent[index];
        if parent == index {
            return Ok((index, Potential::default()));
        }
        let edge = self.potential[index];
        let (root, up) = self.find(parent)?;
        if root == parent {
            return Ok((root, edge));
        }
        let full = Potential {
            negative: edge.negative ^ up.negative,
            a: add_mod(edge.a, self.signed(up.a, edge.negative), self.modulus),
            b: add_mod(edge.b, self.signed(up.b, edge.negative), self.modulus),
            proof: self.linear(edge.proof, up.proof, self.sign(edge.negative))?,
        };
        self.parent[index] = root;
        self.potential[index] = full;
        Ok((root, full))
    }
    fn finish(&self, a: u64, b: u64, proof: usize, relations: usize) -> Option<Dependency> {
        if b == 0 {
            return None;
        }
        let scalar = mul_mod(
            self.signed(a, true),
            pow_mod(b, self.modulus - 2, self.modulus),
            self.modulus,
        );
        let mut coefficients = vec![0; self.proofs.len()];
        let mut weights = vec![0; relations];
        coefficients[proof] = 1;
        for id in (1..self.proofs.len()).rev() {
            let coefficient = coefficients[id];
            if coefficient == 0 {
                continue;
            }
            match self.proofs[id] {
                Proof::Zero => {}
                Proof::Input(index) => {
                    weights[index] = add_mod(weights[index], coefficient, self.modulus)
                }
                Proof::Add { left, right, scale } => {
                    coefficients[left] = add_mod(coefficients[left], coefficient, self.modulus);
                    coefficients[right] = add_mod(
                        coefficients[right],
                        mul_mod(coefficient, scale, self.modulus),
                        self.modulus,
                    );
                }
            }
        }
        Some(Dependency { scalar, weights })
    }
    pub(crate) fn rank(&self) -> usize {
        self.rank
    }
    pub(crate) fn proof_nodes(&self) -> usize {
        self.proofs.len()
    }
    /// Insert one already-checked, distinct row. `index` is its certificate index.
    pub(crate) fn insert(
        &mut self,
        row: SignedRelation,
        a: u64,
        b: u64,
        index: usize,
    ) -> Result<Option<Dependency>> {
        let (mut ru, pu) = self.find(row.i)?;
        let (mut rv, pv) = self.find(row.j)?;
        let a = sub_mod(
            sub_mod(a, self.signed(pu.a, row.negative_i), self.modulus),
            self.signed(pv.a, row.negative_j),
            self.modulus,
        );
        let b = sub_mod(
            sub_mod(b, self.signed(pu.b, row.negative_i), self.modulus),
            self.signed(pv.b, row.negative_j),
            self.modulus,
        );
        let input = self.node(Proof::Input(index))?;
        let proof = self.linear(input, pu.proof, self.sign(!row.negative_i))?;
        let proof = self.linear(proof, pv.proof, self.sign(!row.negative_j))?;
        let mut left_negative = row.negative_i ^ pu.negative;
        let mut right_negative = row.negative_j ^ pv.negative;
        if ru == rv {
            if left_negative != right_negative {
                return Ok(self.finish(a, b, proof, index + 1));
            }
            // A same-sign cycle has root coefficient +2 or -2.
            let inv_two = self.modulus / 2 + 1;
            let inv = self.signed(inv_two, left_negative);
            let new = Anchor {
                a: mul_mod(a, inv, self.modulus),
                b: mul_mod(b, inv, self.modulus),
                proof: self.scale(proof, inv)?,
            };
            if let Some(old) = self.anchor[ru] {
                let dependency = self.linear(new.proof, old.proof, self.modulus - 1)?;
                return Ok(self.finish(
                    sub_mod(new.a, old.a, self.modulus),
                    sub_mod(new.b, old.b, self.modulus),
                    dependency,
                    index + 1,
                ));
            }
            self.anchor[ru] = Some(new);
            self.rank += 1;
            return Ok(None);
        }
        // Keep trees shallow; reversing the chosen edge preserves its proof.
        if self.size[ru] > self.size[rv] {
            std::mem::swap(&mut ru, &mut rv);
            std::mem::swap(&mut left_negative, &mut right_negative);
        }
        let edge = Potential {
            negative: left_negative == right_negative,
            a: self.signed(a, left_negative),
            b: self.signed(b, left_negative),
            proof: self.scale(proof, self.sign(left_negative))?,
        };
        let child_anchor = self.anchor[ru].take();
        let parent_anchor = self.anchor[rv];
        self.parent[ru] = rv;
        self.potential[ru] = edge;
        self.size[rv] += self.size[ru];
        if !(child_anchor.is_some() && parent_anchor.is_some()) {
            self.rank += 1;
        }
        if let Some(child) = child_anchor {
            let difference = self.linear(child.proof, edge.proof, self.modulus - 1)?;
            let new = Anchor {
                a: self.signed(sub_mod(child.a, edge.a, self.modulus), edge.negative),
                b: self.signed(sub_mod(child.b, edge.b, self.modulus), edge.negative),
                proof: self.scale(difference, self.sign(edge.negative))?,
            };
            if let Some(old) = parent_anchor {
                let dependency = self.linear(new.proof, old.proof, self.modulus - 1)?;
                return Ok(self.finish(
                    sub_mod(new.a, old.a, self.modulus),
                    sub_mod(new.b, old.b, self.modulus),
                    dependency,
                    index + 1,
                ));
            }
            self.anchor[rv] = Some(new);
        }
        Ok(None)
    }
}

#[derive(Clone, Debug)]
struct SparsePivot {
    tail: Vec<(usize, u64)>,
    rhs_a: u64,
    rhs_b: u64,
    proof: usize,
}

/// Incremental sparse Gaussian elimination modulo `modulus` with a proof DAG
/// for `2..=4`-summand signed factor-base relations.
pub(crate) struct SparseSystem {
    modulus: u64,
    pivots: Vec<Option<SparsePivot>>,
    proofs: Vec<Proof>,
    max_proofs: usize,
    rank: usize,
    row_buf: Vec<(usize, u64)>,
    merge_buf: Vec<(usize, u64)>,
}

impl SparseSystem {
    pub(crate) fn new(columns: usize, modulus: u64, max_proofs: usize) -> Self {
        Self {
            modulus,
            pivots: vec![None; columns],
            proofs: vec![Proof::Zero],
            max_proofs,
            rank: 0,
            row_buf: Vec::with_capacity(32),
            merge_buf: Vec::with_capacity(32),
        }
    }
    pub(crate) fn rank(&self) -> usize {
        self.rank
    }
    pub(crate) fn proof_nodes(&self) -> usize {
        self.proofs.len()
    }
    fn node(&mut self, proof: Proof) -> Result<usize> {
        if self.proofs.len() >= self.max_proofs {
            return Err(Error::ResourceLimit("proof arena"));
        }
        let id = self.proofs.len();
        self.proofs.push(proof);
        Ok(id)
    }
    fn linear(&mut self, left: usize, right: usize, scale: u64) -> Result<usize> {
        if right == 0 || scale == 0 {
            return Ok(left);
        }
        if left == 0 && scale == 1 {
            return Ok(right);
        }
        self.node(Proof::Add { left, right, scale })
    }
    fn finish(&self, a: u64, b: u64, proof: usize, relations: usize) -> Option<Dependency> {
        if b == 0 {
            return None;
        }
        let neg_a = if a == 0 { 0 } else { self.modulus - a };
        let scalar = mul_mod(
            neg_a,
            pow_mod(b, self.modulus - 2, self.modulus),
            self.modulus,
        );
        let mut coefficients = vec![0; self.proofs.len()];
        let mut weights = vec![0; relations];
        coefficients[proof] = 1;
        for id in (1..self.proofs.len()).rev() {
            let coefficient = coefficients[id];
            if coefficient == 0 {
                continue;
            }
            match self.proofs[id] {
                Proof::Zero => {}
                Proof::Input(index) => {
                    weights[index] = add_mod(weights[index], coefficient, self.modulus)
                }
                Proof::Add { left, right, scale } => {
                    coefficients[left] = add_mod(coefficients[left], coefficient, self.modulus);
                    coefficients[right] = add_mod(
                        coefficients[right],
                        mul_mod(coefficient, scale, self.modulus),
                        self.modulus,
                    );
                }
            }
        }
        Some(Dependency { scalar, weights })
    }
    pub(crate) fn insert(
        &mut self,
        row: MultiSignedRelation,
        a: u64,
        b: u64,
        index: usize,
    ) -> Result<Option<Dependency>> {
        let n = self.modulus;
        let mut raw = [(0usize, 0u64); 4];
        let summands = row.summands();
        for (slot, term) in raw.iter_mut().zip(summands) {
            *slot = (term.index, if term.negative { n - 1 } else { 1 });
        }
        let arity = summands.len();
        for i in 1..arity {
            let mut j = i;
            while j > 0 && raw[j - 1].0 > raw[j].0 {
                raw.swap(j - 1, j);
                j -= 1;
            }
        }
        self.row_buf.clear();
        let mut pos = 0;
        while pos < arity {
            let col = raw[pos].0;
            let mut coeff = raw[pos].1;
            pos += 1;
            while pos < arity && raw[pos].0 == col {
                coeff = add_mod(coeff, raw[pos].1, n);
                pos += 1;
            }
            if coeff != 0 {
                self.row_buf.push((col, coeff));
            }
        }
        let mut rhs_a = a;
        let mut rhs_b = b;
        let mut proof = self.node(Proof::Input(index))?;
        while let Some(&(lead_col, lead_coeff)) = self.row_buf.first() {
            if let Some(pivot) = &self.pivots[lead_col] {
                let p_rhs_a = pivot.rhs_a;
                let p_rhs_b = pivot.rhs_b;
                let p_proof = pivot.proof;
                self.merge_buf.clear();
                let left = &self.row_buf[1..];
                let right = &pivot.tail[..];
                let (mut li, mut ri) = (0usize, 0usize);
                while li < left.len() && ri < right.len() {
                    let (lc, lv) = left[li];
                    let (rc, rv) = right[ri];
                    if lc < rc {
                        self.merge_buf.push((lc, lv));
                        li += 1;
                    } else if rc < lc {
                        let sub = mul_mod(lead_coeff, rv, n);
                        if sub != 0 {
                            self.merge_buf.push((rc, n - sub));
                        }
                        ri += 1;
                    } else {
                        let val = sub_mod(lv, mul_mod(lead_coeff, rv, n), n);
                        if val != 0 {
                            self.merge_buf.push((lc, val));
                        }
                        li += 1;
                        ri += 1;
                    }
                }
                while li < left.len() {
                    self.merge_buf.push(left[li]);
                    li += 1;
                }
                while ri < right.len() {
                    let (rc, rv) = right[ri];
                    let sub = mul_mod(lead_coeff, rv, n);
                    if sub != 0 {
                        self.merge_buf.push((rc, n - sub));
                    }
                    ri += 1;
                }
                std::mem::swap(&mut self.row_buf, &mut self.merge_buf);
                rhs_a = sub_mod(rhs_a, mul_mod(lead_coeff, p_rhs_a, n), n);
                rhs_b = sub_mod(rhs_b, mul_mod(lead_coeff, p_rhs_b, n), n);
                let neg_lead = n - lead_coeff;
                proof = self.linear(proof, p_proof, neg_lead)?;
            } else {
                let inv = pow_mod(lead_coeff, n - 2, n);
                let mut tail = Vec::with_capacity(self.row_buf.len().saturating_sub(1));
                for &(col, val) in &self.row_buf[1..] {
                    tail.push((col, mul_mod(val, inv, n)));
                }
                let scaled_a = mul_mod(rhs_a, inv, n);
                let scaled_b = mul_mod(rhs_b, inv, n);
                let scaled_proof = self.linear(0, proof, inv)?;
                self.pivots[lead_col] = Some(SparsePivot {
                    tail,
                    rhs_a: scaled_a,
                    rhs_b: scaled_b,
                    proof: scaled_proof,
                });
                self.rank += 1;
                return Ok(None);
            }
        }
        Ok(self.finish(rhs_a, rhs_b, proof, index + 1))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // Deliberately dense reference, used only to audit the sparse solver.
    struct Dense {
        n: u64,
        columns: usize,
        pivots: Vec<Option<Vec<u64>>>,
        rank: usize,
    }
    impl Dense {
        fn insert(&mut self, row: SignedRelation, a: u64, b: u64) -> Option<u64> {
            let mut r = vec![0; self.columns + 2];
            r[row.i] = if row.negative_i { self.n - 1 } else { 1 };
            r[row.j] = (r[row.j] + if row.negative_j { self.n - 1 } else { 1 }) % self.n;
            r[self.columns] = (self.n - a) % self.n;
            r[self.columns + 1] = (self.n - b) % self.n;
            for column in 0..self.columns {
                if r[column] == 0 {
                    continue;
                }
                if let Some(pivot) = &self.pivots[column] {
                    let coefficient = r[column];
                    for j in column..r.len() {
                        r[j] = (r[j] + self.n - coefficient * pivot[j] % self.n) % self.n;
                    }
                } else {
                    let inv = (1..self.n).find(|&v| v * r[column] % self.n == 1).unwrap();
                    for value in &mut r {
                        *value = *value * inv % self.n;
                    }
                    self.pivots[column] = Some(r);
                    self.rank += 1;
                    return None;
                }
            }
            let denominator = r[self.columns + 1];
            if denominator == 0 {
                None
            } else {
                let inverse = (1..self.n)
                    .find(|&v| v * denominator % self.n == 1)
                    .unwrap();
                Some((self.n - r[self.columns]) * inverse % self.n)
            }
        }
    }
    fn check_rows(columns: usize, codes: &[SignedRelation], seed: u64) {
        let n = 109;
        let secret = 37;
        let values: Vec<_> = (0..columns).map(|j| (j as u64 * 19 + seed) % n).collect();
        let mut graph = GainGraph::new(columns, n, 10000);
        let mut dense = Dense {
            n,
            columns,
            pivots: vec![None; columns],
            rank: 0,
        };
        let mut originals = Vec::new();
        let mut prior_solution = false;
        for (index, &code) in codes.iter().enumerate() {
            let signed = |v: u64, neg| if neg && v != 0 { n - v } else { v };
            let b = (seed * 3 + index as u64 * 7 + 1) % n;
            let a = (signed(values[code.i], code.negative_i)
                + signed(values[code.j], code.negative_j)
                + n
                - b * secret % n)
                % n;
            originals.push((code, a, b));
            let expected = dense.insert(code, a, b);
            let actual = graph.insert(code, a, b, index).unwrap();
            assert_eq!(graph.rank(), dense.rank);
            // Before recovery the two coefficient bases must find the same
            // first useful dependency. Afterwards they can choose different
            // representatives modulo the already-known G/Q equation.
            if !prior_solution {
                assert_eq!(
                    actual.as_ref().map(|d| d.scalar),
                    expected,
                    "seed={seed} row={index}"
                );
            }
            if let Some(dependency) = actual {
                assert_eq!(dependency.scalar, secret);
                let mut coefficients = vec![0; columns];
                let (mut aa, mut bb) = (0, 0);
                for (&weight, &(r, a, b)) in dependency.weights.iter().zip(&originals) {
                    coefficients[r.i] = (coefficients[r.i] + signed(weight, r.negative_i)) % n;
                    coefficients[r.j] = (coefficients[r.j] + signed(weight, r.negative_j)) % n;
                    aa = (aa + weight * a) % n;
                    bb = (bb + weight * b) % n;
                }
                assert!(coefficients.iter().all(|&v| v == 0));
                assert_ne!(bb, 0);
                assert_eq!((aa + bb * secret) % n, 0);
                prior_solution = true;
            }
        }
    }
    #[test]
    fn anchors_and_balanced_cycles_match_dense_elimination() {
        let row = |i, j, negative_j| SignedRelation {
            i,
            j,
            negative_i: false,
            negative_j,
        };
        check_rows(
            2,
            &[row(0, 0, false), row(1, 1, false), row(0, 1, false)],
            11,
        );
        check_rows(3, &[row(0, 1, true), row(1, 2, true), row(0, 2, true)], 17);
        check_rows(
            3,
            &[
                row(0, 1, false),
                row(1, 2, false),
                row(0, 2, false),
                row(0, 0, false),
            ],
            23,
        );
    }
    #[test]
    fn random_signed_systems_match_rank_first_recovery_and_all_returned_proofs() {
        let mut state = 71u64;
        for seed in 1..50 {
            let columns = 3 + seed as usize % 17;
            let mut codes = Vec::new();
            for _ in 0..(columns * 4) {
                state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
                let i = (state >> 16) as usize % columns;
                let j = (state >> 32) as usize % columns;
                let negative_i = state & 1 != 0;
                let negative_j = state & 2 != 0;
                if i == j && negative_i != negative_j {
                    continue;
                }
                codes.push(SignedRelation {
                    i,
                    j,
                    negative_i,
                    negative_j,
                });
            }
            check_rows(columns, &codes, seed);
        }
    }

    #[test]
    fn sparse_multi_summand_elimination_matches_dense_rank_and_proofs() {
        let n = 109u64;
        let secret = 37u64;
        let mut state = 0x517cc1b727220a95u64;
        for arity in [2usize, 3, 4] {
            for seed in 1..25u64 {
                let columns = 4 + (seed as usize % 13);
                let values: Vec<_> = (0..columns).map(|j| (j as u64 * 23 + seed) % n).collect();
                let mut sparse = SparseSystem::new(columns, n, 100_000);
                let mut dense = Dense {
                    n,
                    columns,
                    pivots: vec![None; columns],
                    rank: 0,
                };
                let mut originals = Vec::new();
                let mut prior_solution = false;
                for _index in 0..(columns * 3) {
                    let mut terms = [crate::SignedTerm::default(); 4];
                    for slot in terms.iter_mut().take(arity) {
                        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
                        slot.index = (state >> 20) as usize % columns;
                        slot.negative = (state & 4) != 0;
                    }
                    let rel = MultiSignedRelation::new(&terms[..arity]).unwrap();
                    if rel.key().is_none() {
                        continue;
                    }
                    let row_idx = originals.len();
                    let signed = |v: u64, neg: bool| if neg && v != 0 { n - v } else { v };
                    let b = if row_idx % 5 == 0 {
                        0
                    } else {
                        (seed * 5 + row_idx as u64 * 11 + 1) % n
                    };
                    let mut lhs = 0u64;
                    let mut r_vec = vec![0u64; columns + 2];
                    for term in rel.summands() {
                        lhs = (lhs + signed(values[term.index], term.negative)) % n;
                        r_vec[term.index] =
                            (r_vec[term.index] + if term.negative { n - 1 } else { 1 }) % n;
                    }
                    let a = (lhs + n - b * secret % n) % n;
                    r_vec[columns] = (n - a) % n;
                    r_vec[columns + 1] = (n - b) % n;
                    let expected = {
                        let mut r = r_vec;
                        let mut dep = None;
                        let mut inserted_pivot = false;
                        for col in 0..columns {
                            if r[col] == 0 {
                                continue;
                            }
                            if let Some(pivot) = &dense.pivots[col] {
                                let coeff = r[col];
                                for j in col..r.len() {
                                    r[j] = (r[j] + n - coeff * pivot[j] % n) % n;
                                }
                            } else {
                                let inv = (1..n).find(|&v| v * r[col] % n == 1).unwrap();
                                for v in &mut r {
                                    *v = *v * inv % n;
                                }
                                dense.pivots[col] = Some(r.clone());
                                dense.rank += 1;
                                inserted_pivot = true;
                                break;
                            }
                        }
                        if !inserted_pivot && r[columns + 1] != 0 {
                            let inv = (1..n).find(|&v| v * r[columns + 1] % n == 1).unwrap();
                            dep = Some((n - r[columns]) * inv % n);
                        }
                        dep
                    };
                    originals.push((rel, a, b));
                    let actual = sparse.insert(rel, a, b, row_idx).unwrap();
                    assert_eq!(sparse.rank(), dense.rank, "arity={arity} seed={seed}");
                    if !prior_solution {
                        assert_eq!(
                            actual.as_ref().map(|d| d.scalar),
                            expected,
                            "arity={arity} seed={seed} row={row_idx}"
                        );
                    }
                    if let Some(dep) = actual {
                        assert_eq!(dep.scalar, secret);
                        let mut check_cols = vec![0u64; columns];
                        let (mut aa, mut bb) = (0u64, 0u64);
                        for (&w, &(orig_rel, oa, ob)) in dep.weights.iter().zip(&originals) {
                            for term in orig_rel.summands() {
                                check_cols[term.index] =
                                    (check_cols[term.index] + signed(w, term.negative)) % n;
                            }
                            aa = (aa + w * oa) % n;
                            bb = (bb + w * ob) % n;
                        }
                        assert!(check_cols.iter().all(|&v| v == 0));
                        assert_ne!(bb, 0);
                        assert_eq!((aa + bb * secret) % n, 0);
                        prior_solution = true;
                    }
                }
            }
        }
    }
}
