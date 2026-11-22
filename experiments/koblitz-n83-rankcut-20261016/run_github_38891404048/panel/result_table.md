# n=83 rank cut (point-addition partner roots): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_kS_cS_over_kR_cR | 1.3336 [1.3300, 1.3377] (n=20) |
| aa_e2e_kR_cR_over_kRaa_cS | 0.9997 [0.9977, 1.0018] (n=20) |
| aa_cold_cR_over_cS | 0.9982 [0.9946, 1.0013] (n=20) |
| planted_rank_attempt_kRX_over_kR | 1.8749 [1.8708, 1.8787] (n=2400) |
| rank_attempt_kS_over_kR | 1.3770 [1.3735, 1.3813] (n=2400) |
| rank_attempt_kR_over_kRaa | 0.9999 [0.9976, 1.0023] (n=2400) |
| rank_attempt_kS_over_kR_short_tercile | 1.3766 [1.3737, 1.3794] (n=800) |
| rank_attempt_kS_over_kR_middle_tercile | 1.3772 [1.3742, 1.3811] (n=800) |
| rank_attempt_kS_over_kR_long_tercile | 1.3770 [1.3732, 1.3811] (n=800) |
| secondary_e2e_kS_cS_over_kR_cRI | 1.3735 [1.3702, 1.3772] (n=20) |
| cold_without_rank_cR_over_cRI | 1.3377 [1.3337, 1.3419] (n=20) |
| online_cR_over_cRI | 0.9999 [0.9981, 1.0020] (n=20) |
| cold_without_rank_cS_over_cR | 1.0018 [0.9988, 1.0055] (n=20) |
| setup_cS_over_cR | 1.0018 [0.9987, 1.0055] (n=20) |
| online_cS_over_cR | 1.0056 [0.9974, 1.0121] (n=20) |
| peak_rss_cS_over_cR | 1.0000 [0.9998, 1.0001] (n=20) |
| e2e_cold_gap_kS_cS_over_rT | 87.5699 [74.1352, 107.2251] (n=20) |
| e2e_cold_gap_kR_cR_over_rT | 65.6656 [55.3831, 80.2071] (n=20) |
| e2e_cold_gap_kR_cRI_over_rT | 63.7561 [53.9974, 77.8282] (n=20) |
| online_gap_cS_over_rT | 0.1107 [0.0602, 0.1752] (n=20) |
| online_gap_cR_over_rT | 0.1101 [0.0590, 0.1744] (n=20) |

End-to-end means (ms): {"kS+cS": 260973.1872561, "kR+cR": 195694.6447286, "kR+cRI": 190003.92108065, "rank_share_kS": 0.9134605668984406, "rank_share_kR": 0.884801535365902}

Mean cold without rank (ms): {"cS": 22584.5, "cR": 22543.7, "cRI": 16853.0}

S end-to-end cold: {"cS (kS)": 10.032179679887598, "cR (kR)": 7.52277986467054, "cRI (kR)": 7.304020371616584}

S online: {"cS": 0.01151681053684272, "cR": 0.011452521443808011, "cRI": 0.011453125318139468}

Rank stage: {"rank_stage_kS_over_kR": 1.3767683859792486, "single_process_e2e_kS_over_kR": 1.3336358499247458, "rank_stage_kRX_over_kR": 1.8742809320049658, "single_process_e2e_kRX_over_kR": 1.7737308306622734, "rank_stage_kR_over_kRaa": 0.9999196437972506, "single_process_e2e_kR_over_kRaa": 0.9999227497892275}

ns per probe: {"kS": 221.84715797580725, "kR": 161.1049393547048, "kRaa": 161.1179528437041, "kRX": 302.0549302705907}

Checks: {"all_executed_rows_valid": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_every_ic_process": true, "one_probe_count_per_point_every_ic_process": true, "q0_matches_archived_feistel_identity": true, "rank_tables_equal_archived": true, "rank_relations_probes_and_root_calls_identical_per_block": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true}
