# EC2 Tier 1 rho arithmetic panels, 2026-10-19

The separate `c7i.4xlarge` instance in `us-east-2c` ran the fresh-Q
one-restart and reuse panels. The [allocation](allocation.json) records the
instance, CPU and NUMA envelope, source and binary digests. The service used
CPU 0 and each timed child used CPU 4 on NUMA node 0. This is Tier 1
cloud-instance evidence; the runner recorded cgroup, steal-time, affinity,
interrupt and memory counters for each arm. Both panels ran through the same
serialized queue. The tarballs preserve every arm, pair, manifest, rule,
preflight and summary receipt; the JSON files are independent audits.

| Panel | Complete pairs | Exact-output and host receipts | A/A gate | Decision |
| --- | ---: | --- | --- | --- |
| [One restart](one-raw.tar.gz), [audit](one-audit.json) | 1,584/1,584 | No invalid arms or structural issues | Failed: OpenSSL control `cal_before`, repeat 7, ratio 1.2118446 exceeded frozen [0.90, 1.11] | Aggregate comparison remains `unknown_after_tier_gate` |
| [Reuse](reuse-raw.tar.gz), [audit](reuse-audit.json) | 3,168/3,168 | No invalid arms or structural issues | Passed at each count | Qualified count-specific comparisons below |

The reuse panel charged target-dependent preparation, all evaluations and
affine output. Median complete online milliseconds and the paired radix-81
to mixed-76 ratio were:

| Restarts per Q | Mixed-76 ms | Radix-81 ms | OpenSSL ms | Radix-81 / mixed-76 paired ratio, Q-cluster 95% interval |
| ---: | ---: | ---: | ---: | --- |
| 1 | 0.119478 | 0.128090 | 0.291246 | 1.0669 [1.0494, 1.0897] |
| 8 | 0.723362 | 0.714030 | 2.255666 | 0.9916 [0.9787, 0.9959] |
| 32 | 2.559708 | 2.680047 | 8.987540 | 1.0475 [1.0439, 1.0492] |
| 128 | 9.799256 | 9.972769 | 35.838602 | 1.0180 [1.0169, 1.0190] |

The observed rank changes at eight restarts, so these counts do not support
a single monotone crossover. The one-restart panel's descriptive mixed-76
advantage remains unselected because its A/A gate failed. The full worker
experiment uses a separate fresh-Q Tier 1 panel and determines the worker
decision independently.

Raw archive SHA-256: one restart
`b3750c69d2970f1412e61d07c2c4bc53f6a6e41cc2f85af13a569188f017707d`;
reuse
`97d2fed9e76ff877e4c3bce0e8f2fcdc04603b891eed144c25f7ed1aabab1957`.
