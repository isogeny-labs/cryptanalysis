//! Candidate arm N2 of volcano-n19-native-loop-20261021: one process = one row, no Sage.
//!
//!   tau6dlp --arm N2|N2aa --serial K --point ID --scalar S --rng-seed STR --out FILE [--warm]
//!   tau6dlp --arm O2 --serial K --scalars S0,S1,.. --seed-format 'tau:tau6:%d' --out FILE
//!   tau6dlp --arm S0b --serial K --systems FILE --out FILE
//!
//! N2 / N2aa: setup = Setup::new() (field, curve, factor base, orbit representatives,
//! base table, solve context, generator), Q = scalar * P outside every interval, online =
//! tauDlp (tauEigen .. verified log), cold = setup + online, process CPU time
//! (clock_gettime CLOCK_PROCESS_CPUTIME_ID, the clock behind Python's time.process_time)
//! and wall (CLOCK_MONOTONIC), the same intervals as arm N. After the intervals: the field
//! check (256 products of the seeded check_field sample, recomputed by the verifier) and,
//! with --warm, the repeated-batch warm measurement (secondary).
//! O2: the ten archived scalars with the archived seeds (O1 for the candidate).
//! S0b: the compiled solve of this binary on every S0 system (compared with Sage's
//! varieties by the verifier).
//!
//! The record is written to --out and printed as raw_b64 with its SHA-256 (as arm.sage does).

use std::collections::BTreeMap;
use std::time::Instant;

use tau6loop::dlp::{Rel, Setup, MODULUS, P_ORD};
use tau6loop::json::{esc, list, num, rel_json, relation_digests};
use tau6loop::pyrand::PyRandom;
use tau6loop::util::{base64, hex, sha256};

#[repr(C)]
struct Timespec {
    tv_sec: i64,
    tv_nsec: i64,
}

extern "C" {
    fn clock_gettime(clk: i32, ts: *mut Timespec) -> i32;
    fn clock_getres(clk: i32, ts: *mut Timespec) -> i32;
    fn sched_getaffinity(pid: i32, size: usize, mask: *mut u8) -> i32;
    fn getpid() -> i32;
}

const CLOCK_PROCESS_CPUTIME_ID: i32 = 2;

fn cpu() -> f64 {
    let mut ts = Timespec { tv_sec: 0, tv_nsec: 0 };
    unsafe { clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &mut ts) };
    ts.tv_sec as f64 + ts.tv_nsec as f64 * 1e-9
}

fn cpu_res() -> f64 {
    let mut ts = Timespec { tv_sec: 0, tv_nsec: 0 };
    unsafe { clock_getres(CLOCK_PROCESS_CPUTIME_ID, &mut ts) };
    ts.tv_sec as f64 + ts.tv_nsec as f64 * 1e-9
}

fn affinity() -> Vec<usize> {
    let mut mask = [0u8; 128];
    let r = unsafe { sched_getaffinity(0, mask.len(), mask.as_mut_ptr()) };
    if r != 0 {
        return vec![];
    }
    (0..1024).filter(|i| mask[i / 8] >> (i % 8) & 1 == 1).collect()
}

/// Sage's str() of a GF(2^19) element: terms in descending degree, "z^k", "z", "1", " + ".
fn sage_str(v: u64) -> String {
    if v == 0 {
        return "0".into();
    }
    let mut t = vec![];
    for i in (0..64).rev() {
        if v >> i & 1 == 1 {
            t.push(match i {
                0 => "1".to_string(),
                1 => "z".to_string(),
                _ => format!("z^{}", i),
            });
        }
    }
    t.join(" + ")
}

struct Row(BTreeMap<String, String>);

impl Row {
    fn set(&mut self, k: &str, v: String) {
        self.0.insert(k.to_string(), v);
    }
    fn text(&self) -> String {
        let v: Vec<String> = self.0.iter().map(|(k, v)| format!("{}:{}", esc(k), v)).collect();
        format!("{{{}}}", v.join(","))
    }
}

fn opt(args: &[String], k: &str) -> Option<String> {
    args.iter().position(|a| a == k).and_then(|i| args.get(i + 1).cloned())
}

fn field_check(row: &mut Row) -> bool {
    // native_binding.check_field's sample: Random('native_binding.check_field'), 256 x
    // (randrange(2^19), randrange(2^19)); products in this binary's field arithmetic and in
    // the v3 solve's gf_mul. The verifier recomputes every product with an independent
    // shift-and-add multiplication modulo Sage's F.modulus() = 854355.
    let f = tau6loop::curve::Field::new(19, MODULUS);
    let mut rng = PyRandom::from_str_seed("native_binding.check_field");
    let mut prods = vec![];
    let mut disagree = 0;
    for _ in 0..256 {
        let a = rng.randrange(0, 1 << 19);
        let b = rng.randrange(0, 1 << 19);
        let c = f.mul(a, b);
        if c != tau6loop::v3::gf_mul(a, b, 19, MODULUS) {
            disagree += 1;
        }
        prods.push((a, b, c));
    }
    let ok = disagree == 0;
    row.set(
        "field_check",
        format!(
            "{{\"native_modulus\":{},\"expected_modulus\":854355,\"products_checked\":256,\
             \"loop_vs_solve_arithmetic_disagree\":{},\"products\":{},\"ok_native_side\":{}}}",
            MODULUS,
            disagree,
            list(&prods, |(a, b, c)| format!("[{},{},{}]", a, b, c)),
            ok
        ),
    );
    ok
}

fn exe_sha256() -> String {
    match std::fs::read("/proc/self/exe") {
        Ok(b) => esc(&hex(&sha256(&b))),
        Err(_) => "null".into(),
    }
}

fn ic_row(args: &[String], row: &mut Row) -> bool {
    let scalar: u64 = opt(args, "--scalar").expect("--scalar").parse().expect("scalar");
    let seed = opt(args, "--rng-seed").expect("--rng-seed");
    let warm = args.iter().any(|a| a == "--warm");
    let (c0, w0) = (cpu(), Instant::now());
    let s = Setup::new();
    let (setup_cpu, setup_wall) = (cpu() - c0, w0.elapsed().as_secs_f64());
    let q = s.f.mul_pt(scalar % P_ORD, s.p); // fixture, outside every interval
    let mut rels: Vec<Rel> = Vec::with_capacity(64);
    let (c1, w1) = (cpu(), Instant::now());
    let st = s.tau_dlp(q, &seed, &mut rels, None, &cpu);
    let (online_cpu, online_wall) = (cpu() - c1, w1.elapsed().as_secs_f64());
    let correct = st.recovered && st.log == Some(scalar % P_ORD);
    let (px, py) = s.p.unwrap();
    row.set("scalar", scalar.to_string());
    row.set("rng_seed", esc(&seed));
    row.set("warm", warm.to_string());
    row.set("targets", st.targets.to_string());
    row.set("gb_calls", st.gb_calls.to_string());
    row.set("spurious", st.spurious.to_string());
    row.set("relations", st.relations.to_string());
    row.set("log", st.log.map(|v| v.to_string()).unwrap_or_else(|| "null".into()));
    row.set("recovered", st.recovered.to_string());
    row.set("orbits", s.reps.len().to_string());
    row.set("v_points", s.v_points.to_string());
    row.set("gb_cpu_s", "null".into()); // not timed per call in N2 (see README: no per-call clock reads)
    row.set("relation_cpu_s", num(st.relation_cpu_s));
    row.set("linalg_cpu_s", num(st.linalg_cpu_s));
    row.set("setup_cpu_s", num(setup_cpu));
    row.set("setup_wall_s", num(setup_wall));
    row.set("online_cpu_s", num(online_cpu));
    row.set("online_wall_s", num(online_wall));
    row.set("cold_cpu_s", num(setup_cpu + online_cpu));
    row.set("cold_wall_s", num(setup_wall + online_wall));
    row.set("relations_digest", relation_digests(&rels, st.lambda, P_ORD));
    row.set("relations_raw", list(&rels, rel_json));
    row.set("P", format!("[{},{}]", esc(&sage_str(px)), esc(&sage_str(py))));
    row.set("P_int", format!("[{},{}]", px, py));
    row.set("reps", list(&s.reps, |&(x, y)| format!("[{},{}]", x, y)));
    row.set("lambda", st.lambda.to_string());
    let mut ok = correct;
    if warm {
        let mut su = vec![];
        let mut s2 = None;
        for _ in 0..20 {
            let c = cpu();
            let x = Setup::new();
            su.push(cpu() - c);
            s2 = Some(x);
        }
        let s2 = s2.unwrap();
        let q2 = s2.f.mul_pt(scalar % P_ORD, s2.p);
        let want = relation_digests(&rels, st.lambda, P_ORD);
        let mut on = vec![];
        let mut same = true;
        for _ in 0..3 {
            let mut r2 = vec![];
            let c = cpu();
            let t = s2.tau_dlp(q2, &seed, &mut r2, None, &cpu);
            on.push(cpu() - c);
            same = same && t.gb_calls == st.gb_calls && t.recovered && relation_digests(&r2, t.lambda, P_ORD) == want;
        }
        row.set(
            "warm_batch",
            format!(
                "{{\"label\":\"repeated-batch, warm (secondary)\",\"setup_reps\":20,\"setup_cpu_s_mean\":{},\
                 \"online_reps\":3,\"online_cpu_s_mean\":{},\"online_cpu_s\":{},\"same_relations\":{}}}",
                num(su.iter().sum::<f64>() / 20.0),
                num(on.iter().sum::<f64>() / 3.0),
                list(&on, |x| num(*x)),
                same
            ),
        );
    }
    ok = field_check(row) && ok;
    ok
}

fn o2_row(args: &[String], row: &mut Row) -> bool {
    let scalars: Vec<u64> =
        opt(args, "--scalars").expect("--scalars").split(',').map(|x| x.parse().expect("scalar")).collect();
    let fmt = opt(args, "--seed-format").expect("--seed-format");
    assert!(fmt.matches("%d").count() == 1);
    let s = Setup::new();
    let mut out = vec![];
    let mut all = true;
    for (ii, &sc) in scalars.iter().enumerate() {
        let seed = fmt.replace("%d", &ii.to_string());
        let q = s.f.mul_pt(sc % P_ORD, s.p);
        let mut rels = vec![];
        let st = s.tau_dlp(q, &seed, &mut rels, None, &cpu);
        let ok = st.recovered && st.log == Some(sc % P_ORD);
        all = all && ok;
        out.push(format!(
            "{{\"instance\":{},\"scalar\":{},\"rng_seed\":{},\"targets\":{},\"gb_calls\":{},\"spurious\":{},\
             \"relations\":{},\"log\":{},\"recovered\":{},\"relations_digest\":{},\"relations_raw\":{}}}",
            ii,
            sc,
            esc(&seed),
            st.targets,
            st.gb_calls,
            st.spurious,
            st.relations,
            st.log.map(|v| v.to_string()).unwrap_or_else(|| "null".into()),
            st.recovered,
            relation_digests(&rels, st.lambda, P_ORD),
            list(&rels, rel_json)
        ));
    }
    let (px, py) = s.p.unwrap();
    row.set("instances", format!("[{}]", out.join(",")));
    row.set("P", format!("[{},{}]", esc(&sage_str(px)), esc(&sage_str(py))));
    row.set("lambda", s.tau_eigen(s.p).to_string());
    field_check(row) && all
}

fn s0b_row(args: &[String], row: &mut Row) -> bool {
    let path = opt(args, "--systems").expect("--systems");
    let text = std::fs::read_to_string(&path).expect("systems file");
    let s = Setup::new();
    let mut buf = vec![0u32; 1 << 12];
    let mut out = vec![];
    for line in text.lines().filter(|l| !l.trim().is_empty()) {
        let w: Vec<u64> = line.split_whitespace().map(|x| x.parse().expect("int")).collect();
        assert!(w.len() == 2 && w[0] >> 19 == 0);
        let c = s.ctx.solve(w[0], w[1] as u32, &mut buf);
        let sols = list(&buf[..c], |&k| format!("[{},{}]", k & 63, k >> 6));
        out.push(format!("[{},{},{}]", w[0], w[1], sols));
    }
    row.set("systems_file_sha256", esc(&hex(&sha256(text.as_bytes()))));
    row.set("systems_count", out.len().to_string());
    row.set("varieties", format!("[{}]", out.join(",")));
    field_check(row)
}

fn main() {
    let t_main = Instant::now();
    let args: Vec<String> = std::env::args().collect();
    let arm = opt(&args, "--arm").expect("--arm");
    let serial: u64 = opt(&args, "--serial").expect("--serial").parse().expect("serial");
    let out = opt(&args, "--out").expect("--out");
    let point = opt(&args, "--point");
    let mut row = Row(BTreeMap::new());
    row.set("arm", esc(&arm));
    row.set("serial", serial.to_string());
    row.set("point", point.as_deref().map(esc).unwrap_or_else(|| "null".into()));
    row.set("pid", unsafe { getpid() }.to_string());
    row.set("affinity", list(&affinity(), |c| c.to_string()));
    row.set("process_time_resolution_s", num(cpu_res()));
    row.set("load_wall_s", num(t_main.elapsed().as_secs_f64()));
    row.set("native_sha256", exe_sha256());
    row.set("implementation", esc("native tau6dlp (Rust), no Sage process"));
    let ok = match arm.as_str() {
        "N2" | "N2aa" => ic_row(&args, &mut row),
        "O2" => o2_row(&args, &mut row),
        "S0b" => s0b_row(&args, &mut row),
        _ => panic!("unknown arm {}", arm),
    };
    row.set("correct", ok.to_string());
    let raw = row.text();
    std::fs::write(&out, format!("{}\n", raw)).expect("write row");
    println!("raw_b64={}", base64(raw.as_bytes()));
    println!(
        "raw_result_sha256={} serial={} arm={} point={} correct={}",
        hex(&sha256(raw.as_bytes())),
        serial,
        arm,
        point.unwrap_or_else(|| "None".into()),
        ok as u8
    );
    if !ok {
        std::process::exit(3);
    }
}
