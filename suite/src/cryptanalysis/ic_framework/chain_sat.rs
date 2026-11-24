//! Native, finite-affine-chart S3 networks. Local monomial masks never span
//! the whole network: each block has at most 3n <= 63 symbolic variables.
//! UNSAT refutes this chart only; identity intermediate sums need other charts.
use std::collections::BTreeMap;
use std::time::Instant;

use super::stages::{
    DecompositionOracle, InstanceCtx, Params, SolverCost, SolverTotals, SystemShape,
};
use crate::cryptanalysis::ic_boundary::{
    BinaryGroup, BinaryInstance, CountedGroup, FactorBase, GroupOps, OracleCounters,
};
use crate::cryptanalysis::koblitz_fast::FastPoint;
use crate::cryptanalysis::pq_descent_symbolic::FieldBoolPoly;
use crate::cryptanalysis::sat::{check_model, Lit, SolveResult, Solver};

#[derive(Clone, Copy)]
struct Node {
    left: usize,
    right: usize,
    output: usize,
}

#[derive(Default)]
struct Encoding {
    vars: u32,
    clauses: Vec<Vec<Lit>>,
    xors: Vec<(Vec<u32>, bool)>,
}
impl Encoding {
    fn variable(&mut self) -> u32 {
        self.vars += 1;
        self.vars
    }
    fn and(&mut self, inputs: &[u32]) -> u32 {
        if inputs.len() == 1 {
            return inputs[0];
        }
        let output = self.variable();
        for &input in inputs {
            self.clauses.push(vec![-(output as Lit), input as Lit]);
        }
        let mut clause = vec![output as Lit];
        clause.extend(inputs.iter().map(|&v| -(v as Lit)));
        self.clauses.push(clause);
        output
    }
}

pub struct ChainSatOracle<'i> {
    m: u32,
    instance: &'i BinaryInstance,
    topology: String,
    conflict_cap: u64,
    model_cap: u64,
    prepared: bool,
    nodes: Vec<Node>,
    words: usize,
    encoding: Encoding,
    shape: SystemShape,
    totals: SolverTotals,
    setup: BTreeMap<String, u64>,
    native: BTreeMap<String, u64>,
}
impl<'i> ChainSatOracle<'i> {
    pub fn new(m: u32, instance: &'i BinaryInstance) -> Self {
        Self {
            m,
            instance,
            topology: "serial".into(),
            conflict_cap: 10_000,
            model_cap: 128,
            prepared: false,
            nodes: Vec::new(),
            words: 0,
            encoding: Encoding::default(),
            shape: SystemShape::default(),
            totals: SolverTotals {
                solver: "native-chain-sat".into(),
                ..Default::default()
            },
            setup: BTreeMap::new(),
            native: BTreeMap::new(),
        }
    }
    fn count(&mut self, key: &str, value: u64) {
        *self.native.entry(key.into()).or_default() += value;
    }
    fn bit(&self, word: usize, bit: u32) -> u32 {
        word as u32 * self.instance.n + bit + 1
    }
    fn word(&self, model: &[bool], word: usize) -> u64 {
        (0..self.instance.n).fold(0, |x, k| {
            x | ((model[(self.bit(word, k) - 1) as usize] as u64) << k)
        })
    }
    fn topology(&mut self) {
        self.nodes.clear();
        self.words = self.m as usize;
        fn subtree(this: &mut ChainSatOracle<'_>, first: usize, end: usize) -> usize {
            if end - first == 1 {
                return first;
            }
            let middle = if this.topology == "serial" {
                end - 1
            } else {
                first + (end - first) / 2
            };
            let left = subtree(this, first, middle);
            let right = subtree(this, middle, end);
            let output = this.words;
            this.words += 1;
            this.nodes.push(Node {
                left,
                right,
                output,
            });
            output
        }
        subtree(self, 0, self.m as usize);
    }
    fn lift(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'_>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        model: &[bool],
        target: FastPoint,
    ) -> Option<Vec<usize>> {
        let mut witnesses: Vec<Option<(FastPoint, Vec<usize>)>> = vec![None; self.words];
        for (leaf, slot) in witnesses.iter_mut().enumerate().take(self.m as usize) {
            let x = self.word(model, leaf);
            self.count("chain_leaf_table_lookups", 1);
            let &index = fb.x_index.get(&x)?.first()?;
            *slot = Some((fb.points[index], vec![index]));
        }
        let nodes = self.nodes.clone();
        for node in nodes {
            let (a, mut ia) = witnesses[node.left].take()?;
            let (b, mut ib) = witnesses[node.right].take()?;
            let x = self.word(model, node.output);
            let plus = ctx.group.add(ops, a, b);
            let sum = if !plus.infinity && plus.x == x {
                plus
            } else {
                self.count("chain_negations", 1);
                let minus = ctx.group.add(ops, a, ctx.group.neg(b));
                if minus.infinity || minus.x != x {
                    return None;
                }
                for i in &mut ib {
                    *i = *fb.neg_index.get(*i)?;
                }
                minus
            };
            ia.extend(ib);
            witnesses[node.output] = Some((sum, ia));
        }
        let (sum, mut indices) = witnesses[self.words - 1].take()?;
        if sum != target {
            self.count("chain_negations", 1);
            if ctx.group.neg(sum) != target {
                return None;
            }
            for index in &mut indices {
                *index = *fb.neg_index.get(*index)?;
            }
        }
        // Independent full-group verification of the returned factor-base row.
        let verified = indices.iter().fold(ctx.group.identity(), |p, &i| {
            ctx.group.add(ops, p, fb.points[i])
        });
        if verified != target || indices.len() != self.m as usize {
            return None;
        }
        Some(indices)
    }
}

impl<'i, 'g> DecompositionOracle<BinaryGroup<'g>> for ChainSatOracle<'i> {
    fn name(&self) -> &str {
        "chain-sat"
    }
    fn summands(&self) -> u32 {
        self.m
    }
    fn describe(&self, _: &Params) -> String {
        format!("native XOR-SAT S3 {} finite-affine tree, m={}, rational leaf table, linear group-operation witness lift; chart UNSAT only", self.topology,self.m)
    }
    fn parameters(&self) -> &[(&str, &str)] {
        &[
            ("m", "2..31"),
            ("topology", "serial|balanced"),
            (
                "conflicts",
                "per-target cumulative conflict cap; default10000",
            ),
            ("models", "per-target model cap; default128"),
        ]
    }
    fn prepare(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'g>>,
        fb: &FactorBase<FastPoint>,
        params: &Params,
        _ops: &mut GroupOps,
    ) -> Result<(), String> {
        self.prepared = false;
        if !(2..=31).contains(&self.m) {
            return Err("chain-sat requires m=2..31".into());
        }
        if self.instance.n == 0 || self.instance.n > 21 {
            return Err(
                "chain-sat local symbolic blocks require field degree1..21 (3n<=63)".into(),
            );
        }
        if ctx.field_degree != Some(self.instance.n) {
            return Err("chain-sat instance/context field mismatch".into());
        }
        for key in params.0.keys() {
            if !matches!(key.as_str(), "m" | "topology" | "conflicts" | "models") {
                return Err(format!("chain-sat does not accept `{key}`"));
            }
        }
        if params.u64_or("m", self.m as u64)? != self.m as u64 {
            return Err("chain-sat constructor/parameter m mismatch".into());
        }
        self.topology = params.get("topology").unwrap_or("serial").into();
        if !matches!(self.topology.as_str(), "serial" | "balanced") {
            return Err("topology must be serial or balanced".into());
        }
        self.conflict_cap = params.u64_or("conflicts", 10_000)?;
        self.model_cap = params.u64_or("models", 128)?;
        if fb.points.iter().any(|p| p.infinity) || fb.neg_index.len() != fb.points.len() {
            return Err("chain-sat needs finite, negation-closed factor-base points".into());
        }
        for (i, p) in fb.points.iter().enumerate() {
            if fb.neg_index[i] >= fb.points.len() || fb.points[fb.neg_index[i]] != ctx.group.neg(*p)
            {
                return Err("invalid factor-base negation map".into());
            }
        }
        self.setup.clear();
        self.native.clear();
        self.totals = SolverTotals {
            solver: "native-chain-sat".into(),
            ..Default::default()
        };
        let started = Instant::now();
        self.topology();
        let n = self.instance.n;
        let basis: Vec<u64> = (0..n).map(|k| 1u64 << k).collect();
        let x = FieldBoolPoly::linear(0, &basis);
        let y = FieldBoolPoly::linear(n, &basis);
        let z = FieldBoolPoly::linear(2 * n, &basis);
        let gf = &self.instance.gf;
        let xy = x.mul(&y, gf);
        let s3 = xy
            .add(&x.mul(&z, gf))
            .add(&y.mul(&z, gf))
            .sqr(gf)
            .add(&xy.mul(&z, gf))
            .add(&FieldBoolPoly::constant(self.instance.b));
        let equations = s3.split(n, (3 * n) as usize);
        let mut encoding = Encoding {
            vars: self.words as u32 * n,
            ..Default::default()
        };
        let mut degrees = Vec::new();
        for node in &self.nodes {
            let mapping: Vec<u32> = [node.left, node.right, node.output]
                .iter()
                .flat_map(|&word| (0..n).map(move |k| word as u32 * n + k + 1))
                .collect();
            let mut products = BTreeMap::<u64, u32>::new();
            for eq in &equations {
                let mut row = Vec::new();
                let mut rhs = false;
                let mut degree = 0;
                for mono in &eq.terms {
                    degree = degree.max(mono.mask.count_ones());
                    if mono.mask == 0 {
                        rhs = !rhs;
                        continue;
                    }
                    let product = *products.entry(mono.mask).or_insert_with(|| {
                        let inputs: Vec<u32> = (0..3 * n)
                            .filter(|&k| mono.mask >> k & 1 != 0)
                            .map(|k| mapping[k as usize])
                            .collect();
                        encoding.and(&inputs)
                    });
                    row.push(product);
                }
                encoding.xors.push((row, rhs));
                degrees.push(degree);
            }
        }
        // Exactly the real factor-base abscissae, not all subspace words.
        let mut xs: Vec<u64> = fb.points.iter().map(|p| p.x).collect();
        xs.sort_unstable();
        xs.dedup();
        for leaf in 0..self.m as usize {
            let mut selectors = Vec::new();
            for &x in &xs {
                let selector = encoding.variable();
                selectors.push(selector as Lit);
                for k in 0..n {
                    let bit = self.bit(leaf, k) as Lit;
                    encoding.clauses.push(vec![
                        -(selector as Lit),
                        if x >> k & 1 != 0 { bit } else { -bit },
                    ]);
                }
            }
            encoding.clauses.push(selectors);
        }
        self.shape = SystemShape {
            n_vars: self.words * n as usize,
            n_equations: degrees.len(),
            degrees,
            semi_regular_degree: None,
        };
        self.setup
            .insert("chain_symbolic_terms".into(), s3.len() as u64);
        self.setup.insert(
            "symbolic_descent_ns".into(),
            started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
        );
        self.setup.insert(
            "chain_symbolic_field_muls".into(),
            3 * (n as u64).pow(2) + (n as u64).pow(3),
        );
        self.setup
            .insert("chain_symbolic_field_squares".into(), 3 * (n as u64).pow(2));
        self.setup
            .insert("chain_cnf_clauses".into(), encoding.clauses.len() as u64);
        self.setup
            .insert("chain_sat_variables".into(), encoding.vars as u64);
        self.setup
            .insert("chain_negations".into(), fb.points.len() as u64);
        self.encoding = encoding;
        self.prepared = true;
        Ok(())
    }
    fn setup_native(&self) -> BTreeMap<String, u64> {
        self.setup.clone()
    }
    fn relation_counters(&self) -> BTreeMap<String, u64> {
        self.native.clone()
    }
    fn decompose(
        &mut self,
        ctx: &InstanceCtx<BinaryGroup<'g>>,
        fb: &FactorBase<FastPoint>,
        ops: &mut GroupOps,
        counters: &mut OracleCounters,
        point: FastPoint,
    ) -> Option<Vec<usize>> {
        if !self.prepared {
            return None;
        }
        // Identity is outside the affine root chart, never certify a refutation.
        if point.infinity {
            self.count("chain_chart_skipped_identity", 1);
            return None;
        }
        let packing = Instant::now();
        let mut solver = Solver::new(self.encoding.vars);
        let mut clauses = self.encoding.clauses.clone();
        for k in 0..self.instance.n {
            let bit = self.bit(self.words - 1, k) as Lit;
            clauses.push(vec![if point.x >> k & 1 != 0 { bit } else { -bit }]);
        }
        for clause in &clauses {
            solver.add_clause(clause.clone());
        }
        for (row, rhs) in &self.encoding.xors {
            solver.add_xor(row, *rhs);
        }
        solver.conflict_budget = self.conflict_cap;
        self.count(
            "chain_system_build_ns",
            packing.elapsed().as_nanos().min(u64::MAX as u128) as u64,
        );
        let started = packing;
        let mut lift_ns = 0u64;
        let mut exceeded = false;
        let mut answer = None;
        if self.model_cap == 0 || self.conflict_cap == 0 {
            exceeded = true;
        } else {
            for attempt in 0..self.model_cap {
                match solver.solve() {
                    SolveResult::Unknown => {
                        exceeded = true;
                        break;
                    }
                    SolveResult::Unsat => {
                        self.count("chain_chart_unsat", 1);
                        break;
                    }
                    SolveResult::Sat => {
                        self.count("chain_models", 1);
                        let model = solver.model();
                        if !check_model(&clauses, &model) || !solver.check_xors(&model) {
                            self.count("chain_invalid_sat_models", 1);
                            exceeded = true;
                            break;
                        }
                        let lift_started = Instant::now();
                        let lifted = self.lift(ctx, fb, ops, &model, point);
                        lift_ns = lift_ns.saturating_add(
                            lift_started.elapsed().as_nanos().min(u64::MAX as u128) as u64,
                        );
                        if let Some(indices) = lifted {
                            answer = Some(indices);
                            break;
                        }
                        counters.lift_failures += 1;
                        if attempt + 1 == self.model_cap || solver.conflicts() >= self.conflict_cap
                        {
                            exceeded = true;
                            break;
                        }
                        let blocked: Vec<Lit> = (1..=self.words as u32 * self.instance.n)
                            .map(|v| {
                                if model[(v - 1) as usize] {
                                    -(v as Lit)
                                } else {
                                    v as Lit
                                }
                            })
                            .collect();
                        solver.reset_search();
                        solver.add_clause(blocked.clone());
                        clauses.push(blocked);
                    }
                }
            }
        }
        let stats = solver.stats;
        let mut extra = BTreeMap::new();
        for (key, value) in [
            ("decisions", stats.decisions),
            ("conflicts", stats.conflicts),
            ("restarts", stats.restarts),
            ("propagations", stats.propagations),
            ("xor_passes", stats.xor_passes),
            ("xor_propagations", stats.xor_propagations),
            ("xor_conflicts", stats.xor_conflicts),
            ("xor_repivots", stats.xor_repivots),
            ("learnt_clauses", stats.learnt_clauses),
            ("xor_row_ops", stats.xor_row_ops),
            ("xor_row_scans", stats.xor_row_scans),
            ("xor_reason_lits", stats.xor_reason_lits),
            ("clause_visits", stats.clause_visits),
            ("clause_lit_visits", stats.clause_lit_visits),
            ("analyze_lit_visits", stats.analyze_lit_visits),
            ("learnt_lits_raw", stats.learnt_lits_raw),
            ("learnt_lits_kept", stats.learnt_lits_kept),
            ("ns_propagate_clauses", stats.ns_propagate_clauses),
            ("ns_propagate_xors", stats.ns_propagate_xors),
            ("ns_analyze", stats.ns_analyze),
            ("ns_minimize", stats.ns_minimize),
            ("ns_reduce_db", stats.ns_reduce_db),
            ("conflict_level_sum", stats.conflict_level_sum),
            ("max_level", stats.max_level),
        ] {
            extra.insert(key.into(), value);
        }
        let cost = SolverCost {
            ops: stats.conflicts,
            op_unit: "conflicts".into(),
            wall_ns: (started.elapsed().as_nanos().min(u64::MAX as u128) as u64)
                .saturating_sub(lift_ns),
            timed_out: exceeded,
            extra,
            ..Default::default()
        };
        self.totals.absorb(&self.shape, Some(&cost), exceeded);
        if exceeded {
            self.count("chain_unknown", 1);
        }
        if answer.is_some() {
            self.count("chain_verified_relations", 1);
        }
        answer
    }
    fn last_system(&self) -> Option<SystemShape> {
        self.prepared.then(|| self.shape.clone())
    }
    fn solver_totals(&self) -> Option<SolverTotals> {
        Some(self.totals.clone())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::cryptanalysis::ic_boundary::{binary_subspace_factor_base, random_binary_instance};

    fn context<'a, 'b>(
        inst: &'a BinaryInstance,
        group: &'b BinaryGroup<'a>,
    ) -> InstanceCtx<'b, BinaryGroup<'a>> {
        InstanceCtx {
            group,
            generator: inst.generator,
            target: inst.generator,
            r: inst.r,
            cofactor: inst.cofactor,
            group_order: inst.group_order,
            name: "chain-test".into(),
            field_degree: Some(inst.n),
        }
    }

    #[test]
    fn two_and_three_agree_with_exhaustive_finite_chart() {
        let inst = random_binary_instance(5, 1, 64).unwrap();
        let group = BinaryGroup(&inst.fast);
        let ctx = context(&inst, &group);
        let fb = binary_subspace_factor_base(&inst, &[1, 2]);
        assert!(!fb.points.is_empty());
        for m in [2, 3] {
            for topology in ["serial", "balanced"] {
                let mut oracle = ChainSatOracle::new(m, &inst);
                let mut params = Params::default();
                params
                    .set("topology", topology)
                    .set("conflicts", "100000")
                    .set("models", "10000");
                let mut ops = GroupOps::default();
                oracle.prepare(&ctx, &fb, &params, &mut ops).unwrap();
                let mut targets = Vec::new();
                for &a in &fb.points {
                    for &b in &fb.points {
                        if m == 2 {
                            let sum = group.add(&mut ops, a, b);
                            if !sum.infinity {
                                targets.push(sum);
                            }
                        } else {
                            for &c in &fb.points {
                                let internal = if topology == "serial" {
                                    group.add(&mut ops, a, b)
                                } else {
                                    group.add(&mut ops, b, c)
                                };
                                if internal.infinity {
                                    continue;
                                }
                                let sum = if topology == "serial" {
                                    group.add(&mut ops, internal, c)
                                } else {
                                    group.add(&mut ops, a, internal)
                                };
                                if !sum.infinity {
                                    targets.push(sum);
                                }
                            }
                        }
                    }
                }
                targets.sort_by_key(|p| (p.x, p.y));
                targets.dedup();
                for target in (0..1u64 << inst.n).flat_map(|x| inst.points_with_x(x)) {
                    let row = oracle.decompose(
                        &ctx,
                        &fb,
                        &mut ops,
                        &mut OracleCounters::default(),
                        target,
                    );
                    assert_eq!(
                        row.is_some(),
                        targets.contains(&target),
                        "m={m} topology={topology} target={target:?}"
                    );
                    if let Some(row) = row {
                        assert_eq!(row.len(), m as usize);
                        let sum = row.iter().fold(group.identity(), |p, &i| {
                            group.add(&mut ops, p, fb.points[i])
                        });
                        assert_eq!(sum, target);
                    }
                }
                assert_eq!(oracle.totals.budget_exceeded, 0);
            }
        }
    }

    #[test]
    fn thirty_one_has_no_global_mask_limit() {
        let inst = random_binary_instance(5, 1, 64).unwrap();
        let group = BinaryGroup(&inst.fast);
        let ctx = context(&inst, &group);
        let mut fb = FactorBase::empty("one abscissa, both signs".into());
        fb.points = vec![inst.generator, group.neg(inst.generator)];
        fb.neg_index = vec![1, 0];
        fb.x_index.insert(inst.generator.x, vec![0, 1]);
        for topology in ["serial", "balanced"] {
            let mut oracle = ChainSatOracle::new(31, &inst);
            let mut params = Params::default();
            params
                .set("topology", topology)
                .set("conflicts", "100000")
                .set("models", "100");
            let mut ops = GroupOps::default();
            oracle.prepare(&ctx, &fb, &params, &mut ops).unwrap();
            assert!(oracle.shape.n_vars > 64);
            // Thirty-one signed copies can sum to one copy. The finite tree
            // witness, not an exponential sign enumerator, supplies the signs.
            let row = oracle
                .decompose(
                    &ctx,
                    &fb,
                    &mut ops,
                    &mut OracleCounters::default(),
                    inst.generator,
                )
                .unwrap();
            assert_eq!(row.len(), 31);
            assert_eq!(
                row.iter().fold(group.identity(), |p, &i| group.add(
                    &mut ops,
                    p,
                    fb.points[i]
                )),
                inst.generator
            );
            assert_eq!(oracle.native.get("chain_invalid_sat_models"), None);
        }
    }

    #[test]
    fn guards_and_zero_budget_are_not_refutations() {
        let inst = random_binary_instance(5, 1, 64).unwrap();
        let group = BinaryGroup(&inst.fast);
        let ctx = context(&inst, &group);
        let fb = binary_subspace_factor_base(&inst, &[1, 2]);
        let mut ops = GroupOps::default();
        for m in [0, 1, 32] {
            assert!(ChainSatOracle::new(m, &inst)
                .prepare(&ctx, &fb, &Params::default(), &mut ops)
                .is_err());
        }
        let mut oracle = ChainSatOracle::new(2, &inst);
        let mut params = Params::default();
        params.set("conflicts", "0");
        oracle.prepare(&ctx, &fb, &params, &mut ops).unwrap();
        assert!(oracle
            .decompose(
                &ctx,
                &fb,
                &mut ops,
                &mut OracleCounters::default(),
                inst.generator
            )
            .is_none());
        assert_eq!(oracle.totals.budget_exceeded, 1);
        assert_eq!(oracle.native.get("chain_chart_unsat"), None);
        let mut mismatch = context(&inst, &group);
        mismatch.field_degree = Some(22);
        assert!(oracle.prepare(&mismatch, &fb, &params, &mut ops).is_err());
    }
}
