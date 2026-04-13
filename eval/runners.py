"""
Evaluation runners for all three IMO-Bench benchmarks.
Two-phase concurrent execution: Phase 1 (solve) → Phase 2 (grade).
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

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


def _run_parallel(tasks, fn, max_workers, label=""):
    """Run tasks concurrently, printing progress."""
    total = len(tasks)
    if total == 0:
        print(f"  {label}: nothing to do (all cached)")
        return

    done_count = 0
    print(f"  {label}: {total} tasks, concurrency={max_workers}")

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(fn, t): t for t in tasks}
        for future in as_completed(futures):
            done_count += 1
            task = futures[future]
            try:
                result_msg = future.result()
                print(f"  [{done_count}/{total}] {result_msg}")
            except Exception as e:
                pid = task.get("pid", task.get("gid", "?"))
                print(f"  [{done_count}/{total}] {pid} ERROR: {e}")


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
    workers = args.concurrency

    done_s = sum(1 for p in problems if ckpt.is_done(p["Problem ID"], "solve"))
    done_g = sum(1 for p in problems if ckpt.is_done(p["Problem ID"], "grade"))
    _header("IMO-AnswerBench", [
        f"Solve model:  {args.model}",
        f"Grader model: {args.grader_model}",
        f"Problems:     {total}  (concurrency: {workers})",
        f"Checkpoint:   {done_s} solved, {done_g} graded",
    ])

    # Phase 1: Solve
    solve_tasks = []
    for p in problems:
        pid = p["Problem ID"]
        if not ckpt.is_done(pid, "solve"):
            solve_tasks.append({"pid": pid, "problem": p["Problem"]})

    def do_solve(t):
        prompt = SOLVE_PROMPT.format(problem=t["problem"])
        resp = call_api(args.base_url, args.api_key, args.model,
                        prompt, temperature=args.temperature)
        ckpt.set_result(t["pid"], "solve", resp)
        return f"{t['pid']} solved"

    _run_parallel(solve_tasks, do_solve, workers, "Phase 1: Solve")

    # Phase 2: Grade
    grade_tasks = []
    for p in problems:
        pid = p["Problem ID"]
        if not ckpt.is_done(pid, "grade"):
            grade_tasks.append({
                "pid": pid,
                "problem": p["Problem"],
                "answer": p["Short Answer"],
            })

    def do_grade(t):
        response = ckpt.get_result(t["pid"], "solve")
        prompt = ANSWER_AUTOGRADER_PROMPT.format(
            problem=t["problem"], response=response, answer=t["answer"]
        )
        grade_resp = call_api(args.base_url, args.api_key, args.grader_model,
                              prompt, temperature=0.0)
        verdict = parse_answer_grade(grade_resp)
        ckpt.set_result(t["pid"], "grade", {"raw": grade_resp, "verdict": verdict})
        mark = "✓" if verdict == "Correct" else "✗"
        return f"{t['pid']} {mark} ({verdict})"

    _run_parallel(grade_tasks, do_grade, workers, "Phase 2: Grade")

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
    workers = args.concurrency

    done_s = sum(1 for p in problems if ckpt.is_done(p["Problem ID"], "solve"))
    done_g = sum(1 for p in problems if ckpt.is_done(p["Problem ID"], "grade"))
    _header("IMO-ProofBench", [
        f"Solve model:  {args.model}",
        f"Grader model: {args.grader_model}",
        f"Problems:     {total}  (concurrency: {workers})",
        f"Checkpoint:   {done_s} solved, {done_g} graded",
    ])

    # Phase 1: Solve
    solve_tasks = []
    for p in problems:
        pid = p["Problem ID"]
        if not ckpt.is_done(pid, "solve"):
            solve_tasks.append({"pid": pid, "problem": p["Problem"]})

    def do_solve(t):
        prompt = SOLVE_PROOF_PROMPT.format(problem=t["problem"])
        resp = call_api(args.base_url, args.api_key, args.model,
                        prompt, temperature=args.temperature)
        ckpt.set_result(t["pid"], "solve", resp)
        return f"{t['pid']} solved"

    _run_parallel(solve_tasks, do_solve, workers, "Phase 1: Solve")

    # Phase 2: Grade
    grade_tasks = []
    for p in problems:
        pid = p["Problem ID"]
        if not ckpt.is_done(pid, "grade"):
            grade_tasks.append({
                "pid": pid,
                "problem": p["Problem"],
                "solution": p["Solution"],
                "guidelines": p["Grading guidelines"],
            })

    def do_grade(t):
        response = ckpt.get_result(t["pid"], "solve")
        prompt = PROOF_AUTOGRADER_PROMPT.format(
            problem=t["problem"], solution=t["solution"],
            guidelines=t["guidelines"], response=response
        )
        grade_resp = call_api(args.base_url, args.api_key, args.grader_model,
                              prompt, temperature=0.0)
        score = parse_proof_score(grade_resp)
        ckpt.set_result(t["pid"], "grade", {"raw": grade_resp, "score": score})
        return f"{t['pid']} score: {score}/7"

    _run_parallel(grade_tasks, do_grade, workers, "Phase 2: Grade")

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
    workers = args.concurrency

    done = sum(1 for p in problems if ckpt.is_done(p["Grading ID"], "grade"))
    _header("IMO-GradingBench", [
        f"Model:      {args.model}",
        f"Examples:   {total}  (concurrency: {workers})",
        f"Checkpoint: {done} graded",
    ])

    grade_tasks = []
    for p in problems:
        gid = p["Grading ID"]
        if not ckpt.is_done(gid, "grade"):
            human_points = int(p["Points"])
            grade_tasks.append({
                "gid": gid,
                "problem": p["Problem"],
                "solution": p["Response"],
                "human_points": human_points,
                "human_label": POINTS_TO_GRADE.get(human_points, "incorrect"),
            })

    def do_grade(t):
        prompt = GRADING_BENCH_PROMPT.format(
            problem=t["problem"], response=t["solution"]
        )
        resp = call_api(args.base_url, args.api_key, args.model,
                        prompt, temperature=0.0)
        pred_label = parse_grading_label(resp)
        ckpt.set_result(t["gid"], "grade", {
            "raw": resp, "pred_label": pred_label,
            "human_points": t["human_points"], "human_label": t["human_label"],
        })
        match = "✓" if pred_label == t["human_label"] else "✗"
        return f"{t['gid']} {match} pred={pred_label} human={t['human_label']}"

    _run_parallel(grade_tasks, do_grade, workers, "Grading")

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
