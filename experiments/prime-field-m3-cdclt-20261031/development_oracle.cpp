#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace {

using u64 = std::uint64_t;
[[noreturn]] void fail(const std::string& message) {
  throw std::runtime_error(message);
}

void require(bool condition, const std::string& message) {
  if (!condition) fail(message);
}

u64 add_mod(u64 x, u64 y, u64 p) {
  require(x < p && y < p, "noncanonical modular addend");
  return x >= p - y ? x - (p - y) : x + y;
}

u64 sub_mod(u64 x, u64 y, u64 p) {
  return x >= y ? x - y : p - (y - x);
}

u64 mul_mod(u64 x, u64 y, u64 p) {
  require(x < p && y < p, "noncanonical modular factor");
  u64 result = 0;
  while (y != 0) {
    if ((y & 1U) != 0) result = add_mod(result, x, p);
    y >>= 1U;
    if (y != 0) x = add_mod(x, x, p);
  }
  return result;
}

u64 pow_mod(u64 x, u64 exponent, u64 p) {
  u64 result = 1 % p;
  while (exponent != 0) {
    if ((exponent & 1U) != 0) result = mul_mod(result, x, p);
    x = mul_mod(x, x, p);
    exponent >>= 1U;
  }
  return result;
}

u64 inv_mod(u64 x, u64 p) {
  require(x != 0, "inverse of zero");
  return pow_mod(x, p - 2, p);
}

bool is_prime(u64 n) {
  if (n < 2) return false;
  if ((n & 1U) == 0) return n == 2;
  for (u64 d = 3; d * d <= n; d += 2) {
    if (n % d == 0) return false;
  }
  return true;
}

struct Field {
  u64 p;
  u64 nonsquare;
};

struct Fp2 {
  u64 a = 0;
  u64 b = 0;

  friend bool operator==(const Fp2&, const Fp2&) = default;
  friend bool operator<(const Fp2& lhs, const Fp2& rhs) {
    return std::tie(lhs.a, lhs.b) < std::tie(rhs.a, rhs.b);
  }
};

Fp2 fp2(u64 a, u64 b, const Field& f) { return {a % f.p, b % f.p}; }
Fp2 add(Fp2 x, Fp2 y, const Field& f) {
  return {add_mod(x.a, y.a, f.p), add_mod(x.b, y.b, f.p)};
}
Fp2 neg(Fp2 x, const Field& f) {
  return {x.a == 0 ? 0 : f.p - x.a, x.b == 0 ? 0 : f.p - x.b};
}
Fp2 sub(Fp2 x, Fp2 y, const Field& f) { return add(x, neg(y, f), f); }
Fp2 mul(Fp2 x, Fp2 y, const Field& f) {
  const u64 real = add_mod(mul_mod(x.a, y.a, f.p),
                           mul_mod(f.nonsquare, mul_mod(x.b, y.b, f.p), f.p), f.p);
  const u64 imag = add_mod(mul_mod(x.a, y.b, f.p), mul_mod(x.b, y.a, f.p), f.p);
  return {real, imag};
}
Fp2 square(Fp2 x, const Field& f) { return mul(x, x, f); }
Fp2 inv(Fp2 x, const Field& f) {
  const u64 norm = sub_mod(mul_mod(x.a, x.a, f.p),
                           mul_mod(f.nonsquare, mul_mod(x.b, x.b, f.p), f.p), f.p);
  require(norm != 0, "Fp2 inverse of zero");
  const u64 scale = inv_mod(norm, f.p);
  return {mul_mod(x.a, scale, f.p),
          x.b == 0 ? 0 : mul_mod(f.p - x.b, scale, f.p)};
}
Fp2 divide(Fp2 x, Fp2 y, const Field& f) { return mul(x, inv(y, f), f); }
bool is_zero(Fp2 x) { return x.a == 0 && x.b == 0; }
bool is_rational(Fp2 x) { return x.b == 0; }

struct Point {
  bool infinity = true;
  Fp2 x{};
  Fp2 y{};

  friend bool operator==(const Point&, const Point&) = default;
};

struct Curve {
  Field field;
  u64 a;
  u64 b;
};

Fp2 curve_rhs(const Curve& curve, Fp2 x) {
  const Fp2 x2 = square(x, curve.field);
  return add(add(mul(x2, x, curve.field),
                 mul(fp2(curve.a, 0, curve.field), x, curve.field), curve.field),
             fp2(curve.b, 0, curve.field), curve.field);
}

bool on_curve(const Curve& curve, const Point& point) {
  return point.infinity || square(point.y, curve.field) == curve_rhs(curve, point.x);
}

Point point_neg(const Curve& curve, Point point) {
  if (!point.infinity) point.y = neg(point.y, curve.field);
  return point;
}

Point point_add(const Curve& curve, const Point& lhs, const Point& rhs) {
  require(on_curve(curve, lhs) && on_curve(curve, rhs), "addition input off curve");
  if (lhs.infinity) return rhs;
  if (rhs.infinity) return lhs;
  const Field& f = curve.field;
  if (lhs.x == rhs.x && is_zero(add(lhs.y, rhs.y, f))) return {};

  Fp2 lambda;
  if (lhs == rhs) {
    require(!is_zero(lhs.y), "doubling rational 2-torsion");
    lambda = divide(add(mul(fp2(3, 0, f), square(lhs.x, f), f), fp2(curve.a, 0, f), f),
                    mul(fp2(2, 0, f), lhs.y, f), f);
  } else {
    lambda = divide(sub(rhs.y, lhs.y, f), sub(rhs.x, lhs.x, f), f);
  }
  const Fp2 x3 = sub(sub(square(lambda, f), lhs.x, f), rhs.x, f);
  const Fp2 y3 = sub(mul(lambda, sub(lhs.x, x3, f), f), lhs.y, f);
  Point out{false, x3, y3};
  require(on_curve(curve, out), "addition output off curve");
  return out;
}

Point point_sub(const Curve& curve, const Point& lhs, const Point& rhs) {
  return point_add(curve, lhs, point_neg(curve, rhs));
}

std::vector<Fp2> roots_fp2(const Curve& curve, u64 x) {
  const Field& f = curve.field;
  const Fp2 rhs = curve_rhs(curve, fp2(x, 0, f));
  std::vector<Fp2> roots;
  for (u64 a = 0; a < f.p; ++a) {
    for (u64 b = 0; b < f.p; ++b) {
      const Fp2 candidate{a, b};
      if (square(candidate, f) == rhs) roots.push_back(candidate);
    }
  }
  std::sort(roots.begin(), roots.end());
  roots.erase(std::unique(roots.begin(), roots.end()), roots.end());
  return roots;
}

std::vector<Point> rational_points_at_x(const Curve& curve, u64 x) {
  std::vector<Point> points;
  for (const Fp2 root : roots_fp2(curve, x)) {
    if (is_rational(root)) points.push_back({false, fp2(x, 0, curve.field), root});
  }
  return points;
}

u64 rational_group_order(const Curve& curve) {
  u64 order = 1;
  for (u64 x = 0; x < curve.field.p; ++x) order += rational_points_at_x(curve, x).size();
  return order;
}

u64 first_nonsquare(u64 p) {
  for (u64 d = 2; d < p; ++d) {
    if (pow_mod(d, (p - 1) / 2, p) == p - 1) return d;
  }
  fail("no quadratic nonresidue");
}

bool nonsingular(u64 p, u64 a, u64 b) {
  const u64 term_a = mul_mod(4 % p, mul_mod(mul_mod(a, a, p), a, p), p);
  const u64 term_b = mul_mod(27 % p, mul_mod(b, b, p), p);
  return add_mod(term_a, term_b, p) != 0;
}

struct Instance {
  Curve curve;
  u64 group_order;
  std::array<std::vector<u64>, 3> windows;
  std::array<Point, 3> planted;
  Point target;
};

void validate_instance(const Instance& instance) {
  const Curve& curve = instance.curve;
  require(is_prime(curve.field.p) && curve.field.p > 3, "unsupported field prime");
  require(nonsingular(curve.field.p, curve.a, curve.b), "singular curve");
  require(is_prime(instance.group_order) && (instance.group_order & 1U) == 1,
          "whole group order is not odd prime");
  require(rational_group_order(curve) == instance.group_order, "wrong whole-group order");
  require(!instance.target.infinity && on_curve(curve, instance.target)
              && is_rational(instance.target.x) && is_rational(instance.target.y),
          "target is not a finite rational point");

  std::set<u64> seen;
  for (const auto& window : instance.windows) {
    require(!window.empty(), "empty factor-base window");
    for (const u64 x : window) {
      require(x < curve.field.p, "window word outside field domain");
      require(seen.insert(x).second, "factor-base windows overlap in abscissa");
    }
  }
  Point planted_sum{};
  for (std::size_t i = 0; i < 3; ++i) {
    const Point& point = instance.planted[i];
    require(!point.infinity && on_curve(curve, point) && is_rational(point.x)
                && is_rational(point.y),
            "planted summand is not a finite rational point");
    require(std::find(instance.windows[i].begin(), instance.windows[i].end(), point.x.a)
                != instance.windows[i].end(),
            "planted summand outside its window");
    planted_sum = point_add(curve, planted_sum, point);
  }
  require(planted_sum == instance.target, "planted tuple does not sum to target");
}

Instance make_fixture() {
  const std::array<u64, 8> primes{5, 7, 11, 13, 17, 19, 23, 29};
  for (const u64 p : primes) {
    const Field field{p, first_nonsquare(p)};
    for (u64 a = 0; a < p; ++a) {
      for (u64 b = 1; b < p; ++b) {
        if (!nonsingular(p, a, b)) continue;
        const Curve curve{field, a, b};
        const u64 order = rational_group_order(curve);
        if (!is_prime(order) || order < 11 || (order & 1U) == 0) continue;

        std::vector<Point> representatives;
        for (u64 x = 0; x < p; ++x) {
          const auto points = rational_points_at_x(curve, x);
          if (!points.empty()) representatives.push_back(points.front());
        }
        if (representatives.size() < 3) continue;
        for (std::size_t i = 0; i < representatives.size(); ++i) {
          for (std::size_t j = i + 1; j < representatives.size(); ++j) {
            for (std::size_t k = j + 1; k < representatives.size(); ++k) {
              const std::array<Point, 3> planted{
                  representatives[i], representatives[j], representatives[k]};
              Point target{};
              for (const Point& point : planted) target = point_add(curve, target, point);
              if (target.infinity) continue;

              std::array<std::vector<u64>, 3> windows;
              std::set<u64> assigned;
              for (std::size_t w = 0; w < 3; ++w) {
                windows[w].push_back(planted[w].x.a);
                assigned.insert(planted[w].x.a);
              }
              std::size_t next = 0;
              for (u64 x = 0; x < p; ++x) {
                if (assigned.count(x) == 0) windows[next++ % 3].push_back(x);
              }
              for (auto& window : windows) std::sort(window.begin(), window.end());
              Instance instance{curve, order, windows, planted, target};
              validate_instance(instance);
              return instance;
            }
          }
        }
      }
    }
  }
  fail("could not construct deterministic development fixture");
}

u64 s3(const Curve& curve, u64 x1, u64 x2, u64 x3) {
  const u64 p = curve.field.p;
  const u64 x1_minus_x2 = sub_mod(x1, x2, p);
  const u64 leading = mul_mod(mul_mod(x1_minus_x2, x1_minus_x2, p),
                              mul_mod(x3, x3, p), p);
  const u64 x1x2_plus_a = add_mod(mul_mod(x1, x2, p), curve.a, p);
  const u64 middle_inner = add_mod(mul_mod(add_mod(x1, x2, p), x1x2_plus_a, p),
                                   mul_mod(2 % p, curve.b, p), p);
  const u64 middle = mul_mod(mul_mod(2 % p, middle_inner, p), x3, p);
  const u64 tail_square = mul_mod(sub_mod(mul_mod(x1, x2, p), curve.a, p),
                                  sub_mod(mul_mod(x1, x2, p), curve.a, p), p);
  const u64 tail_b = mul_mod(mul_mod(4 % p, curve.b, p), add_mod(x1, x2, p), p);
  return sub_mod(add_mod(leading, tail_square, p), add_mod(middle, tail_b, p), p);
}

int point_sign(const Point& point, const Curve& curve) {
  require(!point.infinity && is_rational(point.y), "sign requested for nonrational point");
  const u64 opposite = point.y.a == 0 ? 0 : curve.field.p - point.y.a;
  return point.y.a <= opposite ? 0 : 1;
}

std::string model_key(const std::array<Point, 3>& points, const Curve& curve) {
  std::ostringstream out;
  for (std::size_t i = 0; i < points.size(); ++i) {
    if (i != 0) out << ';';
    out << points[i].x.a << ':' << point_sign(points[i], curve);
  }
  return out.str();
}

bool replays(const Instance& instance, const std::array<Point, 3>& points) {
  Point sum{};
  for (const Point& point : points) {
    if (point.infinity || !on_curve(instance.curve, point) || !is_rational(point.x)
        || !is_rational(point.y)) return false;
    sum = point_add(instance.curve, sum, point);
  }
  return sum == instance.target;
}

std::set<std::string> exhaustive_models(const Instance& instance, u64* fp2_candidates) {
  std::set<std::string> models;
  u64 candidates = 0;
  for (const u64 x0 : instance.windows[0]) {
    for (const Fp2 y0 : roots_fp2(instance.curve, x0)) {
      const Point p0{false, fp2(x0, 0, instance.curve.field), y0};
      for (const u64 x1 : instance.windows[1]) {
        for (const Fp2 y1 : roots_fp2(instance.curve, x1)) {
          const Point p1{false, fp2(x1, 0, instance.curve.field), y1};
          for (const u64 x2 : instance.windows[2]) {
            for (const Fp2 y2 : roots_fp2(instance.curve, x2)) {
              ++candidates;
              const Point p2{false, fp2(x2, 0, instance.curve.field), y2};
              const std::array<Point, 3> points{p0, p1, p2};
              Point sum{};
              for (const Point& point : points) sum = point_add(instance.curve, sum, point);
              if (sum != instance.target) continue;
              require(is_rational(y0) && is_rational(y1) && is_rational(y2),
                      "guarded rationality counterexample");
              const Point intermediate = point_add(instance.curve, p0, p1);
              require(!intermediate.infinity && is_rational(intermediate.x),
                      "unexpected exceptional chained-S3 intermediate");
              require(s3(instance.curve, x0, x1, intermediate.x.a) == 0,
                      "first chained S3 relation failed");
              require(s3(instance.curve, intermediate.x.a, x2, instance.target.x.a) == 0,
                      "second chained S3 relation failed");
              models.insert(model_key(points, instance.curve));
            }
          }
        }
      }
    }
  }
  *fp2_candidates = candidates;
  return models;
}

std::set<std::string> two_window_models(const Instance& instance) {
  std::set<std::string> models;
  for (const u64 x0 : instance.windows[0]) {
    for (const Point p0 : rational_points_at_x(instance.curve, x0)) {
      for (const u64 x1 : instance.windows[1]) {
        for (const Point p1 : rational_points_at_x(instance.curve, x1)) {
          const Point needed = point_sub(
              instance.curve, point_sub(instance.curve, instance.target, p0), p1);
          if (needed.infinity || !is_rational(needed.x) || !is_rational(needed.y)) continue;
          if (std::find(instance.windows[2].begin(), instance.windows[2].end(), needed.x.a)
              == instance.windows[2].end()) continue;
          const std::array<Point, 3> points{p0, p1, needed};
          require(replays(instance, points), "two-window oracle emitted invalid model");
          models.insert(model_key(points, instance.curve));
        }
      }
    }
  }
  return models;
}

using Clause = std::vector<int>;

std::vector<Clause> sinz_exactly_one(std::size_t n) {
  require(n >= 1, "exactly-one needs at least one selector");
  if (n == 1) return {{1}};
  std::vector<Clause> clauses;
  Clause at_least_one;
  for (std::size_t i = 1; i <= n; ++i) at_least_one.push_back(static_cast<int>(i));
  clauses.push_back(std::move(at_least_one));
  const auto aux = [n](std::size_t i) { return static_cast<int>(n + i); };
  clauses.push_back({-1, aux(1)});
  for (std::size_t i = 2; i < n; ++i) {
    clauses.push_back({-static_cast<int>(i), aux(i)});
    clauses.push_back({-aux(i - 1), aux(i)});
    clauses.push_back({-static_cast<int>(i), -aux(i - 1)});
  }
  clauses.push_back({-static_cast<int>(n), -aux(n - 1)});
  return clauses;
}

bool literal_value(int literal, u64 assignment) {
  const std::size_t index = static_cast<std::size_t>(std::abs(literal) - 1);
  const bool value = ((assignment >> index) & 1U) != 0;
  return literal > 0 ? value : !value;
}

bool clauses_hold(const std::vector<Clause>& clauses, u64 assignment) {
  for (const Clause& clause : clauses) {
    bool satisfied = false;
    for (const int literal : clause) satisfied |= literal_value(literal, assignment);
    if (!satisfied) return false;
  }
  return true;
}

void test_sinz_encoding() {
  for (std::size_t n = 1; n <= 8; ++n) {
    const auto clauses = sinz_exactly_one(n);
    const std::size_t auxiliaries = n == 1 ? 0 : n - 1;
    require(clauses.size() == (n == 1 ? 1 : 3 * n - 3), "wrong Sinz clause count");
    for (u64 selectors = 0; selectors < (u64{1} << n); ++selectors) {
      bool extendible = false;
      for (u64 aux = 0; aux < (u64{1} << auxiliaries); ++aux) {
        const u64 assignment = selectors | (aux << n);
        extendible |= clauses_hold(clauses, assignment);
      }
      require(extendible == (__builtin_popcountll(selectors) == 1),
              "Sinz exactly-one semantic mismatch");
    }
  }
}

void test_lambda_lift(const Instance& instance) {
  const Curve& curve = instance.curve;
  const u64 p = curve.field.p;
  for (u64 x = 0; x < p; ++x) {
    const u64 rhs = curve_rhs(curve, fp2(x, 0, curve.field)).a;
    bool rational_lift = false;
    for (u64 y = 0; y < p; ++y) rational_lift |= mul_mod(y, y, p) == rhs;
    for (u64 t = 0; t < p; ++t) {
      for (u64 s0 = 0; s0 < p; ++s0) {
        u64 solutions = 0;
        for (u64 lambda = 0; lambda < p; ++lambda) {
          const u64 displacement = sub_mod(mul_mod(mul_mod(2 % p, t, p), lambda, p), s0, p);
          solutions += mul_mod(displacement, displacement, p) == rhs;
        }
        const u64 discriminant = mul_mod(mul_mod(16 % p, mul_mod(t, t, p), p), rhs, p);
        const u64 bcoef = t == 0 || s0 == 0 ? 0 : p - mul_mod(4 % p, mul_mod(t, s0, p), p);
        const u64 acoef = mul_mod(4 % p, mul_mod(t, t, p), p);
        const u64 ccoef = sub_mod(mul_mod(s0, s0, p), rhs, p);
        const u64 expanded = sub_mod(mul_mod(bcoef, bcoef, p),
                                     mul_mod(4 % p, mul_mod(acoef, ccoef, p), p), p);
        require(discriminant == expanded, "lambda discriminant identity failed");
        if (t != 0) {
          require((solutions != 0) == rational_lift, "lambda/rational-lift equivalence failed");
        } else {
          require(solutions == (mul_mod(s0, s0, p) == rhs ? p : 0),
                  "t=0 exceptional branch misclassified");
        }
      }
    }
  }
}

void test_compact_range(const Instance& instance) {
  const u64 p = instance.curve.field.p;
  unsigned bits = 0;
  while ((u64{1} << bits) < p) ++bits;
  require(bits < 63, "test field too large");
  u64 invalid = 0;
  for (u64 word = 0; word < (u64{1} << bits); ++word) {
    const bool accepted = word < p;
    invalid += !accepted;
    require(accepted == (word <= p - 1), "unsigned range comparator mismatch");
  }
  require(invalid == (u64{1} << bits) - p, "invalid-word census mismatch");
}

std::string canonical_ir(const Instance& instance) {
  std::ostringstream out;
  out << "prime-field-m3-ir/v1\n";
  out << "p=" << instance.curve.field.p << "\n";
  out << "a=" << instance.curve.a << "\n";
  out << "b=" << instance.curve.b << "\n";
  out << "group_order=" << instance.group_order << "\n";
  out << "target=" << instance.target.x.a << ',' << instance.target.y.a << "\n";
  out << "selector_semantics=abscissa-plus-rational-lift-sign\n";
  out << "field_range=unsigned-less-than-p\n";
  out << "exactly_one=sinz-sequential-plus-at-least-one\n";
  for (std::size_t i = 0; i < 3; ++i) {
    out << "window" << i << '=';
    for (std::size_t j = 0; j < instance.windows[i].size(); ++j) {
      if (j != 0) out << ',';
      out << instance.windows[i][j];
    }
    out << "\n";
  }
  return out.str();
}

void mutation_controls(const Instance& instance) {
  Instance overlap = instance;
  overlap.windows[1][0] = overlap.windows[0][0];
  bool rejected = false;
  try {
    validate_instance(overlap);
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  require(rejected, "overlapping-window mutation accepted");

  Instance bad_word = instance;
  bad_word.windows[2][0] = instance.curve.field.p;
  rejected = false;
  try {
    validate_instance(bad_word);
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  require(rejected, "out-of-range word mutation accepted");

  std::array<Point, 3> corrupted = instance.planted;
  corrupted[0] = point_neg(instance.curve, corrupted[0]);
  require(!replays(instance, corrupted), "corrupted sign/root replay accepted");

  Instance bad_curve = instance;
  bad_curve.curve.b = add_mod(bad_curve.curve.b, 1, bad_curve.curve.field.p);
  rejected = false;
  try {
    validate_instance(bad_curve);
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  require(rejected, "coefficient mutation accepted");
}

struct SelfTestResult {
  Instance fixture;
  u64 fp2_candidates;
  std::size_t models;
};

SelfTestResult run_self_test() {
  test_sinz_encoding();
  const Instance instance = make_fixture();
  test_lambda_lift(instance);
  test_compact_range(instance);
  mutation_controls(instance);
  u64 candidates = 0;
  const auto exhaustive = exhaustive_models(instance, &candidates);
  const auto two_window = two_window_models(instance);
  require(!exhaustive.empty(), "fixture has no accepted model");
  require(exhaustive == two_window, "two-window oracle/model-set mismatch");
  require(exhaustive.count(model_key(instance.planted, instance.curve)) == 1,
          "planted projected model missing");
  const std::string first = canonical_ir(instance);
  const std::string second = canonical_ir(instance);
  require(first == second, "canonical IR is not byte stable");
  return {instance, candidates, exhaustive.size()};
}

void print_sizing() {
  std::cout << "s,window_cardinality,selector_variables,sinz_aux_variables,total_boolean_variables,exactly_one_clauses\n";
  for (unsigned s = 6; s <= 27; ++s) {
    const u64 n = u64{1} << s;
    const u64 selectors = 3 * n;
    const u64 auxiliaries = 3 * (n - 1);
    const u64 clauses = 3 * (3 * n - 3);
    std::cout << s << ',' << n << ',' << selectors << ',' << auxiliaries << ','
              << selectors + auxiliaries << ',' << clauses << '\n';
  }
}

void print_summary(const SelfTestResult& result) {
  const Instance& instance = result.fixture;
  std::cout << "PASS development oracle\n";
  std::cout << "fixture p=" << instance.curve.field.p << " a=" << instance.curve.a
            << " b=" << instance.curve.b << " order=" << instance.group_order << '\n';
  std::cout << "windows=" << instance.windows[0].size() << ',' << instance.windows[1].size()
            << ',' << instance.windows[2].size() << " fp2_candidates=" << result.fp2_candidates
            << " projected_models=" << result.models << '\n';
  std::cout << "checks=sinz_exactly_one,compact_range,lambda_discriminant,t0_branch,"
               "disjoint_windows,sign_replay,three_summand_rationality,chained_s3,two_window_oracle\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const std::string mode = argc == 1 ? "--self-test" : argv[1];
    if (mode == "--sizing") {
      print_sizing();
      return 0;
    }
    const SelfTestResult result = run_self_test();
    if (mode == "--self-test") {
      print_summary(result);
    } else if (mode == "--fixture") {
      std::cout << canonical_ir(result.fixture);
    } else if (mode == "--all") {
      print_summary(result);
      print_sizing();
    } else {
      std::cerr << "usage: " << argv[0] << " [--self-test|--fixture|--sizing|--all]\n";
      return 2;
    }
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
