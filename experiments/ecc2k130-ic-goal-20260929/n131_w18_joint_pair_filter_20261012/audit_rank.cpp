// Independent full pivotal-witness replay with batch inversion and low-pivot rank.
#include <array>
#include <bitset>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <algorithm>
#include <chrono>
using U128=unsigned __int128;
static constexpr uint64_t MOD=(1ULL<<41)|(1ULL<<3)|1;
static uint64_t mul(uint64_t a,uint64_t b) {
  U128 p=0,x=a;
  while(b) {if(b&1)p^=x;b>>=1;x<<=1;}
  for(int i=80;i>=41;--i)if((p>>i)&1)p^=U128(MOD)<<(i-41);
  return uint64_t(p);
}
static uint64_t sq(uint64_t a){return mul(a,a);}
static uint64_t inverse(uint64_t a) {
  if(!a)throw std::runtime_error("zero inverse");
  uint64_t out=1,exponent=(1ULL<<41)-2;
  while(exponent) {if(exponent&1)out=mul(out,a);a=sq(a);exponent>>=1;}
  return out;
}
static std::vector<uint64_t> batch_inverse(const std::vector<uint64_t>&x) {
  std::vector<uint64_t> prefix(x.size()+1,1),out(x.size());
  for(size_t i=0;i<x.size();++i) {
    if(!x[i])throw std::runtime_error("zero batch member");
    prefix[i+1]=mul(prefix[i],x[i]);
  }
  uint64_t back=inverse(prefix.back());
  for(size_t i=x.size();i-->0;) {
    out[i]=mul(back,prefix[i]);back=mul(back,x[i]);
    if(mul(out[i],x[i])!=1)throw std::runtime_error("batch inverse replay");
  }
  return out;
}
struct Point {uint64_t x=0,y=0;};
struct State {Point P;std::bitset<128> columns;uint8_t seed=0;bool seen=false;};
static uint16_t read_u16(std::ifstream&in) {
  unsigned char b[2];in.read(reinterpret_cast<char*>(b),2);
  if(!in)throw std::runtime_error("short witness file");
  return uint16_t(b[0])|(uint16_t(b[1])<<8);
}
int main(int argc,char**argv) {
 try {
  if(argc!=4)throw std::runtime_error("usage: audit_rank pairs.tsv ranks.tsv witnesses.bin");
  auto start=std::chrono::steady_clock::now();
  std::ifstream source(argv[1]),ranks(argv[2]),witnesses(argv[3],std::ios::binary);
  if(!source||!ranks||!witnesses)throw std::runtime_error("input open");
  std::string tag;int slots,targets;source>>tag>>slots>>targets;
  if(tag!="ECC2K41_ALLSEED4"||slots!=4||targets!=4)throw std::runtime_error("header");
  std::array<std::vector<State>,2> states;
  for(auto&v:states)v.resize(30952);
  unsigned rows=0;
  while(source>>tag) {
    if(tag=="T") {int id;uint64_t x,y;source>>id>>x>>y;}
    else if(tag=="S") {
      int slot,id,a,b,ca,cb,sa,sb;uint64_t x,y;
      source>>slot>>id>>a>>b>>ca>>cb>>sa>>sb>>x>>y;
      if(slot<0||slot>=4||id<0||id>=30952||a>=b||ca<0||cb<0||
         ca>=128||cb>=128||ca==cb||sa<0||sa>1||sb<0||sb>1)
        throw std::runtime_error("source row");
      if(slot<2) {
        auto&S=states[slot][id];if(S.seen)throw std::runtime_error("duplicate source");
        S.P={x,y};S.columns.set(ca);S.columns.set(cb);S.seed=uint8_t(a^b);
        S.seen=true;++rows;
      }
    } else throw std::runtime_error("source tag");
  }
  if(rows!=61904)throw std::runtime_error("source count");
  for(const auto&v:states)for(const auto&S:v)if(!S.seen)throw std::runtime_error("source gap");
  uint64_t trace_mask=0;
  for(int bit=0;bit<41;++bit) {
    uint64_t x=1ULL<<bit,tr=0;
    for(int k=0;k<41;++k) {tr^=x;x=sq(x);}
    if(tr==1)trace_mask|=1ULL<<bit;
    else if(tr!=0)throw std::runtime_error("trace basis");
  }
  std::string header;std::getline(ranks,header);
  if(header!="seed0 seed1 rank probes pivot_offset")throw std::runtime_error("rank header");
  uint64_t pivots=0,probes_total=0,bins=0;
  for(unsigned s=1;s<256;++s)for(unsigned t=1;t<256;++t) {
    unsigned as,at,expected_rank;uint64_t probes,offset;
    if(!(ranks>>as>>at>>expected_rank>>probes>>offset) ||
       as!=s||at!=t||expected_rank!=41||offset!=pivots)
      throw std::runtime_error("rank row/order");
    probes_total+=probes;
    std::vector<Point> A,B;A.reserve(41);B.reserve(41);
    for(unsigned k=0;k<expected_rank;++k) {
      unsigned id0=read_u16(witnesses),id1=read_u16(witnesses);
      if(id0>=30952||id1>=30952)throw std::runtime_error("witness id");
      const auto&L=states[0][id0];const auto&R=states[1][id1];
      if(L.seed!=s||R.seed!=t||(L.columns&R.columns).any())
        throw std::runtime_error("witness source/column mismatch");
      A.push_back(L.P);B.push_back(R.P);++pivots;
    }
    std::vector<uint64_t> den,nums,base;den.reserve(41);nums.reserve(41);base.reserve(41);
    for(unsigned k=0;k<41;++k) {
      if(A[k].x==B[k].x) {
        if(A[k].y!=B[k].y||!A[k].x)throw std::runtime_error("exceptional sum");
        den.push_back(A[k].x);nums.push_back(A[k].y);base.push_back(0);
      } else {
        den.push_back(A[k].x^B[k].x);nums.push_back(A[k].y^B[k].y);
        base.push_back(A[k].x^B[k].x);
      }
    }
    auto invden=batch_inverse(den);
    std::vector<uint64_t> sumx;sumx.reserve(41);
    for(unsigned k=0;k<41;++k) {
      uint64_t slope=mul(nums[k],invden[k]);
      uint64_t x=sq(slope)^slope^base[k];
      if(!x)throw std::runtime_error("zero-x witness");
      sumx.push_back(x);
    }
    auto reciprocals=batch_inverse(sumx);
    uint64_t basis[42]{};unsigned rank=0;
    for(auto c:reciprocals) {
      if(__builtin_parityll(c&trace_mask))throw std::runtime_error("trace witness");
      uint64_t v=(1ULL<<41)|c;
      for(int bit=0;bit<=41;++bit) {
        if(!(v&(1ULL<<bit)))continue;
        if(basis[bit])v^=basis[bit];
        else {basis[bit]=v;++rank;break;}
      }
    }
    if(rank!=41)throw std::runtime_error("low-pivot rank mismatch");
    ++bins;
  }
  unsigned char tail;if(witnesses.read(reinterpret_cast<char*>(&tail),1))
    throw std::runtime_error("trailing witness data");
  unsigned more;if(ranks>>more)throw std::runtime_error("trailing rank rows");
  double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
  std::cout<<"PASS_INDEPENDENT_LOW_PIVOT "<<bins<<" "<<pivots<<" "<<probes_total
           <<" "<<trace_mask<<" "<<elapsed<<"\n";
  return 0;
 } catch(const std::exception&e) {std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
