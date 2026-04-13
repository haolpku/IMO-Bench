"""
Evaluation runners for all three IMO-Bench benchmarks.
Each runner handles: model inference -> autograding -> summary reporting.
"""

from .api import call_api
from .checkpoint import CheckpointManager
from .data import load_answerbench, load_proofbench, load_gradingbench
from .parsers import (
    parse_answer_grade, parse_proof_score, parse_grading_label,
    GRADE_TO_POINTS, POINTS_TO_GRADE,
)
from .prompts import (
    SOLVE_PROMPT, SOLVE_PROOF_PROMPT,
    ANSWER_AUTOGRADER_PROMPT, PROOF_AUTOGRADER_PROMPT, GRADING_BENCH_PROMPT,
)


def _header(title: str, lines: list[str]):
    print(f"\n{'='*60}")
    print(f"  {title}")
    for line in lines:
        print(f"  {line}")
    print(f"{'='*60}\n")


# ──────────────────────────────────────────────
# IMO-AnswerBench
# ──────────────────────────────────────────────

def run_answerbench(args):
    ckpt = CheckpointManager(
        args.checkpoint or f"ckpt_answerbench_{args.model.replace('/', '_')}.json"
    )
    ckpt.set_metadata("benchmark", "answerbench")
    ckpt.set_metadata("solve_model", args.model)
    ckpt.set_metadata("grader_model", args.grader_model)

    problems = load_answerbench()
    if args.limit:
        problems = problems[:args.limit]
    total = len(problems)

    done_s = sum(1 for p in problems if ckpt.is_done(p["Problem ID"], "solve"))
    done_g = sum(1 for p in problems if ckpt.is_done(p["Problem ID"], "grade"))
    _header("IMO-AnswerBench", [
        f"Solve model:  {args.model}",
        f"Grader model: {args.grader_model}",
        f"Problems:     {total}",
        f"Checkpoint:   {done_s} solved, {done_g} graded",
    ])

    for i, prob in enumerate(problems):
        pid = prob["Problem ID"]
        problem_text = prob["Problem"]
        golden_answer = prob["Short Answer"]

        # Stage 1: solve
        if not ckpt.is_done(pid, "solve"):
            print(f"[{i+1}/{total}] Solving {pid} ...", end=" ", flush=True)
            prompt = SOLVE_PROMPT.format(problem=problem_text)
            response = call_api(args.base_url, args.api_key, args.model,
                                prompt, temperature=args.temperature)
            ckpt.set_result(pid, "solve", response)
            print("done")
        else:
            print(f"[{i+1}/{total}] {pid} solve: cached")

        # Stage 2: grade
        if not ckpt.is_done(pid, "grade"):
            response = ckpt.get_result(pid, "solve")
            print(f"[{i+1}/{total}] Grading {pid} ...", end=" ", flush=True)
            grade_prompt = ANSWER_AUTOGRADER_PROMPT.format(
                problem=problem_text, response=response, answer=golden_answer
            )
            grade_resp = call_api(args.base_url, args.api_key, args.grader_model,
                                  grade_prompt, temperature=0.0)
            verdict = parse_answer_grade(grade_resp)
            ckpt.set_result(pid, "grade", {"raw": grade_resp, "verdict": verdict})
            mark = "✓" if verdict == "Correct" else "✗"
            print(f"{mark} ({verdict})")
        else:
            cached = ckpt.get_result(pid, "grade")
            mark = "✓" if cached["verdict"] == "Correct" else "✗"
            print(f"[{i+1}/{total}] {pid} grade: cached {mark}")

    _print_answerbench_summary(ckpt, problems)


def _print_answerbench_summary(ckpt, problems):
    cat_stats = {}
    total_correct, total_graded = 0, 0

    for prob in problems:
        pid, cat = prob["Problem ID"], prob["Category"]
        grade = ckpt.get_result(pid, "grade")
        if not grade:
            continue
        total_graded += 1
        ok = grade["verdict"] == "Correct"
        if ok:
            total_correct += 1
        s = cat_stats.setdefault(cat, {"correct": 0, "total": 0})
        s["total"] += 1
        if ok:
            s["correct"] += 1

    print(f"\n{'='*60}")
    print(f"  IMO-AnswerBench Results")
    print(f"  Solve: {ckpt.metadata.get('solve_model')}  |  Grader: {ckpt.metadata.get('grader_model')}")
    print(f"{'─'*60}")
    for cat in sorted(cat_stats):
        s = cat_stats[cat]
        pct = s["correct"] / s["total"] * 100 if s["total"] else 0
        print(f"  {cat:20s}  {s['correct']:3d}/{s['total']:3d}  ({pct:.1f}%)")
    print(f"{'─'*60}")
    pct = total_correct / total_graded * 100 if total_graded else 0
    print(f"  {'Overall':20s}  {total_correct:3d}/{total_graded:3d}  ({pct:.1f}%)")
    print(f"{'='*60}\n")


# ──────────────────────────────────────────────
# IMO-ProofBench
# ──────────────────────────────────────────────

def run_proofbench(args):
    ckpt = CheckpointManager(
        args.checkpoint or f"ckpt_proofbench_{args.model.replace('/', '_')}.json"
    )
    ckpt.set_metadata("benchmark", "proofbench")
    ckpt.set_metadata("solve_model", args.model)
    ckpt.set_metadata("grader_model", args.grader_model)

    problems = load_proofbench()
    if args.limit:
        problems = problems[:args.limit]
    total = len(problems)

    done_s = sum(1 for p in problems if ckpt.is_done(p["Problem ID"], "solve"))
    done_g = sum(1 for p in problems if ckpt.is_done(p["Problem ID"], "grade"))
    _header("IMO-ProofBench", [
        f"Solve model:  {args.model}",
        f"Grader model: {args.grader_model}",
        f"Problems:     {total}",
        f"Checkpoint:   {done_s} solved, {done_g} graded",
    ])

    for i, prob in enumerate(problems):
        pid = prob["Problem ID"]
        problem_text = prob["Problem"]
        ref_solution = prob["Solution"]
        guidelines = prob["Grading guidelines"]

        if not ckpt.is_done(pid, "solve"):
            print(f"[{i+1}/{total}] Solving {pid} ...", end=" ", flush=True)
            prompt = SOLVE_PROOF_PROMPT.format(problem=problem_text)
            response = call_api(args.base_url, args.api_key, args.model,
                                prompt, temperature=args.temperature)
            ckpt.set_result(pid, "solve", response)
            print("done")
        else:
            print(f"[{i+1}/{total}] {pid} solve: cached")

        if not ckpt.is_done(pid, "grade"):
            response = ckpt.get_result(pid, "solve")
            print(f"[{i+1}/{total}] Grading {pid} ...", end=" ", flush=True)
            grade_prompt = PROOF_AUTOGRADER_PROMPT.format(
                problem=problem_text, solution=ref_solution,
                guidelines=guidelines, response=response
            )
            grade_resp = call_api(args.base_url, args.api_key, args.grader_model,
                                  grade_prompt, temperature=0.0)
            score = parse_proof_score(grade_resp)
            ckpt.set_result(pid, "grade", {"raw": grade_resp, "score": score})
            print(f"score: {score}/7")
        else:
            cached = ckpt.get_result(pid, "grade")
            print(f"[{i+1}/{total}] {pid} grade: cached (score: {cached['score']}/7)")

    _print_proofbench_summary(ckpt, problems)


def _print_proofbench_summary(ckpt, problems):
    basic_score, basic_max = 0, 0
    adv_score, adv_max = 0, 0
    cat_stats = {}

    for prob in problems:
        pid, cat = prob["Problem ID"], prob.get("Category", "")
        grade = ckpt.get_result(pid, "grade")
        if not grade:
            continue
        score = grade["score"]
        if pid.startswith("PB-Basic"):
            basic_score += score
            basic_max += 7
        else:
            adv_score += score
            adv_max += 7
        s = cat_stats.setdefault(cat, {"score": 0, "max": 0})
        s["score"] += score
        s["max"] += 7

    total_s, total_m = basic_score + adv_score, basic_max + adv_max
    print(f"\n{'='*60}")
    print(f"  IMO-ProofBench Results")
    print(f"  Solve: {ckpt.metadata.get('solve_model')}  |  Grader: {ckpt.metadata.get('grader_model')}")
    print(f"{'─'*60}")
    if basic_max:
        print(f"  Basic:    {basic_score}/{basic_max} ({basic_score/basic_max*100:.1f}%)")
    if adv_max:
        print(f"  Advanced: {adv_score}/{adv_max} ({adv_score/adv_max*100:.1f}%)")
    if total_m:
        print(f"  Overall:  {total_s}/{total_m} ({total_s/total_m*100:.1f}%)")
    print(f"{'─'*60}")
    for cat in sorted(cat_stats):
        s = cat_stats[cat]
        pct = s["score"] / s["max"] * 100 if s["max"] else 0
        print(f"  {cat:20s}  {s['score']:3d}/{s['max']:3d}  ({pct:.1f}%)")
    print(f"{'='*60}\n")


# ──────────────────────────────────────────────
# IMO-GradingBench
# ──────────────────────────────────────────────

def run_gradingbench(args):
    ckpt = CheckpointManager(
        args.checkpoint or f"ckpt_gradingbench_{args.model.replace('/', '_')}.json"
    )
    ckpt.set_metadata("benchmark", "gradingbench")
    ckpt.set_metadata("model", args.model)

    problems = load_gradingbench()
    if args.limit:
        problems = problems[:args.limit]
    total = len(problems)

    done = sum(1 for p in problems if ckpt.is_done(p["Grading ID"], "grade"))
    _header("IMO-GradingBench", [
        f"Model:      {args.model}",
        f"Examples:   {total}",
        f"Checkpoint: {done} graded",
    ])

    for i, prob in enumerate(problems):
        gid = prob["Grading ID"]
        problem_text = prob["Problem"]
        solution_text = prob["Response"]
        human_points = int(prob["Points"])
        human_label = POINTS_TO_GRADE.get(human_points, "incorrect")

        if not ckpt.is_done(gid, "grade"):
            print(f"[{i+1}/{total}] Grading {gid} ...", end=" ", flush=True)
            prompt = GRADING_BENCH_PROMPT.format(
                problem=problem_text, response=solution_text
            )
            resp = call_api(args.base_url, args.api_key, args.model,
                            prompt, temperature=0.0)
            pred_label = parse_grading_label(resp)
            ckpt.set_result(gid, "grade", {
                "raw": resp, "pred_label": pred_label,
                "human_points": human_points, "human_label": human_label,
            })
            match = "✓" if pred_label == human_label else "✗"
            print(f"{match} pred={pred_label} human={human_label}")
        else:
            cached = ckpt.get_result(gid, "grade")
            match = "✓" if cached["pred_label"] == cached["human_label"] else "✗"
            print(f"[{i+1}/{total}] {gid}: cached {match}")

    _print_gradingbench_summary(ckpt, problems)


def _print_gradingbench_summary(ckpt, problems):
    total, correct, total_mae = 0, 0, 0

    for prob in problems:
        gid = prob["Grading ID"]
        grade = ckpt.get_result(gid, "grade")
        if not grade:
            continue
        total += 1
        if grade["pred_label"] == grade["human_label"]:
            correct += 1
        pred_pts = GRADE_TO_POINTS.get(grade["pred_label"], 0)
        total_mae += abs(pred_pts - grade["human_points"])

    print(f"\n{'='*60}")
    print(f"  IMO-GradingBench Results")
    print(f"  Model: {ckpt.metadata.get('model')}")
    print(f"{'─'*60}")
    if total:
        print(f"  Accuracy:  {correct}/{total} ({correct/total*100:.1f}%)")
        print(f"  MAE:       {total_mae/total/7*100:.1f}%")
    else:
        print("  No results yet.")
    print(f"{'='*60}\n")
