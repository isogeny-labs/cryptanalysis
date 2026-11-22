# n=83 K899 factor base (rank-probe producer at K899 against K600): frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_kP600_cP600_over_kP899_cP899 | 1.1873 [1.1247, 1.2523] (n=20) |
| aa_e2e_kP899_cP899_over_kP899aa_cP899aa | 0.9988 [0.9966, 1.0008] (n=20) |
| aa_cold_cP899_over_cP899aa | 0.9997 [0.9966, 1.0026] (n=20) |
| planted_rank_attempt_kPX899_over_kP899 | 1.9353 [1.9321, 1.9397] (n=3596) |
| rank_attempt_kP899_over_kP899aa | 0.9984 [0.9957, 1.0012] (n=3596) |
| rank_stage_kP600_over_kP899 | 1.5176 [1.4149, 1.6235] (n=4) |
| secondary_e2e_kP600_cPI600_over_kP899_cPI899 | 1.2586 [1.1888, 1.3330] (n=20) |
| secondary_e2e_kP600_cP600_over_kP899_cPI899 | 1.3011 [1.2304, 1.3747] (n=20) |
| cold_without_rank_cP899_over_cP600 | 2.0766 [2.0555, 2.0954] (n=20) |
| setup_cP899_over_cP600 | 2.1081 [2.1012, 2.1157] (n=20) |
| index_build_cP899_over_cP600 | 2.2515 [2.2461, 2.2577] (n=20) |
| online_cP899_over_cP600 | 0.4825 [0.2688, 0.8733] (n=20) |
| peak_rss_cP899_over_cP600 | 2.0713 [2.0711, 2.0716] (n=20) |
| cold_without_rank_cP600_over_cPI600 | 1.3389 [1.3340, 1.3437] (n=20) |
| cold_without_rank_cP899_over_cPI899 | 1.3783 [1.3734, 1.3833] (n=20) |
| e2e_cold_gap_kP600_cP600_over_rT | 64.6668 [53.7966, 81.2794] (n=20) |
| e2e_cold_gap_kP899_cP899_over_rT | 54.4666 [45.3135, 68.2024] (n=20) |
| e2e_cold_gap_kP899_cPI899_over_rT | 49.6998 [41.4644, 62.0781] (n=20) |
| online_gap_cP600_over_rT | 0.1803 [0.0978, 0.3116] (n=20) |
| online_gap_cP899_over_rT | 0.0870 [0.0583, 0.1265] (n=20) |

End-to-end means (ms): {"kP600+cP600": 173790.3994616, "kP899+cP899": 146377.69426205, "kP600+cPI600": 168101.64300945, "kP899+cPI899": 133566.94567450002, "rank_share_K600": 0.8706692372220693, "rank_share_K899": 0.6811377494955472}

Mean cold without rank (ms): {"cP600": 22476.4, "cP899": 46674.3, "cP899aa": 46689.8, "cPI600": 16787.7, "cPI899": 33863.6}

Mean index build (ms): {"cP600": 19659.8, "cP899": 44263.4, "cP899aa": 44274.6, "cPI600": 13976.6, "cPI899": 31499.8}

S end-to-end cold: {"kP600+cP600": 6.694454955172959, "kP899+cP899": 5.638509858514318, "kP600+cPI600": 6.475322460294941, "kP899+cPI899": 5.145036228054378}

S online: {"cP600": 0.016793429496731127, "cP899": 0.008103528651203059, "cP899aa": 0.008039582034731346, "cPI600": 0.016740599297812537, "cPI899": 0.008037824831978437}

Rank stage: {"mean_rank_stage_kP600_over_kP899": 1.5176412754101132, "ns_per_probe_kP600_over_kP899": 0.9704967905422983, "mean_rank_stage_kPX899_over_kP899": 1.9317814348871805, "ns_per_probe_kPX899_over_kP899": 1.9353154100742591, "mean_rank_stage_kP899_over_kP899aa": 0.9983546245996746, "ns_per_probe_kP899_over_kP899aa": 0.998360676977683}

ns per probe: {"kP600": 142.19339162031488, "kP899": 146.51608640648823, "kP899aa": 146.7566679910044, "kPX899": 283.55483984624834}

Probe law: {"K600": {"attempts": 2400, "mean_probes": 1772065.08625, "law": 1727856.7188981916, "ratio": 1.025585667415756, "se_ratio": 0.02136711943439121}, "K899": {"attempts": 3596, "mean_probes": 754089.2847608454, "law": 769630.4280394781, "ratio": 0.9798070051385291, "se_ratio": 0.016773574659364777}}

Checks: {"all_executed_rows_valid": true, "one_scalar_per_point_both_K_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_K": true, "one_probe_count_per_point_and_K": true, "q0_matches_frozen_identity_per_K": true, "rank_tables_equal_frozen_per_K": true, "k899_rank_arms_identical_relations_probes_root_calls_counters_per_block": true, "probe_law_band_both_K": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true}
