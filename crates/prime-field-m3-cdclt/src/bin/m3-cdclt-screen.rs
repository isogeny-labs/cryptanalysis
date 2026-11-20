//! s=5..12 scaling screen for Lead 2B compact binary-selector m=3 CDCL(Fp).
use prime_field_m3_cdclt::{sizing_comparison_row, CompactBinarySelector};
use std::time::Instant;

fn main() {
    println!("s,compact_total_vars,sinz_total_vars,compact_range_clauses,sinz_exactly_one_clauses,wall_ms");
    for s in 5u32..=12 {
        let t0 = Instant::now();
        let row = sizing_comparison_row(s);
        let w = 1usize << s;
        let _sel = CompactBinarySelector::new([w, w, w]);
        let ms = t0.elapsed().as_secs_f64() * 1e3;
        println!(
            "{},{},{},{},{},{:.3}",
            s,
            row.compact_total_vars,
            row.sinz_total_vars_no_sign,
            row.compact_range_clauses,
            row.sinz_exactly_one_clauses,
            ms
        );
    }
}
