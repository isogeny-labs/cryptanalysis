//! Public-coordinate fixtures for the existing native M31 CLI. No solver here.
use prime_field_auxiliary_ic::{Backend, Curve, FactorBase};

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(String::as_str).unwrap_or("target");
    let number: u64 = args
        .get(2)
        .expect("scalar or summand count")
        .parse()
        .unwrap();
    let arm = args.get(3).map(String::as_str).unwrap_or("torus");
    // Existing lab reference: cdclt_ct186_audit.rs, main().
    let curve = Curve::<31>::new(2, 14).unwrap();
    let g = curve.point(1, 814455902).unwrap();
    let order = 2147505293u64;
    assert_eq!(curve.modulus(), 2147483647);
    assert!(curve.mul(Some(g), order).unwrap().is_none());
    let roots: Vec<u64> = (0..128).collect();
    let target = if mode == "target" {
        assert!(number > 0 && number < order);
        curve.mul(Some(g), number).unwrap().unwrap()
    } else {
        assert!(mode == "pdp" || mode == "verify");
        assert!((2..=4).contains(&number));
        let base = match arm {
            "torus" | "torus-direct" => FactorBase::torus(curve, 7, None, Backend::Scalar).unwrap(),
            "interval" => FactorBase::without_maps(curve, &roots).unwrap(),
            _ => panic!("unknown fixture arm"),
        };
        let points = base.representatives();
        if mode == "verify" {
            let qx: u64 = args[4].parse().unwrap();
            let qy: u64 = args[5].parse().unwrap();
            let q = curve.point(qx, qy).unwrap();
            let mut sum = None;
            let terms: Vec<&str> = args[6].split(',').collect();
            assert_eq!(terms.len(), number as usize);
            for term in terms {
                let (i, sign) = term.split_once(':').unwrap();
                let mut point = points[i.parse::<usize>().unwrap()];
                match sign {
                    "1" => {}
                    "-1" => point = curve.negate(point).unwrap(),
                    _ => panic!("sign"),
                }
                sum = curve.add(sum, Some(point)).unwrap();
            }
            assert_eq!(sum, Some(q));
            println!("{{\"p\":2147483647,\"replay_passed\":true}}");
            return;
        }
        let mut target = None;
        for point in points.iter().take(number as usize) {
            target = curve.add(target, Some(*point)).unwrap();
        }
        target.expect("finite positive-control sum")
    };
    println!("{{\"public\":{{\"p\":2147483647,\"a\":2,\"b\":14,\"n\":{order},\"P\":[1,814455902],\"Q\":[{},{}]}},\"structured_roots\":[{}]}}",
        target.x(), target.y(), roots.iter().map(u64::to_string).collect::<Vec<_>>().join(","));
}
