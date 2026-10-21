// metalwalk.h - the packed table walk on an Apple GPU (Objective-C++, ARC).
//
// The kernels are metal/walk.metal behind the packed GF(2^131) headers, turned
// into Metal Shading Language by scripts/mslgen.py and compiled here, when the
// client starts, with newLibraryWithSource: nothing needs the offline Metal
// toolchain, so the Command Line Tools build and run this.
//
// The engine follows src/ec2k_gpu.cu: a GPU thread owns ECC_BATCH lanes and
// one inversion, a lane that reports marks itself dead, and the host revives
// dead lanes between launches.  Two things are a Mac's.  Memory is unified, so
// the state buffers are shared and the host writes start points into them
// directly -- there is no init kernel, and lanes are seeded by the CPU
// client's startPoint over PMULL.  And a command buffer that runs for seconds
// is killed by the GPU watchdog, so a launch is cut into dispatches sized from
// the measured time of a step.
#pragma once

#import <Foundation/Foundation.h>
#import <Metal/Metal.h>

#include "cpuwalk.h"

#include <array>
#include <cmath>
#include <cstddef>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

namespace ec2k_metal
{

using namespace ec2k_client;
using eccPacked131::P131;

static const char kWalkSource[] =
#include "walk_metal.inc"
    ;

// Must match WalkArgs in metal/walk.metal.
struct WalkArgs {
    uint32_t threads, steps;
    int32_t dpWeight;
    uint32_t dpCap;
    uint64_t iterBase, maxIters;
    uint32_t guardPeriod, pad;
};

inline uint64_t checkpointHash(const void *data, size_t bytes,
                               uint64_t hash = 1469598103934665603ULL)
{
    const uint8_t *p = (const uint8_t *)data;
    for (size_t i = 0; i < bytes; i++) {
        hash ^= p[i];
        hash *= 1099511628211ULL;
    }
    return hash;
}

struct MetalCheckpointHeader {
    char magic[8];
    uint32_t version, threads, batch, dpWeight, runId, guardPeriod;
    uint64_t pSeed, qSeed, maxIters, iterBase, tableHash, shaderHash, payloadBytes;
    RunTotals totals;
    uint64_t checksum;
};

inline id<MTLDevice> pickDevice(int index)
{
    if (index > 0) {
        NSArray<id<MTLDevice>> *all = MTLCopyAllDevices();
        if ((NSUInteger)index < all.count) return all[(NSUInteger)index];
    }
    return MTLCreateSystemDefaultDevice();
}

// The library for a given lanes-per-thread; nil and a message on failure.
inline id<MTLLibrary> compileWalkLibrary(id<MTLDevice> device, int batch,
                                        std::string *error, uint64_t *sourceHash = nullptr)
{
    MTLCompileOptions *options = [MTLCompileOptions new];
    options.preprocessorMacros = @{@"ECC_BATCH" : @(batch)};
    NSError *err = nil;
    // EC2K_METAL_SOURCE=file replaces the built-in source: shader development
    // without rebuilding the client.
    NSString *source = [NSString stringWithUTF8String:kWalkSource];
    if (const char *path = getenv("EC2K_METAL_SOURCE"))
        source = [NSString stringWithContentsOfFile:[NSString stringWithUTF8String:path]
                                           encoding:NSUTF8StringEncoding
                                              error:&err];
    if (!source) {
        if (error) *error = "cannot read EC2K_METAL_SOURCE";
        return nil;
    }
    if (sourceHash) {
        const char *bytes = [source UTF8String];
        *sourceHash = checkpointHash(bytes, strlen(bytes));
    }
    id<MTLLibrary> lib = [device newLibraryWithSource:source options:options error:&err];
    if (!lib && error) *error = err ? [[err localizedDescription] UTF8String] : "unknown error";
    return lib;
}

inline id<MTLComputePipelineState> pipelineFor(id<MTLDevice> device, id<MTLLibrary> lib,
                                               const char *name, std::string *error)
{
    NSError *err = nil;
    id<MTLFunction> fn = [lib newFunctionWithName:[NSString stringWithUTF8String:name]];
    id<MTLComputePipelineState> ps =
        fn ? [device newComputePipelineStateWithFunction:fn error:&err] : nil;
    if (!ps && error) *error = err ? [[err localizedDescription] UTF8String] : "no such kernel";
    return ps;
}

inline MTLSize threadgroupFor(id<MTLComputePipelineState> ps)
{
    const NSUInteger w = ps.threadExecutionWidth, cap = ps.maxTotalThreadsPerThreadgroup;
    NSUInteger n = cap < 256 ? cap : 256;
    if (n >= w) n -= n % w;
    return MTLSizeMake(n ? n : 1, 1, 1);
}

class MetalEngine
{
  public:
    // `ok()` is false, with `error()`, when there is no device or the shader
    // does not build.
    MetalEngine(const HostTable &table, const Options &o, bool bench, int batch = 0,
                unsigned guardPeriod = ECC_GUARD_PERIOD)
        : seeder_(table, o, bench, seederGeometry())
    {
        // Measured on an M4 Pro (20-core GPU), M it/s at batch x threads:
        // 16 x 16384 294, 32 x 8192 319, 32 x 32768 390, 32 x 65536 420,
        // 64 x 16384 359.  More lanes keep paying a little, at the price of
        // more unreported trail in flight; the default stops at a million.
        batch_ = batch > 0 ? batch : (o.batch > 0 ? o.batch : 32);
        threads_ = o.threads > 0 ? o.threads : 32768;
        args_.threads = (uint32_t)threads_;
        args_.dpWeight = bench ? -1 : o.dpWeight;
        args_.dpCap = o.dpCap;
        args_.iterBase = 0;
        args_.maxIters = o.maxIters;
        args_.guardPeriod = guardPeriod ? guardPeriod : 1;
        args_.pad = 0;
        runId_ = o.runId;
        pSeed_ = o.pSeed;
        qSeed_ = o.qSeed;

        device_ = pickDevice(o.device);
        if (!device_) {
            error_ = "no Metal device";
            return;
        }
        id<MTLLibrary> lib = compileWalkLibrary(device_, batch_, &error_, &shaderHash_);
        if (!lib) return;
        walk_ = pipelineFor(device_, lib, "walk", &error_);
        if (!walk_) return;
        queue_ = [device_ newCommandQueue];

        const size_t lanes = laneCount();
        x_ = shared(lanes * 5 * sizeof(uint32_t));
        y_ = shared(lanes * 5 * sizeof(uint32_t));
        hist_ = shared(lanes * sizeof(uint64_t));
        seed_ = shared(lanes * sizeof(uint64_t));
        start_ = shared(lanes * sizeof(uint64_t));
        dead_ = shared(lanes * sizeof(uint32_t));
        dp_ = shared(size_t(args_.dpCap) * sizeof(DpRecord));
        counts_ = shared(4 * sizeof(uint32_t));
        const std::vector<uint32_t> consts = table.deviceConsts();
        tableHash_ = checkpointHash(consts.data(), consts.size() * sizeof(uint32_t));
        tw_ = [device_ newBufferWithBytes:consts.data()
                                   length:consts.size() * sizeof(uint32_t)
                                  options:MTLResourceStorageModeShared];
        if (!x_ || !y_ || !hist_ || !seed_ || !start_ || !dead_ || !dp_ || !counts_ || !tw_) {
            error_ = "cannot allocate the walk state";
            return;
        }
        memset(counts_.contents, 0, 4 * sizeof(uint32_t));
        if (o.checkpoint.empty() || access(o.checkpoint.c_str(), F_OK) != 0) {
            std::vector<size_t> all(lanes);
            for (size_t i = 0; i < lanes; ++i) all[i] = i;
            seedLanes(all, false);
        }
        ready_ = true;
    }

    bool ok() const { return ready_; }
    const std::string &error() const { return error_; }
    size_t laneCount() const { return size_t(threads_) * size_t(batch_); }
    const char *name() const { return "metal"; }
    std::string deviceName() const { return device_ ? [[device_ name] UTF8String] : "none"; }
    int threads() const { return threads_; }
    int batch() const { return batch_; }
    std::string describe() const
    {
        char buf[256];
        snprintf(buf, sizeof(buf), ",\"threads\":%d,\"batch\":%d,\"device\":\"%s\"", threads_,
                 batch_, deviceName().c_str());
        return buf;
    }

    bool saveCheckpoint(const std::string &path, const RunTotals &totals)
    {
        auto arrays = stateArrays();
        MetalCheckpointHeader h;
        memset(&h, 0, sizeof(h));
        memcpy(h.magic, "EC2KMCK1", 8);
        h.version = 1;
        h.threads = (uint32_t)threads_;
        h.batch = (uint32_t)batch_;
        h.dpWeight = (uint32_t)args_.dpWeight;
        h.runId = runId_;
        h.guardPeriod = args_.guardPeriod;
        h.pSeed = pSeed_;
        h.qSeed = qSeed_;
        h.maxIters = args_.maxIters;
        h.iterBase = args_.iterBase;
        h.tableHash = tableHash_;
        h.shaderHash = shaderHash_;
        h.totals = totals;
        for (const auto &a : arrays) h.payloadBytes += a.second;
        uint64_t hash = checkpointHash(&h, offsetof(MetalCheckpointHeader, checksum));
        for (const auto &a : arrays) hash = checkpointHash(a.first, a.second, hash);
        h.checksum = hash;

        std::string pattern = path + ".tmp.XXXXXX";
        std::vector<char> tmp(pattern.begin(), pattern.end());
        tmp.push_back('\0');
        int fd = mkstemp(tmp.data());
        if (fd < 0) { error_ = "cannot create checkpoint temporary file"; return false; }
        FILE *f = fdopen(fd, "wb");
        if (!f) {
            close(fd);
            unlink(tmp.data());
            error_ = "cannot open checkpoint temporary file";
            return false;
        }
        bool ok = fwrite(&h, sizeof(h), 1, f) == 1;
        for (const auto &a : arrays)
            if (ok) ok = fwrite(a.first, 1, a.second, f) == a.second;
        if (ok) ok = fflush(f) == 0 && fsync(fileno(f)) == 0;
        if (fclose(f) != 0) ok = false;
        if (ok) ok = rename(tmp.data(), path.c_str()) == 0;
        if (ok) {
            size_t slash = path.find_last_of('/');
            std::string dir = slash == std::string::npos ? "." :
                              slash == 0 ? "/" : path.substr(0, slash);
            int dfd = open(dir.c_str(), O_RDONLY);
            ok = dfd >= 0 && fsync(dfd) == 0;
            if (dfd >= 0 && close(dfd) != 0) ok = false;
        }
        if (!ok) {
            unlink(tmp.data());
            error_ = "cannot write, rename or sync checkpoint";
        }
        return ok;
    }

    // 1 = restored, 0 = fresh run, -1 = present but invalid.
    int loadCheckpoint(const std::string &path, RunTotals *totals)
    {
        FILE *f = fopen(path.c_str(), "rb");
        if (!f) {
            if (errno == ENOENT) return 0;
            error_ = "cannot open checkpoint";
            return -1;
        }
        MetalCheckpointHeader h;
        bool ok = fread(&h, sizeof(h), 1, f) == 1;
        auto arrays = stateArrays();
        size_t bytes = 0;
        for (const auto &a : arrays) bytes += a.second;
        if (!ok || memcmp(h.magic, "EC2KMCK1", 8) != 0 || h.version != 1 ||
            h.threads != (uint32_t)threads_ || h.batch != (uint32_t)batch_ ||
            h.dpWeight != (uint32_t)args_.dpWeight || h.runId != runId_ ||
            h.guardPeriod != args_.guardPeriod || h.pSeed != pSeed_ ||
            h.qSeed != qSeed_ || h.tableHash != tableHash_ ||
            h.shaderHash != shaderHash_ || h.payloadBytes != bytes ||
            !std::isfinite(h.totals.elapsed) || h.totals.elapsed < 0 ||
            h.iterBase > UINT64_MAX / laneCount() ||
            h.totals.iterations != h.iterBase * laneCount() ||
            h.totals.verified > h.totals.reports ||
            h.totals.badReports > h.totals.verified) {
            fclose(f);
            error_ = "checkpoint identity, geometry or counters do not match";
            return -1;
        }
        std::vector<uint8_t> payload(bytes);
        ok = fread(payload.data(), 1, bytes, f) == bytes && fgetc(f) == EOF;
        if (fclose(f) != 0) ok = false;
        uint64_t hash = checkpointHash(&h, offsetof(MetalCheckpointHeader, checksum));
        if (ok) hash = checkpointHash(payload.data(), bytes, hash);
        if (!ok || hash != h.checksum) {
            error_ = "checkpoint is truncated or checksum failed";
            return -1;
        }
        size_t off = 0;
        for (const auto &a : arrays) {
            memcpy(a.first, payload.data() + off, a.second);
            off += a.second;
        }
        args_.iterBase = h.iterBase;
        *totals = h.totals;
        if (h.maxIters != args_.maxIters)
            fprintf(stderr, "checkpoint restart limit changed from %llu to %llu\n",
                    (unsigned long long)h.maxIters, (unsigned long long)args_.maxIters);
        return 1;
    }

    void launch(int steps, std::vector<DpRecord> *out, LaunchCounts *counts)
    {
        for (int done = 0; done < steps;) {
            // Size a dispatch to about a quarter of a second from the last one's
            // measured time per step; the first is a single step.
            int n = secondsPerStep_ > 0 ? int(0.25 / secondsPerStep_) : 1;
            n = n < 1 ? 1 : (n > steps - done ? steps - done : n);
            const double t0 = now();
            if (!dispatch(n)) {
                counts->exhausted = true; // ends the run; error_ says why
                return;
            }
            secondsPerStep_ = (now() - t0) / n;
            done += n;
        }
        const uint32_t *c = (const uint32_t *)counts_.contents;
        const uint32_t reported = c[0], kept = reported < args_.dpCap ? reported : args_.dpCap;
        const DpRecord *recs = (const DpRecord *)dp_.contents;
        out->insert(out->end(), recs, recs + kept);
        counts->restarts += c[1];
        counts->dropped += reported - kept;
        counts->exhausted = counts->exhausted || c[2] != 0;
        counts->iterations += (unsigned long long)laneCount() * (unsigned long long)steps;
        const bool any = c[0] || c[1];
        memset(counts_.contents, 0, 4 * sizeof(uint32_t));
        if (any && !counts->exhausted) {
            std::vector<size_t> deadLanes;
            const uint32_t *dead = (const uint32_t *)dead_.contents;
            for (size_t lane = 0; lane < laneCount(); ++lane)
                if (dead[lane]) deadLanes.push_back(lane);
            seedLanes(deadLanes, true);
        }
    }

    // A lane as a report would describe it now: for the tests.
    DpRecord laneRecord(size_t lane) const
    {
        using namespace eccPacked131;
        P131 x, y;
        memcpy(x.v, (const uint32_t *)x_.contents + lane * 5, sizeof(x.v));
        memcpy(y.v, (const uint32_t *)y_.contents + lane * 5, sizeof(y.v));
        DpRecord rec;
        rec.seed = ((const uint64_t *)seed_.contents)[lane];
        rec.iters = args_.iterBase - ((const uint64_t *)start_.contents)[lane];
        toLimbs(fromPacked(fromPolynomial131(x)), rec.x);
        toLimbs(fromPacked(fromPolynomial131(y)), rec.y);
        return rec;
    }

  private:
    std::array<std::pair<void *, size_t>, 6> stateArrays() const
    {
        const size_t lanes = laneCount();
        return {{{x_.contents, lanes * 5 * sizeof(uint32_t)},
                 {y_.contents, lanes * 5 * sizeof(uint32_t)},
                 {hist_.contents, lanes * sizeof(uint64_t)},
                 {seed_.contents, lanes * sizeof(uint64_t)},
                 {start_.contents, lanes * sizeof(uint64_t)},
                 {dead_.contents, lanes * sizeof(uint32_t)}}};
    }

    static ec2k_cpu::Geometry seederGeometry()
    {
        ec2k_cpu::Geometry g;
        g.workers = g.batch = g.chunks = 1;
        return g;
    }

    id<MTLBuffer> shared(size_t bytes)
    {
        return [device_ newBufferWithLength:bytes options:MTLResourceStorageModeShared];
    }

    bool dispatch(int steps)
    {
        args_.steps = (uint32_t)steps;
        id<MTLCommandBuffer> cb = [queue_ commandBuffer];
        id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
        [enc setComputePipelineState:walk_];
        [enc setBytes:&args_ length:sizeof(args_) atIndex:0];
        id<MTLBuffer> buffers[] = {x_, y_, hist_, seed_, start_, dead_, dp_, counts_, tw_};
        for (NSUInteger i = 0; i < 9; ++i) [enc setBuffer:buffers[i] offset:0 atIndex:i + 1];
        [enc dispatchThreads:MTLSizeMake((NSUInteger)threads_, 1, 1)
            threadsPerThreadgroup:threadgroupFor(walk_)];
        [enc endEncoding];
        [cb commit];
        [cb waitUntilCompleted];
        if (cb.status != MTLCommandBufferStatusCompleted) {
            error_ =
                cb.error ? [[cb.error localizedDescription] UTF8String] : "command buffer failed";
            fprintf(stderr, "Metal: %s\n", error_.c_str());
            return false;
        }
        args_.iterBase += (uint64_t)steps;
        return true;
    }

    // (Re)start lanes from their seeds, on the host's cores: a fresh lane from
    // eccSeedFor, a dead one from its next seed.
    void seedLanes(const std::vector<size_t> &lanes, bool revive)
    {
        uint32_t *x = (uint32_t *)x_.contents, *y = (uint32_t *)y_.contents;
        uint64_t *hist = (uint64_t *)hist_.contents, *seed = (uint64_t *)seed_.contents,
                 *start = (uint64_t *)start_.contents;
        uint32_t *dead = (uint32_t *)dead_.contents;
        const uint64_t nowIter = args_.iterBase;
        auto body = [&](size_t from, size_t to) {
            for (size_t i = from; i < to; ++i) {
                const size_t lane = lanes[i];
                seed[lane] = revive ? seed[lane] + 1 : eccSeedFor(runId_, lane);
                P131 xp, yp;
                seeder_.startPoint(seed[lane], &xp, &yp);
                memcpy(x + lane * 5, xp.v, sizeof(xp.v));
                memcpy(y + lane * 5, yp.v, sizeof(yp.v));
                start[lane] = nowIter;
                hist[lane] = ECC_HIST_EMPTY;
                dead[lane] = 0;
            }
        };
        const unsigned cores = std::thread::hardware_concurrency();
        const size_t workers = lanes.size() < 256 ? 1 : (cores ? cores : 1);
        std::vector<std::thread> pool;
        for (size_t w = 1; w < workers; ++w)
            pool.emplace_back(body, lanes.size() * w / workers, lanes.size() * (w + 1) / workers);
        body(0, lanes.size() / workers);
        for (std::thread &t : pool) t.join();
    }

    ec2k_cpu::CpuEngine seeder_;
    WalkArgs args_{};
    unsigned runId_ = 0;
    uint64_t pSeed_ = 0, qSeed_ = 0, tableHash_ = 0, shaderHash_ = 0;
    int threads_ = 0, batch_ = 0;
    double secondsPerStep_ = 0;
    bool ready_ = false;
    std::string error_;
    id<MTLDevice> device_ = nil;
    id<MTLComputePipelineState> walk_ = nil;
    id<MTLCommandQueue> queue_ = nil;
    id<MTLBuffer> x_ = nil, y_ = nil, hist_ = nil, seed_ = nil, start_ = nil, dead_ = nil,
                  dp_ = nil, counts_ = nil, tw_ = nil;
};

} // namespace ec2k_metal
