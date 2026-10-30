# Retrospective Hecke rank-source compression protocol

This is an exhaustive audit of the already generated D79 relation pools at p63317 and p68437. A read-only pilot identified a five-source p63317 witness before this protocol was frozen; the result is retrospective and cannot be used as a prospective source-selection timing claim.

For each prime, form the 40-column relation matrix over its recorded largest-order prime field from all pinned base rows and direct candidates. Retain the baseline rank. Reduce each indexed Hecke candidate row modulo that baseline, then compute the full rank with all Hecke candidates. For a rank gain of one, search every singleton candidate. For a gain of two, search every candidate pair; record every rank-increasing pair's union of the four source IDs per row. Minimize first the source-union size, then sorted source union, then candidate index pair. Retain tested pair count, count of four-source-union pairs and their rank, and the selected row identities. Do not infer a measured cost reduction from retrospective selection.

Independently, through the repository's checked Sage launcher, rebuild the matrices over the exact prime fields, check the selected rows as group relations on the p63317 curve, check baseline and selected ranks, and solve the p63317 anchored log system from the compressed rows. Compare every recovered log with the pinned full-pool solution. Record p68437's remaining rank deficit explicitly.

The witness source-lift times can be summed from pinned source receipts as a component accounting diagnostic. The full-pool discovery and direct-row enumeration were already paid in this experiment, so the witness-only sum is not an end-to-end runtime.
