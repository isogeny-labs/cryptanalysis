//! Static full-theory CNF for exported Lead 2B s=5 instances.
//! This is a model-equivalent closure, not the dynamic CDCL(Fp) clause graph.

use prime_field_m3_cdclt::field::{is_prime_u64, sha256_hex};
use prime_field_m3_cdclt::selector::Lit;
use prime_field_m3_cdclt::{sqrt_mod_canonical, CompactBinarySelector, CurveFp, FpOps, PointFp};
use std::collections::{HashMap, HashSet};
use std::env;
use std::fmt::Write as _;
use std::fs;
use std::path::Path;

struct Instance {
    curve: CurveFp,
    target: PointFp,
    points: [Vec<PointFp>; 3],
    selector: CompactBinarySelector,
}

fn field<'a>(fields: &'a HashMap<&str, &str>, name: &str) -> Result<&'a str, String> {
    fields
        .get(name)
        .copied()
        .ok_or_else(|| format!("missing IR field {name}"))
}

fn number(fields: &HashMap<&str, &str>, name: &str) -> Result<u64, String> {
    field(fields, name)?
        .parse()
        .map_err(|_| format!("invalid integer in IR field {name}"))
}

fn parse_ir(ir: &str) -> Result<Instance, String> {
    let mut lines = ir.lines();
    if lines.next() != Some("prime-field-m3-ir/v2") {
        return Err("wrong canonical IR version".into());
    }
    let mut fields = HashMap::new();
    for line in lines {
        let (key, value) = line
            .split_once('=')
            .ok_or_else(|| format!("malformed IR line: {line}"))?;
        if fields.insert(key, value).is_some() {
            return Err(format!("duplicate IR field {key}"));
        }
    }
    if number(&fields, "rung_s")? != 5 {
        return Err("only s=5 static closure is supported".into());
    }
    let curve = CurveFp {
        p: number(&fields, "p")?,
        a: number(&fields, "a")?,
        b: number(&fields, "b")?,
    };
    if !is_prime_u64(curve.p) || !curve.is_nonsingular() {
        return Err("IR curve must be smooth over an odd prime field".into());
    }
    if !is_prime_u64(number(&fields, "group_order")?) {
        return Err("IR group order must be prime".into());
    }
    let (qx, qy) = field(&fields, "target")?
        .split_once(',')
        .ok_or("invalid target coordinates")?;
    let target = PointFp::affine(
        qx.parse().map_err(|_| "invalid target x")?,
        qy.parse().map_err(|_| "invalid target y")?,
    );
    let mut ops = FpOps::default();
    if !curve.on_curve(target, &mut ops) {
        return Err("target is not on the IR curve".into());
    }
    let mut points: [Vec<PointFp>; 3] = [Vec::new(), Vec::new(), Vec::new()];
    let mut seen_x = HashSet::new();
    for w in 0..3 {
        let name = format!("window{w}");
        let xs: Vec<u64> = field(&fields, &name)?
            .split(',')
            .map(|x| x.parse().map_err(|_| format!("invalid {name} abscissa")))
            .collect::<Result<_, _>>()?;
        if xs.len() != 32 || xs.windows(2).any(|pair| pair[0] >= pair[1]) {
            return Err(format!("{name} must have 32 sorted distinct abscissae"));
        }
        for x in xs {
            if x >= curve.p || !seen_x.insert(x) {
                return Err(format!(
                    "{name} contains an out-of-field or repeated abscissa"
                ));
            }
            let rhs = curve.rhs(x, &mut ops);
            let y = sqrt_mod_canonical(rhs, curve.p, &mut ops)
                .ok_or_else(|| format!("{name} contains a non-rational abscissa"))?;
            if y == 0 {
                return Err(format!("{name} contains a one-lift abscissa"));
            }
            points[w].push(curve.point_from_canonical_lift(x, y, 0));
            points[w].push(curve.point_from_canonical_lift(x, y, 1));
        }
    }
    let selector = CompactBinarySelector::new([32, 32, 32]);
    assert_eq!(selector.total_vars, 18);
    assert!(selector.range_clauses.is_empty());
    Ok(Instance {
        curve,
        target,
        points,
        selector,
    })
}

fn pair_guard(selector: &CompactBinarySelector, indices: [usize; 2], signs: [u8; 2]) -> Vec<Lit> {
    let mut guard = Vec::with_capacity(12);
    for w in 0..2 {
        for b in 0..5 {
            guard.push(-selector.index_bit_lit(w, b, ((indices[w] >> b) & 1) != 0));
        }
        guard.push(-selector.sign_lit(w, signs[w]));
    }
    guard
}

struct StaticCnf {
    clauses: Vec<Vec<Lit>>,
    present_pairs: usize,
}

fn build(inst: &Instance) -> StaticCnf {
    let mut lookup = HashMap::new();
    for (index, pair) in inst.points[2].chunks_exact(2).enumerate() {
        for (sign, &point) in pair.iter().enumerate() {
            assert!(lookup.insert(point, (index, sign as u8)).is_none());
        }
    }
    let mut ops = FpOps::default();
    let mut clauses = Vec::with_capacity(4096 + 5 * 4096);
    let mut present_pairs = 0;
    for i0 in 0..32 {
        for s0 in 0..2 {
            for i1 in 0..32 {
                for s1 in 0..2 {
                    let guard = pair_guard(&inst.selector, [i0, i1], [s0, s1]);
                    let a = inst.points[0][2 * i0 + s0 as usize];
                    let b = inst.points[1][2 * i1 + s1 as usize];
                    let sum = inst.curve.add(a, b, &mut ops);
                    let needed =
                        inst.curve
                            .add(inst.target, inst.curve.neg(sum, &mut ops), &mut ops);
                    if let Some(&(i2, s2)) = lookup.get(&needed) {
                        present_pairs += 1;
                        for bit in 0..5 {
                            let mut clause = guard.clone();
                            clause.push(inst.selector.index_bit_lit(
                                2,
                                bit,
                                ((i2 >> bit) & 1) != 0,
                            ));
                            clauses.push(clause);
                        }
                        let mut clause = guard;
                        clause.push(inst.selector.sign_lit(2, s2));
                        clauses.push(clause);
                    } else {
                        clauses.push(guard);
                    }
                }
            }
        }
    }
    assert_eq!(clauses.len(), 4096 + 5 * present_pairs);
    StaticCnf {
        clauses,
        present_pairs,
    }
}

fn dimacs(cnf: &StaticCnf, ir: &str) -> String {
    let mut out = format!(
        "c m3-static-full-theory-cnf/v1\nc canonical_ir_sha256={}\nc model-equivalent closure; not dynamic CDCL(Fp) clauses\np cnf 18 {}\n",
        sha256_hex(ir.as_bytes()),
        cnf.clauses.len()
    );
    for clause in &cnf.clauses {
        for lit in clause {
            write!(out, "{lit} ").expect("write DIMACS literal");
        }
        out.push_str("0\n");
    }
    out
}

fn main() {
    let mut args = env::args().skip(1);
    let input = args
        .next()
        .expect("usage: m3-static-cnf INPUT.ir OUTPUT.cnf");
    let output = args
        .next()
        .expect("usage: m3-static-cnf INPUT.ir OUTPUT.cnf");
    assert!(args.next().is_none(), "unexpected extra argument");
    let ir = fs::read_to_string(&input).expect("read canonical IR");
    let inst = parse_ir(&ir).expect("valid s=5 canonical IR");
    let cnf = build(&inst);
    let bytes = dimacs(&cnf, &ir);
    let path = Path::new(&output);
    if path.exists() {
        assert_eq!(fs::read(path).expect("read existing CNF"), bytes.as_bytes());
    } else {
        fs::write(path, bytes).expect("write static CNF");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn check_case(ir: &str, expected_hash: &str, expected_model_count: usize) {
        assert_eq!(sha256_hex(ir.as_bytes()), expected_hash);
        let inst = parse_ir(ir).expect("archived s=5 IR");
        let cnf = build(&inst);
        assert_eq!(cnf.present_pairs, expected_model_count);
        assert_eq!(cnf.clauses.len(), 4096 + 5 * expected_model_count);
        let mut accepted = vec![true; 1 << 18];
        for clause in &cnf.clauses {
            assert!(clause.len() == 12 || clause.len() == 13);
            let (mut fixed_mask, mut fixed_bits) = (0u32, 0u32);
            for &lit in clause {
                let bit = (lit.unsigned_abs() - 1) as usize;
                assert!(bit < 18);
                assert_eq!(fixed_mask & (1 << bit), 0, "duplicate variable in clause");
                fixed_mask |= 1 << bit;
                if lit < 0 {
                    fixed_bits |= 1 << bit;
                }
            }
            let free: Vec<usize> = (0..18)
                .filter(|&bit| fixed_mask & (1 << bit) == 0)
                .collect();
            for choice in 0..(1 << free.len()) {
                let mut assignment = fixed_bits;
                for (j, &bit) in free.iter().enumerate() {
                    if (choice >> j) & 1 != 0 {
                        assignment |= 1 << bit;
                    }
                }
                accepted[assignment as usize] = false;
            }
        }
        let mut ops = FpOps::default();
        let mut model_count = 0;
        for (assignment, &cnf_value) in accepted.iter().enumerate() {
            let selected: Vec<PointFp> = (0..3)
                .map(|w| {
                    let index = inst.selector.index_bits[w]
                        .iter()
                        .enumerate()
                        .fold(0usize, |value, (bit, &var)| {
                            value | (((assignment >> var) & 1) << bit)
                        });
                    let sign = (assignment >> inst.selector.sign_vars[w]) & 1;
                    inst.points[w][2 * index + sign]
                })
                .collect();
            let sum = inst.curve.add(
                inst.curve.add(selected[0], selected[1], &mut ops),
                selected[2],
                &mut ops,
            );
            let expected = sum == inst.target;
            assert_eq!(cnf_value, expected, "assignment {assignment}");
            model_count += usize::from(expected);
        }
        assert_eq!(model_count, expected_model_count);
        let output = dimacs(&cnf, ir);
        assert!(output.contains(&format!("p cnf 18 {}\n", cnf.clauses.len())));
        let emitted: Vec<Vec<Lit>> = output
            .lines()
            .filter(|line| !line.starts_with('c') && !line.starts_with('p'))
            .map(|line| {
                let mut words: Vec<Lit> = line
                    .split_whitespace()
                    .map(|word| word.parse().expect("DIMACS integer"))
                    .collect();
                assert_eq!(words.pop(), Some(0), "DIMACS clause terminator");
                words
            })
            .collect();
        assert_eq!(emitted, cnf.clauses);
    }

    #[test]
    fn all_18_bit_assignments_match_exact_group_models() {
        check_case(
            include_str!("../../fixtures/s5/lead2b-s5-planted.ir"),
            "1dd4ef93b48499871e822f38e693f7d4d18a8c5cf4942e9345d3d866f8705a36",
            1,
        );
        check_case(
            include_str!("../../fixtures/s5/lead2b-s5-natural.ir"),
            "701972399e5849cabebcb35df5538990e335038e32a068a9185cdb89e7f45216",
            0,
        );
        check_case(
            include_str!("../../fixtures/s5/lead2b-s5-exact-unsat.ir"),
            "53fa0069d6b5a4f5bee30f001904d31b7d96f05c76e6da3834fc29a935d1552f",
            0,
        );
    }
}
