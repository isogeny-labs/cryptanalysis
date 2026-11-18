# Collector buffer-state comparison

Measured outcome: neither reservation nor gather improves the primary interval against the frozen indexed path with a pointwise interval entirely above 1 on any field. Gather reduces N24 collector time by about 3.5%, but increases charged primary time by about 6.7%. The buffer-state remedies therefore do not establish a useful performance improvement; the earlier regression mechanism remains unresolved. [pcc:unverified]

Standing: unsigned exploratory producer evidence, PCC-20261118-63c772. Qualification remains null; this report does not promote a baseline or establish a physical allocator/cache mechanism. All failed A/A rows, caps and incomplete outcomes are retained. [pcc:unverified]

Analysis status: pass; controller status: matrix_completed_unqualified. Observed blocks: 200 of200. Independent replay: 1600IC, 400rho and 400A/A answers; 10240walk states. Failed A/A controls: 9. Capped IC arms: 0. [pcc:unverified]

Post-launch disclosure: I/O also changes explicit-default input-key presence, so it is not an isolated opaque-barrier effect. O/R and R/G input key sets match. The source-control limitation is preserved in SCIENTIFIC_ADDENDUM_001.md; no frozen row, estimator or source was changed. Corrected disclosure claim PCC-20261118-4f626b remains unsigned. [pcc:unverified]

A=frozen anchor ordinary; C=frozen compact inverse; FI=frozen indexed inverse. S=new staged inverse; I=new indexed inverse; O=observed empty buffers; R=observed reserved buffers; G=observed gathered buffers. The five new configurations share one admitted binary and inverse-vector query implementation. The indexed counter is present throughout; O/R/G share the opaque observation. [pcc:unverified]

| Field | Blocks | Failed A/A | FI / R primary | FI / G primary |
| --- | --- | --- | --- | --- |
| N15 | 40 | 1 | 0.97125 [0.95688, 1.01320] | 0.99502 [0.98313, 1.01779] |
| N18 | 40 | 8 | 0.99182 [0.97575, 1.02141] | 0.97654 [0.95937, 0.99886] |
| N21 | 40 | 0 | 1.00080 [0.98625, 1.01900] | 0.96990 [0.95482, 0.98369] |
| N24 | 40 | 0 | 0.99772 [0.98842, 1.00727] | 0.93694 [0.92719, 0.95085] |
| N27 | 40 | 0 | 0.98274 [0.96514, 0.99903] | 0.94295 [0.92096, 0.96675] |

Ratios are reference/candidate time; above1favors the denominator. Collector restoration alone is insufficient: a candidate must lower charged primary against the frozen indexed path on separately fresh points. Pointwise intervals are exploratory, without familywise coverage. No full-process-cold or GPU-throughput result follows. [pcc:unverified]

# Primary: context + pipeline through oracle cleanup

![setup-primary](setup-primary.svg)

| Effect | N15 | N18 | N21 | N24 | N27 |
| --- | --- | --- | --- | --- | --- |
| S / I | 0.99721 [0.98820, 1.01714] | 1.00537 [0.98853, 1.01879] | 0.99743 [0.97621, 1.01302] | 0.99778 [0.97873, 1.00910] | 0.99475 [0.97854, 1.00753] |
| I / O | 0.99655 [0.97983, 1.03058] | 1.00561 [0.99128, 1.01041] | 1.00229 [0.98838, 1.01205] | 0.99541 [0.99055, 1.00679] | 0.99793 [0.99279, 1.00800] |
| O / R | 0.98789 [0.96668, 1.00193] | 0.98306 [0.96224, 1.00334] | 0.99740 [0.98384, 1.02184] | 1.00437 [0.99569, 1.01282] | 0.99718 [0.97238, 1.00550] |
| R / G | 1.02171 [1.01140, 1.04066] | 0.99633 [0.97387, 1.00684] | 0.96577 [0.95820, 0.98146] | 0.94055 [0.93177, 0.94969] | 0.94939 [0.94269, 0.96505] |
| FI / I | 0.99688 [0.97875, 1.01170] | 0.99487 [0.98525, 1.01799] | 0.99584 [0.98375, 1.01233] | 0.99979 [0.98498, 1.01269] | 0.98960 [0.96691, 1.00414] |
| FI / R | 0.97125 [0.95688, 1.01320] | 0.99182 [0.97575, 1.02141] | 1.00080 [0.98625, 1.01900] | 0.99772 [0.98842, 1.00727] | 0.98274 [0.96514, 0.99903] |
| FI / G | 0.99502 [0.98313, 1.01779] | 0.97654 [0.95937, 0.99886] | 0.96990 [0.95482, 0.98369] | 0.93694 [0.92719, 0.95085] | 0.94295 [0.92096, 0.96675] |
| A / I | 1.02300 [0.98855, 1.04100] | 1.09933 [1.07453, 1.11199] | 1.15266 [1.14264, 1.17271] | 1.31233 [1.29849, 1.32433] | 1.13009 [1.10807, 1.14816] |
| C / I | 0.99320 [0.98190, 1.01044] | 1.00235 [0.97998, 1.02288] | 0.99895 [0.97654, 1.01682] | 0.99331 [0.98794, 1.01112] | 1.00936 [0.99140, 1.02357] |

All9predeclared effects. Paired medians and pointwise95% bootstrap intervals,10000resamples, seed20261116, linear quantiles. All40rows per field remain when complete; no filtering, pooling, replacement host or cross-panel products. Incomplete estimates are unavailable. [pcc:unverified]

# Collector through owned cleanup

![setup-collector](setup-collector.svg)

| Effect | N15 | N18 | N21 | N24 | N27 |
| --- | --- | --- | --- | --- | --- |
| S / I | 0.99079 [0.96969, 1.03652] | 1.02014 [0.99878, 1.05180] | 0.99892 [0.98172, 1.01963] | 0.96171 [0.94929, 0.97571] | 0.98279 [0.97754, 1.00024] |
| I / O | 0.99120 [0.97313, 1.03706] | 0.96962 [0.93893, 1.01096] | 1.01166 [0.99236, 1.02096] | 0.99199 [0.98289, 1.01405] | 1.00466 [0.99029, 1.01016] |
| O / R | 1.00033 [0.98229, 1.02119] | 0.99382 [0.97678, 1.01684] | 0.99723 [0.97913, 1.00736] | 1.00838 [0.99511, 1.02853] | 1.00162 [0.99091, 1.00785] |
| R / G | 1.00598 [0.98548, 1.04836] | 1.01564 [0.99401, 1.04150] | 1.00608 [0.99571, 1.01583] | 1.01878 [1.01040, 1.03712] | 1.00791 [1.00094, 1.01843] |
| FI / I | 1.00766 [0.97054, 1.02414] | 1.00928 [0.97759, 1.04079] | 0.98962 [0.98013, 1.00613] | 1.00267 [0.99208, 1.01423] | 0.99449 [0.98215, 1.00712] |
| FI / R | 0.96441 [0.93260, 1.02788] | 1.00125 [0.97370, 1.01286] | 1.00864 [0.99131, 1.02561] | 1.01828 [1.00249, 1.02556] | 0.99460 [0.97859, 1.00335] |
| FI / G | 0.99323 [0.96553, 1.02757] | 1.00658 [0.98837, 1.04980] | 1.01070 [0.99411, 1.02597] | 1.03675 [1.02555, 1.05037] | 1.00330 [0.99091, 1.01393] |
| A / I | 1.01688 [0.99383, 1.03801] | 1.06902 [1.02858, 1.08746] | 1.12916 [1.10160, 1.14942] | 1.07320 [1.06180, 1.08132] | 1.14379 [1.12953, 1.15256] |
| C / I | 1.01578 [0.98605, 1.03119] | 0.99557 [0.97167, 1.02342] | 0.99764 [0.98341, 1.00835] | 0.96363 [0.94796, 0.97121] | 0.98388 [0.97523, 0.99640] |

All9predeclared effects. Paired medians and pointwise95% bootstrap intervals,10000resamples, seed20261116, linear quantiles. All40rows per field remain when complete; no filtering, pooling, replacement host or cross-panel products. Incomplete estimates are unavailable. [pcc:unverified]

# Pair-table setup, included in primary

![setup-table](setup-table.svg)

| Effect | N15 | N18 | N21 | N24 | N27 |
| --- | --- | --- | --- | --- | --- |
| S / I | 1.16556 [1.14002, 1.29783] | 0.94820 [0.93542, 1.00808] | 0.98955 [0.97686, 0.99909] | 1.01614 [1.00349, 1.02378] | 1.00099 [0.98507, 1.02162] |
| I / O | 1.01415 [0.99660, 1.02465] | 1.02428 [0.99061, 1.04444] | 0.99901 [0.98258, 1.02038] | 1.00606 [0.99876, 1.02142] | 0.99914 [0.99151, 1.01388] |
| O / R | 0.85083 [0.82538, 0.87531] | 0.98224 [0.94330, 1.00568] | 0.99585 [0.98349, 1.01372] | 0.99114 [0.98301, 0.99866] | 0.98855 [0.97290, 1.01216] |
| R / G | 0.94175 [0.87136, 0.95861] | 0.93652 [0.91414, 0.96781] | 0.91409 [0.89483, 0.92420] | 0.89153 [0.87955, 0.90150] | 0.90298 [0.88843, 0.91810] |
| FI / I | 0.99633 [0.98145, 1.00522] | 0.97997 [0.95105, 1.02458] | 0.99541 [0.98467, 1.00255] | 0.99062 [0.98158, 1.00020] | 0.98100 [0.96132, 0.99746] |
| FI / R | 0.87361 [0.84983, 0.88815] | 0.96490 [0.93425, 1.00462] | 0.99673 [0.97661, 1.00741] | 0.99045 [0.96704, 0.99853] | 0.97812 [0.95356, 0.99170] |
| FI / G | 0.82061 [0.79302, 0.83728] | 0.90262 [0.87564, 0.94355] | 0.90062 [0.87966, 0.92320] | 0.87697 [0.87206, 0.88221] | 0.88054 [0.86257, 0.90563] |
| A / I | 1.23819 [1.21820, 1.26878] | 1.15144 [1.12884, 1.18832] | 1.26175 [1.22815, 1.30170] | 1.41249 [1.39468, 1.43961] | 1.12774 [1.11131, 1.14217] |
| C / I | 1.16171 [1.12697, 1.19434] | 0.97148 [0.94871, 1.01130] | 0.99782 [0.98667, 1.00860] | 1.01534 [1.00386, 1.03395] | 1.02083 [1.00515, 1.03574] |

All9predeclared effects. Paired medians and pointwise95% bootstrap intervals,10000resamples, seed20261116, linear quantiles. All40rows per field remain when complete; no filtering, pooling, replacement host or cross-panel products. Incomplete estimates are unavailable. [pcc:unverified]

# Transfer checks and causal limits

| Field | FI / I collector | Inside1%band | I / O collector | Inside1%band |
| --- | --- | --- | --- | --- |
| N15 | 1.00766 [0.97054, 1.02414] | False | 0.99120 [0.97313, 1.03706] | False |
| N18 | 1.00928 [0.97759, 1.04079] | False | 0.96962 [0.93893, 1.01096] | False |
| N21 | 0.98962 [0.98013, 1.00613] | False | 1.01166 [0.99236, 1.02096] | False |
| N24 | 1.00267 [0.99208, 1.01423] | False | 0.99199 [0.98289, 1.01405] | False |
| N27 | 0.99449 [0.98215, 1.00712] | False | 1.00466 [0.99029, 1.01016] | False |

The protocol requires both collector95% intervals entirely inside0.99..1.01 before attributing a reservation/gather contrast to the earlier regression. An interval containing1does not establish equivalence. If either transfer check fails, retain the new-binary contrasts but historical attribution remains inconclusive. [pcc:unverified]

Additional source limitation, disclosed after launch: I explicitly includes suppress_indexed_counter=0 in oracle_params, whereas O/R/G omit the key and use the same default. This configuration is constructed before primary and may alter allocation history. Therefore I/O is a joint configuration-presence/opaque-observation contrast, not a pure barrier effect. O/R and R/G retain matching parameter key sets. Do not infer a unique physical cause from transfer bands. See SCIENTIFIC_ADDENDUM_001.md. [pcc:unverified]

Reservation is O/R; gather traffic is R/G. These are conditional effects, not a factorial interaction. Even successful transfer only supports the declared setup-state contrast in this build; cache placement, allocator behavior, branch history and physical placement require separate evidence. [pcc:unverified]

# Primary means and same-point rho

| Field | A ms | C ms | FI ms | S ms | I ms | O ms | R ms | G ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N15 | 0.5338 | 0.5252 | 0.5231 | 0.5245 | 0.5257 | 0.5299 | 0.5381 | 0.5227 |
| N18 | 0.8629 | 0.7794 | 0.7870 | 0.7856 | 0.7785 | 0.7806 | 0.7916 | 0.7998 |
| N21 | 2.1351 | 1.8612 | 1.8757 | 1.8502 | 1.8656 | 1.8475 | 1.8680 | 1.9098 |
| N24 | 6.2908 | 4.9046 | 4.8799 | 4.9176 | 4.8977 | 4.9074 | 4.8680 | 5.1886 |
| N27 | 23.7933 | 21.2980 | 20.8239 | 20.9434 | 21.0170 | 21.0822 | 21.3458 | 22.1638 |

Arithmetic means in milliseconds are distinct from the paired median-ratio effects. Primary includes context plus factor-base/table/collector/matrix/scalar verification through owned oracle cleanup. Prior fixture/calibration/spec/empty allocation, startup/JSON and later context/report destruction remain excluded. [pcc:unverified]

| Field | Negation rho / I | Negation rho / R | Negation rho / G |
| --- | --- | --- | --- |
| N15 | 0.40968 | 0.39730 | 0.40223 |
| N18 | 0.31906 | 0.30951 | 0.30855 |
| N21 | 0.23164 | 0.23038 | 0.22308 |
| N24 | 0.12288 | 0.12193 | 0.11506 |
| N27 | 0.06003 | 0.05898 | 0.05814 |

These are paired context-plus-rho / primary ratios on identical Q/G/r/seed. Below1favors rho. Plain and negation references remain separately available in the raw analysis. A comparison with A includes older cumulative optimizations and does not isolate a gain from reservation or gather changes. RSS is complete-child GNUTime peak, not an allocation or causal measurement. [pcc:unverified]

| Field | FI mean RSS MiB | I mean RSS MiB | R mean RSS MiB | G mean RSS MiB |
| --- | --- | --- | --- | --- |
| N15 | 5.369 | 5.398 | 5.385 | 5.384 |
| N18 | 5.471 | 5.479 | 5.480 | 5.481 |
| N21 | 5.748 | 5.761 | 5.763 | 5.758 |
| N24 | 6.782 | 6.795 | 6.792 | 6.788 |
| N27 | 11.299 | 11.319 | 11.316 | 11.323 |

RSS means include all attempted rows only when each child measurement is present; unavailable is not zero. These values include child startup/reporting and do not identify the collector mechanism. [pcc:unverified]

# Every failed A/A control retained

![setup-aa](setup-aa.svg)

| Field | Attempted | Failed |
| --- | --- | --- |
| N15 | 40 | 1 |
| N18 | 40 | 8 |
| N21 | 40 | 0 |
| N24 | 40 | 0 |
| N27 | 40 | 0 |

| Field index | Fixture | Pre / post ratio |
| --- | --- | --- |
| 1 | 769 | 0.83230708 |
| 1 | 770 | 0.78969214 |
| 1 | 772 | 1.22999805 |
| 0 | 777 | 1.17631028 |
| 1 | 785 | 0.78811900 |
| 1 | 786 | 1.15401381 |
| 1 | 796 | 1.18449274 |
| 1 | 803 | 1.19034211 |
| 1 | 804 | 0.82442323 |

A/A uses ordinary indexed fixture0 in the new binary before/after each block, acceptance band0.85..1.15. Every failed row remains in all estimates; a field with zero failures does not qualify the full panel or establish a physical cause. [pcc:unverified]

# Identity, source and raw custody

Timing job 20261118-011019-dc56; clean controller/input source 8c79b510a2b8bccc8663c785e56e43a42c9b08a5. All40candidate IDs and200workload IDs were published before timing; the contemporary separately rebuilt ARM probe generated identities only. Native binary/source hashes remain in setup-frozen-inputs.json and the original preparation receipts. [pcc:unverified]

| Binding | Value |
| --- | --- |
| snapshot_sha256 | 52e7da535ff41b4a81ca658cd427be29d54a1dfc9272c23bff192c454b86641b |
| runner_status_sha256 | 6c61366da752a878dd77c4e7822cfbc14a47d6f9d443b1684aa67365ca849fe5 |
| metadata_sha256 | bee7dcf26e3e927ed511fcce859f5920dbee4b6de7afcc5915496e3a5c0c416d |
| published_identities_revision | 2a16aeb8e3b4a7bcc3aac61ffedefdef4461c193 |
| generation_receipt_sha256 | 74a742e8278659959cb53574dab2cfbc146d91bdd0f35c2cd752de28f1da035d |

The existing benchmark record was initialized2026-11-17T18:09:05UTC before this run. Native source/hardware/timestamps come from the original runner receipt; the original coordinator capture and record creation time remain retained. No backdating or replacement record is used. [pcc:unverified]

Working-store raw bundle readback: [{'name': 'timing-setup-001', 'bytes': 9363528, 'files': 2503, 'sha256': '959bb55e57418bb090a15c6460be06c674e6f69722ec2e5c7f53b814d2b7b555'}]. Exact per-member byte/hash checks and per-file S3 addresses are retained. Current CI artifact-pull403 failures are separately diagnosed; local custody does not establish CI credential access or a signed verdict. [pcc:unverified]

# Protocol and remaining work

One approved L4/4CPU/8GiB/900second allocation; actual runner seconds=384.833, exit=0. CPU arithmetic only, pinned to one exposed allowed CPU. No observer subprocess or profiling ran on the timing worker. Physical placement, memory technology/speed/channels and qualified isolation remain unknown. [pcc:unverified]

Fixtures768..807 per field; eight Williams rows repeated5times, each method position and directed adjacency5times. Rotated field order gives8appearances per field position. Matched plain/negation rho uses fresh compact-control processes and the exact same public targets/seeds. Controller780seconds, child12seconds, preflight30seconds,8GiB native virtual-memory cap. [pcc:unverified]

The record inventory is180metrics and25raw references for a complete panel. Keep all failures and caps, native source/binary bindings, replay outputs and initial infrastructure failures. No signed speedup, baseline promotion, full-cold result or mathematical novelty follows automatically from these producer checks. [pcc:unverified]

Next action is determined from the separately reported primary effects and transfer checks. A retained gain requires independent review and the existing evidence gates; an inconclusive or negative configuration remains a measured outcome rather than a successful remedy. The broader performance objective remains open. [pcc:unverified]
