// Exact x-prefix occupancy for both sides of the frozen N41 six-pair join.
#define main archived_join_main
#include "../n41_sixpair_shared_target_20261017/join_exact.cpp"
#undef main
#include <vector>
#include <unordered_set>
#include <sstream>

struct PrefixSet {
    int bits;
    std::vector<uint64_t> bitmap;
    std::unordered_set<uint32_t> sparse;
    uint64_t distinct=0;
    explicit PrefixSet(int k):bits(k) {
        if(k<=28) bitmap.resize((uint64_t(1)<<k)/64);
    }
    uint32_t key(uint64_t x) const {return uint32_t(x>>(41-bits));}
    bool has(uint32_t key) const {
        if(!bitmap.empty()) return (bitmap[key>>6]>>(key&63))&1;
        return sparse.count(key)>0;
    }
    bool put(uint32_t key) {
        if(!bitmap.empty()) {
            uint64_t &cell=bitmap[key>>6],bit=uint64_t(1)<<(key&63);
            if(cell&bit)return false;
            cell|=bit;
        } else if(!sparse.insert(key).second) return false;
        ++distinct;return true;
    }
};

int main(int argc,char **argv) {
    try {
        if(argc!=2)throw std::runtime_error("usage: prefix frozen_join_input.tsv");
        auto begin=Clock::now();
        std::ifstream f(argv[1]);
        std::string tag;int slots,states;uint64_t tx,ty;
        f>>tag>>slots>>states>>tx>>ty;
        if(!f||tag!="ECC2K41"||slots!=6||states!=160)throw std::runtime_error("header");
        Point target{tx,ty,false};
        if(!on_curve(target))throw std::runtime_error("target curve");
        std::array<std::array<State,160>,6> source{};
        std::array<std::array<bool,160>,6> seen{};
        int records=0;
        while(f>>tag) {
            int slot,id,a,b,sa,sb,ca,cb;uint64_t x,y;
            f>>slot>>id>>a>>b>>sa>>sb>>ca>>cb>>x>>y;
            if(!f||tag!="S"||slot<0||slot>=6||id<0||id>=160||seen[slot][id]||
               a<0||b<0||a>=256||b>=256||(a^b)!=56||ca<0||cb<0||
               ca>=128||cb>=128||ca==cb||sa<0||sa>1||sb<0||sb>1)
                throw std::runtime_error("source row");
            Point p{x,y,false};if(!on_curve(p)||!x)throw std::runtime_error("curve row");
            source[slot][id]={p,(U128(1)<<ca)|(U128(1)<<cb),unsigned(a),unsigned(b),unsigned(sa),unsigned(sb)};
            seen[slot][id]=true;++records;
        }
        if(records!=960)throw std::runtime_error("row count");
        for(auto &slot:seen)for(bool v:slot)if(!v)throw std::runtime_error("missing row");
        const std::array<int,7> widths{8,12,16,20,24,28,32};
        std::vector<PrefixSet> left,right;
        for(int k:widths){left.emplace_back(k);right.emplace_back(k);}
        std::array<uint64_t,7> overlapping{};
        uint64_t triples[2]={};
        uint64_t exceptional[2]={};
        // A sum in slots 3..5 contributes the target-conditioned need Q - R.
        for(int side=0;side<2;++side) {
            int offset=side*3;
            for(int a=0;a<160;++a)for(int b=0;b<160;++b) {
                const auto &A=source[offset][a],&B=source[offset+1][b];
                if(!disjoint(A.cols,B.cols))continue;
                Point ab=add(A.point,B.point);U128 used=A.cols|B.cols;
                for(int c=0;c<160;++c) {
                    const auto &C=source[offset+2][c];
                    if(!disjoint(used,C.cols))continue;
                    Point sum=add(ab,C.point);
                    if(side)sum=add(target,neg(sum));
                    ++triples[side];
                    if(sum.inf){++exceptional[side];continue;}
                    for(size_t j=0;j<widths.size();++j) {
                        auto &s=side?right[j]:left[j];
                        uint32_t key=s.key(sum.x);
                        if(side && !right[j].has(key) && left[j].has(key))++overlapping[j];
                        s.put(key);
                    }
                }
            }
        }
        std::cout<<"{\"status\":\"COMPLETE\",\"records\":"<<records
                 <<",\"left_triples\":"<<triples[0]<<",\"right_triples\":"<<triples[1]
                 <<",\"left_infinity\":"<<exceptional[0]
                 <<",\"right_need_infinity\":"<<exceptional[1]
                 <<",\"elapsed_seconds\":"<<elapsed(begin)<<",\"prefixes\":[";
        for(size_t j=0;j<widths.size();++j) {
            if(j)std::cout<<",";
            std::cout<<"{\"bits\":"<<widths[j]<<",\"left_distinct\":"<<left[j].distinct
                     <<",\"right_distinct\":"<<right[j].distinct
                     <<",\"intersection\":"<<overlapping[j]<<"}";
        }
        std::cout<<"]}"<<std::endl;
        return 0;
    } catch(const std::exception &e) {
        std::cerr<<"ERROR "<<e.what()<<std::endl;return 2;
    }
}
