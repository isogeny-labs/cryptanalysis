# n=83 index build, round 2 (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 1.1169 [1.1110, 1.1231] (n=36) |
| primary_e2e_geometric_mean_of_pair_ratios | 1.1178 [1.1120, 1.1238] (n=36) |
| rank_stage_A_over_B | 1.0046 [1.0033, 1.0059] (n=36) |
| cold_A_over_B | 1.1816 [1.1746, 1.1891] (n=36) |
| cpu_time_A_over_B | 1.1204 [1.1159, 1.1248] (n=36) |
| process_wall_A_over_B | 1.1204 [1.1159, 1.1249] (n=36) |
| setup_A_over_B | 1.1898 [1.1844, 1.1954] (n=36) |
| index_build_stage_secondary_A_over_B | 1.2574 [1.2563, 1.2586] (n=36) |
| scan_selftest_A_over_B | 0.9979 [0.9750, 1.0214] (n=36) |
| rank_process_index_build_A_over_B | 1.2559 [1.2549, 1.2568] (n=36) |
| online_A_over_B | 1.0082 [1.0068, 1.0098] (n=36) |
| peak_rss_A_over_B | 1.0000 [0.9999, 1.0001] (n=36) |
| cold_minor_faults_A_over_B | 1.0010 [0.9948, 1.0071] (n=36) |
| aa_e2e_B_over_Baa | 0.9996 [0.9968, 1.0024] (n=24) |
| aa_cold_B_over_Baa | 0.9993 [0.9953, 1.0036] (n=24) |
| aa_cpu_time_B_over_Baa | 0.9998 [0.9977, 1.0019] (n=24) |
| planted_index_build_cM38ICX_over_cM38IC | 2.5856 [2.5830, 2.5883] (n=12) |
| planted_cold_cM38ICX_over_cM38IC | 2.1163 [2.0894, 2.1376] (n=12) |
| probe law kM38IB (mean probes per relation / law) | 1.0479 [0.9380, 1.1750] (n=576) |
| probe law kM38IC (mean probes per relation / law) | 1.0479 [0.9378, 1.1716] (n=576) |

Mean per side (ms; A = kM38IB+cM38IB, B = kM38IC+cM38IC): {"A": {"e2e": 12886.268241416667, "rank_stage": 4235.524624222222, "cold": 8650.743617194445, "cpu_time": 25015.507638888877, "process_wall": 25020.377585305556, "setup": 8315.66191575, "index_build": 6501.899560388889, "scan_selftest": 1433.87613325, "rank_process_index_build": 6497.141919, "cold_minor_faults": 25475.055555555555, "online": 335.08170144444443, "peak_rss": 1895713336.8888888}, "B": {"e2e": 11537.473641416667, "rank_stage": 4216.147083111111, "cold": 7321.326558305555, "cpu_time": 22327.108194444445, "process_wall": 22331.031566083333, "setup": 6988.970379416666, "index_build": 5170.840604861111, "scan_selftest": 1436.9416189444444, "rank_process_index_build": 5173.363283611111, "cold_minor_faults": 25450.86111111111, "online": 332.3561788888889, "peak_rss": 1895754069.3333333}}

Per-point ratio: {"s000": 1.1145892247070996, "s001": 1.1257276622844323, "s002": 1.1055607920144466, "s003": 1.1016620451925658, "s004": 1.119889690811442, "s005": 1.116915476094091, "s006": 1.1267299972470741, "s007": 1.120589381341712, "s008": 1.1196038652627012, "s009": 1.1184128827228075, "s010": 1.133049656238539, "s011": 1.1058773940029343}

Ratio by pair position: {"1": 1.1162182805949943, "2": 1.1221748935224156, "3": 1.1126120793833176}

Ratio when A first / B first: 1.1172268250245538 / 1.1162624944268265

Rank stage: {"kM38IB": {"processes": 36, "mean_rank_stage_ms": 4235.524624222222, "mean_attempt_ms": 264.7143666423611, "ns_per_probe": 148.59200949595046}, "kM38IC": {"processes": 60, "mean_rank_stage_ms": 4126.702122183333, "mean_attempt_ms": 257.9130657739583, "ns_per_probe": 147.95060413147348}, "kM38ICaa": {"processes": 24, "mean_rank_stage_ms": 3991.93415275, "mean_attempt_ms": 249.49005389062498, "ns_per_probe": 147.98913552270295}}

S end-to-end cold: {"A": 0.5061202045265897, "B": 0.4531450385571041}

E2E cold gap over rT: {"A": 4.932650592525977, "B": 4.416354302689129}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "every_row_ran_its_arms_binary": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
