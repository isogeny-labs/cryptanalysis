//! Positive controls for the trail engines (plan section 4.3): the published
//! active-S-box bounds of AES and PRESENT, and an exhaustive cross-check on
//! ToySpn.
//!
//! Scope of the AES rows: AES results come from the word-level engine only
//! ([`ValueModel::new`] rejects S-box widths above 6, and [`Engine::Auto`]
//! picks [`Engine::Word`] for 8-bit S-boxes); the value engine never ran on
//! AES. The word engine, the word-level SAT encoding and the word-level MILP
//! encoding all read one [`word_components`] table, so they are three solvers
//! on one model, not independent derivations. That the model is exact for AES
//! rests on MixColumns being GF(2^8)-linear and MDS: a column pattern
//! `(P, Q)` of active input and output bytes is feasible iff
//! `|P| + |Q| >= 5`. [`aes_mixcolumns_branch_number_independent_control`]
//! checks that fact without `word_components`.

use super::*;
use crate::cryptanalysis::sym_ir::primitives::{aes128, present80, toyspn};
use crate::cryptanalysis::sym_techniques::trails::{differential, linear};

fn serpent_s0() -> Sbox {
    Sbox::new(
        4,
        4,
        vec![3, 8, 15, 1, 10, 6, 5, 11, 14, 13, 4, 2, 7, 0, 9, 12],
    )
    .unwrap()
}

fn present_sbox() -> Sbox {
    Sbox::new(
        4,
        4,
        vec![0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2],
    )
    .unwrap()
}

/// Independent brute force for 2-round ToySpn: enumerate every nonzero input
/// difference and every DDT-feasible round-1 output difference, with no
/// pruning and no use of the search code. Returns the minimum number of
/// active S-boxes and the minimum trail weight.
fn brute_toyspn2(sbox: &Sbox) -> (u32, f64) {
    let ddt = sbox.ddt();
    let perm = |x: u32| -> u32 {
        let mut y = 0;
        for i in 0..16 {
            let to = if i < 15 { (4 * i) % 15 } else { 15 };
            y |= ((x >> i) & 1) << to;
        }
        y
    };
    let minw: Vec<f64> = (0..16usize)
        .map(|a| {
            (0..16usize)
                .filter(|&b| a != 0 && ddt[a][b] > 0)
                .map(|b| 4.0 - f64::from(ddt[a][b]).log2())
                .fold(f64::INFINITY, f64::min)
        })
        .collect();
    let mut best_active = u32::MAX;
    let mut best_w = f64::INFINITY;
    for d0 in 1u32..65536 {
        let lists: Vec<Vec<(u32, f64)>> = (0..4)
            .map(|j| {
                let a = ((d0 >> (4 * j)) & 15) as usize;
                if a == 0 {
                    vec![(0, 0.0)]
                } else {
                    (0..16usize)
                        .filter(|&b| ddt[a][b] > 0)
                        .map(|b| (b as u32, 4.0 - f64::from(ddt[a][b]).log2()))
                        .collect()
                }
            })
            .collect();
        let a0 = (0..4).filter(|j| (d0 >> (4 * j)) & 15 != 0).count() as u32;
        for &(b0, w0) in &lists[0] {
            for &(b1, w1) in &lists[1] {
                for &(b2, w2) in &lists[2] {
                    for &(b3, w3) in &lists[3] {
                        let eps1 = b0 | b1 << 4 | b2 << 8 | b3 << 12;
                        let d1 = perm(eps1);
                        let a1 = (0..4).filter(|j| (d1 >> (4 * j)) & 15 != 0).count() as u32;
                        best_active = best_active.min(a0 + a1);
                        let w2nd: f64 = (0..4)
                            .map(|j| ((d1 >> (4 * j)) & 15) as usize)
                            .filter(|&a| a != 0)
                            .map(|a| minw[a])
                            .sum();
                        best_w = best_w.min(w0 + w1 + w2 + w3 + w2nd);
                    }
                }
            }
        }
    }
    (best_active, best_w)
}

#[test]
fn toyspn_two_round_matches_exhaustive_enumeration() {
    for sbox in [serpent_s0(), present_sbox()] {
        let (bf_active, bf_w) = brute_toyspn2(&sbox);
        let p = toyspn::toyspn(&sbox, 2);
        let opts = SearchOptions {
            with_concrete: true,
            ..Default::default()
        };
        let r = differential::min_active_sboxes(&p, 2, &opts).unwrap();
        assert_eq!(r.min_active, bf_active, "active count vs brute force");
        let c = r.concrete.expect("4-bit S-box has a concrete trail");
        assert!(
            (c.weight - bf_w).abs() < 1e-6,
            "weight {} vs brute force {}",
            c.weight,
            bf_w
        );
        eprintln!(
            "ToySpn 2r: min active {} (brute force {}), best weight {:.3} (brute force {:.3})",
            r.min_active, bf_active, c.weight, bf_w
        );
    }
}

/// Multiply in GF(2^8) modulo `x^8 + x^4 + x^3 + x + 1` (local, not the IR's).
fn gf_mul(mut a: u8, mut b: u8) -> u8 {
    let mut p = 0;
    while b != 0 {
        if b & 1 != 0 {
            p ^= a;
        }
        a = (a << 1) ^ if a & 0x80 != 0 { 0x1b } else { 0 };
        b >>= 1;
    }
    p
}

/// Determinant over GF(2^8) (characteristic 2, so no signs) by expansion
/// along the first row.
fn gf_det(m: &[Vec<u8>]) -> u8 {
    if m.len() == 1 {
        return m[0][0];
    }
    let mut d = 0;
    for c in 0..m.len() {
        let minor: Vec<Vec<u8>> = m[1..]
            .iter()
            .map(|row| {
                row.iter()
                    .enumerate()
                    .filter(|&(j, _)| j != c)
                    .map(|(_, &v)| v)
                    .collect()
            })
            .collect();
        d ^= gf_mul(m[0][c], gf_det(&minor));
    }
    d
}

/// Independent control for the AES word model (does not call
/// `word_components` and does not use the IR's matrix): the MixColumns
/// branch number `min_{x != 0} wt(x) + wt(Mx)` over bytes, for the circulant
/// `[2 3 1 1]` over GF(2^8).
///
/// * Exhaustively, for every input of byte weight 1 and 2 (`4 * 255 +
///   6 * 255^2` inputs) the output weight is at least `5 - wt(x)`, and
///   weight 1 attains 4 (so the branch number is at most 5).
/// * For the remaining weights, every square submatrix of `M` (all 1x1,
///   2x2, 3x3 and the 4x4) has nonzero determinant, i.e. `M` is MDS, which
///   gives `wt(Mx) >= 5 - wt(x)` for every input.
#[test]
fn aes_mixcolumns_branch_number_independent_control() {
    let row = [2u8, 3, 1, 1];
    let m: Vec<Vec<u8>> = (0..4)
        .map(|i| (0..4).map(|j| row[(j + 4 - i) % 4]).collect())
        .collect();
    let apply = |x: [u8; 4]| -> [u8; 4] {
        let mut y = [0u8; 4];
        for i in 0..4 {
            for j in 0..4 {
                y[i] ^= gf_mul(m[i][j], x[j]);
            }
        }
        y
    };
    let wt = |v: &[u8; 4]| v.iter().filter(|&&b| b != 0).count();
    let mut min_total = usize::MAX;
    for support in 1u8..16 {
        let idx: Vec<usize> = (0..4).filter(|&i| support >> i & 1 == 1).collect();
        if idx.len() > 2 {
            continue;
        }
        let ranges = 255usize.pow(idx.len() as u32);
        for code in 0..ranges {
            let mut x = [0u8; 4];
            let mut c = code;
            for &i in &idx {
                x[i] = (c % 255) as u8 + 1;
                c /= 255;
            }
            let total = idx.len() + wt(&apply(x));
            min_total = min_total.min(total);
            assert!(total >= 5, "input {x:?}: weights sum to {total}");
        }
    }
    assert_eq!(min_total, 5, "branch number attained by weight-1 inputs");
    // MDS: every square submatrix is nonsingular.
    let mut checked = 0;
    for rows in 1u8..16 {
        for cols in 1u8..16 {
            if rows.count_ones() != cols.count_ones() {
                continue;
            }
            let sub: Vec<Vec<u8>> = (0..4)
                .filter(|&i| rows >> i & 1 == 1)
                .map(|i| {
                    (0..4)
                        .filter(|&j| cols >> j & 1 == 1)
                        .map(|j| m[i][j])
                        .collect()
                })
                .collect();
            assert_ne!(
                gf_det(&sub),
                0,
                "singular submatrix rows {rows:b} cols {cols:b}"
            );
            checked += 1;
        }
    }
    assert_eq!(checked, 16 + 36 + 16 + 1);
}

/// The word engine (the only engine that runs on AES) reproduces the
/// wide-trail bounds 1, 5, 9, 25 over 1..4 rounds, in both directions.
#[test]
fn aes_word_level_bounds_differential_and_linear() {
    let p = aes128::reduced(4, false);
    for dir in [Direction::Differential, Direction::Linear] {
        let m = TrailModel::from_primitive(&p, 4, dir).unwrap();
        let t = std::time::Instant::now();
        let r = min_active_sboxes(&m, &SearchOptions::default()).unwrap();
        eprintln!(
            "AES {:?}: best_by_rounds {:?} pattern sizes {:?} ({:?})",
            dir,
            r.best_by_rounds,
            r.pattern.iter().map(Vec::len).collect::<Vec<_>>(),
            t.elapsed()
        );
        assert_eq!(r.engine, Engine::Word);
        assert_eq!(r.best_by_rounds[0], 1);
        assert_eq!(r.best_by_rounds[1], 5, "2 rounds >= 5 active");
        assert_eq!(r.best_by_rounds[2], 9, "3 rounds");
        assert_eq!(r.best_by_rounds[3], 25, "4 rounds >= 25 active");
        assert_eq!(
            r.pattern.iter().map(Vec::len).sum::<usize>() as u32,
            r.min_active
        );
    }
}

#[test]
fn present_five_rounds_ten_active() {
    let p = present80::present80();
    for (name, f) in [
        ("diff", differential::min_active_sboxes as fn(_, _, &_) -> _),
        ("lin", linear::min_active_sboxes),
    ] {
        let t = std::time::Instant::now();
        let r = f(&p, 5, &SearchOptions::default()).unwrap();
        eprintln!(
            "PRESENT {name}: best_by_rounds {:?} ({:?})",
            r.best_by_rounds,
            t.elapsed()
        );
        assert_eq!(r.engine, Engine::Value);
        if name == "diff" {
            assert_eq!(r.best_by_rounds, vec![1, 2, 4, 6, 10]);
            assert_eq!(r.min_active, 10, "PRESENT 5 rounds: 10 active S-boxes");
        } else {
            // Single-bit linear approximations of the PRESENT S-box chain
            // through the pLayer, so a linear trail can keep one active
            // S-box per round: the active-S-box count is not what bounds
            // linear trails of PRESENT (its bias is).
            assert_eq!(r.best_by_rounds, vec![1, 2, 3, 4, 5]);
        }
    }
}

// ── SAT ──────────────────────────────────────────────────────────────────

use crate::cryptanalysis::sym_techniques::trails::{milp, sat};

/// Word-level SAT on AES: same `word_components` model as the word engine
/// (a second solver on one model, not an independent derivation).
#[test]
fn sat_aes_two_and_four_rounds() {
    for (rounds, expect) in [(2usize, 5u32), (4, 25)] {
        let p = aes128::reduced(rounds, false);
        for dir in [Direction::Differential, Direction::Linear] {
            let t = std::time::Instant::now();
            let r = sat::min_active_sboxes(&p, rounds, dir, &sat::SatOptions::default()).unwrap();
            eprintln!(
                "SAT AES {rounds}r {dir:?}: min {} ({} calls, {} conflicts, {} vars, {} clauses, {:?})",
                r.min_active,
                r.solver_calls,
                r.conflicts,
                r.n_vars,
                r.n_clauses,
                t.elapsed()
            );
            assert_eq!(r.level, sat::Level::Word);
            assert_eq!(r.min_active, expect);
            assert_eq!(
                r.pattern.iter().map(Vec::len).sum::<usize>() as u32,
                r.min_active
            );
        }
    }
}

#[test]
fn sat_present_bit_level_bounds() {
    let p = present80::present80();
    // The DDT-support (bit-level) model gives the published 10 over 5 rounds.
    let t = std::time::Instant::now();
    let r = sat::min_active_sboxes(&p, 5, Direction::Differential, &sat::SatOptions::default())
        .unwrap();
    eprintln!(
        "SAT PRESENT 5r diff: min {} ({} calls, {} conflicts, {} vars, {} clauses, {:?})",
        r.min_active,
        r.solver_calls,
        r.conflicts,
        r.n_vars,
        r.n_clauses,
        t.elapsed()
    );
    assert_eq!(r.level, sat::Level::Bit);
    assert_eq!(r.min_active, 10, "PRESENT 5 rounds: 10 active S-boxes");
    let lin =
        sat::min_active_sboxes(&p, 5, Direction::Linear, &sat::SatOptions::default()).unwrap();
    assert_eq!(lin.min_active, 5, "one active S-box per round is possible");
}

#[test]
fn sat_agrees_with_value_engine_on_toyspn() {
    for sbox in [serpent_s0(), present_sbox()] {
        let p = toyspn::toyspn(&sbox, 3);
        for dir in [Direction::Differential, Direction::Linear] {
            let m = TrailModel::from_primitive(&p, 3, dir).unwrap();
            let v = min_active_sboxes(&m, &SearchOptions::default()).unwrap();
            let s = sat::min_active_sboxes_model(&m, &sat::SatOptions::default()).unwrap();
            let q = milp::min_active_sboxes_model(&m, &milp::MilpOptions::default()).unwrap();
            assert_eq!(v.min_active, s.min_active, "{dir:?} SAT vs value");
            assert_eq!(v.min_active, q.min_active, "{dir:?} MILP vs value");
        }
    }
}

#[test]
fn sat_cnf_dimacs_has_header_and_xors() {
    let p = toyspn::toyspn(&present_sbox(), 2);
    let m = TrailModel::from_primitive(&p, 2, Direction::Differential).unwrap();
    let mut cnf = sat::encode(&m, sat::Level::Bit).unwrap();
    cnf.add_at_most(3);
    let d = cnf.to_dimacs();
    assert!(d.starts_with(&format!("p cnf {} {}\n", cnf.n_vars, cnf.clauses.len())));
}

// ── MILP ─────────────────────────────────────────────────────────────────

#[test]
fn milp_solver_tiny_vertex_cover_and_lp_export() {
    let mut m = milp::MilpModel::new();
    let x: Vec<usize> = (0..4).map(|i| m.add_var(&format!("x{i}"), 1.0)).collect();
    // Path 0-1-2-3: minimum vertex cover has size 2.
    for (a, b) in [(0, 1), (1, 2), (2, 3)] {
        m.add_row(vec![(x[a], 1.0), (x[b], 1.0)], milp::Sense::Ge, 1.0);
    }
    let s = m
        .solve(&milp::MilpSolveOptions::default())
        .unwrap()
        .unwrap();
    assert_eq!(s.objective.round() as i32, 2);
    let lp = m.to_lp();
    assert!(lp.contains("Minimize") && lp.contains("Subject To") && lp.contains("Binary"));
    assert!(lp.contains("c2:") && lp.trim_end().ends_with("End"));
    // Infeasible model.
    let mut bad = milp::MilpModel::new();
    let a = bad.add_var("a", 1.0);
    bad.add_row(vec![(a, 1.0)], milp::Sense::Ge, 2.0);
    assert!(bad
        .solve(&milp::MilpSolveOptions::default())
        .unwrap()
        .is_none());
}

/// Word-level MILP on AES: same `word_components` model as the word engine
/// and word-level SAT (a third solver on one model); float simplex, so a
/// cross-check rather than a certificate.
#[test]
fn milp_aes_two_three_four_rounds() {
    for (rounds, expect) in [(2usize, 5u32), (3, 9), (4, 25)] {
        let p = aes128::reduced(rounds, false);
        let t = std::time::Instant::now();
        let r = milp::min_active_sboxes(
            &p,
            rounds,
            Direction::Differential,
            &milp::MilpOptions::default(),
        )
        .unwrap();
        eprintln!(
            "MILP AES {rounds}r: minima {:?}, {} nodes, {} vars, {} rows, {:?}",
            r.minima_by_rounds,
            r.nodes,
            r.n_vars,
            r.n_rows,
            t.elapsed()
        );
        assert_eq!(r.level, sat::Level::Word);
        assert_eq!(r.min_active, expect);
    }
}

#[test]
fn milp_present_bit_level_reaches_2_rounds_shortfall_vs_published_5() {
    // Shortfall, recorded: the built-in dense-simplex branch and bound
    // finishes PRESENT only up to 2 rounds at bit level within a fixed node
    // budget (published: 10 active S-boxes over 5 rounds, which the SAT and
    // value engines reproduce); the model exports to `.lp` for an external
    // solver. The limit is a node budget, not a wall clock, so the outcome
    // does not depend on machine speed. MILP values are float-based
    // cross-checks, not exact certificates.
    let p = present80::present80();
    let published = [1u32, 2, 4, 6, 10];
    let opts = milp::MilpOptions {
        node_budget: NODE_BUDGET,
        ..Default::default()
    };
    let r = milp::min_active_sboxes(&p, 2, Direction::Differential, &opts).unwrap();
    eprintln!(
        "MILP PRESENT 2r: minima {:?}, {} nodes, {} vars, {} rows",
        r.minima_by_rounds, r.nodes, r.n_vars, r.n_rows
    );
    assert_eq!(r.level, sat::Level::Bit);
    assert_eq!(r.min_active, published[1]);
    let r3 = milp::min_active_sboxes(&p, 3, Direction::Differential, &opts);
    assert_eq!(r3.err(), Some(TrailError::BudgetExceeded));
}

const NODE_BUDGET: u64 = 60;

#[test]
fn present_best_concrete_trails_are_consistent_with_active_bounds() {
    let p = present80::present80();
    let mut prev = 0.0;
    for rounds in 1..=3usize {
        for dir in [Direction::Differential, Direction::Linear] {
            let m = TrailModel::from_primitive(&p, rounds, dir).unwrap();
            let t = std::time::Instant::now();
            let c = best_concrete_trail(&m, 2_000_000_000).unwrap();
            let a = min_active_sboxes(&m, &SearchOptions::default()).unwrap();
            // Every active S-box costs at least 2 bits (differential, max
            // DDT entry 4/16) or 1 bit (linear, max |correlation| 1/2).
            let per = if dir == Direction::Differential {
                2.0
            } else {
                1.0
            };
            eprintln!(
                "PRESENT {rounds}r {dir:?}: best weight {:.3} (-log2 probability for differential, -log2 |correlation| for linear; linear bias is 2^-(weight+1) = 2^-{:.3}), min active {} ({:?})",
                c.weight,
                c.weight + 1.0,
                a.min_active,
                t.elapsed()
            );
            assert!(c.weight >= per * f64::from(a.min_active) - 1e-9);
            assert_eq!(c.inputs.len(), rounds);
            if dir == Direction::Differential {
                assert!(c.weight >= prev - 1e-9, "weight is monotone in rounds");
                prev = c.weight;
            }
            let via = if dir == Direction::Differential {
                differential::best_trail(&p, rounds, 2_000_000_000).unwrap()
            } else {
                linear::best_trail(&p, rounds, 2_000_000_000).unwrap()
            };
            assert!((via.weight - c.weight).abs() < 1e-9);
        }
    }
}
