// Exact N41 six-pair target-conditioned 3+3 join over frozen pair states.
#include <array>
#include <chrono>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

using U128 = unsigned __int128;
constexpr uint64_t MOD = (1ULL << 41) | (1ULL << 3) | 1;
using Clock = std::chrono::steady_clock;
uint64_t mul(uint64_t a, uint64_t b) {
    uint64_t r=0;
    while(b){if(b&1)r^=a;b>>=1;a<<=1;if(a&(1ULL<<41))a^=MOD;}
    return r;
}
uint64_t sqr(uint64_t a){return mul(a,a);}
uint64_t frob_direct(uint64_t a){for(int i=0;i<18;++i)a=sqr(a);return a;}
std::array<std::array<uint64_t,256>,6> frob_table(){
    std::array<std::array<uint64_t,256>,6> table{};
    for(int j=0;j<6;++j){
        for(int bit=0;bit<8;++bit){int pos=8*j+bit;if(pos>=41)continue;
            uint64_t v=frob_direct(1ULL<<pos);
            for(int byte=0;byte<256;++byte)if(byte&(1<<bit))table[j][byte]^=v;
        }
    }
    return table;
}
uint64_t frob_fast(uint64_t a,const std::array<std::array<uint64_t,256>,6>&t){
    uint64_t z=0;for(int j=0;j<6;++j)z^=t[j][(a>>(8*j))&255];return z;
}

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
    auto ft=frob_table();
    for(int j=0;j<3;++j)for(int id=0;id<160;++id){
        auto p=list[j][id].point;auto q=list[j+3][id].point;
        if(frob_fast(p.x,ft)!=q.x||frob_fast(p.y,ft)!=q.y)
            throw std::runtime_error("frob state mismatch");
    }
    for(int j=0;j<3;++j)for(int a=0;a<160;++a)for(int b=0;b<160;++b){
        if(disjoint(list[j][a].cols,list[(j+1)%3][b].cols)!=
           disjoint(list[j+3][a].cols,list[3+(j+1)%3][b].cols))
            throw std::runtime_error("frob column-disjoint mismatch");
    }
    std::cout<<"CHECK_PASS "<<count<<" "<<elapsed(start)<<"\n"<<std::flush;
    std::unordered_multimap<Point,uint32_t,Hash> left;
    using Entry = std::unordered_multimap<Point,uint32_t,Hash>::value_type;
    std::vector<const Entry*> triple_refs;triple_refs.reserve(4100000);
    left.max_load_factor(0.8f);left.reserve(4100000);
    for(int a=0;a<160;++a)for(int b=0;b<160;++b){
       auto& A=list[0][a];auto& B=list[1][b];if(!disjoint(A.cols,B.cols))continue;
       Point ab=add(A.point,B.point);U128 used=A.cols|B.cols;
       for(int c=0;c<160;++c){auto&C=list[2][c];if(!disjoint(used,C.cols))continue;
          Point s=add(ab,C.point);uint32_t ids=pack(a,b,c);
          auto it=left.emplace(s,ids);triple_refs.push_back(&*it);}
    }
    std::cout<<"LEFT_DONE "<<left.size()<<" "<<elapsed(start)<<"\n"<<std::flush;
    uint64_t probes=0,matches=0;
    for(const Entry* tr:triple_refs){
       auto ids=unpack(tr->second);int a=ids[0],b=ids[1],c=ids[2];
       Point right=tr->first;
       if(!right.inf){right.x=frob_fast(right.x,ft);right.y=frob_fast(right.y,ft);}
       Point need=add(target,neg(right));
       auto range=left.equal_range(need);++probes;
       for(auto it=range.first;it!=range.second;++it){++matches;
          auto l=unpack(it->second);U128 used2=list[3][a].cols|list[4][b].cols|list[5][c].cols;
          bool ok=true;
          for(int i=0;i<3;++i){auto&D=list[i][l[i]];if(!disjoint(used2,D.cols)){ok=false;break;}used2|=D.cols;}
          if(!ok)continue;
          if(!(add(it->first,right)==target))throw std::runtime_error("hit replay");
          std::cout<<"HIT "<<l[0]<<" "<<l[1]<<" "<<l[2]<<" "<<a<<" "<<b<<" "<<c
                   <<" "<<probes<<" "<<matches<<" "<<elapsed(start)<<"\n"<<std::flush;
          return 0;
       }
    }
    std::cout<<"MISS_COMPLETE "<<probes<<" "<<matches<<" "<<elapsed(start)<<"\n"<<std::flush;
    return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
