# n=83 rank probe (rank-cut loop in the target's Frobenius frame): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_kR_cR_over_kP_cP | 1.1033 [1.1010, 1.1056] (n=20) |
| aa_e2e_kP_cP_over_kPaa_cR | 0.9997 [0.9985, 1.0012] (n=20) |
| aa_cold_cP_over_cR | 1.0003 [0.9989, 1.0018] (n=20) |
| planted_rank_attempt_kPX_over_kP | 1.9699 [1.9666, 1.9730] (n=2400) |
| rank_attempt_kR_over_kP | 1.1194 [1.1175, 1.1214] (n=2400) |
| rank_attempt_kP_over_kPaa | 0.9996 [0.9982, 1.0013] (n=2400) |
| rank_attempt_kR_over_kP_short_tercile | 1.1194 [1.1166, 1.1218] (n=800) |
| rank_attempt_kR_over_kP_middle_tercile | 1.1198 [1.1182, 1.1217] (n=800) |
| rank_attempt_kR_over_kP_long_tercile | 1.1193 [1.1170, 1.1215] (n=800) |
| secondary_e2e_kR_cR_over_kP_cPI | 1.1424 [1.1409, 1.1438] (n=20) |
| cold_without_rank_cP_over_cPI | 1.3425 [1.3366, 1.3474] (n=20) |
| online_cP_over_cPI | 0.9980 [0.9952, 1.0010] (n=20) |
| cold_without_rank_cR_over_cP | 0.9997 [0.9982, 1.0011] (n=20) |
| setup_cR_over_cP | 0.9998 [0.9983, 1.0012] (n=20) |
| online_cR_over_cP | 0.9975 [0.9952, 1.0002] (n=20) |
| peak_rss_cR_over_cP | 1.0000 [0.9998, 1.0001] (n=20) |
| e2e_cold_gap_kR_cR_over_rT | 70.6064 [59.3076, 86.2551] (n=20) |
| e2e_cold_gap_kP_cP_over_rT | 63.9977 [53.7363, 78.0148] (n=20) |
| e2e_cold_gap_kP_cPI_over_rT | 61.8047 [51.4375, 75.2365] (n=20) |
| online_gap_cR_over_rT | 0.1288 [0.0836, 0.1816] (n=20) |
| online_gap_cP_over_rT | 0.1291 [0.0847, 0.1830] (n=20) |

End-to-end means (ms): {"kR+cR": 183147.90168015, "kP+cP": 166005.37990025, "kP+cPI": 160316.98649414998, "rank_share_kR": 0.878280665189755, "rank_share_kP": 0.8656746554364746}

Mean cold without rank (ms): {"cR": 22292.6, "cP": 22298.7, "cPI": 16610.3}

S end-to-end cold: {"cR (kR)": 7.049546871159488, "cP (kP)": 6.389713972891699, "cPI (kP)": 6.170761991623967}

S online: {"cR": 0.011662720400040969, "cP": 0.011692014655211925, "cPI": 0.011715013721847373}

Rank stage: {"rank_stage_kR_over_kP": 1.119330670254582, "single_process_e2e_kR_over_kP": 1.1043182726313545, "rank_stage_kPX_over_kP": 1.968994127725951, "single_process_e2e_kPX_over_kP": 1.8395374675189082, "rank_stage_kP_over_kPaa": 0.9995903025215419, "single_process_e2e_kP_over_kPaa": 0.9995934096985369}

ns per probe: {"kR": 158.44662020514664, "kP": 141.54185392997684, "kPaa": 141.59960060723324, "kPX": 278.8180372529533}

Checks: {"all_executed_rows_valid": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_every_ic_process": true, "one_probe_count_per_point_every_ic_process": true, "q0_matches_archived_feistel_identity": true, "rank_tables_equal_archived": true, "rank_relations_probes_root_calls_and_padd_counters_identical_per_block": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true}
