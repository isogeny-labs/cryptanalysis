"""Build a self-contained PMULL variant of the frozen exact join source."""
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVED = HERE.parent / "n41_w8_ninepair_join_control_20261012/join9.cpp"
BASELINE = HERE / "join3.cpp"
EXPECTED = {
    ARCHIVED: "b0a74e93f5daf4f66c22e866c6594b7e6e3e4df024cba2989e4df7e1ac5129db",
    BASELINE: "bfbacc6c806891fd51c6bade01243d9c09a8a5b872f2b52316d8ce0972ea4bd5",
}
for path, digest in EXPECTED.items():
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f"source changed: {path}")
helper = ARCHIVED.read_text().split("int main(int argc, char** argv) {", 1)[0]
body = BASELINE.read_text().split("#undef main\n", 1)[1]
assert helper.count("uint64_t mul(uint64_t a, uint64_t b) {") == 1
helper = helper.replace("uint64_t mul(uint64_t a, uint64_t b) {",
                        "uint64_t slow_mul(uint64_t a, uint64_t b) {", 1)
fast = r'''
// Carryless 41-by-41 product, reduced by x^41 + x^3 + 1 in two folds.
uint64_t mul(uint64_t a, uint64_t b) {
#if defined(__ARM_FEATURE_CRYPTO)
    poly128_t product = vmull_p64((poly64_t)a, (poly64_t)b);
    uint64x2_t lanes = vreinterpretq_u64_p128(product);
    uint64_t lo = vgetq_lane_u64(lanes, 0);
    uint64_t hi = vgetq_lane_u64(lanes, 1);
    constexpr uint64_t mask = (1ULL << 41) - 1;
    uint64_t high = (lo >> 41) ^ (hi << 23);
    uint64_t folded = (lo & mask) ^ high ^ (high << 3);
    uint64_t high2 = folded >> 41;
    return (folded & mask) ^ high2 ^ (high2 << 3);
#else
    return slow_mul(a, b);
#endif
}

'''
helper = helper.replace("uint64_t sqr(uint64_t a)", fast + "uint64_t sqr(uint64_t a)", 1)
selftest = r'''
        uint64_t test_state = 0x175ba1fa9dULL;
        for (unsigned trial = 0; trial < 100000; ++trial) {
            test_state ^= test_state << 7;
            test_state ^= test_state >> 9;
            uint64_t a = test_state & ((1ULL << 41) - 1);
            test_state ^= test_state << 7;
            test_state ^= test_state >> 9;
            uint64_t b = test_state & ((1ULL << 41) - 1);
            if (mul(a, b) != slow_mul(a, b))
                throw std::runtime_error("PMULL differential mismatch");
        }
        std::cout << "FIELD_SELFTEST_PASS 100000\n" << std::flush;
'''
assert body.count("    try {\n") == 1
body = body.replace("    try {\n", "    try {\n" + selftest, 1)
output = "#include <arm_neon.h>\n" + helper + body
target = HERE / "join3_fast.cpp"
if target.exists() and target.read_text() != output:
    raise RuntimeError("generated output differs from existing file")
target.write_text(output)
print(hashlib.sha256(output.encode()).hexdigest())
