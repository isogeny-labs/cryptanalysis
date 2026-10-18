// Additive v2: every zero-length report requires golden start-point replay.
// Native replay/ingestion control. Research arithmetic uses the pinned
// independent fpga/model implementation through the hostcheck bridge.
#include "hostcheck.h"
#include <algorithm>
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace ec2k_gpu;
using Record = std::array<unsigned char, 32>;
static void need(bool b, const char *s) { if (!b) throw std::runtime_error(s); }
template<class T> static std::vector<T> read(const std::string &p) {
    std::ifstream f(p, std::ios::binary | std::ios::ate);
    need(bool(f), "open input failed");
    const auto n=f.tellg(); need(n>=0 && size_t(n)%sizeof(T)==0, "partial input record");
    need(size_t(n)<size_t(2)*1024*1024*1024, "input exceeds bounded reader");
    std::vector<T> v(size_t(n)/sizeof(T)); f.seekg(0);
    if(n) f.read(reinterpret_cast<char *>(v.data()), n);
    need(bool(f), "read failed"); return v;
}
template<class T> static void write(const std::string &p, const std::vector<T> &v) {
    std::ofstream f(p, std::ios::binary | std::ios::trunc);
    f.write(reinterpret_cast<const char *>(v.data()), v.size()*sizeof(T)); need(bool(f), "write failed");
}
struct Header {
    char magic[8]; uint32_t version,m,threads,batch,lanes,runId; uint64_t iterBase;
};
struct Binding { int32_t dpWeight; uint32_t fieldWords; uint64_t maxIters,px[3],qx[3]; };
static_assert(sizeof(Header)==40 && sizeof(Binding)==64 && sizeof(DpRecord)==64);
static Header header(const std::string &p, unsigned run, int weight) {
    std::ifstream f(p, std::ios::binary); Header h{}; Binding b{};
    f.read(reinterpret_cast<char *>(&h), sizeof h); f.read(reinterpret_cast<char *>(&b), sizeof b);
    need(bool(f), "short checkpoint binding");
    need(!memcmp(h.magic,"ECC2K130",8) && h.version==0x100 && h.m==131, "wrong checkpoint format");
    need(h.runId==run && h.threads>0 && h.threads%256==0 && h.batch==16 && h.lanes==1,
         "wrong checkpoint geometry/run");
    need(b.dpWeight==weight && b.maxIters==(1ull<<32), "wrong checkpoint cutoff/restart");
    ec2k_pt p0,q0; challengePoints(&p0,&q0);
    for(int i=0;i<3;i++) need(b.px[i]==p0.x.w[i] && b.qx[i]==q0.x.w[i], "wrong public challenge points");
    need(h.iterBase>0 && b.fieldWords>0, "empty checkpoint work"); return h;
}
static uint64_t count(const std::string &s,const std::string &key) {
    const std::string marker="\""+key+"\":"; const auto i=s.find(marker);
    need(i!=std::string::npos,"summary lacks required counter");
    const auto first=i+marker.size(); need(first<s.size() && s[first]>='0' && s[first]<='9',"invalid summary counter");
    return std::stoull(s.substr(first));
}
static std::string jsonLine(const std::string &path) {
    std::ifstream f(path); need(bool(f),"cannot read JSON result");
    std::string line,last;
    while(std::getline(f,line)) if(!line.empty() && line.front()=='{') last=line;
    need(last.find("\"status\":\"ok\"")!=std::string::npos,"JSON result status is not ok"); return last;
}
static void check(const std::string &p32,const std::string &p64,unsigned run,int weight,
                  unsigned replayMax,unsigned long long stepMax) {
    const auto a=read<Record>(p32); const auto b=read<DpRecord>(p64);
    need(!a.empty() && a.size()==b.size(), "empty corpus or unequal paired corpus sizes");
    HostWalk walk; ec2k_pt p,q; challengePoints(&p,&q); walk.build(p,q);
    unsigned replayed=0; size_t zeros=0, zeroReplayed=0; uint64_t maxSteps=0;
    for(size_t i=0;i<a.size();i++) {
        ec2k_record decoded{};
        need(ec2k_record_decode(&decoded,a[i].data()), "malformed campaign record");
        need((b[i].seed>>48)==run && decoded.seed==b[i].seed, "wrong seed namespace");
        need(b[i].iters<=(1ull<<32), "invalid trail length");
        need(!(b[i].x[2]&~7ull) && !(b[i].y[2]&~7ull), "noncanonical coordinates");
        ec2k_pt pt{feOf(b[i].x),feOf(b[i].y),0};
        need(ec2k_on_curve(&pt), "point off public curve");
        need(int(ec2k_fe_weight(&pt.x))<=weight, "point outside DP cutoff");
        Record expected{}; campaignRecord(expected.data(),b[i]);
        need(expected==a[i], "DP32/DP64 orbit encoding mismatch");
        if(b[i].iters==0) {
            ++zeros;
            need(rewalk(walk,b[i],nullptr), "zero-length golden-model start-point mismatch");
            ++zeroReplayed;
        } else if(replayed<replayMax && b[i].iters<=stepMax) {
            need(rewalk(walk,b[i],nullptr), "golden-model trail replay mismatch"); ++replayed;
        }
        maxSteps=std::max<uint64_t>(maxSteps,b[i].iters);
    }
    std::cout<<"{\"status\":\"ok\",\"records\":"<<a.size()
             <<",\"independent_curve_weight_seed_encoding_checks\":"<<a.size()
             <<",\"zero_length_records\":"<<zeros<<",\"zero_length_golden_replayed\":"<<zeroReplayed
             <<",\"positive_trails_replayed\":"<<replayed
             <<",\"golden_trails_replayed\":"<<replayed+zeroReplayed<<",\"trails_not_replayed\":"<<a.size()-replayed-zeroReplayed
             <<",\"max_trail_steps\":"<<maxSteps<<",\"run_id\":"<<run
             <<",\"dp_weight\":"<<weight<<"}\n";
}
int main(int argc,char **argv) {
    try {
        need(argc>=2,"missing command"); std::string cmd=argv[1];
        if(cmd=="header" || cmd=="iter") {
            need(argc==5,"header/iter path runid weight"); auto h=header(argv[2],std::stoul(argv[3]),std::stoi(argv[4]));
            if(cmd=="iter") std::cout<<h.iterBase<<"\n";
            else std::cout<<"{\"status\":\"ok\",\"iter_base\":"<<h.iterBase
                         <<",\"threads\":"<<h.threads<<",\"batch\":"<<h.batch
                         <<",\"run_id\":"<<h.runId<<",\"cumulative_lane_steps\":"
                         <<h.iterBase*uint64_t(h.threads)*h.batch<<"}\n";
        } else if(cmd=="compare") {
            need(argc==4,"compare first32 second32"); auto a=read<Record>(argv[2]), b=read<Record>(argv[3]);
            std::sort(a.begin(),a.end()); std::sort(b.begin(),b.end());
            need(!a.empty() && a==b,"checkpoint/restart multiset mismatch or empty corpus");
            std::cout<<"{\"status\":\"ok\",\"sorted_records_identical\":true,\"records\":"<<a.size()<<"}\n";
        } else if(cmd=="advance") {
            need(argc==6,"advance first_checkpoint second_checkpoint runid weight");
            auto a=header(argv[2],std::stoul(argv[4]),std::stoi(argv[5]));
            auto b=header(argv[3],std::stoul(argv[4]),std::stoi(argv[5]));
            need(a.threads==b.threads && b.iterBase>a.iterBase,"checkpoint work did not advance");
            std::cout<<"{\"status\":\"ok\",\"checkpoint_advanced\":true,\"first_step\":"<<a.iterBase
                     <<",\"second_step\":"<<b.iterBase<<"}\n";
        } else if(cmd=="merge-check") {
            need(argc==4,"merge-check single_json double_json");
            const auto a=jsonLine(argv[2]),b=jsonLine(argv[3]);
            need(count(a,"records")>0 && count(b,"records")==2*count(a,"records"),"double-ingest record count mismatch");
            need(count(a,"distinct")==count(b,"distinct") && count(a,"malformed")==0 && count(b,"malformed")==0,
                 "double-ingest distinct/malformed mismatch");
            need(count(b,"duplicates")>=count(a,"duplicates")+count(a,"distinct"),"duplicate suppression not observed");
            std::cout<<"{\"status\":\"ok\",\"duplicate_suppression_observed\":true,\"single_records\":"<<count(a,"records")
                     <<",\"distinct\":"<<count(a,"distinct")<<",\"single_collisions\":"<<count(a,"collisions")
                     <<",\"double_duplicates\":"<<count(b,"duplicates")<<"}\n";
        } else if(cmd=="summary") {
            need(argc==6,"summary logfile min_verified min_reports require_stopped");
            const auto last=jsonLine(argv[2]);
            need(count(last,"badReports")==0 && count(last,"dropped")==0,"summary has bad/dropped reports");
            need(count(last,"verified")>=std::stoull(argv[3]) && count(last,"reports")>=std::stoull(argv[4]),"insufficient verification/reports");
            if(std::stoi(argv[5])) need(last.find("\"stopped\":true")!=std::string::npos,"slice did not stop gracefully");
            std::cout<<"{\"status\":\"ok\",\"native_summary_gate\":true,\"verified\":"<<count(last,"verified")
                     <<",\"reports\":"<<count(last,"reports")<<"}\n";
        } else if(cmd=="check") {
            need(argc==8,"check file32 file64 runid weight max_replays max_steps");
            check(argv[2],argv[3],std::stoul(argv[4]),std::stoi(argv[5]),std::stoul(argv[6]),std::stoull(argv[7]));
        } else if(cmd=="zero-fixture") {
            need(argc==5,"zero-fixture source32 source64 output_prefix");
            auto a=read<Record>(argv[2]); auto b=read<DpRecord>(argv[3]);
            need(a.size()==b.size(),"fixture pair size mismatch"); size_t index=0;
            while(index<b.size() && b[index].iters!=0) ++index;
            need(index<b.size(),"source corpus has no zero-length report");
            HostWalk walk; ec2k_pt p,q; challengePoints(&p,&q); walk.build(p,q);
            need(rewalk(walk,b[index],nullptr),"source zero does not golden replay");
            write(std::string(argv[4])+".32",std::vector<Record>{a[index]});
            write(std::string(argv[4])+".64",std::vector<DpRecord>{b[index]});
            std::cout<<"{\"status\":\"fixture_written\",\"source_record_index\":"<<index<<",\"seed\":"<<b[index].seed<<",\"iters\":0}\n";
        } else if(cmd=="tamper-zero-seed") {
            need(argc==4,"tamper-zero-seed source64 output_prefix");
            auto b=read<DpRecord>(argv[2]); need(b.size()==1 && b[0].iters==0,"requires one zero record");
            b[0].seed^=1ull; Record packed{}; campaignRecord(packed.data(),b[0]);
            HostWalk walk; ec2k_pt p,q; challengePoints(&p,&q); walk.build(p,q);
            need(!rewalk(walk,b[0],nullptr),"chosen tampered seed accidentally replays");
            write(std::string(argv[3])+".32",std::vector<Record>{packed});
            write(std::string(argv[3])+".64",b);
            std::cout<<"{\"status\":\"fixture_written\",\"mutation\":\"seed_low_bit_in_both_formats_endpoint_unchanged\",\"iters\":0}\n";
        } else if(cmd=="tamper") {
            need(argc==4,"tamper source64 output64"); auto v=read<DpRecord>(argv[2]);
            need(!v.empty(),"cannot tamper empty input"); v[0].x[0]^=1; write(argv[3],v);
            std::cout<<"{\"status\":\"fixture_written\",\"mutation\":\"first_x_bit\"}\n";
        } else if(cmd=="fixture") {
            need(argc==3,"fixture output_prefix"); HostWalk walk; ec2k_pt p,q; challengePoints(&p,&q); walk.build(p,q);
            std::vector<DpRecord> full; std::vector<Record> packed;
            for(unsigned i=0;i<256 && full.size()<8;i++) {
                DpRecord r{}; need(referenceReport(walk,(53180ull<<48)|(uint64_t(i)<<16),60,10000,&r),"reference fixture failed");
                if(!r.iters) continue; // a CPU fixture starts outside the DP set
                full.push_back(r);
                Record enc{}; campaignRecord(enc.data(),r); packed.push_back(enc);
            }
            need(full.size()==8,"not enough positive-length fixture trails");
            write(std::string(argv[2])+".32",packed); write(std::string(argv[2])+".64",full);
            std::cout<<"{\"status\":\"fixture_written\",\"records\":8,\"run_id\":53180,\"dp_weight\":60}\n";
        } else need(false,"unknown command");
        return 0;
    } catch(const std::exception &e) {
        std::cerr<<"native_ingestion_gate: "<<e.what()<<"\n"; return 1;
    }
}
