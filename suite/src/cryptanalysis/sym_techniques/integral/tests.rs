//! Positive controls for the division-property code.

use super::division_property::*;
use crate::cryptanalysis::sym_ir::primitives::{aes128, simon, toyspn};
use crate::cryptanalysis::sym_ir::{
    ArxOp, Codec, FeedForward, KeySchedule, Kind, Layer, Primitive, Round, SboxId,
};

fn present_sbox() -> crate::cryptanalysis::sbox::Sbox {
    crate::cryptanalysis::sbox::Sbox::new(
        4,
        4,
        vec![0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2],
    )
    .unwrap()
}

#[test]
fn division_trail_table_basic_properties() {
    let s = present_sbox();
    let dt = division_trail_table(&s);
    // A bijection maps the all-ones vector only to the all-ones vector.
    for u in 0..16 {
        assert_eq!(dt[15][u], u == 15, "k = 1111, u = {u}");
    }
    // Only k = 0 reaches u = 0; every k reaches some u.
    for k in 0..16 {
        assert_eq!(dt[k][0], k == 0);
        assert!((0..16).any(|u| dt[k][u]));
    }
    // Monotone: dropping bits of k keeps the transition.
    for k in 0..16usize {
        for u in 0..16 {
            if dt[k][u] {
                for i in 0..4 {
                    assert!(dt[k & !(1 << i)][u]);
                }
            }
        }
    }
    // The same properties on the AES S-box (8 bits).
    let a = aes128::aes128();
    let dt8 = division_trail_table(&a.sboxes[0]);
    for u in 0..256 {
        assert_eq!(dt8[255][u], u == 255);
    }
}

#[test]
fn aes_word_based_three_round_integral() {
    let p = aes128::aes128();
    let tr = word_division_property(&p, 5, &[0]).unwrap();
    let all = |r: usize, want: WordProp| tr[r - 1].iter().all(|&s| s == want);
    assert_eq!(
        tr[0].iter().filter(|&&s| s == WordProp::All).count(),
        4,
        "round 1: one column ALL"
    );
    assert!(all(2, WordProp::All), "round 2: all 16 bytes ALL");
    assert!(all(3, WordProp::Balanced), "round 3: all 16 bytes BALANCED");
    assert!(all(4, WordProp::Unknown), "round 4: nothing known");
    let s = longest_integral_distinguisher_word_only(&p, 6);
    assert_eq!(
        s, 3,
        "3-round integral distinguisher (plus one key-recovery round)"
    );
}

/// Word-based longest distinguisher only (skips the bit-level driver).
fn longest_integral_distinguisher_word_only(p: &Primitive, max: usize) -> usize {
    let words = p.state_bits() / 8;
    let mut best = 0;
    for a in 0..words {
        let tr = word_division_property(p, max, &[a]).unwrap();
        for (r, st) in tr.iter().enumerate() {
            if st
                .iter()
                .any(|&s| s == WordProp::All || s == WordProp::Balanced)
            {
                best = best.max(r + 1);
            }
        }
    }
    best
}

#[test]
fn aes_bit_based_three_round_integral() {
    let p = aes128::aes128();
    let act: Vec<usize> = (0..8).collect();
    let t = std::time::Instant::now();
    let r3 = bit_division_property(&p, 3, &act, 20_000_000).unwrap();
    eprintln!(
        "AES bit-based 3r: {} balanced bits, {} unproven, {} conflicts, {:?}",
        r3.balanced.len(),
        r3.unproven.len(),
        r3.conflicts,
        t.elapsed()
    );
    assert_eq!(
        r3.balanced.len(),
        128,
        "3 rounds: every output bit balanced"
    );
    let t = std::time::Instant::now();
    let r4 = bit_division_property(&p, 4, &act, 20_000_000).unwrap();
    eprintln!(
        "AES bit-based 4r: {} balanced bits, {} unproven, {} conflicts, {:?}",
        r4.balanced.len(),
        r4.unproven.len(),
        r4.conflicts,
        t.elapsed()
    );
    assert!(r4.balanced.is_empty(), "4 rounds: nothing proven balanced");
}

#[test]
fn toyspn_longest_integral_runs_and_is_consistent() {
    let p = toyspn::toyspn(&present_sbox(), 6);
    let s = longest_integral_distinguisher(&p, 6, 5_000_000).unwrap();
    let b = s.best.expect("at least a 1-round distinguisher");
    eprintln!(
        "ToySpn-6r longest integral: {} rounds ({:?}, 2^{} data), word best {:?}",
        b.rounds,
        b.level,
        b.log2_data,
        s.best_word.as_ref().map(|d| d.rounds)
    );
    assert!(b.rounds >= 1 && !b.balanced_bits.is_empty());
    // Soundness cross-check by brute force: the claimed balanced bits really
    // XOR to zero over the claimed input set for the keyed cipher.
    let key = 0x0123_4567_89ab_cdefu64.to_le_bytes();
    for &bit in b.balanced_bits.iter().take(4) {
        let mut acc = 0u16;
        let free = &b.active_bits;
        for v in 0u32..(1 << free.len()) {
            let mut x = 0u16;
            for (i, &pos) in free.iter().enumerate() {
                x |= (((v >> i) & 1) as u16) << pos;
            }
            let c = crate::cryptanalysis::sym_ir::eval_rounds(&p, &key, &x.to_le_bytes(), b.rounds);
            acc ^= u16::from_le_bytes([c[0], c[1]]);
        }
        assert_eq!((acc >> bit) & 1, 0, "output bit {bit} is not balanced");
    }
}

/// Simon-structured primitive with `n`-bit words (round function
/// `(x, y) -> (y ^ (x<<<1 & x<<<8) ^ (x<<<2) ^ k, x)`); the key addition is
/// omitted because the division property ignores it. Built locally so that
/// the 32-bit-block instance can be tested; `simon64_128` is the IR's own.
fn simon_structure(n: usize, rounds: usize) -> Primitive {
    let r = Round {
        layers: vec![Layer::Arx {
            word_bits: n,
            ops: vec![
                ArxOp::Rotl {
                    dst: 2,
                    src: 1,
                    k: 1,
                },
                ArxOp::Rotl {
                    dst: 3,
                    src: 1,
                    k: 8,
                },
                ArxOp::And { dst: 2, a: 2, b: 3 },
                ArxOp::Rotl {
                    dst: 3,
                    src: 1,
                    k: 2,
                },
                ArxOp::Xor { dst: 2, a: 2, b: 3 },
                ArxOp::Xor { dst: 2, a: 2, b: 0 },
                ArxOp::Copy { dst: 0, src: 1 },
                ArxOp::Copy { dst: 1, src: 2 },
            ],
        }],
    };
    Primitive {
        name: format!("SIMON{}-structure", 2 * n),
        block_bits: 2 * n,
        key_bits: 0,
        scratch_bits: 2 * n,
        block_codec: Codec::little(n),
        key_codec: Codec::little(n.max(8)),
        sboxes: vec![],
        rounds: vec![r; rounds],
        key_schedule: KeySchedule::Independent {
            round_keys: 0,
            round_key_bits: 1,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Feistel,
    }
}

#[test]
fn simon_structure_matches_ir_simon_rounds_and_has_integral() {
    // The local construction has the same round structure as the IR Simon64
    // (ignoring the key layer): compare the netlist-relevant result.
    let ir = simon::simon64_128();
    let local = simon_structure(32, ir.num_rounds());
    let act: Vec<usize> = (0..64).filter(|&b| b != 0).collect();
    for rounds in [4usize, 8] {
        let a = bit_division_property(&ir, rounds, &act, 5_000_000).unwrap();
        let b = bit_division_property(&local, rounds, &act, 5_000_000).unwrap();
        assert_eq!(
            a.balanced, b.balanced,
            "IR Simon64 vs local, {rounds} rounds"
        );
    }
}

/// PRESENT-80, bit-based division property, input set "all 64 bits active
/// except bit 0". Published: a 9-round integral distinguisher (Todo-Morii
/// FSE 2016; Xiang et al. ASIACRYPT 2016 report 9 rounds for PRESENT).
#[test]
fn present_nine_round_integral_bit_based() {
    use crate::cryptanalysis::sym_ir::primitives::present80;
    let p = present80::present80();
    let act: Vec<usize> = (1..64).collect();
    let t = std::time::Instant::now();
    let r9 = bit_division_property(&p, 9, &act, 20_000_000).unwrap();
    eprintln!(
        "PRESENT bit-based, constant bit 0, 9 rounds: {} balanced bits, {} conflicts, {:?}",
        r9.balanced.len(),
        r9.conflicts,
        t.elapsed()
    );
    assert!(!r9.balanced.is_empty(), "9-round distinguisher reached");
    assert_eq!(r9.balanced.len(), 28);
    // One more round: nothing is proven balanced, for any choice of the
    // constant bit tried here.
    for c in [0usize, 1, 17, 34, 63] {
        let act: Vec<usize> = (0..64).filter(|&b| b != c).collect();
        let r10 = bit_division_property(&p, 10, &act, 20_000_000).unwrap();
        assert!(r10.balanced.is_empty(), "constant bit {c}: 10 rounds");
    }
}

#[test]
fn aes_longest_integral_distinguisher_is_three_rounds() {
    let p = aes128::aes128();
    // Small per-query conflict budget: the 4-round bit-level queries of the
    // all-but-one-bit families are hard for this solver and are skipped.
    let s = longest_integral_distinguisher(&p, 5, 20_000).unwrap();
    let b = s.best.expect("a distinguisher exists");
    eprintln!(
        "AES-128 longest integral: {} rounds ({:?}, 2^{} data), {} bit candidates tried",
        b.rounds, b.level, b.log2_data, s.bit_candidates_tried
    );
    assert_eq!(b.rounds, 3, "3-round integral distinguisher");
    assert_eq!(b.log2_data, 8);
    assert_eq!(s.best_word.unwrap().rounds, 3);
}

/// SIMON32-structured primitive, bit-based division property, input "all 32
/// bits active except bit 16". The literature value for conventional
/// bit-based division property on SIMON32 is 14 rounds (Todo-Morii FSE 2016;
/// Xiang et al. ASIACRYPT 2016), 15 with three-subset propagation
/// (Todo-Morii). This code reaches 13, one round short of the published 14.
///
/// What is known: an independent model (a separate pysat encoding of the same
/// COPY / AND / XOR propagation rules, written by the reviewer, not this
/// netlist or solver) also gets 13 on SIMON32 (and 15 against 16 on SIMON48),
/// so the gap is not a bug of this netlist. What is not known: the cause of
/// the difference from the published numbers (textbook modelling or
/// convention differences against Todo-Morii FSE 2016 and Xiang et al. 2016
/// were not identified). A different round-counting convention is an untested
/// guess, and a half-swap cannot gain a round in a Feistel network, so it is
/// not a candidate explanation. The exact published SIMON32 14-round
/// input/output sets could not be looked up (research-kb was not reachable
/// from this session) and are not cited here from memory.
#[test]
fn simon32_structure_bit_based_reaches_13_rounds_shortfall_vs_published_14() {
    let p = simon_structure(16, 16);
    let act: Vec<usize> = (0..32).filter(|&b| b != 16).collect();
    let t = std::time::Instant::now();
    let r13 = bit_division_property(&p, 13, &act, 20_000_000).unwrap();
    eprintln!(
        "SIMON32-structure bit-based, 13 rounds: {} balanced bits, {:?}",
        r13.balanced.len(),
        t.elapsed()
    );
    assert!(!r13.balanced.is_empty());
    let r14 = bit_division_property(&p, 14, &act, 20_000_000).unwrap();
    assert!(r14.balanced.is_empty(), "14 rounds not reached");
}

#[test]
fn simon64_ir_bit_based_twelve_rounds() {
    let p = simon::simon64_128();
    let act: Vec<usize> = (1..64).collect();
    let t = std::time::Instant::now();
    let r = bit_division_property(&p, 12, &act, 20_000_000).unwrap();
    eprintln!(
        "SIMON64 (IR) bit-based, 12 rounds, constant bit 0: {} balanced bits, {:?}",
        r.balanced.len(),
        t.elapsed()
    );
    assert_eq!(r.balanced.len(), 64);
}

/// Four 1-bit registers `a, b, e, h` (block) plus two zero-initialised scratch
/// registers; `k` (scratch 4) is a key-dependent constant. Output 0 is
/// `f = a b e k ^ h`.
fn key_and_chain() -> Primitive {
    let r = Round {
        layers: vec![Layer::Arx {
            word_bits: 1,
            ops: vec![
                ArxOp::XorKey {
                    dst: 4,
                    round_key: 0,
                    word: 0,
                },
                ArxOp::And { dst: 5, a: 0, b: 4 },
                ArxOp::And { dst: 5, a: 5, b: 1 },
                ArxOp::And { dst: 5, a: 5, b: 2 },
                ArxOp::Xor { dst: 0, a: 5, b: 3 },
            ],
        }],
    };
    Primitive {
        name: "key-and-chain".into(),
        block_bits: 4,
        key_bits: 1,
        scratch_bits: 2,
        block_codec: Codec::little(1),
        key_codec: Codec::little(8),
        sboxes: vec![],
        rounds: vec![r],
        key_schedule: KeySchedule::Independent {
            round_keys: 1,
            round_key_bits: 1,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Feistel,
    }
}

/// An AND with a key-dependent constant must not make its data input
/// disappear. Over the inputs `a, b, e` active and `h` fixed, output 0 is
/// `a b e k ^ h`, whose XOR over the 8 inputs is `k` (checked by brute force
/// below), so it is NOT balanced for `k = 1`. The earlier model treated the
/// key-dependent constant as a known zero: the AND output became a constant,
/// `a`, `b`, `e` lost their only consumer and the SAT instance was
/// unsatisfiable, so output 0 was reported balanced.
#[test]
fn and_with_key_dependent_constant_keeps_the_data_dependency() {
    for k in [0u8, 1] {
        for h in [0u8, 1] {
            let mut sum = 0u8;
            for x in 0u8..8 {
                let (a, b, e) = (x & 1, x >> 1 & 1, x >> 2 & 1);
                sum ^= (a & b & e & k) ^ h;
            }
            assert_eq!(sum, k, "brute-force XOR over a,b,e at k = {k}, h = {h}");
        }
    }
    let p = key_and_chain();
    let r = bit_division_property(&p, 1, &[0, 1, 2], 1_000_000).unwrap();
    assert!(
        !r.balanced.contains(&0),
        "output 0 must not be reported balanced: {:?}",
        r.balanced
    );
    assert!(r.unproven.contains(&0));
}

/// Same shape with the constant a known zero (no key addition): the output is
/// `h`, independent of the active inputs, and the AND still kills its data
/// input, so division reaches nothing and nothing depends on `a, b, e`.
#[test]
fn and_with_known_zero_constant_still_kills_the_wire() {
    let mut p = key_and_chain();
    if let Layer::Arx { ops, .. } = &mut p.rounds[0].layers[0] {
        ops.remove(0);
    }
    let r = bit_division_property(&p, 1, &[0, 1, 2], 1_000_000).unwrap();
    assert!(!r.unproven.contains(&0));
    assert!(!r.balanced.contains(&0), "output 0 = h is independent");
}

fn one_sbox_primitive(table: Vec<u32>) -> Primitive {
    Primitive {
        name: "one-sbox".into(),
        block_bits: 4,
        key_bits: 0,
        scratch_bits: 0,
        block_codec: Codec::little(4),
        key_codec: Codec::little(8),
        sboxes: vec![crate::cryptanalysis::sbox::Sbox::new(4, 4, table).unwrap()],
        rounds: vec![Round {
            layers: vec![Layer::SboxParallel {
                sbox: SboxId(0),
                width_bits: 4,
                count: 1,
                bit_offset: 0,
            }],
        }],
        key_schedule: KeySchedule::Independent {
            round_keys: 0,
            round_key_bits: 1,
        },
        feed_forward: FeedForward::None,
        kind: Kind::Spn,
    }
}

#[test]
fn word_division_property_requires_bijective_sbox_for_all() {
    let bij = one_sbox_primitive(vec![
        0xC, 5, 6, 0xB, 9, 0, 0xA, 0xD, 3, 0xE, 0xF, 8, 4, 7, 1, 2,
    ]);
    assert!(bij.sboxes[0].is_bijective());
    assert_eq!(
        word_division_property(&bij, 1, &[0]).unwrap()[0],
        vec![WordProp::All]
    );
    let non: Vec<u32> = (0..16).map(|x| x & 7).collect();
    let non = one_sbox_primitive(non);
    assert!(!non.sboxes[0].is_bijective());
    assert_eq!(
        word_division_property(&non, 1, &[0]).unwrap()[0],
        vec![WordProp::Unknown]
    );
    // A constant word stays constant through any S-box.
    assert_eq!(
        word_division_property(&non, 1, &[]).unwrap()[0],
        vec![WordProp::Const]
    );
}
