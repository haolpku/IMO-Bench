"""
Autograder prompt templates from the IMO-Bench paper (Appendix A.5 and B.5).
"""

SOLVE_PROMPT = """You are an expert mathematician. Solve the following problem step by step, showing your complete reasoning. Present your final answer clearly at the end.

Problem: {problem}"""

SOLVE_PROOF_PROMPT = """You are an expert mathematician. Write a complete, rigorous proof for the following problem. Your proof should be logically sound, precise, and complete.

Problem: {problem}"""

# Paper Appendix A.5
ANSWER_AUTOGRADER_PROMPT = r"""# System Role: Deterministic Mathematical Autograder
You are a precise, automated grading system. Your sole function is to determine if the final answer provided in the Model Solution is mathematically equivalent to the Golden Answer. You must NOT grade the reasoning or steps, only the final result.

# 1. Grading Guidelines (Equivalence Rules)
Equivalence is mandatory for a correct grade. You must rigorously verify if the answers represent the exact same mathematical value or expression, even if the format differs.
* **Algebraic Equivalence:** e.g., 'n(n+1)/2' is equivalent to 'n^2/2 + n/2'. You must verify the algebra.
* **Numerical Equivalence:** e.g., '1/2' is equivalent to '0.5'; 'sqrt(2)/2' is equivalent to '1/sqrt(2)'.
* **Set/List Equivalence:** Unless specified as an ordered tuple/vector, the order of elements does not matter (e.g., {{1, 2}} is equivalent to {{2, 1}}).
* **Partial Credit:** No partial credit is allowed. If the answer is incomplete or partially incorrect, it is incorrect.
* **No Answers:** If no clear, unambiguous final answer can be extracted, the solution must be graded as incorrect.

# 3. Output Protocol (Strict Compliance Required)
You must execute the task using a two-part structure.

**Part 1: Analysis (Chain-of-Thought)**
You MUST perform your analysis within <thinking></thinking> tags.
1. **Golden Answer:** State the Golden Answer.
2. **Extracted Model Answer:** State the extracted answer.
3. **Equivalence Analysis:** Compare the two answers using the Grading Guidelines.
4. **Conclusion:** State "Correct" or "Incorrect".

**Part 2: Final Grade**
Immediately after </thinking>, output ONLY:
* If Correct: \boxed{{Correct}}
* If Incorrect: \boxed{{Incorrect}}

# 4. Input Data
Problem: {problem}

Model Solution: {response}

Golden Answer: {answer}"""

# Paper Appendix B.5
PROOF_AUTOGRADER_PROMPT = """You are an expert grader for the International Mathematics Olympiad (IMO). Your task is to evaluate a proposed solution strictly and rigorously. Keep in mind the standards at the IMO are extremely high: only arguments that are logically sound, complete, and precise should be rewarded.

### General Scoring Rubric
Scores are assigned on a 0-7 scale. The general guidelines are:
* **7 Points (Correct):** The solution is complete, correct, and fully rigorous. If the submission contains incorrect attempts but ultimately presents a complete and correct solution, it should still be awarded full points.
* **6 Points (Almost Correct):** The solution is almost correct with a sound core argument, but contains minor errors in calculation or small gaps in logic. Missing proofs for major components, unjustified claims, or sketchy arguments are **not** eligible for 6 points.
* **1 Point (Partial Progress):** The solution demonstrates substantial progress explicitly mentioned in the grading guidelines. Initial observations, reformulating the problem without making substantive headway, or proving partial results not mentioned in the grading guidelines are generally **not** eligible for this score.
* **0 Points (Incorrect):** The solution doesn't make substantial progress that is a key step in the full solution or is fundamentally flawed. All partial progress without key results or lacking rigor also fall in this category.

### Input Data and Interpretation
You are provided with the following:
1. **Problem Statement:** The IMO problem.
2. **Ground Truth Solution:** A reference solution. Assume this solution is correct. It demonstrates one valid approach.
3. **Specific Grading Guidelines:** Criteria for awarding credit for this specific problem. These guidelines take precedence over the General Scoring Rubric, especially for partial credit.
4. **Proposed Solution:** The student submission.

### Evaluation Process
You must follow this structured process:
1. **Analyze References:** Meticulously read and understand the problem and Ground Truth Solution, check the Specific Grading Guidelines. Identify the key steps for a complete solution and the criteria for partial credit.
2. **Step-by-Step Verification:** Verify the logical validity and rigor of every step. Identify all flaws, gaps, assumptions, and errors. **Make sure you fully understand every piece of logic behind each step of the proposed solution, you must be careful for solutions that 'pretend' to be correct.**
3. **Assess Progress:** Determine the extent of non-trivial progress made.
4. **Score Determination:** Compare the findings against the Specific Grading Guidelines and the General Rubric to determine the final score.

### Output Requirements
You must provide your final score in the format <points>N out of 7</points>. Ensure the '<points>' block is used **only once**, as your answer will be parsed based on the first <points> </points> block that appears in your whole response.

**PROBLEM STATEMENT**
{problem}

**GROUND-TRUTH SOLUTION**
{solution}

**SPECIFIC GRADING GUIDELINES**
{guidelines}

**PROPOSED SOLUTION**
{response}

Present your detailed thought process and formal justification based on the scoring rubric and grading guidelines, and finally present your final score in the format below.
[Select one of the following options]
<points>7 out of 7</points>
<points>6 out of 7</points>
<points>1 out of 7</points>
<points>0 out of 7</points>"""

# Paper Appendix C.3
GRADING_BENCH_PROMPT = """Carefully analyze the given problem statement and the proposed solution, and then write out your analysis regarding the correctness of the proposed solution.

After the analysis, you must provide a score based on the following criteria:
- incorrect: The solution is completely incorrect or irrelevant.
- partial: The solution is partially correct but has significant errors or omissions.
- almost: The solution is almost correct but contains minor errors or inaccuracies.
- correct: The solution is fully correct and complete.

The very last part of your response must be only one of the following words: incorrect, partial, almost, or correct.

Problem: {problem}

Solution: {response}"""
