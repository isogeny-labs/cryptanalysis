#!/usr/bin/env python3
"""Derive the closure + index-lift n=83 producer from its two frozen parents, exactly.

Input: `snapshots/r770/examples/koblitz_orbit_dlp_fast_online_logcache.rs`
(crypto 770f6a69 plus B's `ic_log_cache.patch`, restored and digest-checked
by `restore.py`).

Both parents derive from the same rank-probe producer
(`make_rankprobe_source.py` and its five verbatim parents, frozen digest
d4394df3..., `koblitz-n83-rankprobe-20261019`, PR #980):

* `make_indexlift_source.py` is `koblitz-n83-indexlift-20261019`'s
  `make_online_source.py` (PR #981, on main), verbatim. Its output must hash
  to the index-lift protocol's frozen `online_source_sha256`
  (`INDEXLIFT_SHA256`, 7df72603...): the producer of run 39290913632, the
  current n = 83 row. It adds `KIC_INDEX_CANON=lift_plant`,
  `KIC_SCAN_SELFTEST` and the two layout digests; `KIC_INDEX_CANON=lift`
  itself is already a runtime selector of the rank-probe producer.
* `make_closure_source.py` is `koblitz-n83-closure-20261019`'s
  `make_online_source.py` (branch claude/n83-closure, frozen commit
  3761fd260, run 39305259093), verbatim. Its output must hash to the closure
  protocol's frozen `online_source_sha256` (`CLOSURE_SHA256`, 8916e034...).
  It adds the Z[tau]-closure header path: four counted replacements
  (`closure_edits`).

This producer is the index-lift producer's text with the closure's four
counted replacements applied to it (`closure_edits`, imported, not
re-typed). No other text changes. The replacements touch none of the text
the index-lift edits touch (each is checked to occur exactly once in the
index-lift text by `replace`), so:

* on B's K600 header (no `orbit_representatives`) the code path is the
  index-lift producer's, token for token;
* on a closure header the code path is the closure producer's plus the
  index-lift producer's runtime options, which the arms set to
  `KIC_INDEX_CANON=lift` and `KIC_SCAN_SELFTEST=full`.

`check_composition()` also verifies that the composed text minus the
closure's inserted text is the index-lift text, and minus the index-lift's
inserted text is the closure text (both by applying the edits the other way
round and comparing after removing the two header comments).

`--check` regenerates and requires byte identity with the existing output.
"""

import argparse
import hashlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_rankprobe_source as rankprobe  # noqa: E402  (koblitz-n83-rankprobe-20261019, verbatim)
import make_indexlift_source as indexlift  # noqa: E402  (koblitz-n83-indexlift-20261019, verbatim)
import make_closure_source as closure  # noqa: E402  (koblitz-n83-closure-20261019 at 3761fd260, verbatim)

EXAMPLES = HERE / "snapshots" / "r770" / "examples"
OUTPUT = EXAMPLES / "koblitz_orbit_dlp_fast_online_closure_indexlift.rs"
RANKPROBE_SHA256 = "d4394df35d065afbfb05022eac3006492239cc64b94de16fba501322cb578bb5"
# protocol.json "sources.online_source_sha256" of koblitz-n83-indexlift-20261019 (PR #981, run 39290913632).
INDEXLIFT_SHA256 = "7df72603a443239fe0c86ea121d34ed67cd36119af83f1969862e68163eb281f"
# protocol.json "sources.online_source_sha256" of koblitz-n83-closure-20261019 (commit 3761fd260, run 39305259093).
CLOSURE_SHA256 = "8916e034b4e24a027079019e4988f1dc6fbf74ec1c2349befa9aa8eea7ce330a"
WIDE_START = rankprobe.WIDE_START
WIDE_END = rankprobe.WIDE_END

HEAD_NOTE_OLD = closure.HEAD_NEW
HEAD_NOTE_NEW = closure.HEAD_NEW + """// koblitz-n83-closure-indexlift-20261019: the index-lift producer with the
// closure's four replacements (make_online_source.py); one binary for every arm.
"""


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def parents():
    base = rankprobe.derive(rankprobe.rankcut_text())
    if sha(base) != RANKPROBE_SHA256:
        raise ValueError("rank-probe derivation differs from its frozen producer: " + sha(base))
    lifted = indexlift.derive(base)
    if sha(lifted) != INDEXLIFT_SHA256:
        raise ValueError("index-lift derivation differs from its frozen producer: " + sha(lifted))
    closed = closure.derive(base)
    if sha(closed) != CLOSURE_SHA256:
        raise ValueError("closure derivation differs from its frozen producer: " + sha(closed))
    return base, lifted, closed


def compose(lifted):
    """closure_edits on the index-lift text, then one header line."""
    text = closure.derive(lifted)
    head, rest = text.split(WIDE_START, 1)
    head = rankprobe.replace(head, HEAD_NOTE_OLD, HEAD_NOTE_NEW)
    return head + WIDE_START + rest


def check_composition(base, lifted, closed, text):
    """The two edit sets commute up to the order of the header comments."""
    other = indexlift.derive(closed)
    strip = lambda t: (t.replace(closure.HEAD_NEW[len(closure.HEAD_OLD):], "")  # noqa: E731
                       .replace(indexlift.HEAD_NEW[len(indexlift.HEAD_OLD):], "")
                       .replace(HEAD_NOTE_NEW[len(HEAD_NOTE_OLD):], ""))
    if strip(other) != strip(text):
        raise ValueError("closure and index-lift edits do not commute")
    if strip(text) == strip(lifted) or strip(text) == strip(closed):
        raise ValueError("composition lost one parent's edits")
    return {"rankprobe_sha256": sha(base), "indexlift_sha256": sha(lifted), "closure_sha256": sha(closed),
            "commutes_up_to_header_comments": True}


def derive():
    base, lifted, closed = parents()
    text = compose(lifted)
    check_composition(base, lifted, closed, text)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = derive()
    if args.check:
        if OUTPUT.read_text() != text:
            raise SystemExit("derived online source differs from " + str(OUTPUT))
    else:
        OUTPUT.write_text(text)
    print("online_source_sha256=" + sha(text))


if __name__ == "__main__":
    sys.exit(main())
