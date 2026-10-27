# Independent validator sign correction

The first invocation of `python3 validate.py` exited 1 at the assertion
checking the transported neighbor sum. Its source compared that sum with
`2*target`. The degree-7 Hecke coefficient on `11a1` is `a_7=-2`, so the
correct comparator is `-2*target`. The assertion was corrected in
`validate.py` before the successful replay. The initial stderr was
overwritten by the rerun; the observed exception was:

```
File "validate.py", line 89, in main
    assert acc == add(pts[67], pts[67])
AssertionError
```

The corrected run exited 0 and saved `validation.json`; the Sage
diagnostic separately checked the same group sum against `a_7*target`.
