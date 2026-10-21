//! Inspect and exercise the complete linked binary-field EFD catalogue.
use cryptanalysis_suite::binary_ecc::{
    curve::{point_add, point_double},
    efd::{catalogue, weierstrass_operation},
    BinaryCurve,
};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<_> = std::env::args().skip(1).collect();
    match args.first().map(String::as_str).unwrap_or("list") {
        "list" => {
            println!("formula\tcoordinates\tM\tS\tI\tadd");
            for f in catalogue()
                .formulas
                .iter()
                .filter(|f| args.get(1).is_none_or(|filter| f.id.contains(filter)))
            {
                let c = f.compile()?.operation_counts();
                let r = catalogue().representation(&f.representation).unwrap();
                println!(
                    "{}\t{}\t{}\t{}\t{}\t{}",
                    f.id,
                    r.variables.len(),
                    c.multiplications,
                    c.squarings,
                    c.inversions,
                    c.additions
                );
            }
        }
        "show" => {
            let id = args.get(1).ok_or("show needs an exact formula id")?;
            let f = catalogue().formula(id).ok_or("unknown formula id")?;
            let rep = catalogue().representation(&f.representation).unwrap();
            println!(
                "Representation: {}\nModel/format assumptions: {:?}\nCoordinate relations: {:?}",
                rep.id, rep.assumptions, rep.relations
            );
            println!("{}\n{}\nRequired names (cache parameters may be derived): {:?}\nRecord:\n{}\nProgram:\n{}",f.id,f.record.url,f.compile()?.required_inputs(),f.record.text,f.program.text);
        }
        "demo" => {
            let curve = BinaryCurve::sect163k1();
            let p = point_double(&curve, &curve.generator);
            let q = point_add(&curve, &p, &curve.generator);
            let id = "shortw/lambda/addition/add-2013-olar";
            let r = weierstrass_operation(&curve, id, &p, Some(&q))?;
            assert_eq!(r.point, point_add(&curve, &p, &q));
            println!(
                "{id}: [2]G + [3]G = [5]G; path={:?}; verified with existing affine law",
                r.path
            );
        }
        _ => return Err("usage: efd_binary [list [FILTER] | show FORMULA_ID | demo]".into()),
    }
    Ok(())
}

#[test]
fn catalogue_example_has_the_linked_scope() {
    assert_eq!(catalogue().formulas.len(), 135);
    assert_eq!(catalogue().representations.len(), 19);
}
