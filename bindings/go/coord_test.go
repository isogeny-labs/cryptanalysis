package cryptanalysis_test

import (
	"reflect"
	"strings"
	"sync"
	"testing"

	ca "github.com/aburan28/cryptanalysis/bindings/go"
)

// A small instance with a planted secret, so every run is checkable.
// p = 2q+1 with q = 1000151, a real prime-order subgroup.
func testJob(t *testing.T, secret uint64) (ca.Job, *ca.Ctx, uint64) {
	t.Helper()
	g, err := ca.NewZp(2000303, 1000151)
	if err != nil {
		t.Fatalf("group: %v", err)
	}
	t.Cleanup(g.Close)
	gen, err := g.FindGenerator(1)
	if err != nil {
		t.Fatalf("generator: %v", err)
	}
	x := secret % g.Order()
	if x == 0 {
		x = 1
	}
	h, err := g.Mul(gen, x)
	if err != nil {
		t.Fatalf("mul: %v", err)
	}
	job, err := ca.NewJob(&ca.JobParams{
		Kind: ca.GroupZp, P: g.P(), Order: g.Order(),
		Base: gen, Target: h,
		DPBits: 5, Branches: 16, UnitSize: 32, Seed: 7,
	})
	if err != nil {
		t.Fatalf("job: %v", err)
	}
	ctx, err := ca.OpenCtx(job)
	if err != nil {
		t.Fatalf("ctx: %v", err)
	}
	t.Cleanup(ctx.Close)
	return job, ctx, x
}

func TestJobRoundTrip(t *testing.T) {
	job, ctx, _ := testJob(t, 123456)

	back, err := ca.ParseJob(job.String())
	if err != nil {
		t.Fatalf("parse: %v", err)
	}
	if back.ID() != job.ID() {
		t.Errorf("id changed across a round trip: %x != %x", back.ID(), job.ID())
	}
	if back.Order != 1000151 || back.DPBits != 5 || back.UnitSize != 32 {
		t.Errorf("fields did not survive: %+v", back)
	}
	if got := ctx.ExpectedSteps(); got < 1000 || got > 1e7 {
		t.Errorf("expected steps out of range for a 2^20 group: %g", got)
	}

	// A document altered in transit is refused, not walked: two agents
	// on different branch tables silently stop colliding.
	altered := strings.Replace(job.String(), " dp=5 ", " dp=6 ", 1)
	if altered == job.String() {
		t.Fatal("test bug: nothing was altered")
	}
	if _, err := ca.ParseJob(altered); err == nil {
		t.Error("an altered job document was accepted")
	}

	// A trailing newline is what /v1/job serves.
	if _, err := ca.ParseJob(job.String() + "\n"); err != nil {
		t.Errorf("a served job did not parse: %v", err)
	}
}

func TestVersionVectorWire(t *testing.T) {
	vv := ca.ParseVersionVector("vv alice.0:7 bob.1:3 alice.0:2")
	if vv["alice.0"] != 7 {
		t.Errorf("a lower repeat lowered the vector: %v", vv)
	}
	if vv["bob.1"] != 3 {
		t.Errorf("missing entry: %v", vv)
	}
	// A vector is a hint: garbage entries are skipped, not fatal, and
	// the worst a wrong one costs is a resend.
	vv = ca.ParseVersionVector("vv broken alice.0:notanumber carol.2:9 :5")
	if len(vv) != 1 || vv["carol.2"] != 9 {
		t.Errorf("unparsable entries were not skipped: %v", vv)
	}
	if got := ca.ParseVersionVector(vv.String()); got["carol.2"] != 9 {
		t.Errorf("vector did not survive its own encoding: %v", got)
	}
}

// The merge is a CRDT: order-independent, idempotent, and it refuses
// what it cannot verify.
func TestStateMergeAndRefusals(t *testing.T) {
	_, ctx, secret := testJob(t, 55555)

	src, err := ca.NewState(ctx)
	if err != nil {
		t.Fatalf("state: %v", err)
	}
	defer src.Close()
	if _, err := ca.RunLane(ctx, src, ca.LaneParams{
		Peer: "a.0", MaxWalkers: 24, CheckinEvery: 4,
	}); err != nil {
		t.Fatalf("lane: %v", err)
	}
	lines := src.DeltaFrom(ca.VersionVector{})
	if len(lines) < 3 {
		t.Fatalf("a lane produced only %d check-ins", len(lines))
	}

	forward, err := ca.NewState(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer forward.Close()
	reverse, err := ca.NewState(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer reverse.Close()
	for _, l := range lines {
		if _, err := forward.ApplyLine(l); err != nil {
			t.Fatalf("apply: %v", err)
		}
	}
	for _, l := range lines { // idempotent: the same lines again
		if _, err := forward.ApplyLine(l); err != nil {
			t.Fatalf("re-apply: %v", err)
		}
	}
	for i := len(lines) - 1; i >= 0; i-- { // and order-independent
		if _, err := reverse.ApplyLine(lines[i]); err != nil {
			t.Fatalf("apply reversed: %v", err)
		}
	}
	f, r := forward.Progress(120), reverse.Progress(120)
	if f.DPsStored != r.DPsStored || f.Steps != r.Steps || f.Checkins != r.Checkins {
		t.Errorf("merge is order-dependent:\n forward %+v\n reverse %+v", f, r)
	}
	if f.RejectedDPs != 0 {
		t.Errorf("genuine records were rejected: %d", f.RejectedDPs)
	}
	if f.Solved && f.Solution != secret {
		t.Errorf("solved with the wrong x: %d != %d", f.Solution, secret)
	}

	// A line for another job is refused.
	other := strings.Replace(lines[0], "ci ", "ci 1", 1)
	if _, err := forward.ApplyLine(other); err == nil {
		t.Error("a foreign job's check-in was accepted")
	}
	// So is a forged point: same shape, wrong coefficients.
	for _, l := range lines {
		if !strings.Contains(l, "D:") || strings.Contains(l, "D: ") {
			continue
		}
		forged := forgeCoefficient(l)
		if forged == l {
			continue
		}
		oc, err := forward.ApplyLine(forged)
		if err != nil {
			continue // refused outright, also fine
		}
		if oc.RejectedDPs == 0 && oc.AcceptedDPs > 0 {
			t.Error("a forged point was accepted")
		}
		break
	}
}

// forgeCoefficient bumps the `a` of the first distinguished point in a
// check-in line, which must make a*G + b*H stop matching the point.
func forgeCoefficient(line string) string {
	i := strings.Index(line, "D:")
	if i < 0 {
		return line
	}
	rest := line[i+2:]
	end := strings.Index(rest, ";")
	if end < 0 {
		return line
	}
	fields := strings.Split(rest[:end], ",")
	if len(fields) != 8 {
		return line
	}
	fields[6] = "1"
	return line[:i+2] + strings.Join(fields, ",") + rest[end:]
}

func TestDeltaAndLog(t *testing.T) {
	_, ctx, _ := testJob(t, 8080)
	a, err := ca.NewState(ctx)
	if err != nil {
		t.Fatal(err)
	}
	defer a.Close()
	if _, err := ca.RunLane(ctx, a, ca.LaneParams{Peer: "a.0", MaxWalkers: 16, CheckinEvery: 4}); err != nil {
		t.Fatalf("lane: %v", err)
	}

	all := a.DeltaFrom(ca.VersionVector{})
	if len(all) != a.LogLen() {
		t.Errorf("the empty vector is owed the whole log: %d != %d", len(all), a.LogLen())
	}
	// Owed nothing once the vectors agree -- the property that makes one
	// round trip enough.
	if got := a.DeltaFrom(a.VersionVector()); len(got) != 0 {
		t.Errorf("still owed %d entries after matching vectors", len(got))
	}
	// Partial knowledge is owed exactly the tail.
	vv := a.VersionVector()
	full := vv["a.0"]
	vv["a.0"] = full - 1
	if got := a.DeltaFrom(vv); len(got) != 1 {
		t.Errorf("a vector one behind is owed one entry, got %d", len(got))
	}
	if e, ok := a.LogAt(0); !ok || e.Peer != "a.0" || e.Seq == 0 || !strings.HasPrefix(e.Line, "ci ") {
		t.Errorf("log entry 0 is wrong: %+v ok=%v", e, ok)
	}
	if _, ok := a.LogAt(a.LogLen()); ok {
		t.Error("reading past the end of the log succeeded")
	}
}

func TestLogScansPreserveCopiesAcrossMultiplePeers(t *testing.T) {
	_, ctx, _ := testJob(t, 9090)

	maxPeer := strings.Repeat("m", ca.PeerMax-1)
	sharedPrefix := strings.Repeat("s", ca.PeerMax-2)
	peers := []string{
		maxPeer,
		"a",
		sharedPrefix + "x",
		"b",
		sharedPrefix + "y",
	}
	streams := make([][]string, 0, len(peers))
	expected := ca.VersionVector{}
	for _, peer := range peers {
		source, err := ca.NewState(ctx)
		if err != nil {
			t.Fatalf("source state: %v", err)
		}
		var stream []string
		if _, err := ca.RunLane(ctx, source, ca.LaneParams{
			Peer: peer, MaxWalkers: 8, CheckinEvery: 2,
		}); err != nil {
			source.Close()
			t.Fatalf("lane %s: %v", peer, err)
		}
		for i := 0; i < source.LogLen(); i++ {
			entry, ok := source.LogAt(i)
			if !ok {
				source.Close()
				t.Fatalf("source %s has no entry %d", peer, i)
			}
			stream = append(stream, entry.Line)
			if entry.Seq > expected[entry.Peer] {
				expected[entry.Peer] = entry.Seq
			}
		}
		streams = append(streams, stream)
		source.Close()
	}
	if len(expected) != len(peers) {
		t.Fatalf("fixture version vector has %d peers, want %d", len(expected), len(peers))
	}

	state, err := ca.NewState(ctx)
	if err != nil {
		t.Fatalf("state: %v", err)
	}
	// Round-robin insertion makes every scan reuse one scratch buffer across
	// alternating maximum-length, short, and shared-prefix peer names.  A key
	// made directly from stale scratch bytes would split the short peers.
	var encoded []string
	for index := 0; ; index++ {
		added := false
		for streamIndex, stream := range streams {
			if index >= len(stream) {
				continue
			}
			line := stream[index]
			if _, err := state.ApplyLine(line); err != nil {
				state.Close()
				t.Fatalf("apply stream %d entry %d: %v", streamIndex, index, err)
			}
			encoded = append(encoded, line)
			added = true
		}
		if !added {
			break
		}
	}
	first, ok := state.LogAt(0)
	if !ok {
		state.Close()
		t.Fatal("missing first merged entry")
	}
	firstCopy := first

	if got := state.VersionVector(); !reflect.DeepEqual(got, expected) {
		state.Close()
		t.Fatalf("version vector = %v, want %v", got, expected)
	}
	all, reached := state.DeltaSince(ca.VersionVector{})
	if len(all) != len(encoded) || !reflect.DeepEqual(reached, expected) {
		state.Close()
		t.Fatalf("full delta: lines=%d/%d reached=%v want=%v", len(all), len(encoded), reached, expected)
	}
	allCopy := append([]string(nil), all...)

	// Caller-supplied vector keys are arbitrary Go strings, whereas log peers
	// are validated C peer names.  In particular, an embedded-NUL key must not
	// alias the valid short peer when the transient scan key is constructed.
	foreign := ca.VersionVector{"a\x00": ^uint64(0)}
	foreignLines, foreignReached := state.DeltaSince(foreign)
	wantForeignReached := ca.VersionVector{"a\x00": ^uint64(0)}
	for peer, seq := range expected {
		wantForeignReached[peer] = seq
	}
	if len(foreignLines) != len(encoded) || !reflect.DeepEqual(foreignReached, wantForeignReached) {
		state.Close()
		t.Fatalf("foreign-key delta: lines=%d/%d reached=%v want=%v",
			len(foreignLines), len(encoded), foreignReached, wantForeignReached)
	}

	known := ca.VersionVector{}
	for peer, seq := range expected {
		known[peer] = seq
	}
	known["a"]--
	missing, reached := state.DeltaSince(known)
	if len(missing) != 1 || !reflect.DeepEqual(reached, expected) {
		state.Close()
		t.Fatalf("one-behind delta: lines=%d reached=%v want=%v", len(missing), reached, expected)
	}
	if !reflect.DeepEqual(all, allCopy) || first != firstCopy {
		state.Close()
		t.Fatal("a later scan mutated strings returned by an earlier scan")
	}

	state.Close()
	if _, ok := state.LogAt(0); ok {
		t.Fatal("LogAt succeeded after Close")
	}
}

func TestLogScansConcurrentApplyAndClose(t *testing.T) {
	_, ctx, _ := testJob(t, 9191)

	source, err := ca.NewState(ctx)
	if err != nil {
		t.Fatalf("source state: %v", err)
	}
	if _, err := ca.RunLane(ctx, source, ca.LaneParams{
		Peer: "writer.0", MaxWalkers: 128, CheckinEvery: 1,
	}); err != nil {
		source.Close()
		t.Fatalf("source lane: %v", err)
	}
	encoded := source.DeltaFrom(ca.VersionVector{})
	expected := source.VersionVector()
	source.Close()
	if len(encoded) < 32 {
		t.Fatalf("fixture produced only %d entries", len(encoded))
	}
	if len(expected) != 1 || expected["writer.0"] == 0 {
		t.Fatalf("fixture version vector = %v, want one nonzero peer", expected)
	}

	state, err := ca.NewState(ctx)
	if err != nil {
		t.Fatalf("state: %v", err)
	}

	// ApplyLine and the scans all hold the lifetime lock for reading.  Their C
	// calls serialize on the C lock, while each scan retains the immutable log
	// prefix length it observed at its start.
	scanStarted := make(chan struct{})
	writeDone := make(chan struct{})
	scanDone := make(chan struct{})
	go func() {
		defer close(scanDone)
		_ = state.VersionVector()
		close(scanStarted)
		for {
			select {
			case <-writeDone:
				return
			default:
				known := state.VersionVector()
				state.DeltaSince(known)
			}
		}
	}()
	<-scanStarted
	for i, line := range encoded {
		if _, err := state.ApplyLine(line); err != nil {
			close(writeDone)
			<-scanDone
			state.Close()
			t.Fatalf("apply entry %d: %v", i, err)
		}
	}
	close(writeDone)
	<-scanDone

	if got := state.VersionVector(); !reflect.DeepEqual(got, expected) {
		state.Close()
		t.Fatalf("version vector after concurrent writes = %v, want %v", got, expected)
	}
	if lines, reached := state.DeltaSince(ca.VersionVector{}); len(lines) != len(encoded) || !reflect.DeepEqual(reached, expected) {
		state.Close()
		t.Fatalf("delta after concurrent writes: lines=%d/%d reached=%v want=%v", len(lines), len(encoded), reached, expected)
	}

	// Keep readers and a duplicate writer active while Close takes the
	// exclusive lifetime lock.  Close must wait for an in-flight scan/C call,
	// and every later operation must observe the nil pointer rather than use
	// freed C storage.  The race/checkptr runs exercise this path directly.
	const readers = 4
	stop := make(chan struct{})
	ready := make(chan struct{}, readers+1)
	var workers sync.WaitGroup
	for i := 0; i < readers; i++ {
		workers.Add(1)
		go func() {
			defer workers.Done()
			_ = state.VersionVector()
			ready <- struct{}{}
			for {
				select {
				case <-stop:
					return
				default:
					state.DeltaSince(expected)
				}
			}
		}()
	}
	workers.Add(1)
	go func() {
		defer workers.Done()
		_, _ = state.ApplyLine(encoded[0])
		ready <- struct{}{}
		for {
			select {
			case <-stop:
				return
			default:
				if _, err := state.ApplyLine(encoded[0]); err != nil {
					return
				}
			}
		}
	}()
	for i := 0; i < readers+1; i++ {
		<-ready
	}

	state.Close()
	close(stop)
	workers.Wait()
	if got := state.VersionVector(); len(got) != 0 {
		t.Fatalf("version vector after Close = %v, want empty", got)
	}
	if lines, reached := state.DeltaSince(expected); len(lines) != 0 || !reflect.DeepEqual(reached, expected) {
		t.Fatalf("delta after Close: lines=%v reached=%v, want no lines and %v", lines, reached, expected)
	}
}
