// Exact unpinned N41 phi eight-leaf target join; one native worker.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>
#include <sys/resource.h>

using U128 = unsigned __int128;
using Clock = std::chrono::steady_clock;
constexpr uint64_t MOD=(1ULL<<41)|(1ULL<<3)|1;

uint64_t mul(uint64_t a,uint64_t b){
  uint64_t out=0;
  while(b){if(b&1)out^=a;b>>=1;a<<=1;if(a&(1ULL<<41))a^=MOD;}
  return out;
}
uint64_t sq(uint64_t a){return mul(a,a);}
int deg(uint64_t a){if(!a)throw std::runtime_error("zero degree");return 63-__builtin_clzll(a);}
uint64_t inv(uint64_t a){
  if(!a)throw std::runtime_error("zero inverse");
  uint64_t u=a,v=MOD;U128 g=1,h=0;
  while(u!=1){int k=deg(u)-deg(v);if(k<0){std::swap(u,v);std::swap(g,h);k=-k;}u^=v<<k;g^=h<<k;}
  for(int bit=127;bit>=41;--bit)if((g>>bit)&1)g^=U128(MOD)<<(bit-41);
  auto result=uint64_t(g);
  if(mul(a,result)!=1)throw std::runtime_error("inverse check");
  return result;
}
struct Point{
  uint64_t x=0,y=0;bool inf=true;
  bool operator==(const Point&b)const{return inf==b.inf&&(inf||(x==b.x&&y==b.y));}
};
struct Hash{size_t operator()(const Point&p)const{
  if(p.inf)return 0x9e3779b97f4a7c15ULL;
  uint64_t z=p.x^(p.y<<17)^(p.y>>24);z^=z>>30;z*=0xbf58476d1ce4e5b9ULL;
  z^=z>>27;z*=0x94d049bb133111ebULL;return size_t(z^(z>>31));
}};
Point neg(Point p){if(!p.inf)p.y^=p.x;return p;}
Point add(Point p,Point q){
  if(p.inf)return q;if(q.inf)return p;
  uint64_t s,x,y;
  if(p.x==q.x){
    if(p.y!=q.y||!p.x)return {};
    s=p.x^mul(p.y,inv(p.x));x=sq(s)^s;y=sq(p.x)^mul(s^1,x);
  }else{
    s=mul(p.y^q.y,inv(p.x^q.x));x=sq(s)^s^p.x^q.x;
    y=mul(s,p.x^x)^x^p.y;
  }
  return {x,y,false};
}
bool on_curve(Point p){return p.inf||(sq(p.y)^mul(p.x,p.y))==(mul(sq(p.x),p.x)^1);}
uint64_t rss(){struct rusage u{};getrusage(RUSAGE_SELF,&u);return uint64_t(u.ru_maxrss);}
double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
struct State{Point p;uint32_t col=0;int code=0,sign=0;};
struct Pair{Point p;uint32_t cols=0;uint16_t ids=0;};
uint16_t pack2(int a,int b){return uint16_t(a|(b<<6));}
int first(uint16_t ids){return ids&63;}
int second(uint16_t ids){return (ids>>6)&63;}
uint32_t pack4(uint16_t a,uint16_t b){return uint32_t(a)|(uint32_t(b)<<12);}
uint16_t low2(uint32_t x){return uint16_t(x&4095);}
uint16_t high2(uint32_t x){return uint16_t(x>>12);}

int main(int argc,char**argv)try{
  if(argc!=4)throw std::runtime_error("usage: join input.tsv native_cap_seconds rss_cap_bytes");
  auto start=Clock::now();double cap=std::stod(argv[2]);uint64_t rss_cap=std::stoull(argv[3]);
  std::ifstream in(argv[1]);if(!in)throw std::runtime_error("missing input");
  std::string tag;int slots,states;uint64_t tx,ty;in>>tag>>slots>>states>>tx>>ty;
  if(tag!="PHI41"||slots!=8||states!=60)throw std::runtime_error("header");
  Point target{tx,ty,false};if(!on_curve(target))throw std::runtime_error("target curve");
  std::array<std::array<State,60>,8> source{};
  std::array<std::array<bool,60>,8> seen{};int rows=0;
  while(in>>tag){
    int slot,id,code,sign,col;uint64_t x,y;in>>slot>>id>>code>>sign>>col>>x>>y;
    if(!in||tag!="S"||slot<0||slot>=8||id<0||id>=60||seen[slot][id]||
       code<0||code>=64||sign<0||sign>1||col<0||col>=26)
      throw std::runtime_error("state row");
    Point p{x,y,false};if(!on_curve(p)||!x)throw std::runtime_error("state curve");
    source[slot][id]={p,uint32_t(1)<<col,code,sign};seen[slot][id]=true;++rows;
  }
  if(rows!=480)throw std::runtime_error("row count");
  for(auto&slot:seen)for(bool ok:slot)if(!ok)throw std::runtime_error("missing state");
  std::cout<<"INPUT "<<rows<<" "<<elapsed(start)<<" "<<rss()<<"\n"<<std::flush;
  std::array<std::vector<Pair>,4> pairs;
  for(int block=0;block<4;++block){
    auto&out=pairs[block];out.reserve(3600);
    for(int a=0;a<60;++a)for(int b=0;b<60;++b){
      const auto&A=source[2*block][a],&B=source[2*block+1][b];
      if(A.col&B.col)continue;
      out.push_back({add(A.p,B.p),A.col|B.col,pack2(a,b)});
    }
  }
  std::cout<<"PAIR_SETUP "<<pairs[0].size()<<" "<<pairs[1].size()<<" "
           <<pairs[2].size()<<" "<<pairs[3].size()<<" "<<elapsed(start)<<" "<<rss()<<"\n"<<std::flush;
  std::unordered_multimap<Point,uint32_t,Hash> left;
  left.max_load_factor(0.8f);left.reserve(13000000);
  uint64_t skipped=0;
  for(const auto&A:pairs[0])for(const auto&B:pairs[1]){
    if(A.cols&B.cols){++skipped;continue;}
    left.emplace(add(A.p,B.p),pack4(A.ids,B.ids));
    if((left.size()&16383)==0){
      if(elapsed(start)>cap){std::cout<<"CAP_LEFT "<<left.size()<<" "<<elapsed(start)<<" "<<rss()<<"\n";return 2;}
      if(rss()>rss_cap){std::cout<<"OOM_LEFT "<<left.size()<<" "<<elapsed(start)<<" "<<rss()<<"\n";return 3;}
    }
  }
  std::cout<<"LEFT_DONE "<<left.size()<<" "<<skipped<<" "<<elapsed(start)<<" "<<rss()<<"\n"<<std::flush;
  uint64_t probes=0,matches=0;
  for(const auto&A:pairs[2])for(const auto&B:pairs[3]){
    if(A.cols&B.cols)continue;
    Point right=add(A.p,B.p),need=add(target,neg(right));
    auto range=left.equal_range(need);++probes;
    for(auto it=range.first;it!=range.second;++it){
      ++matches;uint16_t ab=low2(it->second),cd=high2(it->second);
      std::array<int,8> ids={first(ab),second(ab),first(cd),second(cd),
                             first(A.ids),second(A.ids),first(B.ids),second(B.ids)};
      uint32_t used=0;bool distinct=true;
      for(int i=0;i<8;++i){uint32_t c=source[i][ids[i]].col;if(used&c){distinct=false;break;}used|=c;}
      if(!distinct)continue;
      if(!(add(it->first,right)==target))throw std::runtime_error("hit point replay");
      std::cout<<"HIT";for(int id:ids)std::cout<<" "<<id;
      std::cout<<" "<<probes<<" "<<matches<<" "<<elapsed(start)<<" "<<rss()<<"\n"<<std::flush;
      return 0;
    }
    if((probes&16383)==0){
      if(elapsed(start)>cap){std::cout<<"CAP_RIGHT "<<probes<<" "<<elapsed(start)<<" "<<rss()<<"\n";return 2;}
      if(rss()>rss_cap){std::cout<<"OOM_RIGHT "<<probes<<" "<<elapsed(start)<<" "<<rss()<<"\n";return 3;}
    }
  }
  std::cout<<"MISS_COMPLETE "<<probes<<" "<<matches<<" "<<elapsed(start)<<" "<<rss()<<"\n"<<std::flush;
  return 0;
}catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 1;}
