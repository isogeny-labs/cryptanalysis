// Exact target-conditioned three-pair completion with two unresolved indexed pairs.
#define main archived_ninepair_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main

#include <bitset>
#include <sstream>

struct Pair { Point point; uint8_t a,b; };
struct Double { Point point; uint16_t i,j; std::bitset<128> columns; };
static uint64_t rng=0xbb67ae8584caa73bULL;
static uint64_t word() {
    rng^=rng>>12; rng^=rng<<25; rng^=rng>>27;
    return rng*2685821657736338717ULL;
}
static bool on_curve(Point p) {
    return p.infinity || (sqr(p.y)^mul(p.x,p.y))==(mul(sqr(p.x),p.x)^1);
}
static bool insert(std::bitset<128>& used,const Pair& p) {
    if(p.a>=128||p.b>=128||p.a==p.b||used.test(p.a)||used.test(p.b))return false;
    used.set(p.a);used.set(p.b);return true;
}

int main(int argc,char**argv) {
try {
    if(argc!=7)throw std::runtime_error("usage: triple pairs.tsv Qx Qy width outer_cap query_cap_s");
    auto start=std::chrono::steady_clock::now();
    Point target{std::stoull(argv[2]),std::stoull(argv[3]),false};
    unsigned width=std::stoul(argv[4]);
    uint64_t outer_cap=std::stoull(argv[5]);
    double query_cap_s=std::stod(argv[6]);
    if(!on_curve(target)||width!=6||outer_cap==0||outer_cap>100000||query_cap_s<=0)
        throw std::runtime_error("invalid input");
    std::ifstream in(argv[1]);std::string line;
    if(!std::getline(in,line)||line!="ECC2K41_ALLSEED4 4 4")
        throw std::runtime_error("source header mismatch");
    std::vector<Pair> source;unsigned raw_targets=0;
    while(std::getline(in,line)) {
        std::istringstream row(line);std::string tag;row>>tag;
        if(tag=="T") {++raw_targets;continue;}
        if(tag!="S")throw std::runtime_error("source tag mismatch");
        unsigned slot,id,ma,mb,ca,cb,sa,sb;uint64_t x,y;
        row>>slot>>id>>ma>>mb>>ca>>cb>>sa>>sb>>x>>y;
        if(slot!=0||ma>=(1u<<width)||mb>=(1u<<width))continue;
        if(ma>=mb||ca>=128||cb>=128||ca==cb||sa!=((id>>1)&1)||sb!=(id&1))
            throw std::runtime_error("source row mismatch");
        Point p{x,y,false};if(!on_curve(p))throw std::runtime_error("source off curve");
        Point q=add(p,p);q=add(q,q);
        if(q.infinity||!on_curve(q))throw std::runtime_error("bad subgroup projection");
        source.push_back({q,uint8_t(ca),uint8_t(cb)});
    }
    if(source.size()!=1956||raw_targets!=4)throw std::runtime_error("source count mismatch");
    std::vector<Double> doubles;doubles.reserve(1956*1955/2);
    for(uint16_t i=0;i<source.size();++i)
        for(uint16_t j=i+1;j<source.size();++j) {
            std::bitset<128> used;
            if(!insert(used,source[i])||!insert(used,source[j]))continue;
            doubles.push_back({add(source[i].point,source[j].point),i,j,used});
        }
    std::unordered_multimap<Point,uint32_t,Hash> index;
    index.max_load_factor(0.8f);index.reserve(doubles.size());
    for(uint32_t k=0;k<doubles.size();++k)index.emplace(doubles[k].point,k);
    std::vector<uint32_t> order(doubles.size());
    for(uint32_t i=0;i<order.size();++i)order[i]=i;
    for(size_t i=order.size();i>1;--i)std::swap(order[i-1],order[word()%i]);
    const double setup_s=elapsed(start);
    std::cout<<"SOURCE_PASS "<<source.size()<<" "<<raw_targets<<"\n"
             <<"INDEX_READY "<<doubles.size()<<" "<<index.size()<<" "<<setup_s<<"\n"<<std::flush;
    const auto query_start=std::chrono::steady_clock::now();
    uint64_t families=0,inner=0,point_matches=0,column_rejects=0;
    for(uint32_t code:order) {
        if(families>=outer_cap||elapsed(query_start)>=query_cap_s)break;
        ++families;
        const Double& outer=doubles[code];
        const Point target_minus_outer=add(target,negate(outer.point));
        for(uint16_t k=0;k<source.size();++k) {
            if(outer.columns.test(source[k].a)||outer.columns.test(source[k].b))continue;
            ++inner;
            Point need=add(target_minus_outer,negate(source[k].point));
            auto range=index.equal_range(need);
            for(auto it=range.first;it!=range.second;++it) {
                ++point_matches;
                const Double& tail=doubles[it->second];
                std::bitset<128> all=outer.columns;
                if(!insert(all,source[k])||(all&tail.columns).any()) {
                    ++column_rejects;continue;
                }
                Point check=add(add(outer.point,source[k].point),tail.point);
                if(!(check==target))throw std::runtime_error("group witness mismatch");
                std::cout<<"HIT "<<outer.i<<" "<<outer.j<<" "<<k<<" "
                         <<tail.i<<" "<<tail.j<<" "<<families<<" "<<inner<<" "
                         <<point_matches<<" "<<column_rejects<<" "
                         <<elapsed(query_start)<<"\n"<<std::flush;
                return 0;
            }
        }
    }
    std::cout<<"EXHAUSTED "<<families<<" "<<inner<<" "<<point_matches<<" "
             <<column_rejects<<" "<<setup_s<<" "<<elapsed(query_start)<<"\n"<<std::flush;
    return 0;
} catch(const std::exception& e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
