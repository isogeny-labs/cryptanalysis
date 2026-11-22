//! Independent verifier for the H114 multiradix carry-cohomology experiment.
//!
//! This file intentionally shares no source with the producer. Compile with:
//! `rustc --edition=2021 -O h114_multiradix_verify.rs -o h114_multiradix_verify`.

use std::collections::{BTreeSet, HashMap};
use std::env;
use std::fs;

const PROTOCOL_SHA256: &str = "8d89092331a64a00d51ce7caa1602b035ff582835f8b6f7287912d07590ed51c";
const SECTION_DOMAIN: u64 = 0x4831_3134_5345_4354;
const LABEL_DOMAIN: u64 = 0x4831_3134_4c41_424c;
const MIX_INC: u64 = 0x9e37_79b9_7f4a_7c15;
const MIX_M1: u64 = 0xbf58_476d_1ce4_e5b9;
const MIX_M2: u64 = 0x94d0_49bb_1331_11eb;
const CHANNELS: [&str; 8] = [
    "raw",
    "plus",
    "minus",
    "forward",
    "backward",
    "curvature",
    "anchor_plus",
    "anchor_minus",
];

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
struct Point {
    x: u64,
    y: u64,
}

#[derive(Clone, Copy, Debug)]
struct Curve {
    slug: &'static str,
    icv1: &'static str,
    p: u64,
    a: u64,
    b: u64,
    r: u64,
}

const CURVES: [Curve; 7] = [
    Curve {
        slug: "icv1-fp7-t19-5c8a8fbb",
        icv1: "ICV1:fp-101:19:83:63:unk:unk:r:5c8a8fbb4306",
        p: 101,
        a: 6,
        b: 9,
        r: 83,
    },
    Curve {
        slug: "icv1-fp7-t19-7e6da47e",
        icv1: "ICV1:fp-127:19:109:21:unk:unk:r:7e6da47e5756",
        p: 127,
        a: 1,
        b: 7,
        r: 109,
    },
    Curve {
        slug: "icv1-fp8-t11-972f2836",
        icv1: "ICV1:fp-149:11:139:26:unk:unk:r:972f2836fd54",
        p: 149,
        a: 2,
        b: 8,
        r: 139,
    },
    Curve {
        slug: "icv1-fp8-tm11-e7c21318",
        icv1: "ICV1:fp-211:-11:223:46:unk:unk:r:e7c21318e16c",
        p: 211,
        a: 1,
        b: 1,
        r: 223,
    },
    Curve {
        slug: "icv1-fp9-t3-f53f79d8",
        icv1: "ICV1:fp-283:3:281:267:unk:unk:r:f53f79d850fc",
        p: 283,
        a: 2,
        b: 7,
        r: 281,
    },
    Curve {
        slug: "icv1-fp9-t5-51f1adea",
        icv1: "ICV1:fp-503:5:499:220:unk:unk:r:51f1adea5613",
        p: 503,
        a: 3,
        b: 8,
        r: 499,
    },
    Curve {
        slug: "icv1-fp10-tm39-d6809684",
        icv1: "ICV1:fp-907:-39:947:340:unk:unk:r:d6809684812b",
        p: 907,
        a: 1,
        b: 1,
        r: 947,
    },
];

const ISO_CURVES: [Curve; 2] = [
    Curve {
        slug: "icv1-fp7-t19-227f3bd5",
        icv1: "ICV1:fp-101:19:83:63:unk:unk:r:227f3bd5a83b",
        p: 101,
        a: 96,
        b: 71,
        r: 83,
    },
    Curve {
        slug: "icv1-fp7-t19-28271374",
        icv1: "ICV1:fp-127:19:109:21:unk:unk:r:282713748f5c",
        p: 127,
        a: 16,
        b: 67,
        r: 109,
    },
];

#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
struct Record {
    k2: u64,
    k3: u64,
    k5: u64,
    n23: i64,
    n25: i64,
    n35: i64,
    w23: i64,
    w25: i64,
    w35: i64,
    heights: [i64; 6],
    braid_residual: i64,
}

#[derive(Clone)]
struct Dataset {
    values: Vec<Record>,
    seen: Vec<bool>,
}

impl Dataset {
    fn new(r: u64) -> Self {
        Self {
            values: vec![Record::default(); r as usize],
            seen: vec![false; r as usize],
        }
    }
}

#[derive(Clone, Copy)]
enum Section {
    Canonical,
    Random {
        generator_multiplier: u64,
        replicate: u64,
    },
    Torsion,
}

fn fail<T>(message: impl Into<String>) -> Result<T, String> {
    Err(message.into())
}

fn residue(value: i128, modulus: u64) -> u64 {
    value.rem_euclid(modulus as i128) as u64
}

fn addm(a: u64, b: u64, n: u64) -> u64 {
    ((a as u128 + b as u128) % n as u128) as u64
}

fn subm(a: u64, b: u64, n: u64) -> u64 {
    residue(a as i128 - b as i128, n)
}

fn mulm(a: u64, b: u64, n: u64) -> u64 {
    ((a as u128 * b as u128) % n as u128) as u64
}

fn inverse(a: u64, n: u64) -> Result<u64, String> {
    let (mut r0, mut r1) = (n as i128, (a % n) as i128);
    let (mut s0, mut s1) = (0i128, 1i128);
    while r1 != 0 {
        let q = r0 / r1;
        (r0, r1) = (r1, r0 - q * r1);
        (s0, s1) = (s1, s0 - q * s1);
    }
    if r0 != 1 {
        return fail(format!("{} is not a unit modulo {}", a, n));
    }
    Ok(residue(s0, n))
}

fn on_curve(curve: Curve, point: Point, modulus: u64) -> bool {
    mulm(point.y, point.y, modulus)
        == addm(
            addm(
                mulm(mulm(point.x, point.x, modulus), point.x, modulus),
                mulm(curve.a, point.x, modulus),
                modulus,
            ),
            curve.b,
            modulus,
        )
}

fn negative(point: Option<Point>, modulus: u64) -> Option<Point> {
    point.map(|q| Point {
        x: q.x,
        y: residue(-(q.y as i128), modulus),
    })
}

fn ec_add(
    curve: Curve,
    left: Option<Point>,
    right: Option<Point>,
    modulus: u64,
) -> Result<Option<Point>, String> {
    let (p, q) = match (left, right) {
        (None, value) | (value, None) => return Ok(value),
        (Some(p), Some(q)) => (p, q),
    };
    if p.x == q.x && addm(p.y, q.y, modulus) == 0 {
        return Ok(None);
    }
    let (top, bottom) = if p == q {
        (
            addm(mulm(3, mulm(p.x, p.x, modulus), modulus), curve.a, modulus),
            mulm(2, p.y, modulus),
        )
    } else {
        (subm(q.y, p.y, modulus), subm(q.x, p.x, modulus))
    };
    if bottom % curve.p == 0 {
        return fail("affine addition encountered a nonunit denominator");
    }
    let slope = mulm(top, inverse(bottom, modulus)?, modulus);
    let x3 = subm(
        subm(mulm(slope, slope, modulus), p.x, modulus),
        q.x,
        modulus,
    );
    let y3 = subm(mulm(slope, subm(p.x, x3, modulus), modulus), p.y, modulus);
    let out = Point { x: x3, y: y3 };
    if !on_curve(curve, out, modulus) {
        return fail("affine addition left the curve");
    }
    Ok(Some(out))
}

fn ec_mul(
    curve: Curve,
    mut scalar: u64,
    point: Option<Point>,
    modulus: u64,
) -> Result<Option<Point>, String> {
    let mut acc = None;
    let mut power = point;
    while scalar != 0 {
        if scalar & 1 == 1 {
            acc = ec_add(curve, acc, power, modulus)?;
        }
        scalar >>= 1;
        if scalar != 0 {
            power = ec_add(curve, power, power, modulus)?;
        }
    }
    Ok(acc)
}

fn first_point(curve: Curve) -> Result<Point, String> {
    for x in 0..curve.p {
        for y in 1..curve.p {
            let q = Point { x, y };
            if on_curve(curve, q, curve.p) && ec_mul(curve, curve.r, Some(q), curve.p)?.is_none() {
                return Ok(q);
            }
        }
    }
    fail(format!("no order-r point for {}", curve.slug))
}

fn hensel(curve: Curve, point: Point, u: u64) -> Result<Point, String> {
    let p = curve.p;
    let n = p * p;
    let discrepancy = point.x as i128 * point.x as i128 * point.x as i128
        + curve.a as i128 * point.x as i128
        + curve.b as i128
        - point.y as i128 * point.y as i128;
    if discrepancy.rem_euclid(p as i128) != 0 {
        return fail("base point does not satisfy the Hensel premise");
    }
    let constant = residue(discrepancy / p as i128, p);
    let tangent = addm(mulm(3, mulm(point.x, point.x, p), p), curve.a, p);
    let v = mulm(
        addm(constant, mulm(tangent, u % p, p), p),
        inverse(2 * point.y, p)?,
        p,
    );
    let out = Point {
        x: point.x + p * (u % p),
        y: point.y + p * v,
    };
    if !on_curve(curve, out, n) {
        return fail("constructed lift is not on E(Z/p^2Z)");
    }
    Ok(out)
}

fn kernel_parameter(curve: Curve, left: Point, right: Point) -> Result<u64, String> {
    let n = curve.p * curve.p;
    let h = subm(right.x, left.x, n);
    let z = mulm(2, h, n);
    let i = mulm(z, z, n);
    let j = mulm(h, i, n);
    let rr = mulm(2, subm(right.y, left.y, n), n);
    let v = mulm(left.x, i, n);
    let x = subm(subm(mulm(rr, rr, n), j, n), mulm(2, v, n), n);
    let y = subm(
        mulm(rr, subm(v, x, n), n),
        mulm(2, mulm(left.y, j, n), n),
        n,
    );
    if z % curve.p != 0 || y % curve.p == 0 {
        return fail("mixed sum did not land in the first formal layer");
    }
    let t = mulm(residue(-(mulm(x, z, n) as i128), n), inverse(y, n)?, n);
    if t % curve.p != 0 {
        return fail("formal parameter is not divisible by p");
    }
    Ok((t / curve.p) % curve.p)
}

fn splitmix_once(input: u64) -> u64 {
    let mut z = input.wrapping_add(MIX_INC);
    z = (z ^ (z >> 30)).wrapping_mul(MIX_M1);
    z = (z ^ (z >> 27)).wrapping_mul(MIX_M2);
    z ^ (z >> 31)
}

fn control_seed(domain: &str, curve: Curve, generator_multiplier: u64, replicate: u64) -> u64 {
    let material = format!(
        "{}\0{}\0{}\0{}",
        domain, curve.slug, generator_multiplier, replicate
    );
    u64::from_be_bytes(sha256(material.as_bytes())[..8].try_into().unwrap())
}

fn random_u(curve: Curve, point: Point, generator_multiplier: u64, replicate: u64) -> u64 {
    splitmix_once(
        control_seed(
            "H114/random-section/v1",
            curve,
            generator_multiplier,
            replicate,
        ) ^ SECTION_DOMAIN
            ^ point.x.wrapping_shl(32)
            ^ point.y,
    ) % curve.p
}

fn r_torsion_tau(curve: Curve, point: Point, u: u64, split: u64) -> Result<u64, String> {
    let lifted = hensel(curve, point, u)?;
    let n = curve.p * curve.p;
    let left = ec_mul(curve, split, Some(lifted), n)?.ok_or("left split reached identity")?;
    let right =
        ec_mul(curve, curve.r - split, Some(lifted), n)?.ok_or("right split reached identity")?;
    kernel_parameter(curve, left, right)
}

fn torsion_u(curve: Curve, point: Point) -> Result<u64, String> {
    let split = (curve.r - 1) / 2;
    let tau0 = r_torsion_tau(curve, point, 0, split)?;
    let tau_alt = r_torsion_tau(curve, point, 0, std::cmp::max(1, curve.r / 3))?;
    if tau0 != tau_alt {
        return fail("torsion parameter depends on the addition split");
    }
    let tau1 = r_torsion_tau(curve, point, 1, split)?;
    let slope = subm(tau1, tau0, curve.p);
    if slope == 0 {
        return fail("torsion-section slope vanished");
    }
    let u = residue(-(tau0 as i128) * inverse(slope, curve.p)? as i128, curve.p);
    if r_torsion_tau(curve, point, u, split)? != 0 {
        return fail("solved torsion lift is not r-torsion");
    }
    Ok(u)
}

fn section_u(curve: Curve, point: Point, section: Section) -> Result<u64, String> {
    match section {
        Section::Canonical => Ok(0),
        Section::Random {
            generator_multiplier,
            replicate,
        } => Ok(random_u(curve, point, generator_multiplier, replicate)),
        Section::Torsion => torsion_u(curve, point),
    }
}

fn carry(
    curve: Curve,
    root: Point,
    target: Point,
    multiplier: u64,
    section: Section,
) -> Result<u64, String> {
    let n = curve.p * curve.p;
    let root_lift = hensel(curve, root, section_u(curve, root, section)?)?;
    let target_lift = hensel(curve, target, section_u(curve, target, section)?)?;
    let multiplied = ec_mul(curve, multiplier, Some(root_lift), n)?
        .ok_or("lifted small multiple reached identity")?;
    if (Point {
        x: multiplied.x % curve.p,
        y: multiplied.y % curve.p,
    }) != target
    {
        return fail("lifted multiplication reduced to the wrong point");
    }
    kernel_parameter(curve, multiplied, negative(Some(target_lift), n).unwrap())
}

fn root(curve: Curve, q: Point, multiplier: u64) -> Result<Point, String> {
    ec_mul(curve, inverse(multiplier, curve.r)?, Some(q), curve.p)?
        .ok_or_else(|| format!("{multiplier}-root is identity"))
}

fn kappa(curve: Curve, q: Point, multiplier: u64, section: Section) -> Result<u64, String> {
    carry(curve, root(curve, q, multiplier)?, q, multiplier, section)
}

fn pair_windings(
    curve: Curve,
    q: Point,
    section: Section,
) -> Result<(u64, u64, u64, i64, i64, i64, i64, i64, i64), String> {
    let h2 = root(curve, q, 2)?;
    let h3 = root(curve, q, 3)?;
    let h5 = root(curve, q, 5)?;
    let k2 = kappa(curve, q, 2, section)?;
    let k3 = kappa(curve, q, 3, section)?;
    let k5 = kappa(curve, q, 5, section)?;
    let n23 = 2 * kappa(curve, h2, 3, section)? as i64 + k2 as i64
        - 3 * kappa(curve, h3, 2, section)? as i64
        - k3 as i64;
    let n25 = 2 * kappa(curve, h2, 5, section)? as i64 + k2 as i64
        - 5 * kappa(curve, h5, 2, section)? as i64
        - k5 as i64;
    let n35 = 3 * kappa(curve, h3, 5, section)? as i64 + k3 as i64
        - 5 * kappa(curve, h5, 3, section)? as i64
        - k5 as i64;
    for numerator in [n23, n25, n35] {
        if numerator.rem_euclid(curve.p as i64) != 0 {
            return fail("pair-winding numerator is not exactly divisible by p");
        }
    }
    let (w23, w25, w35) = (
        n23 / curve.p as i64,
        n25 / curve.p as i64,
        n35 / curve.p as i64,
    );
    if !(-3..=2).contains(&w23) || !(-5..=2).contains(&w25) || !(-5..=3).contains(&w35) {
        return fail("pair winding lies outside its frozen range");
    }
    Ok((k2, k3, k5, n23, n25, n35, w23, w25, w35))
}

fn winding(curve: Curve, q: Point, section: Section) -> Result<Record, String> {
    let (k2, k3, k5, n23, n25, n35, w23, w25, w35) = pair_windings(curve, q, section)?;
    let h2 = root(curve, q, 2)?;
    let h3 = root(curve, q, 3)?;
    let h5 = root(curve, q, 5)?;
    let h6 = root(curve, q, 6)?;
    let h10 = root(curve, q, 10)?;
    let h15 = root(curve, q, 15)?;
    let heights = [
        6 * kappa(curve, h6, 5, section)? as i64
            + 2 * kappa(curve, h2, 3, section)? as i64
            + k2 as i64,
        10 * kappa(curve, h10, 3, section)? as i64
            + 2 * kappa(curve, h2, 5, section)? as i64
            + k2 as i64,
        6 * kappa(curve, h6, 5, section)? as i64
            + 3 * kappa(curve, h3, 2, section)? as i64
            + k3 as i64,
        15 * kappa(curve, h15, 2, section)? as i64
            + 3 * kappa(curve, h3, 5, section)? as i64
            + k3 as i64,
        10 * kappa(curve, h10, 3, section)? as i64
            + 5 * kappa(curve, h5, 2, section)? as i64
            + k5 as i64,
        15 * kappa(curve, h15, 2, section)? as i64
            + 5 * kappa(curve, h5, 3, section)? as i64
            + k5 as i64,
    ];
    if heights
        .iter()
        .any(|height| height.rem_euclid(curve.p as i64) != heights[0].rem_euclid(curve.p as i64))
    {
        return fail("six represented path heights disagree modulo p");
    }

    let n = curve.p * curve.p;
    let h30 = root(curve, q, 30)?;
    let h30_lift = hensel(curve, h30, section_u(curve, h30, section)?)?;
    let q_lift = hensel(curve, q, section_u(curve, q, section)?)?;
    let direct = ec_mul(curve, 30, Some(h30_lift), n)?.ok_or("direct path is identity")?;
    for order in [
        [2, 3, 5],
        [2, 5, 3],
        [3, 2, 5],
        [3, 5, 2],
        [5, 2, 3],
        [5, 3, 2],
    ] {
        let mut path = Some(h30_lift);
        for multiplier in order.into_iter().rev() {
            path = ec_mul(curve, multiplier, path, n)?;
        }
        if path != Some(direct) {
            return fail("one of the six lifted paths differs from [30]");
        }
    }
    if (Point {
        x: direct.x % curve.p,
        y: direct.y % curve.p,
    }) != q
    {
        return fail("direct lifted path reduces to the wrong point");
    }
    let path_tau = kernel_parameter(curve, direct, negative(Some(q_lift), n).unwrap())?;
    if heights
        .iter()
        .any(|height| height.rem_euclid(curve.p as i64) as u64 != path_tau)
    {
        return fail("represented path height disagrees with formal parameter");
    }

    let (_, _, _, _, _, _, _, w25q3, _) = pair_windings(curve, h3, section)?;
    let (_, _, _, _, _, _, _, _, w35q2) = pair_windings(curve, h2, section)?;
    let (_, _, _, _, _, _, w23q5, _, _) = pair_windings(curve, h5, section)?;
    let p = curve.p as i64;
    if heights[0] - heights[2] != p * w23
        || heights[2] - heights[3] != 3 * p * w25q3
        || heights[3] - heights[5] != p * w35
        || heights[0] - heights[1] != 2 * p * w35q2
        || heights[1] - heights[4] != p * w25
        || heights[4] - heights[5] != 5 * p * w23q5
    {
        return fail("oriented path-edge equation failed");
    }
    let braid_residual = w23 + 3 * w25q3 + w35 - 2 * w35q2 - w25 - 5 * w23q5;
    if braid_residual != 0 {
        return fail("braid residual is nonzero");
    }
    Ok(Record {
        k2,
        k3,
        k5,
        n23,
        n25,
        n35,
        w23,
        w25,
        w35,
        heights,
        braid_residual,
    })
}

fn curve_by_slug(slug: &str) -> Result<Curve, String> {
    CURVES
        .iter()
        .chain(ISO_CURVES.iter())
        .find(|c| c.slug == slug)
        .copied()
        .ok_or_else(|| format!("unknown curve slug {slug}"))
}

fn permutations(size: usize) -> Vec<Vec<u8>> {
    let mut p = (0..size as u8).collect::<Vec<_>>();
    let mut out = vec![p.clone()];
    loop {
        let Some(i) = (0..size - 1).rev().find(|&i| p[i] < p[i + 1]) else {
            break;
        };
        let j = (i + 1..size).rev().find(|&j| p[i] < p[j]).unwrap();
        p.swap(i, j);
        p[i + 1..].reverse();
        out.push(p.clone());
    }
    out
}

fn channel_values(wq: i64, wp: i64, wm: i64, wg: i64, wng: i64) -> [i64; 8] {
    [
        wq,
        wp,
        wm,
        wp - wq,
        wq - wm,
        wp - 2 * wq + wm,
        wp - wq - wg,
        wm - wq - wng,
    ]
}

fn features(records: &[Record], r: u64, generator_index: u64, scalar: u64) -> [u8; 8] {
    let q = scalar * generator_index % r;
    let plus = (q + generator_index) % r;
    let minus = (q + r - generator_index) % r;
    let qrec = records[q as usize];
    let prec = records[plus as usize];
    let mrec = records[minus as usize];
    let grec = records[generator_index as usize];
    let ngrec = records[(r - generator_index) as usize];
    let c35 = channel_values(qrec.w35, prec.w35, mrec.w35, grec.w35, ngrec.w35);
    let c25 = channel_values(qrec.w25, prec.w25, mrec.w25, grec.w25, ngrec.w25);
    let c23 = channel_values(qrec.w23, prec.w23, mrec.w23, grec.w23, ngrec.w23);
    let mut out = [0u8; 8];
    for channel in 0..8 {
        out[channel] = c35[channel].rem_euclid(2) as u8 * 15
            + c25[channel].rem_euclid(3) as u8 * 5
            + c23[channel].rem_euclid(5) as u8;
    }
    out
}

fn digits(p: &[u8]) -> String {
    p.iter().map(|value| char::from(b'0' + *value)).collect()
}

fn predicate_id(channel: usize, p2: &[u8], p3: &[u8], p5: &[u8]) -> String {
    format!(
        "channel:{}:pi2:{}:pi3:{}:pi5:{}",
        CHANNELS[channel],
        digits(p2),
        digits(p3),
        digits(p5)
    )
}

fn mapped_digit(code: u8, p2: &[u8], p3: &[u8], p5: &[u8]) -> u8 {
    let z2 = code / 15;
    let remainder = code % 15;
    let z3 = remainder / 5;
    let z5 = remainder % 5;
    ((15 * p2[z2 as usize] as u16 + 10 * p3[z3 as usize] as u16 + 6 * p5[z5 as usize] as u16) % 30)
        as u8
}

struct Score {
    best_matches: u64,
    best_ids: Vec<String>,
    exact_ids: Vec<String>,
    matrix: [[[u64; 30]; 30]; 8],
}

fn score(records: &[Record], r: u64, generator_index: u64, labels: &[u8]) -> Score {
    let mut matrix = [[[0u64; 30]; 30]; 8];
    for scalar in 1..r {
        let f = features(records, r, generator_index, scalar);
        for channel in 0..8 {
            matrix[channel][f[channel] as usize][labels[(scalar - 1) as usize] as usize] += 1;
        }
    }
    let mut best_matches = 0;
    let mut best_ids = Vec::new();
    let mut exact_ids = Vec::new();
    let permutations2 = permutations(2);
    let permutations3 = permutations(3);
    let permutations5 = permutations(5);
    for channel in 0..8 {
        for p2 in &permutations2 {
            for p3 in &permutations3 {
                for p5 in &permutations5 {
                    let matches = (0..30)
                        .map(|code| {
                            matrix[channel][code][mapped_digit(code as u8, p2, p3, p5) as usize]
                        })
                        .sum();
                    let id = predicate_id(channel, p2, p3, p5);
                    if matches > best_matches {
                        best_matches = matches;
                        best_ids = vec![id.clone()];
                    } else if matches == best_matches {
                        best_ids.push(id.clone());
                    }
                    if matches == r - 1 {
                        exact_ids.push(id);
                    }
                }
            }
        }
    }
    Score {
        best_matches,
        best_ids,
        exact_ids,
        matrix,
    }
}

fn canonical_labels(r: u64) -> Vec<u8> {
    (1..r).map(|k| (k % 30) as u8).collect()
}

fn shuffled_labels(curve: Curve, generator_multiplier: u64, replicate: u64) -> Vec<u8> {
    let mut labels = canonical_labels(curve.r);
    let mut state = control_seed(
        "H114/label-shuffle/v1",
        curve,
        generator_multiplier,
        replicate,
    ) ^ LABEL_DOMAIN;
    for i in (1..labels.len()).rev() {
        state = state.wrapping_add(MIX_INC);
        let mut z = state;
        z = (z ^ (z >> 30)).wrapping_mul(MIX_M1);
        z = (z ^ (z >> 27)).wrapping_mul(MIX_M2);
        z ^= z >> 31;
        labels.swap(i, (z % (i as u64 + 1)) as usize);
    }
    labels
}

fn parse_u64(text: &str, context: &str) -> Result<u64, String> {
    text.parse()
        .map_err(|_| format!("invalid u64 {text:?} in {context}"))
}

fn parse_i64(text: &str, context: &str) -> Result<i64, String> {
    text.parse()
        .map_err(|_| format!("invalid i64 {text:?} in {context}"))
}

fn expected_base(curve: Curve, tag: &str, bases: &HashMap<String, Point>) -> Result<Point, String> {
    if let Some(base) = bases.get(curve.slug) {
        return Ok(*base);
    }
    let original = CURVES
        .iter()
        .find(|c| c.slug == tag)
        .ok_or_else(|| format!("ISO tag {tag} is not a primary curve"))?;
    let base = *bases
        .get(original.slug)
        .ok_or("ISO row appeared before its primary curve")?;
    let mapped = Point {
        x: base.x * 4 % curve.p,
        y: base.y * 8 % curve.p,
    };
    if !on_curve(curve, mapped, curve.p) {
        return fail("mapped ISO base is off curve");
    }
    Ok(mapped)
}

fn extract_json_string(json: &str, key: &str) -> Result<String, String> {
    let marker = format!("\"{}\": \"", key);
    let start = json
        .find(&marker)
        .ok_or_else(|| format!("summary missing {key}"))?
        + marker.len();
    let end = json[start..]
        .find('"')
        .ok_or_else(|| format!("unterminated summary field {key}"))?
        + start;
    Ok(json[start..end].to_string())
}

fn extract_json_u64(json: &str, key: &str) -> Result<u64, String> {
    let marker = format!("\"{}\": ", key);
    let start = json
        .find(&marker)
        .ok_or_else(|| format!("summary missing {key}"))?
        + marker.len();
    let end = json[start..]
        .find(|c: char| !c.is_ascii_digit())
        .unwrap_or(json.len() - start)
        + start;
    parse_u64(&json[start..end], key)
}

fn extract_json_string_array(json: &str, key: &str) -> Result<Vec<String>, String> {
    let marker = format!("\"{}\": [", key);
    let start = json
        .find(&marker)
        .ok_or_else(|| format!("summary missing {key}"))?
        + marker.len();
    let end = json[start..]
        .find(']')
        .ok_or_else(|| format!("unterminated summary array {key}"))?
        + start;
    let body = json[start..end].trim();
    if body.is_empty() {
        return Ok(Vec::new());
    }
    body.split(',')
        .map(|item| {
            let item = item.trim();
            if item.len() < 2 || !item.starts_with('"') || !item.ends_with('"') {
                fail(format!("malformed string in summary array {key}"))
            } else {
                Ok(item[1..item.len() - 1].to_string())
            }
        })
        .collect()
}

fn dataset_key(kind: &str, slug: &str, tag: &str) -> String {
    format!("{kind}\t{slug}\t{tag}")
}

fn joined(values: &[String]) -> String {
    if values.is_empty() {
        "-".to_string()
    } else {
        values.join(",")
    }
}

fn verify(raw: &[u8], summary: &str) -> Result<String, String> {
    let text = std::str::from_utf8(raw).map_err(|_| "raw result is not UTF-8")?;
    let lines: Vec<&str> = text.lines().collect();
    if lines.first() != Some(&"H114_RESULT_V1") {
        return fail("wrong raw schema header");
    }
    if lines.get(1) != Some(&format!("PROTOCOL_SHA256\t{}", PROTOCOL_SHA256).as_str()) {
        return fail("raw protocol digest mismatch");
    }
    let mode = lines
        .get(2)
        .and_then(|x| x.strip_prefix("MODE\t"))
        .ok_or("missing raw mode")?;
    if mode != "quick" && mode != "full" {
        return fail("unknown raw mode");
    }
    if extract_json_string(summary, "schema")? != "h114.multiradix-carry-cohomology.result/v1"
        || extract_json_string(summary, "mode")? != mode
        || extract_json_u64(summary, "predicate_count")? != 11_520
    {
        return fail("summary schema, mode, or predicate count mismatch");
    }
    if extract_json_string(summary, "protocol_sha256")? != PROTOCOL_SHA256 {
        return fail("summary protocol digest mismatch");
    }
    let digest = hex(&sha256(raw));
    if extract_json_string(summary, "scientific_payload_sha256")? != digest {
        return fail("scientific payload digest mismatch");
    }
    if extract_json_u64(summary, "raw_bytes")? != raw.len() as u64 {
        return fail("summary raw byte count mismatch");
    }

    let mut bases: HashMap<String, Point> = HashMap::new();
    let mut datasets: HashMap<String, Dataset> = HashMap::new();
    let mut matrices: HashMap<String, String> = HashMap::new();
    let mut row_sets: Vec<BTreeSet<String>> = Vec::new();
    let mut row_identities: Vec<(Curve, u64)> = Vec::new();
    let mut curve_rows = 0u64;
    let mut targets = 0u64;
    let mut rows_with_exact = 0u64;
    let mut rows_decoded = 0u64;
    let mut decoded_targets = 0u64;
    let mut final_seen = false;
    let mut uniform_decode_receipts = BTreeSet::new();
    let mut kind_counts: HashMap<String, u64> = HashMap::new();

    for (zero_index, line) in lines.iter().enumerate().skip(3) {
        let line_no = zero_index + 1;
        let f: Vec<&str> = line.split('\t').collect();
        *kind_counts.entry(f[0].to_string()).or_default() += 1;
        match f[0] {
            "CURVE" => {
                if f.len() != 9 {
                    return fail(format!("line {line_no}: CURVE has {} fields", f.len()));
                }
                let curve = curve_by_slug(f[1])?;
                if f[2] != curve.icv1
                    || parse_u64(f[3], "p")? != curve.p
                    || parse_u64(f[4], "a")? != curve.a
                    || parse_u64(f[5], "b")? != curve.b
                    || parse_u64(f[6], "r")? != curve.r
                {
                    return fail(format!(
                        "line {line_no}: curve metadata differs from freeze"
                    ));
                }
                let base = Point {
                    x: parse_u64(f[7], "base x")?,
                    y: parse_u64(f[8], "base y")?,
                };
                if base != first_point(curve)? {
                    return fail(format!(
                        "line {line_no}: base is not lexicographically first"
                    ));
                }
                if bases.insert(curve.slug.to_string(), base).is_some() {
                    return fail("duplicate CURVE line");
                }
            }
            "CANON" | "RANDOM" | "ISO" | "TORSION" => {
                if f.len() != 22 {
                    return fail(format!("line {line_no}: record has {} fields", f.len()));
                }
                let curve = curve_by_slug(f[1])?;
                let tag = f[2];
                let scalar = parse_u64(f[3], "scalar")?;
                if scalar == 0 || scalar >= curve.r {
                    return fail(format!("line {line_no}: scalar out of range"));
                }
                let point = Point {
                    x: parse_u64(f[4], "x")?,
                    y: parse_u64(f[5], "y")?,
                };
                let base = expected_base(curve, tag, &bases)?;
                if ec_mul(curve, scalar, Some(base), curve.p)? != Some(point) {
                    return fail(format!("line {line_no}: point/scalar label mismatch"));
                }
                let section = match f[0] {
                    "CANON" | "ISO" => Section::Canonical,
                    "RANDOM" => Section::Random {
                        generator_multiplier: 1,
                        replicate: parse_u64(tag, "random replicate")?,
                    },
                    "TORSION" => Section::Torsion,
                    _ => unreachable!(),
                };
                let got = winding(curve, point, section)?;
                let stated = Record {
                    k2: parse_u64(f[6], "k2")?,
                    k3: parse_u64(f[7], "k3")?,
                    k5: parse_u64(f[8], "k5")?,
                    n23: parse_i64(f[9], "n23")?,
                    n25: parse_i64(f[10], "n25")?,
                    n35: parse_i64(f[11], "n35")?,
                    w23: parse_i64(f[12], "w23")?,
                    w25: parse_i64(f[13], "w25")?,
                    w35: parse_i64(f[14], "w35")?,
                    heights: [
                        parse_i64(f[15], "K235")?,
                        parse_i64(f[16], "K253")?,
                        parse_i64(f[17], "K325")?,
                        parse_i64(f[18], "K352")?,
                        parse_i64(f[19], "K523")?,
                        parse_i64(f[20], "K532")?,
                    ],
                    braid_residual: parse_i64(f[21], "braid residual")?,
                };
                if got != stated {
                    return fail(format!(
                        "line {line_no}: independently recomputed winding record differs"
                    ));
                }
                if f[0] == "TORSION" && stated != Record::default() {
                    return fail("torsion control is nonzero");
                }
                let key = dataset_key(f[0], curve.slug, tag);
                let data = datasets.entry(key).or_insert_with(|| Dataset::new(curve.r));
                if data.seen[scalar as usize] {
                    return fail(format!("line {line_no}: duplicate scalar record"));
                }
                data.seen[scalar as usize] = true;
                data.values[scalar as usize] = stated;
            }
            "ROW" | "RANDOM_ROW" | "LABEL_ROW" | "ISO_ROW" => {
                if f.len() != 8 {
                    return fail(format!("line {line_no}: score has {} fields", f.len()));
                }
                let curve = curve_by_slug(f[1])?;
                let (data_kind, data_tag, generator_index, labels) = match f[0] {
                    "ROW" => (
                        "CANON",
                        "0",
                        parse_u64(f[2], "generator multiplier")?,
                        canonical_labels(curve.r),
                    ),
                    "RANDOM_ROW" => ("RANDOM", f[2], 1, canonical_labels(curve.r)),
                    "LABEL_ROW" => (
                        "CANON",
                        "0",
                        1,
                        shuffled_labels(curve, 1, parse_u64(f[2], "label replicate")?),
                    ),
                    "ISO_ROW" => ("ISO", f[2], 1, canonical_labels(curve.r)),
                    _ => unreachable!(),
                };
                let data = datasets
                    .get(&dataset_key(data_kind, curve.slug, data_tag))
                    .ok_or_else(|| format!("line {line_no}: score precedes its records"))?;
                if data.seen.iter().skip(1).any(|seen| !seen) {
                    return fail(format!("line {line_no}: incomplete dataset"));
                }
                let computed = score(&data.values, curve.r, generator_index, &labels);
                if parse_u64(f[3], "best matches")? != computed.best_matches
                    || parse_u64(f[4], "score targets")? != curve.r - 1
                    || parse_u64(f[5], "best ID count")? != computed.best_ids.len() as u64
                    || f[6] != joined(&computed.best_ids)
                    || f[7] != joined(&computed.exact_ids)
                {
                    return fail(format!("line {line_no}: score or predicate IDs differ"));
                }
                for channel in 0..8 {
                    let flat = computed.matrix[channel]
                        .iter()
                        .flat_map(|row| row.iter())
                        .map(u64::to_string)
                        .collect::<Vec<_>>()
                        .join(",");
                    matrices.insert(
                        format!("{}\t{}\t{}\t{}", f[0], curve.slug, f[2], CHANNELS[channel]),
                        flat,
                    );
                }
                if f[0] == "ROW" {
                    curve_rows += 1;
                    targets += curve.r - 1;
                    if !computed.exact_ids.is_empty() {
                        rows_with_exact += 1;
                        rows_decoded += 1;
                    }
                    row_sets.push(computed.exact_ids.iter().cloned().collect());
                    row_identities.push((curve, generator_index));
                    let base = *bases.get(curve.slug).ok_or("ROW lacks primary base")?;
                    let generator = ec_mul(curve, generator_index, Some(base), curve.p)?.unwrap();
                    for id in &computed.exact_ids {
                        for scalar in 1..curve.r {
                            let target = ec_mul(curve, scalar, Some(generator), curve.p)?.unwrap();
                            if decode(curve, generator, target, id)? != scalar {
                                return fail("conditional decoder returned the wrong scalar");
                            }
                            decoded_targets += 1;
                        }
                    }
                }
            }
            "MATRIX" => {
                if f.len() != 6 {
                    return fail(format!("line {line_no}: MATRIX has {} fields", f.len()));
                }
                let key = format!("{}\t{}\t{}\t{}", f[1], f[2], f[3], f[4]);
                let expected = matrices
                    .remove(&key)
                    .ok_or_else(|| format!("line {line_no}: unexpected matrix"))?;
                if f[5] != expected || f[5].split(',').count() != 900 {
                    return fail(format!("line {line_no}: contingency matrix differs"));
                }
            }
            "COUNTS" => {
                if f.len() != 4 {
                    return fail(format!("line {line_no}: COUNTS has {} fields", f.len()));
                }
                curve_by_slug(f[1])?;
                for value in &f[2..] {
                    if !value.starts_with('{')
                        || !value.ends_with('}')
                        || !value.contains("\"kappa_evaluations\":")
                        || !value.contains("\"braid_checks\":")
                        || !value.contains("\"crt_evaluations\":")
                    {
                        return fail(format!("line {line_no}: malformed operation counts"));
                    }
                }
            }
            "UNIFORM_DECODE" => {
                if f.len() != 5 {
                    return fail(format!(
                        "line {line_no}: UNIFORM_DECODE has {} fields",
                        f.len()
                    ));
                }
                let curve = curve_by_slug(f[1])?;
                let multiplier = parse_u64(f[2], "uniform multiplier")?;
                if ![1, 2, 3, 5].contains(&multiplier) {
                    return fail(format!("line {line_no}: unknown uniform multiplier"));
                }
                parse_predicate(f[3])?;
                if parse_u64(f[4], "uniform target count")? != curve.r - 1 {
                    return fail(format!("line {line_no}: uniform target count differs"));
                }
                let receipt = format!("{}\t{}\t{}\t{}", f[1], f[2], f[3], f[4]);
                if !uniform_decode_receipts.insert(receipt) {
                    return fail(format!("line {line_no}: duplicate uniform receipt"));
                }
            }
            "FINAL" => {
                if f.len() != 9 {
                    return fail(format!("line {line_no}: FINAL has {} fields", f.len()));
                }
                if final_seen {
                    return fail("duplicate FINAL line");
                }
                final_seen = true;
                let uniform = row_sets
                    .iter()
                    .cloned()
                    .reduce(|a, b| a.intersection(&b).cloned().collect())
                    .unwrap_or_default();
                let uniform_rows = curve_rows * uniform.len() as u64;
                let uniform_targets = uniform.len() as u64 * targets;
                let expected = [
                    curve_rows,
                    targets,
                    rows_with_exact,
                    uniform.len() as u64,
                    rows_decoded,
                    decoded_targets,
                    uniform_rows,
                    uniform_targets,
                ];
                for (index, value) in expected.iter().enumerate() {
                    if parse_u64(f[index + 1], "FINAL")? != *value {
                        return fail(format!("line {line_no}: FINAL field {} differs", index + 1));
                    }
                }
                let mut expected_receipts = BTreeSet::new();
                for (curve, multiplier) in &row_identities {
                    for predicate in &uniform {
                        expected_receipts.insert(format!(
                            "{}\t{}\t{}\t{}",
                            curve.slug,
                            multiplier,
                            predicate,
                            curve.r - 1
                        ));
                    }
                }
                if uniform_decode_receipts != expected_receipts {
                    return fail("uniform decoder receipt set mismatch");
                }
            }
            other => return fail(format!("line {line_no}: unknown record kind {other}")),
        }
    }
    if !final_seen || !matrices.is_empty() {
        return fail("missing FINAL or MATRIX records");
    }
    for (key, data) in &datasets {
        if data.seen.iter().skip(1).any(|seen| !seen) {
            return fail(format!("incomplete dataset {key}"));
        }
    }
    let expected_curves = if mode == "quick" { 1 } else { 7 };
    let expected_rows = if mode == "quick" { 1 } else { 28 };
    let expected_targets = if mode == "quick" { 82 } else { 9_096 };
    let expected_controls = if mode == "quick" { 1 } else { 16 };
    let expected_iso = if mode == "quick" { 1 } else { 2 };
    let count = |kind: &str| *kind_counts.get(kind).unwrap_or(&0);
    if bases.len() != expected_curves
        || curve_rows != expected_rows
        || targets != expected_targets
        || count("RANDOM_ROW") != expected_controls
        || count("LABEL_ROW") != expected_controls
        || count("ISO_ROW") != expected_iso
        || count("COUNTS") != expected_curves as u64
        || count("FINAL") != 1
    {
        return fail("mode-specific cohort or control cardinality mismatch");
    }
    let uniform: BTreeSet<String> = row_sets
        .iter()
        .cloned()
        .reduce(|a, b| a.intersection(&b).cloned().collect())
        .unwrap_or_default();
    let summary_uniform: BTreeSet<String> =
        extract_json_string_array(summary, "uniform_exact_predicate_ids")?
            .into_iter()
            .collect();
    if summary_uniform != uniform {
        return fail("summary uniform exact-ID set differs");
    }
    if extract_json_u64(summary, "curve_rows")? != curve_rows
        || extract_json_u64(summary, "targets")? != targets
        || extract_json_u64(summary, "rows_with_exact_predicate")? != rows_with_exact
        || extract_json_u64(summary, "rows_decoded")? != rows_decoded
        || extract_json_u64(summary, "decoded_targets")? != decoded_targets
        || extract_json_u64(summary, "uniform_rows_decoded")? != curve_rows * uniform.len() as u64
        || extract_json_u64(summary, "uniform_decoded_targets")? != uniform.len() as u64 * targets
    {
        return fail("summary aggregate differs from verified raw data");
    }
    if !summary.contains("\"all_structural_checks_passed\": true")
        || !summary.contains("\"all_torsion_carries_zero\": true")
    {
        return fail("summary structural booleans are not true");
    }
    Ok(format!("verified mode={mode} curve_rows={curve_rows} targets={targets} rows_with_exact={rows_with_exact} sha256={digest}"))
}

fn parse_permutation(text: &str, size: usize) -> Result<Vec<u8>, String> {
    if text.len() != size {
        return fail("predicate permutation has wrong length");
    }
    let mut values = text
        .bytes()
        .map(|byte| byte.wrapping_sub(b'0'))
        .collect::<Vec<_>>();
    if values.iter().any(|value| *value >= size as u8) {
        return fail("predicate permutation contains an invalid digit");
    }
    let original = values.clone();
    values.sort_unstable();
    if values != (0..size as u8).collect::<Vec<_>>() {
        return fail("predicate limb is not a permutation");
    }
    Ok(original)
}

fn parse_predicate(id: &str) -> Result<(usize, Vec<u8>, Vec<u8>, Vec<u8>), String> {
    let pieces: Vec<&str> = id.split(':').collect();
    if pieces.len() != 8
        || pieces[0] != "channel"
        || pieces[2] != "pi2"
        || pieces[4] != "pi3"
        || pieces[6] != "pi5"
    {
        return fail("malformed predicate ID");
    }
    let channel = CHANNELS
        .iter()
        .position(|name| *name == pieces[1])
        .ok_or("unknown channel")?;
    Ok((
        channel,
        parse_permutation(pieces[3], 2)?,
        parse_permutation(pieces[5], 3)?,
        parse_permutation(pieces[7], 5)?,
    ))
}

fn public_digit(
    curve: Curve,
    generator: Point,
    target: Point,
    predicate: &str,
) -> Result<u8, String> {
    let plus = ec_add(curve, Some(target), Some(generator), curve.p)?;
    let minus = ec_add(
        curve,
        Some(target),
        negative(Some(generator), curve.p),
        curve.p,
    )?;
    let w = |point: Option<Point>| -> Result<(i64, i64, i64), String> {
        match point {
            None => Ok((0, 0, 0)),
            Some(q) => {
                let record = winding(curve, q, Section::Canonical)?;
                Ok((record.w23, record.w25, record.w35))
            }
        }
    };
    let wq = w(Some(target))?;
    let wp = w(plus)?;
    let wm = w(minus)?;
    let wg = w(Some(generator))?;
    let wng = w(negative(Some(generator), curve.p))?;
    let c35 = channel_values(wq.2, wp.2, wm.2, wg.2, wng.2);
    let c25 = channel_values(wq.1, wp.1, wm.1, wg.1, wng.1);
    let c23 = channel_values(wq.0, wp.0, wm.0, wg.0, wng.0);
    let (channel, p2, p3, p5) = parse_predicate(predicate)?;
    Ok(((15 * p2[c35[channel].rem_euclid(2) as usize] as u16
        + 10 * p3[c25[channel].rem_euclid(3) as usize] as u16
        + 6 * p5[c23[channel].rem_euclid(5) as usize] as u16)
        % 30) as u8)
}

fn inverse_thirty_certificate(curve: Curve) -> Result<(u64, u64), String> {
    let inv30 = inverse(30, curve.r)?;
    let inverse_product = inv30
        .checked_mul(30)
        .ok_or("inverse-thirty certificate overflow")?;
    if inverse_product % curve.r != 1 {
        return fail("inverse-thirty residue certificate failed");
    }
    let inverse_quotient = (inverse_product - 1) / curve.r;
    if inverse_product != 1 + inverse_quotient * curve.r {
        return fail("inverse-thirty integer certificate failed");
    }
    Ok((inv30, inverse_quotient))
}

fn decode(curve: Curve, generator: Point, target: Point, predicate: &str) -> Result<u64, String> {
    let (inv30, _) = inverse_thirty_certificate(curve)?;
    let mut current = Some(target);
    let mut answer = 0u64;
    let mut place = 1u64;
    let mut queries = 0u32;
    while let Some(q) = current {
        if queries > 1 + curve.r.ilog(30) {
            return fail("decoder exceeded radix-thirty bound");
        }
        let digit = public_digit(curve, generator, q, predicate)? as u64;
        current = ec_add(
            curve,
            current,
            negative(ec_mul(curve, digit, Some(generator), curve.p)?, curve.p),
            curve.p,
        )?;
        current = ec_mul(curve, inv30, current, curve.p)?;
        answer += digit * place;
        place *= 30;
        queries += 1;
    }
    if answer >= curve.r || ec_mul(curve, answer, Some(generator), curve.p)? != Some(target) {
        return fail("decoder final EC check failed");
    }
    Ok(answer)
}

fn replace_json_string(json: &str, key: &str, value: &str) -> Result<String, String> {
    let marker = format!("\"{}\": \"", key);
    let start = json
        .find(&marker)
        .ok_or_else(|| format!("summary missing {key}"))?
        + marker.len();
    let end = json[start..]
        .find('"')
        .ok_or_else(|| format!("unterminated summary field {key}"))?
        + start;
    let mut out = json.to_string();
    out.replace_range(start..end, value);
    Ok(out)
}

fn replace_json_u64(json: &str, key: &str, value: u64) -> Result<String, String> {
    let marker = format!("\"{}\": ", key);
    let start = json
        .find(&marker)
        .ok_or_else(|| format!("summary missing {key}"))?
        + marker.len();
    let end = json[start..]
        .find(|c: char| !c.is_ascii_digit())
        .unwrap_or(json.len() - start)
        + start;
    let mut out = json.to_string();
    out.replace_range(start..end, &value.to_string());
    Ok(out)
}

fn bind_summary_to_raw(summary: &str, raw: &[u8]) -> Result<String, String> {
    let rebound = replace_json_string(summary, "scientific_payload_sha256", &hex(&sha256(raw)))?;
    replace_json_u64(&rebound, "raw_bytes", raw.len() as u64)
}

fn require_rejection(name: &str, raw: &[u8], summary: &str) -> Result<(), String> {
    if verify(raw, summary).is_ok() {
        return fail(format!("{name} tamper was accepted"));
    }
    Ok(())
}

fn tamper_test(raw: &[u8], summary: &str) -> Result<(), String> {
    verify(raw, summary)?;
    let text = std::str::from_utf8(raw).map_err(|_| "raw result is not UTF-8")?;
    let mut lines: Vec<String> = text.lines().map(str::to_string).collect();
    let record_index = lines
        .iter()
        .position(|line| line.starts_with("CANON\t"))
        .ok_or("no CANON row for tamper test")?;
    let original = lines[record_index].clone();
    let mut fields: Vec<String> = original.split('\t').map(str::to_string).collect();
    fields[15] = (parse_i64(&fields[15], "tamper path coefficient")? + 1).to_string();
    lines[record_index] = fields.join("\t");
    let path_tamper = format!("{}\n", lines.join("\n"));
    let path_summary = bind_summary_to_raw(summary, path_tamper.as_bytes())?;
    require_rejection("path-coefficient", path_tamper.as_bytes(), &path_summary)?;

    lines[record_index] = original.clone();
    let mut fields: Vec<String> = lines[record_index]
        .split('\t')
        .map(str::to_string)
        .collect();
    fields[3] = (parse_u64(&fields[3], "tamper label")? + 1).to_string();
    lines[record_index] = fields.join("\t");
    let label_tamper = format!("{}\n", lines.join("\n"));
    let label_summary = bind_summary_to_raw(summary, label_tamper.as_bytes())?;
    require_rejection("scalar-label", label_tamper.as_bytes(), &label_summary)?;

    lines[record_index] = original;
    let score_index = lines
        .iter()
        .position(|line| line.starts_with("ROW\t"))
        .ok_or("no ROW for CRT tamper test")?;
    let score_original = lines[score_index].clone();
    let mut score_fields = score_original
        .split('\t')
        .map(str::to_string)
        .collect::<Vec<_>>();
    score_fields[6] = if score_fields[6].contains("pi2:01") {
        score_fields[6].replacen("pi2:01", "pi2:00", 1)
    } else {
        score_fields[6].replacen("pi2:10", "pi2:11", 1)
    };
    if score_fields[6] == score_original.split('\t').nth(6).unwrap() {
        return fail("could not construct CRT-limb tamper");
    }
    lines[score_index] = score_fields.join("\t");
    let crt_tamper = format!("{}\n", lines.join("\n"));
    let crt_summary = bind_summary_to_raw(summary, crt_tamper.as_bytes())?;
    require_rejection("CRT-limb", crt_tamper.as_bytes(), &crt_summary)?;

    let digest_tamper = replace_json_string(summary, "scientific_payload_sha256", &"0".repeat(64))?;
    require_rejection("digest", raw, &digest_tamper)?;
    let rows = extract_json_u64(summary, "curve_rows")?;
    let count_tamper = replace_json_u64(summary, "curve_rows", rows + 1)?;
    require_rejection("summary-count", raw, &count_tamper)?;
    Ok(())
}

fn self_test() -> Result<(), String> {
    if permutations(2).len() != 2 || permutations(3).len() != 6 || permutations(5).len() != 120 {
        return fail("permutation enumerator produced the wrong limb count");
    }
    let mut ids = BTreeSet::new();
    for channel in 0..CHANNELS.len() {
        for p2 in permutations(2) {
            for p3 in permutations(3) {
                for p5 in permutations(5) {
                    let id = predicate_id(channel, &p2, &p3, &p5);
                    let parsed = parse_predicate(&id)?;
                    if parsed != (channel, p2.clone(), p3.clone(), p5.clone()) {
                        return fail("predicate ID did not round-trip");
                    }
                    if !ids.insert(id) {
                        return fail("duplicate predicate ID");
                    }
                }
            }
        }
    }
    if ids.len() != 11_520 {
        return fail("predicate family does not contain 11,520 unique IDs");
    }
    for z2 in 0..2u8 {
        for z3 in 0..3u8 {
            for z5 in 0..5u8 {
                let digit = ((15 * z2 as u16 + 10 * z3 as u16 + 6 * z5 as u16) % 30) as u8;
                if digit % 2 != z2 || digit % 3 != z3 || digit % 5 != z5 {
                    return fail("CRT residue self-test failed");
                }
            }
        }
    }
    if hex(&sha256(b"abc")) != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad" {
        return fail("SHA-256 known-answer test failed");
    }
    let curve = CURVES[0];
    if inverse_thirty_certificate(curve)? != (36, 13) {
        return fail("unexpected inverse-thirty certificate fixture");
    }
    let base = first_point(curve)?;
    let record = winding(curve, base, Section::Canonical)?;
    if record.w23 != -1
        || record.w25 != 1
        || record.w35 != 0
        || record.n23 != -(curve.p as i64)
        || record.braid_residual != 0
    {
        return fail(format!("unexpected independent fixture {record:?}"));
    }
    let mut tampered = record;
    tampered.k2 += 1;
    if tampered == winding(curve, base, Section::Canonical)? {
        return fail("coefficient mutation was not distinguished");
    }
    let labels = canonical_labels(curve.r);
    let mut changed = labels.clone();
    changed[0] = (changed[0] + 1) % 30;
    if labels == changed {
        return fail("label mutation was not distinguished");
    }
    println!(
        "self-test ok: {} base=({}, {}) record={:?}",
        curve.slug, base.x, base.y, record
    );
    Ok(())
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn sha256(input: &[u8]) -> [u8; 32] {
    const INITIAL: [u32; 8] = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab,
        0x5be0cd19,
    ];
    const ROUND: [u32; 64] = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
        0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
        0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
        0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
        0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
        0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
        0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
        0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
        0xc67178f2,
    ];
    let mut padded = input.to_vec();
    let bit_len = (padded.len() as u64) * 8;
    padded.push(0x80);
    while padded.len() % 64 != 56 {
        padded.push(0);
    }
    padded.extend_from_slice(&bit_len.to_be_bytes());
    let mut state = INITIAL;
    for block in padded.chunks_exact(64) {
        let mut words = [0u32; 64];
        for i in 0..16 {
            words[i] = u32::from_be_bytes(block[4 * i..4 * i + 4].try_into().unwrap());
        }
        for i in 16..64 {
            let s0 = words[i - 15].rotate_right(7)
                ^ words[i - 15].rotate_right(18)
                ^ (words[i - 15] >> 3);
            let s1 = words[i - 2].rotate_right(17)
                ^ words[i - 2].rotate_right(19)
                ^ (words[i - 2] >> 10);
            words[i] = words[i - 16]
                .wrapping_add(s0)
                .wrapping_add(words[i - 7])
                .wrapping_add(s1);
        }
        let mut v = state;
        for i in 0..64 {
            let big1 = v[4].rotate_right(6) ^ v[4].rotate_right(11) ^ v[4].rotate_right(25);
            let choose = (v[4] & v[5]) ^ ((!v[4]) & v[6]);
            let t1 = v[7]
                .wrapping_add(big1)
                .wrapping_add(choose)
                .wrapping_add(ROUND[i])
                .wrapping_add(words[i]);
            let big0 = v[0].rotate_right(2) ^ v[0].rotate_right(13) ^ v[0].rotate_right(22);
            let majority = (v[0] & v[1]) ^ (v[0] & v[2]) ^ (v[1] & v[2]);
            let t2 = big0.wrapping_add(majority);
            v = [
                t1.wrapping_add(t2),
                v[0],
                v[1],
                v[2],
                v[3].wrapping_add(t1),
                v[4],
                v[5],
                v[6],
            ];
        }
        for i in 0..8 {
            state[i] = state[i].wrapping_add(v[i]);
        }
    }
    let mut out = [0u8; 32];
    for (i, word) in state.iter().enumerate() {
        out[4 * i..4 * i + 4].copy_from_slice(&word.to_be_bytes());
    }
    out
}

fn real_main() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    if args.len() == 2 && args[1] == "--self-test" {
        return self_test();
    }
    let (tamper, raw_path, summary_path) =
        match args.as_slice() {
            [_, raw, summary] => (false, raw, summary),
            [_, flag, raw, summary] if flag == "--tamper-test" => (true, raw, summary),
            _ => return fail(
                "usage: h114_multiradix_verify [--tamper-test] RAW.tsv SUMMARY.json | --self-test",
            ),
        };
    let raw = fs::read(raw_path).map_err(|e| format!("read {raw_path}: {e}"))?;
    let summary =
        fs::read_to_string(summary_path).map_err(|e| format!("read {summary_path}: {e}"))?;
    let receipt = verify(&raw, &summary)?;
    if tamper {
        tamper_test(&raw, &summary)?;
        println!(
            "{receipt} tamper_tests=path-coefficient,crt-limb,scalar-label,digest,summary-count:rejected"
        );
    } else {
        println!("{receipt}");
    }
    Ok(())
}

fn main() {
    if let Err(error) = real_main() {
        eprintln!("H114 verification failed: {error}");
        std::process::exit(1);
    }
}
