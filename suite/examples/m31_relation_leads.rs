//! Native experiments for target witnesses, partial relations and base selection.
//! This uses the existing target-curve arithmetic and decomposition code.
mod m31_relation_encodings;
use prime_field_auxiliary_ic::{Backend, Curve, FactorBase, Point};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::time::{Duration, Instant};

const P: u64 = 2147483647;
const N: u64 = 2147505293;
const TARGETS: [(u64, u64); 2] = [(2144058214, 807222724), (1764015007, 688050509)];
const SAMPLER: [u64; 2] = [13278325787951376526, 7996699001791978753];
const BASE_SEEDS: [u64; 2] = [13493305759439970643, 12458066285612794378];
fn plus(a: u64, b: u64, p: u64) -> u64 {
    (a + b) % p
}
fn minus(a: u64, b: u64, p: u64) -> u64 {
    (a + p - b % p) % p
}
fn times(a: u64, b: u64, p: u64) -> u64 {
    (a as u128 * b as u128 % p as u128) as u64
}
fn power(mut a: u64, mut n: u64, p: u64) -> u64 {
    let mut v = 1;
    while n > 0 {
        if n & 1 != 0 {
            v = times(v, a, p);
        }
        a = times(a, a, p);
        n >>= 1;
    }
    v
}
fn inv(a: u64, p: u64) -> u64 {
    assert_ne!(a, 0);
    power(a, p - 2, p)
}
fn coords(p: Option<Point>) -> Value {
    p.map_or(Value::Null, |q| json!([q.x(), q.y()]))
}
fn interval<const B: u32>(c: Curve<B>, k: usize) -> Vec<Point> {
    let mut v = Vec::new();
    for x in 0..c.modulus() {
        if let Some(p) = c.lift_x(x).unwrap() {
            v.push(p);
            if v.len() == k {
                break;
            }
        }
    }
    assert_eq!(v.len(), k);
    v
}
fn sum<const B: u32>(c: Curve<B>, v: &[Point]) -> Option<Point> {
    v.iter().fold(None, |a, p| c.add(a, Some(*p)).unwrap())
}
fn signed<const B: u32>(c: Curve<B>, p: Point, s: i32) -> Point {
    if s < 0 {
        c.negate(p).unwrap()
    } else {
        p
    }
}
fn splitmix(s: &mut u64) -> u64 {
    *s = s.wrapping_add(0x9e3779b97f4a7c15);
    let mut z = *s;
    z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
    z ^ (z >> 31)
}
fn sample(s: &mut u64, n: u64) -> u64 {
    let cut = n.wrapping_neg() % n;
    loop {
        let x = splitmix(s);
        if x >= cut {
            return x % n;
        }
    }
}

fn panel() {
    let c = Curve::<31>::new(2, 14).unwrap();
    let mut cases = Vec::new();
    for k in [2, 4] {
        let base = interval(c, k);
        for m in [3, 4] {
            let leaves: Vec<Point> = (0..m).map(|i| base[i % k]).collect();
            let planted = sum(c, &leaves).expect("finite planted target");
            for (label, q) in [
                ("planted", planted),
                ("ordinary0", c.point(TARGETS[0].0, TARGETS[0].1).unwrap()),
                ("ordinary1", c.point(TARGETS[1].0, TARGETS[1].1).unwrap()),
            ] {
                cases.push(json!({"id":format!("k{k}-m{m}-{label}"),"p":P,"a":2,"b":14,"m":m,"base":base.iter().map(|p|[p.x(),p.y()]).collect::<Vec<_>>(),"target":[q.x(),q.y()],"kind":label}));
            }
        }
    }
    println!(
        "{}",
        json!({"schema":"m31-public-encoding-panel/v1","cases":cases})
    );
}

// Fp(i), i^2=-1. For M31, -1 is a nonsquare. Only this control uses Fp2.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct E(u64, u64);
impl E {
    fn add(self, o: Self) -> Self {
        Self(plus(self.0, o.0, P), plus(self.1, o.1, P))
    }
    fn neg(self) -> Self {
        Self(minus(0, self.0, P), minus(0, self.1, P))
    }
    fn sub(self, o: Self) -> Self {
        self.add(o.neg())
    }
    fn mul(self, o: Self) -> Self {
        Self(
            minus(times(self.0, o.0, P), times(self.1, o.1, P), P),
            plus(times(self.0, o.1, P), times(self.1, o.0, P), P),
        )
    }
    fn inverse(self) -> Self {
        let d = inv(
            plus(times(self.0, self.0, P), times(self.1, self.1, P), P),
            P,
        );
        Self(times(self.0, d, P), minus(0, times(self.1, d, P), P))
    }
    fn sq(self) -> Self {
        self.mul(self)
    }
}
type EP = Option<(E, E)>;
fn eneg(q: EP) -> EP {
    q.map(|(x, y)| (x, y.neg()))
}
fn eadd(q: EP, r: EP) -> EP {
    let (x, y) = match q {
        None => return r,
        Some(q) => q,
    };
    let (u, v) = match r {
        None => return q,
        Some(r) => r,
    };
    if x == u && y == v.neg() {
        return None;
    }
    let slope = if x == u {
        E(3, 0)
            .mul(x.sq())
            .add(E(2, 0))
            .mul(E(2, 0).mul(y).inverse())
    } else {
        v.sub(y).mul(u.sub(x).inverse())
    };
    let z = slope.sq().sub(x).sub(u);
    Some((z, slope.mul(x.sub(z)).sub(y)))
}
fn ej(q: EP) -> Value {
    q.map_or(Value::Null, |(x, y)| json!({"x":[x.0,x.1],"y":[y.0,y.1]}))
}
fn salvage(lifts: &[EP], r: EP) -> Value {
    let c = Curve::<31>::new(2, 14).unwrap();
    let (rx, ry) = r.expect("finite rational target");
    assert_eq!(rx.1, 0);
    assert_eq!(ry.1, 0);
    let rational_r = c.point(rx.0, ry.0).unwrap();
    let mut a = None;
    let mut t = None;
    let mut rational_terms = Vec::new();
    let mut roots = Vec::new();
    for lift in lifts {
        let (x, y) = lift.expect("affine input root lift");
        assert_eq!(x.1, 0);
        assert!(x.0 < P && y.0 < P && y.1 < P);
        assert_eq!(y.sq(), x.sq().mul(x).add(E(2, 0).mul(x)).add(E(14, 0)));
        roots.push(x.0);
        if y.1 == 0 {
            let point = c.point(x.0, y.0).unwrap();
            a = c.add(a, Some(point)).unwrap();
            rational_terms.push(point);
        } else {
            assert_eq!(y.0, 0);
            let conjugate = Some((E(x.0, minus(0, x.1, P)), E(y.0, minus(0, y.1, P))));
            assert_eq!(conjugate, eneg(*lift));
            t = eadd(t, *lift);
        }
    }
    assert_eq!(lifts.iter().fold(None, |sum, lift| eadd(sum, *lift)), r);
    roots.push(rx.0);
    let summation_zero =
        m31_relation_encodings::numeric_summation_root(P, 2, 14, &roots, Duration::from_secs(5))
            .unwrap();
    assert!(summation_zero);
    assert_eq!(eadd(t, t), None);
    let projected_target = c.mul(Some(rational_r), 2).unwrap();
    let projected_terms: Vec<Point> = rational_terms
        .iter()
        .map(|q| {
            c.mul(Some(*q), 2)
                .unwrap()
                .expect("odd order nonzero point")
        })
        .collect();
    assert_eq!(projected_target, sum(c, &projected_terms));
    assert_eq!(projected_target, c.mul(a, 2).unwrap());
    assert!(projected_terms
        .iter()
        .all(|q| c.mul(Some(*q), N).unwrap().is_none()));
    json!({"summation_polynomial":"S5","numeric_summation_polynomial_zero":summation_zero,"input_affine_terms":lifts.len(),"rational_terms_retained":rational_terms.len(),"nonrational_terms_removed":lifts.len()-rational_terms.len(),"T":ej(t),"two_T_is_O":true,"projection_multiplier":2,"cofactor":1,"projected_target":coords(projected_target),"projected_terms":projected_terms.iter().map(|p|[p.x(),p.y()]).collect::<Vec<_>>(),"projected_relation_replayed":true,"odd_subgroup_membership_replayed":true,"scope":"signed root lifts supplied; this procedure does not solve the bare-root sign problem"})
}
fn extension_control() -> Value {
    assert_eq!(power(P - 1, (P - 1) / 2, P), P - 1);
    let c = Curve::<31>::new(2, 14).unwrap();
    let mut twists = Vec::new();
    for x in 0..100 {
        if c.lift_x(x).unwrap().is_none() {
            let rhs = plus(plus(times(times(x, x, P), x, P), times(2, x, P), P), 14, P);
            let z = power(minus(0, rhs, P), (P + 1) / 4, P);
            assert_eq!(minus(0, times(z, z, P), P), rhs);
            twists.push(Some((E(x, 0), E(0, z))));
        }
    }
    let t1 = twists[0];
    let t2 = *twists
        .iter()
        .skip(1)
        .find(|t| {
            let r = eadd(t1, **t);
            r.is_some() && r.unwrap().0 != t1.unwrap().0 && r.unwrap().0 != t.unwrap().0
        })
        .unwrap();
    let t3 = eneg(eadd(t1, t2));
    let rational = interval(c, 1)[0];
    let a = Some((E(rational.x(), 0), E(rational.y(), 0)));
    let t = eadd(eadd(t1, t2), t3);
    assert!(t.is_none());
    for q in [t1, t2, t3] {
        let (x, y) = q.unwrap();
        assert_eq!(x.1, 0);
        assert_eq!(y.0, 0);
        assert_ne!(y.1, 0);
        assert_eq!(y.sq(), x.sq().mul(x).add(E(2, 0).mul(x)).add(E(14, 0)));
    }
    let r = eadd(eadd(eadd(a, t1), t2), t3);
    assert_eq!(r, a);
    assert_eq!(eadd(t, t), None);
    assert_eq!(eadd(r, r), eadd(a, a));
    let odd = c.mul(Some(rational), N).unwrap().is_none();
    assert!(odd);
    let recovered = salvage(&[a, t1, t2, t3], r);
    json!({"control":"nonrational_lift_salvage","p":P,"extension":"i^2=-1","rational_terms":1,"nonrational_terms":3,"raw_root_x":[rational.x(),t1.unwrap().0.0,t2.unwrap().0.0,t3.unwrap().0.0],"target":ej(r),"lifts":[ej(a),ej(t1),ej(t2),ej(t3)],"salvage":recovered,"T":ej(t),"two_T_is_O":true,"two_R_eq_two_A":true,"cofactor":1,"two_h_projection_replayed":odd,"qualification":"constructed signed-decomposition control; not a relation-yield estimate"})
}

#[derive(Clone)]
struct Tree {
    point: Option<Point>,
    leaf: Option<usize>,
    left: Option<Box<Tree>>,
    right: Option<Box<Tree>>,
}
fn tree(c: Curve<31>, leaves: &[Point], offset: usize) -> Tree {
    if leaves.len() == 1 {
        return Tree {
            point: Some(leaves[0]),
            leaf: Some(offset),
            left: None,
            right: None,
        };
    }
    let n = leaves.len() / 2;
    let a = tree(c, &leaves[..n], offset);
    let b = tree(c, &leaves[n..], offset + n);
    let p = c.add(a.point, b.point).unwrap();
    Tree {
        point: p,
        leaf: None,
        left: Some(Box::new(a)),
        right: Some(Box::new(b)),
    }
}
fn orient(c: Curve<31>, t: &Tree, want: Option<Point>, out: &mut Vec<(usize, i32)>, ops: &mut u64) {
    if let Some(i) = t.leaf {
        let p = c.lift_x(t.point.unwrap().x()).unwrap().unwrap();
        out.push((
            i,
            if Some(p) == want {
                1
            } else {
                assert_eq!(Some(c.negate(p).unwrap()), want);
                -1
            },
        ));
        return;
    }
    let l = t.left.as_ref().unwrap();
    let r = t.right.as_ref().unwrap();
    // Witness stores the actual rational intermediate abscissa (or infinity),
    // not its sign. Canonicalise each child before reconstructing orientations.
    let canonical = |p: Option<Point>| p.map(|q| c.lift_x(q.x()).unwrap().unwrap());
    for sl in [1, -1] {
        for sr in [1, -1] {
            let lp = canonical(l.point).map(|q| signed(c, q, sl));
            let rp = canonical(r.point).map(|q| signed(c, q, sr));
            *ops += 1;
            if c.add(lp, rp).unwrap() == want {
                orient(c, l, lp, out, ops);
                orient(c, r, rp, out, ops);
                return;
            }
        }
    }
    panic!("unrecoverable rational tree witness");
}
fn bare_signs(c: Curve<31>, xs: &[u64], target: Point) -> (Vec<Point>, u64, u64) {
    let mut patterns = 0;
    let mut ops = 0;
    for bits in 0..1u64 << xs.len() {
        patterns += 1;
        let mut points = Vec::new();
        let mut acc = None;
        for (i, x) in xs.iter().enumerate() {
            let p = signed(
                c,
                c.lift_x(*x).unwrap().unwrap(),
                if bits >> i & 1 == 1 { -1 } else { 1 },
            );
            points.push(p);
            acc = c.add(acc, Some(p)).unwrap();
            ops += 1;
        }
        if acc == Some(target) {
            return (points, patterns, ops);
        }
    }
    panic!("constructed root has no signed lift");
}
fn target_controls() -> Value {
    let c = Curve::<31>::new(2, 14).unwrap();
    let base = interval(c, 8);
    let mut records = Vec::new();
    for m in [2usize, 3, 4, 8] {
        let leaves: Vec<Point> = (0..m)
            .map(|i| signed(c, base[i], if i % 3 == 0 { -1 } else { 1 }))
            .collect();
        let witness = tree(c, &leaves, 0);
        let q = witness.point.expect("finite target");
        let mut recovered = Vec::new();
        let mut ops = 0;
        orient(c, &witness, Some(q), &mut recovered, &mut ops);
        let rs: Vec<Point> = recovered
            .iter()
            .map(|(i, s)| signed(c, c.lift_x(leaves[*i].x()).unwrap().unwrap(), *s))
            .collect();
        assert_eq!(sum(c, &rs), Some(q));
        assert!(ops <= 4 * (m as u64 - 1));
        let xs: Vec<u64> = leaves.iter().map(|p| p.x()).collect();
        let (_, patterns, brute_ops) = bare_signs(c, &xs, q);
        let nq = c.negate(q).unwrap();
        assert_eq!(q.x(), nq.x());
        let mut cache = BTreeMap::new();
        let mut solves = 0;
        let mut hits = 0;
        let mut cache_search_ops = 0;
        for target in [q, nq] {
            let key = (m, target.x());
            if cache.contains_key(&key) {
                hits += 1;
            } else {
                solves += 1;
                let (points, _, cost) = bare_signs(c, &xs, target);
                cache_search_ops += cost;
                cache.insert(key, points);
            }
            let cached = &cache[&key];
            let got = sum(c, cached);
            let oriented = if got == Some(target) {
                cached.clone()
            } else {
                cached.iter().map(|p| c.negate(*p).unwrap()).collect()
            };
            assert_eq!(sum(c, &oriented), Some(target));
        }
        records.push(json!({"m":m,"tree_group_additions":ops,"bare_root_sign_patterns":patterns,"bare_root_group_additions":brute_ops,"tree_signed_relation_replayed":true,"x_cache_requests":2,"x_cache_solves":solves,"x_cache_hits":hits,"cache_actual_search_group_additions":cache_search_ops,"negative_target_replayed":true}));
    }
    json!({"mode":"target_controls","p":P,"extension_control":extension_control(),"rational_tree_and_cache":records})
}

// Eliminate outside-point coefficients over the scalar field. Every row
// carries its original-row weights; graph topology alone is never used.
#[derive(Clone)]
struct Row {
    h: Vec<u64>,
    weights: Vec<u64>,
}
struct Elim {
    p: u64,
    pivots: Vec<Option<Row>>,
    inputs: Vec<Vec<u64>>,
}
impl Elim {
    fn new(columns: usize, p: u64) -> Self {
        Self {
            p,
            pivots: vec![None; columns],
            inputs: Vec::new(),
        }
    }
    fn insert(&mut self, h: Vec<u64>) -> Option<Vec<u64>> {
        let idx = self.inputs.len();
        self.inputs.push(h.clone());
        let mut row = Row {
            h,
            weights: vec![0; idx + 1],
        };
        row.weights[idx] = 1;
        for j in 0..row.h.len() {
            if row.h[j] == 0 {
                continue;
            }
            if let Some(pivot) = &self.pivots[j] {
                let a = row.h[j];
                for k in j..row.h.len() {
                    row.h[k] = minus(row.h[k], times(a, pivot.h[k], self.p), self.p);
                }
                for (k, w) in pivot.weights.iter().enumerate() {
                    row.weights[k] = minus(row.weights[k], times(a, *w, self.p), self.p);
                }
            } else {
                let a = inv(row.h[j], self.p);
                for x in &mut row.h {
                    *x = times(*x, a, self.p);
                }
                for x in &mut row.weights {
                    *x = times(*x, a, self.p);
                }
                self.pivots[j] = Some(row);
                return None;
            }
        }
        for j in 0..self.pivots.len() {
            assert_eq!(
                self.inputs
                    .iter()
                    .zip(&row.weights)
                    .fold(0, |a, (h, w)| plus(a, times(h[j], *w, self.p), self.p)),
                0
            );
        }
        Some(row.weights)
    }
    fn rank(&self) -> usize {
        self.pivots.iter().filter(|p| p.is_some()).count()
    }
}
fn cancellation_controls() -> Value {
    let mut bad = Elim::new(3, 101);
    for h in [vec![1, 1, 0], vec![0, 1, 1], vec![1, 0, 1]] {
        assert!(bad.insert(h).is_none());
    }
    assert_eq!(bad.rank(), 3);
    let c = Curve::<31>::new(2, 14).unwrap();
    let points = interval(c, 20);
    assert!(points.iter().all(|p| c.mul(Some(*p), N).unwrap().is_none()));
    let outside = &points[4..];
    let mut e = Elim::new(outside.len(), N);
    let mut targets = Vec::new();
    let mut fs = Vec::new();
    let mut certificates = Vec::new();
    for i in 0..64 {
        let mut h = vec![0; outside.len()];
        let j = i % outside.len();
        let k = (i * 7 + 3) % outside.len();
        h[j] = plus(h[j], 1, N);
        h[k] = minus(h[k], 1, N);
        let f = points[(i / outside.len()) % 4];
        let mut q = Some(f);
        for (p, a) in outside.iter().zip(&h) {
            q = c.add(q, c.mul(Some(*p), *a).unwrap()).unwrap();
        }
        targets.push(q);
        fs.push(f);
        if let Some(w) = e.insert(h) {
            let mut lhs = None;
            let mut rhs = None;
            for ((q, p), a) in targets.iter().zip(&fs).zip(&w) {
                lhs = c.add(lhs, c.mul(*q, *a).unwrap()).unwrap();
                rhs = c.add(rhs, c.mul(Some(*p), *a).unwrap()).unwrap();
            }
            assert_eq!(lhs, rhs);
            certificates.push(json!({"weights":w,"combined_target":coords(lhs),"final_base_sum":coords(rhs),"nonidentity_combined_target":lhs.is_some(),"outside_zero":true,"native_group_replay":true}));
        }
    }
    let nontrivial = certificates
        .iter()
        .filter(|v| v["nonidentity_combined_target"] == true)
        .count();
    assert!(nontrivial > 0);
    json!({"mode":"signed_cancellation_controls","p":P,"scalar_modulus":N,"ordinary_triangle_rank_mod101":bad.rank(),"ordinary_triangle_dependency":false,"synthetic_partial_rows":64,"outside_columns":outside.len(),"outside_rank":e.rank(),"outside_dependencies":certificates.len(),"nonidentity_combined_targets":nontrivial,"certificates":certificates,"qualification":"synthetic cancellation controls; no accepted-partial generation rate or independent relation yield inferred"})
}

fn base(arm: &str, rep: usize) -> FactorBase<31> {
    let c = Curve::<31>::new(2, 14).unwrap();
    let g = c.point(1, 814455902).unwrap();
    let columns = FactorBase::torus(c, 7, None, Backend::Scalar)
        .unwrap()
        .representatives()
        .len();
    match arm {
        "torus" => FactorBase::torus(c, 7, None, Backend::Scalar)
            .unwrap()
            .direct_control()
            .unwrap(),
        "interval" => {
            let points = interval(c, columns);
            FactorBase::without_maps(c, &points.iter().map(|p| p.x()).collect::<Vec<_>>()).unwrap()
        }
        "random" => {
            FactorBase::random_control(c, N, g, columns, BASE_SEEDS[rep], 100000)
                .unwrap()
                .0
        }
        _ => panic!("base arm"),
    }
}
fn collect(arm: &str, method: &str, rep: usize, m: u8, queries: u64, ms: u64) {
    let c = Curve::<31>::new(2, 14).unwrap();
    let g = c.point(1, 814455902).unwrap();
    let q = c.point(TARGETS[rep].0, TARGETS[rep].1).unwrap();
    let start = Instant::now();
    let ambient = base(arm, rep);
    assert!(ambient
        .representatives()
        .iter()
        .all(|p| c.mul(Some(*p), N).unwrap().is_none()));
    let split = ambient.representatives().len() * 3 / 4;
    let final_points = &ambient.representatives()[..split];
    let final_base =
        FactorBase::without_maps(c, &final_points.iter().map(|p| p.x()).collect::<Vec<_>>())
            .unwrap();
    let preparation_ns = start.elapsed().as_nanos();
    let b = if method == "full" {
        &final_base
    } else {
        &ambient
    };
    let mut scratch = b.workspace();
    let mut rng = SAMPLER[rep];
    let mut records = Vec::new();
    let mut e = Elim::new(ambient.representatives().len() - split, N);
    let mut accepted_rows = Vec::new();
    let mut accepted_query_indices = Vec::new();
    let mut combined = Vec::new();
    let mut distinct_final = BTreeSet::new();
    let mut final_elim = Elim::new(split + 2, N);
    let online = Instant::now();
    let deadline = Duration::from_millis(ms);
    let mut raw_hits = 0;
    let mut full_hits = 0;
    let mut outside_hist = [0u64; 5];
    for index in 0..queries {
        if online.elapsed() >= deadline {
            break;
        }
        let a = sample(&mut rng, N);
        let bb = sample(&mut rng, N);
        let target = c
            .add(c.mul(Some(g), a).unwrap(), c.mul(Some(q), bb).unwrap())
            .unwrap();
        let target = match target {
            None => {
                records.push(json!({"index":index,"a":a,"b":bb,"target":null,"identity_target":true,"query_ns":0,"relation":null}));
                continue;
            }
            Some(t) => t,
        };
        let t = Instant::now();
        let found = b.decompose_multi(m, target, &mut scratch).unwrap();
        let query_ns = t.elapsed().as_nanos();
        let mut row_json = Value::Null;
        if let Some(row) = found {
            raw_hits += 1;
            let terms = row.summands();
            let outside_count = terms.iter().filter(|t| t.index >= split).count();
            outside_hist[outside_count] += 1;
            let mut replay = None;
            for t in terms {
                replay = c
                    .add(
                        replay,
                        Some(signed(
                            c,
                            b.representatives()[t.index],
                            if t.negative { -1 } else { 1 },
                        )),
                    )
                    .unwrap();
            }
            assert_eq!(replay, Some(target));
            let mut h = vec![0; ambient.representatives().len() - split];
            if outside_count == 0 {
                full_hits += 1;
            }
            if method == "partial" && outside_count > 0 && outside_count <= 2 {
                for term in terms {
                    if term.index >= split {
                        let x = &mut h[term.index - split];
                        *x = if term.negative {
                            minus(*x, 1, N)
                        } else {
                            plus(*x, 1, N)
                        };
                    }
                }
                let term_vec: Vec<(usize, i32)> = terms
                    .iter()
                    .map(|t| (t.index, if t.negative { -1 } else { 1 }))
                    .collect();
                accepted_rows.push((a, bb, term_vec.clone()));
                accepted_query_indices.push(index);
                if let Some(w) = e.insert(h) {
                    let mut lhs = None;
                    let mut rhs = None;
                    let mut coefficient_a = 0;
                    let mut coefficient_b = 0;
                    let mut final_coefficients = vec![0; split];
                    let mut outside_acc = vec![0; ambient.representatives().len() - split];
                    for ((aa, bb, ts), weight) in accepted_rows.iter().zip(&w) {
                        coefficient_a = plus(coefficient_a, times(*aa, *weight, N), N);
                        coefficient_b = plus(coefficient_b, times(*bb, *weight, N), N);
                        for (j, s) in ts {
                            let coeff = if *s < 0 {
                                minus(0, *weight, N)
                            } else {
                                *weight
                            };
                            if *j < split {
                                final_coefficients[*j] = plus(final_coefficients[*j], coeff, N);
                                rhs = c
                                    .add(
                                        rhs,
                                        c.mul(Some(ambient.representatives()[*j]), coeff).unwrap(),
                                    )
                                    .unwrap();
                            } else {
                                outside_acc[*j - split] = plus(outside_acc[*j - split], coeff, N);
                            }
                        }
                    }
                    assert!(outside_acc.iter().all(|x| *x == 0));
                    lhs = c.add(lhs, c.mul(Some(g), coefficient_a).unwrap()).unwrap();
                    lhs = c.add(lhs, c.mul(Some(q), coefficient_b).unwrap()).unwrap();
                    assert_eq!(lhs, rhs);
                    let mut canonical = final_coefficients.clone();
                    canonical.push(minus(0, coefficient_a, N));
                    canonical.push(minus(0, coefficient_b, N));
                    let nonzero = canonical.iter().any(|x| *x != 0);
                    if let Some(pivot) = canonical.iter().find(|x| **x != 0).copied() {
                        let scale = inv(pivot, N);
                        for v in &mut canonical {
                            *v = times(*v, scale, N);
                        }
                    }
                    let distinct = nonzero && distinct_final.insert(canonical.clone());
                    let rank_before = final_elim.rank();
                    final_elim.insert(canonical.clone());
                    let rank_increased = final_elim.rank() > rank_before;
                    combined.push(json!({"weights":w,"a":coefficient_a,"b":coefficient_b,"final_coefficients":final_coefficients,"normalized_coefficient_row":canonical,"nonzero_coefficient_row":nonzero,"new_distinct_row":distinct,"coefficient_rank_increased":rank_increased,"outside_zero":true,"group_replay":true}));
                }
            }
            row_json = json!({"terms":terms.iter().map(|t|json!({"column":t.index,"sign":if t.negative{-1}else{1}})).collect::<Vec<_>>(),"outside_terms":outside_count,"native_replay":true});
        }
        records.push(json!({"index":index,"a":a,"b":bb,"target":[target.x(),target.y()],"query_ns":query_ns,"relation":row_json}));
    }
    let elapsed = online.elapsed().as_nanos();
    let count = records.len();
    let status = if count as u64 == queries {
        "complete"
    } else {
        "time_censored"
    };
    println!(
        "{}",
        json!({"mode":"partial_generation_and_base_selection","p":P,"scalar_modulus":N,"arm":arm,"method":method,"replicate":rep,"m":m,"sampler_seed":SAMPLER[rep],"factor_base_seed":if arm=="random"{json!(BASE_SEEDS[rep])}else{Value::Null},"ambient_columns":ambient.representatives().len(),"final_columns":split,"outside_columns":e.pivots.len(),"base_coordinates":ambient.representatives().iter().map(|p|[p.x(),p.y()]).collect::<Vec<_>>(),"preparation_ns":preparation_ns,"online_ns":elapsed,"status":status,"queries":count,"requested_queries":queries,"soft_budget_ms":ms,"raw_decompositions":raw_hits,"direct_final_relations":full_hits,"outside_term_histogram":outside_hist,"accepted_partial_rows":accepted_rows.len(),"accepted_query_indices":accepted_query_indices,"outside_rank":e.rank(),"outside_dependencies":combined.len(),"combined_final_relations":distinct_final.len(),"combined_coefficient_row_rank":final_elim.rank(),"combined_certificates":combined,"records":records,"accepted_partial_cost_ns":if accepted_rows.is_empty(){Value::Null}else{json!(elapsed as f64/accepted_rows.len() as f64)},"generation_qualification":"actual public coefficient walks; first-witness acceptance policy (rejecting >2 outside terms does not rule out another admissible witness); rejection and zero-yield outcomes retained; synthetic controls excluded; no uniformity assumption asserted"})
    );
}
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let command = args.get(1).map(String::as_str).unwrap_or("panel");
    match command {
        "panel" => panel(),
        "target" => println!("{}", target_controls()),
        "cancel" => println!("{}", cancellation_controls()),
        "collect" => {
            assert_eq!(args.len(), 8);
            collect(
                &args[2],
                &args[3],
                args[4].parse().unwrap(),
                args[5].parse().unwrap(),
                args[6].parse().unwrap(),
                args[7].parse().unwrap(),
            );
        }
        _ => panic!("panel | target | cancel | collect ARM METHOD REP M QUERIES MS"),
    }
}
