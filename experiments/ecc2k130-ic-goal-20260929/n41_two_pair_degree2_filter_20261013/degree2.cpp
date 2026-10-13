// Search for an exact degree <= 2 Boolean annihilator of two-pair x outputs.
#define main archived_nine_pair_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main

#include <array>
#include <bitset>
#include <fstream>
#include <sstream>
#include <sys/resource.h>

struct PairState { Point point; uint8_t col_a, col_b; };
static uint64_t random_state = 0x6a09e667f3bcc909ULL;
static uint64_t random_word() {
    random_state ^= random_state >> 12;
    random_state ^= random_state << 25;
    random_state ^= random_state >> 27;
    return random_state * 2685821657736338717ULL;
}
static bool on_curve(Point p) {
    return p.infinity || (sqr(p.y) ^ mul(p.x,p.y)) == (mul(sqr(p.x),p.x) ^ 1);
}
static bool add_columns(std::bitset<128>& used, const PairState& p) {
    if (p.col_a == p.col_b || used.test(p.col_a) || used.test(p.col_b)) return false;
    used.set(p.col_a); used.set(p.col_b); return true;
}

constexpr unsigned FEATURES = 1 + 41 + 41*40/2;
constexpr unsigned WORDS = (FEATURES + 63)/64;
using Bits = std::array<uint64_t, WORDS>;

static void setbit(Bits& value, unsigned i) { value[i/64] |= uint64_t(1) << (i%64); }
static bool getbit(const Bits& value, unsigned i) { return (value[i/64] >> (i%64)) & 1; }
static void xorbits(Bits& a, const Bits& b) {
    for (unsigned i=0; i<WORDS; ++i) a[i] ^= b[i];
}
static Bits features(uint64_t x) {
    Bits out{};
    setbit(out, 0);
    for (unsigned i=0; i<41; ++i) if ((x>>i)&1) setbit(out, 1+i);
    unsigned k=42;
    for (unsigned i=0; i<41; ++i)
        for (unsigned j=i+1; j<41; ++j,++k)
            if (((x>>i)&1) && ((x>>j)&1)) setbit(out,k);
    if (k != FEATURES) throw std::runtime_error("feature count drift");
    return out;
}

int main(int argc, char** argv) {
try {
    if (argc != 5) throw std::runtime_error("usage: degree2 pairs.tsv witnesses.tsv result.json max_attempts");
    auto started = std::chrono::steady_clock::now();
    std::ifstream in(argv[1]);
    if (!in) throw std::runtime_error("source missing");
    std::string line;
    if (!std::getline(in,line) || line != "ECC2K41_ALLSEED4 4 4")
        throw std::runtime_error("source header mismatch");
    std::vector<PairState> source;
    while (std::getline(in,line)) {
        std::istringstream row(line);
        std::string tag; row >> tag;
        if (tag == "T") continue;
        if (tag != "S") throw std::runtime_error("source tag mismatch");
        unsigned slot,sid,a,b,ca,cb,sa,sb; uint64_t x,y;
        row >> slot >> sid >> a >> b >> ca >> cb >> sa >> sb >> x >> y;
        if (slot != 0) continue;
        if (sid != source.size() || sid >= 30952 || a >= b || ca >= 128 || cb >= 128 ||
            ca == cb || sa > 1 || sb > 1 || !row || !row.eof())
            throw std::runtime_error("invalid source row");
        Point raw{x,y,false};
        if (!on_curve(raw)) throw std::runtime_error("source point off curve");
        Point twice=add(raw,raw), projected=add(twice,twice);
        if (projected.infinity || !on_curve(projected))
            throw std::runtime_error("invalid projected source point");
        source.push_back({projected,uint8_t(ca),uint8_t(cb)});
    }
    if (source.size()!=30952) throw std::runtime_error("source size drift");
    for (unsigned i=0;i<source.size();++i)
        if (!(negate(source[i].point)==source[i^3].point))
            throw std::runtime_error("sign partner drift");
    const uint64_t cap=std::stoull(argv[4]);
    if (cap==0 || cap>1000000) throw std::runtime_error("invalid attempt cap");
    std::ofstream witnesses(argv[2]);
    if (!witnesses) throw std::runtime_error("witness open failed");
    witnesses << "attempt\tstate_a\tstate_b\tx\tpivot\n";
    std::array<Bits, FEATURES> basis{};
    std::array<bool, FEATURES> occupied{};
    uint64_t attempted=0, valid=0, zero_rejected=0, column_rejected=0, rank=0;
    for (;attempted<cap && rank<FEATURES;) {
        ++attempted;
        unsigned a=random_word()%source.size(), b=random_word()%source.size();
        std::bitset<128> used;
        if (!add_columns(used,source[a]) || !add_columns(used,source[b])) {
            ++column_rejected; continue;
        }
        Point sum=add(source[a].point,source[b].point);
        if (sum.infinity) { ++zero_rejected; continue; }
        ++valid;
        Bits row=features(sum.x);
        for (unsigned pivot=0;pivot<FEATURES;++pivot) if (getbit(row,pivot)) {
            if (occupied[pivot]) {xorbits(row,basis[pivot]); continue;}
            occupied[pivot]=true; basis[pivot]=row; ++rank;
            witnesses << attempted << '\t' << a << '\t' << b << '\t'
                      << sum.x << '\t' << pivot << '\n';
            break;
        }
    }
    witnesses.flush();
    if (!witnesses) throw std::runtime_error("witness write failed");
    struct rusage usage{}; getrusage(RUSAGE_SELF,&usage);
    std::ofstream result(argv[3]);
    if (!result) throw std::runtime_error("result open failed");
    result << "{\"status\":\"" << (rank==FEATURES?"FULL_DEGREE2_RANK":"RANK_DEFICIT_AT_CAP")
           << "\",\"features\":" << FEATURES << ",\"rank\":" << rank
           << ",\"attempts\":" << attempted << ",\"valid_outputs\":" << valid
           << ",\"column_rejected\":" << column_rejected
           << ",\"identity_rejected\":" << zero_rejected
           << ",\"source_states\":" << source.size()
           << ",\"elapsed_seconds_exploratory\":" << elapsed(started)
           << ",\"maxrss_bytes\":" << usage.ru_maxrss << "}\n";
    if (!result) throw std::runtime_error("result write failed");
    std::cout << (rank==FEATURES?"FULL_DEGREE2_RANK":"RANK_DEFICIT_AT_CAP")
              << " rank=" << rank << " attempts=" << attempted << "\n";
    return 0;
} catch (const std::exception& e) {std::cerr << "ERROR " << e.what() << "\n"; return 2;}
}
