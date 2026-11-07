# D39 visual report artifacts

`report.typ` is the editable Typst source. It embeds `d39-evidence-map.svg`, a vector schematic derived from the frozen audit JSON records. Compile with:

```sh
typst compile report.typ report.pdf
```

The SVG is an evidence-flow schematic, not a literal map of rational points, isogenies, or ideal-class orbits. The report uses only the frozen experiment and audit records linked from its final section; it does not rerun any producer or audit.
