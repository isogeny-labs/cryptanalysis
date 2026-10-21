# n=83 online frame, round 2 (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 1.0165 [1.0110, 1.0221] (n=64) |
| primary_e2e_geometric_mean_of_pair_ratios | 1.0162 [1.0110, 1.0221] (n=64) |
| rank_stage_A_over_B | 1.0035 [0.9964, 1.0115] (n=64) |
| cold_A_over_B | 1.0233 [1.0167, 1.0304] (n=64) |
| cpu_time_A_over_B | 1.0150 [1.0099, 1.0204] (n=64) |
| process_wall_A_over_B | 1.0150 [1.0097, 1.0204] (n=64) |
| setup_A_over_B | 1.0021 [0.9999, 1.0044] (n=64) |
| online_stage_secondary_A_over_B | 1.5541 [1.5324, 1.5766] (n=64) |
| layout_online_cM38OS_over_cM38OF | 1.5794 [1.5456, 1.6130] (n=16) |
| layout_cold_cM38OS_over_cM38OF | 1.0217 [1.0124, 1.0306] (n=16) |
| rank_process_online_A_over_B | 1.5585 [1.5426, 1.5728] (n=64) |
| index_build_A_over_B | 1.0030 [1.0007, 1.0055] (n=64) |
| scan_selftest_A_over_B | 0.9984 [0.9937, 1.0029] (n=64) |
| rank_process_index_build_A_over_B | 1.0043 [1.0016, 1.0075] (n=64) |
| peak_rss_A_over_B | 1.0000 [1.0000, 1.0000] (n=64) |
| cold_minor_faults_A_over_B | 1.0000 [1.0000, 1.0000] (n=64) |
| aa_e2e_B_over_Baa | 1.0009 [0.9962, 1.0063] (n=16) |
| aa_cold_B_over_Baa | 1.0006 [0.9971, 1.0050] (n=16) |
| aa_cpu_time_B_over_Baa | 1.0009 [0.9974, 1.0045] (n=16) |
| planted_online_cM38OFX_over_cM38OF | 2.6404 [2.6137, 2.6625] (n=16) |
| planted_cold_cM38OFX_over_cM38OF | 1.0611 [1.0412, 1.0816] (n=16) |
| probe law kM38IC (mean probes per relation / law) | 1.0236 [0.9383, 1.1083] (n=1024) |
| probe law kM38OF (mean probes per relation / law) | 1.0236 [0.9340, 1.1156] (n=1024) |

Mean per side (ms; A = kM38IC+cM38IC, B = kM38OF+cM38OF): {"A": {"e2e": 13105.501537640625, "rank_stage": 4447.197586296875, "cold": 8658.30395134375, "cpu_time": 26005.501687499956, "process_wall": 26011.6170141875, "setup": 8155.1517700625, "index_build": 6438.679791515625, "scan_selftest": 1336.6462258125, "rank_process_index_build": 6439.189578015625, "cold_minor_faults": 730115.25, "online": 503.15218128125, "rank_process_online": 502.19792803125, "peak_rss": 1895574464.0}, "B": {"e2e": 12893.223696828125, "rank_stage": 4431.71769728125, "cold": 8461.505999546875, "cpu_time": 25621.704593750026, "process_wall": 25627.966409140627, "setup": 8137.7547999375, "index_build": 6419.263713828125, "scan_selftest": 1338.7839581875, "rank_process_index_build": 6411.568379140625, "cold_minor_faults": 730120.46875, "online": 323.751199609375, "rank_process_online": 322.233183515625, "peak_rss": 1895633088.0}}

Online ns per probe: {"cM38IC": 250.1325677753507, "cM38OF": 160.1674318571274, "cM38OFX": 422.2875194661757, "cM38OFaa": 159.1237480958716, "cM38OS": 250.39047521160148, "kM38IC": 249.65817886358516, "kM38OF": 159.85818623665992, "kM38OFaa": 159.72999203689284}

Per-point ratio: {"s000": 1.004950904761113, "s001": 1.0124829941293048, "s002": 1.0313253161423686, "s003": 1.0132835306794168, "s004": 1.0129295925376416, "s005": 1.026366452311322, "s006": 1.0122574861711842, "s007": 1.0222203130019147, "s008": 1.0030459684958746, "s009": 1.0047882606339928, "s010": 1.021991117174248, "s011": 1.001854238045197, "s012": 1.0081004513659066, "s013": 1.0168987028523464, "s014": 1.039375937690764, "s015": 1.0275757440552609}

Ratio by pair position: {"1": 1.016203291122125, "2": 1.0213061512485084, "3": 1.0150280134726277, "4": 1.0136730824225666}

Ratio when A first / B first: 1.0172937372422928 / 1.0153962410048027

Rank stage: {"kM38IC": {"processes": 64, "mean_rank_stage_ms": 4447.197586296875, "mean_attempt_ms": 277.94405047070313, "ns_per_probe": 159.7195275200665}, "kM38OF": {"processes": 80, "mean_rank_stage_ms": 4459.6762859375, "mean_attempt_ms": 278.72415252265625, "ns_per_probe": 159.27574290704723}, "kM38OFaa": {"processes": 16, "mean_rank_stage_ms": 4564.2468745625, "mean_attempt_ms": 285.259756765625, "ns_per_probe": 159.45802957820385}}

S end-to-end cold: {"A": 0.497105308327363, "B": 0.48905338897081757}

E2E cold gap over rT: {"A": 5.430353805171374, "B": 5.342395036306337}

Online gap over rT: {"A": 0.23161186481881887, "B": 0.149029700890718}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_root_call_and_relation_check_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "every_row_ran_its_arms_binary": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true, "all_layout_pairs_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
