//! Bounded CLI smoke check. Full-domain acceptance is in the four native tests.
use chained_t20_prime_norm_checker::{Maps, Pair, Result};
use isogeny_algos::curve::Pt;
use std::io::Read;

fn run() -> Result<()> {
    let mut args = std::env::args().skip(1);
    let fixture = args
        .next()
        .ok_or("usage: chained-t20-prime-norm-checker FIXTURE [CERTIFICATE_OUTPUT]")?;
    let certificate = args.next();
    if args.next().is_some() {
        return Err("too many arguments".into());
    }
    let file = std::fs::File::open(fixture).map_err(|e| e.to_string())?;
    let mut bytes = Vec::new();
    file.take(chained_t20_prime_norm_checker::MAX_FIXTURE_BYTES as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    let maps = Maps::load(&bytes)?;
    let mut checked = 0;
    for i in 0..2 {
        let t = &maps.fixture().targets[i];
        let points = maps.target_points(i)?;
        let mut selected: Vec<_> = points.into_iter().take(16).collect();
        selected.push(t.infinity_point());
        selected.push(isogeny_algos::curve::neg(maps.field(), &t.infinity_point()));
        for point in selected {
            let d = maps.pull_component(i, &point)?;
            let mut expected: Pair = [Pt::Inf; 2];
            expected[i] = isogeny_algos::curve::pmul(maps.field(), &t.curve(), &point, 4);
            let image = maps.norm(&d)?;
            if image != expected
                || maps.recover(&image)? != d
                || maps.recover_components(&image)? != d
            {
                return Err("bounded norm/pullback/recovery smoke failed".into());
            }
            checked += 1;
        }
    }
    if let Some(path) = certificate {
        let json = balanced_source_engine::fibre_certificate(
            include_bytes!("../lean/PullbackFibres.lean"),
            "experiments/chained-transfer-reference/norm-checker/lean/PullbackFibres.lean",
        )?;
        std::fs::write(path, json).map_err(|e| e.to_string())?;
    }
    println!(
        "{}",
        serde_json::json!({"schema":"chained-t20-prime-norm-smoke/v1","field":101,"scope":"fixture admission and bounded rational-fibre smoke only;full12317 domain belongs to native tests","smoke_fibres_including_duplicates":checked,"unsigned":true})
    );
    Ok(())
}
fn main() {
    if let Err(e) = run() {
        eprintln!("REJECT {e}");
        std::process::exit(2);
    }
}
