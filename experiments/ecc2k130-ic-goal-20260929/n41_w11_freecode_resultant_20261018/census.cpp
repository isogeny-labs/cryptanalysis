// Exhaustive native evaluation of the frozen 13-term free-code resultant.
#define main inherited_join_main
#include "../n41_w11_fivepair_native_join_20261018/join.cpp"
#undef main
#include <algorithm>
#include <map>
#include <set>
#include <sys/resource.h>

struct ProductRow { int code; uint64_t p1,p2; std::array<uint64_t,5> a,b; };
struct Term { int i,j; uint64_t value; };

int main(int argc,char**argv) {
    try {
        if (argc!=4) throw std::runtime_error("usage: census resultant_input.tsv join_input.tsv output.json");
        auto started=std::chrono::steady_clock::now();
        std::ifstream source(argv[1]);
        if (!source) throw std::runtime_error("resultant input missing");
        std::string tag; int targets,codes,term_count;
        source>>tag>>targets>>codes>>term_count;
        if (tag!="FREECODE"||targets!=25||codes!=281||term_count!=13)
            throw std::runtime_error("resultant input header");
        std::vector<ProductRow> products;
        products.reserve(codes);
        std::set<int> valid;
        for (int k=0;k<codes;k++) {
            ProductRow row{};
            source>>tag>>row.code>>row.p1>>row.p2;
            if (tag!="P"||row.code<0||row.code>=1024||!valid.insert(row.code).second)
                throw std::runtime_error("product row");
            row.a[0]=row.b[0]=1;
            for (int i=1;i<=4;i++) {
                row.a[i]=mul(row.a[i-1],row.p1);
                row.b[i]=mul(row.b[i-1],row.p2);
            }
            products.push_back(row);
        }
        if (!valid.contains(253)||!valid.contains(63)) throw std::runtime_error("positive codes missing");

        std::ifstream states_in(argv[2]);
        if (!states_in) throw std::runtime_error("state input missing");
        int slots,state_count,raw_targets;
        states_in>>tag>>slots>>state_count>>raw_targets;
        if (tag!="W11FIVE"||slots!=5||state_count!=1124||raw_targets!=1)
            throw std::runtime_error("state input header");
        std::array<std::array<std::array<State,4>,1024>,2> states{};
        std::array<std::array<std::array<bool,4>,1024>,2> seen{};
        int state_rows=0;
        while (states_in>>tag) {
            if (tag=="T") {
                int id; uint64_t x,y; states_in>>id>>x>>y;
            } else if (tag=="S") {
                int slot,sid,code,branch; uint64_t ma,mb,ca,cb,x,y;
                states_in>>slot>>sid>>code>>branch>>ma>>mb>>ca>>cb>>x>>y;
                if (slot<0||slot>=5||sid<0||sid>=1124||code<0||code>=1024||
                    branch<0||branch>=4||branch!=sid%4)
                    throw std::runtime_error("state record");
                if (slot>=3) {
                    if (seen[slot-3][code][branch]) throw std::runtime_error("duplicate state");
                    Point point{x,y,false};
                    if (!on_curve(point)) throw std::runtime_error("state off curve");
                    states[slot-3][code][branch]={point,uint16_t(code),ca,cb};
                    seen[slot-3][code][branch]=true;
                    ++state_rows;
                }
            } else if (tag=="C") {
                uint64_t v[6]; for (auto& entry:v) states_in>>entry;
            } else throw std::runtime_error("unexpected state record");
        }
        if (state_rows!=2*1124) throw std::runtime_error("state row count");
        for (int code:valid) for (int slot=0;slot<2;slot++) for (bool present:seen[slot][code])
            if (!present) throw std::runtime_error("missing signed state");

        std::ofstream output(argv[3]);
        if (!output) throw std::runtime_error("output open");
        output<<"{\"status\":\"COMPLETE_N41_W11_FREECODE_RESULTANT_CENSUS\","
              "\"candidate_id\":null,\"curve_id\":\"EC1N41Ckb1h7d5e80d3c4d0\","
              "\"source_codes\":"<<codes<<",\"target_count\":"<<targets<<",\"rows\":[";
        for (int k=0;k<targets;k++) {
            int index;uint64_t x,y;
            source>>tag>>index>>x>>y;
            if (tag!="T"||index!=k||x>=(1ULL<<41)||y>=(1ULL<<41))
                throw std::runtime_error("target row");
            Point target{x,y,false};
            if (!on_curve(target)) throw std::runtime_error("target off curve");
            std::array<std::array<uint64_t,5>,5> coeff{};
            std::set<std::pair<int,int>> exponents;
            for (int n=0;n<term_count;n++) {
                int row_index,i,j;uint64_t value;
                source>>tag>>row_index>>i>>j>>value;
                if (tag!="C"||row_index!=k||i<0||i>4||j<0||j>4||
                    !value||value>=(1ULL<<41)||!exponents.insert({i,j}).second)
                    throw std::runtime_error("coefficient row");
                coeff[i][j]=value;
            }
            auto query_start=std::chrono::steady_clock::now();
            int zeros=0,distinct_zeros=0,compatible_zeros=0,exact_pairs=0;
            std::vector<std::pair<int,int>> zero_pairs;
            for (const auto& left:products) {
                std::array<uint64_t,5> weighted{};
                for (int j=0;j<=4;j++) for (int i=0;i<=4;i++)
                    if (coeff[i][j]) weighted[j]^=mul(coeff[i][j],left.a[i]);
                for (const auto& right:products) {
                    uint64_t value=0;
                    for (int j=0;j<=4;j++) if (weighted[j]) value^=mul(weighted[j],right.b[j]);
                    if (value) continue;
                    ++zeros;
                    zero_pairs.push_back({left.code,right.code});
                    if (left.code==right.code) continue;
                    ++distinct_zeros;
                    bool compatible_pair=false, exact_pair=false;
                    for (const State& a:states[0][left.code])
                        for (const State& b:states[1][right.code])
                            if (compatible(a,b)) {
                                compatible_pair=true;
                                if (add(a.p,b.p)==target) exact_pair=true;
                            }
                    compatible_zeros+=compatible_pair;
                    exact_pairs+=exact_pair;
                }
            }
            if (k==0 && (std::find(zero_pairs.begin(),zero_pairs.end(),
                                   std::pair<int,int>{253,63})==zero_pairs.end()||exact_pairs<1))
                throw std::runtime_error("positive witness absent");
            output<<(k?",":"")<<"{\"index\":"<<k<<",\"target_point\":["<<x<<","<<y<<"]"
                  <<",\"raw_zero_code_pairs\":"<<zeros
                  <<",\"distinct_code_zero_pairs\":"<<distinct_zeros
                  <<",\"folded_compatible_zero_pairs\":"<<compatible_zeros
                  <<",\"direct_group_hit_code_pairs\":"<<exact_pairs
                  <<",\"zero_pairs\":[";
            for (size_t i=0;i<zero_pairs.size();i++)
                output<<(i?",":"")<<"["<<zero_pairs[i].first<<","<<zero_pairs[i].second<<"]";
            output<<"],\"query_seconds\":"<<elapsed(query_start)<<"}";
        }
        std::string trailing;
        if (source>>trailing) throw std::runtime_error("trailing input");
        struct rusage usage{};getrusage(RUSAGE_SELF,&usage);
        output<<"],\"total_wall_seconds\":"<<elapsed(started)
              <<",\"self_maxrss_raw\":"<<usage.ru_maxrss<<"}\n";
        std::cout<<"COMPLETE_N41_W11_FREECODE_RESULTANT_CENSUS\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr<<"ERROR "<<error.what()<<"\n";
        return 2;
    }
}
