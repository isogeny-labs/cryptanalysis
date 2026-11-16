#![allow(dead_code)]
use super::original_counters::{bump_ladd, bump_lmul};
use std::collections::HashMap;
pub type P3 = [u64; 3];
pub type Row = Vec<(u32, u64)>;
pub struct Rel2Out {
    pub full: Vec<Vec<(u32, u8)>>,
    pub ground: Vec<(u32, Vec<(u32, u8)>, bool)>, // (vertex, factor-base part, half)
    pub edges: Vec<(u32, u32, u32, u32)>,         // (vertex x, vertex y, fb index of A, fb index of B)
    pub vertex_pts: Vec<P3>,
    pub pairs: u64,
    pub no_roots: u64,
}

#[inline(always)]
pub fn lm(a: u64, b: u64, ell: u64) -> u64 {
    bump_lmul(1);
    ((a as u128 * b as u128) % ell as u128) as u64
}
#[inline(always)]
pub fn la(a: u64, b: u64, ell: u64) -> u64 {
    bump_ladd(1);
    let s = a + b;
    if s >= ell {
        s - ell
    } else {
        s
    }
}
fn vec_from(map: HashMap<u32, u64>) -> Row {
    let mut v: Row = map.into_iter().filter(|x| x.1 != 0).collect();
    v.sort();
    v
}
fn acc(map: &mut HashMap<u32, u64>, c: u32, v: u64, ell: u64) {
    let e = map.entry(c).or_insert(0);
    *e = la(*e, v, ell);
}

/// Relation rows from the large-prime graph. Every vertex gets a potential `p_v` (a sparse
/// vector over the factor-base columns and eta, with lambda_v = p_v . (lambda, eta)): grounded
/// vertices from their ground relation, others along breadth-first tree edges. Each non-tree edge
/// (and each repeated grounding) gives a relation among factor-base logs and eta only.
pub fn cycle_rows_2lp(ro: &Rel2Out, ell: u64, eta_col: u32, target: usize) -> Vec<Row> {
    let nv = ro.vertex_pts.len();
    let mut p: Vec<Option<Row>> = vec![None; nv];
    let mut adj: Vec<Vec<(u32, u32)>> = vec![vec![]; nv];
    for (e, &(x, y, _, _)) in ro.edges.iter().enumerate() {
        adj[x as usize].push((y, e as u32));
        adj[y as usize].push((x, e as u32));
    }
    let col = |i: u32| -> Option<u32> { if i == 0 { None } else { Some(i - 1) } };
    let minus1 = ell - 1;
    let inv2 = (ell + 1) / 2;
    let mut rows: Vec<Row> = Vec::new();
    let mut queue: std::collections::VecDeque<u32> = std::collections::VecDeque::new();
    for (v, fpart, half) in &ro.ground {
        let mut m: HashMap<u32, u64> = HashMap::new();
        let sc = if *half { inv2 } else { 1 };
        acc(&mut m, eta_col, sc, ell);
        for &(i, mu) in fpart {
            if let Some(c) = col(i) {
                acc(&mut m, c, lm(lm(mu as u64, sc, ell), minus1, ell), ell);
            }
        }
        let newp = vec_from(m);
        match &p[*v as usize] {
            None => {
                p[*v as usize] = Some(newp);
                queue.push_back(*v);
            }
            Some(old) => {
                let mut m2: HashMap<u32, u64> = HashMap::new();
                for &(c, a) in &newp {
                    acc(&mut m2, c, a, ell);
                }
                for &(c, a) in old {
                    acc(&mut m2, c, lm(a, minus1, ell), ell);
                }
                let r = vec_from(m2);
                if !r.is_empty() {
                    rows.push(r);
                }
            }
        }
    }
    let mut used = vec![false; ro.edges.len()];
    'bfs: while let Some(x) = queue.pop_front() {
        let px = p[x as usize].clone().unwrap();
        for &(y, e) in &adj[x as usize] {
            if used[e as usize] {
                continue;
            }
            used[e as usize] = true;
            let (_, _, ia, ib) = ro.edges[e as usize];
            let mut fe: HashMap<u32, u64> = HashMap::new();
            for i in [ia, ib] {
                if let Some(c) = col(i) {
                    acc(&mut fe, c, 1, ell);
                }
            }
            match &p[y as usize] {
                None => {
                    // p_y = eta - F_e - p_x
                    let mut m: HashMap<u32, u64> = HashMap::new();
                    acc(&mut m, eta_col, 1, ell);
                    for (&c, &a) in &fe {
                        acc(&mut m, c, lm(a, minus1, ell), ell);
                    }
                    for &(c, a) in &px {
                        acc(&mut m, c, lm(a, minus1, ell), ell);
                    }
                    p[y as usize] = Some(vec_from(m));
                    queue.push_back(y);
                }
                Some(py) => {
                    // F_e + p_x + p_y - eta = 0
                    let mut m: HashMap<u32, u64> = HashMap::new();
                    for (&c, &a) in &fe {
                        acc(&mut m, c, a, ell);
                    }
                    for &(c, a) in &px {
                        acc(&mut m, c, a, ell);
                    }
                    for &(c, a) in py {
                        acc(&mut m, c, a, ell);
                    }
                    acc(&mut m, eta_col, minus1, ell);
                    let r = vec_from(m);
                    if !r.is_empty() {
                        rows.push(r);
                    }
                    if rows.len() >= target {
                        break 'bfs;
                    }
                }
            }
        }
    }
    rows
}

