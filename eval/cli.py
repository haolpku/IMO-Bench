"""
Command-line interface for IMO-Bench evaluation.
"""

import argparse
from .runners import run_answerbench, run_proofbench, run_gradingbench


def main():
    parser = argparse.ArgumentParser(
        description="IMO-Bench Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # AnswerBench (400 short-answer problems)
  python -m eval.cli answerbench --model gemini-2.5-pro

  # ProofBench (60 proof problems), use a strong grader
  python -m eval.cli proofbench --model gemini-3.1-pro-preview --grader-model gemini-2.5-pro

  # GradingBench (1000 proof-grading examples)
  python -m eval.cli gradingbench --model gemini-2.5-pro

  # Quick test with first 5 problems
  python -m eval.cli answerbench --model gemini-2.5-flash --limit 5

  # Custom API endpoint
  python -m eval.cli answerbench --model gpt-4o \\
      --base-url https://api.openai.com/v1 --api-key sk-xxx
        """
    )
    parser.add_argument("benchmark",
                        choices=["answerbench", "proofbench", "gradingbench"],
                        help="Which benchmark to evaluate")
    parser.add_argument("--model", required=True,
                        help="Model ID for solving (answerbench/proofbench) or grading (gradingbench)")
    parser.add_argument("--grader-model", default=None,
                        help="Model for autograding (default: same as --model). "
                             "Paper recommends gemini-2.5-pro.")
    parser.add_argument("--api-key", required=True,
                        help="API key for the endpoint")
    parser.add_argument("--base-url", required=True,
                        help="API base URL (e.g. http://host:port/v1)")
    parser.add_argument("--checkpoint", default=None,
                        help="Checkpoint file path (auto-generated if not set)")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Temperature for the solve model (default: 0.7)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only evaluate first N problems (for testing)")

    args = parser.parse_args()
    if args.grader_model is None:
        args.grader_model = args.model

    runners = {
        "answerbench": run_answerbench,
        "proofbench": run_proofbench,
        "gradingbench": run_gradingbench,
    }
    runners[args.benchmark](args)


if __name__ == "__main__":
    main()
