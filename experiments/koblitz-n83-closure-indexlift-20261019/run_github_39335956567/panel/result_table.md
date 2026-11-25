# n=83 closure + index lift (M38I primary, M10I secondary) over the index-lift row: frozen result

Verdict: **improvement**

| statistic | estimate [95%] |
| --- | --- |
| primary_e2e_kPI_cPI_over_kM38I_cM38I | 7.6558 [7.2192, 8.1103] (n=20) |
| aa_e2e_kM38I_cM38I_over_kM38Iaa_cM38Iaa | 1.0001 [0.9979, 1.0023] (n=20) |
| aa_cold_cM38I_over_cM38Iaa | 1.0006 [0.9979, 1.0032] (n=20) |
| planted_rank_attempt_kM38IX_over_kM38I | 1.9607 [1.9470, 1.9747] (n=64) |
| rank_attempt_kM38I_over_kM38Iaa | 0.9981 [0.9948, 1.0014] (n=256) |
| secondary_e2e_kPI_cPI_over_kM10I_cM10I | 4.9504 [4.5846, 5.3402] (n=20) |
| secondary_e2e_kM10I_cM10I_over_kM38I_cM38I | 1.5465 [1.4482, 1.6520] (n=20) |
| cold_without_rank_cPI_over_cM38I | 0.9931 [0.9837, 1.0035] (n=20) |
| setup_cPI_over_cM38I | 0.9830 [0.9806, 0.9855] (n=20) |
| online_cPI_over_cM38I | 1.6445 [1.0217, 2.7261] (n=20) |
| index_build_cPI_over_cM38I | 0.9753 [0.9731, 0.9776] (n=20) |
| peak_rss_cPI_over_cM38I | 0.9884 [0.9883, 0.9885] (n=20) |
| cold_without_rank_cPI_over_cM10I | 1.0063 [0.9880, 1.0242] (n=20) |
| online_cPI_over_cM10I | 0.9638 [0.5122, 1.9636] (n=20) |
| e2e_cold_gap_kPI_cPI_over_rT | 52.4884 [43.9508, 63.5316] (n=20) |
| e2e_cold_gap_kM38I_cM38I_over_rT | 6.8561 [5.7985, 8.1934] (n=20) |
| e2e_cold_gap_kM10I_cM10I_over_rT | 10.6028 [8.8855, 12.8337] (n=20) |
| online_gap_cPI_over_rT | 0.1521 [0.0980, 0.2158] (n=20) |
| online_gap_cM38I_over_rT | 0.0925 [0.0594, 0.1352] (n=20) |
| online_gap_cM10I_over_rT | 0.1578 [0.0790, 0.2707] (n=20) |
| probe law kPI (mean probes per relation / law) | 0.9715 [0.9176, 1.0230] (n=2400) |
| probe law kM38I (mean probes per relation / law) | 1.0304 [0.8728, 1.1825] (n=256) |
| probe law kM10I (mean probes per relation / law) | 1.0605 [0.9475, 1.1930] (n=480) |

End-to-end means (ms): {"kPI+cPI": 160520.83940695002, "kM38I+cM38I": 20967.280493399998, "kM10I+cM10I": 32425.512287275, "rank_share": {"kPI": 0.8950942001866276, "kM38I": 0.19127617551605813, "kM10I": 0.48390586529091484}}

Mean cold without rank (ms): {"cPI": 16839.6, "cM38I": 16956.7, "cM38Iaa": 16946.0, "cM10I": 16734.6}

S end-to-end cold: {"kPI+cPI": 6.168883278142615, "kM38I+cM38I": 0.8057813957473043, "kM10I+cM10I": 1.2461260561132976}

S online: {"cPI": 0.016295980653255666, "cM38I": 0.009909307986682124, "cM38Iaa": 0.009868618766859086, "cM10I": 0.01690776772747591}

Rank stage: {"rank_stage_kPI_over_kM38I": 35.82590586811195, "rank_stage_kPI_over_kM10I": 9.156983527274079, "rank_stage_kM10I_over_kM38I": 3.912413488721966, "rank_stage_kM38IX_over_kM38I": 2.3825542578054892, "rank_stage_kM38I_over_kM38Iaa": 0.9980696424401444}

Mean rank stage (ms): {"kPI": 143681.27236225002, "kM38I": 4010.54122375, "kM38Iaa": 4018.297975625, "kM38IX": 9555.33206875, "kM10I": 15690.895580875}

ns per probe: {"kPI": 142.5512568443877, "kM38I": 143.0825028553142, "kM38Iaa": 143.3593695909336, "kM38IX": 280.6320273445729, "kM10I": 142.44908662268753}

Checks: {"all_executed_rows_valid": true, "pre_timing_tables_and_closure_bases_verified": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_per_point_and_base": true, "one_probe_count_per_point_and_base": true, "one_index_and_layout_digest_set_per_base_equal_frozen": true, "q0_matches_archived_and_frozen_identities": true, "rank_tables_equal_frozen_verified_tables": true, "rank_relations_probes_root_calls_and_counters_identical_per_block": true, "primary_probe_law_inside_frozen_band": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "all_rank_blocks_complete": true}

Controls: {"aa_e2e_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true, "planted_exactness_corruptions_rejected": true}
