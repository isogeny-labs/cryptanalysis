// ARM64 M31 square membership for canonical inputs. Replay on ARM64 with
// clang++ -std=c++17 -O3 -mcpu=native bench.cpp -o bench && ./bench 4315
// Rows give input count, block, method, and elapsed nanoseconds. Methods 0, 1,
// and 2 are direct squaring, lookup, and lookup with fresh table construction.
#include <algorithm>
#include <arm_neon.h>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <random>
#include <vector>

using Word = uint32_t;
using Vec = uint32x4_t;
constexpr Word prime = 2147483647;
template <bool highMultiply> Vec squareVector(Vec x) {
  Vec hi;
  Vec lo;
  if constexpr (highMultiply) {
    int32x4_t sx = vreinterpretq_s32_u32(x);
    hi = vreinterpretq_u32_s32(vqdmulhq_s32(sx, sx));
    lo = vmulq_u32(x, x);
  } else {
    uint64x2_t a = vmull_u32(vget_low_u32(x), vget_low_u32(x));
    uint64x2_t b = vmull_high_u32(x, x);
    lo = vcombine_u32(vmovn_u64(a), vmovn_u64(b));
    hi = vcombine_u32(vshrn_n_u64(a, 31), vshrn_n_u64(b, 31));
  }
  Vec p = vdupq_n_u32(prime);
  Vec sum = vaddq_u32(vandq_u32(lo, p), hi);
  return vsubq_u32(sum, vandq_u32(vcgeq_u32(sum, p), p));
}

#include <numeric>
constexpr Word N = 1 << 17;
// Each subgroup element imposes one XOR equation between two table entries.
struct Tables {
  std::vector<uint8_t> label = std::vector<uint8_t>(2 * N);
  Word salt = 0;
  Word left(Word x) const { return x & (N - 1); }
  Word right(Word x) const { return N + ((x * salt) >> (32 - 17)); }
  unsigned get(Word x) const { return label[left(x)] ^ label[right(x)]; }
  Tables() {
    for (salt = 2654435761u;; salt += 2) {
      std::vector<Word> parent(2 * N);
      std::iota(parent.begin(), parent.end(), 0);
      std::vector<uint8_t> parity(2 * N), rank(2 * N);
      // Accumulate parity along the path to the component root.
      auto root = [&](Word x) {
        unsigned val = 0;
        while (x != parent[x]) {
          val ^= parity[x];
          x = parent[x];
        }
        return std::pair{x, val};
      };
      // An inconsistent cycle invalidates this salt.
      Word y = 1;
      bool ok = true;
      for (Word i = 0; i < 65534; ++i) {
        auto [a, u] = root(left(y));
        auto [b, v] = root(right(y));
        auto diff = u ^ v ^ ((i & 1) ^ 1);
        if (a == b) {
          if (diff) {
            ok = false;
            break;
          }
        } else {
          if (rank[a] > rank[b])
            std::swap(a, b);
          parent[a] = b;
          parity[a] = diff;
          rank[b] += (rank[a] == rank[b]);
        }
        y = uint64_t(y) * 1251907261ULL % prime;
      }
      if (!ok)
        continue;
      for (Word j = 0; j < 2 * N; ++j)
        label[j] = root(j).second;
      break;
    }
  }
};
template <bool lookup>
__attribute__((noinline)) void eval(const std::vector<Word> &x,
                                    std::vector<Word> &out, const Tables &t) {
  for (size_t i = 0; i < x.size(); i += 32) {
    Vec a[8], b[8];
    for (int k = 0; k < 8; ++k)
      a[k] = b[k] = vld1q_u32(&x[i + k * 4]);
    for (int j = 0; j < (lookup ? 15 : 30); ++j)
      for (int k = 0; k < 8; ++k)
        b[k] = squareVector<true>(b[k]);
    for (int k = 0; k < 8; ++k) {
      if constexpr (lookup) {
        Vec hi = vreinterpretq_u32_s32(vqdmulhq_s32(
            vreinterpretq_s32_u32(a[k]), vreinterpretq_s32_u32(b[k])));
        Vec sum =
            vaddq_u32(hi, vandq_u32(vmulq_u32(a[k], b[k]), vdupq_n_u32(prime)));
        Word ys[4];
        vst1q_u32(ys, vminq_u32(sum, vsubq_u32(sum, vdupq_n_u32(prime))));
        for (int z = 0; z < 4; ++z)
          out[i + 4 * k + z] = x[i + 4 * k + z] == 0 || t.get(ys[z]);
      } else
        vst1q_u32(&out[i + k * 4], vshrq_n_u32(vceqq_u32(a[k], b[k]), 31));
    }
  }
}
int main(int argc, char **argv) {
  std::mt19937 gen(argc == 2 ? std::atoi(argv[1]) : 4315);
  Tables t;
  Word y = 1;
  for (Word i = 0; i < 65534; ++i) {
    if (t.get(y) != ((i & 1) ^ 1))
      return 1;
    y = uint64_t(y) * 1251907261ULL % prime;
    if (y == 1 && i != 65533)
      return 1;
  }
  if (y != 1)
    return 1;
  // Exercise zero in every SIMD lane position before the nonzero timing panel.
  std::vector<Word> edge(64), direct(64), projected(64);
  for (size_t i = 0; i < edge.size(); ++i)
    edge[i] = i % 3 == 0 ? 0 : (i % 3 == 1 ? 1 : prime - 1);
  eval<false>(edge, direct, t);
  eval<true>(edge, projected, t);
  for (size_t i = 0; i < edge.size(); ++i)
    if (direct[i] != Word(edge[i] != prime - 1) || projected[i] != direct[i])
      return 4;
  // Six permutations per cycle. Drop the first cycle for timing summaries.
  for (size_t n : {1024, 65536, 1048576}) {
    std::vector<Word> x(n), out(n), ref(n);
    std::array<int, 3> order = {0, 1, 2};
    for (int r = 0; r < 24; ++r) {
      for (auto &v : x)
        v = 1 + gen() % (prime - 1);
      for (int k : order) {
        auto st = std::chrono::steady_clock::now();
        if (k == 2) {
          Tables cold;
          eval<true>(x, out, cold);
        } else if (k == 1)
          eval<true>(x, out, t);
        else
          eval<false>(x, out, t);
        auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                      std::chrono::steady_clock::now() - st)
                      .count();
        if (k == order[0])
          ref = out;
        else if (out != ref)
          return 2;
        printf("%zu %d %d %lld\n", n, r, k, (long long)ns);
      }
      for (size_t i = 0; i < 64; ++i) {
        Word v = x[i];
        for (int j = 0; j < 30; ++j)
          v = uint64_t(v) * v % prime;
        if (ref[i] != Word(v == x[i]))
          return 3;
      }
      std::next_permutation(order.begin(), order.end());
    }
  }
}
