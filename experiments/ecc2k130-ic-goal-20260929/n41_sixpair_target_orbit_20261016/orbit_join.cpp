// Exact N41 six-pair target-conditioned 3+3 join over frozen pair states.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>

using U128 = unsigned __int128;
constexpr uint64_t MOD = (1ULL << 41) | (1ULL << 3) | 1;
using Clock = std::chrono::steady_clock;
uint64_t mul(uint64_t a, uint64_t b) {
    uint64_t r=0;
    while(b){if(b&1)r^=a;b>>=1;a<<=1;if(a&(1ULL<<41))a^=MOD;}
    return r;
}
uint64_t sqr(uint64_t a){return mul(a,a);}
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
    if(p.inf)return q;if(q.inf)return p;
    uint64_t s,x,y;
    if(p.x==q.x){if(p.y!=q.y||!p.x)return {};s=p.x^mul(p.y,inv(p.x));x=sqr(s)^s;y=sqr(p.x)^mul(s^1,x);}
    else{s=mul(p.y^q.y,inv(p.x^q.x));x=sqr(s)^s^p.x^q.x;y=mul(s,p.x^x)^x^p.y;}
    return {x,y,false};
}
bool on_curve(Point p){return p.inf||(sqr(p.y)^mul(p.x,p.y))==(mul(sqr(p.x),p.x)^1);}
struct State{Point point;U128 cols=0;unsigned a=0,b=0,sa=0,sb=0;};
uint32_t pack(int a,int b,int c){return a|(b<<8)|(c<<16);}
std::array<int,3> unpack(uint32_t x){return {int(x&255),int((x>>8)&255),int((x>>16)&255)};}
bool disjoint(U128 a,U128 b){return !(a&b);}
double elapsed(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
int main(int argc,char**argv){
 try{
    if(argc!=2)throw std::runtime_error("usage: join_exact input.tsv");
    auto start=Clock::now();std::ifstream f(argv[1]);if(!f)throw std::runtime_error("input missing");
    std::string tag;int slots,states;uint64_t tx,ty;f>>tag>>slots>>states>>tx>>ty;
    if(tag!="ECC2K41"||slots!=6||states!=160)throw std::runtime_error("header");
    Point target{tx,ty,false};if(!on_curve(target))throw std::runtime_error("target curve");
    std::array<Point,41> targets{};
    targets[0]=target;
    for(int j=1;j<41;++j)targets[j]={sqr(targets[j-1].x),sqr(targets[j-1].y),false};
    if(sqr(targets[40].x)!=target.x||sqr(targets[40].y)!=target.y)
       throw std::runtime_error("target Frobenius period");
    for(int j=0;j<41;++j)if(!on_curve(targets[j]))throw std::runtime_error("orbit curve");
    std::array<std::array<State,160>,6> list{};std::array<std::array<bool,160>,6> seen{};
    int count=0;
    while(f>>tag){
       if(tag!="S")throw std::runtime_error("row tag");
       int slot,id,a,b,sa,sb,ca,cb;uint64_t x,y;
       f>>slot>>id>>a>>b>>sa>>sb>>ca>>cb>>x>>y;
       if(slot<0||slot>=6||id<0||id>=160||seen[slot][id]||a<0||b<0||a>=256||b>=256||
          (a^b)!=56||ca<0||cb<0||ca>=128||cb>=128||ca==cb||sa<0||sa>1||sb<0||sb>1)
          throw std::runtime_error("row field");
       Point p{x,y,false};if(!on_curve(p)||!x)throw std::runtime_error("state curve");
       list[slot][id]={p,(U128(1)<<ca)|(U128(1)<<cb),unsigned(a),unsigned(b),unsigned(sa),unsigned(sb)};
       seen[slot][id]=true;++count;
    }
    if(count!=960)throw std::runtime_error("row count");
    for(auto&slot:seen)for(bool v:slot)if(!v)throw std::runtime_error("missing row");
    std::cout<<"CHECK_PASS "<<count<<" "<<elapsed(start)<<"\n"<<std::flush;
    std::unordered_multimap<Point,uint32_t,Hash> left;
    left.max_load_factor(0.8f);left.reserve(4100000);
    for(int a=0;a<160;++a)for(int b=0;b<160;++b){
       auto& A=list[0][a];auto& B=list[1][b];if(!disjoint(A.cols,B.cols))continue;
       Point ab=add(A.point,B.point);U128 used=A.cols|B.cols;
       for(int c=0;c<160;++c){auto&C=list[2][c];if(!disjoint(used,C.cols))continue;
          left.emplace(add(ab,C.point),pack(a,b,c));}
    }
    std::cout<<"LEFT_DONE "<<left.size()<<" "<<elapsed(start)<<"\n"<<std::flush;
    uint64_t total_probes=0,orbit_hits=0;
    for(int j=0;j<41;++j){
       uint64_t probes=0,matches=0;bool found=false;
       for(int a=0;a<160&&!found;++a)for(int b=0;b<160&&!found;++b){
          auto&A=list[3][a];auto&B=list[4][b];if(!disjoint(A.cols,B.cols))continue;
          Point ab=add(A.point,B.point);U128 used=A.cols|B.cols;
          for(int c=0;c<160&&!found;++c){auto&C=list[5][c];if(!disjoint(used,C.cols))continue;
             Point right=add(ab,C.point);Point need=add(targets[j],neg(right));
             auto range=left.equal_range(need);++probes;
             for(auto it=range.first;it!=range.second;++it){++matches;
                auto ids=unpack(it->second);U128 used2=used|C.cols;bool ok=true;
                for(int i=0;i<3;++i){auto&D=list[i][ids[i]];if(!disjoint(used2,D.cols)){ok=false;break;}used2|=D.cols;}
                if(!ok)continue;
                if(!(add(it->first,right)==targets[j]))throw std::runtime_error("hit replay");
                std::cout<<"ORBIT_HIT "<<j<<" "<<ids[0]<<" "<<ids[1]<<" "<<ids[2]
                         <<" "<<a<<" "<<b<<" "<<c<<" "<<probes<<" "<<matches
                         <<" "<<elapsed(start)<<"\n"<<std::flush;
                found=true;break;
             }
          }
       }
       total_probes+=probes;orbit_hits+=found;
       std::cout<<"ORBIT_DONE "<<j<<" "<<found<<" "<<probes<<" "<<matches
                <<" "<<elapsed(start)<<"\n"<<std::flush;
    }
    std::cout<<"CENSUS_COMPLETE "<<orbit_hits<<" "<<total_probes<<" "<<elapsed(start)<<"\n"<<std::flush;
    return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
