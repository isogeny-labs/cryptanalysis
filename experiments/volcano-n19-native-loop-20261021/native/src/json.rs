//! Minimal JSON writing (no dependencies) and the relation digests of
//! ../relation_digest.py, byte for byte: `json.dumps(obj, separators=(',', ':'),
//! sort_keys=True)` of nested lists of ints is the obvious text, so the digests
//! here equal Python's (the verifier recomputes them from relations_raw anyway).

use crate::dlp::{modpow, Rel};
use crate::util::{hex, sha256};

pub fn esc(s: &str) -> String {
    let mut o = String::with_capacity(s.len() + 2);
    o.push('"');
    for ch in s.chars() {
        match ch {
            '"' => o.push_str("\\\""),
            '\\' => o.push_str("\\\\"),
            '\n' => o.push_str("\\n"),
            c if (c as u32) < 0x20 => o.push_str(&format!("\\u{:04x}", c as u32)),
            c => o.push(c),
        }
    }
    o.push('"');
    o
}

/// A float as JSON (finite; Rust's shortest round-trip text).
pub fn num(x: f64) -> String {
    assert!(x.is_finite());
    let s = format!("{:?}", x);
    s
}

pub fn rel_json(r: &Rel) -> String {
    format!("[[{},{},{}],[{},{},{}]]", r[0].0, r[0].1, r[0].2, r[1].0, r[1].1, r[1].2)
}

pub fn list<T, F: Fn(&T) -> String>(xs: &[T], f: F) -> String {
    let v: Vec<String> = xs.iter().map(f).collect();
    format!("[{}]", v.join(","))
}

/// relation_digest.relation_digests(rels, lam, p): ordered, canonical and rows SHA-256 and the count.
pub fn relation_digests(rels: &[Rel], lam: u64, p: u64) -> String {
    let ordered = list(rels, rel_json);
    let canon = list(rels, |r| {
        let mut v = vec![(r[0].0 as i64, r[0].1, r[0].2 as i64), (r[1].0 as i64, r[1].1, r[1].2 as i64)];
        v.sort();
        format!("[[{},{},{}],[{},{},{}]]", v[0].0, v[0].1, v[0].2, v[1].0, v[1].1, v[1].2)
    });
    let rows = list(rels, |r| {
        let mut row: Vec<(usize, u64)> = vec![];
        for &(c, s, e) in r.iter() {
            let t = modpow(lam, e as u64, p);
            let t = if s == 1 { t } else { (p - t) % p };
            match row.iter_mut().find(|x| x.0 == c) {
                Some(x) => x.1 = (x.1 + t) % p,
                None => row.push((c, t)),
            }
        }
        row.sort();
        list(&row, |(c, v)| format!("[{},{}]", c, v))
    });
    format!(
        "{{\"canonical_sha256\":{},\"count\":{},\"ordered_sha256\":{},\"rows_sha256\":{}}}",
        esc(&hex(&sha256(canon.as_bytes()))),
        rels.len(),
        esc(&hex(&sha256(ordered.as_bytes()))),
        esc(&hex(&sha256(rows.as_bytes())))
    )
}
