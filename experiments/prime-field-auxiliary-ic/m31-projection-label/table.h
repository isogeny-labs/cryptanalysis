#pragma once
#include <algorithm>
#include <cstdint>
#include <numeric>
#include <utility>
#include <vector>

namespace m31_projection {
using Word = uint32_t;
constexpr Word prime = 2147483647;
constexpr Word N = 1 << 17;
// Each subgroup element imposes one XOR equation between two table entries.
struct Tables {
  std::vector<uint64_t> labels = std::vector<uint64_t>(2 * N / 64);
  Word salt = 0;
  Word left(Word x) const { return x & (N - 1); }
  Word right(Word x) const { return N + ((x * salt) >> (32 - 17)); }
  unsigned labelBit(Word vertex) const {
    return (labels[vertex / 64] >> (vertex % 64)) & 1;
  }
  unsigned get(Word x) const { return labelBit(left(x)) ^ labelBit(right(x)); }
  bool isSquare(Word input, Word projected) const { return input == 0 || get(projected); }
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
        labels[j / 64] |= uint64_t(root(j).second) << (j % 64);
      break;
    }
  }
};
} // namespace m31_projection
