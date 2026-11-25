# n=83 Z[tau]-multiplier closure (M38 primary, M10 secondary): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_kP_cP_over_kM38_cM38 | 6.4444 [6.0993, 6.7853] (n=20) |
| aa_e2e_kM38_cM38_over_kM38aa_cM38aa | 0.9977 [0.9940, 1.0015] (n=20) |
| aa_cold_cM38_over_cM38aa | 0.9981 [0.9944, 1.0017] (n=20) |
| planted_rank_attempt_kM38X_over_kM38 | 1.8304 [1.7954, 1.8730] (n=64) |
| rank_attempt_kM38_over_kM38aa | 0.9956 [0.9823, 1.0100] (n=256) |
| secondary_e2e_kP_cP_over_kM10_cM10 | 4.5318 [4.1827, 4.8771] (n=20) |
| secondary_e2e_kM10_cM10_over_kM38_cM38 | 1.4220 [1.3381, 1.5204] (n=20) |
| cold_without_rank_cP_over_cM38 | 0.9760 [0.9608, 0.9888] (n=20) |
| setup_cP_over_cM38 | 0.9803 [0.9762, 0.9845] (n=20) |
| online_cP_over_cM38 | 0.7860 [0.3828, 1.4402] (n=20) |
| index_build_cP_over_cM38 | 0.9765 [0.9722, 0.9809] (n=20) |
| peak_rss_cP_over_cM38 | 0.9883 [0.9882, 0.9884] (n=20) |
| cold_without_rank_cP_over_cM10 | 1.0116 [1.0008, 1.0228] (n=20) |
| online_cP_over_cM10 | 1.6329 [0.8628, 2.8370] (n=20) |
| e2e_cold_gap_kP_cP_over_rT | 67.4559 [56.3980, 82.4499] (n=20) |
| e2e_cold_gap_kM38_cM38_over_rT | 10.4674 [8.8168, 12.6875] (n=20) |
| e2e_cold_gap_kM10_cM10_over_rT | 14.8849 [12.2379, 18.0775] (n=20) |
| online_gap_cP_over_rT | 0.1689 [0.0929, 0.2612] (n=20) |
| online_gap_cM38_over_rT | 0.2149 [0.1290, 0.3123] (n=20) |
| online_gap_cM10_over_rT | 0.1034 [0.0664, 0.1516] (n=20) |
| probe law kP (mean probes per relation / law) | 0.9948 [0.9376, 1.0493] (n=2400) |
| probe law kM38 (mean probes per relation / law) | 0.9625 [0.8147, 1.1449] (n=256) |
| probe law kM10 (mean probes per relation / law) | 1.0572 [0.9163, 1.2332] (n=480) |

End-to-end means (ms): {"kP+cP": 124138.98490895, "kM38+cM38": 19263.2005065, "kM10+cM10": 27392.653087225, "rank_share": {"kP": 0.870163243118013, "kM38": 0.14274707572981674, "kM10": 0.4183770346242864}}

Mean cold without rank (ms): {"cP": 16117.8, "cM38": 16513.4, "cM38aa": 16545.3, "cM10": 15932.2}

S end-to-end cold: {"kP+cP": 7.188173826535081, "kM38+cM38": 1.1154210242469738, "kM10+cM10": 1.5861508139877667}

S online: {"cP": 0.01639345709378197, "cM38": 0.020855667663318454, "cM38aa": 0.020570800732487446, "cM10": 0.010039690476991166}

Rank stage: {"rank_stage_kP_over_kM38": 39.28377895332281, "rank_stage_kP_over_kM10": 9.425556240624964, "rank_stage_kM10_over_kM38": 4.16779423414889, "rank_stage_kM38X_over_kM38": 1.9178770356628967, "rank_stage_kM38_over_kM38aa": 0.9956436498982648}

Mean rank stage (ms): {"kP": 108021.18170575, "kM38": 2749.7655415, "kM38aa": 2761.7968956875, "kM38X": 5273.7121855, "kM10": 11460.456969125}

ns per probe: {"kP": 104.63402045671518, "kM38": 105.03070659159737, "kM38aa": 105.49030116178561, "kM38X": 192.68525136597592, "kM10": 104.36761813630997}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "q0_matches_archived_and_frozen_identities": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_block": true, "primary_probe_law_inside_frozen_band": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
