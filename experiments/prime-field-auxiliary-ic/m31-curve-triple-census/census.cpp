// Exhaustive cardinalities for the two public M31 sumsets. Only totals are emitted.
#include "common.hpp"
#include <bit>
#include <set>

struct Coverage {
    std::vector<U> words = std::vector<U>((FP + 63) / 64);
    bool infinity = false;

    void include(Point p) {
        if (p.inf) {
            infinity = true;
        } else {
            assert(p.x < FP && p.y != 0 && oncurve(p));
            words[p.x / 64] |= U{1} << (p.x % 64);
        }
    }
};

std::vector<Point> read_basis(const char* path) {
    std::ifstream in(path);
    U p, n, a, b, px, py, qx, qy, count;
    if (!(in >> p >> n >> a >> b >> px >> py >> qx >> qy >> count) ||
        p != FP || n != 2147505293 || a != 2 || b != 14 || count != 500)
        throw std::runtime_error("unexpected fixture");
    A = a;
    B = b;
    std::set<U> coordinates;
    std::vector<Point> basis;
    for (U i = 0; i < count; ++i) {
        Point point{0, 0, false};
        if (!(in >> point.x >> point.y) || point.x >= FP || point.y >= FP ||
            !point.y || !oncurve(point) || !coordinates.insert(point.x).second)
            throw std::runtime_error("invalid representative");
        basis.push_back(point);
    }
    return basis;
}

Coverage census(const std::vector<Point>& basis) {
    Coverage full;
    std::vector<Point> terms = basis;
    for (Point point : basis) terms.push_back(neg(point));
    for (size_t i = 0; i < terms.size(); ++i)
        for (size_t j = i; j < terms.size(); ++j)
            for (Point sum : add_batch(add(terms[i], terms[j]), terms, j))
                full.include(sum);

    // Repeat in the scalar arithmetic path, using the canonical descriptions
    // from TripleCoverage.lean and the invariance of x under negation.
    Coverage check;
    for (size_t i = 0; i < basis.size(); ++i) {
        check.include(basis[i]);
        for (size_t j = i; j < basis.size(); ++j) {
            Point pair = add(basis[i], basis[j]);
            for (size_t k = j; k < basis.size(); ++k)
                check.include(add(pair, basis[k]));
            for (size_t k = 0; k < basis.size(); ++k)
                if (k != i && k != j) check.include(add(pair, neg(basis[k])));
        }
    }
    if (full.words != check.words || full.infinity != check.infinity)
        throw std::runtime_error("census mismatch");
    return full;
}

int main(int argc, char** argv) {
    if (argc != 3) return 2;
    auto aux = census(read_basis(argv[1]));
    auto plain = census(read_basis(argv[2]));
    U a = aux.infinity, b = plain.infinity, both = aux.infinity && plain.infinity;
    for (size_t i = 0; i < aux.words.size(); ++i) {
        a += 2 * std::popcount(aux.words[i]);
        b += 2 * std::popcount(plain.words[i]);
        both += 2 * std::popcount(aux.words[i] & plain.words[i]);
    }
    std::cout << "auxiliary,plain,both,auxiliary_only,plain_only,neither\n"
              << a << ',' << b << ',' << both << ',' << a-both << ',' << b-both
              << ',' << 2147505293ULL-a-b+both << '\n';
}
