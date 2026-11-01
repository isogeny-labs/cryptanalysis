# n=83 Bernstein-Lange gap on the rank-probe producer: frozen result (a measurement)

Reading: **bl_online_faster_than_ic**

| statistic | estimate [95%] |
| --- | --- |
| primary_online_gap_cP_over_BL | 22.55 [16.23, 31.44] (n=64) |
| rho_online_over_BL | 118.8 [90.52, 159.2] (n=64) |
| online_gap_cP_over_rT | 0.1899 [0.1432, 0.2453] (n=64) |
| online_gap_BL_over_rT | 0.008419 [0.006242, 0.01104] (n=64) |
| e2e_cold_gap_IC_over_rT | 67.74 [59.99, 77.46] (n=64) |
| cold_gap_BL_over_rT | 68.79 [61.3, 78.33] (n=64) |
| cold_ic_over_bl | 0.9847 [0.9481, 1.022] (n=64) |
| aa_ic_cold_cP_over_cPaa | 0.9994 [0.9979, 1.001] (n=64) |
| aa_ic_online_cP_over_cPaa | 1 [0.9976, 1.003] (n=64) |
| aa_bl_online_geo_BL_over_BLaa | 0.9996 [0.9947, 1.004] (n=64) |

End-to-end cold (ms): {"IC (kP+cP)": 174368.16415415626, "BL": 177071.7490831406, "rT": 2574.080346828125, "IC_rank_stage_mean": 151361.68323075, "BL_precompute": 172921.756318, "BL_median_process_setup": 4130.980796}

S cold: {"IC (kP+cP)": 7.416814367257258, "BL": 7.531812352363437, "rT": 0.10948945979583119}

S online: {"cP": 0.01823855561170711, "rT": 0.09605254486188108, "BL": 0.0008086811405972931}

Mean online (ms): {"cP": 428.78563509375, "cPaa": 428.5986659375, "rT": 2258.180544984375, "BL": 19.011969140625, "BLaa": 18.99490628125}

BL table: {"entries": 10282240, "alpha": 1.2746936316175798e-05, "covered_points": 648782602, "steps": 648284870, "duplicate_points": 4154, "ns_per_step": 266.73730071473057, "rounds": 10290176, "precompute_ms": 172921.756318, "budget_ms": 172919.811755}

BL model check: {"mean_steps": 74793.890625, "model_steps": 83658.68850904191, "measured_over_model": 0.8940361360902306, "class": "model check, secondary"}

Matched fraction: 0.9941383787113465

Host class: "INTEL(R) XEON(R) PLATINUM 8573C | avx512=y gfni=y vpclmulqdq=y avx2=y bmi2=y"

Checks: {"all_executed_rows_valid": true, "one_scalar_per_point_every_arm": true, "oracle_replay": true, "one_relation_per_point_every_ic_process": true, "one_probe_count_per_point_every_ic_process": true, "bl_and_blaa_steps_identical": true, "bl_rows_loaded_this_jobs_table": true, "q0_ic_matches_archived_feistel_identity": true, "q0_every_arm_recovers_the_sidecar_scalar": true, "bl_step_identity_q0_831000": true, "rank_tables_equal_archived": true, "bl_positive_control_pass": true, "bl_positive_control_rows_equal_archived": true, "ic_budget_pass": true, "bl_precompute_pass_at_this_jobs_P_IC": true, "bl_table_checks_pass": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"ic_aa_cold_inside_0.97_1.03": true, "ic_aa_online_inside_0.95_1.05": true, "bl_aa_interval_inside_0.9_1.1": true}
