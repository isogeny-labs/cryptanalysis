mod divisor_a;
mod elliptic_a;
mod field49_a;
#[path = "inputs/crypto5114/field_a.rs"]
mod field_d;
#[path = "inputs/crypto5114/poly_d.rs"]
mod poly_d;

use divisor_a::{cantor, gamma, identity, neg, pull1, pull2, push, scalar, valid, Div, H};
use elliptic_a::{add_base, mul_base, EP};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::OpenOptions;
use std::io::{BufWriter, Write};
use std::path::Path;

fn bsgs(base: &Div, target: &Div, order: usize) -> Option<usize> {
    assert!(valid(base) && valid(target));
    assert_ne!(base, &identity());
    assert_eq!(scalar(base, order), identity());
    let mut m = 1;
    while m * m < order {
        m += 1;
    }
    let mut babies = BTreeMap::new();
    let mut r = identity();
    for j in 0..m {
        assert!(babies.insert(r.clone(), j).is_none());
        r = cantor(&r, base);
    }
    let stride = neg(&r);
    let mut giant = target.clone();
    for i in 0..m {
        if let Some(&j) = babies.get(&giant) {
            let k = i * m + j;
            if k < order && scalar(base, k) == *target {
                return Some(k);
            }
        }
        giant = cantor(&giant, &stride);
    }
    None
}
fn point(p: EP) -> String {
    p.map_or_else(|| "O".to_owned(), |(x, y)| format!("{x}:{y}"))
}
fn new_file(path: &Path) -> BufWriter<std::fs::File> {
    BufWriter::new(
        OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .unwrap(),
    )
}
fn main() {
    let args: Vec<_> = std::env::args().collect();
    assert_eq!(
        args.len(),
        2,
        "one fresh complete-dataset directory required"
    );
    let out = Path::new(&args[1]);
    std::fs::create_dir(out).unwrap();
    println!("PROFILE\tactual-inert-genus2-Cantor-cover-pushforward-A\tfixed-F7-correctness\tunsigned-no-benchmark");
    field49_a::BASE.validate();
    let (g, s, t) = poly_d::bezout(&H, &poly_d::derivative(&H));
    assert_eq!(g, vec![1]);
    println!(
        "FULL_MODEL\tH={H:?}\tsquarefree-Bezout-s={s:?}\tt={t:?}\tleading6-minus-all-squares={:?}",
        (0..7)
            .map(|x| field_d::sub(6, field_d::mul(x, x)))
            .collect::<Vec<_>>()
    );
    assert!((0..7).all(|x| field_d::mul(x, x) != 6));
    let epoints = elliptic_a::points();
    assert_eq!(epoints.len(), 11);
    let generator = Some((1, 3));
    let orbit: BTreeSet<_> = (0..11).map(|k| mul_base(generator, k)).collect();
    assert_eq!(orbit, epoints.iter().copied().collect());
    assert_eq!(mul_base(generator, 11), None);
    println!("FULL_ORIGINAL_E_POINTS\t{epoints:?}\tT={generator:?}\tall11-orbit-distinct=true");
    let mut classes = vec![identity()];
    let mut tested = 0;
    for u0 in 0..7 {
        for u1 in 0..7 {
            for v0 in 0..7 {
                for v1 in 0..7 {
                    tested += 1;
                    let d = Div {
                        u: vec![u0, u1, 1],
                        v: poly_d::trim(vec![v0, v1]),
                    };
                    if valid(&d) {
                        classes.push(d);
                    }
                }
            }
        }
    }
    assert_eq!(tested, 2401);
    assert_eq!(classes.len(), 121);
    let ids: BTreeMap<_, _> = classes
        .iter()
        .cloned()
        .enumerate()
        .map(|(i, d)| (d, i))
        .collect();
    assert_eq!(ids.len(), 121);
    let projections: Vec<_> = classes.iter().map(push).collect();
    let actual_pairs: BTreeSet<_> = projections.iter().map(|p| p.pair).collect();
    let all_pairs: BTreeSet<_> = epoints
        .iter()
        .flat_map(|&p| epoints.iter().map(move |&q| (p, q)))
        .collect();
    assert_eq!(actual_pairs, all_pairs);
    let mut records = new_file(&out.join("classes.csv"));
    writeln!(
        records,
        "id,u_degree,u0,u1,v0,v1,push1,push2,root_type,field_u0,field_u1,r0_a,r0_b,r1_a,r1_b"
    )
    .unwrap();
    let mut types = BTreeMap::new();
    for (id, (d, p)) in classes.iter().zip(&projections).enumerate() {
        *types.entry(p.kind).or_insert(0usize) += 1;
        writeln!(
            records,
            "{id},{},{},{},{},{},{},{},{},{},{},{},{},{},{}",
            d.u.len() - 1,
            d.u.first().copied().unwrap_or(0),
            d.u.get(1).copied().unwrap_or(0),
            d.v.first().copied().unwrap_or(0),
            d.v.get(1).copied().unwrap_or(0),
            point(p.pair.0),
            point(p.pair.1),
            p.kind,
            p.field.u0,
            p.field.u1,
            p.roots[0].0[0],
            p.roots[0].0[1],
            p.roots[1].0[0],
            p.roots[1].0[1]
        )
        .unwrap();
    }
    records.flush().unwrap();
    println!("COMPLETE_IDEAL_ENUMERATION\tcandidates={tested}\tclasses={}\tactual-root-types={types:?}\tactual-push-pair-bijection=true",classes.len());
    let mut table = vec![vec![0usize; 121]; 121];
    for (i, a) in classes.iter().enumerate() {
        for (j, b) in classes.iter().enumerate() {
            let sum = cantor(a, b);
            let id = *ids
                .get(&sum)
                .expect("every exact Cantor sum belongs to complete actual population");
            let p = projections[i].pair;
            let q = projections[j].pair;
            assert_eq!(
                projections[id].pair,
                (add_base(p.0, q.0), add_base(p.1, q.1)),
                "actual-root pushforward disagreement at {i},{j}"
            );
            table[i][j] = id;
        }
    }
    let mut cayley = new_file(&out.join("cayley.csv"));
    write!(cayley, "left_id").unwrap();
    for j in 0..121 {
        write!(cayley, ",{j}").unwrap();
    }
    writeln!(cayley).unwrap();
    for (i, row) in table.iter().enumerate() {
        write!(cayley, "{i}").unwrap();
        for id in row {
            write!(cayley, ",{id}").unwrap();
        }
        writeln!(cayley).unwrap();
    }
    cayley.flush().unwrap();
    let mut triples = 0usize;
    for (i, row) in table.iter().enumerate() {
        assert_eq!(row[0], i);
        assert_eq!(table[0][i], i);
        assert_eq!(row[ids[&neg(&classes[i])]], 0);
        assert_eq!(scalar(&classes[i], 11), identity());
        for (j, &ij) in row.iter().enumerate() {
            assert_eq!(ij, table[j][i]);
            for (k, &jk) in table[j].iter().enumerate() {
                assert_eq!(table[ij][k], row[jk]);
                triples += 1;
            }
        }
    }
    assert_eq!(triples, 1771561);
    println!("COMPLETE_ACTUAL_GROUP\tCantor-additions=14641\tall-independent-push-pairs=true\tidentity-inverse-exponent11=true\tcommutative=true\tassociative-triples={triples}\twhole-cayley.csv-written=true");
    let base = gamma(generator);
    assert_ne!(base, identity());
    for k in 0..11 {
        let p = mul_base(generator, k);
        let a = pull1(p);
        let b = pull2(p);
        let mapped = gamma(p);
        assert!(valid(&a) && valid(&b) && valid(&mapped));
        assert_eq!(push(&a).pair, (mul_base(p, 2), None));
        assert_eq!(push(&b).pair, (None, mul_base(p, 2)));
        assert_eq!(push(&mapped).pair, (p, mul_base(p, 9)));
        assert_eq!(mapped, scalar(&base, k));
        let recovered = bsgs(&base, &mapped, 11).expect("all actual image targets soluble");
        assert_eq!(recovered, k);
        assert_eq!(mul_base(generator, recovered), p);
        println!("ALL_CHAIN_AND_BSGS_REPLAY\tk-oracle-driver-only={k}\tP={}\tp1pull-id={}\tp2pull-id={}\tGamma-id={}\tu={:?}\tv={:?}\tpush1={}\tpush2={}\tBSGS-result={recovered}\tsource-replay=true",point(p),ids[&a],ids[&b],ids[&mapped],mapped.u,mapped.v,point(push(&mapped).pair.0),point(push(&mapped).pair.1));
    }
    let original = pull1(generator);
    let mut bad_h = H;
    bad_h[0] = field_d::add(bad_h[0], 1);
    assert!(!divisor_a::valid_with_h(&original, &bad_h));
    assert!(valid(&original));
    println!("REAL_MODEL_MUTANT\tH0+1={bad_h:?}\toriginal-ideal={original:?}\tcurve-congruence-rejects\tpristine-restored");
    let mut bad_ideal = original.clone();
    bad_ideal.u[0] = field_d::add(bad_ideal.u[0], 1);
    let accepted = valid(&bad_ideal);
    let original_relation = accepted && push(&bad_ideal).pair == push(&original).pair;
    assert!(!original_relation);
    println!("REAL_IDEAL_MUTANT\tu0+1={bad_ideal:?}\ton-curve={accepted}\toriginal-push-relation-rejected\tpristine-restored");
    let sum = cantor(&base, &base);
    let bad_sign = neg(&sum);
    assert!(valid(&bad_sign));
    assert_ne!(bad_sign, sum);
    assert_ne!(push(&bad_sign).pair, push(&sum).pair);
    println!("REAL_SIGN_MUTANT\tactual-sum={sum:?}\tchanged-v={bad_sign:?}\tvalid-inverse=true\toriginal-addition-relation-rejected\tpristine-restored");
    let unhalved = cantor(&pull1(generator), &pull2(mul_base(generator, 9)));
    let bad_gamma = scalar(&unhalved, 5);
    assert_ne!(push(&bad_gamma).pair.0, generator);
    assert_eq!(push(&base).pair.0, generator);
    println!("REAL_CHAIN_MUTANT\tscalar6-to5\tbad-actual-ideal={bad_gamma:?}\tbad-push1={}\tleft-inverse-rejected\tpristine-restored",point(push(&bad_gamma).pair.0));
    println!("RESTORED_PRISTINE\tactual-Cantor-class-group-and-cover-chain\tall121-ideals-14641-sums-1771561-triples-11-inputs-11-BSGS-source-replays\tprojection-only-is-original-point\tfull-formal-geometry-and-signed-verdict-open");
}
