use chained_n4_completed_v2::NormV2;
use chained_n4_odd_product_models::{er, three, GluingModel, SourceE};
use chained_n4_odd_source::OddSourceIsogeny;
use chained_n4_public_target::CheckedInstance;
use chained_original_smith_engine::original;
use isogeny_algos::{
    curve::{Curve, Isogeny, Pt},
    field::{Field, Rng},
    fpr::{FpR, ER},
    kernel::kohel::kohel,
    poly,
};
use serde_json::{json, Value};
use std::collections::{BTreeMap, BTreeSet};

fn vs(s: u64) -> Vec<u8> {
    (0..64).filter(|&i| s & (1u64 << i) != 0).collect()
}
fn bits(v: &[u8]) -> u64 {
    v.iter().fold(0, |s, &v| s | (1u64 << v))
}
fn pairing(a: u8, b: u8) -> u32 {
    ((((a & 0x15) << 1) | ((a & 0x2a) >> 1)) & b).count_ones() & 1
}
fn frob(x: u8) -> u8 {
    ((x << 2) & 63) | (x >> 4)
}
fn span(g: [u8; 3]) -> u64 {
    bits(
        &(0..8)
            .map(|v| {
                g.iter().enumerate().fold(0, |out, (i, &b)| {
                    out ^ if v & (1 << i) != 0 { b } else { 0 }
                })
            })
            .collect::<Vec<_>>(),
    )
}
fn rank(v: &[u8]) -> u32 {
    let mut basis = [0u8; 6];
    let mut r = 0;
    for &x in v {
        let mut x = x;
        for bit in (0..6).rev() {
            if x & (1 << bit) != 0 {
                if basis[bit] != 0 {
                    x ^= basis[bit];
                } else {
                    basis[bit] = x;
                    r += 1;
                    break;
                }
            }
        }
    }
    r
}
fn dimension(s: u64) -> u32 {
    let v = vs(s);
    assert!(v.contains(&0));
    assert!(v.len().is_power_of_two());
    for &a in &v {
        for &b in &v {
            assert!(v.contains(&(a ^ b)));
            assert_eq!(pairing(a, b), 0);
        }
    }
    let d = (v.len() as u32).trailing_zeros();
    assert_eq!(d, rank(&v));
    d
}
fn original_all() -> BTreeSet<u64> {
    let basis = [3u8, 5, 15, 23, 63, 95];
    let mask = |v: u8| {
        basis
            .iter()
            .enumerate()
            .fold(0, |a, (i, &b)| a ^ if v & (1 << i) != 0 { b } else { 0 })
    };
    let mut inverse = [255; 128];
    for v in 0..64 {
        assert_eq!(inverse[mask(v) as usize], 255);
        inverse[mask(v) as usize] = v;
    }
    for a in 0..64 {
        for b in 0..64 {
            assert_eq!(pairing(a, b), (mask(a) & mask(b)).count_ones() & 1);
        }
    }
    let out: BTreeSet<_> = original::lagrangians()
        .iter()
        .map(|(v, _)| {
            let mut row = v
                .iter()
                .map(|&x| {
                    let y = inverse[x as usize];
                    assert!(y < 64);
                    y
                })
                .collect::<Vec<_>>();
            row.push(0);
            let s = bits(&row);
            assert_eq!(dimension(s), 3);
            s
        })
        .collect();
    assert_eq!(out.len(), 135);
    out
}
fn fp(f: &FpR, mut x: ER, power: usize) -> ER {
    for _ in 0..power {
        x = f.frobenius(x);
    }
    x
}
fn pp(f: &FpR, p: Pt<ER>, power: usize) -> Pt<ER> {
    match p {
        Pt::Inf => Pt::Inf,
        Pt::Aff(x, y) => Pt::Aff(fp(f, x, power), fp(f, y, power)),
    }
}
fn point(p: Pt<ER>) -> Value {
    match p {
        Pt::Inf => Value::Null,
        Pt::Aff(x, y) => json!([three(x), three(y)]),
    }
}
fn torsion(f: &FpR, e: &Curve<ER>) -> Vec<Pt<ER>> {
    let mut roots = poly::roots(f, &vec![e.b, e.a, f.zero(), f.one()], &mut Rng::new(0x6611));
    roots.sort();
    roots.dedup();
    assert_eq!(roots.len(), 3);
    std::iter::once(Pt::Inf)
        .chain(roots.into_iter().map(|x| Pt::Aff(x, f.zero())))
        .collect()
}
pub fn audit_all(
    c: &CheckedInstance,
    old: &NormV2,
    source: &SourceE,
    t: &OddSourceIsogeny,
    models: &[GluingModel],
    summary: &Value,
    old_gold: u64,
) -> Vec<Value> {
    let f = source.field();
    let old2 = torsion(f, t.source());
    let new2 = torsion(f, t.target());
    let mut permutation = [0u8; 4];
    for (i, &p) in old2.iter().enumerate() {
        let q = t.forward(p).unwrap();
        permutation[i] = new2.iter().position(|&r| r == q).unwrap() as u8;
    }
    assert_eq!(
        permutation.iter().copied().collect::<BTreeSet<_>>().len(),
        4
    );
    assert_eq!(permutation[0], 0);
    for a in 0..4 {
        for b in 0..4 {
            assert_eq!(permutation[a ^ b], permutation[a] ^ permutation[b]);
        }
    }
    let h: Vec<[u64; 3]> =
        serde_json::from_value(t.certificate["forward_kernel"]["kernel"].clone()).unwrap();
    let num: Vec<[u64; 3]> =
        serde_json::from_value(t.certificate["forward"]["x_num"].clone()).unwrap();
    let den: Vec<[u64; 3]> =
        serde_json::from_value(t.certificate["forward"]["x_den"].clone()).unwrap();
    let mut conjugates = vec![];
    for power in 0..3 {
        let e = Curve::new(fp(f, t.source().a, power), fp(f, t.source().b, power));
        let kernel = h.iter().map(|&x| fp(f, er(x), power)).collect();
        let m = kohel(f, &e, &kernel, 13);
        assert_eq!(
            m.num,
            num.iter().map(|&x| fp(f, er(x), power)).collect::<Vec<_>>()
        );
        assert_eq!(
            m.den,
            den.iter().map(|&x| fp(f, er(x), power)).collect::<Vec<_>>()
        );
        assert_eq!(
            m.cod,
            Curve::new(fp(f, t.target().a, power), fp(f, t.target().b, power))
        );
        let mut rows = vec![];
        for i in 0..4 {
            let p = pp(f, old2[i], power);
            let q = m.eval(f, &p);
            assert_eq!(q, pp(f, new2[permutation[i] as usize], power));
            rows.push(json!({"source":point(p),"image":point(q)}));
        }
        conjugates.push(json!({"factor":power,"source_a":three(e.a),"source_b":three(e.b),"target_a":three(m.cod.a),"target_b":three(m.cod.b),"kernel":m.ker.iter().copied().map(three).collect::<Vec<_>>(),"x_num":m.num.iter().copied().map(three).collect::<Vec<_>>(),"x_den":m.den.iter().copied().map(three).collect::<Vec<_>>(),"all4_points":rows}));
    }
    let transport = |v: u8| {
        (0..3).fold(0, |out, i| {
            out | (permutation[((v >> (2 * i)) & 3) as usize] << (2 * i))
        })
    };
    let actual = |v: u8, new: bool| {
        (0..3)
            .map(|i| {
                point(pp(
                    f,
                    if new {
                        new2[((v >> (2 * i)) & 3) as usize]
                    } else {
                        old2[((v >> (2 * i)) & 3) as usize]
                    },
                    i,
                ))
            })
            .collect::<Vec<_>>()
    };
    let mut vector_rows = vec![];
    assert_eq!((0..64).map(transport).collect::<BTreeSet<_>>().len(), 64);
    for a in 0..64 {
        assert_eq!(transport(frob(a)), frob(transport(a)));
        for b in 0..64 {
            assert_eq!(transport(a ^ b), transport(a) ^ transport(b));
            assert_eq!(pairing(a, b), pairing(transport(a), transport(b)));
        }
        vector_rows.push(json!({"old_vector":a,"new_vector":transport(a),"old_actual_coordinates":actual(a,false),"new_actual_coordinates":actual(transport(a),true)}));
    }
    let transported_gold = bits(&vs(old_gold).into_iter().map(transport).collect::<Vec<_>>());
    assert_eq!(dimension(transported_gold), 3);
    let all = original_all();
    let from_models: BTreeSet<_> = summary["all135_kernels"]
        .as_array()
        .unwrap()
        .iter()
        .map(|r| r["mask"].as_u64().unwrap())
        .collect();
    assert_eq!(all, from_models);
    assert!(all.contains(&transported_gold));
    let mut histogram = BTreeMap::new();
    let mut all_rows = vec![];
    for &g in &all {
        let intersection = g & transported_gold;
        let d = dimension(intersection);
        *histogram.entry(d).or_insert(0usize) += 1;
        all_rows.push(json!({"mask":g,"whole_intersection":vs(intersection),"dimension_cardinality_and_gaussian_rank":d,"actual_target_coordinates":vs(intersection).into_iter().map(|v|actual(v,true)).collect::<Vec<_>>()}));
    }
    assert_eq!(
        histogram,
        BTreeMap::from([(0, 64), (1, 56), (2, 14), (3, 1)])
    );
    let mut rational = vec![];
    for q in 1..4 {
        rational.push((format!("product-Q{q}"), span([q, q << 2, q << 4]), false));
    }
    for m in models {
        rational.push((
            format!("HLP-{}-{}", m.root_index, m.sign_index),
            m.kernel_mask,
            m.square_root.is_some(),
        ));
    }
    let stable: BTreeSet<_> = all
        .iter()
        .copied()
        .filter(|&g| vs(g).into_iter().all(|v| g & (1u64 << frob(v)) != 0))
        .collect();
    assert_eq!(stable, rational.iter().map(|r| r.1).collect());
    assert_eq!(stable.len(), 9);
    let types:Vec<_>=rational.iter().map(|(label,g,eligible)|{
        let intersection=g&transported_gold;let d=dimension(intersection);let a=3-d;let b=2*d;
        assert_eq!(4u64.pow(a)*2u64.pow(b),64);assert_eq!(2u64.pow(a+b),8*intersection.count_ones()as u64);
        let wrong=dimension(g&old_gold);
        json!({"target":label,"kernel":g,"eligible_actual_Jacobian":eligible,"transported_intersection":vs(intersection),"dimension":d,"C4_factors":a,"C2_factors":b,"C13_factors":3,"total_kernel_order":4u64.pow(a)*2u64.pow(b)*13u64.pow(3),"free_C52_cubed":d==0,"matched_kernel_factorization_candidate":*g==transported_gold,"wrong_untransported_dimension":wrong,"wrong_untransported_free_C52_cubed":wrong==0,"wrong_control_changes_result":d!=wrong,"scope":"native2torsion_census;fulltype_requires_written_etale_degree_exponent_exactness_and_groupclassification;no_actual_J4_J13_coordinates"})
    }).collect();
    println!(
        "N4_REFINEMENT_GAMMA2 {}",
        json!({"protocol":"579e08","actual_permutation":permutation,"all3_coefficient_conjugates":conjugates,"all64_coordinate_vector_images":vector_rows,"all4096_linearity_pairing_checks_and_Frobenius_commutation":true,"literal_old_Gold":old_gold,"actual_transported_Gold":transported_gold,"original_quartic":c.inst.f,"original_P0":old.a.pic.base_point()})
    );
    println!(
        "N4_REFINEMENT_INTERSECTIONS {}",
        json!({"all135_original_Smith_and_model_censuses_equal":true,"all135":all_rows,"histogram":histogram,"independent_gaussian_rank_matches_all_cardinality_dimensions":true,"all9_rational_kernels":rational})
    );
    println!(
        "N4_REFINEMENT_KERNEL_TYPES {}",
        json!({"all9":types,"degree":140608,"annihilator":52,"native_scope":"actual transported2torsion/conditional geometric classification;written proof required","rational_cofactor_tables":"do not determine full geometric kernel"})
    );
    types
}
