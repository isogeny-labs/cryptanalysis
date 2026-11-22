# Checked M31 roots on the frozen 32-coordinate fiber

This latency panel takes the cubic values of the 32 coordinates in the frozen Projection.lean fixture. It measures the earlier arithmetic kernels at this exact width. Input preparation is outside both clocks. For a standalone checkout, the fixture is experiments/prime-field-auxiliary-ic/m31-boolean-lifts/Projection.lean from companion PR 1889 at commit 5c561e1c011370d0157b81528144366a3af85a8d.

Run python3 run.py on native ARM with Apple clang. The harness checks the SHA-256 of the kernel source, specializes its constant width to 32 and compiles a fresh binary. Each of 36 blocks launches three processes, one per implementation. All six launch orders occur six times. Each process measures its first invocation and then measures 8192 more invocations after checking the first result against a modular-exponentiation oracle. All outputs are checked after the repeated interval as well.

| Median nanoseconds per 32 elements | Scalar | Widening NEON | High multiply NEON |
|---|---:|---:|---:|
| First invocation | 1125 | 750 | 520.5 |
| Repeated invocation | 1486.8 | 906.4 | 439.1 |

On the local shared M4 Pro the paired median widening/high time ratio was 1.522 on first invocation and 1.817 on repeated calls. High multiply won 31/36 and 33/36 blocks respectively. The first-invocation timer includes the kernel call and timer overhead inside an already launched process. It excludes process startup. A shared machine and submicrosecond timings limit interpretation of individual rows. The repeated interval includes a compiler memory barrier per invocation. These are square-root kernel measurements with precomputed cubic values.
