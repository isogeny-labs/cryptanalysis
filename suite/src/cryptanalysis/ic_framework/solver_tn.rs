//! # `tn-f2`: bucket elimination as a polynomial-system solver.
//!
//! A boolean system `p_1 = … = p_m = 0` over `F_2^n` is a tensor
//! network: one Boolean factor `[p_j(x) = 0]` per equation over its
//! support, and the solution set is the support of the contraction of
//! all factors.  This engine contracts it by **variable elimination**
//! (bucket elimination, Dechter 1999): pick an order of the variables;
//! to eliminate `x`, multiply (AND) every factor that mentions `x` and
//! sum (OR) `x` out, which makes one new factor over the union of their
//! scopes minus `x`.  The cost is `2^w` table entries per bucket, `w`
//! the *induced width* of the order on the primal graph (two variables
//! adjacent iff they share an equation).
//!
//! * **Factors** are dense bit tables over the variables of their scope
//!   in ascending index order (`table[pext(point, scope_mask)]`).  An
//!   equation's table is its ANF turned into a truth table by a Möbius
//!   transform on the packed words.
//! * **Order**: greedy min-fill, ties by min-degree then index.
//! * **Solutions** are enumerated by back-substitution in the reverse
//!   order.  Every bucket's generated factor says which assignments of
//!   its scope extend, so the search never dead-ends: the work is
//!   `O(#solutions · n)` lookups on top of the contraction.
//! * **Resource limit, never a wrong answer**: the induced width of the
//!   order is known before any table is built.  Above `tn_max_width`
//!   (default 26) the engine returns [`SolverVerdict::BudgetExceeded`]
//!   and records `width_limit_exceeded = 1` and the width in `extra`;
//!   it never answers `Unsatisfiable` or a partial solution list for a
//!   system it did not contract.  The same verdict is returned on the
//!   wall budget and on `tn_max_solutions` (default 2^22).
//!
//! Native unit: `table entries` — entries written (initial truth tables
//! and generated factors) plus entries read (factor lookups during
//! contraction and back-substitution).  It is not `word XORs`, so the
//! runner prices the engine by its measured wall time.
//!
//! Dense descents (every equation touches every unknown) have induced
//! width `n_vars - 1`: the contraction is then an exhaustive search over
//! `2^{n_vars}` points with a worse constant than `fes-f2`.  The engine
//! earns something only on systems whose primal graph has a small
//! separator; `induced_width_sum / calls` in the report says which kind
//! the pipeline produces.

use std::collections::BTreeMap;
use std::time::{Duration, Instant};

use super::stages::{BooleanSystem, Params, SolverCost, SolverVerdict, SystemShape, SystemSolver};
use crate::cryptanalysis::pq_groebner_f2::F2BoolPoly;

/// Default induced-width budget: a generated table of `2^26` bits is
/// 8 MiB.
pub const DEFAULT_MAX_WIDTH: u64 = 26;
/// Default cap on the number of solutions returned.
pub const DEFAULT_MAX_SOLUTIONS: u64 = 1 << 22;

// ── bit gather / scatter ───────────────────────────────────────────

#[inline(always)]
fn pext_soft(x: u64, mut m: u64) -> u64 {
    let mut out = 0u64;
    let mut k = 0;
    while m != 0 {
        let low = m & m.wrapping_neg();
        if x & low != 0 {
            out |= 1 << k;
        }
        k += 1;
        m ^= low;
    }
    out
}

#[inline(always)]
fn pdep_soft(x: u64, mut m: u64) -> u64 {
    let mut out = 0u64;
    let mut k = 0;
    while m != 0 {
        let low = m & m.wrapping_neg();
        if x >> k & 1 != 0 {
            out |= low;
        }
        k += 1;
        m ^= low;
    }
    out
}

#[inline(always)]
fn pext<const HW: bool>(x: u64, m: u64) -> u64 {
    #[cfg(target_arch = "x86_64")]
    if HW {
        // SAFETY: HW is only instantiated under a bmi2 target feature.
        return unsafe { core::arch::x86_64::_pext_u64(x, m) };
    }
    pext_soft(x, m)
}

#[inline(always)]
fn pdep<const HW: bool>(x: u64, m: u64) -> u64 {
    #[cfg(target_arch = "x86_64")]
    if HW {
        // SAFETY: as above.
        return unsafe { core::arch::x86_64::_pdep_u64(x, m) };
    }
    pdep_soft(x, m)
}

fn have_bmi2() -> bool {
    #[cfg(target_arch = "x86_64")]
    {
        std::arch::is_x86_feature_detected!("bmi2")
    }
    #[cfg(not(target_arch = "x86_64"))]
    {
        false
    }
}

// ── factors ────────────────────────────────────────────────────────

/// A Boolean function of the variables in `mask`, as a packed truth
/// table indexed by `pext(point, mask)`.
struct Factor {
    mask: u64,
    bits: Vec<u64>,
}

impl Factor {
    fn width(&self) -> u32 {
        self.mask.count_ones()
    }

    #[inline(always)]
    fn get(&self, idx: u64) -> bool {
        self.bits[(idx >> 6) as usize] >> (idx & 63) & 1 != 0
    }

    fn bytes(&self) -> u64 {
        self.bits.len() as u64 * 8
    }
}

fn table_words(width: u32) -> usize {
    if width <= 6 {
        1
    } else {
        1usize << (width - 6)
    }
}

/// Valid-bit mask of a table of this width's single word.
fn tail_mask(width: u32) -> u64 {
    if width >= 6 {
        !0
    } else {
        (1u64 << (1u64 << width)) - 1
    }
}

/// In-place subset-sum (Möbius) transform over F_2 on a packed table:
/// ANF coefficients in, truth table out.
fn mobius(bits: &mut [u64], width: u32) {
    const LOW: [u64; 6] = [
        0x5555_5555_5555_5555,
        0x3333_3333_3333_3333,
        0x0f0f_0f0f_0f0f_0f0f,
        0x00ff_00ff_00ff_00ff,
        0x0000_ffff_0000_ffff,
        0x0000_0000_ffff_ffff,
    ];
    for j in 0..width.min(6) {
        for w in bits.iter_mut() {
            *w ^= (*w & LOW[j as usize]) << (1u32 << j);
        }
    }
    for j in 6..width {
        let half = 1usize << (j - 6);
        let mut base = 0;
        while base < bits.len() {
            for i in base..base + half {
                bits[i + half] ^= bits[i];
            }
            base += 2 * half;
        }
    }
}

/// The factor `[p = 0]` over the support of `p`.
fn equation_factor(p: &F2BoolPoly) -> Factor {
    let mask = p.terms.iter().fold(0u64, |a, t| a | t.mask);
    let k = mask.count_ones();
    let mut bits = vec![0u64; table_words(k)];
    for t in &p.terms {
        let idx = pext_soft(t.mask, mask);
        bits[(idx >> 6) as usize] ^= 1 << (idx & 63);
    }
    mobius(&mut bits, k);
    for w in bits.iter_mut() {
        *w = !*w;
    }
    if k < 6 {
        bits[0] &= tail_mask(k);
    }
    Factor { mask, bits }
}

// ── elimination order ──────────────────────────────────────────────

/// Greedy min-fill order on the primal graph.  Returns the order and the
/// induced width (the largest neighbour set at elimination, which is the
/// scope of the factor that elimination generates).
fn min_fill_order(n: usize, scopes: &[u64]) -> (Vec<usize>, u32) {
    let mut adj = vec![0u64; n];
    for &s in scopes {
        for v in 0..n {
            if s >> v & 1 != 0 {
                adj[v] |= s & !(1u64 << v);
            }
        }
    }
    let mut alive: u64 = if n == 64 { !0 } else { (1u64 << n) - 1 };
    let mut order = Vec::with_capacity(n);
    let mut width = 0u32;
    while alive != 0 {
        let mut best: Option<(u32, u32, usize)> = None;
        for v in 0..n {
            if alive >> v & 1 == 0 {
                continue;
            }
            let nb = adj[v] & alive;
            let deg = nb.count_ones();
            let mut fill = 0u32;
            let mut r = nb;
            while r != 0 {
                let u = r.trailing_zeros() as usize;
                r &= r - 1;
                fill += (nb & !adj[u] & !(1u64 << u)).count_ones();
            }
            let key = (fill / 2, deg, v);
            if best.map_or(true, |b| key < b) {
                best = Some(key);
            }
        }
        let (_, deg, v) = best.unwrap();
        let nb = adj[v] & alive;
        width = width.max(deg);
        let mut r = nb;
        while r != 0 {
            let u = r.trailing_zeros() as usize;
            r &= r - 1;
            adj[u] |= nb & !(1u64 << u);
        }
        alive &= !(1u64 << v);
        order.push(v);
    }
    (order, width)
}

// ── contraction ────────────────────────────────────────────────────

#[derive(Default)]
struct Tally {
    written: u64,
    read: u64,
    live_bytes: u64,
    peak_bytes: u64,
    buckets: u64,
}

enum Stop {
    Wall,
    Unsat,
}

/// Eliminate `x` from the factors of its bucket: the factor over the
/// union of their scopes minus `x`, true where some value of `x` makes
/// every factor true.
#[inline(always)]
fn eliminate_kernel<const HW: bool>(
    x: usize,
    factors: &[Factor],
    deadline: Option<Instant>,
    tally: &mut Tally,
) -> Result<Factor, Stop> {
    let xbit = 1u64 << x;
    let scope = factors.iter().fold(0u64, |a, f| a | f.mask) & !xbit;
    let w = scope.count_ones();
    let mut out = vec![0u64; table_words(w)];
    let masks: Vec<u64> = factors.iter().map(|f| f.mask).collect();
    let mut read = 0u64;
    let total = 1u64 << w;
    let mut any = false;
    for v in 0..total {
        if v & 0xffff == 0 {
            if let Some(d) = deadline {
                if Instant::now() > d {
                    tally.read += read;
                    return Err(Stop::Wall);
                }
            }
        }
        let point = pdep::<HW>(v, scope);
        let mut ok = false;
        'b: for b in 0..2u64 {
            let a = point | (xbit * b);
            for (f, &m) in factors.iter().zip(&masks) {
                read += 1;
                if !f.get(pext::<HW>(a, m)) {
                    continue 'b;
                }
            }
            ok = true;
            break;
        }
        if ok {
            out[(v >> 6) as usize] |= 1 << (v & 63);
            any = true;
        }
    }
    tally.read += read;
    tally.written += total;
    if !any {
        return Err(Stop::Unsat);
    }
    Ok(Factor {
        mask: scope,
        bits: out,
    })
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "bmi2")]
unsafe fn eliminate_bmi2(
    x: usize,
    factors: &[Factor],
    deadline: Option<Instant>,
    tally: &mut Tally,
) -> Result<Factor, Stop> {
    eliminate_kernel::<true>(x, factors, deadline, tally)
}

fn eliminate(
    hw: bool,
    x: usize,
    factors: &[Factor],
    deadline: Option<Instant>,
    tally: &mut Tally,
) -> Result<Factor, Stop> {
    #[cfg(target_arch = "x86_64")]
    if hw {
        // SAFETY: `hw` is `is_x86_feature_detected!("bmi2")`.
        return unsafe { eliminate_bmi2(x, factors, deadline, tally) };
    }
    let _ = hw;
    eliminate_kernel::<false>(x, factors, deadline, tally)
}

/// Back-substitution in reverse elimination order.
fn enumerate(
    rank: isize,
    point: u64,
    order: &[usize],
    buckets: &[Vec<Factor>],
    out: &mut Vec<u64>,
    cap: usize,
    read: &mut u64,
) -> bool {
    if rank < 0 {
        if out.len() >= cap {
            return false;
        }
        out.push(point);
        return true;
    }
    let r = rank as usize;
    let x = order[r];
    for b in 0..2u64 {
        let a = point | (b << x);
        let mut ok = true;
        for f in &buckets[r] {
            *read += 1;
            if !f.get(pext::<false>(a, f.mask)) {
                ok = false;
                break;
            }
        }
        if ok && !enumerate(rank - 1, a, order, buckets, out, cap, read) {
            return false;
        }
    }
    true
}

/// `tn-f2`.
pub struct TnF2;

impl SystemSolver for TnF2 {
    fn name(&self) -> &str {
        "tn-f2"
    }

    fn describe(&self) -> String {
        "tensor-network contraction: bucket elimination of one Boolean factor per equation, min-fill order, dense bit tables, back-substitution for every solution; aborts above an induced-width budget".into()
    }

    fn parameters(&self) -> &[(&str, &str)] {
        &[
            (
                "tn_max_width",
                "largest induced width (variables in a generated factor) the engine will contract; above it the call is BudgetExceeded (default 26)",
            ),
            (
                "tn_max_solutions",
                "most solutions returned; above it the call is BudgetExceeded (default 4194304)",
            ),
        ]
    }

    fn accepts(&self, shape: &SystemShape) -> bool {
        shape.n_vars <= 64
    }

    fn solve(
        &self,
        system: &BooleanSystem,
        params: &Params,
        budget: Option<Duration>,
    ) -> (SolverVerdict, SolverCost) {
        let started = Instant::now();
        let deadline = budget.map(|b| started + b);
        let max_width = params
            .u64_or("tn_max_width", DEFAULT_MAX_WIDTH)
            .unwrap_or(DEFAULT_MAX_WIDTH)
            .min(34) as u32;
        let max_solutions = params
            .u64_or("tn_max_solutions", DEFAULT_MAX_SOLUTIONS)
            .unwrap_or(DEFAULT_MAX_SOLUTIONS) as usize;
        let n = system.n_vars;
        let mut extra: BTreeMap<String, u64> = BTreeMap::new();
        let mut tally = Tally::default();

        let finish = |verdict: SolverVerdict,
                      tally: &Tally,
                      mut extra: BTreeMap<String, u64>,
                      timed_out: bool,
                      enum_read: u64| {
            extra.insert("entries_written".into(), tally.written);
            extra.insert("entries_read".into(), tally.read + enum_read);
            extra.insert("buckets".into(), tally.buckets);
            extra.insert("peak_table_bytes".into(), tally.peak_bytes);
            let cost = SolverCost {
                ops: tally.written + tally.read + enum_read,
                op_unit: "table entries".into(),
                wall_ns: started.elapsed().as_nanos() as u64,
                peak_bytes: tally.peak_bytes,
                degree_reached: None,
                solving_degree: None,
                timed_out,
                extra,
            };
            (verdict, cost)
        };

        // Scopes first: the width is known before any table exists.
        let supports: Vec<u64> = system
            .equations
            .iter()
            .map(|p| p.terms.iter().fold(0u64, |a, t| a | t.mask))
            .collect();
        let live: Vec<usize> = (0..system.equations.len())
            .filter(|&i| !system.equations[i].terms.is_empty())
            .collect();
        let scopes: Vec<u64> = live.iter().map(|&i| supports[i]).collect();
        let (order, width) = min_fill_order(n, &scopes);
        extra.insert("induced_width_sum".into(), width as u64);
        extra.insert("n_vars_sum".into(), n as u64);
        let max_support = scopes.iter().map(|s| s.count_ones()).max().unwrap_or(0);
        extra.insert("max_support_sum".into(), max_support as u64);
        if width > max_width || max_support > max_width + 1 {
            extra.insert("width_limit_exceeded".into(), 1);
            return finish(SolverVerdict::BudgetExceeded, &tally, extra, false, 0);
        }

        let mut rank_of = vec![0usize; n];
        for (r, &v) in order.iter().enumerate() {
            rank_of[v] = r;
        }
        let first_rank = |mask: u64| -> usize {
            let mut m = mask;
            let mut best = usize::MAX;
            while m != 0 {
                let v = m.trailing_zeros() as usize;
                m &= m - 1;
                best = best.min(rank_of[v]);
            }
            best
        };

        let mut buckets: Vec<Vec<Factor>> = (0..n).map(|_| Vec::new()).collect();
        for &i in &live {
            let f = equation_factor(&system.equations[i]);
            tally.written += 1u64 << f.width();
            if f.width() == 0 {
                if !f.get(0) {
                    return finish(SolverVerdict::Unsatisfiable, &tally, extra, false, 0);
                }
                continue;
            }
            tally.live_bytes += f.bytes();
            tally.peak_bytes = tally.peak_bytes.max(tally.live_bytes);
            buckets[first_rank(f.mask)].push(f);
        }

        let hw = have_bmi2();
        for r in 0..n {
            if buckets[r].is_empty() {
                continue;
            }
            tally.buckets += 1;
            match eliminate(hw, order[r], &buckets[r], deadline, &mut tally) {
                Ok(g) => {
                    if g.width() == 0 {
                        // Constant true (a false constant is `Unsat`).
                        continue;
                    }
                    tally.live_bytes += g.bytes();
                    tally.peak_bytes = tally.peak_bytes.max(tally.live_bytes);
                    let dest = first_rank(g.mask);
                    buckets[dest].push(g);
                }
                Err(Stop::Unsat) => {
                    return finish(SolverVerdict::Unsatisfiable, &tally, extra, false, 0)
                }
                Err(Stop::Wall) => {
                    return finish(SolverVerdict::BudgetExceeded, &tally, extra, true, 0)
                }
            }
        }

        let mut out = Vec::new();
        let mut read = 0u64;
        let complete = enumerate(
            n as isize - 1,
            0,
            &order,
            &buckets,
            &mut out,
            max_solutions,
            &mut read,
        );
        extra.insert("solutions".into(), out.len() as u64);
        if !complete {
            extra.insert("solution_cap_exceeded".into(), 1);
            return finish(SolverVerdict::BudgetExceeded, &tally, extra, false, read);
        }
        out.sort_unstable();
        // A satisfiable contraction always yields a point; an empty list
        // here would be a bug, never a verdict.
        assert!(!out.is_empty(), "tn-f2: contraction passed, no solution");
        finish(SolverVerdict::Solved(out), &tally, extra, false, read)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::pq_groebner_f2::F2BoolMono;
    use rand::{Rng, SeedableRng};
    use std::collections::BTreeSet;

    fn set_of(v: SolverVerdict) -> BTreeSet<u64> {
        match v {
            SolverVerdict::Solved(s) => s.into_iter().collect(),
            SolverVerdict::Unsatisfiable => BTreeSet::new(),
            other => panic!("undecided: {other:?}"),
        }
    }

    fn reference(sys: &BooleanSystem) -> BTreeSet<u64> {
        let mut out = BTreeSet::new();
        for v in 0..1u64 << sys.n_vars {
            if sys.equations.iter().all(|e| e.eval(v) == 0) {
                out.insert(v);
            }
        }
        out
    }

    /// Random sparse systems of mixed degree: low-width, so the
    /// contraction does real elimination rather than one big table.
    fn random_sparse(n: usize, m: usize, rng: &mut impl Rng) -> BooleanSystem {
        let equations = (0..m)
            .map(|_| {
                let k = rng.gen_range(1..=4.min(n));
                let mut support = 0u64;
                while support.count_ones() < k as u32 {
                    support |= 1 << rng.gen_range(0..n);
                }
                let mut monos = Vec::new();
                for sub in 0..1u64 << k {
                    if rng.gen_bool(0.4) {
                        monos.push(F2BoolMono::from_mask(pdep_soft(sub, support)));
                    }
                }
                F2BoolPoly::from_monos(monos, n)
            })
            .collect();
        BooleanSystem {
            equations,
            n_vars: n,
        }
    }

    #[test]
    fn matches_exhaustive_on_random_systems() {
        let mut rng = rand::rngs::StdRng::seed_from_u64(20261122);
        let mut sat = 0;
        for trial in 0..400usize {
            let n = 1 + trial % 14;
            let m = 1 + trial % 9;
            let sys = random_sparse(n, m, &mut rng);
            let want = reference(&sys);
            let (v, cost) = TnF2.solve(&sys, &Params::default(), None);
            assert_eq!(set_of(v), want, "trial {trial} n={n} m={m}");
            assert_eq!(cost.op_unit, "table entries");
            sat += !want.is_empty() as usize;
        }
        assert!(sat > 50 && sat < 400, "both outcomes exercised: {sat}");
    }

    #[test]
    fn matches_exhaustive_on_dense_quadratics_and_free_variables() {
        let mut rng = rand::rngs::StdRng::seed_from_u64(9);
        for trial in 0..60usize {
            let n = 2 + trial % 11;
            // fewer equations than unknowns: many solutions, some free
            let m = 1 + trial % 4;
            let equations = (0..m)
                .map(|_| {
                    let mut monos = vec![];
                    for i in 0..n.saturating_sub(trial % 3) {
                        for j in 0..i {
                            if rng.gen_bool(0.5) {
                                monos.push(F2BoolMono::from_mask((1 << i) | (1 << j)));
                            }
                        }
                        if rng.gen_bool(0.5) {
                            monos.push(F2BoolMono::from_mask(1 << i));
                        }
                    }
                    F2BoolPoly::from_monos(monos, n)
                })
                .collect();
            let sys = BooleanSystem {
                equations,
                n_vars: n,
            };
            let (v, _) = TnF2.solve(&sys, &Params::default(), None);
            assert_eq!(set_of(v), reference(&sys), "trial {trial}");
        }
    }

    #[test]
    fn constants_and_unsatisfiable() {
        let one = F2BoolPoly::one(3);
        let zero = F2BoolPoly::zero(3);
        let sys = BooleanSystem {
            equations: vec![zero.clone()],
            n_vars: 3,
        };
        assert_eq!(
            set_of(TnF2.solve(&sys, &Params::default(), None).0).len(),
            8
        );
        let sys = BooleanSystem {
            equations: vec![zero, one],
            n_vars: 3,
        };
        assert!(matches!(
            TnF2.solve(&sys, &Params::default(), None).0,
            SolverVerdict::Unsatisfiable
        ));
    }

    /// Above the width budget the answer is a recorded resource limit,
    /// not `Unsatisfiable` and not a partial list.
    #[test]
    fn width_budget_is_a_resource_limit() {
        let n = 12;
        let all = (1u64 << n) - 1;
        let sys = BooleanSystem {
            equations: vec![F2BoolPoly::from_monos(
                vec![F2BoolMono::from_mask(all), F2BoolMono::from_mask(0)],
                n,
            )],
            n_vars: n,
        };
        let mut p = Params::default();
        p.set("tn_max_width", "5");
        let (v, cost) = TnF2.solve(&sys, &p, None);
        assert!(matches!(v, SolverVerdict::BudgetExceeded));
        assert_eq!(cost.extra["width_limit_exceeded"], 1);
        assert_eq!(cost.ops, 0, "no table is built past the limit");
        let (v, _) = TnF2.solve(&sys, &Params::default(), None);
        // all-ones monomial + 1 = 0 has the single solution v = 1…1
        assert_eq!(set_of(v), [all].into_iter().collect());
    }

    /// Real descended systems of a tiny instance: the same solution set
    /// as `exhaustive`.
    #[test]
    fn matches_exhaustive_on_descent_systems() {
        use super::super::solvers::Exhaustive;
        use crate::cryptanalysis::ic_boundary::random_binary_instance;
        use crate::cryptanalysis::pq_descent_symbolic::descend;
        let mut rng = rand::rngs::StdRng::seed_from_u64(7);
        let mut widths = Vec::new();
        for &(n, np, m, seed) in &[
            (7u32, 4u32, 2u32, 1u64),
            (9, 5, 2, 2),
            (11, 6, 2, 3),
            (7, 2, 3, 4),
        ] {
            let inst = random_binary_instance(n, seed, 1 << 20).unwrap();
            let words: Vec<u64> = (0..np).map(|k| 1u64 << k).collect();
            for t in 0..4 {
                let x_r = rng.gen::<u64>() & ((1u64 << n) - 1);
                let d = descend(&inst.gf, inst.b, x_r, &words, m).unwrap();
                let sys = BooleanSystem {
                    equations: d.equations,
                    n_vars: d.n_vars,
                };
                let (tn, cost) = TnF2.solve(&sys, &Params::default(), None);
                let (ex, _) = Exhaustive.solve(&sys, &Params::default(), None);
                assert_eq!(set_of(tn), set_of(ex), "n={n} n'={np} m={m} target {t}");
                widths.push((sys.n_vars, cost.extra["induced_width_sum"]));
            }
        }
        eprintln!("(n_vars, induced width) per descent system: {widths:?}");
    }
}
