# Matrix-screen launcher correction

The first matrix-screen freeze invocation used system `python3` and stopped
at import because that interpreter lacks `psutil`. The raw stdout/stderr
are `matrix_freeze_attempt1.*`. It created no matrix protocol or solver
process. The unchanged script was then frozen through the checked repository
`./sage -python` launcher and both frozen solver arms completed.
