# IMO-Bench Data

Benchmark datasets from [IMO-Bench](https://imobench.github.io).

| File | Description | Size |
|------|-------------|------|
| `answerbench_v2.csv` | Short-answer problems (v2, with data fix) | 400 problems |
| `proofbench.csv` | Proof-based problems with solutions & grading guidelines | 60 problems |
| `gradingbench.csv` | Human-graded model solutions for proof evaluation | 1000 examples |

## Data Fix

`imo-bench-algebra-036` in `answerbench_v2.csv` had a CSV formatting bug (missing
closing quote in a multi-line LaTeX field) that caused column misalignment. This has
been fixed in this fork. See [upstream issue #13](https://github.com/google-deepmind/superhuman/issues/13).
