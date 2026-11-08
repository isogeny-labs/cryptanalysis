# n=83 field ops (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 1.0256 [1.0236, 1.0278] (n=36) |
| primary_e2e_geometric_mean_of_pair_ratios | 1.0258 [1.0238, 1.0278] (n=36) |
| stage_secondary_index_build_A_over_B | 1.0500 [1.0484, 1.0515] (n=36) |
| stage_secondary_scan_selftest_A_over_B | 0.9976 [0.9922, 1.0027] (n=36) |
| stage_secondary_rank_stage_A_over_B | 1.0061 [1.0018, 1.0108] (n=36) |
| stage_secondary_online_A_over_B | 0.9974 [0.9920, 1.0038] (n=36) |
| cold_A_over_B | 1.0355 [1.0334, 1.0376] (n=36) |
| cpu_time_A_over_B | 1.0257 [1.0243, 1.0274] (n=36) |
| process_wall_A_over_B | 1.0257 [1.0243, 1.0274] (n=36) |
| setup_A_over_B | 1.0384 [1.0363, 1.0403] (n=36) |
| rank_process_index_build_A_over_B | 1.0510 [1.0495, 1.0524] (n=36) |
| peak_rss_A_over_B | 1.0000 [0.9999, 1.0000] (n=36) |
| cold_minor_faults_A_over_B | 0.9999 [0.9997, 1.0000] (n=36) |
| aa_e2e_B_over_Baa | 0.9997 [0.9984, 1.0009] (n=24) |
| aa_cold_B_over_Baa | 1.0002 [0.9991, 1.0014] (n=24) |
| aa_cpu_time_B_over_Baa | 0.9999 [0.9988, 1.0011] (n=24) |
| planted_index_build_cM38R1X_over_cM38R1 | 2.8145 [2.8067, 2.8209] (n=12) |
| planted_cold_cM38R1X_over_cM38R1 | 2.3099 [2.2613, 2.3512] (n=12) |
| probe law kM38FO (mean probes per relation / law) | 0.9530 [0.8532, 1.0583] (n=576) |
| probe law kM38R1 (mean probes per relation / law) | 0.9530 [0.8542, 1.0615] (n=576) |

Mean per side (ms; A = kM38FO+cM38FO, B = kM38R1+cM38R1): {"A": {"e2e": 8864.116715722223, "rank_stage": 2932.5939681944446, "cold": 5931.522747527778, "cpu_time": 18248.215722222216, "process_wall": 18251.011441416667, "setup": 5526.854096472222, "index_build": 4338.94015275, "scan_selftest": 886.4544918888889, "rank_process_index_build": 4339.774988444445, "cold_minor_faults": 728101.4166666666, "online": 404.6686510555556, "peak_rss": 1898395306.6666667}, "B": {"e2e": 8642.885417222222, "rank_stage": 2914.751780111111, "cold": 5728.133637111111, "cpu_time": 17790.150805555564, "process_wall": 17792.86762561111, "setup": 5322.4139795, "index_build": 4132.277221888889, "scan_selftest": 888.5896358888889, "rank_process_index_build": 4129.064468722222, "cold_minor_faults": 728165.2777777778, "online": 405.71965761111113, "peak_rss": 1898488490.6666667}}

Per-point ratio: {"s000": 1.0230803072996797, "s001": 1.02735772437423, "s002": 1.0287103876997175, "s003": 1.02524545664938, "s004": 1.0238080056447212, "s005": 1.027117661025367, "s006": 1.0233730742834992, "s007": 1.0212035806528057, "s008": 1.0317798084737306, "s009": 1.0261038806852152, "s010": 1.0253665813185777, "s011": 1.024921746212404}

Ratio by pair position: {"1": 1.0258245769343903, "2": 1.025814518115376, "3": 1.0251446897167737}

Ratio when A first / B first: 1.0267696727825004 / 1.0247619229394322

Rank stage: {"kM38FO": {"processes": 36, "mean_rank_stage_ms": 2932.5939681944446, "mean_attempt_ms": 183.28197089930555, "ns_per_probe": 113.1253874483739}, "kM38R1": {"processes": 60, "mean_rank_stage_ms": 2933.3786427, "mean_attempt_ms": 183.331122578125, "ns_per_probe": 112.41378198868787}, "kM38R1aa": {"processes": 24, "mean_rank_stage_ms": 2965.5352394166666, "mean_attempt_ms": 185.34086588541666, "ns_per_probe": 112.53925211810107}}

S end-to-end cold: {"A": 0.3895376145635725, "B": 0.37981550518163726}

E2E cold gap over rT: {"A": 3.2463880430650383, "B": 3.165364443620743}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "every_ic_row_ran_its_arms_rank_probe_pipeline": true, "every_ic_row_ran_its_arms_field_ops_pipeline": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "every_row_ran_its_arms_binary": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
