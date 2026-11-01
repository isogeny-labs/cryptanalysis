# volcano-n19-native-tau6-v3-20261020 result

**Verdict: improvement**

| statistic | estimate [95%, two-stage paired bootstrap] |
| --- | --- |
| primary_cold_cpu_B_over_N | 141 [136.8, 145] (20 points, 60 pairs) |
| primary_geo_mean_pair_ratio | 140.1 [135.9, 144.1] (20 points, 60 pairs) |
| online_cpu_B_over_N | 206.7 [203.3, 209.8] (20 points, 60 pairs) |
| setup_cpu_B_over_N | 1.29 [1.279, 1.297] (20 points, 60 pairs) |
| cold_wall_B_over_N | 141.2 [137.1, 145.2] (20 points, 60 pairs) |
| gb_cpu_B_over_N | 911.3 [908.9, 913.7] (20 points, 60 pairs) |
| launcher_wall_B_over_N | 12.96 [12.39, 13.52] (20 points, 60 pairs) |
| child_cpu_B_over_N | 12.81 [12.2, 13.42] (20 points, 60 pairs) |
| aa_cold_cpu_N_over_Naa | 1 [0.9964, 1.004] (20 points, 60 pairs) |
| aa_launcher_wall_N_over_Naa | 1.005 [1, 1.011] (20 points, 60 pairs) |
| planted_cold_cpu_NX_over_N | 140.8 [136.6, 144.6] (20 points, 20 pairs) |
| cold_gap_N_over_rho_geo | 117.9 [113.4, 122.6] (20 points, 60 pairs) |

Mean per arm: {"B": {"cold_cpu": 48.2229285211, "online_cpu": 48.08186927138333, "setup_cpu": 0.14105924971666667, "cold_wall": 48.305339877133314, "gb_cpu": 47.794604514383316, "launcher_wall": 50.4425478941, "child_cpu": 49.43925814999999, "processes": 60, "gb_calls_mean": 5446.4, "solve_ms_per_call": 8.775448831224903}, "N": {"cold_cpu": 0.3421072786, "online_cpu": 0.2330105776285714, "setup_cpu": 0.10909670097142858, "cold_wall": 0.34216134710000495, "gb_cpu": 0.05252359193571309, "launcher_wall": 2.5116819768285716, "child_cpu": 2.474971564285708, "processes": 140, "gb_calls_mean": 5446.4, "solve_ms_per_call": 0.009643726486433808}, "Naa": {"cold_cpu": 0.3420428973833333, "online_cpu": 0.23329089719999999, "setup_cpu": 0.10875200018333334, "cold_wall": 0.34207453383333, "gb_cpu": 0.052535110416669216, "launcher_wall": 1.4705659391333334, "child_cpu": 1.43589631666666, "processes": 60, "gb_calls_mean": 5446.4, "solve_ms_per_call": 0.009645841366162825}, "NX": {"cold_cpu": 48.2165964995, "online_cpu": 48.0744928385, "setup_cpu": 0.142103661, "cold_wall": 48.30066706659999, "gb_cpu": 47.79339764779998, "launcher_wall": 50.2011312351, "child_cpu": 49.436661950000065, "processes": 20, "gb_calls_mean": 5446.4, "solve_ms_per_call": 8.775227241443885}}

S: {"B": {"cold": 4429.3481909660195, "online": 4416.391687665351, "setup": 12.95650330066867}, "N": {"cold": 31.42306579162216, "online": 21.40237045212777, "setup": 10.020695339494393}, "Naa": {"cold": 31.41715228047051, "online": 21.428118224498256, "setup": 9.989034055972256}, "NX": {"cold": 4428.766585300847, "online": 4415.714151259961, "setup": 13.052434040885595}}

Ratio when B first / N first: 143.10724138914188 / 139.2368549462605

Ratio by pair position: {"1": 141.62056759557225, "2": 140.45523847838453, "3": 140.9766490578655}

Gates: {"receipt_rows_match_schedule": true, "rows_in_schedule_order": true, "every_scheduled_row_valid": true, "raw_records_verified": true, "relation_digests_recomputed": true, "runner_identity_matches_frozen_files": true, "schedule_and_panel_regenerate": true, "native_library_one_digest": true, "placement_pinned_every_process": true, "host_cpu_identity_unchanged": true, "tier1_counters_recorded": true, "s0_passed": true, "o1_passed": true, "field_check_every_native_process": true, "counts_and_log_identical_per_point": true, "relations_identical_per_point": true, "planted_compared_every_call": true, "generator_equals_archived": true, "rho_verified": true, "warm_batch_reproduced": true, "sage_smoke_gate_passed": true, "all_primary_pairs_complete": true, "all_aa_pairs_complete": true, "all_planted_pairs_complete": true}

Controls: {"aa_estimate_inside_window": true, "planted_lower_bound_above_1": true}

Gate-name audit: {"unknown": [], "missing": [], "protocol_differs": [], "not_true": []}
