# n=83 field-ops-2 (R1) vs field-ops on D4 (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 1.0504 [1.0467, 1.0541] (n=36) |
| primary_e2e_geometric_mean_of_pair_ratios | 1.0506 [1.0469, 1.0541] (n=36) |
| stage_secondary_index_build_A_over_B | 1.0745 [1.0721, 1.0772] (n=36) |
| stage_secondary_scan_selftest_A_over_B | 1.0027 [0.9947, 1.0108] (n=36) |
| stage_secondary_rank_stage_A_over_B | 1.0505 [1.0461, 1.0550] (n=36) |
| stage_secondary_online_A_over_B | 1.0232 [1.0091, 1.0314] (n=36) |
| cold_A_over_B | 1.0503 [1.0460, 1.0544] (n=36) |
| cpu_time_A_over_B | 1.0430 [1.0403, 1.0463] (n=36) |
| process_wall_A_over_B | 1.0430 [1.0403, 1.0463] (n=36) |
| setup_A_over_B | 1.0575 [1.0553, 1.0599] (n=36) |
| rank_process_index_build_A_over_B | 1.0744 [1.0722, 1.0764] (n=36) |
| peak_rss_A_over_B | 1.0000 [0.9999, 1.0000] (n=36) |
| cold_minor_faults_A_over_B | 1.0000 [1.0000, 1.0000] (n=36) |
| aa_e2e_B_over_Baa | 0.9995 [0.9969, 1.0019] (n=24) |
| aa_cold_B_over_Baa | 0.9987 [0.9958, 1.0015] (n=24) |
| aa_cpu_time_B_over_Baa | 1.0008 [0.9987, 1.0029] (n=24) |
| planted_index_build_cD4R1X_over_cD4R1 | 3.0054 [2.9892, 3.0195] (n=12) |
| planted_cold_cD4R1X_over_cD4R1 | 2.2156 [2.1094, 2.3312] (n=12) |
| probe law kD4FO (mean probes per relation / law) | 0.9916 [0.7738, 1.2394] (n=144) |
| probe law kD4R1 (mean probes per relation / law) | 0.9916 [0.7772, 1.2420] (n=144) |

Mean per side (ms; A = kD4FO+cD4FO (field-ops), B = kD4R1+cD4R1 (field-ops-2), both on D4): {"A": {"e2e": 5281.308276277778, "rank_stage": 1877.7204426666667, "cold": 3403.5878336111114, "cpu_time": 10596.474472222228, "process_wall": 10598.434069527777, "setup": 2708.4381016666666, "index_build": 2107.128985083333, "scan_selftest": 208.63376375, "rank_process_index_build": 2103.778706972222, "cold_minor_faults": 358443.9166666667, "online": 695.1497319444444, "peak_rss": 915321059.5555556}, "B": {"e2e": 5027.996559388889, "rank_stage": 1787.4109079444445, "cold": 3240.5856514444445, "cpu_time": 10159.52030555555, "process_wall": 10161.417509277779, "setup": 2561.2153270833332, "index_build": 1960.9818120277778, "scan_selftest": 208.07605508333333, "rank_process_index_build": 1958.0306481388889, "cold_minor_faults": 358445.80555555556, "online": 679.3703243611111, "peak_rss": 915349845.3333334}}

Per-point ratio: {"s000": 1.0512793531594042, "s001": 1.046773391919286, "s002": 1.0478606477785173, "s003": 1.0541574837344507, "s004": 1.0553934486000152, "s005": 1.049935813241917, "s006": 1.060056924005682, "s007": 1.0462799629251336, "s008": 1.0548734376096827, "s009": 1.0510271871508354, "s010": 1.0503166067683285, "s011": 1.0374353050980993}

Ratio by pair position: {"1": 1.0504307304617713, "2": 1.048554710531675, "3": 1.0520978971059807}

Ratio when A first / B first: 1.052732946040703 / 1.049242262047098

Observed CV per side: {"A": {"e2e": 0.20916275340026166, "rank_stage": 0.5325164080578104, "online": 0.7453311710773167, "index_build": 0.00917380870272523, "scan_selftest": 0.01834526993742923, "cold": 0.14951008046421102}, "B": {"e2e": 0.2103955708613875, "rank_stage": 0.5328374176937556, "online": 0.7416313751744101, "index_build": 0.009610308035486051, "scan_selftest": 0.016974765612471687, "cold": 0.1537972812323461}}

Rank stage: {"kD4FO": {"processes": 36, "mean_rank_stage_ms": 1877.7204426666667, "mean_attempt_ms": 469.4220725833333, "ns_per_probe": 115.71287702725313}, "kD4R1": {"processes": 60, "mean_rank_stage_ms": 1776.3438622833332, "mean_attempt_ms": 444.07821740833333, "ns_per_probe": 110.27723828568352}, "kD4R1aa": {"processes": 24, "mean_rank_stage_ms": 1757.9273742083333, "mean_attempt_ms": 439.47417739583335, "ns_per_probe": 110.36134627157236}}

S end-to-end cold: {"A": 0.22389183457359646, "B": 0.21315312703251488}

E2E cold gap over rT: {"A": 2.145539250692831, "B": 2.0426309933417666}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "every_ic_row_ran_its_arms_rank_probe_pipeline": true, "every_ic_row_ran_its_arms_field_ops_pipeline": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "probe_law_attempts_at_least_64": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "every_row_ran_its_arms_binary": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
