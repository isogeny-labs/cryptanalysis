# n=83 index build (paired, repeated alternating pairs): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_paired_A_over_B | 1.7406 [1.7129, 1.7676] (n=36) |
| primary_e2e_geometric_mean_of_pair_ratios | 1.7448 [1.7185, 1.7708] (n=36) |
| rank_stage_A_over_B | 1.0008 [0.9982, 1.0032] (n=36) |
| cold_A_over_B | 2.0756 [2.0299, 2.1139] (n=36) |
| cpu_time_A_over_B | 1.7456 [1.7240, 1.7658] (n=36) |
| process_wall_A_over_B | 1.7455 [1.7238, 1.7662] (n=36) |
| setup_A_over_B | 2.1446 [2.1404, 2.1493] (n=36) |
| index_build_stage_secondary_A_over_B | 2.3574 [2.3539, 2.3611] (n=36) |
| scan_selftest_A_over_B | 1.4583 [1.4480, 1.4708] (n=36) |
| rank_process_index_build_A_over_B | 2.3559 [2.3490, 2.3617] (n=36) |
| online_A_over_B | 0.9947 [0.9888, 1.0006] (n=36) |
| peak_rss_A_over_B | 1.0010 [1.0009, 1.0011] (n=36) |
| cold_minor_faults_A_over_B | 1.0977 [1.0896, 1.1056] (n=36) |
| aa_e2e_B_over_Baa | 0.9998 [0.9984, 1.0011] (n=24) |
| aa_cold_B_over_Baa | 0.9994 [0.9977, 1.0010] (n=24) |
| aa_cpu_time_B_over_Baa | 1.0001 [0.9991, 1.0011] (n=24) |
| planted_index_build_cM38IBX_over_cM38IB | 2.0847 [2.0812, 2.0876] (n=12) |
| planted_cold_cM38IBX_over_cM38IB | 1.8032 [1.7670, 1.8330] (n=12) |
| probe law kM38I (mean probes per relation / law) | 0.9937 [0.8859, 1.1074] (n=576) |
| probe law kM38IB (mean probes per relation / law) | 0.9937 [0.8861, 1.1062] (n=576) |

Mean per side (ms; A = kM38I+cM38I, B = kM38IB+cM38IB): {"A": {"e2e": 24736.50036925, "rank_stage": 4433.481159111111, "cold": 20303.01921013889, "cpu_time": 49371.927027777696, "process_wall": 49380.10496352778, "setup": 19719.420871, "index_build": 17084.83291713889, "scan_selftest": 2233.5950631944443, "rank_process_index_build": 17080.452143555554, "cold_minor_faults": 27904.0, "online": 583.5983391388888, "peak_rss": 1897379157.3333333}, "B": {"e2e": 14211.601843083334, "rank_stage": 4429.868695361111, "cold": 9781.733147722221, "cpu_time": 28283.92325000007, "process_wall": 28289.610969805555, "setup": 9195.047430777779, "index_build": 7247.205447777777, "scan_selftest": 1531.6145028888889, "rank_process_index_build": 7250.164736777778, "cold_minor_faults": 25421.333333333332, "online": 586.6857169444445, "peak_rss": 1895541191.1111112}}

Per-point ratio: {"s000": 1.7225242337898927, "s001": 1.7712722622668644, "s002": 1.6878817029648812, "s003": 1.771868580942074, "s004": 1.7335352623939682, "s005": 1.7391736478213065, "s006": 1.7034656644510604, "s007": 1.7576845586508048, "s008": 1.768979882207315, "s009": 1.7753977214838514, "s010": 1.6832485193345432, "s011": 1.79065805352199}

Ratio by pair position: {"1": 1.7466823038874575, "2": 1.7462192066426125, "3": 1.7291204582020931}

Ratio when A first / B first: 1.7237572857828518 / 1.7653799135442878

Rank stage: {"kM38I": {"processes": 36, "mean_rank_stage_ms": 4433.481159111111, "mean_attempt_ms": 277.08607828472225, "ns_per_probe": 164.02330646146734}, "kM38IB": {"processes": 60, "mean_rank_stage_ms": 4387.971654783333, "mean_attempt_ms": 274.2417324520833, "ns_per_probe": 163.93601267591862}, "kM38IBaa": {"processes": 24, "mean_rank_stage_ms": 4322.2575068333335, "mean_attempt_ms": 270.13471954687503, "ns_per_probe": 163.89858146953767}}

S end-to-end cold: {"A": 0.8418660009189551, "B": 0.483668434568126}

E2E cold gap over rT: {"A": 7.237534859799426, "B": 4.158104914499835}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_seed": true, "primary_probe_law_inside_frozen_band": true, "runner_identity_matches_frozen_files": true, "binaries_unchanged": true, "host_cpu_identity_unchanged": true, "every_row_ran_its_arms_binary": true, "placement_pinned_every_process": true, "receipt_matches_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_present": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
