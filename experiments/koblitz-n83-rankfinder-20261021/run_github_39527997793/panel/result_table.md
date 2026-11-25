# n=83 rank finder (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 1.0196 [1.0147, 1.0255] (n=36) |
| primary_e2e_geometric_mean_of_pair_ratios | 1.0194 [1.0144, 1.0253] (n=36) |
| rank_stage_secondary_A_over_B | 1.0467 [1.0399, 1.0534] (n=36) |
| cold_A_over_B | 1.0026 [0.9961, 1.0100] (n=36) |
| cpu_time_A_over_B | 1.0100 [1.0067, 1.0133] (n=36) |
| process_wall_A_over_B | 1.0100 [1.0067, 1.0133] (n=36) |
| setup_A_over_B | 1.0026 [0.9962, 1.0099] (n=36) |
| index_build_A_over_B | 1.0031 [0.9956, 1.0116] (n=36) |
| scan_selftest_A_over_B | 0.9967 [0.9882, 1.0063] (n=36) |
| rank_process_index_build_A_over_B | 0.9994 [0.9941, 1.0055] (n=36) |
| online_A_over_B | 1.0030 [0.9970, 1.0113] (n=36) |
| peak_rss_A_over_B | 0.9999 [0.9998, 1.0001] (n=36) |
| cold_minor_faults_A_over_B | 1.0001 [0.9941, 1.0064] (n=36) |
| aa_e2e_B_over_Baa | 0.9998 [0.9955, 1.0040] (n=24) |
| aa_cold_B_over_Baa | 0.9982 [0.9928, 1.0036] (n=24) |
| aa_cpu_time_B_over_Baa | 1.0001 [0.9969, 1.0036] (n=24) |
| planted_rank_stage_kM38RFX_over_kM38RF | 1.8688 [1.8541, 1.8845] (n=12) |
| planted_index_build_kM38RFX_over_kM38RF | 0.9996 [0.9948, 1.0040] (n=12) |
| probe law kM38IC (mean probes per relation / law) | 1.0892 [0.9637, 1.2196] (n=576) |
| probe law kM38RF (mean probes per relation / law) | 1.0892 [0.9738, 1.2279] (n=576) |

Mean per side (ms; A = kM38IC+cM38IC, B = kM38RF+cM38RF): {"A": {"e2e": 7416.1376665, "rank_stage": 2937.4611492777776, "cold": 4478.676517222222, "cpu_time": 14434.205777777765, "process_wall": 14437.730438444443, "setup": 4319.6422710277775, "index_build": 3256.238316138889, "scan_selftest": 840.9971583611111, "rank_process_index_build": 3245.1695195277775, "cold_minor_faults": 25460.777777777777, "online": 159.03424619444445, "peak_rss": 1895630506.6666667}, "B": {"e2e": 7273.533708666667, "rank_stage": 2806.4967148055557, "cold": 4467.036993861111, "cpu_time": 14291.830722222243, "process_wall": 14295.320891472222, "setup": 4308.477003111111, "index_build": 3246.3308360555557, "scan_selftest": 843.7667937777778, "rank_process_index_build": 3247.1818158055557, "cold_minor_faults": 25457.472222222223, "online": 158.55999075, "peak_rss": 1895758620.4444444}}

Per-point ratio: {"s000": 1.0191377333020297, "s001": 1.0434517424086263, "s002": 1.015779282153604, "s003": 1.0210516080668393, "s004": 1.0184190223594725, "s005": 1.0208293405663726, "s006": 1.0170185251640222, "s007": 1.0154086223002095, "s008": 1.0079063016979593, "s009": 1.0191310994957494, "s010": 1.0211988679407207, "s011": 1.0163667201585747}

Ratio by pair position: {"1": 1.017271093938666, "2": 1.0239306384848732, "3": 1.0173231098202604}

Ratio when A first / B first: 1.015932863244704 / 1.0232684274873205

Rank stage: {"kM38IC": {"processes": 36, "mean_rank_stage_ms": 2937.4611492777776, "mean_attempt_ms": 183.58598278993057, "ns_per_probe": 99.14287521032621}, "kM38RF": {"processes": 72, "mean_rank_stage_ms": 2763.9564783055557, "mean_attempt_ms": 172.74149167274305, "ns_per_probe": 94.53129839798386}, "kM38RFaa": {"processes": 24, "mean_rank_stage_ms": 2864.867216583333, "mean_attempt_ms": 179.04866448177083, "ns_per_probe": 94.17744661832845}, "kM38RFX": {"processes": 12, "mean_rank_stage_ms": 4524.0192705, "mean_attempt_ms": 282.7455746927083, "ns_per_probe": 175.99880965844505}}

S end-to-end cold: {"A": 0.45531388189534305, "B": 0.44655870979167067}

E2E cold gap over rT: {"A": 4.0011057495563875, "B": 3.924169001446408}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "every_ic_row_ran_its_arms_rank_probe_pipeline": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "every_row_ran_its_arms_binary": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
