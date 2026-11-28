# Native M31 PairIndex bitmap comparison

The frozen first panel used all five public M31 targets and three manifest-derived walk seeds with four arms: current 128 KiB multiplicative bitmap (`current20`), direct 512 KiB high-bit bitmap (`high22`), high-plus-low 1 MiB bitmap (`dual22`), and matched archived rho. All 60 fresh-process arms solved. The three IC arms had the same public answer, exact certificate, pair/work counters and relation counts within every target-seed block. `audit.py` independently replayed every saved certificate equation and coefficient elimination: 9,153 IC relations across 45 IC arms. All reported scalars were independently checked by public generator multiplication. No arm failed or was censored. Raw CSV SHA-256: `0aaf1ff1f2ee7d2610e16bcf35b74c782724bb71bbc6796164bbb8c46760380c`.

| First panel, 15 blocks | Median wall ms | Median CPU ms | Median pair index ms | Median online ms |
| --- | ---: | ---: | ---: | ---: |
| Current 20-bit | 44.321 | 35.536 | 3.191 | 27.168 |
| Direct high 22-bit | 38.914 | 32.212 | 3.180 | 25.435 |
| Dual high/low 22-bit | 44.773 | 34.095 | 3.531 | 27.097 |
| Matched rho | 18.271 | 14.400 | — | — |

Current/high paired wall and CPU ratios were 1.1001 and 1.1037 (13/15 and 14/15 high wins). High/dual ratios were 0.9683 and 0.9734 (only 4/15 and 5/15 dual wins). Dual/current ratios were 1.0357 and 1.0502 (10/15 and 12/15 dual wins). The dual filter missed the frozen gate against **both** controls; it is a negative native result even though it helped the separate standalone flat-index collector. The pair table here uses a HashMap, so the extra low-bit read and build work do not pay for themselves on this workload. That causal explanation is an inference from the phase timings, not a separately isolated microarchitectural measurement.

The first panel's high-only result triggered the separately frozen `HIGH_CONFIRM_PROTOCOL.md`. The confirmation used three fresh manifest-derived walk seeds from `SEEDS_CONFIRM.json`, the same five public Q and three arms (`current20`, `high22`, matched rho). All 45 fresh-process arms solved. The two IC arms had identical exact certificates and workload counters in all 15 blocks. `audit_confirm.py` independently replayed 6,282 IC certificate relations and verified all public answers. No arm failed or was censored. Raw CSV SHA-256: `9742be13fe7aa12c7136296e9efb1e830fb77536b5d365edda181392da4062b7`.

| Confirmation, 15 blocks | Median wall ms | Median CPU ms | Median pair index ms | Median online ms |
| --- | ---: | ---: | ---: | ---: |
| Current 20-bit | 41.587 | 35.393 | 3.376 | 27.484 |
| Direct high 22-bit | 40.195 | 32.898 | 3.674 | 25.780 |
| Matched rho | 20.753 | 16.084 | — | — |

The confirmation's paired current/high ratios were 1.0415 wall and 1.0409 CPU, with 10/15 and 12/15 high wins. Its prespecified 1.05 and 12/15 gate failed on wall and ratio. High-only remains a possible small local optimization but is not selected as the library default. In the first panel high/rho paired ratios were 2.3765 wall and 2.4447 CPU; these are directly matched same-target comparisons within that panel, and the implementations use different languages and arithmetic. The native IC path still has a material rho gap under this measurement.

The wrapper's wall and parent-plus-child CPU clocks include the fresh Rust process, basis generation, pair-table setup, relation collection, elimination, certificate verification, output parsing and independent public answer verification. The internal `cold_to_report_ns`, `pair_index_ns` and `online_ns` columns offer phase attribution. Compilation and frozen public JSON loading preceded timing; OS caches were not flushed. `HOST.json` records the exposed machine. This is exploratory local producer evidence [pcc:unverified], without Tier 1 isolation or an independent signed performance review. Seeds are walk replicates across five fixed public points, not new curves or factor-base constructions.

The algorithmic bitmap safety obligation is first successful payload preservation when both projections mark every inserted x; `m31-dual-x-bitmap/DualBitmap.lean` proves that conditional implication. The native unit test enumerates every retained M31 pair class for a small basis and checks that both signs survive bitmap filtering. The Lean proof does not verify Rust code or runtime. No theorem about timestamp arithmetic supports the performance conclusion.

Source commit for the measured Rust variants: `e6d9a6b898de9750a5d08a5444f55864aa12d20b`; `pair_index.rs` SHA-256 `f018a6f46000c1af2f412b8ddf16c99e087372f3445a93a0f3072c6533bae13f`. `replay.py` SHA-256 `1059f2f229ed240e7b231ae309c20e885ac26a3fb167c24acd55ad72eff1f027`. The first-panel CSV stores each binary SHA-256 and every report SHA-256; confirmation used the same three binary hashes. The exact public target file SHA-256 and both seed-manifest hashes are in the frozen protocols.
