# Bitmap collector A/A local noise control

The A/A protocol was frozen in `BLOOM_AA_PROTOCOL.md` before measurement. Two binaries with identical source and compile-time settings were built in separate directories. Both used the 6 MiB sign-packed index, one-multiply hash, validated shared-x paired arithmetic and 128 KiB x bitmap. Complete sorted index maps were byte-identical on both frozen public M31 bases (auxiliary SHA-256 `ce7dab41355b3b236be455dbeaf9c46aaac83d29b272de5db727f54676407879`, plain `8b55e48edff4cbc66ac73ba30bc601ade0e7ae03fbf5439aaaaf2d807ec0d6fa`). Every matched pair agreed on basis digest, verified scalar, trials, relations and entries.

| Basis | Median paired A/B wall ratio | B wall wins | Wall ratio range | Median paired A/B CPU ratio | B CPU wins | CPU ratio range |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Auxiliary | 1.0186 | 12/24 | 0.289–2.727 | 1.0149 | 12/24 | 0.718–1.456 |
| Plain | 0.9720 | 11/24 | 0.341–3.062 | 1.0510 | 13/24 | 0.748–1.195 |

The median A/A ratios are close to one with balanced wins, but individual wall observations are noisy on this shared host. This supports interpreting the direct original/candidate result through paired medians and CPU as well as wall time. It does not substitute for isolated or independent performance replay. All charged phases and raw observations follow the direct comparison's timing boundary. `bloom-aa-raw.csv` SHA-256 is `3df76bed17290dbeb2ac9f58c7205614ca503cbeb29fd8f7a620a4d7bcb60323`. [pcc:unverified]
