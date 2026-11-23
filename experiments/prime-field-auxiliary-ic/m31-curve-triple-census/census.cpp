// Exhaustive cardinalities for the two public M31 sumsets. Only totals are emitted.
#include "common.hpp"
#include <bit>
#include <set>
#include <map>
#include <string>

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

template<class Record>
void signed_triples(const std::vector<Point>& basis, Record record) {
    std::vector<Point> terms = basis;
    for (Point point : basis) terms.push_back(neg(point));
    for (size_t i = 0; i < terms.size(); ++i)
        for (size_t j = i; j < terms.size(); ++j)
            for (Point sum : add_batch(add(terms[i], terms[j]), terms, j))
                record(sum);
}

template<class Record>
void canonical_forms(const std::vector<Point>& basis, Record record) {
    for (size_t i = 0; i < basis.size(); ++i) {
        record(basis[i]);
        for (size_t j = i; j < basis.size(); ++j) {
            Point pair = add(basis[i], basis[j]);
            for (size_t k = j; k < basis.size(); ++k)
                record(add(pair, basis[k]));
            for (size_t k = 0; k < basis.size(); ++k)
                if (k != i && k != j) record(add(pair, neg(basis[k])));
        }
    }
}

Coverage census(const std::vector<Point>& basis) {
    Coverage full, check;
    signed_triples(basis, [&](Point p) { full.include(p); });
    canonical_forms(basis, [&](Point p) { check.include(p); });
    if (full.words != check.words || full.infinity != check.infinity)
        throw std::runtime_error("census mismatch");
    return full;
}

// Count halves of negation orbits. These frozen bases do not represent infinity.
std::map<U, U> histogram(const std::vector<Point>& basis, bool use_canonical) {
    std::vector<std::uint32_t> xs;
    xs.reserve(use_canonical ? 83334000 : 167167000);
    auto record = [&](Point p) {
        if (p.inf || !p.y || !oncurve(p)) throw std::runtime_error("unexpected affine orbit");
        xs.push_back(static_cast<std::uint32_t>(p.x));
    };
    if (use_canonical) canonical_forms(basis, record);
    else signed_triples(basis, record);
    std::sort(xs.begin(), xs.end());
    std::set<U> singleton_x;
    for (Point p : basis) singleton_x.insert(p.x);
    std::map<U, U> result;
    for (size_t i = 0; i < xs.size();) {
        size_t end = i + 1;
        while (end < xs.size() && xs[end] == xs[i]) ++end;
        U multiplicity = end - i;
        if (!use_canonical) {
            // Each non-fixed orbit has two outputs in the unfurled traversal.
            assert(multiplicity % 2 == 0);
            multiplicity /= 2;
            // Every signed singleton has 500 syntactic triples formed by
            // adjoining a cancelling pair. All give one coefficient vector.
            if (singleton_x.contains(xs[i])) {
                assert(multiplicity >= basis.size());
                multiplicity -= basis.size() - 1;
            }
        }
        result[multiplicity] += 2;
        i = end;
    }
    return result;
}

void print_histogram(const char* name, const char* path, U expected_coverage) {
    auto basis = read_basis(path);
    auto canonical = histogram(basis, true);
    if (canonical != histogram(basis, false)) throw std::runtime_error("histogram mismatch");
    U coverage = 0, descriptions = 0;
    for (auto [k, points] : canonical) {
        coverage += points;
        descriptions += k * points;
        std::cout << name << ',' << k << ',' << points << '\n';
    }
    if (coverage != expected_coverage || descriptions != 166668000)
        throw std::runtime_error("coverage or description count mismatch");
}

int main(int argc, char** argv) {
    if (argc == 4 && std::string(argv[3]) == "--multiplicity") {
        std::cout << "basis,descriptions,points\n";
        print_histogram("auxiliary", argv[1], 160361708);
        print_histogram("plain", argv[2], 160352874);
        return 0;
    }
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
