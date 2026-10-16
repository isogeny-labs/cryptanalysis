// Exact product-over-third-span gate on all valid second codes at once.
#define main inherited_root_main
#include "../n41_native_rootproduct_span_20261014/native.cpp"
#undef main

#include <bit>
#include <cstring>
#include <tuple>

static constexpr int SIDE = 40;
static constexpr int TENSOR = 17 * 17 * 25;
static constexpr int CHART = 33;

static std::vector<Word> read_symbolic(const char* path) {
    if (std::endian::native != std::endian::little) throw std::runtime_error("endian");
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    if (!in || in.tellg() != std::streampos(TENSOR * CHART * sizeof(Word)))
        throw std::runtime_error("symbolic tensor size");
    in.seekg(0);
    std::vector<Word> out(TENSOR * CHART);
    in.read(reinterpret_cast<char*>(out.data()), out.size() * sizeof(Word));
    if (!in) throw std::runtime_error("symbolic tensor read");
    return out;
}

static std::vector<Word> specialize(const std::vector<Word>& poly, Word t) {
    std::vector<Word> out(TENSOR);
    for (int c = 0; c < TENSOR; ++c) {
        Word value = 0;
        for (int a = CHART - 1; a >= 0; --a) value = fm(value, t) ^ poly[size_t(c) * CHART + a];
        out[c] = value;
    }
    return out;
}

static Poly divide_linear(const Poly& f, Word a) {
    if (f.size() < 2 || f.back() != 1) throw std::runtime_error("linear division input");
    Poly out(f.size() - 1, 0);
    out.back() = 1;
    for (int k = int(out.size()) - 2; k >= 0; --k)
        out[k] = f[k + 1] ^ fm(a, out[k + 1]);
    if ((f[0] ^ fm(a, out[0])) != 0) throw std::runtime_error("non-root division");
    trim(out);
    return out;
}

static std::array<std::array<Word, 25>, 17> contract_p(const std::vector<Word>& tensor, Word p) {
    std::array<Word, 17> pp{};
    pp[0] = 1;
    for (int i = 1; i < 17; ++i) pp[i] = fm(pp[i - 1], p);
    std::array<std::array<Word, 25>, 17> out{};
    for (int i = 0; i < 17; ++i) if (pp[i])
        for (int j = 0; j < 17; ++j)
            for (int k = 0; k < 25; ++k) {
                Word c = tensor[(i * 17 + j) * 25 + k];
                if (c) out[j][k] ^= fm(c, pp[i]);
            }
    return out;
}

static Poly in_q(const std::array<std::array<Word, 25>, 17>& by_q_r, Word r) {
    Poly out(17);
    for (int j = 0; j < 17; ++j) {
        Word value = 0;
        for (int k = 24; k >= 0; --k) value = fm(value, r) ^ by_q_r[j][k];
        out[j] = value;
    }
    trim(out);
    return out;
}
