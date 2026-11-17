# Collector setup counterfactual

Outcome: omitting the indexed metadata entry did not establish a primary improvement over the frozen indexed control in any field. N24 reproduces a collector slowdown from indexed preparation within one binary, with or without that entry. The physical cause remains open. [pcc:unverified]

Standing: unsigned producer evidence, claim PCC-20261117-262375. Invalid for promotion: all 13 failed A/A rows are retained. Native preparation is separately recorded as unsigned PCC-20261117-b8257b. No independently signed speedup verdict or mathematical-novelty conclusion follows. [pcc:unverified]

| Field | Blocks | Failed A/A | II / IA primary, paired median [95%] |
| --- | --- | --- | --- |
| N15 | 42 | 7 | 1.00157 [0.98562, 1.01389] |
| N18 | 42 | 5 | 1.00907 [0.98864, 1.02610] |
| N21 | 42 | 1 | 0.99857 [0.99059, 1.00675] |
| N24 | 42 | 0 | 1.00574 [0.99743, 1.01279] |
| N27 | 42 | 0 | 1.00597 [0.97222, 1.02438] |

The panel completed 210 blocks: 1470 IC, 420 same-target rho and 420 A/A answers. Existing independent Python arithmetic checked all 2310 answers and 10240 exported walk states. There were 0 capped IC arms. [pcc:unverified]

A = frozen anchor ordinary; CI = compact inverse; II = frozen indexed inverse. SP/SA = staged preparation with metadata present/absent. IP/IA = indexed preparation with metadata present/absent. The four new paths use one binary and the same inverse-vector query body. Default behavior stays IP; absence is an experimental control. [pcc:unverified]

Primary includes context plus pipeline through owned oracle cleanup: base/table setup, collector, matrix and scalar check. Prior fixture/calibration/spec/empty allocation, startup/JSON and later context/report destruction are excluded. Collector has its own cleanup boundary. Full-process cold remains open. [pcc:unverified]

# Primary: context + pipeline through owned oracle cleanup

![native-primary](native-primary.svg)

| Effect | N15 | N18 | N21 | N24 | N27 |
| --- | --- | --- | --- | --- | --- |
| SP / IP | 1.00189 [0.99323, 1.02659] | 0.98955 [0.97821, 1.00059] | 0.99623 [0.99208, 1.00360] | 1.00474 [0.99897, 1.01535] | 1.00966 [0.98989, 1.02108] |
| SA / IA | 0.99676 [0.98096, 1.02847] | 1.00360 [0.98687, 1.01684] | 0.99617 [0.98553, 1.00465] | 1.00807 [1.00088, 1.01391] | 1.01008 [0.99618, 1.02690] |
| SP / SA | 0.99624 [0.97323, 1.01891] | 1.00101 [0.98238, 1.01458] | 0.99915 [0.99065, 1.00484] | 0.99419 [0.98931, 1.00679] | 1.00272 [0.99325, 1.01480] |
| IP / IA | 0.99488 [0.98586, 1.00673] | 1.01080 [1.00043, 1.01802] | 0.99578 [0.98704, 1.00652] | 0.99873 [0.99351, 1.00744] | 0.99583 [0.98611, 1.01097] |
| A / IP | 1.04641 [1.02442, 1.07817] | 1.11694 [1.10789, 1.13299] | 1.16048 [1.15679, 1.18206] | 1.21637 [1.19992, 1.22644] | 1.11592 [1.10370, 1.13712] |
| CI / IP | 1.02086 [1.00013, 1.03929] | 0.99434 [0.98354, 1.01097] | 0.99714 [0.98596, 1.00553] | 1.00230 [0.99408, 1.00728] | 1.00564 [0.98199, 1.01611] |
| II / IP | 1.01489 [0.98347, 1.03565] | 1.00045 [0.98393, 1.01021] | 0.99962 [0.98607, 1.01579] | 1.00684 [0.99700, 1.01430] | 1.00254 [0.98754, 1.00953] |
| II / IA | 1.00157 [0.98562, 1.01389] | 1.00907 [0.98864, 1.02610] | 0.99857 [0.99059, 1.00675] | 1.00574 [0.99743, 1.01279] | 1.00597 [0.97222, 1.02438] |
| (SP*IA)/(IP*SA) | 1.02290 [0.98705, 1.03316] | 0.98674 [0.96894, 1.00319] | 1.00664 [0.98780, 1.01844] | 1.00044 [0.98729, 1.01542] | 0.99697 [0.97950, 1.02565] |

Each cell is median reference/candidate time and a pointwise 95% paired bootstrap interval, 10000 resamples, seed 20261116, all 42 rows per field. Above 1 favors the denominator for pairwise effects. The interaction is neutral: it measures relative setup effects, not a standalone optimization direction. No familywise coverage, filtering, host pooling or cross-panel products. [pcc:unverified]

# Collector through owned collector/matrix cleanup

![native-collector](native-collector.svg)

| Effect | N15 | N18 | N21 | N24 | N27 |
| --- | --- | --- | --- | --- | --- |
| SP / IP | 1.00649 [0.97769, 1.01703] | 0.99717 [0.98632, 1.00713] | 1.00109 [0.99530, 1.00811] | 0.97357 [0.96951, 0.97801] | 0.99443 [0.98230, 1.00896] |
| SA / IA | 1.01316 [0.97431, 1.03090] | 0.98397 [0.96322, 0.99902] | 0.99922 [0.99380, 1.00570] | 0.97634 [0.96209, 0.98308] | 0.99198 [0.98524, 1.00284] |
| SP / SA | 0.99774 [0.99270, 1.01178] | 0.98439 [0.97583, 1.01134] | 0.99947 [0.98798, 1.00816] | 0.99749 [0.98961, 1.00629] | 0.99878 [0.99131, 1.01151] |
| IP / IA | 1.00749 [0.99453, 1.02259] | 0.97766 [0.96170, 1.00154] | 1.00198 [0.99153, 1.01054] | 0.99837 [0.99118, 1.00650] | 0.99747 [0.99083, 1.01337] |
| A / IP | 1.04975 [1.01409, 1.06158] | 1.10943 [1.07899, 1.12512] | 1.14437 [1.13207, 1.15555] | 1.07834 [1.06323, 1.09618] | 1.12478 [1.11683, 1.14187] |
| CI / IP | 1.02329 [1.00464, 1.03577] | 1.00835 [0.99600, 1.03384] | 0.99581 [0.98480, 1.00250] | 0.96211 [0.95445, 0.96805] | 0.97967 [0.96880, 0.99321] |
| II / IP | 0.98968 [0.96972, 1.00697] | 1.01049 [0.98577, 1.03336] | 1.00395 [0.99668, 1.01125] | 1.01013 [0.99683, 1.01440] | 0.99447 [0.98783, 1.00682] |
| II / IA | 0.98580 [0.97306, 1.01542] | 1.00262 [0.97382, 1.01510] | 1.00120 [0.99197, 1.01495] | 1.00426 [0.98939, 1.01359] | 1.00263 [0.99101, 1.01460] |
| (SP*IA)/(IP*SA) | 0.98860 [0.96298, 1.01389] | 1.00309 [0.98025, 1.03590] | 0.99630 [0.98431, 1.01749] | 0.99886 [0.99122, 1.01979] | 1.00157 [0.98519, 1.02224] |

Each cell is median reference/candidate time and a pointwise 95% paired bootstrap interval, 10000 resamples, seed 20261116, all 42 rows per field. Above 1 favors the denominator for pairwise effects. The interaction is neutral: it measures relative setup effects, not a standalone optimization direction. No familywise coverage, filtering, host pooling or cross-panel products. [pcc:unverified]

N24 SP/IP and SA/IA intervals lie below 1. The collector slowdown persists without the counter entry; the counter-removal and interaction intervals do not establish a remedy. N27 indexing-effect intervals contain1. These effects identify declared preparation choices in this build, not a cache, allocator or historical cross-binary cause. [pcc:unverified]

# Pair-table preparation, included in primary

![native-setup](native-setup.svg)

| Effect | N15 | N18 | N21 | N24 | N27 |
| --- | --- | --- | --- | --- | --- |
| SP / IP | 1.15434 [1.13859, 1.16530] | 0.98689 [0.94678, 0.99553] | 0.99296 [0.98104, 1.00910] | 1.02348 [1.01671, 1.03178] | 1.01703 [1.00158, 1.03749] |
| SA / IA | 1.15986 [1.13850, 1.17568] | 1.00064 [0.98530, 1.01738] | 0.99387 [0.98623, 1.00127] | 1.02621 [1.01803, 1.03478] | 1.01530 [1.00617, 1.04323] |
| SP / SA | 0.99508 [0.98247, 1.00715] | 1.00083 [0.98073, 1.01291] | 1.00254 [0.99113, 1.00981] | 1.00268 [0.99041, 1.00973] | 1.01002 [0.99196, 1.01520] |
| IP / IA | 0.98669 [0.97851, 1.00097] | 1.01002 [0.99542, 1.03316] | 1.00257 [0.98997, 1.01168] | 0.99639 [0.98585, 1.00396] | 1.00180 [0.97797, 1.01694] |
| A / IP | 1.30442 [1.28980, 1.32054] | 1.15896 [1.11807, 1.20451] | 1.26377 [1.24753, 1.27685] | 1.32101 [1.30133, 1.33575] | 1.12875 [1.10690, 1.14639] |
| CI / IP | 1.15248 [1.13717, 1.16349] | 1.00038 [0.93022, 1.02342] | 1.00017 [0.99344, 1.01373] | 1.03017 [1.01698, 1.04009] | 1.01847 [0.99587, 1.03822] |
| II / IP | 1.00689 [0.99708, 1.02738] | 0.99215 [0.94502, 1.01169] | 0.99299 [0.98267, 1.00536] | 1.00111 [0.99298, 1.01089] | 1.00287 [0.98008, 1.02851] |
| II / IA | 1.00527 [0.98542, 1.01320] | 1.02154 [0.98973, 1.04644] | 0.99729 [0.98397, 1.00577] | 1.00094 [0.99135, 1.00794] | 1.00743 [0.98134, 1.02452] |
| (SP*IA)/(IP*SA) | 0.99486 [0.97068, 1.03523] | 0.99210 [0.93881, 1.00667] | 1.00373 [0.97999, 1.01845] | 1.00427 [0.98381, 1.01829] | 0.99292 [0.96275, 1.02439] |

Each cell is median reference/candidate time and a pointwise 95% paired bootstrap interval, 10000 resamples, seed 20261116, all 42 rows per field. Above 1 favors the denominator for pairwise effects. The interaction is neutral: it measures relative setup effects, not a standalone optimization direction. No familywise coverage, filtering, host pooling or cross-panel products. [pcc:unverified]

# Mean costs and matched same-point rho

| Field | A ms | CI ms | II ms | SP ms | SA ms | IP ms | IA ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| N15 | 0.5490 | 0.5381 | 0.5294 | 0.5282 | 0.5307 | 0.5356 | 0.5301 |
| N18 | 0.8659 | 0.7675 | 0.7725 | 0.7643 | 0.7724 | 0.7752 | 0.7782 |
| N21 | 2.1753 | 1.8536 | 1.8624 | 1.8541 | 1.8517 | 1.8582 | 1.8550 |
| N24 | 6.0240 | 4.9907 | 4.9998 | 5.0211 | 5.0304 | 4.9801 | 5.0631 |
| N27 | 23.6532 | 20.8579 | 20.7599 | 20.9130 | 20.9035 | 20.8370 | 20.8330 |

Primary arithmetic means in milliseconds; these are separate from the paired median-ratio estimands. Earlier optimizations shared by the new cells explain their comparison with the older anchor. An anchor comparison is not a newly isolated gain from omitting metadata. [pcc:unverified]

| Field | Plain rho / IP | Negation rho / IP | Plain rho / IA | Negation rho / IA |
| --- | --- | --- | --- | --- |
| N15 | 0.60629 | 0.38885 | 0.58281 | 0.38899 |
| N18 | 0.41588 | 0.28687 | 0.42602 | 0.27740 |
| N21 | 0.28619 | 0.22607 | 0.28430 | 0.22409 |
| N24 | 0.17895 | 0.14271 | 0.17648 | 0.13603 |
| N27 | 0.08176 | 0.06221 | 0.08216 | 0.06414 |

Reference entries are paired medians of context-plus-rho compute / IC primary on the exact same Q/G/r/seed. Ratios below 1 favor rho. Original compact-control rho arithmetic is retained. No setup-reused-rho or full-process-cold crossover is established. [pcc:unverified]

| Field | II mean RSS MiB | IP mean RSS MiB | IA mean RSS MiB |
| --- | --- | --- | --- |
| N15 | 6.418 | 6.386 | 6.533 |
| N18 | 6.561 | 6.424 | 6.429 |
| N21 | 6.764 | 6.689 | 6.660 |
| N24 | 7.997 | 7.750 | 7.789 |
| N27 | 12.200 | 12.216 | 12.285 |

RSS is complete-child GNUtime peak RSS, averaged over 42 targets. It includes startup/reporting and does not measure heap allocations or diagnose the collector mechanism. [pcc:unverified]

# Instruction evidence and native admission

| Cell | Whole guest Ir | Collector own Ir | Walker own Ir | Probe own Ir | Lookup own Ir |
| --- | --- | --- | --- | --- | --- |
| SP | 25,844,720 | 869,478 | 1,304,203 | 315,713 | 377,271 |
| SA | 25,841,760 | 869,478 | 1,304,203 | 315,713 | 377,271 |
| IP | 25,021,255 | 869,478 | 1,304,203 | 315,713 | 377,271 |
| IA | 25,018,206 | 869,478 | 1,304,203 | 315,713 | 377,271 |

Separate pre-generation N24 fixture 0 captures use synthetic cost units 1 and pinned Callgrind tools. All four use the same binary. Selected generic-dispatch exclusive Ir is 0. Whole counts include setup/reporting; selected function-exclusive counts exclude callees. Neither is a native collector clock, hardware retirement count or complete physical-cost explanation. [pcc:unverified]

| Field | Complete maps | Staged maps | Staged compact | Indexed pairs | Const pairs |
| --- | --- | --- | --- | --- | --- |
| 15 | 40 | 5 | 5 | 4350 | 2668 |
| 18 | 40 | 5 | 5 | 22780 | 15276 |
| 21 | 40 | 5 | 5 | 81280 | 56100 |
| 24 | 40 | 5 | 5 | 331530 | 232852 |
| 27 | 40 | 5 | 5 | 1412460 | 1001012 |

Native preparation passed strict library/probe Clippy, 29 framework tests and the existing walker/vector/inverse/compact/packed/guard controls plus staged first-witness checks. Positive native AVX2/PCLMUL128 use was admitted. Independent arithmetic checked 20 four-cell pipeline answers, 2,560 walk states and 4 diagnostic answers before fresh identities. [pcc:unverified]

Pair/chunk order, first witnesses, compact 8 byte payload, field arithmetic, direct m2 probe, query schedule and inverse counters are preserved. Counter absence never constructs and then removes the entry; accumulation remains. Native table map controls separately establish staged/indexed selection. [pcc:unverified]

# Every failed A/A control retained

![aa-controls](aa-controls.svg)

| Field | Controls | Failed | Minimum ratio | Maximum ratio |
| --- | --- | --- | --- | --- |
| N15 | 42 | 7 | 0.77566 | 1.69967 |
| N18 | 42 | 5 | 0.85749 | 1.31781 |
| N21 | 42 | 1 | 0.82330 | 1.07641 |
| N24 | 42 | 0 | 0.92649 | 1.04922 |
| N27 | 42 | 0 | 0.91901 | 1.11495 |

| Field | Fixture | Pre / post ratio |
| --- | --- | --- |
| N15 | 727 | 0.81506455 |
| N15 | 728 | 1.17539496 |
| N18 | 728 | 1.31780650 |
| N15 | 731 | 1.26582193 |
| N18 | 733 | 1.16488288 |
| N18 | 734 | 1.19249089 |
| N21 | 737 | 0.82330100 |
| N18 | 745 | 1.19630895 |
| N15 | 747 | 1.23020134 |
| N15 | 749 | 0.77566012 |
| N15 | 754 | 1.21533745 |
| N18 | 760 | 1.22873407 |
| N15 | 767 | 1.69966527 |

A/A is IP ordinary fixture 0 before/after each block, acceptance band 0.85..1.15. All failures remain in all 42 row estimates. No replacement host or filtered panel was used. N24/N27 have no failed A/A rows, but the full panel remains unsigned and invalid for promotion. [pcc:unverified]

# Source identity and raw custody

anchor-input.json: binary 1026bf749fbf8e4a1a266d9833b89a78bf3468956aa9e91eec1af9ffb84d0027; source 25be1116c0cc56f4d7be8a0932de7c6531cdf947; preparation 20261116-152859-d0d3. [pcc:unverified]

prepared-input.json: binary a44e5e80d1ad745d3bf373acc6c497be2c207f9d45ba02b7bd53ddbe48165103; source 2221a26dae90dbcdd703a4a5e3b155c784b908cd; preparation 20261117-043656-db46. [pcc:unverified]

indexed-input.json: binary 847d9407bfbee7b13662f2bc33bb6fa204ec8df93bc0362d5f25a7c92f52d278; source bfd0e5062cbedccbc3b2a28856832dd434533510; preparation 20261117-083200-f519. [pcc:unverified]

optimized-input.json: binary 4bebe2b62aa3192032bfd0ec9c978c31eda9fb39dcc67b97abf12a48ad4cf542; source 5623753791bd66e01056ecb8bd901b5f6caf352e; preparation 20261117-145812-d15b. [pcc:unverified]

Native preparation source 5623753791bd66e01056ecb8bd901b5f6caf352e reconstructs the exact indexed sixteen-source recipe, including its archived Cargo manifest, with three declared Rust overlays. Compiler/root/environment match. Later main integration does not relabel the frozen native binary or source. [pcc:unverified]

Timing source 0c3e791087b39b273f7cc0d5d01d1494a9130c18 and all 35 candidate / 210 workload identities were published before launch. Fresh-generation.json records the contemporaneous ARM identity-probe hash, prior build receipt and generator/controller hashes. The probe hash matched before/after generation; it is an identity generator, not the x86 timing binary. [pcc:unverified]

The completed job snapshot matches all 15 declared controller/input hashes and the published identities. Every native target matched its workload. See fresh-snapshot-binding.json for full snapshot, runner-status, metadata and generation-receipt SHA256 values. [pcc:unverified]

All 130 preparation files and 2,413 timing files were uploaded through scoped default/us-west-2/crypto-autoresearcher in lossless bundles. Fresh downloads checked every member size/hash. Per-file absolute URIs, bundle receipts and readback receipts are retained. No earlier raw arm, failed local check or checkpoint attempt was overwritten. [pcc:unverified]

Ledger bookkeeping limitation: the benchmark record was initialized after native execution. Its original creation time and coordinator capture are retained; native source/hardware/command timestamps come from the original runner receipt. Protocols, controllers, identities and the generation receipt were prospectively published. The ledger entry is not backdated. [pcc:unverified]

# Reproduction, limits and next falsifier

Timing job 20261117-154829-472b uses one Modal L4 / 4 CPU / 8 GiB / 900 s allocation, CPU arithmetic on one exposed CPU. Startup preceded actual execution, which completed in 373 seconds. GPU arithmetic was not measured. Physical placement, memory technology/speed/channels and a qualified isolation tier remain unknown. [pcc:unverified]

Fixtures 726..767 per field; fourteen Williams orders repeated 3, every method position and ordered adjacent pair 6 times. Matched plain/negation rho use separate compact-control processes. Controller 780 s, child 12 s / preflight 30 s, and 8 GiB native virtual cap. No observer subprocess or extra instrumentation ran on the timing worker. [pcc:unverified]

Use a fresh verification checkout for analysis/binding regeneration. Existing replay receipts include invocation timings and are immutable evidence; write new replay outputs when checking the same data. [pcc:unverified]

From this study directory: python3 analyze_fresh.py [pcc:unverified]

From this study directory: python3 replay_fresh_answers.py --stem independent-arithmetic-check [pcc:unverified]

From this study directory: python3 replay_fresh_states.py timing-optimized-001 --out independent-states-check.json [pcc:unverified]

From this study directory: python3 seal_fresh_provenance.py 20261117-154829-472b --identities-revision 0c3e791087b39b273f7cc0d5d01d1494a9130c18 [pcc:unverified]

The record/export plan remains 203 metrics and 25 raw references. Nine effects are reported separately for primary, collector and table setup; within-block interaction is computed before aggregation. The raw analysis retains every method cost, reference, failed control and diagnostic. All intervals are pointwise and exploratory. [pcc:unverified]

Next discriminating experiment: retain indexed arithmetic/table contents and independently vary the old scratch reservations and old gather writes. A repeatable restored collector cost would narrow the preparation-state mechanism; no effect rejects that factor. Any candidate remedy must lower the charged primary against the frozen control on separately fresh targets. [pcc:unverified]

The original extra general-dispatch work was fixed earlier. The later indexed collector regression remains unresolved at the physical-mechanism level. No new primary improvement over frozen indexed, qualified speedup, full-cold result, GPU throughput or broader mathematical breakthrough is established here. The broader performance objective remains open. [pcc:unverified]

