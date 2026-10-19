# n=83 index lift (lift_scan in the index build): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_shared_cP_over_cPI | 1.0344 [1.0324, 1.0364] (n=20) |
| aa_e2e_shared_cP_over_cPaa | 0.9999 [0.9998, 1.0001] (n=20) |
| aa_cold_cP_over_cPaa | 0.9996 [0.9982, 1.0007] (n=20) |
| sharing_rank_attempt_kPI_over_kP | 0.9981 [0.9966, 0.9994] (n=1800) |
| planted_cold_cPIX_over_cPI | 1.4081 [1.4033, 1.4120] (n=20) |
| secondary_e2e_own_kP_cP_over_kPI_cPI | 1.0361 [1.0346, 1.0377] (n=20) |
| secondary_e2e_shared_cP_over_cPIT | 1.0460 [1.0435, 1.0488] (n=20) |
| cold_without_rank_cP_over_cPI | 1.3376 [1.3340, 1.3406] (n=20) |
| cold_without_rank_cPI_over_cPIT | 1.1233 [1.1202, 1.1261] (n=20) |
| cold_without_rank_cP_over_cPIT | 1.5025 [1.4956, 1.5087] (n=20) |
| cold_without_rank_cPIX_over_cP | 1.0527 [1.0517, 1.0537] (n=20) |
| setup_cP_over_cPI | 1.3457 [1.3442, 1.3471] (n=20) |
| index_build_cP_over_cPI | 1.4021 [1.4004, 1.4036] (n=20) |
| online_cP_over_cPI | 1.0006 [0.9982, 1.0040] (n=20) |
| peak_rss_cP_over_cPI | 0.9999 [0.9998, 1.0000] (n=20) |
| scan_selftest_cP_over_cPI | 1.0020 [0.9984, 1.0059] (n=20) |
| scan_selftest_cPI_over_cPIT | 781.6477 [780.0255, 783.2395] (n=20) |
| online_cPI_over_cPIT | 0.9960 [0.9911, 0.9992] (n=20) |
| e2e_cold_gap_cP_over_rT | 65.1076 [53.9304, 80.9792] (n=20) |
| e2e_cold_gap_cPI_over_rT | 62.9448 [52.4705, 78.5268] (n=20) |
| e2e_cold_gap_cPIT_over_rT | 62.2418 [51.7264, 77.0185] (n=20) |
| online_gap_cP_over_rT | 0.1667 [0.0926, 0.2808] (n=20) |
| online_gap_cPI_over_rT | 0.1666 [0.0914, 0.2830] (n=20) |

End-to-end means (ms): {"shared_rank_stage": 148384.40902316666, "K+cP": 170873.27595891667, "K+cPaa": 170883.08660651668, "K+cPI": 165196.93063266666, "K+cPIT": 163352.07484616665, "K+cPIX": 172058.47093851666, "rank_share_cP": 0.8683886242038396, "rank_share_cPI": 0.8982273971731081}

Mean cold without rank (ms): {"cP": 22488.9, "cPaa": 22498.7, "cPI": 16812.5, "cPIT": 14967.7, "cPIX": 23674.1}

Mean index build (ms): {"cP": 19778.4, "cPaa": 19790.0, "cPI": 14106.3, "cPIT": 14125.8, "cPIX": 20963.0}

S end-to-end cold: {"cP": 6.58454782617137, "cPI": 6.365811648329588, "cPIT": 6.29472071213475}

S online: {"cP": 0.015127658757960877, "cPaa": 0.015126255735135631, "cPI": 0.015118241661328342, "cPIT": 0.015179713439011025, "cPIX": 0.015148305574629577}

Rank stage: {"rank_stage_kPI_over_kP": 0.9981140864331417, "single_process_e2e_kP_over_kPI": 1.0358528310345083}

ns per probe: {"kP": 141.61407928343712, "kPI": 141.3473551868239}

Checks: {"all_executed_rows_valid": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_every_ic_process": true, "one_probe_count_per_point_every_ic_process": true, "one_index_digest_set_every_ic_process": true, "q0_matches_archived_feistel_identity": true, "rank_tables_equal_archived": true, "rank_relations_probes_root_calls_and_counters_identical_per_block": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "sharing_rank_attempt_inside_0.97_1.03": true, "planted_lower_bound_above_1": true}
