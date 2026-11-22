// Target-conditioned fifth-pair residual lookup on the frozen N41 source.
#define main archived_ninepair_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main

#include <bitset>
#include <sstream>

struct Pair { Point point; uint8_t a, b; };
struct Double { Point point; uint16_t i, j; std::bitset<128> columns; };

static uint64_t rng = 0x3c6ef372fe94f82bULL;
static uint64_t word() {
    rng ^= rng >> 12; rng ^= rng << 25; rng ^= rng >> 27;
    return rng * 2685821657736338717ULL;
}
static bool on_curve(Point p) {
    return p.infinity || (sqr(p.y) ^ mul(p.x,p.y)) == (mul(sqr(p.x),p.x) ^ 1);
}
static bool insert(std::bitset<128>& used, const Pair& p) {
    if (p.a >= 128 || p.b >= 128 || p.a == p.b ||
        used.test(p.a) || used.test(p.b)) return false;
    used.set(p.a); used.set(p.b); return true;
}

int main(int argc, char** argv) {
try {
    if (argc != 7) throw std::runtime_error("usage: residual pairs.tsv Qx Qy doubles kept cap_s");
    const auto started=std::chrono::steady_clock::now();
    const Point target{std::stoull(argv[2]),std::stoull(argv[3]),false};
    const uint64_t double_count=std::stoull(argv[4]), kept_limit=std::stoull(argv[5]);
    const double cap_s=std::stod(argv[6]);
    if (!on_curve(target) || double_count>2000000 || kept_limit>100000000 || cap_s<=0)
        throw std::runtime_error("invalid input");
    std::ifstream in(argv[1]); std::string line;
    if (!std::getline(in,line) || line!="ECC2K41_ALLSEED4 4 4")
        throw std::runtime_error("source header mismatch");
    std::vector<Pair> source; unsigned raw_targets=0;
    while (std::getline(in,line)) {
        std::istringstream row(line); std::string tag; row>>tag;
        if (tag=="T") { ++raw_targets; continue; }
        if (tag!="S") throw std::runtime_error("source tag mismatch");
        unsigned slot,id,ma,mb,ca,cb,sa,sb; uint64_t x,y;
        row>>slot>>id>>ma>>mb>>ca>>cb>>sa>>sb>>x>>y;
        if (slot!=0) continue;
        if (id!=source.size() || ma>=mb || ca>=128 || cb>=128 || ca==cb ||
            sa!=((id>>1)&1) || sb!=(id&1))
            throw std::runtime_error("source row mismatch");
        Point p{x,y,false}; if(!on_curve(p)) throw std::runtime_error("source off curve");
        Point doubled=add(p,p), projected=add(doubled,doubled);
        if(projected.infinity || !on_curve(projected)) throw std::runtime_error("bad projection");
        source.push_back({projected,uint8_t(ca),uint8_t(cb)});
    }
    if(source.size()!=30952 || raw_targets!=4) throw std::runtime_error("source size mismatch");
    std::unordered_multimap<Point,uint16_t,Hash> terminal;
    terminal.reserve(source.size());
    for (uint16_t i=0;i<source.size();++i) terminal.emplace(source[i].point,i);
    std::vector<Double> doubles; doubles.reserve(double_count);
    uint64_t double_attempts=0;
    while(doubles.size()<double_count) {
        ++double_attempts;
        uint16_t i=word()%source.size(),j=word()%source.size();
        std::bitset<128> used;
        if(!insert(used,source[i]) || !insert(used,source[j])) continue;
        doubles.push_back({add(source[i].point,source[j].point),i,j,used});
    }
    const double setup_s=elapsed(started);
    std::cout<<"SOURCE_PASS "<<source.size()<<" "<<terminal.size()<<"\n"
             <<"DOUBLE_READY "<<doubles.size()<<" "<<double_attempts<<" "<<setup_s<<"\n"<<std::flush;
    const auto query_start=std::chrono::steady_clock::now();
    uint64_t attempted=0,kept=0,point_hits=0,column_rejects=0;
    while(kept<kept_limit && elapsed(query_start)<cap_s) {
        ++attempted;
        const Double &a=doubles[word()%doubles.size()], &b=doubles[word()%doubles.size()];
        if((a.columns & b.columns).any()) continue;
        ++kept;
        const Point sum=add(a.point,b.point);
        const Point need=add(target,negate(sum));
        auto range=terminal.equal_range(need);
        for(auto it=range.first;it!=range.second;++it) {
            ++point_hits;
            std::bitset<128> all=a.columns|b.columns;
            if(!insert(all,source[it->second])) { ++column_rejects; continue; }
            if(!(add(sum,source[it->second].point)==target))
                throw std::runtime_error("hit group replay mismatch");
            std::cout<<"HIT "<<a.i<<" "<<a.j<<" "<<b.i<<" "<<b.j<<" "
                     <<it->second<<" "<<attempted<<" "<<kept<<" "
                     <<point_hits<<" "<<column_rejects<<" "<<elapsed(query_start)<<"\n"<<std::flush;
            return 0;
        }
    }
    std::cout<<"EXHAUSTED "<<attempted<<" "<<kept<<" "<<point_hits<<" "
             <<column_rejects<<" "<<setup_s<<" "<<elapsed(query_start)<<"\n"<<std::flush;
    return 0;
} catch(const std::exception& e) { std::cerr<<"ERROR "<<e.what()<<"\n"; return 2; }
}
