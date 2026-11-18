# ARM target-feature call-boundary audit

The reduced-scope optimized Apple ARM audit rejects an extra per-multiply call explanation on the recorded rustc1.93.1/LLVM21.1.8 toolchain. Adding an aes-enabled wrapper around the identical extracted Gf2 batch-inversion body does not remove any direct helper call: the baseline already inlines PMULL. This is unsigned claim PCC-20261117-1afaee. [pcc:unverified]

| Optimized wrapper | Static PMULL instructions | Direct clmul_u64_neon call sites |
|---|---:|---:|
| Baseline body |16|0|
| aes-enabled body |16|0|

These are static counts in the wrapper bodies, not dynamic multiplication counts, hardware retirement or wall time. The compiler's default target configuration already includes aes. The initial unoptimized identity binary was unsuitable for performance inference; its calls were not used to claim a production bottleneck. Both optimized paths passed11980element checks over5registered fields, including zeros and batch boundaries, against independent schoolbook field products. [pcc:unverified]

Compilation uses the exact extracted Gf2Tables/Gf2 arithmetic, removes only unused general-element conversion adapters, and supplies the two-field polynomial input representation. It is not a full-crate validation or a test of Graviton/generic Linux ARM compilation. Runtime aes detection precedes the enabled-wrapper call. Compiler/source/generated-source/assembly/binary hashes, command bounds and all output are retained in arm-codegen-001. [pcc:unverified]

Production arithmetic and every prepublished timing controller remain unchanged. Do not add an ARM wrapper merely from the debug call trace. The primary next experiment remains the already prepared x86 buffer-state timing panel, awaiting its separate allocation approval. The broader performance objective is incomplete. [pcc:unverified]
