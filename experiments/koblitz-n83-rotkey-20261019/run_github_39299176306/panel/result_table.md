# n=83 rotation-key probe (v^83 in F2[X]/(X^83+1) as the rank-stage key): frozen result

Verdict: **not_separated**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_kP_cP_over_kK_cK | 0.9983 [0.9701, 1.0227] (n=20) |
| aa_e2e_kK_cK_over_kKaa_cP | 0.9813 [0.9622, 1.0001] (n=20) |
| aa_cold_cK_over_cP | 1.0012 [0.9926, 1.0100] (n=20) |
| planted_rank_attempt_kKX_over_kK | 3.0543 [2.9489, 3.1728] (n=2400) |
| rank_attempt_kP_over_kK | 1.0156 [0.9820, 1.0450] (n=2400) |
| rank_attempt_kK_over_kKaa | 0.9779 [0.9538, 0.9995] (n=2400) |
| rank_attempt_kP_over_kK_short_tercile | 1.0282 [0.9932, 1.0649] (n=800) |
| rank_attempt_kP_over_kK_middle_tercile | 1.0218 [0.9880, 1.0552] (n=800) |
| rank_attempt_kP_over_kK_long_tercile | 1.0122 [0.9783, 1.0402] (n=800) |
| cold_without_rank_cP_over_cK | 0.9988 [0.9900, 1.0070] (n=20) |
| setup_cP_over_cK | 0.9992 [0.9907, 1.0073] (n=20) |
| online_cP_over_cK | 0.9748 [0.9498, 1.0052] (n=20) |
| peak_rss_cP_over_cK | 1.0000 [1.0000, 1.0000] (n=20) |
| e2e_cold_gap_kP_cP_over_rT | 69.3962 [52.5093, 93.5124] (n=20) |
| e2e_cold_gap_kK_cK_over_rT | 69.5122 [52.4311, 93.0225] (n=20) |
| online_gap_cP_over_rT | 0.1658 [0.1041, 0.2628] (n=20) |
| online_gap_cK_over_rT | 0.1701 [0.1045, 0.2720] (n=20) |

End-to-end means (ms): {"kP+cP": 171019.8645291, "kK+cK": 171305.79388744998, "rank_share_kP": 0.8616900461769154, "rank_share_kK": 0.8617569059222291}

Mean cold without rank (ms): {"cP": 23653.7, "cK": 23681.8}

S end-to-end cold: {"cP (kP)": 7.452988750640492, "cK (kK)": 7.465449456869724}

S online: {"cP": 0.01646986700748482, "cK": 0.01689531489263847}

Rank stage: {"rank_stage_kP_over_kK": 0.9982534274271495, "single_process_e2e_kP_over_kK": 0.9986830251362581, "rank_stage_kKX_over_kK": 3.019388488950571, "single_process_e2e_kKX_over_kK": 2.7446613713914365, "rank_stage_kK_over_kKaa": 0.9782113937956517, "single_process_e2e_kK_over_kKaa": 0.9776942694396703}

ns per probe: {"kP": 143.5538565678961, "kK": 141.34600499266782, "kKaa": 144.53667260769464, "kKX": 431.71313446327196}

Checks: {"all_executed_rows_valid": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_every_ic_process": true, "one_probe_count_per_point_every_ic_process": true, "q0_matches_archived_feistel_identity": true, "rank_tables_equal_archived": true, "rank_relations_probes_root_calls_and_padd_counters_identical_per_block": true, "rotation_key_hits_identical_and_no_collisions_per_block": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true}
