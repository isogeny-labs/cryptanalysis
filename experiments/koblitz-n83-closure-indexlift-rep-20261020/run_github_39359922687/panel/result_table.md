# n=83 closure + index lift replication (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 7.4133 [7.1999, 7.6362] (n=30) |
| primary_e2e_geometric_mean_of_pair_ratios | 7.4164 [7.2100, 7.6469] (n=30) |
| rank_stage_A_over_B | 38.3338 [34.9034, 42.5698] (n=30) |
| cold_A_over_B | 0.9788 [0.9564, 1.0023] (n=30) |
| cpu_time_A_over_B | 4.2193 [4.1257, 4.3167] (n=30) |
| process_wall_A_over_B | 4.2192 [4.1251, 4.3185] (n=30) |
| setup_A_over_B | 0.9782 [0.9737, 0.9829] (n=30) |
| index_build_A_over_B | 0.9730 [0.9683, 0.9778] (n=30) |
| online_A_over_B | 1.0088 [0.2789, 3.2201] (n=30) |
| peak_rss_A_over_B | 0.9893 [0.9893, 0.9893] (n=30) |
| aa_e2e_B_over_Baa | 0.9991 [0.9942, 1.0049] (n=20) |
| aa_cold_B_over_Baa | 0.9979 [0.9933, 1.0022] (n=20) |
| aa_cpu_time_B_over_Baa | 0.9991 [0.9950, 1.0041] (n=20) |
| planted_rank_attempt_kM38IX_over_kM38I | 1.9418 [1.9072, 1.9747] (n=160) |
| probe law kPI (mean probes per relation / law) | 0.9988 [0.9806, 1.0182] (n=18000) |
| probe law kM38I (mean probes per relation / law) | 0.9883 [0.8754, 1.1164] (n=480) |

Mean per side (ms; A = kPI+cPI, B = kM38I+cM38I): {"A": {"e2e": 161165.43495583333, "rank_stage": 143551.397225, "cold": 17614.037730833334, "cpu_time": 182200.90903333327, "process_wall": 182222.46542996666, "setup": 17261.652747933334, "index_build": 15208.524750933333, "online": 352.3849829, "peak_rss": 1875243554.1333334}, "B": {"e2e": 21740.070469433333, "rank_stage": 3744.7721256, "cold": 17995.298343833332, "cpu_time": 43182.65226666669, "process_wall": 43188.885526, "setup": 17646.00015443333, "index_build": 15630.432839, "online": 349.2981894, "peak_rss": 1895542784.0}}

Per-point ratio: {"s000": 7.144904257780538, "s001": 7.8807519714194365, "s002": 7.789218377368037, "s003": 7.043721147958643, "s004": 7.307127303273297, "s005": 7.250651596708462, "s006": 7.508407360983229, "s007": 7.006992593718652, "s008": 7.523225946267617, "s009": 7.759606201874427}

Ratio by pair position: {"1": 7.311376102660509, "2": 7.541110741536859, "3": 7.388335991311211}

Ratio when A first / B first: 7.554611675926032 / 7.0984862325618705

Rank stage: {"kPI": {"processes": 30, "mean_rank_stage_ms": 143551.397225, "mean_attempt_ms": 239.06933800805555, "ns_per_probe": 138.52703339330844}, "kM38I": {"processes": 60, "mean_rank_stage_ms": 3765.91461345, "mean_attempt_ms": 235.36430919270833, "ns_per_probe": 140.07639245600032}, "kM38Iaa": {"processes": 20, "mean_rank_stage_ms": 3704.88161925, "mean_attempt_ms": 231.549738359375, "ns_per_probe": 139.89750531630378}, "kM38IX": {"processes": 10, "mean_rank_stage_ms": 7601.7363124, "mean_attempt_ms": 475.103386525, "ns_per_probe": 274.5479193980497}}

S end-to-end cold: {"A": 7.05873608678698, "B": 0.9521732745854304}

E2E cold gap over rT: {"A": 62.525605978154545, "B": 8.434259371320003}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
