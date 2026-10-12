// Exact all-seed four-pair public-point join; source pairing is frozen by Sage.
#define main archived_join_main
#include "../../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <bitset>

struct SourceState { Point point; std::bitset<128> columns; uint16_t a,b; };
static uint64_t rng_state = 0x24f4907c59b8ed31ULL;
static uint64_t random_word() {
    rng_state ^= rng_state >> 12; rng_state ^= rng_state << 25;
    rng_state ^= rng_state >> 27; return rng_state * 2685821657736338717ULL;
}
static constexpr unsigned COUNT=30952;
static constexpr uint64_t KEEP=3000000;
static bool sample(const std::array<std::vector<SourceState>,4>& lists,
                   unsigned lo, unsigned& a, unsigned& b, Point& sum,
                   std::bitset<128>& cols) {
    a=random_word()%COUNT; b=random_word()%COUNT;
    const auto& A=lists[lo][a]; const auto& B=lists[lo+1][b];
    if ((A.columns&B.columns).any()) return false;
    cols=A.columns|B.columns;
    sum=add(A.point,B.point); return true;
}
int main(int argc,char** argv) {
 try {
    if(argc!=2) throw std::runtime_error("usage: join4 pairs.tsv");
    auto start=std::chrono::steady_clock::now();
    std::ifstream in(argv[1]); if(!in) throw std::runtime_error("input missing");
    std::string tag; int slots,targets; in>>tag>>slots>>targets;
    if(tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4) throw std::runtime_error("header");
    std::array<std::vector<SourceState>,4> lists;
    for(auto& list:lists) list.resize(COUNT);
    std::array<Point,4> raw{};
    std::array<std::vector<bool>,4> seen;
    for(auto& v:seen) v.resize(COUNT,false);
    unsigned rows=0,ts=0;
    while(in>>tag) {
      if(tag=="T") { int id;uint64_t x,y;in>>id>>x>>y;
        if(id<0||id>=4) throw std::runtime_error("target id");
        raw[id]={x,y,false};++ts;
      } else if(tag=="S") {
        int slot,id,a,b,ca,cb,sa,sb;uint64_t x,y;
        in>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
        if(slot<0||slot>=4||id<0||id>=int(COUNT)||seen[slot][id]||
           a>=b||ca==cb||ca<0||cb<0||ca>=128||cb>=128||
           sa<0||sa>1||sb<0||sb>1) throw std::runtime_error("source row");
        SourceState s{{x,y,false},{},uint16_t(a),uint16_t(b)};
        s.columns.set(ca);s.columns.set(cb);
        lists[slot][id]=s;seen[slot][id]=true;++rows;
      } else throw std::runtime_error("tag");
    }
    if(rows!=4*COUNT||ts!=4) throw std::runtime_error("source count");
    for(const auto& v:seen) for(bool b:v) if(!b) throw std::runtime_error("missing row");
    std::cout<<"SOURCE_PASS "<<rows<<" "<<elapsed(start)<<"\n"<<std::flush;
    std::unordered_multimap<Point,uint32_t,Hash> left;
    left.max_load_factor(0.8f);left.reserve(KEEP);
    uint64_t left_attempts=0;
    while(left.size()<KEEP) {
      ++left_attempts;unsigned a,b;Point sum;std::bitset<128> cols;
      if(!sample(lists,0,a,b,sum,cols)) continue;
      left.emplace(sum,uint32_t(a)|(uint32_t(b)<<16));
    }
    double setup=elapsed(start);
    std::cout<<"LEFT_DONE "<<left.size()<<" "<<left_attempts<<" "<<setup<<"\n"<<std::flush;
    uint64_t right_attempts=0,right_kept=0,point_hits=0,column_rejects=0;
    while(right_kept<KEEP) {
      ++right_attempts;unsigned c,d;Point sum;std::bitset<128> cols;
      if(!sample(lists,2,c,d,sum,cols)) continue;
      ++right_kept;
      for(unsigned t=0;t<4;++t) {
        Point need=add(raw[t],negate(sum));
        auto range=left.equal_range(need);
        for(auto it=range.first;it!=range.second;++it) {
          ++point_hits;unsigned a=it->second&65535,b=it->second>>16;
          auto leftcols=lists[0][a].columns|lists[1][b].columns;
          if((leftcols&cols).any()) {++column_rejects;continue;}
          Point chk=add(add(add(lists[0][a].point,lists[1][b].point),
                             lists[2][c].point),lists[3][d].point);
          if(!(chk==raw[t])) throw std::runtime_error("replay mismatch");
          std::cout<<"HIT "<<t<<" "<<a<<" "<<b<<" "<<c<<" "<<d
                   <<" "<<left.size()<<" "<<left_attempts<<" "<<right_kept
                   <<" "<<right_attempts<<" "<<point_hits<<" "<<column_rejects
                   <<" "<<setup<<" "<<elapsed(start)<<"\n"<<std::flush;
          return 0;
        }
      }
    }
    std::cout<<"EXHAUSTED "<<left.size()<<" "<<left_attempts<<" "<<right_kept
             <<" "<<right_attempts<<" "<<point_hits<<" "<<column_rejects
             <<" "<<setup<<" "<<elapsed(start)<<"\n"<<std::flush;
    return 0;
 } catch(const std::exception& e) {std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
