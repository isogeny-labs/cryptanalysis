package cryptanalysis_test

import (
	"os"
	"runtime"
	"runtime/pprof"
	"strconv"
	"testing"

	ca "github.com/aburan28/cryptanalysis/bindings/go"
)

// This file is an experiment-only overlay. The profile runner copies it into
// bindings/go beside coord_benchmark_test.go in an exact synthetic source
// tree. It deliberately reuses that file's deterministic fixture, digests,
// and sinks instead of changing production code.

func BenchmarkProfileStateVersionVector(b *testing.B) {
	for _, entries := range []int{1024, 8192} {
		b.Run(benchmarkLogName(entries), func(b *testing.B) {
			profileAllocationRate(b)
			state := newCoordinatorBenchmarkState(b, entries)
			expectedDigest := versionVectorDigest(state.VersionVector())

			var got ca.VersionVector
			finish := beginOperationProfiles(b)
			cgoBefore := runtime.NumCgoCall()
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				got = state.VersionVector()
			}
			b.StopTimer()
			cgoAfter := runtime.NumCgoCall()
			finish()
			benchmarkVersionVectorSink = got

			gotDigest := versionVectorDigest(got)
			if gotDigest != expectedDigest {
				b.Fatalf("version-vector digest = %s, want %s", gotDigest, expectedDigest)
			}
			b.ReportMetric(float64(cgoAfter-cgoBefore)/float64(b.N), "cgo-calls/op")
			b.ReportMetric(float64(entries), "log_entries")
			b.Logf("correctness vector_sha256=%s vector=%s", gotDigest, canonicalVersionVector(got))
		})
	}
}

func BenchmarkProfileStateDeltaSinceCaughtUp(b *testing.B) {
	benchmarkProfileStateDeltaSince(b, true)
}

func BenchmarkProfileStateDeltaSinceOneBehind(b *testing.B) {
	benchmarkProfileStateDeltaSince(b, false)
}

func benchmarkProfileStateDeltaSince(b *testing.B, caughtUp bool) {
	for _, entries := range []int{1024, 8192} {
		b.Run(benchmarkLogName(entries), func(b *testing.B) {
			profileAllocationRate(b)
			state := newCoordinatorBenchmarkState(b, entries)
			known := cloneVersionVector(state.VersionVector())
			if !caughtUp {
				seq := known[coordinatorBenchmarkPeer]
				if seq == 0 {
					b.Fatalf("fixture has no sequence for %q", coordinatorBenchmarkPeer)
				}
				known[coordinatorBenchmarkPeer] = seq - 1
			}

			expectedLines, expectedReached := state.DeltaSince(known)
			expectedLinesDigest := linesDigest(expectedLines)
			expectedReachedDigest := versionVectorDigest(expectedReached)
			wantLines := 0
			if !caughtUp {
				wantLines = 1
			}
			if len(expectedLines) != wantLines {
				b.Fatalf("fixture delta has %d lines, want %d", len(expectedLines), wantLines)
			}

			var lines []string
			var reached ca.VersionVector
			finish := beginOperationProfiles(b)
			cgoBefore := runtime.NumCgoCall()
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				lines, reached = state.DeltaSince(known)
			}
			b.StopTimer()
			cgoAfter := runtime.NumCgoCall()
			finish()
			benchmarkDeltaLinesSink = lines
			benchmarkDeltaReachedSink = reached

			gotLinesDigest := linesDigest(lines)
			gotReachedDigest := versionVectorDigest(reached)
			if gotLinesDigest != expectedLinesDigest {
				b.Fatalf("delta digest = %s, want %s", gotLinesDigest, expectedLinesDigest)
			}
			if gotReachedDigest != expectedReachedDigest {
				b.Fatalf("reached-vector digest = %s, want %s", gotReachedDigest, expectedReachedDigest)
			}
			b.ReportMetric(float64(cgoAfter-cgoBefore)/float64(b.N), "cgo-calls/op")
			b.ReportMetric(float64(entries), "log_entries")
			b.ReportMetric(float64(len(expectedLines)), "lines/op")
			b.Logf("correctness lines_sha256=%s reached_vector_sha256=%s reached=%s",
				gotLinesDigest, gotReachedDigest, canonicalVersionVector(reached))
		})
	}
}

func benchmarkLogName(entries int) string {
	if entries == 1024 {
		return "log_1024"
	}
	if entries == 8192 {
		return "log_8192"
	}
	panic("unregistered coordinator profile length")
}

func profileAllocationRate(b *testing.B) {
	b.Helper()
	if os.Getenv("MISAGI_ALLOC_PROFILE") != "" && profileThisRun(b) {
		// Rate one records every allocation. This is diagnostic observer
		// overhead and is never mixed with an unprofiled timing row.
		runtime.MemProfileRate = 1
	}
}

// beginOperationProfiles starts after deterministic fixture construction and
// returns a closure that stops before post-loop correctness hashing. Go's
// allocation profile is cumulative and therefore includes process startup and
// fixture construction; the protocol forbids treating it as loop-only.
func beginOperationProfiles(b *testing.B) func() {
	b.Helper()
	alloc := os.Getenv("MISAGI_ALLOC_PROFILE")
	cpu := os.Getenv("MISAGI_CPU_PROFILE")
	if cpu != "" && alloc != "" {
		b.Fatal("CPU and allocation profiles require separate fresh processes")
	}
	if (cpu != "" || alloc != "") && !profileThisRun(b) {
		return func() {}
	}

	var cpuFile *os.File
	if cpu != "" {
		var err error
		cpuFile, err = exclusiveProfileFile(cpu)
		if err != nil {
			b.Fatalf("create CPU profile: %v", err)
		}
		if err := pprof.StartCPUProfile(cpuFile); err != nil {
			_ = cpuFile.Close()
			b.Fatalf("start CPU profile: %v", err)
		}
	}

	return func() {
		if cpuFile != nil {
			pprof.StopCPUProfile()
			if err := cpuFile.Close(); err != nil {
				b.Fatalf("close CPU profile: %v", err)
			}
		}
		if alloc != "" {
			runtime.GC()
			writeRuntimeProfile(b, "allocs", alloc)
		}
	}
}

// Go's benchmark driver makes an initial b.N=1 discovery call even when
// -test.benchtime is an exact Nx value. Only the registered final-N call may
// create the one-shot profile artifact.
func profileThisRun(b *testing.B) bool {
	b.Helper()
	value := os.Getenv("MISAGI_PROFILE_EXPECTED_N")
	if value == "" {
		b.Fatal("MISAGI_PROFILE_EXPECTED_N is required for a profile mode")
	}
	expected, err := strconv.Atoi(value)
	if err != nil || expected < 1 {
		b.Fatalf("invalid MISAGI_PROFILE_EXPECTED_N %q", value)
	}
	return b.N == expected
}

func writeRuntimeProfile(b *testing.B, name, path string) {
	b.Helper()
	profile := pprof.Lookup(name)
	if profile == nil {
		b.Fatalf("runtime profile %q is unavailable", name)
	}
	file, err := exclusiveProfileFile(path)
	if err != nil {
		b.Fatalf("create %s profile: %v", name, err)
	}
	if err := profile.WriteTo(file, 0); err != nil {
		_ = file.Close()
		b.Fatalf("write %s profile: %v", name, err)
	}
	if err := file.Close(); err != nil {
		b.Fatalf("close %s profile: %v", name, err)
	}
}

func exclusiveProfileFile(path string) (*os.File, error) {
	return os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
}
