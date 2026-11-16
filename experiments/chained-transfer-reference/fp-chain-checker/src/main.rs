//! Bounded CLI smoke only;full-domain acceptance belongs to the four tests.
use chained_f101_c0_t20_checker::{Maps, Result, MAX_BYTES};
use isogeny_algos::curve::{self, Pt};
use std::io::Read;
fn run() -> Result<()> {
    let mut args = std::env::args().skip(1);
    let path = args
        .next()
        .ok_or("usage: chained-f101-c0-t20-checker FIXTURE")?;
    if args.next().is_some() {
        return Err("too many arguments".into());
    }
    let file = std::fs::File::open(path).map_err(|e| e.to_string())?;
    let mut bytes = Vec::new();
    file.take(MAX_BYTES as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    let maps = Maps::load(&bytes)?;
    let mut checked = 0;
    for i in 0..2 {
        let mut points: Vec<_> = maps.points(i)?.into_iter().take(16).collect();
        points.extend(if i == 0 {
            [Pt::Aff(2, 37), Pt::Aff(2, 64)]
        } else {
            [Pt::Aff(38, 56), Pt::Aff(38, 45)]
        });
        for p in points {
            let d = maps.source_pull_component(i, &p)?;
            let n = maps.source_norm(&d)?;
            let mut expected = [Pt::Inf; 2];
            expected[i] = curve::pmul(maps.field(), &maps.fixture().covers[i].curve(), &p, 2);
            let target = maps.forward(&d)?;
            if n != expected
                || maps.forward_alternative(&d)? != target
                || maps.inverse(&target)? != d
                || maps.inverse_alternative(&target)? != d
                || maps.t20().norm(&target)? != maps.chain_norm_image(&d)?
            {
                return Err("bounded F101 chain smoke failed".into());
            }
            checked += 1;
        }
    }
    println!(
        "{}",
        serde_json::json!({"schema":"chained-f101-c0-t20-smoke/v1","field":101,"bounded_fibres_including_duplicates":checked,"scope":"fixed fixture admission and36fibre two-way chain smoke only;full12317BOTHdomains belongs to four native tests","unsigned":true})
    );
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("REJECT {e}");
        std::process::exit(2);
    }
}
