# Selective XOR matrix activation on the N131 terminal circuit

Raising only CryptoMiniSat's small-matrix limits activated **five 3,315×9,132 XOR matrices** on the frozen N131 terminal-32 public-point formula while leaving the 24,554- and 32,851-row components excluded. The solver then automatically disabled Gaussian elimination after measuring **13.4% usefulness over 6,526 calls**. In a matched 120-second one-worker diagnostic, the default and selective settings ended BOUNDED_UNKNOWN after **38** and **33** restart rows, respectively; sampled peak solver RSS was **171 MB** and **242 MB**. The selective setting is not promoted.

The exact ordinary XCNF is the archived [terminal-32 circuit](../n131_w18_terminal_fiber_20261011/RESULT.md) on curve EC1N131Ckb1heb5f1998f20b, the frozen public point, and raw preimage zero. The [byte-replay receipt](../n131_w18_terminal_fiber_20261011/archive_receipt.json) fixes its raw SHA-256 as 4eeaae703849f9877d2c5b4deb2fce015d8e78241651ef952bda3bef187f18a2. Both cases used the same CryptoMiniSat 5.14.7 binary, native-XOR input, one thread, a 90-second solver setting, a 120-second parent cap, a 4-GiB RSS cap, and the frozen order default then selective. The selective flags raised the maximum matrix rows to 4,000 and columns to 10,000.

| Frozen ordinary query | Default | Selective small matrices |
| --- | ---: | ---: |
| XOR matrices activated | 0 | **5** |
| Restart rows by parent wall cap | 38 | 33 |
| Max sampled RSS | 170,950,656 B | 241,434,624 B |
| Child high-water RSS | 170,950,656 B | 241,614,848 B |
| Terminal status | BOUNDED_UNKNOWN | BOUNDED_UNKNOWN |

The [versioned protocol](protocol_v2.json), [default transcript](default.stdout.txt), [selective transcript](selective.stdout.txt), [run receipt](result.json), and [terminal verifier](verification.json) bind the input, flags, matrix messages, restart counts, process stops, and memory. The first runner stopped before solver launch because this macOS Python build rejected its address-space resource limit; the [failure receipt](failure_v1.json) records PRODUCER_FAILURE. The versioned runner used a 3.75-GiB live RSS guard and retained the 4-GiB result cap. Both solver runs reached the parent wall cap with empty stderr and no SAT/UNSAT line.

The host had heavy CPU contention, so restart counts and wall behavior are exploratory. The structural result is exact: the selected small XOR matrices can be enabled within the memory envelope, but CryptoMiniSat judged them unhelpful and turned the feature off. The next N131 effort should focus on an earlier target-conditioned family constraint or a substantially different XOR propagation scheme, with a matched unpinned N41 relation gate before another full-width public-point run.
