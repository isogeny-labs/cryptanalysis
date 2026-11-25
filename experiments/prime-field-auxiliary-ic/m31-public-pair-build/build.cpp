#include "common.hpp"
#ifdef M31_FLAT_INDEX
#include "../m31-public-hash-layout/flat.hpp"
using Index = FlatIndex;
#else
using Index = std::unordered_map<U, uint32_t, Hasher>;
#endif
using Clock = std::chrono::steady_clock;
int main(int argc, char **argv) {
  if (argc != 4)
    return 1;
  bool compact = std::string(argv[2]) == "compact";
  std::ifstream points(argv[1]);
  U x, y;
  A = 2;
  B = 14;
  std::vector<Point> basis;
  while (points >> x >> y)
    basis.push_back({x, y, false});
  if (basis.size() != 500)
    return 2;
  auto start = Clock::now();
  std::vector<Point> signedPoints;
  signedPoints.reserve(2 * basis.size());
  for (auto pt : basis) {
    if (!oncurve(pt))
      return 3;
    signedPoints.push_back(pt);
    signedPoints.push_back(neg(pt));
  }
  Index index;
  index.reserve(compact ? 250000 : 500000);
  size_t finite = 0;
  auto visit = [&](size_t i, size_t j, Point pt) {
    if (pt.inf)
      return;
    ++finite;
    if (compact && (pt.y & 1))
      return;
    index.emplace(compact ? pt.x : key(pt), uint32_t((i << 16) | j));
  };
#ifdef M31_REFLECT_ROWS
  for (size_t i = 0; i < signedPoints.size(); i += 2) {
    auto sums = add_batch(signedPoints[i], signedPoints, i);
    for (size_t j = i; j < signedPoints.size(); ++j)
      visit(i, j, sums[j - i]);
    for (size_t j = i + 1; j < signedPoints.size(); ++j)
      visit(i + 1, j, neg(sums[(j ^ 1) - i]));
  }
#else
  for (size_t i = 0; i < signedPoints.size(); ++i) {
    auto sums = add_batch(signedPoints[i], signedPoints, i);
    for (size_t off = 0; off < sums.size(); ++off)
      visit(i, i + off, sums[off]);
  }
#endif
  auto stop = Clock::now();
  if (finite != 500000)
    return 4;
  std::ifstream ref(argv[3], std::ios::binary);
  uint32_t rec[2];
  size_t verified = 0;
  while (ref.read(reinterpret_cast<char *>(rec), sizeof(rec))) {
    auto pos = index.find(rec[0]);
    if (pos == index.end() || pos->second != rec[1])
      return 5;
    ++verified;
  }
  if (verified != index.size() || ref.gcount() != 0 || !ref.eof())
    return 6;
  std::cout << std::chrono::duration_cast<std::chrono::nanoseconds>(stop -
                                                                    start)
                   .count()
            << '\n';
}
