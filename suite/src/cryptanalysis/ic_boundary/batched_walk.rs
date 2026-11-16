//! Independent walk states for one public target, advanced in bounded batches.
//! Scalar and native modes share this exact state/guard/restart schedule.
use super::{
    addmod, draw_jumps, draw_pool_offset, mix, CountedGroup, GroupOps, GroupPairScratch,
    RestartPool,
};
use rand::{rngs::StdRng, Rng, SeedableRng};

const LANES: usize = 16;

struct Lane<E> {
    point: E,
    a: u64,
    b: u64,
    steps: u64,
    fresh: bool,
    permutation: [usize; LANES],
}

pub(super) struct BatchedWalker<E: Copy> {
    generator: E,
    target: E,
    r: u64,
    cap: u64,
    native: bool,
    vector: bool,
    vector_pairs: u64,
    vector_inverse: bool,
    inverse_elements: u64,
    inverse_batches: u64,
    inverse_padded: u64,
    rng: StdRng,
    pool_rng: StdRng,
    jumps: Vec<(E, u64, u64)>,
    pool: Vec<(E, u64, u64)>,
    pool_ops: GroupOps,
    lanes: Vec<Lane<E>>,
    left: Vec<E>,
    right: Vec<E>,
    output: Vec<E>,
    scratch: GroupPairScratch,
    cursor: usize,
    ready: usize,
    generated: u64,
    consumed: u64,
    steps: u64,
    restarts: u64,
    pool_taken: u64,
    pair_calls: u64,
    pair_adds: u64,
}

impl<E: Copy> BatchedWalker<E> {
    #[allow(clippy::too_many_arguments)]
    pub(super) fn new<G: CountedGroup<Elt = E>>(
        g: &G,
        generator: E,
        target: E,
        r: u64,
        seed: u64,
        cap: u64,
        native: bool,
        pool_mode: RestartPool,
        ops: &mut GroupOps,
    ) -> Self {
        let count = cap.min(LANES as u64) as usize;
        let mut this = Self {
            generator,
            target,
            r,
            cap,
            native,
            vector: false,
            vector_pairs: 0,
            vector_inverse: false,
            inverse_elements: 0,
            inverse_batches: 0,
            inverse_padded: 0,
            rng: StdRng::seed_from_u64(seed),
            pool_rng: StdRng::seed_from_u64(seed ^ 0x504F_4F4C_5F4F_4646),
            jumps: Vec::new(),
            pool: Vec::new(),
            pool_ops: GroupOps::default(),
            lanes: Vec::with_capacity(count),
            left: Vec::with_capacity(count),
            right: Vec::with_capacity(count),
            output: Vec::with_capacity(count),
            scratch: GroupPairScratch::default(),
            cursor: 0,
            ready: 0,
            generated: 0,
            consumed: 0,
            steps: 0,
            restarts: 0,
            pool_taken: 0,
            pair_calls: 0,
            pair_adds: 0,
        };
        if cap == 0 {
            return this;
        }
        this.jumps = draw_jumps(g, generator, target, r, &mut this.rng, ops, LANES);
        if pool_mode == RestartPool::Eager {
            for _ in 0..LANES {
                this.pool.push(draw_pool_offset(
                    g,
                    generator,
                    target,
                    r,
                    &mut this.pool_rng,
                    ops,
                    &mut this.pool_ops,
                ));
            }
        }
        let a = this.rng.gen_range(1..r);
        let b = this.rng.gen_range(1..r);
        let ag = g.mul(ops, generator, a);
        let bq = g.mul(ops, target, b);
        let point = g.add(ops, ag, bq);
        for i in 0..count {
            let (pa, pb) = if i == 0 {
                (a, b)
            } else {
                this.left.push(point);
                this.right.push(this.jumps[i].0);
                (addmod(a, this.jumps[i].1, r), addmod(b, this.jumps[i].2, r))
            };
            this.lanes.push(Lane {
                point,
                a: pa,
                b: pb,
                steps: 0,
                fresh: false,
                permutation: std::array::from_fn(|i| i),
            });
        }
        if count > 1 {
            this.add_pairs(g, ops);
            for (lane, &point) in this.lanes[1..].iter_mut().zip(&this.output) {
                lane.point = point;
            }
        }
        this.generated = count as u64;
        this.restarts = count as u64;
        this.ready = count;
        this
    }

    /// Preserve shared-inverse initialization; vectorize subsequent advances.
    pub(super) fn enable_vector(&mut self) {
        self.vector = true;
    }

    pub(super) fn enable_vector_inverse(&mut self) {
        self.vector = true;
        self.vector_inverse = true;
    }

    fn add_pairs<G: CountedGroup<Elt = E>>(&mut self, g: &G, ops: &mut GroupOps) {
        self.output.clear();
        if self.vector_inverse {
            let (pairs, elements) = g.add_pairwise_vector_inverse(
                ops,
                &self.left,
                &self.right,
                &mut self.output,
                &mut self.scratch,
            );
            self.vector_pairs += pairs as u64;
            self.inverse_elements += elements as u64;
            if elements != 0 {
                self.inverse_batches += 1;
                self.inverse_padded += (elements.div_ceil(4) * 4 - elements) as u64;
            }
        } else if self.vector {
            self.vector_pairs += g.add_pairwise_vector(
                ops,
                &self.left,
                &self.right,
                &mut self.output,
                &mut self.scratch,
            ) as u64;
        } else if self.native {
            g.add_pairwise(
                ops,
                &self.left,
                &self.right,
                &mut self.output,
                &mut self.scratch,
            );
        } else {
            self.output.extend(
                self.left
                    .iter()
                    .zip(&self.right)
                    .map(|(&p, &q)| g.add(ops, p, q)),
            );
        }
        assert_eq!(self.output.len(), self.left.len());
        self.pair_calls += 1;
        self.pair_adds += self.left.len() as u64;
    }

    pub(super) fn next<G: CountedGroup<Elt = E>>(
        &mut self,
        g: &G,
        ops: &mut GroupOps,
    ) -> Option<(E, u64, u64, usize)> {
        if self.cursor == self.ready {
            let count = (self.cap - self.generated).min(self.lanes.len() as u64) as usize;
            if count == 0 {
                return None;
            }
            self.left.clear();
            self.right.clear();
            let segment_cap = ((self.r as f64).sqrt() * 4.0) as u64 + 65_536;
            for lane in &mut self.lanes[..count] {
                let (point, a, b) = if lane.fresh || lane.steps >= segment_cap {
                    let index = self.pool_taken as usize % LANES;
                    self.pool_taken += 1;
                    if index == self.pool.len() {
                        self.pool.push(draw_pool_offset(
                            g,
                            self.generator,
                            self.target,
                            self.r,
                            &mut self.pool_rng,
                            ops,
                            &mut self.pool_ops,
                        ));
                    }
                    for i in (1..LANES).rev() {
                        lane.permutation.swap(i, self.rng.gen_range(0..i + 1));
                    }
                    lane.fresh = false;
                    lane.steps = 0;
                    self.restarts += 1;
                    self.pool[index]
                } else {
                    let index = lane.permutation[(mix(g.key(&lane.point)) >> 24) as usize % LANES];
                    lane.steps += 1;
                    self.steps += 1;
                    self.jumps[index]
                };
                self.left.push(lane.point);
                self.right.push(point);
                lane.a = addmod(lane.a, a, self.r);
                lane.b = addmod(lane.b, b, self.r);
            }
            self.add_pairs(g, ops);
            for (lane, &point) in self.lanes[..count].iter_mut().zip(&self.output) {
                lane.point = point;
            }
            self.generated += count as u64;
            self.cursor = 0;
            self.ready = count;
        }
        let index = self.cursor;
        self.cursor += 1;
        self.consumed += 1;
        let lane = &self.lanes[index];
        Some((lane.point, lane.a, lane.b, index))
    }

    pub(super) fn restart(&mut self, lane: usize) {
        self.lanes[lane].fresh = true;
    }

    pub(super) fn counters<G: CountedGroup<Elt = E>>(&self, g: &G) -> [(&'static str, u64); 23] {
        [
            ("walk_jumps", (self.jumps.len() + self.pool.len()) as u64),
            ("walk_pool_offsets", self.pool.len() as u64),
            ("walk_pool_ops", self.pool_ops.adds + self.pool_ops.doubles),
            ("walk_pool_restarts", self.pool_taken),
            ("walk_steps", self.steps),
            ("walk_restarts", self.restarts),
            ("walk_batch_lanes", self.lanes.len() as u64),
            ("walk_batch_generated", self.generated),
            ("walk_batch_consumed", self.consumed),
            ("walk_batch_unused", self.generated - self.consumed),
            ("walk_batch_pair_calls", self.pair_calls),
            ("walk_batch_pair_adds", self.pair_adds),
            (
                "walk_batch_inverse_vector_requested",
                u64::from(self.vector_inverse),
            ),
            ("walk_batch_inverse_vector_elements", self.inverse_elements),
            ("walk_batch_inverse_vector_batches", self.inverse_batches),
            (
                "walk_batch_inverse_vector_padded_lanes",
                self.inverse_padded,
            ),
            (
                "walk_batch_inverse_vector_backend",
                u64::from(self.inverse_batches != 0),
            ),
            ("walk_batch_vector_requested", u64::from(self.vector)),
            ("walk_batch_vector_pairs", self.vector_pairs),
            (
                "walk_batch_vector_backend",
                u64::from(self.vector_pairs != 0),
            ),
            ("walk_batch_native_requested", u64::from(self.native)),
            (
                "walk_batch_native_backend",
                u64::from(self.native && self.pair_calls != 0 && g.has_native_pairwise()),
            ),
            (
                "walk_batch_generation_limit",
                u64::from(self.generated == self.cap),
            ),
        ]
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::{random_binary_instance, BinaryGroup};
    use std::collections::HashSet;

    fn compare_stream<G: CountedGroup>(
        g: &G,
        generator: G::Elt,
        target: G::Elt,
        r: u64,
        cap: u64,
        pool: RestartPool,
    ) -> Vec<(G::Elt, u64, u64)> {
        let mut native_ops = GroupOps::default();
        let mut scalar_ops = GroupOps::default();
        let mut vector_ops = GroupOps::default();
        let mut inverse_ops = GroupOps::default();
        let mut native = BatchedWalker::new(
            g,
            generator,
            target,
            r,
            71,
            cap,
            true,
            pool,
            &mut native_ops,
        );
        let mut scalar = BatchedWalker::new(
            g,
            generator,
            target,
            r,
            71,
            cap,
            false,
            pool,
            &mut scalar_ops,
        );
        let mut vector = BatchedWalker::new(
            g,
            generator,
            target,
            r,
            71,
            cap,
            true,
            pool,
            &mut vector_ops,
        );
        vector.enable_vector();
        let mut inverse = BatchedWalker::new(
            g,
            generator,
            target,
            r,
            71,
            cap,
            true,
            pool,
            &mut inverse_ops,
        );
        inverse.enable_vector_inverse();
        let mut seen = HashSet::new();
        let mut rows = Vec::new();
        loop {
            let n = native.next(g, &mut native_ops);
            let s = scalar.next(g, &mut scalar_ops);
            assert_eq!(n, s);
            assert_eq!(n, vector.next(g, &mut vector_ops));
            assert_eq!(n, inverse.next(g, &mut inverse_ops));
            let Some((point, a, b, lane)) = n else {
                break;
            };
            let mut check_ops = GroupOps::default();
            let ag = g.mul(&mut check_ops, generator, a);
            let bq = g.mul(&mut check_ops, target, b);
            assert_eq!(point, g.add(&mut check_ops, ag, bq));
            if g.is_identity(&point) || !seen.insert(g.key(&point)) || rows.len() % 11 == 0 {
                native.restart(lane);
                scalar.restart(lane);
                vector.restart(lane);
                inverse.restart(lane);
            }
            rows.push((point, a, b));
            assert!(rows.len() as u64 <= cap);
        }
        assert_eq!(rows.len() as u64, cap);
        assert_eq!(native_ops, scalar_ops);
        assert_eq!(native_ops, vector_ops);
        assert_eq!(native_ops, inverse_ops);
        let nc = native.counters(g);
        let sc = scalar.counters(g);
        for ((name, nv), (sname, sv)) in nc.iter().zip(&sc) {
            assert_eq!(name, sname);
            if !matches!(
                *name,
                "walk_batch_native_requested" | "walk_batch_native_backend"
            ) {
                assert_eq!(nv, sv, "{name}");
            }
        }
        for ((name, value), (vname, vvalue)) in nc.iter().zip(vector.counters(g)) {
            assert_eq!(*name, vname);
            if !name.starts_with("walk_batch_vector_") {
                assert_eq!(*value, vvalue, "{name}");
            }
        }
        for ((name, value), (iname, ivalue)) in nc.iter().zip(inverse.counters(g)) {
            assert_eq!(*name, iname);
            if !name.starts_with("walk_batch_vector_")
                && !name.starts_with("walk_batch_inverse_vector_")
            {
                assert_eq!(*value, ivalue, "{name}");
            }
        }
        rows
    }

    #[test]
    fn native_and_scalar_streams_preserve_coefficients_restarts_and_caps() {
        let inst = random_binary_instance(13, 3, 8).unwrap();
        let group = BinaryGroup(&inst.fast);
        let target = group.mul(&mut GroupOps::default(), inst.generator, 17);
        for cap in [0, 1, 7, 16, 17, 31, 128, 257] {
            let lazy = compare_stream(
                &group,
                inst.generator,
                target,
                inst.r,
                cap,
                RestartPool::Lazy,
            );
            let eager = compare_stream(
                &group,
                inst.generator,
                target,
                inst.r,
                cap,
                RestartPool::Eager,
            );
            assert_eq!(lazy, eager, "pool policy changed the stream at cap={cap}");
        }
        let mut ops = GroupOps::default();
        let mut walker = BatchedWalker::new(
            &group,
            inst.generator,
            target,
            inst.r,
            71,
            128,
            true,
            RestartPool::Lazy,
            &mut ops,
        );
        for _ in 0..5 {
            assert!(walker.next(&group, &mut ops).is_some());
        }
        let counts: std::collections::BTreeMap<_, _> =
            walker.counters(&group).into_iter().collect();
        assert_eq!(counts["walk_batch_generated"], 16);
        assert_eq!(counts["walk_batch_consumed"], 5);
        assert_eq!(counts["walk_batch_unused"], 11);
        assert_eq!(counts["walk_batch_pair_adds"], 15);
    }

    struct Additive101;
    impl CountedGroup for Additive101 {
        type Elt = u64;
        fn identity(&self) -> u64 {
            0
        }
        fn is_identity(&self, p: &u64) -> bool {
            *p == 0
        }
        fn add(&self, ops: &mut GroupOps, p: u64, q: u64) -> u64 {
            ops.adds += 1;
            (p + q) % 101
        }
        fn double(&self, ops: &mut GroupOps, p: u64) -> u64 {
            ops.doubles += 1;
            2 * p % 101
        }
        fn neg(&self, p: u64) -> u64 {
            (101 - p) % 101
        }
        fn key(&self, p: &u64) -> u64 {
            *p
        }
    }
    #[test]
    fn generic_pairwise_fallback_preserves_the_same_schedule() {
        assert!(!Additive101.has_native_pairwise());
        for cap in [0, 1, 17, 257] {
            compare_stream(&Additive101, 1, 17, 101, cap, RestartPool::Lazy);
        }
    }
}
