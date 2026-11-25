use crate::field49_a::{Quadratic, BASE, K};

pub type EP = Option<(u8, u8)>;
pub type EK = Option<(K, K)>;

pub fn valid(q: Quadratic, p: EK) -> bool {
    p.is_none_or(|(x, y)| q.mul(y, y) == q.add(q.add(q.pow(x, 3), q.scale(x, 2)), q.base(6)))
}
pub fn add(q: Quadratic, p: EK, r: EK) -> EK {
    assert!(valid(q, p) && valid(q, r));
    let (Some((x1, y1)), Some((x2, y2))) = (p, r) else {
        return p.or(r);
    };
    if x1 == x2 && q.add(y1, y2) == q.base(0) {
        return None;
    }
    let slope = if x1 == x2 {
        assert_eq!(y1, y2);
        q.mul(
            q.add(q.scale(q.mul(x1, x1), 3), q.base(2)),
            q.inv(q.scale(y1, 2)),
        )
    } else {
        q.mul(q.sub(y2, y1), q.inv(q.sub(x2, x1)))
    };
    let x = q.sub(q.sub(q.mul(slope, slope), x1), x2);
    let y = q.sub(q.mul(slope, q.sub(x1, x)), y1);
    let out = Some((x, y));
    assert!(valid(q, out));
    out
}
pub fn lift(q: Quadratic, p: EP) -> EK {
    p.map(|(x, y)| (q.base(x), q.base(y)))
}
pub fn descend(p: EK) -> EP {
    p.map(|(x, y)| {
        assert_eq!((x.0[1], y.0[1]), (0, 0));
        (x.0[0], y.0[0])
    })
}
pub fn add_base(p: EP, r: EP) -> EP {
    descend(add(BASE, lift(BASE, p), lift(BASE, r)))
}
pub fn mul_base(p: EP, n: usize) -> EP {
    (0..n).fold(None, |a, _| add_base(a, p))
}
pub fn points() -> Vec<EP> {
    let mut out = vec![None];
    for x in 0..7 {
        for y in 0..7 {
            let p = Some((x, y));
            if valid(BASE, lift(BASE, p)) {
                out.push(p);
            }
        }
    }
    out
}
