//! Positive controls for the ARX techniques; see each test's doc comment.
//! Numbers are printed with `--nocapture`.

use super::diff_linear::*;
use super::machine::ArxMachine;
use super::pnb::*;
use super::rotational::*;
use crate::cryptanalysis::sym_ir::primitives::{chacha, speck};
use crate::cryptanalysis::sym_ir::{eval_rounds, Primitive};
use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};

fn chacha_consts(w: usize) -> Vec<(usize, u64)> {
    chacha::constants(w).iter().copied().enumerate().collect()
}

fn dl_chacha(prim: &Primitive, r: usize) -> DlTarget<'_> {
    let w = prim.block_codec.word_bits;
    DlTarget::new(prim, r).with_fixed_words(&chacha_consts(w))
}

// ---- exact controls: xdp+, correlation of addition, rotational ----------

/// `xdp+` equals exhaustive counting: all `(α, β, γ)` at 4 bits and the full
/// output distribution for 64 random `(α, β)` at 8 bits (exact equality).
#[test]
fn xdp_add_matches_brute_force() {
    for a in 0..16u64 {
        for b in 0..16u64 {
            for g in 0..16u64 {
                assert_eq!(
                    xdp_add(4, a, b, g),
                    xdp_add_brute(4, a, b, g),
                    "{a} {b} {g}"
                );
            }
        }
    }
    let mut rng = SmallRng::seed_from_u64(1);
    let mut nonzero = 0;
    for _ in 0..64 {
        let (a, b) = (rng.gen::<u64>() & 255, rng.gen::<u64>() & 255);
        let mut hist = vec![0u64; 256];
        for x in 0..256u64 {
            for y in 0..256u64 {
                hist[((((x ^ a) + (y ^ b)) ^ (x + y)) & 255) as usize] += 1;
            }
        }
        for (g, &c) in hist.iter().enumerate() {
            let exact = c as f64 / 65536.0;
            assert_eq!(xdp_add(8, a, b, g as u64), exact, "8-bit {a} {b} {g}");
            nonzero += (c > 0) as u32;
        }
    }
    assert!(nonzero > 64);
}

/// The Wallén transducer equals exhaustive correlation: all `(u, v, t)` at
/// 4 bits, 400 random and structured triples at 8 bits (exact equality), and
/// every nonzero value is `±2^{-k}`.
#[test]
fn lin_corr_add_matches_brute_force() {
    for u in 0..16u64 {
        for v in 0..16u64 {
            for t in 0..16u64 {
                assert_eq!(lin_corr_add(4, u, v, t), lin_corr_add_brute(4, u, v, t));
            }
        }
    }
    let mut rng = SmallRng::seed_from_u64(2);
    let mut nz = 0;
    for i in 0..400 {
        let (mut u, mut v, mut t) = (
            rng.gen::<u64>() & 255,
            rng.gen::<u64>() & 255,
            rng.gen::<u64>() & 255,
        );
        if i % 2 == 0 {
            // structured: v = t = u keeps the correlation nonzero often
            v = u;
            t = u ^ (rng.gen::<u64>() & rng.gen::<u64>() & 255);
        }
        if i % 5 == 0 {
            u &= rng.gen::<u64>() & 255;
        }
        let (c, b) = (lin_corr_add(8, u, v, t), lin_corr_add_brute(8, u, v, t));
        assert_eq!(c, b, "{u} {v} {t}");
        if c != 0.0 {
            nz += 1;
            let k = -c.abs().log2();
            assert!((k - k.round()).abs() < 1e-12, "not a power of two: {c}");
        }
    }
    assert!(nz > 40, "only {nz} nonzero correlations exercised");
}

/// The rotational probability formula and the exact RX dynamic program
/// equal exhaustive counting at 8 bits, for all `γ`, 300 RX tuples with
/// reachable `δz` (random operand) and 300 with a constant operand.
#[test]
fn rotational_probabilities_match_brute_force() {
    for g in 0..8 {
        assert_eq!(rot_add_prob(8, g), rot_add_prob_brute(8, g), "gamma {g}");
    }
    let mut rng = SmallRng::seed_from_u64(3);
    let m = 255u64;
    for i in 0..600 {
        let g = rng.gen_range(0..8usize);
        let (dx, dy, c) = (
            rng.gen::<u64>() & m,
            rng.gen::<u64>() & m,
            rng.gen::<u64>() & m,
        );
        let (x, y) = (rng.gen::<u64>() & m, rng.gen::<u64>() & m);
        let rot = |v: u64| ((v << g) | (v >> (8 - g))) & m;
        if i % 2 == 0 {
            let dz = ((rot(x) ^ dx) + (rot(y) ^ dy)) & m ^ rot((x + y) & m);
            let o = Operand::Random(dy);
            assert_eq!(rx_add_dp(8, g, dx, o, dz), rx_add_brute(8, g, dx, o, dz));
            assert!(rx_add_dp(8, g, dx, o, dz) > 0.0);
            assert_eq!(rx_add_prob(8, g, dx, dy, dz), rx_add_dp(8, g, dx, o, dz));
        } else {
            let dz = ((rot(x) ^ dx) + c) & m ^ rot((x + c) & m);
            let o = Operand::Const(c);
            assert_eq!(rx_add_dp(8, g, dx, o, dz), rx_add_brute(8, g, dx, o, dz));
            assert!(rx_add_dp(8, g, dx, o, dz) > 0.0);
        }
    }
    // pure rotational is RX with zero differences
    assert_eq!(rx_add_prob(8, 3, 0, 0, 0), rot_add_prob(8, 3));
}

/// The compiled evaluator equals `eval_rounds` (with feed-forward) and its
/// backward pass inverts it, for ChaCha at w = 16 and 32.
#[test]
fn machine_matches_ir_and_inverts() {
    let mut rng = SmallRng::seed_from_u64(4);
    for (w, p) in [(16, chacha::reduced_width(16, 7)), (32, chacha::chacha(8))] {
        let mc = ArxMachine::compile(&p).unwrap();
        assert!(mc.is_invertible());
        for _ in 0..50 {
            let blk: Vec<u8> = (0..p.block_bytes()).map(|_| rng.gen()).collect();
            let want = eval_rounds(&p, &[], &blk, p.num_rounds());
            let mut st = mc.load(&blk);
            let init = st.clone();
            mc.forward(&mut st, 0, p.num_rounds());
            let pre = st.clone();
            mc.add_feed_forward(&mut st, &init);
            assert_eq!(mc.store(&st), want, "w={w}");
            mc.sub_feed_forward(&mut st, &init);
            assert_eq!(st, pre);
            mc.backward(&mut st, p.num_rounds(), 0);
            assert_eq!(st, init);
        }
    }
}

// ---- ChaCha differential-linear controls ---------------------------------

/// Aumasson et al. (FSE 2008): ID = bit 13 of state word 13 (our block bit
/// `13*32 + 13`, RFC 8439 word order, bit `k` = value `2^k`), OD = bit 0 of
/// word 11 after 3 rounds, published bias `0.026`. Measured at full 32-bit
/// width with 2^22 pairs (random key and counter/nonce, constants fixed,
/// state before the feed-forward). The published figure is given to two
/// digits without an error bar; the assertion is that the measured `|ε|` is
/// within 3σ of 0.026 (σ of our estimate), with the sign negative here.
#[test]
fn chacha_3round_published_differential_linear() {
    let p = chacha::chacha(3);
    let t = dl_chacha(&p, 3);
    assert!(t.uses_compiled_evaluator());
    let id = bit_vector(512, &[13 * 32 + 13]);
    let od = bit_vector(512, &[11 * 32]);
    let n = 1u64 << 22;
    let e = t.estimate_bias(&id, &od, n, 0xA11CE);
    let sigma = 1.0 / (n as f64).sqrt();
    println!(
        "ChaCha 3 rounds, ID (13,13) -> OD (11,0): eps = {:+.5} (p1 = {:.6}), N = 2^22, sigma = {:.5}, published 0.026, |diff| = {:.1} sigma",
        e.eps, e.p1, sigma, (e.eps.abs() - 0.026).abs() / sigma
    );
    assert!((e.eps.abs() - 0.026).abs() < 3.0 * sigma, "{e:?}");
    assert!(e.z.abs() > 40.0);
    // an unrelated output bit is unbiased at the same budget
    let od2 = bit_vector(512, &[5 * 32 + 3]);
    let e2 = t.estimate_bias(&id, &od2, n, 0xA11CE);
    assert!(e2.z.abs() < 4.0, "{e2:?}");
}

/// Group of the round-4 (diagonal) quarter round containing state word `j`.
fn diag_group(j: usize) -> [usize; 4] {
    [[0, 5, 10, 15], [1, 6, 11, 12], [2, 7, 8, 13], [3, 4, 9, 14]]
        .into_iter()
        .find(|g| g.contains(&j))
        .unwrap()
}

/// Negative-result record: single-bit differences (words 12..15) against all
/// single-bit masks on reduced-width ChaCha (w = 8: 3, 4, 5 rounds; w = 16:
/// 3, 4 rounds), 2^18 pairs per input bit, top candidates re-estimated with
/// 2^22 fresh pairs: none is distinguishable from zero.
/// Run manually: `cargo test --release --lib explore_small -- --ignored --nocapture`.
#[test]
#[ignore = "exploration"]
fn explore_small_single_bit() {
    for (w, r) in [(8usize, 3usize), (8, 4), (8, 5), (16, 3), (16, 4)] {
        let p = chacha::reduced_width(w, r);
        let t = dl_chacha(&p, r);
        let ins: Vec<usize> = (12 * w..16 * w).collect();
        let c = t.search_single_bit(&ins, 1 << 18, 4, 1 << 22, 3);
        for x in c.iter().take(3) {
            println!("w{w} r{r}: ID ({},{}) -> OD ({},{}): search {:+.4} confirm {:+.4} +- {:.4} z {:.1} (N=2^22)", x.in_bit / w, x.in_bit % w, x.out_bit / w, x.out_bit % w, x.search.eps, x.confirm.eps, x.confirm.eps_std_err(), x.confirm.z);
        }
    }
}

/// Negative-result record: all 128 single-bit differences of words 12..15
/// against all 512 single-bit masks on 4 full-width ChaCha rounds (2^20 pairs
/// each, top 6 re-estimated with 2^24 fresh pairs): every confirmation has
/// `|z| < 1.3`. Run manually with `--ignored --nocapture`.
#[test]
#[ignore = "exploration"]
fn explore_full_4round_all_ids() {
    let p = chacha::chacha(4);
    let t = dl_chacha(&p, 4);
    let ins: Vec<usize> = (12 * 32..16 * 32).collect();
    let c = t.search_single_bit(&ins, 1 << 20, 6, 1 << 24, 0xFEED);
    for x in &c {
        println!("full width r4 all 128 IDs: ID ({},{}) -> OD ({},{}): search {:+.5} (2^20) confirm {:+.5} +- {:.5} z {:.1} (2^24)", x.in_bit / 32, x.in_bit % 32, x.out_bit / 32, x.out_bit % 32, x.search.eps, x.confirm.eps, x.confirm.eps_std_err(), x.confirm.z);
    }
}

/// Negative-result record: for nine strongly biased round-3 bits (ID (13,13)),
/// every XOR of at most three bits of the round-4 quarter round that updates
/// the word is scored by correlation with the round-3 bit (2^17 pairs; the
/// best correlations, about 0.013, are at the 4.5 sigma noise level of that
/// budget); the four best predicted masks are re-measured with 2^25 pairs
/// and are consistent with zero. Run manually with `--ignored --nocapture`.
#[test]
#[ignore = "exploration"]
fn explore_ext4() {
    let p = chacha::chacha(4);
    let t = dl_chacha(&p, 4);
    let id = 13 * 32 + 13;
    let targets = [
        (3usize, 24usize, -0.1103f64),
        (3, 4, 0.0821),
        (2, 8, 0.0596),
        (0, 20, -0.058),
        (15, 0, -0.0567),
        (2, 28, 0.0558),
        (0, 0, -0.052),
        (2, 20, -0.042),
        (11, 0, -0.0273),
    ];
    let mut best: Vec<(f64, Vec<usize>)> = vec![];
    for (wd, bt, e3) in targets {
        let win: Vec<usize> = diag_group(wd)
            .iter()
            .flat_map(|&j| (0..32).map(move |b| j * 32 + b))
            .collect();
        let r = t.search_extension_masks(id, 3, wd * 32 + bt, &win, 3, 1 << 17, 4, 77);
        for (bits, c) in &r {
            let names: Vec<String> = bits
                .iter()
                .map(|b| format!("({},{})", b / 32, b % 32))
                .collect();
            println!("target r3 ({wd},{bt}) eps3 {e3:+.4}: mask {} corr {c:+.4} -> predicted eps4 {:+.5}", names.join("^"), e3 * c);
            best.push((e3 * c, bits.clone()));
        }
    }
    best.sort_by(|a, b| b.0.abs().total_cmp(&a.0.abs()));
    for (pred, bits) in best.iter().take(4) {
        let e = t.estimate_bias_bits(&[id], bits, 1 << 25, 5);
        println!("CONFIRM 4-round mask {:?}: predicted {pred:+.5}, measured eps {:+.5} +- {:.5}, z {:.1}, N = 2^25", bits.iter().map(|b| (b / 32, b % 32)).collect::<Vec<_>>(), e.eps, e.eps_std_err(), e.z);
    }
}

/// Negative-result record: all two-bit masks against single-bit differences on
/// 4 rounds of w = 16 and w = 8 ChaCha (2^20 pairs, top 3 re-estimated with
/// 2^24): none is distinguishable from zero. Run manually.
#[test]
#[ignore = "exploration"]
fn explore_w16_r4() {
    for (w, r) in [(16usize, 4usize), (8, 4)] {
        let p = chacha::reduced_width(w, r);
        let t = dl_chacha(&p, r);
        for id in [13 * w + if w == 16 { 7 } else { 3 }, 13 * w + w - 1] {
            let c = t.search_two_bit_masks(id, 1 << 20, 3, 1 << 24, 5);
            for x in &c {
                println!("w{w} r{r} ID ({},{}) -> ({},{})^({},{}): search {:+.5} confirm {:+.5} +- {:.5} z {:.1}", id / w, id % w, x.out_bits.0 / w, x.out_bits.0 % w, x.out_bits.1 / w, x.out_bits.1 % w, x.search.eps, x.confirm.eps, x.confirm.eps_std_err(), x.confirm.z);
            }
        }
    }
}

/// Table of the independence-estimate versus measurement ratio for Speck64/128
/// at 2 and 3 rounds and rotation amounts 1, 3, 8, 16 (2^19 pairs each).
/// Run manually with `--ignored --nocapture`.
#[test]
#[ignore = "exploration"]
fn explore_speck_table() {
    let p = speck::speck64_128();
    let (zb, zk) = (vec![0u64; 1], vec![0u64; 2]);
    let n = 1u64 << 19;
    for rounds in [2usize, 3] {
        for gamma in [1usize, 3, 8, 16] {
            let rc = rotational_chain(&p, rounds, gamma);
            let rx = rx_chain(&p, rounds, gamma, &zb, &zk);
            let e = empirical_rx(&p, rounds, gamma, &zb, &zk, &rx.out_delta, n, 99);
            let pr = rx.prob();
            let sig = (pr * (1.0 - pr) / n as f64).sqrt();
            print!(
                "Speck64 {rounds}r gamma {gamma:2}: RX est {:.3e} emp {:.3e} ratio {:.2} z {:+.1}",
                pr,
                e.p1,
                e.p1 / pr,
                (e.p1 - pr) / sig
            );
            if rounds == 2 {
                let e0 = empirical_rx(&p, rounds, gamma, &zb, &zk, &zb, n, 98);
                println!(
                    " | ROT est {:.3e} emp {:.3e} ratio {:.2}",
                    rc.prob(),
                    e0.p1,
                    e0.p1 / rc.prob()
                );
            } else {
                println!();
            }
        }
    }
}

// ---- PNB end to end -------------------------------------------------------

/// Full-width ChaCha6 and ChaCha7 PNB estimates with the published
/// distinguisher (13,13) -> (11,0) on r = 3 rounds, `ε_d` measured with 2^22
/// pairs, neutrality with 2^12 draws, `ε_a` with 2^20 draws for each of the
/// fixed thresholds `γ in {0.9, 0.8, 0.7, 0.6, 0.5, 0.4}`. The best
/// significant row is reported (the threshold grid is fixed in advance and
/// nothing is tuned toward a target). Published: 2^139 (ChaCha6) and 2^248
/// (ChaCha7), Aumasson et al. 2008; 2^77.4 for 6 rounds is a later line.
#[test]
fn chacha_pnb_full_width_estimates() {
    let nb = 512;
    let id = bit_vector(nb, &[13 * 32 + 13]);
    let od = bit_vector(nb, &[11 * 32]);
    for (big_r, lo, hi) in [(6usize, 110.0, 160.0), (7, 200.0, 256.0)] {
        let p = chacha::chacha(big_r);
        let t = PnbTarget::chacha(&p);
        let (d, e) = t.distinguisher(3, id.clone(), od.clone(), 1 << 22, 41);
        let g = t.neutrality_measures(&d, 1 << 12, 42);
        let rows = t.sweep(&d, &g, &[0.9, 0.8, 0.7, 0.6, 0.5, 0.4], 1 << 20, 43);
        for r in &rows {
            println!(
                "ChaCha{big_r} r=3 gamma {:.1}: m {:3} eps_a {:+.4} (z {:.1}) eps_d {:+.4} eps* prod {:+.2e} direct {:+.2e}  log2 N {:.1} alpha {:.0} log2 T {:.1} (direct-eps* log2 T {:.1}){}",
                r.gamma, r.m, r.backward.eps_a.eps, r.backward.eps_a.z, d.eps_d, d.eps_d * r.backward.eps_a.eps,
                r.backward.eps_star_direct.eps, r.complexity.log2_data_pairs, r.complexity.alpha, r.complexity.log2_time,
                r.complexity_direct.log2_time, if r.significant() { "" } else { "  [not significant]" }
            );
        }
        let best = best_significant(&rows).expect("a significant row");
        println!(
            "ChaCha{big_r}: eps_d = {:+.5} (N = 2^22); best significant: gamma {:.1}, m = {}, log2 time = {:.1}, log2 data (pairs) = {:.1}; published {}",
            e.eps, best.gamma, best.m, best.complexity.log2_time, best.complexity.log2_data_pairs,
            if big_r == 6 { "2^139 (Aumasson et al. 2008); later line 2^77.4" } else { "2^248 (Aumasson et al. 2008)" }
        );
        assert!(
            best.complexity.log2_time > lo && best.complexity.log2_time < hi,
            "{best:?}"
        );
        assert!(best.complexity.beats_brute_force);
    }
}

/// End-to-end PNB key recovery on 4-round, 16-bit-word ChaCha (128-bit
/// key) as a **key-space-reduced instance**: the distinguisher is found by
/// search on r = 2 rounds (`R - r = 2` rounds are inverted), the 24
/// unknown key bits (below; the other 104 bits are given to the attacker)
/// are chosen from the neutrality measures, the data is produced through the IR, phase 1 enumerates the
/// non-PNB unknown bits and phase 2 the PNB unknown bits. Recovery of the
/// full key is asserted.
///
/// Unknown part: the 16 least-neutral key bits plus 8 key bits with
/// `γ >= 0.9`; the PNBs are those 8 (threshold 0.9).
#[test]
fn pnb_w16_four_round_key_recovery() {
    let p = chacha::reduced_width(16, 4);
    let t = PnbTarget::chacha(&p);
    let ins: Vec<usize> = (12 * 16..14 * 16).collect();
    let (d, c) = t.find_distinguisher(2, &ins, 1 << 16, 8, 1 << 20, 13);
    println!(
        "w16 R=4 r=2 distinguisher: ID ({},{}) OD ({},{}) eps_d {:+.4}",
        c.in_bit / 16,
        c.in_bit % 16,
        c.out_bit / 16,
        c.out_bit % 16,
        c.confirm.eps
    );
    assert!(c.confirm.eps.abs() > 0.5);
    let g = t.neutrality_measures(&d, 1 << 14, 5);
    let mut order: Vec<usize> = (0..128).collect();
    order.sort_by(|&a, &b| g[a].total_cmp(&g[b]));
    let mut unknown: Vec<usize> = order[..16].to_vec();
    let high: Vec<usize> = order
        .iter()
        .copied()
        .filter(|&i| g[i] >= 0.9)
        .take(8)
        .collect();
    assert_eq!(high.len(), 8);
    unknown.extend(&high);
    let pnb: Vec<usize> = unknown.iter().copied().filter(|&i| g[i] >= 0.9).collect();
    let b = t.backward_bias(&d, &pnb, 1 << 16, 6);
    let eps_star = d.eps_d * b.eps_a.eps;
    let n_np = unknown.len() - pnb.len();
    let pairs = (2.0 * required_pairs(eps_star, n_np as f64))
        .ceil()
        .max(256.0) as usize;
    println!(
        "unknown {} bits (non-PNB {}, PNB {}), eps_a {:+.4}, eps* {:+.4}, pairs {pairs}",
        unknown.len(),
        n_np,
        pnb.len(),
        b.eps_a.eps,
        eps_star
    );
    let mut rng = SmallRng::seed_from_u64(0x4B31_u64 ^ 0x1234);
    let key: [u64; 8] = [(); 8].map(|_| rng.gen::<u64>() & 0xFFFF);
    let res = t.recover_key(&d, &pnb, &unknown, &key, pairs, 256, 77);
    println!("{res:?}");
    assert_eq!(res.recovered, Some(key));
    assert!(res.true_rank.is_some_and(|r| r < 256));
    // the same attack's estimate for the full 128-bit key
    let rows = t.sweep(&d, &g, &[0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3], 1 << 18, 8);
    let best = best_significant(&rows).unwrap();
    println!(
        "w16 R=4 full-key estimate: gamma {:.1} m {} log2 time {:.1} (brute force 2^128)",
        best.gamma, best.m, best.complexity.log2_time
    );
    assert!(best.complexity.beats_brute_force);
}

// ---- Speck ------------------------------------------------------------------

/// One round of Speck64/128: a single addition, so the rotational and
/// rotational-XOR estimates are exact (`(1 + 2^{1-32} + 2^{-1} + 2^{-32})/4`
/// for `γ = 1`), and the empirical probability over 2^20 random pairs agrees
/// within 3σ.
#[test]
fn speck_one_round_rotational_exact() {
    let p = speck::speck64_128();
    let (zb, zk) = (vec![0u64; 1], vec![0u64; 2]);
    let rc = rotational_chain(&p, 1, 1);
    assert_eq!((rc.data_adds, rc.key_schedule_adds), (1, 0));
    assert!((rc.prob() - rot_add_prob(32, 1)).abs() < 1e-9);
    let n = 1u64 << 20;
    let e = empirical_rx(&p, 1, 1, &zb, &zk, &zb, n, 5);
    let sig = (rc.prob() * (1.0 - rc.prob()) / n as f64).sqrt();
    println!(
        "Speck64 1 round gamma 1 pure rotational: est {:.5} emp {:.5} ({:+.2} sigma)",
        rc.prob(),
        e.p1,
        (e.p1 - rc.prob()) / sig
    );
    assert!((e.p1 - rc.prob()).abs() < 3.0 * sig);
    let rx = rx_chain(&p, 1, 1, &zb, &zk);
    let er = empirical_rx(&p, 1, 1, &zb, &zk, &rx.out_delta, n, 6);
    let sig = (rx.prob() * (1.0 - rx.prob()) / n as f64).sqrt();
    println!(
        "Speck64 1 round gamma 1 RX: est {:.5} emp {:.5} ({:+.2} sigma)",
        rx.prob(),
        er.p1,
        (er.p1 - rx.prob()) / sig
    );
    assert!((er.p1 - rx.prob()).abs() < 3.0 * sig);
}

/// Speck64/128 at 2 and 3 rounds, `γ = 1`, 2^19 pairs: the chained estimate
/// (product of exact per-addition probabilities, additions assumed
/// independent) is compared with the measured probability. **The estimates
/// do not agree within 3σ**: the measured probability is about twice the
/// estimate (the additions of consecutive rounds, and the round-key
/// addition in the key schedule, are not independent: the second operand of
/// a round's addition is built from the first). The test records that
/// discrepancy: the independence estimate is a lower bound here and is
/// within a factor 3 of the measurement, and the 1-round estimate (one
/// addition, no independence assumption) is exact (previous test).
#[test]
fn speck_multi_round_independence_estimate_is_conservative() {
    let p = speck::speck64_128();
    let (zb, zk) = (vec![0u64; 1], vec![0u64; 2]);
    let n = 1u64 << 19;
    for rounds in [2usize, 3] {
        let rx = rx_chain(&p, rounds, 1, &zb, &zk);
        let e = empirical_rx(&p, rounds, 1, &zb, &zk, &rx.out_delta, n, 99);
        let est = rx.prob();
        let sig = (est * (1.0 - est) / n as f64).sqrt();
        println!(
            "Speck64 {rounds} rounds gamma 1 RX: {}+{} additions, estimate {:.3e}, measured {:.3e} (N = 2^19), ratio {:.2}, {:+.1} sigma",
            rx.data_adds, rx.key_schedule_adds, est, e.p1, e.p1 / est, (e.p1 - est) / sig
        );
        assert!(e.p1 > est && e.p1 < 3.0 * est);
        if rounds == 2 {
            let rc = rotational_chain(&p, rounds, 1);
            let e0 = empirical_rx(&p, rounds, 1, &zb, &zk, &zb, n, 98);
            println!("Speck64 2 rounds gamma 1 pure rotational: estimate {:.3e}, measured {:.3e}, ratio {:.2}", rc.prob(), e0.p1, e0.p1 / rc.prob());
            assert!(e0.p1 > rc.prob() && e0.p1 < 3.0 * rc.prob());
        }
    }
}

/// Four single ChaCha rounds at full width, input difference (13,13): the
/// 512 single-bit output masks are scanned with 2^22 pairs, and the three
/// best are re-estimated with 2^23 fresh pairs. No single-bit mask is
/// distinguishable from zero at this budget (all confirmations have
/// `|z| < 6`): **the "clearly nonzero 4-round bias" control is not met by
/// single-bit masks here** (see also the ignored scans in this file for
/// two-bit and weight-3 extension masks, also negative).
#[test]
fn chacha_4round_single_bit_bias_below_resolution() {
    let p = chacha::chacha(4);
    let t = dl_chacha(&p, 4);
    let c = t.search_single_bit(&[13 * 32 + 13], 1 << 22, 3, 1 << 23, 0xBEE5);
    for x in &c {
        println!(
            "4 rounds: ID (13,13) -> OD ({},{}): search {:+.5} (N=2^22), confirm {:+.5} +- {:.5}, z {:.1} (N=2^23)",
            x.out_bit / 32, x.out_bit % 32, x.search.eps, x.confirm.eps, x.confirm.eps_std_err(), x.confirm.z
        );
        assert!(x.confirm.z.abs() < 6.0);
    }
}
