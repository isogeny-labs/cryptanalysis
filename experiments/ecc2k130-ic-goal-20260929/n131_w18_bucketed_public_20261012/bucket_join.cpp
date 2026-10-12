// Exact public-point join after target-ordered first-pair source partition.
#define main archived_join_main
#include "../n41_w8_ninepair_join_control_20261012/join9.cpp"
#undef main
#include <bitset>

struct BucketState {Point point;std::bitset<128> columns;uint16_t a,b;};
static constexpr unsigned PAIRS=30952;
static uint64_t rng_state=0x886277c3da9b7e17ULL;
static uint64_t random_word() {
  rng_state^=rng_state>>12;rng_state^=rng_state<<25;rng_state^=rng_state>>27;
  return rng_state*2685821657736338717ULL;
}
int main(int argc,char**argv) {
 try {
  if(argc!=2)throw std::runtime_error("usage: bucket_join pairs.tsv");
  auto start=std::chrono::steady_clock::now();
  std::ifstream in(argv[1]);if(!in)throw std::runtime_error("input");
  std::string tag;int slots,targets;in>>tag>>slots>>targets;
  if(tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4)throw std::runtime_error("header");
  std::array<std::vector<BucketState>,4> lists;
  std::array<std::vector<bool>,4> seen;
  for(auto&v:lists)v.resize(PAIRS);
  for(auto&v:seen)v.resize(PAIRS);
  std::array<Point,4> raw{};unsigned row_count=0,target_count=0;
  while(in>>tag) {
    if(tag=="T") {
      int id;uint64_t x,y;in>>id>>x>>y;
      if(id<0||id>=4)throw std::runtime_error("target id");
      raw[id]={x,y,false};++target_count;
    } else if(tag=="S") {
      int slot,id,a,b,ca,cb,sa,sb;uint64_t x,y;
      in>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
      if(slot<0||slot>=4||id<0||id>=int(PAIRS)||seen[slot][id]||a>=b||
         ca<0||cb<0||ca>=128||cb>=128||ca==cb||sa<0||sa>1||sb<0||sb>1)
        throw std::runtime_error("source row");
      auto&S=lists[slot][id];S.point={x,y,false};S.a=a;S.b=b;
      S.columns.set(ca);S.columns.set(cb);seen[slot][id]=true;++row_count;
    } else throw std::runtime_error("source tag");
  }
  if(row_count!=4*PAIRS||target_count!=4)throw std::runtime_error("source count");
  for(const auto&v:seen)for(bool x:v)if(!x)throw std::runtime_error("source gap");
  std::vector<unsigned> first;
  for(unsigned i=0;i<PAIRS;++i) {
    const auto&S=lists[0][i];
    unsigned x=S.a&63,y=S.b&63;
    if((x==9&&y==14)||(x==14&&y==9))first.push_back(i);
  }
  if(first.size()!=4)throw std::runtime_error("bucket source count");
  std::unordered_multimap<Point,uint32_t,Hash> left;
  left.max_load_factor(0.8f);left.reserve(first.size()*PAIRS);
  uint64_t left_rejects=0;
  for(auto a:first)for(unsigned b=0;b<PAIRS;++b) {
    if((lists[0][a].columns&lists[1][b].columns).any()) {++left_rejects;continue;}
    left.emplace(add(lists[0][a].point,lists[1][b].point),uint32_t(a)|(uint32_t(b)<<16));
  }
  std::cout<<"SETUP "<<first.size()<<" "<<left.size()<<" "<<left_rejects<<" "
           <<elapsed(start)<<"\n"<<std::flush;
  uint64_t attempts=0,kept=0,hits=0,col_rejects=0;
  while(kept<50000000) {
    ++attempts;unsigned c=random_word()%PAIRS,d=random_word()%PAIRS;
    const auto&C=lists[2][c];const auto&D=lists[3][d];
    if((C.columns&D.columns).any())continue;
    ++kept;Point sum=add(C.point,D.point);
    Point need=add(raw[1],negate(sum));
    auto range=left.equal_range(need);
    for(auto it=range.first;it!=range.second;++it) {
      ++hits;unsigned a=it->second&65535,b=it->second>>16;
      auto cols=lists[0][a].columns|lists[1][b].columns;
      if((cols&(C.columns|D.columns)).any()) {++col_rejects;continue;}
      Point chk=add(add(add(lists[0][a].point,lists[1][b].point),C.point),D.point);
      if(!(chk==raw[1]))throw std::runtime_error("group replay");
      std::cout<<"HIT 1 "<<a<<" "<<b<<" "<<c<<" "<<d<<" "
               <<left.size()<<" "<<attempts<<" "<<kept<<" "<<hits<<" "
               <<col_rejects<<" "<<elapsed(start)<<"\n"<<std::flush;
      return 0;
    }
    if(kept%1000000==0)
      std::cout<<"PROGRESS "<<kept<<" "<<attempts<<" "<<hits<<" "
               <<col_rejects<<" "<<elapsed(start)<<"\n"<<std::flush;
  }
  std::cout<<"EXHAUSTED "<<left.size()<<" "<<attempts<<" "<<kept<<" "
           <<hits<<" "<<col_rejects<<" "<<elapsed(start)<<"\n"<<std::flush;
  return 0;
 } catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
