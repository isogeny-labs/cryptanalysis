//! Fast CI regression checks for Lead P1-3b (#1347 disjoint 3-window F_p CDCL(T) nogood width)
//! and Lead P1-4b (CT186 prime-field chained Jacobian transfer cost floor).

#[allow(dead_code)]
#[path = "../examples/cdclt_ct186_audit.rs"]
mod audit;

use prime_field_auxiliary_ic::Curve;

#[test]
fn oracle_1347_f7_and_live_rref_and_nogood_width_barrier_hold() {
    let summary = audit::verify_1347_development_oracle();
    assert_eq!(summary.p, 7);
    assert_eq!(summary.group_order, 13);
    assert_eq!(summary.window_sizes, [3, 2, 2]);
    assert_eq!(summary.fp2_candidates, 96);
    assert_eq!(summary.projected_models, 5);

    let curve = Curve::<31>::new(2, 14).unwrap();
    let g = curve.point(1, 814455902).unwrap();

    let mut unsat_points = Vec::new();
    for s in 5..=6 {
        let sz = 1usize << s;
        let starts = [10_000u64, 500_000_000u64, 1_200_000_000u64];
        let mut windows = [
            Vec::with_capacity(sz),
            Vec::with_capacity(sz),
            Vec::with_capacity(sz),
        ];
        for w in 0..3 {
            let mut x = starts[w];
            while windows[w].len() < sz {
                if curve.lift_x(x).unwrap().is_some() {
                    windows[w].push(x);
                }
                x += 1;
            }
        }

        // Check live F_p-RREF on s=5 partial assignments has zero pre-2-window unit propagations.
        if s == 5 {
            for mask in [0u64, 0b1011, 0b1_1111, (0b1_1111) | (0b0_1111 << 5)] {
                let (conf, forced) = audit::radix_rref_forced_or_conflict(
                    curve.modulus(),
                    2,
                    14,
                    starts,
                    s,
                    g.x(),
                    mask,
                    0,
                );
                assert!(!conf && forced == 0);
            }
        }

        // Natural UNSAT check across WindowMajor and BitInterleaved.
        let nat_target = curve.mul(Some(g), 20_261_119 + s as u64).unwrap().unwrap();
        for order in [
            audit::BranchOrder::WindowMajor,
            audit::BranchOrder::BitInterleaved,
        ] {
            let (sol, m) = audit::run_cdclt_3window(
                curve,
                &windows,
                s,
                nat_target,
                "natural",
                "prefiltered",
                false,
                order,
            );
            assert!(sol.is_none());
            assert_eq!(m.theory_conflicts, 1u64 << (2 * s));
            assert_eq!(m.min_raw_nogood_width, 2 * s);
            assert_eq!(m.max_raw_nogood_width, 2 * s);
            assert_eq!(m.max_1uip_width, 2 * s);
            if order == audit::BranchOrder::WindowMajor {
                unsat_points.push((s, m.theory_conflicts));
            }
        }

        // Planted SAT check.
        let p0 = curve.lift_x(windows[0][3]).unwrap().unwrap();
        let p1 = curve.lift_x(windows[1][5]).unwrap().unwrap();
        let p2 = curve.lift_x(windows[2][7]).unwrap().unwrap();
        let s01 = curve.add(Some(p0), Some(p1)).unwrap();
        let planted = curve.add(s01, Some(p2)).unwrap().unwrap();
        let (sol, m_sat) = audit::run_cdclt_3window(
            curve,
            &windows,
            s,
            planted,
            "planted",
            "prefiltered",
            false,
            audit::BranchOrder::BitInterleaved,
        );
        let pts = sol.expect("planted SAT");
        let check01 = curve.add(Some(pts[0]), Some(pts[1])).unwrap();
        assert_eq!(curve.add(check01, Some(pts[2])).unwrap(), Some(planted));
        assert!(m_sat.min_raw_nogood_width >= 2 * s);
    }

    let slope = audit::ols_slope_log2(&unsat_points);
    assert!((slope - 2.0).abs() < 1e-9);

    let ct186 = audit::compute_ct186_cost_floor_panel();
    assert_eq!(ct186.len(), 4);
    for row in &ct186 {
        assert!(
            row.log2_g2_dlp_gttd07_floor_ops > row.log2_pollard_rho_ops + 15.0,
            "prime-field CT186 floor must strictly exceed Pollard rho"
        );
    }
}
