# Frozen unified diff format classification

The complete claimed literal-derivative.diff must retain its standard
unified-diff context prefix. A blank context line is one literal space;
trimming it would change the claimed diff and its frozen replay hash.
Use a new norm-assisted-ic/.gitattributes with ONLY the exact path rule
literal-derivative.diff whitespace=-blank-at-eol. Preserve all .rs source,
the diff bytes and all784 replay inputs. The unchanged Git whitespace
checker still checks every source file and every other whitespace class.
This classifies data syntax,not a source-code whitespace exception or
a mathematical/CI acceptance waiver. [pcc:unverified]
