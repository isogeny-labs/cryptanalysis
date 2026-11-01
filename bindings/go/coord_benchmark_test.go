package cryptanalysis_test

import (
	"crypto/sha256"
	"encoding/binary"
	"encoding/hex"
	"fmt"
	"sort"
	"strings"
	"syscall"
	"testing"

	ca "github.com/aburan28/cryptanalysis/bindings/go"
)

const coordinatorBenchmarkPeer = "bench.0"

var (
	benchmarkVersionVectorSink ca.VersionVector
	benchmarkDeltaLinesSink    []string
	benchmarkDeltaReachedSink  ca.VersionVector
)

// BenchmarkStateVersionVector exposes the coordinator's full-log scan.  The
// fixture is built before the timer starts, and its canonical vector digest is
// checked after the timer stops so an implementation cannot win by omitting
// entries.
func BenchmarkStateVersionVector(b *testing.B) {
	for _, entries := range []int{1024, 8192} {
		b.Run(fmt.Sprintf("log_%d", entries), func(b *testing.B) {
			state := newCoordinatorBenchmarkState(b, entries)
			expected := state.VersionVector()
			expectedDigest := versionVectorDigest(expected)

			var got ca.VersionVector
			b.ReportAllocs()
			cpuBefore := processCPUNanoseconds(b)
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				got = state.VersionVector()
			}
			b.StopTimer()
			cpuNanos := processCPUNanoseconds(b) - cpuBefore
			benchmarkVersionVectorSink = got

			gotDigest := versionVectorDigest(got)
			if gotDigest != expectedDigest {
				b.Fatalf("version-vector digest = %s, want %s", gotDigest, expectedDigest)
			}
			b.ReportMetric(float64(entries), "log_entries")
			b.ReportMetric(float64(cpuNanos)/float64(b.N), "cpu-ns/op")
			b.Logf("correctness vector_sha256=%s vector=%s", gotDigest, canonicalVersionVector(got))
		})
	}
}

func BenchmarkStateDeltaSinceCaughtUp(b *testing.B) {
	benchmarkStateDeltaSince(b, true)
}

func BenchmarkStateDeltaSinceOneBehind(b *testing.B) {
	benchmarkStateDeltaSince(b, false)
}

// benchmarkStateDeltaSince covers both the common caught-up push-loop case and
// a one-record delivery.  In both cases the current implementation still scans
// and copies every log record, which is the hotspot this benchmark is intended
// to retain through optimization work.
func benchmarkStateDeltaSince(b *testing.B, caughtUp bool) {
	for _, entries := range []int{1024, 8192} {
		b.Run(fmt.Sprintf("log_%d", entries), func(b *testing.B) {
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
			b.ReportAllocs()
			cpuBefore := processCPUNanoseconds(b)
			b.ResetTimer()
			for i := 0; i < b.N; i++ {
				lines, reached = state.DeltaSince(known)
			}
			b.StopTimer()
			cpuNanos := processCPUNanoseconds(b) - cpuBefore
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
			b.ReportMetric(float64(entries), "log_entries")
			b.ReportMetric(float64(len(expectedLines)), "lines/op")
			b.ReportMetric(float64(cpuNanos)/float64(b.N), "cpu-ns/op")
			b.Logf("correctness lines_sha256=%s reached_vector_sha256=%s reached=%s",
				gotLinesDigest, gotReachedDigest, canonicalVersionVector(reached))
		})
	}
}

// newCoordinatorBenchmarkState builds an exact-length, deterministic log.  A
// lane generates valid check-ins; copying a prefix into a fresh state fixes the
// requested length, and replacing only the sender timestamp makes the encoded
// lines stable across benchmark processes.  None of this setup is timed.
func newCoordinatorBenchmarkState(b *testing.B, entries int) *ca.State {
	b.Helper()

	const (
		p      = uint64(4503599627372423)
		order  = uint64(2251799813686211)
		secret = uint64(0x123456789ab)
	)
	g, err := ca.NewZp(p, order)
	if err != nil {
		b.Fatalf("benchmark group: %v", err)
	}
	b.Cleanup(g.Close)
	base, err := g.FindGenerator(1)
	if err != nil {
		b.Fatalf("benchmark generator: %v", err)
	}
	target, err := g.Mul(base, secret)
	if err != nil {
		b.Fatalf("benchmark target: %v", err)
	}
	job, err := ca.NewJob(&ca.JobParams{
		Kind:     ca.GroupZp,
		P:        p,
		Order:    order,
		Base:     base,
		Target:   target,
		DPBits:   4,
		Branches: 16,
		UnitSize: 256,
		Seed:     0x5eed,
	})
	if err != nil {
		b.Fatalf("benchmark job: %v", err)
	}
	ctx, err := ca.OpenCtx(job)
	if err != nil {
		b.Fatalf("benchmark context: %v", err)
	}
	b.Cleanup(ctx.Close)

	source, err := ca.NewState(ctx)
	if err != nil {
		b.Fatalf("benchmark source state: %v", err)
	}
	defer source.Close()
	result, err := ca.RunLane(ctx, source, ca.LaneParams{
		Peer:         coordinatorBenchmarkPeer,
		CheckinEvery: 1,
		ClaimWindow:  1,
		MaxWalkers:   uint64(entries),
	})
	if err != nil {
		b.Fatalf("benchmark lane: %v", err)
	}
	if result.Solved {
		b.Fatalf("benchmark fixture unexpectedly solved the planted DLP")
	}
	if source.LogLen() < entries {
		b.Fatalf("benchmark lane produced %d log entries, want at least %d", source.LogLen(), entries)
	}

	state, err := ca.NewState(ctx)
	if err != nil {
		b.Fatalf("benchmark state: %v", err)
	}
	b.Cleanup(state.Close)
	for i := 0; i < entries; i++ {
		entry, ok := source.LogAt(i)
		if !ok {
			b.Fatalf("benchmark source has no log entry %d", i)
		}
		line := fixedCheckinTime(b, entry.Line)
		outcome, err := state.ApplyLine(line)
		if err != nil {
			b.Fatalf("apply benchmark log entry %d: %v", i, err)
		}
		if !outcome.Fresh || outcome.RejectedDPs != 0 {
			b.Fatalf("benchmark log entry %d: fresh=%t rejected=%d", i, outcome.Fresh, outcome.RejectedDPs)
		}
	}
	if got := state.LogLen(); got != entries {
		b.Fatalf("benchmark log length = %d, want %d", got, entries)
	}
	return state
}

func fixedCheckinTime(b *testing.B, line string) string {
	b.Helper()
	fields := strings.SplitN(line, " ", 6)
	if len(fields) != 6 || fields[0] != "ci" {
		b.Fatalf("unexpected check-in encoding %q", line)
	}
	fields[4] = "1700000000"
	return strings.Join(fields, " ")
}

func cloneVersionVector(vv ca.VersionVector) ca.VersionVector {
	clone := make(ca.VersionVector, len(vv))
	for peer, seq := range vv {
		clone[peer] = seq
	}
	return clone
}

func canonicalVersionVector(vv ca.VersionVector) string {
	peers := make([]string, 0, len(vv))
	for peer := range vv {
		peers = append(peers, peer)
	}
	sort.Strings(peers)
	var out strings.Builder
	for _, peer := range peers {
		fmt.Fprintf(&out, "%s:%d\n", peer, vv[peer])
	}
	return out.String()
}

func versionVectorDigest(vv ca.VersionVector) string {
	sum := sha256.Sum256([]byte(canonicalVersionVector(vv)))
	return hex.EncodeToString(sum[:])
}

func linesDigest(lines []string) string {
	h := sha256.New()
	var length [8]byte
	for _, line := range lines {
		binary.LittleEndian.PutUint64(length[:], uint64(len(line)))
		_, _ = h.Write(length[:])
		_, _ = h.Write([]byte(line))
	}
	return hex.EncodeToString(h.Sum(nil))
}

func processCPUNanoseconds(b *testing.B) int64 {
	b.Helper()
	var usage syscall.Rusage
	if err := syscall.Getrusage(syscall.RUSAGE_SELF, &usage); err != nil {
		b.Fatalf("read process CPU time: %v", err)
	}
	seconds := usage.Utime.Sec + usage.Stime.Sec
	microseconds := usage.Utime.Usec + usage.Stime.Usec
	return seconds*1e9 + microseconds*1e3
}
