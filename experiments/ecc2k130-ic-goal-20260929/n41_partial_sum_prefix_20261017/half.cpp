// First twenty canonical pair codes in every slot; exact join and x-prefix census.
#define main archived_join_main
#include "../n41_sixpair_shared_target_20261017/join_exact.cpp"
#undef main
#include <vector>
#include <unordered_set>

struct Set {
    int bits;
    std::vector<uint64_t> map;
    std::unordered_set<uint32_t> sparse;
    uint64_t size=0;
    explicit Set(int n):bits(n) {if(n<=28)map.resize((uint64_t(1)<<n)/64);}
    uint32_t key(uint64_t x)const{return uint32_t(x>>(41-bits));}
    bool has(uint32_t k)const {
        return !map.empty()?bool((map[k>>6]>>(k&63))&1):sparse.count(k)!=0;
    }
    bool insert(uint32_t k) {
        if(!map.empty()){
            uint64_t &word=map[k>>6],bit=uint64_t(1)<<(k&63);
            if(word&bit)return false;
            word|=bit;
        }else if(!sparse.insert(k).second)return false;
        ++size;return true;
    }
};

int main(int argc,char **argv) {
  try {
    if(argc!=2)throw std::runtime_error("usage: half join_input.tsv");
    auto start=Clock::now();std::ifstream f(argv[1]);
    std::string tag;int slots,states;uint64_t tx,ty;
    f>>tag>>slots>>states>>tx>>ty;
    if(!f||tag!="ECC2K41"||slots!=6||states!=160)throw std::runtime_error("header");
    Point target{tx,ty,false};if(!on_curve(target))throw std::runtime_error("target curve");
    std::array<std::array<State,160>,6> list{};
    std::array<std::array<bool,160>,6> seen{};
    int count=0;
    while(f>>tag){
        int slot,id,a,b,sa,sb,ca,cb;uint64_t x,y;
        f>>slot>>id>>a>>b>>sa>>sb>>ca>>cb>>x>>y;
        if(!f||tag!="S"||slot<0||slot>=6||id<0||id>=160||seen[slot][id]||
           a<0||b<0||a>=256||b>=256||(a^b)!=56||ca<0||cb<0||
           ca>=128||cb>=128||ca==cb||sa<0||sa>1||sb<0||sb>1)
            throw std::runtime_error("source row");
        Point p{x,y,false};if(!on_curve(p)||!x)throw std::runtime_error("curve row");
        list[slot][id]={p,(U128(1)<<ca)|(U128(1)<<cb),unsigned(a),unsigned(b),unsigned(sa),unsigned(sb)};
        seen[slot][id]=true;++count;
    }
    if(count!=960)throw std::runtime_error("row count");
    for(auto &slot:seen)for(bool v:slot)if(!v)throw std::runtime_error("missing row");
    std::array<int,7> widths{8,12,16,20,24,28,32};
    std::vector<Set> left,right;
    for(int n:widths){left.emplace_back(n);right.emplace_back(n);}
    std::array<uint64_t,7> both{};
    std::unordered_multimap<Point,uint32_t,Hash> index;
    index.max_load_factor(0.8f);index.reserve(600000);
    uint64_t triples[2]={},infinity[2]={},coordinate_hits=0,relations=0;
    std::array<int,6> first_hit{};
    for(int side=0;side<2;++side){
      int slot=3*side;
      for(int a=0;a<80;++a)for(int b=0;b<80;++b){
        auto &A=list[slot][a],&B=list[slot+1][b];
        if(!disjoint(A.cols,B.cols))continue;
        Point ab=add(A.point,B.point);U128 used=A.cols|B.cols;
        for(int c=0;c<80;++c){
          auto &C=list[slot+2][c];if(!disjoint(used,C.cols))continue;
          Point subtotal=add(ab,C.point);
          Point point=side?add(target,neg(subtotal)):subtotal;
          ++triples[side];
          if(!side)index.emplace(point,pack(a,b,c));
          else {
            auto range=index.equal_range(point);
            for(auto it=range.first;it!=range.second;++it){
              ++coordinate_hits;
              U128 all=used|C.cols;auto ids=unpack(it->second);bool valid=true;
              for(int j=0;j<3;++j){
                auto &L=list[j][ids[j]];
                if(!disjoint(all,L.cols)){valid=false;break;}
                all|=L.cols;
              }
              if(valid){
                ++relations;
                if(relations==1)first_hit={ids[0],ids[1],ids[2],a,b,c};
              }
            }
          }
          if(point.inf){++infinity[side];continue;}
          for(size_t j=0;j<widths.size();++j){
            auto &set=side?right[j]:left[j];uint32_t key=set.key(point.x);
            if(side&&!set.has(key)&&left[j].has(key))++both[j];
            set.insert(key);
          }
        }
      }
    }
    std::cout<<"{\"status\":\"COMPLETE\",\"panel\":\"code_ordinal_0_to_19\""
             <<",\"left_triples\":"<<triples[0]<<",\"right_triples\":"<<triples[1]
             <<",\"left_infinity\":"<<infinity[0]<<",\"right_need_infinity\":"<<infinity[1]
             <<",\"coordinate_hits\":"<<coordinate_hits<<",\"relations\":"<<relations
             <<",\"first_hit\":[";
    for(size_t i=0;i<first_hit.size();++i){if(i)std::cout<<",";std::cout<<first_hit[i];}
    std::cout<<"],\"elapsed_seconds\":"<<elapsed(start)<<",\"prefixes\":[";
    for(size_t j=0;j<widths.size();++j){
        if(j)std::cout<<",";
        std::cout<<"{\"bits\":"<<widths[j]<<",\"left_distinct\":"<<left[j].size
                 <<",\"right_distinct\":"<<right[j].size<<",\"intersection\":"<<both[j]<<"}";
    }
    std::cout<<"]}"<<std::endl;
    return 0;
  }catch(const std::exception &e){std::cerr<<"ERROR "<<e.what()<<std::endl;return 2;}
}
