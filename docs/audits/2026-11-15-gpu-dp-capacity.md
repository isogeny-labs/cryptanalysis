# Saturated GPU distinguished-point capacity

The driver accepts a walk count bounded by32-bit IDs and a32-bit explicit
launch length. With `nwalks=UINT32_MAX-7`, `steps=UINT32_MAX` and `dp_bits=0`,
the previous `uint64_t(exp_dps*2)+4096` converted approximately3.68935e19
before applying its2^20 cap. A standalone capture of that exact production
formula at source `c021359ce7b5f4f5b867ffc50b4873769bde6f9a` fails under
Clang `-fsanitize=undefined,float-cast-overflow -fno-sanitize-recover=all`.
This reproduces pre-allocation arithmetic undefined behavior without attempting
the enormous walk-buffer allocation or running a GPU kernel.

The internal helper now computes the exact saturated integer expression
`min(2^20, floor(2*walks*steps/2^dp_bits)+4096)`. The product fits uint64_t
under the existing validated dimensions. For zero DP bits, saturation happens
before doubling; otherwise a right shift computes the quotient without an
overflowing double-width product. Public parameters and checkpoint layout are
unchanged. No frozen benchmark or research source identity is rewritten.

The GPU test compares2,304 boundary combinations over all64 DP-bit values
against an independent128-bit expression and adds explicit saturation-boundary
checks. Existing GPU emulator arithmetic, group-law and solve controls pass
under ASan/UBSan. This is a correctness fix and removal of floating-point
capacity arithmetic; no timing claim is made.

Hardware discovery is read-only. Local Apple M4 Pro has no CUDA toolchain or
NVIDIA device. Two configured RunPod SSH endpoints refuse connections and the
AWS SSH route times out; no running EC2 instance appears in us-west-2 or
us-east-2 for the current credentials. An additional provider API inventory
shows an A100 pod with desired status RUNNING, but both exposed HTTP ports
return the provider waiting-for-service page, with no usable SSH/CUDA session.
Desired status is not hardware execution evidence. No pod was created, stopped,
restarted or reconfigured, and no existing workload was preempted. Optional
PTX hardware validation remains unavailable.

The first complete ASan/UBSan run passed18other C tests and failed two new
explicit expected values: the saturation threshold had been transcribed as
521216instead of522240. The implementation matched all2,304independent
128-bit cases. The corrected expectations and targeted GPU rerun are recorded
separately; the first failed run remains retained. No production arithmetic
was changed to accommodate those incorrect expected values.

The corrected targeted GPU CTest completed successfully under ASan/UBSan,
covering80,074checks. Together with the18unchanged checks in the complete run,
all19Ctest names have passed; the complete first invocation itself remains
recorded as18/19, not retrospectively relabeled green.
