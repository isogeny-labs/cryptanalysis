#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using U128=unsigned __int128;
using Clock=std::chrono::steady_clock;
constexpr uint64_t MOD=(1ULL<<41)|(1ULL<<3)|1;
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
struct Point{uint64_t x=0,y=0;bool inf=true;bool operator==(const Point& q)const{return inf==q.inf&&(inf||(x==q.x&&y==q.y));}};
struct Hash{size_t operator()(const Point& p)const{if(p.inf)return 0x9e3779b97f4a7c15ULL;uint64_t z=p.x^(p.y<<17)^(p.y>>24);z^=z>>30;z*=0xbf58476d1ce4e5b9ULL;z^=z>>27;z*=0x94d049bb133111ebULL;return static_cast<size_t>(z^(z>>31));}};
Point neg(Point p){if(!p.inf)p.y^=p.x;return p;}
Point add(Point p,Point q){
    if(p.inf)return q;if(q.inf)return p;uint64_t s,x,y;
    if(p.x==q.x){if(p.y!=q.y||!p.x)return {};s=p.x^mul(p.y,inv(p.x));x=sq(s)^s;y=sq(p.x)^mul(s^1,x);}
    else{s=mul(p.y^q.y,inv(p.x^q.x));x=sq(s)^s^p.x^q.x;y=mul(s,p.x^x)^x^p.y;}
    return {x,y,false};
}
bool on_curve(Point p){return p.inf||(sq(p.y)^mul(p.x,p.y))==(mul(sq(p.x),p.x)^1);}
struct State{Point point;U128 cols=0;bool seen=false;};
struct Two{int a,b;Point point;};
bool disjoint(U128 a,U128 b){return !(a&b);}
double secs(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
int main(int argc,char**argv){
 try{
  if(argc!=2)throw std::runtime_error("usage: native input.tsv");
  auto start=Clock::now();std::ifstream f(argv[1]);if(!f)throw std::runtime_error("input missing");
  std::string tag;int n;uint64_t tx,ty;f>>tag>>n>>tx>>ty;
  if(tag!="N41_4"||n!=160)throw std::runtime_error("header");
  Point target{tx,ty,false};if(!on_curve(target))throw std::runtime_error("target curve");
  std::array<std::array<State,160>,4> states{};
  std::array<State,3> suffix{};
  std::array<Point,160> residual{};std::array<bool,160> residual_seen{};
  std::vector<std::pair<int,int>> cases;
  int rows=0;
  while(f>>tag){
   if(tag=="S"){
    int axis,id,ca,cb;uint64_t x,y;f>>axis>>id>>ca>>cb>>x>>y;
    if(axis<0||axis>=7||id<0||id>=160||ca<0||cb<0||ca==cb||ca>=128||cb>=128)throw std::runtime_error("state row");
    Point p{x,y,false};if(!on_curve(p))throw std::runtime_error("state curve");
    State s{p,(U128(1)<<ca)|(U128(1)<<cb),true};
    if(axis<4){if(states[axis][id].seen)throw std::runtime_error("duplicate state");states[axis][id]=s;}
    else{if(suffix[axis-4].seen)throw std::runtime_error("duplicate suffix");suffix[axis-4]=s;}
    rows++;
   }else if(tag=="T"){
    int id;uint64_t x,y;f>>id>>x>>y;
    if(id<0||id>=160||residual_seen[id])throw std::runtime_error("target row");
    residual[id]={x,y,false};if(!on_curve(residual[id]))throw std::runtime_error("residual curve");
    residual_seen[id]=true;
   }else if(tag=="C"){
    int a,b;f>>a>>b;if(a<0||a>=40||b<0||b>=40)throw std::runtime_error("case row");cases.emplace_back(a,b);
   }else throw std::runtime_error("unknown tag");
  }
  if(rows!=643||cases.size()!=1554)throw std::runtime_error("row counts");
  for(auto&axis:states)for(auto&s:axis)if(!s.seen)throw std::runtime_error("state missing");
  for(auto&s:suffix)if(!s.seen)throw std::runtime_error("suffix missing");
  for(bool b:residual_seen)if(!b)throw std::runtime_error("residual missing");
  std::array<std::array<U128,40>,4> code_cols{};
  for(int axis=0;axis<4;++axis)for(int code=0;code<40;++code){
    code_cols[axis][code]=states[axis][4*code].cols;
    for(int k=1;k<4;++k)if(code_cols[axis][code]!=states[axis][4*code+k].cols)throw std::runtime_error("column sign mismatch");
  }
  U128 suffix_cols=suffix[0].cols|suffix[1].cols|suffix[2].cols;
  if(!disjoint(suffix[0].cols,suffix[1].cols)||!disjoint(suffix[0].cols|suffix[1].cols,suffix[2].cols))throw std::runtime_error("suffix collision");
  std::array<uint64_t,40*40*40> allowed{};
  uint64_t eligible_quads=0;
  for(int a=0;a<40;++a)for(int b=0;b<40;++b)for(int c=0;c<40;++c){
    U128 ca=code_cols[0][a],cb=code_cols[1][b],cc=code_cols[2][c];
    if(!disjoint(ca,suffix_cols)||!disjoint(cb,suffix_cols)||!disjoint(cc,suffix_cols)||
       !disjoint(ca,cb)||!disjoint(ca,cc)||!disjoint(cb,cc))continue;
    U128 used=ca|cb|cc|suffix_cols;uint64_t mask=0;
    for(int d=0;d<40;++d)if(disjoint(used,code_cols[3][d]))mask|=1ULL<<d;
    allowed[(a*40+b)*40+c]=mask;eligible_quads+=__builtin_popcountll(mask);
  }
  if(eligible_quads!=1386816)throw std::runtime_error("eligible quad count");
  std::unordered_map<Point,std::vector<int>,Hash> target_map;target_map.reserve(320);
  for(int id=0;id<160;++id)target_map[residual[id]].push_back(id);
  auto query_start=Clock::now();uint64_t triples=0,quads=0,two_sums=0,three_sums=0,matches=0;
  int witness[7]={97,151,42,0,14,109,51};bool witness_seen=false;
  for(auto [a,b]:cases){
    std::array<Two,16> pair{};int pos=0;
    for(int i=4*a;i<4*a+4;++i)for(int j=4*b;j<4*b+4;++j)
       pair[pos++]={i,j,add(states[0][i].point,states[1][j].point)};
    two_sums+=16;
    for(int c=0;c<40;++c){uint64_t mask=allowed[(a*40+b)*40+c];if(!mask)continue;
      ++triples;quads+=__builtin_popcountll(mask);
      for(int k=4*c;k<4*c+4;++k)for(auto &p:pair){
        Point total=add(p.point,states[2][k].point);++three_sums;
        auto it=target_map.find(total);if(it==target_map.end())continue;
        for(int id:it->second){int code=id/4;if(!(mask&(1ULL<<code)))continue;
          U128 used=states[0][p.a].cols|states[1][p.b].cols|states[2][k].cols|
            states[3][id].cols|suffix_cols;
          if(__builtin_popcountll(static_cast<uint64_t>(used))+__builtin_popcountll(static_cast<uint64_t>(used>>64))!=14)
             throw std::runtime_error("column collision");
          Point check=add(total,states[3][id].point);
          for(auto&s:suffix)check=add(check,s.point);
          if(!(check==target))throw std::runtime_error("hit sum");
          if(p.a==witness[0]&&p.b==witness[1]&&k==witness[2]&&id==witness[3])witness_seen=true;
          ++matches;
        }
      }
    }
  }
  if(triples!=42432||quads!=1386816||two_sums!=24864||three_sums!=2715648||matches!=1||!witness_seen)
     throw std::runtime_error("frozen census mismatch");
  std::cout<<"{\"status\":\"PASS_N41_NATIVE_FOUR_AXIS\",\"eligible_triples\":"<<triples
           <<",\"eligible_quads\":"<<quads<<",\"first_two_state_sums\":"<<two_sums
           <<",\"first_three_state_sums\":"<<three_sums<<",\"matches\":"<<matches
           <<",\"witness\":[97,151,42,0,14,109,51],\"setup_s\":"
           <<std::fixed<<secs(start)-secs(query_start)<<",\"traversal_s\":"<<secs(query_start)
           <<",\"wall_s\":"<<secs(start)<<"}\n";
  return 0;
 }catch(std::exception const& e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
