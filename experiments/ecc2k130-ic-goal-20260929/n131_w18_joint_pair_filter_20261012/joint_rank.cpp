// Exact affine rank of two diagonal all-seed pair sums, conditioned on both seeds.
#define main archived_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <bitset>
#include <cstring>

struct RankState { Point point; std::bitset<128> columns; uint16_t id; };
static void write_u16(std::ofstream& out,uint16_t x) {
    char b[2]={char(x&255),char(x>>8)};out.write(b,2);
}
int main(int argc,char**argv) {
 try {
    if(argc!=4) throw std::runtime_error("usage: joint_rank input.tsv ranks.tsv witnesses.bin");
    auto start=std::chrono::steady_clock::now();
    std::ifstream in(argv[1]);if(!in)throw std::runtime_error("input");
    std::string tag;int slots,targets;in>>tag>>slots>>targets;
    if(tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4)throw std::runtime_error("header");
    std::array<std::array<std::vector<RankState>,256>,2> buckets{};
    std::array<std::vector<bool>,2> seen{};for(auto& x:seen)x.resize(30952,false);
    unsigned rows=0;
    while(in>>tag) {
      if(tag=="T") {int id;uint64_t x,y;in>>id>>x>>y;}
      else if(tag=="S") {
        int slot,id,a,b,ca,cb,sa,sb;uint64_t x,y;
        in>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
        if(slot<0||slot>=4||id<0||id>=30952||a>=b||ca==cb||
           ca<0||cb<0||ca>=128||cb>=128||sa<0||sa>1||sb<0||sb>1)
          throw std::runtime_error("source row");
        if(slot<2) {
          if(seen[slot][id])throw std::runtime_error("duplicate row");
          seen[slot][id]=true;
          RankState state{{x,y,false},{},uint16_t(id)};
          state.columns.set(ca);state.columns.set(cb);
          buckets[slot][a^b].push_back(state);++rows;
        }
      } else throw std::runtime_error("tag");
    }
    if(rows!=2*30952)throw std::runtime_error("row count");
    for(const auto& v:seen)for(bool b:v)if(!b)throw std::runtime_error("missing row");
    std::ofstream ranks(argv[2]),witnesses(argv[3],std::ios::binary);
    if(!ranks||!witnesses)throw std::runtime_error("output open");
    ranks<<"seed0 seed1 rank probes pivot_offset\n";
    uint64_t total_probes=0,total_pivots=0,rank_full=0,rank_deficient=0;
    unsigned min_rank=41;
    for(unsigned s=1;s<256;++s)for(unsigned t=1;t<256;++t) {
      uint64_t basis[42]{};unsigned rank=0;uint64_t probes=0,offset=total_pivots;
      for(const auto& A:buckets[0][s]) {
        if(rank==41)break;
        for(const auto& B:buckets[1][t]) {
          if(rank==41)break;
          if((A.columns&B.columns).any())continue;
          Point sum=add(A.point,B.point);++probes;
          if(sum.infinity||!sum.x)continue;
          uint64_t c=inv(sum.x);
          if(c&1)throw std::runtime_error("trace-zero invariant failed");
          uint64_t row=(1ULL<<41)|c;
          for(int bit=41;bit>=0;--bit) {
            if(!(row&(1ULL<<bit)))continue;
            if(basis[bit])row^=basis[bit];
            else {basis[bit]=row;++rank;write_u16(witnesses,A.id);write_u16(witnesses,B.id);
                  ++total_pivots;break;}
          }
        }
      }
      total_probes+=probes;min_rank=std::min(min_rank,rank);
      if(rank==41)++rank_full;else ++rank_deficient;
      ranks<<s<<" "<<t<<" "<<rank<<" "<<probes<<" "<<offset<<"\n";
    }
    ranks.close();witnesses.close();
    std::cout<<"RANK_RESULT "<<rank_full<<" "<<rank_deficient<<" "<<min_rank
             <<" "<<total_probes<<" "<<total_pivots<<" "<<elapsed(start)<<"\n";
    return 0;
 } catch(const std::exception&e) {std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
