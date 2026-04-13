# IMO-Bench Eval

A reproduction and evaluation framework for
[IMO-Bench](https://imobench.github.io) — the benchmark suite proposed in
*[Towards Robust Mathematical Reasoning](https://arxiv.org/abs/2511.01846)*
(Luong et al., EMNLP 2025, Google DeepMind).

The [original repository](https://github.com/google-deepmind/superhuman) only
releases the benchmark **data** (CSV files) without any evaluation code or
tooling. This project provides a **complete, reproducible evaluation pipeline**
and addresses several issues found in the upstream repository:

### Issues Addressed

| Issue | Description | Status |
|-------|-------------|--------|
| [Data bug (upstream #13)](https://github.com/google-deepmind/superhuman/issues/13) | `imo-bench-algebra-036` in `answerbench_v2.csv` has misaligned columns — a missing CSV quote delimiter in a multi-line LaTeX field causes Short Answer, Category, Subcategory, and Source to all shift by one column | **Fixed** |
| [No autograder prompts (upstream #2)](https://github.com/google-deepmind/superhuman/issues/2) | The AnswerAutoGrader and ProofAutoGrader prompt templates are only in the paper appendix, not in the repository | **Included** in `eval/prompts.py` |
| [No evaluation harness (upstream #11)](https://github.com/google-deepmind/superhuman/pull/11) | No standardized tooling for running evaluations end-to-end; researchers must build their own pipeline | **Implemented** for all 3 benchmarks |
| [No difficulty labels for AnswerBench (upstream #4)](https://github.com/google-deepmind/superhuman/issues/4) | `answerbench_v2.csv` lacks per-problem difficulty levels (unlike `proofbench.csv`) | Noted, awaiting upstream |
| Non-benchmark content in repo | Original repo mixes IMO-Bench with Aletheia (math research agent) and AlphaGeometry projects | **Removed** — this repo is focused solely on IMO-Bench evaluation |

## Benchmarks

| Benchmark | Size | Task | Metric |
|-----------|------|------|--------|
| **IMO-AnswerBench** | 400 problems | Solve and get the correct short answer | Accuracy (%) |
| **IMO-ProofBench** | 60 problems | Write a rigorous mathematical proof | Score (0-7 per problem) |
| **IMO-GradingBench** | 1000 examples | Grade a given proof | Accuracy & MAE |

## Setup

```bash
conda create -n imo_bench python=3.11 -y
conda activate imo_bench
pip install -r requirements.txt
```

## Usage

All evaluations are run via `python -m eval.cli` from the repo root. The script
uses **curl** for API calls (compatible with any OpenAI-format endpoint) and
supports **checkpoint/resume** — you can interrupt at any time and re-run the
same command to continue from where you left off.

### IMO-AnswerBench

The model solves 400 short-answer problems. An autograder (LLM-based, following
the paper's AnswerAutoGrader prompt) checks semantic equivalence against ground
truth.

```bash
python -m eval.cli answerbench \
    --model gemini-2.5-pro \
    --api-key YOUR_KEY \
    --base-url http://your-api:port/v1
```

### IMO-ProofBench

The model writes complete proofs for 60 problems. A ProofAutoGrader (LLM-based,
with reference solutions and grading guidelines) scores each proof on the IMO
0-7 scale.

```bash
python -m eval.cli proofbench \
    --model gemini-2.5-pro \
    --grader-model gemini-2.5-pro \
    --api-key YOUR_KEY \
    --base-url http://your-api:port/v1
```

### IMO-GradingBench

Tests the model's ability to grade proofs. The model receives a problem and a
candidate solution, and must classify it as correct/almost/partial/incorrect.
Results are compared against 1000 human expert grades.

```bash
python -m eval.cli gradingbench \
    --model gemini-2.5-pro \
    --api-key YOUR_KEY \
    --base-url http://your-api:port/v1
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--model` | Model ID for solving / grading | (required) |
| `--grader-model` | Model for autograding (AnswerBench/ProofBench) | same as `--model` |
| `--api-key` | API key | (required) |
| `--base-url` | OpenAI-compatible API base URL | (required) |
| `--checkpoint` | Custom checkpoint file path | auto-generated |
| `--temperature` | Sampling temperature for solve model | 0.7 |
| `--limit N` | Only evaluate first N problems (for testing) | all |

### Checkpoint / Resume

Each completed step (solve or grade) is saved to a JSON checkpoint file
immediately. If the process is interrupted, simply re-run the same command — it
will skip all completed problems and continue from where it left off.

Checkpoint files are named `ckpt_<benchmark>_<model>.json` by default.

## Evaluation Pipeline

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Load Data   │───▶│  Model Solve │───▶│  AutoGrader  │───▶ Results
│  (CSV)       │    │  (API call)  │    │  (API call)  │
└──────────────┘    └──────────────┘    └──────────────┘
                          │                    │
                     checkpoint            checkpoint
                      (solve)               (grade)
```

- **AnswerBench**: Solve → AnswerAutoGrader (extracts & compares final answers)
- **ProofBench**: Solve → ProofAutoGrader (scores proof with reference solution + rubric)
- **GradingBench**: Grade only (model acts as the grader, compared to human labels)

## Project Structure

```
.
├── eval/                    # Evaluation framework
│   ├── cli.py               # Command-line interface
│   ├── runners.py           # Benchmark runners (answerbench/proofbench/gradingbench)
│   ├── api.py               # API client (curl-based)
│   ├── checkpoint.py        # Checkpoint/resume manager
│   ├── data.py              # CSV data loaders
│   ├── parsers.py           # Output parsers for autograder responses
│   └── prompts.py           # Prompt templates from the paper
├── imobench/                # Benchmark data
│   ├── answerbench_v2.csv   # 400 short-answer problems (fixed)
│   ├── proofbench.csv       # 60 proof-based problems
│   ├── gradingbench.csv     # 1000 human-graded solutions
│   └── imgs/                # Figures from the paper
├── requirements.txt
└── README.md
```

## Citing

```bibtex
@inproceedings{luong-etal-2025-towards,
    title = "Towards Robust Mathematical Reasoning",
    author  = {Thang Luong and Dawsen Hwang and Hoang H. Nguyen and Golnaz Ghiasi and Yuri Chervonyi and Insuk Seo and Junsu Kim and Garrett Bingham and Jonathan Lee and Swaroop Mishra and Alex Zhai and Clara Huiyi Hu and Henryk Michalewski and Jimin Kim and Jeonghyun Ahn and Junhwi Bae and Xingyou Song and Trieu H. Trinh and Quoc V. Le and Junehyuk Jung},
    booktitle = "Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing",
    year = "2025",
    url = "https://aclanthology.org/2025.emnlp-main.1794/",
}
```

## License

Data and benchmark materials: [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode).
Evaluation code: [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0).
