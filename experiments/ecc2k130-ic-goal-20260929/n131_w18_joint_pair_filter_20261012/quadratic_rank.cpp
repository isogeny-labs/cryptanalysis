// Exact degree-at-most-two evaluation rank of reciprocal sums, for equal seed bins.
#define main archived_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <array>
#include <bitset>
#include <vector>

struct QuadraticState {Point point;std::bitset<128> columns;};
static constexpr int FEATURES=821;
static constexpr int WORDS=(FEATURES+63)/64;
using Feature=std::array<uint64_t,WORDS>;
static Feature feature(uint64_t c) {
  Feature v{};int bit=0;
  auto push=[&](bool yes){if(yes)v[bit/64]|=1ULL<<(bit%64);++bit;};
  push(true);
  for(int i=1;i<41;++i)push((c>>i)&1);
  for(int i=1;i<41;++i)for(int j=i+1;j<41;++j)
    push(((c>>i)&1)&&((c>>j)&1));
  if(bit!=FEATURES)throw std::runtime_error("feature count");
  return v;
}
int main(int argc,char**argv) {
 try {
  if(argc!=3)throw std::runtime_error("usage: quadratic_rank input.tsv output.tsv");
  auto start=std::chrono::steady_clock::now();
  std::ifstream in(argv[1]);if(!in)throw std::runtime_error("input");
  std::string tag;int slots,targets;in>>tag>>slots>>targets;
  if(tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4)throw std::runtime_error("header");
  std::array<std::array<std::vector<QuadraticState>,256>,2> buckets{};
  unsigned rows=0;
  while(in>>tag) {
    if(tag=="T") {int id;uint64_t x,y;in>>id>>x>>y;}
    else if(tag=="S") {
      int slot,id,a,b,ca,cb,sa,sb;uint64_t x,y;
      in>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
      if(slot<0||slot>=4||id<0||id>=30952||a>=b||ca<0||cb<0||
         ca>=128||cb>=128||ca==cb||sa<0||sa>1||sb<0||sb>1)
        throw std::runtime_error("source row");
      if(slot<2) {
        QuadraticState q{{x,y,false},{}};q.columns.set(ca);q.columns.set(cb);
        buckets[slot][a^b].push_back(q);++rows;
      }
    } else throw std::runtime_error("source tag");
  }
  if(rows!=61904)throw std::runtime_error("source count");
  std::ofstream out(argv[2]);if(!out)throw std::runtime_error("output");
  out<<"seed rank probes valid\n";
  unsigned full=0,minrank=FEATURES;uint64_t totalprobes=0,totalvalid=0;
  for(int seed=1;seed<256;++seed) {
    std::array<Feature,FEATURES> basis{};int rank=0;
    uint64_t probes=0,valid=0;
    for(const auto&A:buckets[0][seed]) {
      if(rank==FEATURES)break;
      for(const auto&B:buckets[1][seed]) {
        if(rank==FEATURES)break;
        if((A.columns&B.columns).any())continue;
        ++probes;Point sum=add(A.point,B.point);
        if(sum.infinity||!sum.x)continue;
        uint64_t c=inv(sum.x);if(c&1)throw std::runtime_error("trace invariant");
        ++valid;Feature v=feature(c);
        for(int bit=FEATURES-1;bit>=0;--bit) {
          if(!(v[bit/64]&(1ULL<<(bit%64))))continue;
          if(basis[bit][bit/64]&(1ULL<<(bit%64))) {
            for(int w=0;w<WORDS;++w)v[w]^=basis[bit][w];
          } else {basis[bit]=v;++rank;break;}
        }
      }
    }
    out<<seed<<" "<<rank<<" "<<probes<<" "<<valid<<"\n";
    if(rank==FEATURES)++full;
    minrank=std::min(minrank,unsigned(rank));totalprobes+=probes;totalvalid+=valid;
  }
  std::cout<<"QUADRATIC_RANK "<<full<<" 255 "<<minrank<<" "
           <<totalprobes<<" "<<totalvalid<<" "<<elapsed(start)<<"\n";
  return 0;
 } catch(const std::exception&e) {std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
