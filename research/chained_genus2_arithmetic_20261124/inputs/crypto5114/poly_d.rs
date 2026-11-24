use crate::field_d::*;
pub type P = Vec<u8>;
pub fn trim(mut p: P) -> P {
    while p.last() == Some(&0) {
        p.pop();
    }
    p
}
pub fn addp(a: &[u8], b: &[u8]) -> P {
    trim(
        (0..a.len().max(b.len()))
            .map(|i| {
                add(
                    a.get(i).copied().unwrap_or(0),
                    b.get(i).copied().unwrap_or(0),
                )
            })
            .collect(),
    )
}
pub fn scale(a: &[u8], c: u8) -> P {
    trim(a.iter().map(|&a| mul(a, c)).collect())
}
pub fn subp(a: &[u8], b: &[u8]) -> P {
    addp(a, &scale(b, 6))
}
pub fn times(a: &[u8], b: &[u8]) -> P {
    if a.is_empty() || b.is_empty() {
        return Vec::new();
    }
    let mut out = vec![0; a.len() + b.len() - 1];
    for (i, &a) in a.iter().enumerate() {
        for (j, &b) in b.iter().enumerate() {
            out[i + j] = add(out[i + j], mul(a, b));
        }
    }
    trim(out)
}
pub fn pow(a: &[u8], n: usize) -> P {
    (0..n).fold(vec![1], |r, _| times(&r, a))
}
pub fn divrem(a: &[u8], b: &[u8]) -> (P, P) {
    let b = trim(b.to_vec());
    assert!(!b.is_empty());
    let mut r = trim(a.to_vec());
    let mut q = Vec::new();
    while !r.is_empty() && r.len() >= b.len() {
        let degree = r.len() - b.len();
        let c = mul(*r.last().unwrap(), inv(*b.last().unwrap()));
        let mut t = vec![0; degree + 1];
        t[degree] = c;
        q = addp(&q, &t);
        r = subp(&r, &times(&b, &t));
    }
    assert_eq!(addp(&times(&b, &q), &r), trim(a.to_vec()));
    (q, r)
}
pub fn derivative(a: &[u8]) -> P {
    trim(
        a.iter()
            .enumerate()
            .skip(1)
            .map(|(i, &a)| mul(a, u8::try_from(i % 7).unwrap()))
            .collect(),
    )
}
pub fn evaluate(a: &[u8], x: u8) -> u8 {
    a.iter().rev().fold(0, |r, &a| add(mul(r, x), a))
}
pub fn bezout(a: &[u8], b: &[u8]) -> (P, P, P) {
    let (mut old_r, mut r) = (trim(a.to_vec()), trim(b.to_vec()));
    let (mut old_s, mut s) = (vec![1], vec![]);
    let (mut old_t, mut t) = (vec![], vec![1]);
    while !r.is_empty() {
        let (q, next) = divrem(&old_r, &r);
        old_r = r;
        r = next;
        let ns = subp(&old_s, &times(&q, &s));
        old_s = s;
        s = ns;
        let nt = subp(&old_t, &times(&q, &t));
        old_t = t;
        t = nt;
    }
    let unit = inv(*old_r.last().unwrap());
    let (g, s, t) = (
        scale(&old_r, unit),
        scale(&old_s, unit),
        scale(&old_t, unit),
    );
    assert_eq!(addp(&times(a, &s), &times(b, &t)), g);
    (g, s, t)
}
