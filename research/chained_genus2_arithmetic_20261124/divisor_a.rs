use crate::elliptic_a::{self, EP};
use crate::field49_a::{Quadratic, BASE, K};
use crate::field_d::{add, inv, mul, sub};
use crate::poly_d::{addp, bezout, divrem, evaluate, pow, scale, subp, times, trim, P};

pub const H: [u8; 7] = [1, 0, 0, 0, 2, 0, 6];

#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub struct Div {
    pub u: P,
    pub v: P,
}

pub fn identity() -> Div {
    Div {
        u: vec![1],
        v: vec![],
    }
}
pub fn valid_with_h(a: &Div, h: &[u8]) -> bool {
    if a == &identity() {
        return true;
    }
    a.u.len() == 3
        && a.u[2] == 1
        && a.v.len() <= 2
        && trim(a.v.clone()) == a.v
        && a.u.iter().chain(&a.v).all(|&x| x < 7)
        && divrem(&subp(h, &pow(&a.v, 2)), &a.u).1.is_empty()
}
pub fn valid(a: &Div) -> bool {
    valid_with_h(a, &H)
}
fn exact(a: &[u8], b: &[u8]) -> P {
    let (q, r) = divrem(a, b);
    assert!(r.is_empty(), "nonexact divisor division: {a:?}/{b:?}");
    q
}
pub fn neg(a: &Div) -> Div {
    assert!(valid(a));
    Div {
        u: a.u.clone(),
        v: scale(&a.v, 6),
    }
}
pub fn cantor(a: &Div, b: &Div) -> Div {
    assert!(valid(a) && valid(b));
    let (d1, e1, e2) = bezout(&a.u, &b.u);
    let (d, c1, c2) = bezout(&d1, &addp(&a.v, &b.v));
    let (s1, s2, s3) = (times(&c1, &e1), times(&c1, &e2), c2);
    assert_eq!(
        addp(
            &addp(&times(&s1, &a.u), &times(&s2, &b.u)),
            &times(&s3, &addp(&a.v, &b.v))
        ),
        d
    );
    let mut u = exact(&times(&a.u, &b.u), &pow(&d, 2));
    let numerator = addp(
        &addp(
            &times(&times(&s1, &a.u), &b.v),
            &times(&times(&s2, &b.u), &a.v),
        ),
        &times(&s3, &addp(&times(&a.v, &b.v), &H)),
    );
    let mut v = divrem(&exact(&numerator, &d), &u).1;
    assert!(divrem(&subp(&H, &pow(&v, 2)), &u).1.is_empty());
    assert!([1, 3, 5].contains(&u.len()));
    if u.len() == 5 {
        let next = exact(&subp(&H, &pow(&v, 2)), &u);
        assert_eq!(next.len(), 3, "inert leading coefficient must not cancel");
        u = scale(&next, inv(*next.last().unwrap()));
        v = divrem(&scale(&v, 6), &u).1;
    }
    let out = Div { u, v };
    assert!(valid(&out));
    out
}
pub fn scalar(a: &Div, mut n: usize) -> Div {
    let mut r = identity();
    let mut b = a.clone();
    while n > 0 {
        if n & 1 == 1 {
            r = cantor(&r, &b);
        }
        n >>= 1;
        if n > 0 {
            b = cantor(&b, &b);
        }
    }
    r
}
pub fn pull1(p: EP) -> Div {
    p.map_or_else(identity, |(x, y)| Div {
        u: vec![sub(0, add(mul(5, x), 3)), 0, 1],
        v: trim(vec![y]),
    })
}
pub fn pull2(p: EP) -> Div {
    p.map_or_else(identity, |(x, y)| {
        assert_ne!(x, 0);
        Div {
            u: vec![sub(0, inv(x)), 0, 1],
            v: trim(vec![0, mul(y, inv(x))]),
        }
    })
}
pub fn gamma(p: EP) -> Div {
    scalar(&cantor(&pull1(p), &pull2(elliptic_a::mul_base(p, 9))), 6)
}

#[derive(Clone, Debug)]
pub struct Push {
    pub pair: (EP, EP),
    pub kind: &'static str,
    pub roots: [K; 2],
    pub field: Quadratic,
}
pub fn push(a: &Div) -> Push {
    assert!(valid(a));
    if a == &identity() {
        return Push {
            pair: (None, None),
            kind: "identity",
            roots: [K([0, 0]); 2],
            field: BASE,
        };
    }
    let rational: Vec<_> = (0..7).filter(|&x| evaluate(&a.u, x) == 0).collect();
    let (q, roots, kind) = match rational.as_slice() {
        &[x, y] => (BASE, [BASE.base(x), BASE.base(y)], "split"),
        &[x] => {
            assert_eq!(a.u, vec![mul(x, x), mul(5, x), 1]);
            (BASE, [BASE.base(x); 2], "double")
        }
        [] => {
            let q = Quadratic {
                u0: a.u[0],
                u1: a.u[1],
            };
            q.validate();
            let x = K([0, 1]);
            let y = q.conjugate(x);
            assert_eq!(q.pow(x, 7), y);
            (q, [x, y], "quadratic")
        }
        _ => panic!("invalid quadratic root population"),
    };
    let mut out = (None, None);
    for x in roots {
        assert_eq!(
            q.add(q.add(q.mul(x, x), q.scale(x, a.u[1])), q.base(a.u[0])),
            q.base(0)
        );
        let y =
            a.v.iter()
                .rev()
                .fold(q.base(0), |r, &c| q.add(q.mul(r, x), q.base(c)));
        let image1 = Some((q.add(q.scale(q.mul(x, x), 3), q.base(5)), y));
        let image2 = if x == q.base(0) {
            None
        } else {
            Some((q.inv(q.mul(x, x)), q.mul(y, q.inv(q.pow(x, 3)))))
        };
        assert!(elliptic_a::valid(q, image1) && elliptic_a::valid(q, image2));
        out.0 = elliptic_a::add(q, out.0, image1);
        out.1 = elliptic_a::add(q, out.1, image2);
    }
    Push {
        pair: (elliptic_a::descend(out.0), elliptic_a::descend(out.1)),
        kind,
        roots,
        field: q,
    }
}
