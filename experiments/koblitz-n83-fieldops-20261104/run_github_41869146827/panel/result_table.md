# n=83 field ops (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 1.2610 [1.2541, 1.2681] (n=36) |
| primary_e2e_geometric_mean_of_pair_ratios | 1.2615 [1.2548, 1.2682] (n=36) |
| stage_secondary_index_build_A_over_B | 1.3069 [1.3001, 1.3134] (n=36) |
| stage_secondary_scan_selftest_A_over_B | 1.3165 [1.3077, 1.3269] (n=36) |
| stage_secondary_rank_stage_A_over_B | 1.1996 [1.1894, 1.2099] (n=36) |
| stage_secondary_online_A_over_B | 1.4053 [1.3632, 1.4460] (n=36) |
| cold_A_over_B | 1.2944 [1.2877, 1.3011] (n=36) |
| cpu_time_A_over_B | 1.2226 [1.2181, 1.2276] (n=36) |
| process_wall_A_over_B | 1.2226 [1.2181, 1.2276] (n=36) |
| setup_A_over_B | 1.2910 [1.2850, 1.2968] (n=36) |
| rank_process_index_build_A_over_B | 1.3179 [1.3135, 1.3224] (n=36) |
| peak_rss_A_over_B | 0.9999 [0.9998, 0.9999] (n=36) |
| cold_minor_faults_A_over_B | 1.0001 [1.0000, 1.0003] (n=36) |
| aa_e2e_B_over_Baa | 0.9998 [0.9944, 1.0051] (n=24) |
| aa_cold_B_over_Baa | 0.9998 [0.9949, 1.0062] (n=24) |
| aa_cpu_time_B_over_Baa | 1.0000 [0.9965, 1.0035] (n=24) |
| planted_index_build_cM38FOX_over_cM38FO | 2.7348 [2.7233, 2.7463] (n=12) |
| planted_cold_cM38FOX_over_cM38FO | 2.3256 [2.2926, 2.3526] (n=12) |
| probe law kM38RF (mean probes per relation / law) | 0.9789 [0.8818, 1.0839] (n=576) |
| probe law kM38FO (mean probes per relation / law) | 0.9789 [0.8832, 1.0834] (n=576) |

Mean per side (ms; A = kM38RF+cM38RF, B = kM38FO+cM38FO): {"A": {"e2e": 11318.528972666667, "rank_stage": 3790.41021775, "cold": 7528.118754916666, "cpu_time": 22440.220888888904, "process_wall": 22444.06981266667, "setup": 7287.522490472222, "index_build": 5801.923214972222, "scan_selftest": 1183.987986, "rank_process_index_build": 5820.878874555556, "cold_minor_faults": 728153.3055555555, "online": 240.59626444444444, "peak_rss": 1898120874.6666667}, "B": {"e2e": 8975.731336027779, "rank_stage": 3159.7941433333335, "cold": 5815.937192694444, "cpu_time": 18354.614805555542, "process_wall": 18357.976264916666, "setup": 5644.735597638889, "index_build": 4439.3957775, "scan_selftest": 899.3169041944444, "rank_process_index_build": 4416.797519527778, "cold_minor_faults": 728107.2777777778, "online": 171.20159505555554, "peak_rss": 1898393486.2222223}}

Per-point ratio: {"s000": 1.2589621567245488, "s001": 1.2653196144448462, "s002": 1.2544869048559004, "s003": 1.2522642012879939, "s004": 1.254273941719254, "s005": 1.2660569058421407, "s006": 1.2502728055276013, "s007": 1.2661094704520675, "s008": 1.2711492912739675, "s009": 1.2541410518862335, "s010": 1.2809145476612451, "s011": 1.2598419709531832}

Ratio by pair position: {"1": 1.2554395745116138, "2": 1.2576992523227306, "3": 1.27049915853994}

Ratio when A first / B first: 1.2577383284619348 / 1.2621058001298384

Rank stage: {"kM38RF": {"processes": 36, "mean_rank_stage_ms": 3790.41021775, "mean_attempt_ms": 236.89509542881945, "ns_per_probe": 142.35396703857134}, "kM38FO": {"processes": 60, "mean_rank_stage_ms": 3224.4638271666668, "mean_attempt_ms": 201.52329272083335, "ns_per_probe": 118.46837121972989}, "kM38FOaa": {"processes": 24, "mean_rank_stage_ms": 3322.2901410416666, "mean_attempt_ms": 207.63755233854167, "ns_per_probe": 118.21158787787179}}

S end-to-end cold: {"A": 0.4945575835487647, "B": 0.39219018751011625}

E2E cold gap over rT: {"A": 5.164496572260702, "B": 4.095508685836502}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "every_ic_row_ran_its_arms_rank_probe_pipeline": true, "every_ic_row_ran_its_arms_field_ops_pipeline": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "every_row_ran_its_arms_binary": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
