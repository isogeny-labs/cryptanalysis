# n=83 online frame (the rank stage's frame loop in the one-target online scan): frozen result

Verdict: **improvement**

Classification: pipeline improvement (end-to-end lower bound above 1)

| statistic | estimate [95%] |
| --- | --- |
| primary_online_cS_over_cF | 1.5733 [1.5714, 1.5753] (n=64) |
| aa_online_cF_over_cFaa | 0.9986 [0.9975, 0.9998] (n=64) |
| aa_cold_cF_over_cFaa | 0.9999 [0.9989, 1.0008] (n=64) |
| planted_online_cFX_over_cF | 2.7052 [2.6979, 2.7127] (n=64) |
| online_cS_over_cFaa | 1.5711 [1.5690, 1.5732] (n=64) |
| online_cS_over_cF_geometric | 1.5682 [1.5633, 1.5728] (n=64) |
| online_cS_over_cF_short_tercile | 1.5632 [1.5515, 1.5738] (n=21) |
| online_cS_over_cF_middle_tercile | 1.5728 [1.5694, 1.5760] (n=21) |
| online_cS_over_cF_long_tercile | 1.5742 [1.5720, 1.5766] (n=22) |
| secondary_e2e_cS_over_cF | 1.0008 [1.0006, 1.0010] (n=64) |
| cold_cS_over_cF | 1.0060 [1.0043, 1.0078] (n=64) |
| setup_cS_over_cF | 0.9994 [0.9989, 1.0000] (n=64) |
| index_build_cS_over_cF | 0.9995 [0.9989, 1.0001] (n=64) |
| peak_rss_cS_over_cF | 1.0000 [0.9999, 1.0001] (n=64) |
| online_gap_cS_over_rT | 0.1714 [0.1249, 0.2273] (n=64) |
| online_gap_cF_over_rT | 0.1089 [0.0791, 0.1449] (n=64) |
| e2e_cold_gap_cS_over_rT | 66.5204 [58.2510, 76.5390] (n=64) |
| e2e_cold_gap_cF_over_rT | 66.4685 [58.2375, 76.5783] (n=64) |

Mean online (ms): {"cS": 399.07, "cF": 253.651, "cFaa": 254.008, "cFX": 686.188}

Online ns per probe: {"cS": 222.76, "cF": 141.58, "cFaa": 141.78, "cFX": 383.02}

Mean cold (ms): {"cS": 22310.2, "cF": 22176.9, "cFaa": 22178.3, "cFX": 22604.8}

End-to-end (ms): {"cS": 170862.7273473125, "cF": 170729.47714925001, "rank_stage_K": 148552.574525}

Shared rank stage: {"rank_stage_ms": 148552.574525, "attempts": 600, "ns_per_probe": 141.64844957308105, "mean_attempt_probes": 1746427.9033333333, "process_cold_ms": 171400.850204}

S online: {"cS": 0.015374648484553043, "cF": 0.00977220445007317, "cFaa": 0.009785973012286306, "cFX": 0.026436219399053437}

S end-to-end cold: {"cS": 6.582697185619962, "cF": 6.577563557488261}

Checks: {"all_executed_rows_valid": true, "one_scalar_per_point_ic_and_rho": true, "oracle_replay": true, "one_relation_probe_count_root_calls_and_relation_checks_per_point_every_ic_process": true, "q0_matches_archived_feistel_identity": true, "rank_table_equal_archived": true, "receipt_matches_schedule": true, "every_scheduled_row_present": true, "all_points_complete": true, "shared_rank_process_present": true}

Controls: {"aa_online_inside_0.97_1.03": true, "aa_cold_inside_0.97_1.03": true, "planted_lower_bound_above_1": true}
