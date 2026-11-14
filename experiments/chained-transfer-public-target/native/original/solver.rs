// End-to-end N4 solve (IC) and the matched rho on E0(K).
#![allow(dead_code)]
use crate::common::*;
use crate::ghs::*;
use crate::ic::*;
use crate::pic;
use std::collections::{HashMap, HashSet};

#[derive(Clone)]
pub struct Params {
    pub nfb: usize,       // 0 = all rational points
    pub rows_mult: f64,   // rows used = rows_mult * columns + 30
    pub max_desc: usize,  // descent trial cap per class
    pub sge: bool,        // structured elimination of the relation matrix before Lanczos
    pub maxw: usize,      // widest merged row allowed in the elimination
    pub lp2: bool,        // double large primes (graph of large-prime pairs)
}

#[derive(Default, Clone)]
pub struct Report {
    pub ok: bool,
    pub fail: String,
    pub k_found: Option<u64>,
    pub phases: Vec<(String, Cnt, f64)>,
    pub stats: Vec<(String, f64)>,
}
impl Report {
    pub fn stat(&mut self, k: &str, v: f64) {
        self.stats.push((k.to_string(), v));
    }
}

fn pc<R>(cv: &pic::PlaneQuartic, f: impl FnOnce() -> R) -> R {
    let b = cv.counter();
    let r = f();
    let d = cv.counter().since(&b);
    bump_mul(d.mul);
    bump_inv(d.inv);
    bump_add(d.add);
    r
}

pub fn all_points(cv: &Curve, rng: &mut Rng) -> Vec<P3> {
    let f = &cv.f;
    let q = f.q;
    let mut seen: HashSet<u64> = HashSet::new();
    let mut out = Vec::new();
    for a in 0..q {
        for p in cv.line_points(&[a, 0, 1], &[0, 1, 0], rng) {
            if seen.insert(pack(&p)) {
                out.push(p);
            }
        }
    }
    for p in cv.line_points(&[1, 0, 0], &[0, 1, 0], rng) {
        if seen.insert(pack(&p)) {
            out.push(p);
        }
    }
    out
}

pub fn sample_points(cv: &Curve, n: usize, rng: &mut Rng) -> Vec<P3> {
    let q = cv.f.q;
    let mut seen: HashSet<u64> = HashSet::new();
    let mut out = Vec::new();
    while out.len() < n {
        let a = [rng.below(q), rng.below(q), rng.below(q)];
        let b = [rng.below(q), rng.below(q), rng.below(q)];
        if a == [0, 0, 0] || b == [0, 0, 0] {
            continue;
        }
        let a = pnorm(&cv.f, &a);
        let b = pnorm(&cv.f, &b);
        if a == b {
            continue;
        }
        for p in cv.line_points(&a, &b, rng) {
            if out.len() < n && seen.insert(pack(&p)) {
                out.push(p);
            }
        }
    }
    out
}

fn to_u32(p: &P3) -> [u32; 3] {
    [p[0] as u32, p[1] as u32, p[2] as u32]
}

pub fn ic_solve(inst: &Inst, prm: &Params, k_true: u64, seed: u64, verify_rel: bool) -> Report {
    let mut rep = Report::default();
    let q = inst.q;
    let ell = inst.ell;
    let mut rng = Rng::new(seed ^ 0xC0FFEE);
    let curve = Curve::new(q, &inst.f);
    let f = curve.f;
    let t_all = std::time::Instant::now();
    let mut mark = (snap(), std::time::Instant::now());
    macro_rules! phase {
        ($name:expr) => {{
            let now = snap();
            rep.phases.push(($name.to_string(), now.since(&mark.0), mark.1.elapsed().as_secs_f64()));
            mark = (now, std::time::Instant::now());
        }};
    }
    let target = inst.ec.mul(&inst.g, k_true as u128);

    // 1. factor base
    let mut fb = if prm.nfb == 0 || prm.nfb as u64 >= q + 1 {
        all_points(&curve, &mut rng)
    } else {
        sample_points(&curve, prm.nfb, &mut rng)
    };
    // base point P0 for the canonical Pic^0 arithmetic (first point that the library accepts)
    let mut cv = None;
    for i in 0..fb.len() {
        let c = pic::PlaneQuartic::new(q as u32, inst.f, to_u32(&fb[i]));
        if let Ok(c) = c {
            fb.swap(0, i);
            let sc = c.setup_cost();
            bump_mul(sc.mul);
            bump_inv(sc.inv);
            bump_add(sc.add);
            cv = Some(c);
            break;
        }
    }
    let cv = match cv {
        Some(c) => c,
        None => {
            rep.fail = "no base point".into();
            return rep;
        }
    };
    cv.reset_counter();
    let n = fb.len();
    rep.stat("n_fb", n as f64);
    phase!("fb");

    // 2. relations
    let mut ro2: Option<Rel2Out> = None;
    let ro = if prm.lp2 {
        let r2 = find_relations_2lp(&curve, &fb);
        let ro = RelOut {
            full: r2.full.iter().map(|c| Rel { c: c.clone(), lp: None }).collect(),
            lp: r2.ground.iter().filter(|g| !g.2).map(|(v, fp, _)| Rel { c: fp.clone(), lp: Some(*v) }).collect(),
            lp_pts: r2.vertex_pts.clone(),
            pairs: r2.pairs,
            multi_lines: r2.edges.len() as u64,
            unsure: r2.no_roots,
        };
        rep.stat("graph_edges", r2.edges.len() as f64);
        rep.stat("graph_ground", r2.ground.len() as f64);
        ro2 = Some(r2);
        ro
    } else {
        find_relations(&curve, &fb, &mut rng)
    };
    rep.stat("pairs", ro.pairs as f64);
    rep.stat("multi_lines", ro.multi_lines as f64);
    rep.stat("rel_full", ro.full.len() as f64);
    rep.stat("rel_lp", ro.lp.len() as f64);
    rep.stat("lp_distinct", ro.lp_pts.len() as f64);
    rep.stat("rel_unsure", ro.unsure as f64);
    phase!("relations");
    if verify_rel {
        // independent check through the canonical group law: every sampled relation sums to
        // the line-section class
        let mut kappa: Option<pic::PicClass> = None;
        let mut bad = 0;
        let mut tested = 0;
        let cls = |p: &P3| cv.point_class(to_u32(p));
        let mut allrels: Vec<(Vec<(u32, u8)>, Option<u32>)> = Vec::new();
        for r in ro.full.iter().take(10) {
            allrels.push((r.c.clone(), None));
        }
        for r in ro.lp.iter().take(30) {
            allrels.push((r.c.clone(), r.lp));
        }
        let mut edge_checks: Vec<(u32, u32, u32, u32)> = Vec::new();
        if let Some(r2) = &ro2 {
            edge_checks = r2.edges.iter().take(40).copied().collect();
        }
        for (c, lp) in allrels {
            let mut s = cv.zero();
            for (i, m) in c {
                let x = cls(&fb[i as usize]);
                for _ in 0..m {
                    s = cv.add(&s, &x);
                }
            }
            if let Some(l) = lp {
                s = cv.add(&s, &cls(&ro.lp_pts[l as usize]));
            }
            match &kappa {
                None => kappa = Some(s),
                Some(k0) => {
                    if *k0 != s {
                        bad += 1;
                    }
                }
            }
            tested += 1;
        }
        if let Some(r2) = &ro2 {
            for &(vx, vy, ia, ib) in &edge_checks {
                let mut sm = cv.zero();
                for pt in [&fb[ia as usize], &fb[ib as usize], &r2.vertex_pts[vx as usize], &r2.vertex_pts[vy as usize]] {
                    sm = cv.add(&sm, &cls(pt));
                }
                match &kappa {
                    None => kappa = Some(sm),
                    Some(k0) => {
                        if *k0 != sm {
                            bad += 1;
                        }
                    }
                }
                tested += 1;
            }
        }
        rep.stat("relations_verified", tested as f64);
        rep.stat("relations_bad", bad as f64);
        cv.reset_counter();
    }

    // 3. matrix: columns fb[1..] -> 0..n-2, eta -> n-1
    let ncols_all = n;
    let eta_col = (n - 1) as u32;
    let col = |i: u32| -> Option<u32> { if i == 0 { None } else { Some(i - 1) } };
    let to_mod = |v: i64| -> u64 { if v >= 0 { (v as u64) % ell } else { ell - ((-v) as u64 % ell) } };
    let mut full_rows: Vec<Row> = Vec::new();
    for r in &ro.full {
        let mut row: Row = Vec::new();
        for &(i, m) in &r.c {
            if let Some(c) = col(i) {
                row.push((c, m as u64));
            }
        }
        row.push((eta_col, ell - 1));
        full_rows.push(row);
    }
    let mut lp_groups: std::collections::BTreeMap<u32, Vec<usize>> = std::collections::BTreeMap::new();
    for (ri, r) in ro.lp.iter().enumerate() {
        lp_groups.entry(r.lp.unwrap()).or_default().push(ri);
    }
    let mut lp_rows: Vec<Row> = Vec::new();
    for (_l, rs) in &lp_groups {
        for w in 1..rs.len() {
            let mut m: HashMap<u32, i64> = HashMap::new();
            for &(i, mu) in &ro.lp[rs[w]].c {
                if let Some(c) = col(i) {
                    *m.entry(c).or_insert(0) += mu as i64;
                }
            }
            for &(i, mu) in &ro.lp[rs[0]].c {
                if let Some(c) = col(i) {
                    *m.entry(c).or_insert(0) -= mu as i64;
                }
            }
            let mut row: Row = m.into_iter().filter(|x| x.1 != 0).map(|(c, v)| (c, to_mod(v))).collect();
            if !row.is_empty() {
                row.sort();
                lp_rows.push(row);
            }
        }
    }
    if let Some(r2) = &ro2 {
        let target = (prm.rows_mult * ncols_all as f64).ceil() as usize * 3 + 100;
        let cr = cycle_rows_2lp(r2, ell, eta_col, target);
        rep.stat("rows_cycle", cr.len() as f64);
        lp_rows.extend(cr);
    }
    rep.stat("rows_full", full_rows.len() as f64);
    rep.stat("rows_lp_combined", lp_rows.len() as f64);
    if full_rows.is_empty() {
        rep.fail = "no full relation (eta unanchored)".into();
        return rep;
    }
    let (z, used, remap, hold_ok, hold_bad) = if prm.sge {
        // all rows go in; 60 random ones are held out
        let nf = full_rows.len();
        let mut all: Vec<Row> = full_rows;
        all.extend(lp_rows);
        for i in (1..all.len()).rev() {
            let j = rng.below(i as u64 + 1) as usize;
            all.swap(i, j);
        }
        let hold: Vec<Row> = all.drain(..all.len().min(60)).collect();
        rep.stat("rows_available", all.len() as f64);
        rep.stat("rows_full_total", nf as f64);
        let out = sge(all, ncols_all, eta_col, ell, prm.maxw);
        let nact = out.cols.len();
        rep.stat("sge_singles", out.singles as f64);
        rep.stat("sge_merges", out.merges as f64);
        rep.stat("sge_pruned", out.pruned as f64);
        rep.stat("sge_skipped_wide", out.skipped_wide as f64);
        rep.stat("cols_active", nact as f64);
        rep.stat("rows_used", out.core.len() as f64);
        rep.stat("core_nnz", out.core.iter().map(|r| r.len()).sum::<usize>() as f64);
        if out.core.len() < nact || nact == 0 {
            rep.fail = format!("too few relations after elimination: {} rows for {} columns", out.core.len(), nact);
            return rep;
        }
        phase!("matrix");
        let mut zc = None;
        for _ in 0..3 {
            if let Some(v) = lanczos_kernel(&out.core, nact, ell, &mut rng) {
                if out.core.iter().all(|r| row_apply(r, &v, ell) == 0) {
                    zc = Some(v);
                    break;
                }
            }
        }
        let zc = match zc {
            Some(z) => z,
            None => {
                rep.fail = "lanczos failed".into();
                return rep;
            }
        };
        let mut vals: Vec<Option<u64>> = vec![None; ncols_all];
        for (i, &c) in out.cols.iter().enumerate() {
            vals[c as usize] = Some(zc[i]);
        }
        back_substitute(&out, &mut vals, ell);
        let used: Vec<bool> = vals.iter().map(|v| v.is_some()).collect();
        let remap: Vec<u32> = (0..ncols_all).map(|c| if used[c] { c as u32 } else { u32::MAX }).collect();
        let z: Vec<u64> = vals.iter().map(|v| v.unwrap_or(0)).collect();
        let (mut ho, mut hb) = (0, 0);
        for r in &hold {
            if r.iter().all(|&(c, _)| used[c as usize]) {
                if row_apply(r, &z, ell) == 0 { ho += 1; } else { hb += 1; }
            }
        }
        (z, used, remap, ho, hb)
    } else {
    let want = (prm.rows_mult * ncols_all as f64).ceil() as usize + 30;
    let mut rows: Vec<Row> = Vec::new();
    let nf = full_rows.len();
    let mut rest: Vec<Row> = Vec::new();
    for (i, r) in full_rows.into_iter().enumerate() {
        if i < 3 {
            rows.push(r);
        } else {
            rest.push(r);
        }
    }
    rest.extend(lp_rows);
    // shuffle rest (double large primes: lightest rows first)
    for i in (1..rest.len()).rev() {
        let j = rng.below(i as u64 + 1) as usize;
        rest.swap(i, j);
    }

    let mut hold: Vec<Row> = Vec::new();
    for r in rest {
        if rows.len() < want {
            rows.push(r);
        } else if hold.len() < 60 {
            hold.push(r);
        }
    }
    // active columns
    let mut used = vec![false; ncols_all];
    for r in &rows {
        for &(c, _) in r {
            used[c as usize] = true;
        }
    }
    used[eta_col as usize] = true;
    let mut remap = vec![u32::MAX; ncols_all];
    let mut nact = 0usize;
    for c in 0..ncols_all {
        if used[c] {
            remap[c] = nact as u32;
            nact += 1;
        }
    }
    let rows_c: Vec<Row> = rows.iter().map(|r| r.iter().map(|&(c, a)| (remap[c as usize], a)).collect()).collect();
    rep.stat("rows_used", rows_c.len() as f64);
    rep.stat("cols_active", nact as f64);
    rep.stat("rows_full_total", nf as f64);
    if rows_c.len() < nact {
        rep.fail = format!("too few relations: {} rows for {} columns", rows_c.len(), nact);
        return rep;
    }
    phase!("matrix");

    // 4. linear algebra
    let mut z = None;
    for _ in 0..3 {
        if let Some(v) = lanczos_kernel(&rows_c, nact, ell, &mut rng) {
            // verify A z = 0
            if rows_c.iter().all(|r| row_apply(r, &v, ell) == 0) {
                z = Some(v);
                break;
            }
        }
    }
    let z = match z {
        Some(z) => z,
        None => {
            rep.fail = "lanczos failed".into();
            return rep;
        }
    };
    // hold-out relations (only those whose columns are all active)
    let mut hold_ok = 0;
    let mut hold_bad = 0;
    for r in &hold {
        if r.iter().all(|&(c, _)| remap[c as usize] != u32::MAX) {
            let rr: Row = r.iter().map(|&(c, a)| (remap[c as usize], a)).collect();
            if row_apply(&rr, &z, ell) == 0 {
                hold_ok += 1;
            } else {
                hold_bad += 1;
            }
        }
    }
        (z, used, remap, hold_ok, hold_bad)
    };
    rep.stat("holdout_ok", hold_ok as f64);
    rep.stat("holdout_bad", hold_bad as f64);
    phase!("linear_algebra");
    if hold_bad > 0 {
        rep.fail = "kernel not unique (hold-out relations violated)".into();
        return rep;
    }
    let eta = z[remap[eta_col as usize] as usize];
    if eta == 0 {
        rep.fail = "eta is zero in the kernel vector".into();
        return rep;
    }
    // logs of F points and large primes
    let mut logs: HashMap<u64, u64> = HashMap::new();
    let mut active_idx: Vec<u32> = Vec::new();
    logs.insert(pack(&fb[0]), 0);
    for i in 1..n {
        let c = (i - 1) as usize;
        if used[c] {
            logs.insert(pack(&fb[i]), z[remap[c] as usize]);
            active_idx.push(i as u32);
        }
    }
    let mut lp_known = 0usize;
    let mut seen_lp: HashSet<u32> = HashSet::new();
    for r in &ro.lp {
        let l = r.lp.unwrap();
        if !seen_lp.insert(l) {
            continue;
        }
        let mut s = 0u64;
        let mut okr = true;
        for &(i, mu) in &r.c {
            let key = pack(&fb[i as usize]);
            match logs.get(&key) {
                Some(&v) => s = la(s, lm(mu as u64, v, ell), ell),
                None => {
                    okr = false;
                    break;
                }
            }
        }
        if okr {
            logs.insert(pack(&ro.lp_pts[l as usize]), ls(eta, s, ell));
            lp_known += 1;
        }
    }
    if let Some(r2) = &ro2 {
        let lam = {
            let fbl = |i: u32| -> Option<u64> { logs.get(&pack(&fb[i as usize])).copied() };
            propagate_2lp(r2, &fbl, eta, ell)
        };
        let mut reached = 0;
        for (v, l) in lam.iter().enumerate() {
            if let Some(l) = l {
                logs.insert(pack(&r2.vertex_pts[v]), *l);
                reached += 1;
            }
        }
        lp_known = reached;
    }
    rep.stat("lp_known", lp_known as f64);
    rep.stat("known_points", logs.len() as f64);
    phase!("log_recovery");

    // 5. descent of the three transfer classes
    let mons2 = pic::mons_of_degree(2);
    let mut cls_cache: HashMap<u32, pic::PicClass> = HashMap::new();
    let mut total_trials = 0u64;
    let mut ys: Vec<u64> = Vec::new();
    // pick r0 with all of r0, r0+G, r0+Q valid transfers
    let mut rtries = 0;
    let mut picks: Vec<EP> = Vec::new();
    let mut desc_ok = true;
    'outer: loop {
        rtries += 1;
        if rtries > 400 {
            rep.fail = "no valid transfer triple".into();
            return rep;
        }
        let r = rng.below(ell - 1) + 1;
        let r0 = inst.ec.mul(&inst.g, r as u128);
        let r1 = inst.ec.add(&r0, &inst.g);
        let r2 = inst.ec.add(&r0, &target);
        let mut rows3 = Vec::new();
        for p in [r0, r1, r2] {
            match inst.transfer_cubics(&p) {
                Some(c) => rows3.push(c),
                None => continue 'outer,
            }
        }
        // descend each
        ys.clear();
        for rows in rows3 {
            let mut x = pc(&cv, || cv.reduce_deg6(&pic::Gen { k: 3, rows }));
            let mut added: Vec<u32> = Vec::new();
            let mut got = None;
            for _t in 0..prm.max_desc {
                total_trials += 1;
                if let pic::PicClass::Typ(m) = &x {
                    if let Some(pts) = split3(&f, m, &mons2, &mut rng) {
                        bump_hash(3);
                        let l: Vec<Option<u64>> = pts.iter().map(|p| logs.get(&pack(p)).copied()).collect();
                        if l.iter().all(|v| v.is_some()) {
                            let mut s = 0u64;
                            for v in l {
                                s = la(s, v.unwrap(), ell);
                            }
                            s = ls(s, eta, ell);
                            for &j in &added {
                                s = ls(s, logs[&pack(&fb[j as usize])], ell);
                            }
                            got = Some(s);
                            break;
                        }
                    }
                }
                let j = active_idx[rng.below(active_idx.len() as u64) as usize];
                let cj = cls_cache
                    .entry(j)
                    .or_insert_with(|| pc(&cv, || cv.point_class(to_u32(&fb[j as usize]))))
                    .clone();
                x = pc(&cv, || cv.add(&x, &cj));
                added.push(j);
            }
            match got {
                Some(v) => ys.push(v),
                None => {
                    desc_ok = false;
                    break 'outer;
                }
            }
        }
        break;
    }
    rep.stat("descent_trials", total_trials as f64);
    phase!("descent");
    if !desc_ok {
        rep.fail = "descent exhausted".into();
        return rep;
    }
    // 6. recover k and verify on E0
    let den = ls(ys[1], ys[0], ell);
    if den == 0 {
        rep.fail = "degenerate denominator".into();
        return rep;
    }
    let kk = lm(ls(ys[2], ys[0], ell), inv_mod_u64(den, ell), ell);
    let chk = inst.ec.mul(&inst.g, kk as u128);
    rep.k_found = Some(kk);
    rep.ok = chk == target;
    if !rep.ok {
        rep.fail = "recovered k does not satisfy kG = Q".into();
    }
    phase!("verify");
    rep.stat("wall_total", t_all.elapsed().as_secs_f64());
    rep
}

// ---------------------------------------------------------------- matched rho on E0(K)
pub struct RhoOut {
    pub ok: bool,
    pub steps: u64,
    pub dps: u64,
    pub cnt: Cnt,
    pub wall: f64,
}

pub fn rho(inst: &Inst, k_true: u64, seed: u64) -> RhoOut {
    // Plain Pollard rho: one trail, r-adding walk (R = 16 steps M_j = a_j G or b_j Q), distinguished
    // points stored by full point; a repeated DP closes the trail. No negation map.
    let ell = inst.ell;
    let ec = &inst.ec;
    let mut rng = Rng::new(seed ^ 0xABCDEF);
    let b0 = snap();
    let t0 = std::time::Instant::now();
    let target = ec.mul(&inst.g, k_true as u128);
    const R: usize = 16;
    let mut ma = [0u64; R];
    let mut mb = [0u64; R];
    let mut mp = [EP::Inf; R];
    for j in 0..R {
        if j % 2 == 0 {
            ma[j] = 1 + rng.below(ell - 1);
            mp[j] = ec.mul(&inst.g, ma[j] as u128);
        } else {
            mb[j] = 1 + rng.below(ell - 1);
            mp[j] = ec.mul(&target, mb[j] as u128);
        }
    }
    let dbits = {
        let s = (ell as f64).sqrt() / 64.0;
        (s.max(4.0).log2().floor() as u32).max(1)
    };
    let mask = (1u64 << dbits) - 1;
    let mut table: HashMap<[u64; 6], (u64, u64)> = HashMap::new();
    let mut steps = 0u64;
    let mut dps = 0u64;
    let maxlen = 20u64 << dbits;
    loop {
        let (mut a, mut b) = (rng.below(ell), rng.below(ell));
        let mut p = ec.add(&ec.mul(&inst.g, a as u128), &ec.mul(&target, b as u128));
        let mut since_dp = 0u64;
        loop {
            let (x, y) = match &p {
                EP::Inf => break,
                EP::A(x, y) => (*x, *y),
            };
            bump_cmp(1);
            let h = x[0].wrapping_mul(0x9E3779B97F4A7C15) ^ x[1].wrapping_mul(0xC2B2AE3D27D4EB4F) ^ x[2];
            if (h >> 20) & mask == 0 {
                dps += 1;
                bump_hash(1);
                let key = [x[0], x[1], x[2], y[0], y[1], y[2]];
                if let Some(&(a2, b2)) = table.get(&key) {
                    if b2 != b {
                        let num = ls(a, a2, ell);
                        let den = ls(b2, b, ell);
                        let k = lm(num, inv_mod_u64(den, ell), ell);
                        let ok = ec.mul(&inst.g, k as u128) == target;
                        return RhoOut { ok, steps, dps, cnt: snap().since(&b0), wall: t0.elapsed().as_secs_f64() };
                    }
                } else {
                    table.insert(key, (a, b));
                }
                since_dp = 0;
            }
            let j = (h as usize) % R;
            p = ec.add(&p, &mp[j]);
            a = la(a, ma[j], ell);
            b = la(b, mb[j], ell);
            steps += 1;
            since_dp += 1;
            if since_dp > maxlen {
                break; // trapped in a short cycle without a distinguished point: restart
            }
        }
        if steps > 60 * (ell as f64).sqrt() as u64 + 200000 {
            return RhoOut { ok: false, steps, dps, cnt: snap().since(&b0), wall: t0.elapsed().as_secs_f64() };
        }
    }
}
