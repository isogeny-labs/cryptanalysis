import csv
import hashlib
import itertools
import re
import subprocess
from pathlib import Path

directory = Path(__file__).resolve().parent
source = (directory.parent / "m31-native-root/bench.cpp").read_bytes()
assert hashlib.sha256(source).hexdigest() == "8ed0d5761b1c7f06457df37943fd985b6bb1f82cf4116e3f07b58da2d4dd445e"
prefix = source.decode().split("int main() {")[0].replace("count = 4096", "count = 32")
fixture = (directory.parent / "m31-boolean-lifts/Projection.lean").read_text()
coords = [int(x) for row in re.findall(r"List Nat := \[([0-9,]+)\]", fixture)
          for x in row.split(",")]
assert len(set(coords)) == len(coords) == 32
p = 2**31 - 1
inputs = ",".join(str((x**3 + 2*x + 14) % p) for x in coords)
driver = r"""
int main(int argc, char** argv) {
    if (argc != 2) return 1;
    unsigned arm = std::atoi(argv[1]);
    constexpr std::array methods = {roots<0>, roots<1>, roots<2>};
    const std::array<Word, count> input = {INPUTS};
    std::array<Word, count> output{};
    auto method = methods.at(arm);
    using Clock = std::chrono::steady_clock;
    auto measure = [&](int reps) {
        auto start = Clock::now();
        for (int i = 0; i < reps; ++i) {
            method(input.data(), output.data());
            asm volatile("" : : "r"(output.data()) : "memory");
        }
        return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count();
    };
    auto first = measure(1);
    std::array<Word, count> expected{};
    std::transform(input.begin(), input.end(), expected.begin(), oracle);
    if (output != expected) return 1;
    auto warm = measure(8192);
    if (output != expected) return 1;
    std::printf("%lld,%lld\n", static_cast<long long>(first), static_cast<long long>(warm));
}
"""
binary = directory / "bench"
subprocess.run(["clang++", "-O3", "-std=c++17", "-mcpu=native", "-Wall", "-Wextra",
                "-Werror", "-x", "c++", "-", "-o", str(binary)],
               input=prefix + driver.replace("INPUTS", inputs), text=True, check=True)
with (directory / "rows.csv").open("w") as file:
    writer = csv.writer(file)
    writer.writerow(["block", "position", "arm", "first_ns", "warm_8192_ns"])
    orders = list(itertools.permutations(range(3)))
    for block in range(36):
        for pos, arm in enumerate(orders[block % 6]):
            output = subprocess.check_output([binary, str(arm)], text=True)
            first, warm = map(int, output.strip().split(","))
            writer.writerow([block, pos, arm, first, warm])
