// Replays the degree-two rank rows with independent full-product field arithmetic.
#define main archived_audit_main
#include "audit_rank.cpp"
#undef main

static constexpr int QF=821, QW=(QF+63)/64;
using QVec=std::array<uint64_t,QW>;
static QVec quadratic_feature(uint64_t c) {
  QVec v{};int k=0;
  auto set=[&](bool b){if(b)v[k/64]|=1ULL<<(k%64);++k;};
  set(true);
  for(int i=1;i<=40;++i)set((c>>i)&1);
  for(int i=1;i<=40;++i)for(int j=i+1;j<=40;++j)
    set(((c>>i)&1)&&((c>>j)&1));
  if(k!=QF)throw std::runtime_error("feature dimension");
  return v;
}
int main(int argc,char**argv) {
 try {
  if(argc!=3)throw std::runtime_error("usage: quadratic_audit pairs.tsv ranks.tsv");
  auto start=std::chrono::steady_clock::now();
  std::ifstream in(argv[1]),table(argv[2]);if(!in||!table)throw std::runtime_error("input");
  std::string tag;int slots,targets;in>>tag>>slots>>targets;
  if(tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4)throw std::runtime_error("header");
  std::array<std::array<std::vector<State>,256>,2> groups{};
  std::array<std::vector<bool>,2> seen;for(auto&v:seen)v.resize(30952);
  int rows=0;
  while(in>>tag) {
    if(tag=="T") {int id;uint64_t x,y;in>>id>>x>>y;}
    else if(tag=="S") {
      int slot,id,a,b,ca,cb,sa,sb;uint64_t x,y;
      in>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
      if(slot<0||slot>=4||id<0||id>=30952||a>=b||ca<0||cb<0||
         ca>=128||cb>=128||ca==cb||sa<0||sa>1||sb<0||sb>1)
        throw std::runtime_error("source row");
      if(slot<2) {
        if(seen[slot][id])throw std::runtime_error("duplicate row");
        seen[slot][id]=true;State S;S.P={x,y};S.columns.set(ca);S.columns.set(cb);
        groups[slot][a^b].push_back(S);++rows;
      }
    } else throw std::runtime_error("source tag");
  }
  if(rows!=61904)throw std::runtime_error("row count");
  for(auto&v:seen)for(bool b:v)if(!b)throw std::runtime_error("missing row");
  std::string header;std::getline(table,header);
  if(header!="seed rank probes valid")throw std::runtime_error("rank header");
  uint64_t totalprobe=0,totalvalid=0;
  for(int seed=1;seed<256;++seed) {
    int listed,rank_expected;uint64_t probes_expected,valid_expected;
    if(!(table>>listed>>rank_expected>>probes_expected>>valid_expected)||
       listed!=seed||rank_expected!=QF)throw std::runtime_error("table row");
    std::array<QVec,QF> basis{};int rank=0;uint64_t probes=0,valid=0;
    for(const auto&A:groups[0][seed]) {
      if(rank==QF)break;
      std::vector<const State*> right;
      std::vector<uint64_t> den,num,base;
      for(const auto&B:groups[1][seed]) {
        if((A.columns&B.columns).any())continue;
        if(A.P.x==B.P.x)throw std::runtime_error("exceptional pair");
        right.push_back(&B);den.push_back(A.P.x^B.P.x);
        num.push_back(A.P.y^B.P.y);base.push_back(A.P.x^B.P.x);
      }
      auto invden=batch_inverse(den);
      std::vector<uint64_t> sumx;
      for(size_t j=0;j<den.size();++j) {
        uint64_t slope=mul(num[j],invden[j]);
        uint64_t x=sq(slope)^slope^base[j];
        if(!x)throw std::runtime_error("zero x pair");
        sumx.push_back(x);
      }
      auto reciprocals=batch_inverse(sumx);
      for(auto c:reciprocals) {
        ++probes;++valid;
        if(c&1)throw std::runtime_error("trace witness");
        QVec v=quadratic_feature(c);
        for(int bit=0;bit<QF;++bit) {
          if(!(v[bit/64]&(1ULL<<(bit%64))))continue;
          if(basis[bit][bit/64]&(1ULL<<(bit%64))) {
            for(int w=0;w<QW;++w)v[w]^=basis[bit][w];
          } else {basis[bit]=v;++rank;break;}
        }
        if(rank==QF)break;
      }
    }
    if(rank!=QF||probes!=probes_expected||valid!=valid_expected)
      throw std::runtime_error("rank/probe mismatch seed "+std::to_string(seed)+
                               " rank "+std::to_string(rank)+
                               " probes "+std::to_string(probes));
    totalprobe+=probes;totalvalid+=valid;
  }
  unsigned extra;if(table>>extra)throw std::runtime_error("trailing rows");
  double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  std::cout<<"PASS_INDEPENDENT_QUADRATIC "<<255<<" "<<QF<<" "
           <<totalprobe<<" "<<totalvalid<<" "<<elapsed<<"\n";
  return 0;
 } catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
