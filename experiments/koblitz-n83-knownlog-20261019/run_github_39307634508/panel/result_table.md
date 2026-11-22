# n=83 known-log K220 reference row (seeded scalar orbits, LAnone): frozen result

REFERENCE ROW, not the IC baseline and not an IC improvement. Without relations this is generic BSGS on the Frobenius quotient, bounded by the DKM non-adaptive line: it can never beat rho.

Reading: **measured_above_rho**

| statistic | estimate [95%] |
| --- | --- |
| primary_gap_cL220_over_rT | 2.1919 [1.8584, 2.5893] (n=40) |
| primary_S_e2e_cold_cL220 | 0.2303 [0.2059, 0.2577] (n=40) |
| secondary_reference_not_ic_improvement_e2e_kP_cP_over_cL220 | 27.9894 [24.7842, 31.5336] (n=40) |
| secondary_reference_not_ic_improvement_e2e_kP_cP_over_cL600 | 7.1801 [6.8893, 7.4867] (n=40) |
| e2e_cold_gap_kP_cP_over_rT | 61.3504 [53.2618, 71.2778] (n=40) |
| e2e_cold_gap_cL600_over_rT | 8.5446 [7.4573, 9.8800] (n=40) |
| e2e_cL600_over_cL220 | 3.8982 [3.4860, 4.3638] (n=40) |
| online_gap_cL220_over_rT | 1.1235 [0.8527, 1.4457] (n=40) |
| online_gap_cL600_over_rT | 0.1410 [0.0951, 0.1951] (n=40) |
| online_gap_cP_over_rT | 0.1775 [0.1200, 0.2504] (n=40) |
| cold_cP_over_cL600 | 0.9996 [0.9894, 1.0109] (n=40) |
| aa_e2e_cL220_over_cLaa | 1.0005 [0.9954, 1.0067] (n=40) |

End-to-end means (ms): {"kP+cP": 190268.3317064, "cL600": 26499.565904850002, "cL220": 6797.8592682}

S end-to-end cold: {"kP+cP": 6.446959279081634, "cL600": 0.8978983563356774, "cL220": 0.2303353453197852}

S online: {"cP": 0.017217361967520127, "cL600": 0.013677302563942532, "cL220": 0.10897704194345724}

Mean phases: {"cL600": {"gen_ms": 177.322593425, "base_load_ms": 315.36215635, "index_ms": 23228.2990106, "scan_selftest_ms": 2213.8493451, "log_verify_ms": 91.622237125, "setup_ms": 25918.586730325, "online_ms": 403.6565811, "cold_ms": 26322.243311425, "e2e_ms": 26499.565904850002, "ops": 1562926.075, "peak_rss_bytes": 1875188531.2}, "cL220": {"gen_ms": 78.8208309, "base_load_ms": 285.44933925, "index_ms": 3074.62042425, "scan_selftest_ms": 77.9205285, "log_verify_ms": 33.301302575, "setup_ms": 3502.81214095, "online_ms": 3216.2262963499998, "cold_ms": 6719.0384373, "e2e_ms": 6797.8592682, "ops": 12445556.55, "peak_rss_bytes": 264733900.8}, "cLaa": {"gen_ms": 79.447373125, "base_load_ms": 287.856333125, "index_ms": 3073.30487935, "scan_selftest_ms": 77.1619453, "log_verify_ms": 33.1408672, "setup_ms": 3503.45487225, "online_ms": 3211.528016975, "cold_ms": 6714.982889225, "e2e_ms": 6794.43026235, "ops": 12445556.55, "peak_rss_bytes": 264680038.4}, "cP": {"cold_ms": 26489.6909019, "setup_ms": 25981.55697455, "online_ms": 508.13392735, "index_ms": 23282.829875675, "ops": 1948856.825, "peak_rss_bytes": 1875186073.6}}

Rank stage kP: {"mean_rank_stage_ms": 163778.6408045, "mean_attempt_probes": 1683272.4116666666, "rank_attempt_probes_over_law_K600": 0.9742560337664212, "ns_per_probe": 162.02769720585738}

Probe law: {"cL220": {"orbit_columns": 220, "law_probes": 12851044.886279749, "points": 40, "mean_over_law": 0.968447053148755, "max_over_law": 3.7960126535766947}, "cL600": {"orbit_columns": 600, "law_probes": 1727751.5902664994, "points": 40, "mean_over_law": 0.904601149728315, "max_over_law": 3.508329573619453}, "cP": {"orbit_columns": 600, "law_probes": 1727751.5902664994, "points": 40, "mean_over_law": 1.1279728150615655, "max_over_law": 4.719454489833384}}

Checks: {"all_executed_rows_valid": true, "independent_verification_of_every_base_log": true, "independent_verifier_planted_cases_detected": true, "every_knownlog_process_ran_the_verified_files": true, "one_scalar_per_point_every_ic_process_and_rho": true, "oracle_replay": true, "one_relation_per_point_within_each_base": true, "one_probe_count_per_point_within_each_base": true, "q0_matches_archived_and_frozen_identities": true, "planted_table_refused_by_the_producer": true, "rank_tables_equal_archived": true, "probes_inside_the_law_band": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "planted_table_refused": true, "independent_verifier_planted_detected": true}
