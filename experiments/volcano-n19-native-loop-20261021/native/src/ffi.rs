//! C ABI of the native loop (besides the v3 `tau6_*` solve ABI re-exported from `v3`).
//!
//! * `tau6loop_dlp_trace`: setup + tauDlp for one point, with the full trace as JSON:
//!   the planted arm (Sage) compares every item with Sage's own run.
//! * `tau6loop_rng_*`: the MT19937 port, for the pure-Python test against CPython's `random`.

use crate::dlp::{Setup, Trace};
use crate::json::{esc, list, rel_json, relation_digests};
use crate::pyrand::PyRandom;

unsafe fn seed_str<'a>(p: *const u8, len: usize) -> Option<&'a str> {
    if p.is_null() {
        return None;
    }
    std::str::from_utf8(std::slice::from_raw_parts(p, len)).ok()
}

unsafe fn emit(s: &str, out: *mut u8, cap: usize) -> i64 {
    if s.len() <= cap && !out.is_null() {
        std::ptr::copy_nonoverlapping(s.as_ptr(), out, s.len());
    }
    s.len() as i64
}

fn pt_json(p: crate::curve::Pt) -> String {
    match p {
        None => "null".into(),
        Some((x, y)) => format!("[{},{}]", x, y),
    }
}

/// The trace of setup + tauDlp(P, scalar * P, Random(seed)) as JSON; returns its
/// length (written only when it fits in `cap`), or -1 on a bad argument.
pub fn dlp_trace_json(scalar: u64, seed: &str) -> String {
    let s = Setup::new();
    let q = s.f.mul_pt(scalar, s.p);
    let mut rels = vec![];
    let mut tr = Trace::default();
    let st = s.tau_dlp(q, seed, &mut rels, Some(&mut tr), &|| 0.0);
    let base: Vec<String> = s
        .base
        .iter()
        .enumerate()
        .filter_map(|(x, b)| b.map(|b| format!("[{},{},{},{},{},{}]", x, b.pt.0, b.pt.1, b.col, b.e, b.sign)))
        .collect();
    let targets = list(&tr.targets, |t| {
        format!(
            "[{},{},{},{},{},{}]",
            t.al,
            t.be,
            pt_json(t.r),
            list(&t.shifts, |j| j.to_string()),
            t.calls,
            t.rel.map(|r| rel_json(&r)).unwrap_or_else(|| "null".into())
        )
    });
    format!(
        "{{\"setup\":{{\"P\":{},\"reps\":{},\"base\":[{}],\"v_points\":{},\"orbits\":{}}},\"lambda\":{},\
         \"targets\":{},\"counts\":{{\"targets\":{},\"gb_calls\":{},\"spurious\":{},\"relations\":{},\"log\":{}}},\
         \"recovered\":{},\"relations_raw\":{},\"relations_digest\":{},\"used_cols\":{},\"kernel_basis\":{},\
         \"kernel_index\":{},\"Q\":{},\"seed\":{}}}",
        pt_json(s.p),
        list(&s.reps, |&(x, y)| format!("[{},{}]", x, y)),
        base.join(","),
        s.v_points,
        s.reps.len(),
        st.lambda,
        targets,
        st.targets,
        st.gb_calls,
        st.spurious,
        st.relations,
        st.log.map(|v| v.to_string()).unwrap_or_else(|| "null".into()),
        st.recovered,
        list(&rels, rel_json),
        relation_digests(&rels, st.lambda, crate::dlp::P_ORD),
        list(&tr.used_cols, |c| c.to_string()),
        list(&tr.kernel_basis, |v| list(v, |x| x.to_string())),
        tr.kernel_index.map(|v| v.to_string()).unwrap_or_else(|| "null".into()),
        pt_json(q),
        esc(seed)
    )
}

#[no_mangle]
pub unsafe extern "C" fn tau6loop_dlp_trace(scalar: u64, seed: *const u8, seed_len: usize, out: *mut u8,
                                            cap: usize) -> i64 {
    match seed_str(seed, seed_len) {
        None => -1,
        Some(sd) => emit(&dlp_trace_json(scalar, sd), out, cap),
    }
}

/// `n` draws of randrange(start, stop) from Random(seed).
#[no_mangle]
pub unsafe extern "C" fn tau6loop_rng_randrange(seed: *const u8, seed_len: usize, start: u64, stop: u64, n: usize,
                                                out: *mut u64) -> i64 {
    let sd = match seed_str(seed, seed_len) {
        None => return -1,
        Some(v) => v,
    };
    if stop <= start || stop - start >= (1u64 << 32) || out.is_null() {
        return -1;
    }
    let mut r = PyRandom::from_str_seed(sd);
    for i in 0..n {
        *out.add(i) = r.randrange(start, stop);
    }
    n as i64
}

/// `rounds` successive shuffles of one list [0, len): writes every round's result.
#[no_mangle]
pub unsafe extern "C" fn tau6loop_rng_shuffle(seed: *const u8, seed_len: usize, len: usize, rounds: usize,
                                              out: *mut u32) -> i64 {
    let sd = match seed_str(seed, seed_len) {
        None => return -1,
        Some(v) => v,
    };
    if out.is_null() {
        return -1;
    }
    let mut r = PyRandom::from_str_seed(sd);
    let mut v: Vec<u32> = (0..len as u32).collect();
    for k in 0..rounds {
        r.shuffle(&mut v);
        for (i, &x) in v.iter().enumerate() {
            *out.add(k * len + i) = x;
        }
    }
    (rounds * len) as i64
}

/// Interleaved randrange(1, p) twice and shuffle(list of 19), as tauDlp draws them,
/// `rounds` times: writes al, be, then the 19 shifts, per round.
#[no_mangle]
pub unsafe extern "C" fn tau6loop_rng_tau_stream(seed: *const u8, seed_len: usize, p: u64, rounds: usize,
                                                 out: *mut u64) -> i64 {
    let sd = match seed_str(seed, seed_len) {
        None => return -1,
        Some(v) => v,
    };
    if out.is_null() || p < 2 {
        return -1;
    }
    let mut r = PyRandom::from_str_seed(sd);
    let mut v: Vec<u32> = (0..19).collect();
    let mut o = 0usize;
    for _ in 0..rounds {
        *out.add(o) = r.randrange(1, p);
        *out.add(o + 1) = r.randrange(1, p);
        o += 2;
        r.shuffle(&mut v);
        for &x in &v {
            *out.add(o) = x as u64;
            o += 1;
        }
    }
    o as i64
}

/// One product in the loop's own field arithmetic (`curve::Field::mul`), for the field check.
#[no_mangle]
pub extern "C" fn tau6loop_mul(a: u64, b: u64) -> u64 {
    thread_local!(static F: crate::curve::Field = crate::curve::Field::new(19, crate::dlp::MODULUS));
    if a >> 19 != 0 || b >> 19 != 0 {
        return u64::MAX;
    }
    F.with(|f| f.mul(a, b))
}
