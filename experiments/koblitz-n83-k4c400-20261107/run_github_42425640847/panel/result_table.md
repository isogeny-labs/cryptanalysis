# n=83 K'=4 / 400 orbits vs M38 (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 2.0014 [1.8777, 2.1308] (n=60) |
| primary_e2e_geometric_mean_of_pair_ratios | 2.0242 [1.9049, 2.1519] (n=60) |
| stage_secondary_index_build_A_over_B | 2.3928 [2.3794, 2.4065] (n=60) |
| stage_secondary_scan_selftest_A_over_B | 4.9689 [4.8934, 5.0602] (n=60) |
| stage_secondary_rank_stage_A_over_B | 1.7485 [1.5039, 2.0287] (n=60) |
| stage_secondary_online_A_over_B | 0.6487 [0.3347, 1.1395] (n=60) |
| cold_A_over_B | 2.1757 [2.0530, 2.2975] (n=60) |
| cpu_time_A_over_B | 2.0715 [1.9855, 2.1626] (n=60) |
| process_wall_A_over_B | 2.0713 [1.9871, 2.1588] (n=60) |
| setup_A_over_B | 2.4353 [2.4198, 2.4516] (n=60) |
| rank_process_index_build_A_over_B | 2.3629 [2.3470, 2.3790] (n=60) |
| peak_rss_A_over_B | 2.0740 [2.0740, 2.0741] (n=60) |
| cold_minor_faults_A_over_B | 2.0314 [2.0313, 2.0317] (n=60) |
| aa_e2e_B_over_Baa | 1.0022 [0.9982, 1.0064] (n=40) |
| aa_cold_B_over_Baa | 1.0007 [0.9960, 1.0053] (n=40) |
| aa_cpu_time_B_over_Baa | 1.0016 [0.9991, 1.0043] (n=40) |
| planted_index_build_cD4FOX_over_cD4FO | 2.6961 [2.6802, 2.7099] (n=20) |
| planted_cold_cD4FOX_over_cD4FO | 2.1473 [2.0863, 2.2063] (n=20) |
| probe law kM38FO (mean probes per relation / law) | 1.0018 [0.9233, 1.0897] (n=960) |
| probe law kD4FO (mean probes per relation / law) | 1.0999 [0.9383, 1.2634] (n=240) |

Mean per side (ms; A = kM38FO+cM38FO on M38, B = kD4FO+cD4FO on D4): {"A": {"e2e": 10702.994416716667, "rank_stage": 3814.842887383333, "cold": 6888.151529333333, "cpu_time": 21412.674849999963, "process_wall": 21416.127440433334, "setup": 6589.74266025, "index_build": 5115.8393494, "scan_selftest": 1092.8661268, "rank_process_index_build": 5085.114340133333, "cold_minor_faults": 728151.9833333333, "online": 298.40886908333334, "peak_rss": 1898377079.4666667}, "B": {"e2e": 5347.680183633333, "rank_stage": 2181.7641472833334, "cold": 3165.91603635, "cpu_time": 10336.8012666667, "process_wall": 10339.2261626, "setup": 2705.8761700833334, "index_build": 2137.9972935, "scan_selftest": 219.94089243333335, "rank_process_index_build": 2152.0319897333334, "cold_minor_faults": 358445.15, "online": 460.03986626666665, "peak_rss": 915308680.5333333}}

Per-point ratio: {"s000": 1.9715614677633386, "s001": 2.1142460424989125, "s002": 1.8521910636707748, "s003": 2.105399253544921, "s004": 1.88768512618426, "s005": 2.1452076334696026, "s006": 2.042584175748322, "s007": 2.3359550746886484, "s008": 1.8861724916457283, "s009": 1.9003475102863052, "s010": 1.8337024281098508, "s011": 1.7133023210917933, "s012": 1.5778664737661485, "s013": 1.9759581676390867, "s014": 1.8438279297850915, "s015": 2.3825579745608896, "s016": 2.105048936144563, "s017": 2.375189734010477, "s018": 2.1600846431951717, "s019": 2.132322779432081}

Ratio by pair position: {"1": 2.000701419530839, "2": 2.0306850721891903, "3": 1.973627545569506}

Ratio when A first / B first: 2.0361045891297054 / 1.9690664525348451

Observed CV per side: {"A": {"e2e": 0.08990091361385213, "rank_stage": 0.22211080475089198, "online": 1.0818615248921826, "index_build": 0.016023521772693707, "scan_selftest": 0.048885780768537015, "cold": 0.05333999922277069}, "B": {"e2e": 0.1758618181020901, "rank_stage": 0.4146359212849414, "online": 0.7909673749427554, "index_build": 0.007483704989603814, "scan_selftest": 0.00307885167687139, "cold": 0.1142576922495039}}

Rank stage: {"kD4FO": {"processes": 100, "mean_rank_stage_ms": 2191.48212502, "mean_attempt_ms": 547.86431418, "ns_per_probe": 121.40885944690723}, "kD4FOaa": {"processes": 40, "mean_rank_stage_ms": 2196.33950935, "mean_attempt_ms": 549.0786186375001, "ns_per_probe": 121.1683014739936}}

S end-to-end cold: {"A": 0.4193800817880773, "B": 0.209540476755347}

E2E cold gap over rT: {"A": 4.0999260278750675, "B": 2.0485008512557865}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "every_ic_row_ran_its_arms_rank_probe_pipeline": true, "every_ic_row_ran_its_arms_field_ops_pipeline": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "probe_law_attempts_at_least_64": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "every_row_ran_its_arms_binary": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_e2e_interval_contains_1": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
