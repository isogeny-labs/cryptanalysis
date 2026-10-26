// Persistent, versioned, bounded worker protocol. All words are little-endian.
#pragma once
#include "arithmetic.h"
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
static_assert(sizeof(CcInteger)==20 && sizeof(CcPoint)==44 && sizeof(CcCurve)==172,
              "worker curve ABI");
static_assert(sizeof(CcWalk)==84 && sizeof(CcRho)==180,"worker rho ABI");
constexpr std::uint32_t CC_REQUEST=0x43435131, CC_RESPONSE=0x43435231;
struct CcRequest {
    std::uint32_t op=0,n=0,steps=0;
    CcCurve curve{};
    std::vector<CcPoint> left,right,points;
    std::vector<CcInteger> scalars;
    std::vector<CcRho> states,rho;
};
inline void cc_read(void *p,std::size_t n) {
    if (!std::cin.read(static_cast<char *>(p),static_cast<std::streamsize>(n)))
        throw std::runtime_error("truncated request");
}
inline bool cc_read_request(CcRequest &r) {
    std::uint32_t h[4];
    if (!std::cin.read(reinterpret_cast<char *>(h),sizeof(h))) {
        if (std::cin.eof() && std::cin.gcount()==0) return false;
        throw std::runtime_error("truncated request header");
    }
    if (h[0]!=CC_REQUEST || h[1]<1 || h[1]>3 || h[2]==0 || h[2]>4096 ||
        (h[1]==3 && (h[3]==0 || h[3]>64)))
        throw std::runtime_error("invalid request bounds or protocol");
    r.op=h[1];r.n=h[2];r.steps=h[3];cc_read(&r.curve,sizeof(r.curve));
    if (r.curve.binary>1) throw std::runtime_error("invalid field kind");
    if (r.op==3) {
        r.states.resize(r.n);r.rho.resize(r.n);
        cc_read(r.states.data(),r.n*sizeof(CcRho));
    } else {
        r.left.resize(r.n);r.points.resize(r.n);
        cc_read(r.left.data(),r.n*sizeof(CcPoint));
        if (r.op==1) {
            r.right.resize(r.n);cc_read(r.right.data(),r.n*sizeof(CcPoint));
        } else {
            r.scalars.resize(r.n);cc_read(r.scalars.data(),r.n*sizeof(CcInteger));
        }
    }
    return true;
}
inline void cc_respond(const CcRequest &r) {
    const std::uint32_t h[3]={CC_RESPONSE,0,r.n};
    std::cout.write(reinterpret_cast<const char *>(h),sizeof(h));
    if (r.op==3) std::cout.write(reinterpret_cast<const char *>(r.rho.data()),r.n*sizeof(CcRho));
    else std::cout.write(reinterpret_cast<const char *>(r.points.data()),r.n*sizeof(CcPoint));
    std::cout.flush();
    if (!std::cout) throw std::runtime_error("worker response write failed");
}
inline void cc_error(const std::string &message) {
    std::string text=message.substr(0,4096);
    const std::uint32_t h[3]={CC_RESPONSE,1,static_cast<std::uint32_t>(text.size())};
    std::cout.write(reinterpret_cast<const char *>(h),sizeof(h));
    std::cout.write(text.data(),text.size());std::cout.flush();
}
template<class Device> int cc_worker_main(int argc,char **argv) {
    bool greeted=false,probe=false;
    try {
        int ordinal=0;
        for (int i=1;i<argc;++i) {
            if (!std::strcmp(argv[i],"--device") && i+1<argc) {
                std::size_t end=0;std::string arg=argv[++i];
                ordinal=std::stoi(arg,&end);
                if (end!=arg.size() || ordinal<0) throw std::runtime_error("invalid device ordinal");
            } else if (!std::strcmp(argv[i],"--probe")) probe=true;
            else throw std::runtime_error("usage: certicom_WORKER [--device N] [--probe]");
        }
        const std::uint32_t endian=1;
        if (*reinterpret_cast<const unsigned char *>(&endian)!=1)
            throw std::runtime_error("worker requires a little-endian host");
        Device device(ordinal,argv[0]);
        std::cout<<"CERTICOM_WORKER 1 "<<device.kind()<<" "<<device.name()<<"\n"<<std::flush;
        greeted=true;
        if (probe) return 0;
        for (;;) {
            CcRequest r;
            if (!cc_read_request(r)) break;
            device.execute(r);cc_respond(r);
        }
        return 0;
    } catch (const std::exception &e) {
        if (greeted) cc_error(e.what());
        std::cerr<<"certicom worker: "<<e.what()<<"\n";return 3;
    }
}
