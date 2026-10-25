#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/resource.h>

using U128=unsigned __int128;
using Clock=std::chrono::steady_clock;
constexpr uint64_t MOD=(1ULL<<41)|(1ULL<<3)|1;
constexpr uint64_t MASK=(1ULL<<41)-1;
uint64_t mul(uint64_t a,uint64_t b){uint64_t r=0;while(b){if(b&1)r^=a;b>>=1;a<<=1;if(a&(1ULL<<41))a^=MOD;}return r;}
uint64_t sq(uint64_t a){return mul(a,a);}
int degree(uint64_t x){if(!x)throw std::runtime_error("zero inverse");return 63-__builtin_clzll(x);}
uint64_t inv(uint64_t a){
 if(!a)throw std::runtime_error("zero inverse");
 uint64_t u=a,v=MOD;U128 x=1,y=0;
 while(u!=1){int j=degree(u)-degree(v);if(j<0){std::swap(u,v);std::swap(x,y);j=-j;}u^=v<<j;x^=y<<j;}
 for(int bit=127;bit>=41;--bit)if((x>>bit)&1)x^=U128(MOD)<<(bit-41);
 uint64_t r=static_cast<uint64_t>(x);if(mul(a,r)!=1)throw std::runtime_error("inverse check");return r;
}
uint64_t lin(const std::array<uint64_t,8>&a,uint64_t x,int count){
 uint64_t y=0,v=x;for(int i=0;i<count;++i){y^=mul(a[i],v);v=sq(v);}return y;
}
struct Root{uint64_t u,u2,tau;};
struct Family{int left,right;std::array<Root,8> roots;};
struct Chart{uint64_t t,t2,tau;};
double secs(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
int main(int argc,char**argv){
 try{
  if(argc<2||argc>3)throw std::runtime_error("usage: quotient input.tsv [--rank]");
  bool rank_mode=argc==3&&std::string(argv[2])=="--rank";
  if(argc==3&&!rank_mode)throw std::runtime_error("unknown mode");
  auto started=Clock::now();std::ifstream f(argv[1]);if(!f)throw std::runtime_error("input missing");
  std::string tag;int rank,products_count,charts_count,families_count;uint64_t seed;
  f>>tag>>rank>>products_count>>charts_count>>families_count>>seed;
  if(tag!="N41Q"||rank!=7||products_count!=40||charts_count!=160||families_count!=1554||seed>MASK)
     throw std::runtime_error("header");
  std::array<uint64_t,7> basis{};std::array<uint64_t,40> products{};
  std::array<Chart,160> charts{};std::array<bool,40> pseen{};std::array<bool,160> tseen{};
  for(int i=0;i<7;++i){f>>tag>>basis[i];if(tag!="B"||basis[i]>MASK||!basis[i])throw std::runtime_error("basis");}
  for(int i=0;i<40;++i){int code;uint64_t p;f>>tag>>code>>p;
   if(tag!="P"||code<0||code>=40||pseen[code]||p>MASK)throw std::runtime_error("product");
   products[code]=p;pseen[code]=true;
  }
  for(int i=0;i<160;++i){int id;uint64_t t;f>>tag>>id>>t;
   if(tag!="T"||id<0||id>=160||tseen[id]||t>MASK)throw std::runtime_error("chart");
   charts[id]={t,sq(t),mul(t,t^1)};tseen[id]=true;
  }
  std::vector<Family> families;families.reserve(1554);
  for(int i=0;i<1554;++i){Family row;f>>tag>>row.left>>row.right;
   if(tag!="C"||row.left<0||row.left>=40||row.right<0||row.right>=40)
      throw std::runtime_error("family");
   for(int j=0;j<8;++j){uint64_t v;f>>v;if(v>MASK||v==1)throw std::runtime_error("root");
    uint64_t u=mul(v,inv(v^1));row.roots[j]={u,sq(u),mul(u,u^1)};
   }
   families.push_back(row);
  }
  if(f>>tag)throw std::runtime_error("trailing input");
  std::array<uint64_t,8> a{};a[0]=1;int d=0;
  for(uint64_t b:basis){uint64_t value=lin(a,b,d+1);if(!value)throw std::runtime_error("dependent basis");
   std::array<uint64_t,8> next{};
   for(int i=0;i<=d+1;++i){uint64_t left=i?sq(a[i-1]):0;
    uint64_t right=i<=d?mul(value,a[i]):0;next[i]=left^right;}
   a=next;++d;
  }
  if(d!=7||a[7]!=1)throw std::runtime_error("vanisher degree");
  for(uint64_t b:basis)if(lin(a,b,8))throw std::runtime_error("vanisher basis");
  std::array<uint64_t,8> asq{};for(int i=0;i<8;++i)asq[i]=sq(a[i]);
  std::array<uint64_t,7> basis_sq{};for(int i=0;i<7;++i)basis_sq[i]=sq(basis[i]);
  uint64_t S=sq(seed),S2=sq(S);
  uint64_t families_seen=0,queries=0,exceptions=0,gate_hits=0,source_hits=0;
  int hit_state=-1,hit_left=-1,hit_right=-1,hit_root=-1,hit_code=-1;
  auto query_start=Clock::now();
  for(int sid=0;sid<160;++sid){auto &chart=charts[sid];
   for(auto &family:families){++families_seen;
    for(int ri=0;ri<8;++ri){auto &root=family.roots[ri];
     uint64_t B=mul(root.tau,chart.tau),D=chart.t2^root.u2;
     uint64_t c0=sq(D)^S2^mul(S2^S,sq(B));
     uint64_t c1=mul(B,D^S),c2=mul(D,D^1);bool got=false;
     if(rank_mode){
      std::array<uint64_t,41> piv{};
      for(int bi=0;bi<7;++bi){uint64_t value=mul(c1,basis[bi])^mul(c2,basis_sq[bi]);
       while(value){int bit=63-__builtin_clzll(value);
        if(piv[bit])value^=piv[bit];else{piv[bit]=value;break;}}
      }
      uint64_t value=c0;got=true;
      while(value){int bit=63-__builtin_clzll(value);
       if(!piv[bit]){got=false;break;}value^=piv[bit];}
     }else if(c2){uint64_t inverted=inv(c2),lam=mul(c1,inverted),y=mul(c0,inverted);
      uint64_t pl=lin(a,lam,8);
      std::array<uint64_t,8> powers{},q{};powers[0]=lam;q[7]=1;
      for(int k=1;k<8;++k)powers[k]=sq(powers[k-1]);
      for(int k=7;k>=1;--k){uint64_t sk=mul(pl,a[k])^asq[k-1];
        q[k-1]=sk^mul(q[k],powers[k]);}
      if(queries==0&&mul(q[0],lam)!=mul(pl,a[0]))throw std::runtime_error("quotient recurrence");
      got=lin(q,y,8)==0;
     }else if(c1){++exceptions;got=lin(a,mul(c0,inv(c1)),8)==0;}
     else{++exceptions;got=c0==0;}
     ++queries;if(!got)continue;++gate_hits;
     for(int code=0;code<40;++code){uint64_t p=products[code];
      if((c0^mul(c1,p)^mul(c2,sq(p)))==0){++source_hits;
       hit_state=sid;hit_left=family.left;hit_right=family.right;hit_root=ri;hit_code=code;}
     }
    }
   }
  }
  double query_s=secs(query_start),setup_s=secs(started)-query_s;
  if(families_seen!=248640||queries!=1989120||gate_hits!=1||source_hits!=1||
     hit_state!=0||hit_left!=24||hit_right!=37||hit_root!=2||hit_code!=10)
     throw std::runtime_error("frozen hit census");
  rusage usage{};getrusage(RUSAGE_SELF,&usage);
  std::cout<<"{\"status\":\"PASS_N41_FULL_GATE\",\"mode\":\""<<(rank_mode?"rank":"quotient")
           <<"\",\"families\":"<<families_seen
           <<",\"queries\":"<<queries<<",\"exceptions\":"<<exceptions
           <<",\"gate_hits\":"<<gate_hits<<",\"source_hits\":"<<source_hits
           <<",\"hit\":["<<hit_state<<","<<hit_left<<","<<hit_right<<","<<hit_root<<","<<hit_code<<"]"
           <<",\"setup_s\":"<<setup_s<<",\"query_s\":"<<query_s
           <<",\"wall_s\":"<<secs(started)<<",\"maxrss_raw\":"<<usage.ru_maxrss<<"}\n";
  return 0;
 }catch(std::exception const& e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
