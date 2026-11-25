use crate::cm::{self, Action, H, R, S, T};
use crate::ec::{self, Group};
use crate::field::{self, Encoding, F, ONE, Q, ZERO};
use crate::geometry;
use crate::packet::{Packet, Reader};
use crate::{need, AResult};
use std::collections::BTreeSet;

fn division_factor(x: F) -> F {
    [1, 0, 3, 1, 1, 1, 5]
        .into_iter()
        .fold(ZERO, |a, n| a.times(x).plus(F::prime(n)))
}
fn root_bitset(bytes: &[u8], encoding: &Encoding) -> AResult<()> {
    need(
        bytes.len() == (Q as usize).div_ceil(8),
        "whole division bitset length",
    )?;
    need(
        bytes.last().copied().ok_or("division bitset empty")? & 0xfe == 0,
        "division bitset unused tail bits",
    )?;
    let mut roots = Vec::new();
    for (index, &byte) in bytes.iter().enumerate() {
        for bit in 0..8 {
            if byte & (1 << bit) != 0 {
                roots.push((index * 8 + bit) as u32);
            }
        }
    }
    need(roots.len() == 6, "six-root degree-bound cohort")?;
    for &root in &roots {
        need(
            division_factor(encoding.decode(root)?) == ZERO,
            "marked actual division root",
        )?;
    }
    // Six distinct encoded roots of a monic degree-six polynomial in the
    // qualified field prove all other bit decisions without a field search.
    println!("WHOLE_ROOT_BITSET\tbits=117649\tsix_marked_roots={roots:?}\tdegree_bound_no_field_scan\tPASS");
    Ok(())
}
fn group_cm(g: &Group) -> AResult<()> {
    for p in 0..g.points.len() {
        let w = g.omega(p);
        let ww = g.omega(w);
        need(
            g.plus[g.plus[ww][g.negative[w]]][g.scalar(p, 5)] == 0,
            "actual omega quadratic relation",
        )?;
    }
    Ok(())
}
fn e4(packet: &Packet<'_>, encoding: &Encoding) -> AResult<(Group, Vec<u8>)> {
    root_bitset(packet.section(b"E4XS").bytes, encoding)?;
    let points = ec::read_points(packet.section(b"E4PT").bytes, 16, encoding)?;
    let group = Group::new(points, 4)?;
    group.addition_records(packet.section(b"E4AD").bytes)?;
    group_cm(&group)?;
    let mut records = Reader::new(packet.section(b"E4FR").bytes);
    for p in 0..16 {
        need(
            usize::from(records.u8()?) == group.frobenius[p],
            "actual E4 Frobenius record",
        )?;
        need(
            usize::from(records.u8()?) == group.negative[p],
            "actual E4 negative record",
        )?;
        need(
            usize::from(records.u8()?) == group.scalar(p, 2),
            "actual E4 double record",
        )?;
    }
    records.end()?;
    need(
        (0..16).filter(|&p| group.scalar(p, 2) == 0).count() == 4,
        "full actual E2 subgroup",
    )?;
    let mut span = BTreeSet::new();
    for i in 0..4 {
        for j in 0..4 {
            span.insert(group.plus[group.scalar(4, i)][group.scalar(6, j)]);
        }
    }
    need(span.len() == 16, "actual E4 full fixed basis")?;
    let t = Some((F::prime(1), F::prime(3)));
    need(
        ec::valid(t) && ec::times(t, 11).is_none(),
        "actual order11 moving point",
    )?;
    let auxiliary = ec::times(t, 3);
    need(
        auxiliary.is_some() && auxiliary != t && auxiliary != ec::times(t, 2),
        "third moving divisor auxiliary",
    )?;
    let i = encoding.decode(1029)?;
    need(
        i.pow(2) == F::prime(-1) && i != ONE && i != F::prime(-1),
        "same actual primitive fourth root",
    )?;
    let powers = [ONE, i, i.pow(2), i.pow(3)];
    let stored = packet.section(b"E4WP").bytes;
    let mut pairings = Vec::new();
    for p in 0..16 {
        for q in 0..16 {
            let actual = ec::weil4(group.points[p], group.points[q], auxiliary)
                .ok_or("generic Miller moving support intersects")?;
            let exponent = powers
                .iter()
                .position(|&value| value == actual)
                .ok_or("Miller value not fourth root")? as u8;
            need(
                stored[p * 16 + q] == exponent,
                "actual third-auxiliary Weil record differs",
            )?;
            pairings.push(exponent);
        }
    }
    for p in 0..16 {
        need(pairings[p * 16 + p] == 0, "Weil alternating")?;
        need(
            p == 0 || pairings[p * 16..p * 16 + 16].iter().any(|&e| e != 0),
            "Weil nondegenerate",
        )?;
        for q in 0..16 {
            need(
                (pairings[p * 16 + q] + pairings[q * 16 + p]) % 4 == 0,
                "Weil skew symmetry",
            )?;
            need(
                pairings[group.frobenius[p] * 16 + group.frobenius[q]]
                    == (7 * pairings[p * 16 + q]) % 4,
                "Weil Frobenius7 covariance",
            )?;
            for r in 0..16 {
                need(
                    pairings[group.plus[p][q] * 16 + r]
                        == (pairings[p * 16 + r] + pairings[q * 16 + r]) % 4,
                    "Weil first bilinearity",
                )?;
                need(
                    pairings[p * 16 + group.plus[q][r]]
                        == (pairings[p * 16 + q] + pairings[p * 16 + r]) % 4,
                    "Weil second bilinearity",
                )?;
            }
        }
    }
    need(pairings[4 * 16 + 6] == 1, "fixed actual Weil orientation")?;
    println!("ACTUAL_E4_WEIL\tpoints=16\taddition=256\tpairings=256\tgeneric_Miller_auxiliary_3T={auxiliary:?}\tPASS");
    Ok((group, pairings))
}

fn h_pair(g: &Group, e: &[u8], h: &Action, p: [usize; 3], q: [usize; 3]) -> u8 {
    let image = h.apply(g, q);
    (0..3).fold(0, |s, i| (s + e[p[i] * 16 + image[i]]) % 4)
}
fn j4(packet: &Packet<'_>, g: &Group, e: &[u8]) -> AResult<()> {
    let s = Action::new(S, g)?;
    let r = Action::new(R, g)?;
    let h = Action::new(H, g)?;
    let mut input = Reader::new(packet.section(b"J4MP").bytes);
    let mut kernel = Vec::new();
    let mut j2 = Vec::new();
    let mut images2 = BTreeSet::new();
    let basis: Vec<_> = (0..3)
        .flat_map(|coordinate| {
            [4, 6].map(move |point| {
                let mut p = [0; 3];
                p[coordinate] = point;
                p
            })
        })
        .collect();
    for index in 0..4096 {
        let p = cm::decode(index, 16);
        let sp = s.apply(g, p);
        let rp = r.apply(g, p);
        let fp = p.map(|a| g.frobenius[a]);
        let four = p.map(|a| g.scalar(a, 4));
        need(
            input.u16()? == cm::encode(sp, 16),
            "actual J4 S record differs",
        )?;
        need(
            input.u16()? == cm::encode(rp, 16),
            "actual J4 R record differs",
        )?;
        need(
            input.u16()? == cm::encode(fp, 16),
            "actual J4 Frobenius record differs",
        )?;
        let killed = sp == [0; 3];
        need(
            input.u8()? == u8::from(killed),
            "actual J4 kernel flag differs",
        )?;
        if killed {
            kernel.push(index);
        }
        need(
            r.apply(g, sp) == four && s.apply(g, rp) == four,
            "both actual J4 composites",
        )?;
        need(
            s.apply(g, fp) == sp.map(|a| g.frobenius[a])
                && r.apply(g, fp) == rp.map(|a| g.frobenius[a]),
            "actual J4 maps commute with Frobenius",
        )?;
        need(
            (p == [0; 3]) == basis.iter().all(|&b| h_pair(g, e, &h, b, p) == 0),
            "actual whole J4 H pairing nondegenerate",
        )?;
        if p.iter().all(|&a| g.scalar(a, 2) == 0) {
            j2.push(index);
            images2.insert(cm::encode(sp, 16));
            need(
                p.iter()
                    .all(|&a| g.plus[g.plus[g.frobenius[g.frobenius[a]]][g.frobenius[a]]][a] == 0),
                "actual J2 irreducible Frobenius polynomial",
            )?;
        }
    }
    input.end()?;
    need(
        kernel.len() == 64 && j2.len() == 64 && images2.len() == 4,
        "actual mixed kernel/J2 image counts",
    )?;
    let killed2 = kernel
        .iter()
        .filter(|&&id| cm::decode(id, 16).iter().all(|&a| g.scalar(a, 2) == 0))
        .count();
    need(killed2 == 16, "actual mixed kernel sixteen killed by2")?;
    let mut input = Reader::new(packet.section(b"KERN").bytes);
    for &index in &kernel {
        need(
            input.u16()? == index,
            "complete sorted kernel entries differ",
        )?;
        let image = cm::encode(cm::decode(index, 16).map(|a| g.frobenius[a]), 16);
        need(
            kernel.binary_search(&image).is_ok(),
            "actual kernel Frobenius stability",
        )?;
    }
    input.end()?;
    let mut input = Reader::new(packet.section(b"K4WP").bytes);
    for &p in &kernel {
        for &q in &kernel {
            let actual = h_pair(g, e, &h, cm::decode(p, 16), cm::decode(q, 16));
            need(
                actual == 0 && input.u8()? == actual,
                "actual complete kernel isotropic pairing record",
            )?;
        }
    }
    input.end()?;
    println!("ACTUAL_J4\trecords=4096\tkernel=64\tkilled2=16\torder4=48\tkernel_pairs=4096\tS_J2_image=4\tPASS");
    Ok(())
}

fn rational(packet: &Packet<'_>, encoding: &Encoding) -> AResult<()> {
    let points = ec::read_points(packet.section(b"E11P").bytes, 11, encoding)?;
    let group = Group::new(points, 11)?;
    let g = &group;
    g.addition_records(packet.section(b"E11A").bytes)?;
    group_cm(g)?;
    need(
        (0..11).all(|p| g.frobenius[p] == p),
        "every supplied point prime-field rational",
    )?;
    let t = Some((F::prime(1), F::prime(3)));
    let generator = g.index(t)?;
    need(
        (0..11)
            .map(|n| g.scalar(generator, n))
            .collect::<BTreeSet<_>>()
            .len()
            == 11,
        "actual full eleven-point scalar group",
    )?;
    let s = Action::new(S, g)?;
    let r = Action::new(R, g)?;
    let inclusion = Action::new(T, g)?;
    let mut input = Reader::new(packet.section(b"J11M").bytes);
    let mut s_images = BTreeSet::new();
    let mut r_images = BTreeSet::new();
    for index in 0..1331 {
        let p = cm::decode(index, 11);
        let sp = s.apply(g, p);
        let rp = r.apply(g, p);
        let four = p.map(|a| g.scalar(a, 4));
        need(
            input.u16()? == cm::encode(sp, 11),
            "actual rational S record differs",
        )?;
        need(
            input.u16()? == cm::encode(rp, 11),
            "actual rational R record differs",
        )?;
        need(
            input.u16()? == cm::encode(four, 11),
            "actual rational four record differs",
        )?;
        need(
            r.apply(g, sp) == four && s.apply(g, rp) == four,
            "both actual rational composites",
        )?;
        s_images.insert(cm::encode(sp, 11));
        r_images.insert(cm::encode(rp, 11));
    }
    input.end()?;
    need(
        s_images.len() == 1331 && r_images.len() == 1331,
        "actual rational map bijections",
    )?;
    let mut input = Reader::new(packet.section(b"ELDL").bytes);
    for n in 0..11 {
        let point = g.scalar(generator, n);
        let embedded = inclusion.apply(g, [point, 0, 0]);
        let image = s.apply(g, embedded);
        let recovered = r.apply(g, image).map(|a| g.scalar(a, 3));
        need(
            usize::from(input.u8()?) == point,
            "original scalar EC record",
        )?;
        need(
            input.u16()? == cm::encode(embedded, 11),
            "original actual inclusion record",
        )?;
        need(
            input.u16()? == cm::encode(image, 11),
            "original actual transferred scalar record",
        )?;
        need(
            recovered == embedded && usize::from(input.u8()?) == recovered[0],
            "actual original scalar recovery record",
        )?;
    }
    input.end()?;
    println!("ACTUAL_RATIONAL_TRANSFER\tJacobian_records=1331\tE11_additions=121\tall11_scalars_preserved_recovered\tPASS");
    Ok(())
}

pub fn verify(bytes: &[u8]) -> AResult<()> {
    let packet = Packet::parse(bytes)?;
    let encoding = field::qualify()?;
    cm::qualify()?;
    let (group, pairings) = e4(&packet, &encoding)?;
    geometry::verify(packet.section(b"FIBR").bytes, &group, &encoding)?;
    j4(&packet, &group, &pairings)?;
    rational(&packet, &encoding)?;
    Ok(())
}
