// Exact negation-quotiented partial-sum index on frozen N41 public input.
#define main archived_join_main
#include "../n41_sixpair_shared_target_20261017/join_exact.cpp"
#undef main
#include <algorithm>
#include <vector>
#include <sys/resource.h>

struct Row { Point p; uint32_t ids; };
bool less_point(const Point& a,const Point& b){
    if(a.inf!=b.inf)return a.inf<b.inf;
    if(a.x!=b.x)return a.x<b.x;
    return a.y<b.y;
}
uint64_t rss_bytes(){struct rusage r{};getrusage(RUSAGE_SELF,&r);return uint64_t(r.ru_maxrss);}

int main(int argc,char**argv){
 try{
    if(argc!=2)throw std::runtime_error("usage: sorted_join input.tsv");
    auto start=Clock::now();std::ifstream f(argv[1]);if(!f)throw std::runtime_error("input missing");
    std::string tag;int slots,states;uint64_t tx,ty;f>>tag>>slots>>states>>tx>>ty;
    if(tag!="ECC2K41"||slots!=6||states!=160)throw std::runtime_error("header");
    Point target{tx,ty,false};if(!on_curve(target))throw std::runtime_error("target curve");
    std::array<std::array<State,160>,6> list{};
    std::array<std::array<bool,160>,6> seen{};int count=0;
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
    std::array<std::array<int,160>,6> negid{};
    for(int slot=0;slot<6;++slot)for(int id=0;id<160;++id){
        auto&s=list[slot][id];int other=-1;
        for(int j=0;j<160;++j){auto&t=list[slot][j];
            if(s.a==t.a&&s.b==t.b&&s.sa==(t.sa^1)&&s.sb==(t.sb^1)){
                if(other!=-1)throw std::runtime_error("multiple neg states");
                other=j;
            }
        }
        if(other<0||other==id||!(list[slot][other].point==neg(s.point))||
           list[slot][other].cols!=s.cols)throw std::runtime_error("neg state check");
        negid[slot][id]=other;
    }
    std::cout<<"CHECK_PASS "<<count<<" "<<elapsed(start)<<"\n"<<std::flush;
    std::vector<Row> left;left.reserve(2050000);
    for(int a=0;a<160;++a)for(int b=0;b<160;++b){
        if(a>negid[0][a])continue;
        auto&A=list[0][a];auto&B=list[1][b];if(!disjoint(A.cols,B.cols))continue;
        Point ab=add(A.point,B.point);U128 used=A.cols|B.cols;
        for(int c=0;c<160;++c){auto&C=list[2][c];if(!disjoint(used,C.cols))continue;
            left.push_back({add(ab,C.point),pack(a,b,c)});}
    }
    std::cout<<"LEFT_ENUM "<<left.size()<<" "<<elapsed(start)<<" "<<rss_bytes()<<"\n"<<std::flush;
    std::sort(left.begin(),left.end(),[](const Row& a,const Row& b){return less_point(a.p,b.p);});
    std::cout<<"LEFT_SORT "<<left.size()<<" "<<elapsed(start)<<" "<<rss_bytes()<<"\n"<<std::flush;
    uint64_t unique_points=0,unique_x=0,collision_rows=0,both_y_x=0;
    std::array<uint64_t,5> prefix{};constexpr int depths[5]={8,16,24,32,41};
    uint64_t previous_prefix[5]={};bool first=true;size_t x_group_begin=0;
    for(size_t i=0;i<left.size();++i){
        if(i==0||!(left[i].p==left[i-1].p))++unique_points;
        else ++collision_rows;
        if(i==0||left[i].p.x!=left[i-1].p.x){
            if(i>0){
                if(left[x_group_begin].p.y!=left[i-1].p.y)++both_y_x;
                x_group_begin=i;
            }
            ++unique_x;
            for(int d=0;d<5;++d){
                uint64_t v=left[i].p.x>>(41-depths[d]);
                if(first||v!=previous_prefix[d])++prefix[d];
                previous_prefix[d]=v;
            }
            first=false;
        }
    }
    if(!left.empty()&&left[x_group_begin].p.y!=left.back().p.y)++both_y_x;
    std::cout<<"CENSUS "<<unique_points<<" "<<unique_x<<" "<<collision_rows<<" "
             <<both_y_x;
    for(auto x:prefix)std::cout<<" "<<x;
    std::cout<<" "<<elapsed(start)<<" "<<rss_bytes()<<"\n"<<std::flush;
    constexpr unsigned K=16;std::vector<uint32_t> begin((1u<<K)+1);
    size_t cursor=0;
    for(uint32_t bucket=0;bucket<=(1u<<K);++bucket){
        while(cursor<left.size()&&(left[cursor].p.x>>(41-K))<bucket)++cursor;
        begin[bucket]=uint32_t(cursor);
    }
    uint64_t probes=0,matches=0;
    for(int a=0;a<160;++a)for(int b=0;b<160;++b){
        auto&A=list[3][a];auto&B=list[4][b];if(!disjoint(A.cols,B.cols))continue;
        Point ab=add(A.point,B.point);U128 used=A.cols|B.cols;
        for(int c=0;c<160;++c){auto&C=list[5][c];if(!disjoint(used,C.cols))continue;
            Point right=add(ab,C.point);Point need=add(target,neg(right));
            uint32_t bucket=uint32_t(need.x>>(41-K));
            auto lo=left.begin()+begin[bucket],hi=left.begin()+begin[bucket+1];
            auto it=std::lower_bound(lo,hi,need.x,[](const Row& row,uint64_t x){
                return row.p.x<x;});++probes;
            for(;it!=hi&&it->p.x==need.x;++it){
                bool flipped=false;
                if(it->p==need)flipped=false;
                else if(neg(it->p)==need)flipped=true;
                else continue;
                ++matches;
                auto ids=unpack(it->ids);
                if(flipped)for(int j=0;j<3;++j)ids[j]=negid[j][ids[j]];
                U128 used2=used|C.cols;bool ok=true;
                for(int j=0;j<3;++j){auto&D=list[j][ids[j]];
                    if(!disjoint(used2,D.cols)){ok=false;break;}used2|=D.cols;}
                if(!ok)continue;
                Point actual=flipped?neg(it->p):it->p;
                if(!(add(actual,right)==target))throw std::runtime_error("hit replay");
                std::cout<<"HIT "<<ids[0]<<" "<<ids[1]<<" "<<ids[2]<<" "
                         <<a<<" "<<b<<" "<<c<<" "<<probes<<" "<<matches<<" "
                         <<(flipped?1:0)<<" "
                         <<elapsed(start)<<" "<<rss_bytes()<<"\n"<<std::flush;
                return 0;
            }
        }
    }
    std::cout<<"MISS_COMPLETE "<<probes<<" "<<matches<<" "<<elapsed(start)<<" "
             <<rss_bytes()<<"\n"<<std::flush;
    return 0;
 }catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<"\n";return 2;}
}
