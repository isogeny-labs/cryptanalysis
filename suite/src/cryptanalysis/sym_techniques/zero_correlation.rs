//! Zero-correlation linear hulls over the
//! [`sym_ir`](crate::cryptanalysis::sym_ir) cipher IR: the dual of the
//! miss-in-the-middle search in [`impossible`](super::impossible).
//!
//! A pair of linear masks `(alpha, beta)` has *correlation zero* over `r`
//! rounds if every linear trail from `alpha` to `beta` contains a
//! zero-correlation S-box approximation, so the hull sums to exactly zero
//! for every key. Bogdanov and Rijmen, "Linear hulls with correlation zero
//! and linear cryptanalysis of block ciphers", Designs, Codes and
//! Cryptography 70(3), 2014 (ePrint 2011/123), obtain such hulls by
//! propagating `alpha` forward and `beta` backward through the linear layer
//! *transposed* and finding a layer boundary where the two abstractions
//! contradict each other; Bogdanov and Wang, FSE 2012, use them for key
//! recovery.
//!
//! This module reuses the engine of the impossible-differential search with
//! two changes:
//!
//! * a linear layer `M` propagates a mask forward through `(M^-1)^T` and
//!   backward through `M^T` (a bit permutation is its own
//!   inverse-transpose);
//! * an S-box relates mask `a` to mask `b` when the correlation
//!   `sum_x (-1)^(a.x + b.S(x))` is non-zero (for the word model, a
//!   bijective S-box maps non-zero masks to non-zero masks and zero to
//!   zero).
//!
//! Round counting, final-round variants, models and budgets are exactly as
//! documented in [`impossible`](super::impossible).
//!
//! A contradiction proves the mask pair has correlation zero in the model.
//! "Not found" proves nothing. [`exhaustive_correlation`] gives an
//! independent numerical check on small blocks.

use super::impossible::{
    check_pair, find_in_prefix, longest, CellValue, FinalRound, Meet, MissInTheMiddle, Model,
    Propagation, SearchBudget, SearchReport, TechniqueError,
};
use crate::cryptanalysis::sbox::Sbox;
use crate::cryptanalysis::sym_ir::{eval_rounds, Primitive};

/// Correlation `2 * #{x : a.x = b.S(x)} / 2^n - 1` of the S-box masks
/// `(a, b)`, computed exactly over all `2^n` inputs. This is the formula
/// the AES-specific
/// [`aes::zero_correlation::sbox_correlation`](crate::cryptanalysis::aes::zero_correlation::sbox_correlation)
/// used before it became a wrapper over this function.
pub fn sbox_correlation(sbox: &Sbox, a: u32, b: u32) -> f64 {
    let n = 1u32 << sbox.n_in();
    let mut matches: i64 = 0;
    for x in 0..n {
        let lhs = (a & x).count_ones() & 1;
        let rhs = (b & sbox.lookup(x)).count_ones() & 1;
        if lhs == rhs {
            matches += 1;
        }
    }
    (2.0 * matches as f64 / n as f64) - 1.0
}

/// Search `p` for the longest zero-correlation linear hull reachable inside
/// `budget`; see [`longest_impossible_differential`] for the search
/// structure.
///
/// [`longest_impossible_differential`]: super::impossible::longest_impossible_differential
pub fn longest_zero_correlation(
    p: &Primitive,
    budget: &SearchBudget,
) -> Result<SearchReport, TechniqueError> {
    longest(p, Propagation::LinearMask, budget)
}

/// Search the first `rounds` rounds for a zero-correlation hull in the given
/// final-round variant.
pub fn find_zero_correlation(
    p: &Primitive,
    rounds: usize,
    final_round: FinalRound,
    budget: &SearchBudget,
) -> Result<Option<MissInTheMiddle>, TechniqueError> {
    let mut checks = 0;
    find_in_prefix(
        p,
        Propagation::LinearMask,
        rounds,
        final_round,
        budget,
        &mut checks,
        &mut Vec::new(),
    )
}

/// Test whether the truncated mask pair `input -> output` has correlation
/// zero over the first `rounds` rounds according to the model. `Ok(None)`
/// means the model cannot show it, not that the correlation is non-zero.
pub fn check_zero_correlation(
    p: &Primitive,
    rounds: usize,
    final_round: FinalRound,
    model: Model,
    input: &[CellValue],
    output: &[CellValue],
) -> Result<Option<Meet>, TechniqueError> {
    check_pair(
        p,
        Propagation::LinearMask,
        rounds,
        final_round,
        model,
        input,
        output,
    )
}

/// Exact correlation of the masks `(alpha, beta)` (byte strings in the
/// block codec, i.e. the same bit order as a block) over the first `rounds`
/// rounds under `key`, by enumerating all `2^block_bits` plaintexts.
/// Intended for blocks of at most 24 bits; panics beyond 28.
///
/// Returns `sum_x (-1)^(alpha.x + beta.E(x)) / 2^block_bits`.
pub fn exhaustive_correlation(
    p: &Primitive,
    key: &[u8],
    rounds: usize,
    alpha: &[u8],
    beta: &[u8],
) -> f64 {
    assert!(p.block_bits <= 28, "block too large to enumerate");
    let table = encryption_table(p, key, rounds);
    table_correlation(p, &table, alpha, beta)
}

/// All `2^block_bits` encryptions (index = plaintext as a little-endian
/// integer over the block bytes).
pub fn encryption_table(p: &Primitive, key: &[u8], rounds: usize) -> Vec<u32> {
    assert!(p.block_bits <= 28 && p.block_bits.is_multiple_of(8));
    let nb = p.block_bytes();
    (0u64..(1u64 << p.block_bits))
        .map(|x| {
            let pt: Vec<u8> = (0..nb).map(|i| (x >> (8 * i)) as u8).collect();
            let ct = eval_rounds(p, key, &pt, rounds);
            ct.iter()
                .enumerate()
                .fold(0u32, |a, (i, &b)| a | (b as u32) << (8 * i))
        })
        .collect()
}

/// Correlation of `(alpha, beta)` from a precomputed [`encryption_table`].
pub fn table_correlation(p: &Primitive, table: &[u32], alpha: &[u8], beta: &[u8]) -> f64 {
    let pack = |m: &[u8]| {
        m.iter()
            .enumerate()
            .fold(0u32, |a, (i, &b)| a | (b as u32) << (8 * i))
    };
    let (a, b) = (pack(alpha), pack(beta));
    let mut sum: i64 = 0;
    for (x, &c) in table.iter().enumerate() {
        let par = ((a & x as u32).count_ones() + (b & c).count_ones()) & 1;
        sum += if par == 0 { 1 } else { -1 };
    }
    sum as f64 / (1u64 << p.block_bits) as f64
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::sym_ir::primitives::{aes128, present80, sbox_from_u8, toyspn};

    fn cell(c: usize) -> Vec<CellValue> {
        vec![CellValue {
            cell: c,
            value: None,
        }]
    }

    /// Positive control: Bogdanov-Rijmen zero-correlation hulls with one
    /// active byte in the input mask and one in the output mask over four
    /// AES rounds (last MixColumns omitted), found generically; none at
    /// five rounds in the same form.
    #[test]
    fn aes_four_round_zero_correlation() {
        let p4 = aes128::reduced(4, false);
        let mut hits = 0;
        for i in 0..16 {
            for j in 0..16 {
                if check_zero_correlation(
                    &p4,
                    4,
                    FinalRound::AsGiven,
                    Model::Word,
                    &cell(i),
                    &cell(j),
                )
                .unwrap()
                .is_some()
                {
                    hits += 1;
                }
            }
        }
        assert_eq!(hits, 256);
        let p5 = aes128::reduced(5, false);
        assert!(
            find_zero_correlation(&p5, 5, FinalRound::AsGiven, &SearchBudget::default())
                .unwrap()
                .is_none()
        );
        let b = SearchBudget {
            max_rounds: 8,
            ..SearchBudget::default()
        };
        let r = longest_zero_correlation(&aes128::aes128(), &b).unwrap();
        assert_eq!(r.best.expect("found").rounds, 4);
    }

    /// Numerical check on small-scale AES SR(4,2,2,4): the reported
    /// single-cell hull has correlation exactly zero for every non-zero
    /// choice of the cell masks, under several keys (all 2^16 plaintexts).
    #[test]
    fn small_scale_hull_is_exactly_zero() {
        let p = aes128::small_scale(4);
        let d = find_zero_correlation(&p, 4, FinalRound::AsGiven, &SearchBudget::default())
            .unwrap()
            .expect("found");
        let (ci, co) = (d.input[0].cell, d.output[0].cell);
        assert_eq!((d.input.len(), d.output.len()), (1, 1));
        for key in [[0x12u8, 0x34], [0xde, 0xad]] {
            let t = encryption_table(&p, &key, 4);
            for a in 1u32..16 {
                for b in 1u32..16 {
                    let al = (a << (4 * ci)).to_le_bytes()[..2].to_vec();
                    let be = (b << (4 * co)).to_le_bytes()[..2].to_vec();
                    assert_eq!(table_correlation(&p, &t, &al, &be), 0.0);
                }
            }
        }
        // sanity: the detector is not blind (a mask pair with large
        // correlation exists in one round)
        let t1 = encryption_table(&p, &[1, 2], 1);
        let mut max = 0f64;
        for a in 1u32..=0xffff {
            let c = table_correlation(
                &p,
                &t1,
                &[a as u8, (a >> 8) as u8],
                &[a as u8, (a >> 8) as u8],
            );
            max = max.max(c.abs());
            if max > 0.1 {
                break;
            }
        }
        assert!(max > 0.1);
    }

    /// PRESENT-80 zero-correlation search: the longest hull found within the
    /// default budget (reported, not compared with the literature).
    #[test]
    fn present_report() {
        let b = SearchBudget {
            max_rounds: 9,
            ..SearchBudget::default()
        };
        let r = longest_zero_correlation(&present80::present80(), &b).unwrap();
        let best = r.best.as_ref().expect("found");
        println!("PRESENT zero-correlation best: {} rounds", best.rounds);
        assert_eq!(best.rounds, 6);
    }

    /// Correlation sanity check on a reduced instance (ToySpn, 16-bit state):
    /// the longest reported hull has correlation exactly zero for every
    /// non-zero mask pair on its cells, under two keys (all 2^16 plaintexts).
    #[test]
    fn toyspn_hull_is_exactly_zero() {
        let sb = sbox_from_u8(4, &crate::symmetric::present::SBOX);
        let p = toyspn::toyspn(&sb, 5);
        let r = longest_zero_correlation(&p, &SearchBudget::default()).unwrap();
        let d = r.best.expect("found");
        assert_eq!((d.input.len(), d.output.len()), (1, 1));
        let (ci, co) = (d.input[0].cell, d.output[0].cell);
        // Word model: every non-zero cell mask; bit model: the exact mask.
        let masks = |c: &CellValue| -> Vec<u32> {
            c.value.map_or((1u32..16).collect(), |v| vec![v as u32])
        };
        let (ma, mb) = (masks(&d.input[0]), masks(&d.output[0]));
        for key in [
            [1u8, 2, 3, 4, 5, 6, 7, 8],
            [0xff, 0, 0xaa, 0x55, 9, 8, 7, 6],
        ] {
            let t = encryption_table(&p, &key, d.rounds);
            for &a in &ma {
                for &b in &mb {
                    let al = (a << (4 * ci)).to_le_bytes()[..2].to_vec();
                    let be = (b << (4 * co)).to_le_bytes()[..2].to_vec();
                    assert_eq!(table_correlation(&p, &t, &al, &be), 0.0);
                }
            }
        }
    }

    #[test]
    fn sbox_correlation_matches_lat() {
        let p = aes128::reduced(1, false);
        let s = &p.sboxes[0];
        assert!((sbox_correlation(s, 0, 0) - 1.0).abs() < 1e-12);
        let lat = s.lat();
        assert!((sbox_correlation(s, 3, 7) - 2.0 * lat[3][7] as f64 / 256.0).abs() < 1e-12);
    }
}
