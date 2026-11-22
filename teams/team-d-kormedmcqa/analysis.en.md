# Benchmark Analysis Report: KorMedMCQA

[한국어](analysis.md) | **English**

> Team: STPs (STP즈) · Dataset: [sean0042/KorMedMCQA](https://huggingface.co/datasets/sean0042/KorMedMCQA)
> Reference versions: dataset revision [`79efd6f`](https://huggingface.co/datasets/sean0042/KorMedMCQA/tree/79efd6f91edfc8036330d7a4daa88b9f2deb9a82), lm-evaluation-harness [`97a5e2c`](https://github.com/EleutherAI/lm-evaluation-harness/tree/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa) (task version 3.0), lighteval [`7fa19dc`](https://github.com/huggingface/lighteval/tree/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7), paper arXiv [2403.01469v3](https://arxiv.org/abs/2403.01469v3)

## 1. Summary: what does it measure?

7,469 five-option multiple-choice questions from the 2012–2024 Korean healthcare professional licensing exams (doctor, nurse, pharmacist, dentist). Besides medical knowledge, it tests knowledge of Korean medical terminology and Korean laws and healthcare institutions.

## 2. Sources: paper, authors, year, official code

- Paper: _KorMedMCQA: Multi-Choice Question Answering Benchmark for Korean Healthcare Professional Licensing Examinations_, arXiv [2403.01469v3](https://arxiv.org/abs/2403.01469v3) (2024)
- Authors: Sunjun Kweon, Byungjin Choi (co-first authors) et al. KAIST, Ajou University School of Medicine, UNIST, Kyung Hee University School of Dentistry
- Official evaluation code: there is no separate repository. In the paper, open-source models were measured with lm-evaluation-harness (8× A100, seed 0) and commercial models through their APIs.
- Source questions: past exam PDFs published by the Korea Health Personnel Licensing Examination Institute (KHPLEI, 국시원)

## 3. Dataset: Hugging Face ID, configs and splits, question counts, fields, two examples

- Hugging Face ID: `sean0042/KorMedMCQA`
- Configs: `doctor`, `nurse`, `pharm`, `dentist`
- Splits: `train` / `dev` / `test` / `fewshot`. Split by year (train up to 2020, dev 2021, test 2022–2024). `fewshot` has 5 questions per config.

| config | train | dev | test | total |
|---|---|---|---|---|
| doctor | 1,890 | 164 | 435 | 2,489 |
| nurse | 582 | 291 | 878 | 1,751 |
| pharm | 632 | 300 | 885 | 1,817 |
| dentist | 297 | 304 | 811 | 1,412 |
| total | 3,401 | 1,059 | 3,009 | 7,469 |

Question counts were checked with the HF datasets-server `/size` endpoint. The 20 `fewshot` questions are not included in the totals.

Fields:
- `question` (string): question text
- `A`–`E` (string): options
- `answer` (int, 1–5): number of the correct option (1=A … 5=E). Note that it starts at 1, not 0.
- `cot` (string): worked solution. Only present in the `fewshot` split; empty string elsewhere
- `subject`, `year`, `period`, `q_number`: profession, year, exam session, question number

We wondered where the 5 `fewshot` questions came from and cross-checked them: for all four professions, 5 question texts each match `dev` (2021) and none overlap with `test`. Each profession has exactly one answer of each letter A–E (doctor: E, A, C, D, B).

Two examples (test split). The question text is kept verbatim in Korean. The first asks for the right nursing intervention for a bed-rest patient after hip replacement (answer: anti-embolism stockings). The second asks for the correct procedure for opening a clinic in a county under Korean medical law (answer: file an opening report with the county head).

```
# nurse, 2022 — answer 3 (C)
question: 고관절전치환술을 받고 절대안정 중인 환자에게 '비효과적 말초조직 관류의 위험'이라는
          간호진단을 내렸을 때 간호중재는?
A: 하지운동을 제한한다.
B: 무릎 밑에 높은 베개를 받쳐준다.
C: 항혈전스타킹을 적용한다.
D: 드레싱을 자주 교환한다.
E: 예방적 항생제를 투여한다.
```

```
# doctor, 2022 session 1 — answer 1 (A)
question: 의사 'A'가 군지역에 의원을 개설하려고 한다. 적절한 절차는?
A: 개설신고서 → 군수
B: 개설신고서 → 도지사
C: 신고서 → 의사협회
D: 개설허가신청서 → 군수
E: 허가신청서 → 도지사
```

## 4. License and access: license, whether accepting terms is required

- License: the HF dataset card says CC BY-NC 2.0 (`license:cc-by-nc-2.0`, non-commercial use). However, the [paper's appendix datasheet](https://arxiv.org/html/2403.01469v3#A5) says "released under MIT license". The two disagree.
- Access: not gated (HF API `gated: False`). It downloads without logging in or accepting any terms.
- For the implementation: lighteval tasks load the data straight from HF instead of storing it in the repository. We decided to state the stricter HF card license (CC BY-NC 2.0) in the docstring and to report the mismatch to the authors (section 8).

## 5. Official evaluation method: prompt format, few-shot count and source, scoring, answer extraction, metric, paper numbers

Our reference is harness [`lm_eval/tasks/kormedmcqa`](https://github.com/EleutherAI/lm-evaluation-harness/tree/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa). The per-profession yaml files (`doctor.yaml` etc.) include `_template_yaml` and differ only in `dataset_name`.

### Prompt format

```
{question.strip()}
A. {A}
B. {B}
C. {C}
D. {D}
E. {E}
정답：
```

- `정답` means "answer", so the last line reads "Answer:".
- The final colon is the full-width colon `：`. It must not be replaced with a regular `:`. ([`_template_yaml` L9](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L9))
- The answer letter is built as `['A','B','C','D','E'][answer-1]`. ([L10](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L10))

### Few-shot count and source

- The paper uses 5-shot (Table 1).
- The examples are the first 5 questions of the `fewshot` split, in order (`sampler: first_n`). Each example gets only the answer letter, as in `정답： E\n\n` ("Answer: E"); the `cot` solution is not included. ([`_template_yaml` L3-L7](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L3-L7))

### Scoring, answer extraction, normalization

| Step | Details | Source |
|---|---|---|
| Generation | `generate_until`, greedy (`do_sample: false`, `temperature: 0.0`), `max_gen_toks: 1024` | [`_template_yaml` L8, L25-L34](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L25-L34) |
| Stopping | Stops as soon as one of `"Q:"`, `"</s>"`, `"<\|im_end\|>"`, `"."`, `"\n\n"` appears | Same file, L26-L31 |
| Answer extraction | Tries four regexes from the top and uses the last match of the first pattern that matches. If none match, an empty string (wrong) | [`utils.py` L14-L33](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/utils.py#L14-L33), paper Appendix B |
| Normalization | `exact_match` after `ignore_case`, `ignore_punctuation`, and removing spaces and newlines | [`_template_yaml` L16-L24](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L16-L24) |

Answer extraction regexes (all `IGNORECASE`):

```python
CHOICE_PATTERNS = [
    re.compile(r"정답[:\s]*([ABCDE])", re.IGNORECASE),
    re.compile(r"정답은\s*([ABCDE])\s*입니다", re.IGNORECASE),
    re.compile(r"\b([ABCDE])\.", re.IGNORECASE),
    re.compile(r"\b([ABCDE])\b", re.IGNORECASE),
]
```

- Pattern 1 catches `정답` ("answer") followed by a letter; pattern 2 catches `정답은 X입니다` ("The answer is X"); patterns 3 and 4 catch a bare letter.
- These regexes were added in task version 3.0 ([harness PR #3842](https://github.com/EleutherAI/lm-evaluation-harness/pull/3842), merged 2026-06-24). Before that, the whole generation was compared with `exact_match`.
- CoT cannot be reproduced with harness. Since `"."` is a stop string, generation is cut at the first period, right after "차근차근 생각해봅시다." ("Let's think step by step."). The paper's CoT scores (Table 2) were measured separately through APIs.

### Metric

- Accuracy: mean `exact_match` per profession
- Overall score: mean weighted by test question count (`weight_by_size: true`). ([`_kormedmcqa.yaml` L7-L11](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_kormedmcqa.yaml#L7-L11)) Computing it ourselves from the paper's per-profession GPT-4o scores, the weighted mean is 85.61, the same as the paper, while the simple mean is 85.53.

### Paper numbers

Direct 5-shot, mean weighted by question count. A few rows taken from Table 1 of the paper.

| Model | Mean |
|---|---|
| o1-preview | 92.72 |
| Claude-3.5-Sonnet | 86.51 |
| GPT-4o | 85.61 |
| Qwen2.5-72B | 78.86 |
| Llama-3.1-70B | 74.31 |
| EXAONE-3.0-7.8B | 55.73 |
| EEVE-10.8B | 54.94 |
| (Reference) mean of human examinees | 77.05 |

### This week's team decision: default scoring method

We decided to follow the original: generation plus extraction with the original regexes. The examples are the 5 questions of the `fewshot` split in order, and the stop strings and maximum generation length are kept as in the original.

Reasons:
1. Both the original (harness) and the paper use this method. Switching to log-likelihood would give a different score even for the same model, so the numbers would not be comparable.
2. The 5 shots set the answer format. Asked without examples, the model answers along the lines of `정답은 3번입니다` ("The answer is number 3"), which the regexes cannot catch. Seeing `정답： E` ("Answer: E") in the five examples, the model follows suit and writes something like ` C`.
3. Results are only reproducible if the same 5 examples are used in the same order every time. Random sampling would make the score wobble from run to run.

Also:
- The chat template is turned off. The default harness run does not use it, and when it is on, lighteval drops the stop strings and only stops at EOS, which changes the conditions (section 8 ④). Scores with the template on will only be looked at later, as a separate experiment.
- A log-likelihood version is not added to the default task. We plan to ask the maintainers in the issue whether to build one separately.
- The scope is Direct 5-shot, the four configs, and the test split. CoT, KorMedMCQA-V (image questions) and data fixes are out of scope this time.

## 6. Existing implementations: official code, other evaluation tools

| Tool | Implementation | Notes |
|---|---|---|
| lm-evaluation-harness | [`lm_eval/tasks/kormedmcqa/`](https://github.com/EleutherAI/lm-evaluation-harness/tree/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa) | The `kormedmcqa` group and `kormedmcqa_{doctor,nurse,pharm,dentist}`. Generation plus regex extraction (v3.0) |
| lighteval (`main`) | None | The medical tasks (`med.py` etc.) are in English; for Korean there are only translated and multilingual sets (`global_mmlu` etc.) |
| lighteval (open PRs) | None | See section 7 |

lighteval code we plan to refer to:
- `src/lighteval/tasks/tasks/gpqa.py`: an instruct-style task that generates and then extracts the answer
- `src/lighteval/tasks/tasks/mmlu.py`: short generation compared with `exact_match`
- `src/lighteval/tasks/tasks/musr.py`: listed as reference code in the team README. Shows the docstring format (`name`, `dataset`, `abstract`, `languages`, `tags`, `paper`) and how inspect-ai is attached

## 7. Duplicate check: search keywords and results (issues, PRs)

Searched `huggingface/lighteval` (main `7fa19dc`) on 2026-10-17.

| Keyword | Target | Result |
|---|---|---|
| `kormedmcqa` | Issues, PRs | 0 |
| `kormedmcqa` | Code | 0 |
| `medical korean` | Issues, PRs | 0 |
| `korean` | Issues, PRs | KMMLU issue [#1424](https://github.com/huggingface/lighteval/issues/1424) and PR [#1425](https://github.com/huggingface/lighteval/pull/1425) (open, Team A's scope), translation-literal PR #1179 (open), #356 (merged). Unrelated to KorMedMCQA |

Within the scope of our search, nothing overlaps.


## 8. Parts that look hard to implement

Most of these are "we want to port the original exactly, but lighteval's defaults differ, so they need adjusting".

| # | Difficulty | Original | lighteval default | Plan |
|---|---|---|---|---|
| ① | Answer extraction | A cascade of four regexes | `exact_match` compares the whole output as is ([`metrics.py` L255-L261](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/metrics/metrics.py#L255-L261)); `extractive_match` uses different rules | Write a new metric that ports `extract_choice` as is |
| ② | Gaps in the regex | See below | — | Keep the original and count the impact separately |
| ③ | Few-shot order | `first_n` | `balanced` ([`prompt_manager.py` L205](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/tasks/prompt_manager.py#L205)) | Switch to `few_shots_select="sequential"` (from the front, [L261-L267](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/tasks/prompt_manager.py#L261-L267)) and compare the prompt character by character, including the separators between examples |
| ④ | Chat template | Not used by default | Turned on automatically when the tokenizer has a chat template ([`models/utils.py` L109-L132](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/models/utils.py#L109-L132)). When on, the stop strings are dropped and generation only stops at EOS ([transformers L693-L698](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/models/transformers/transformers_model.py#L693-L698), [vLLM L630](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/models/vllm/vllm_model.py#L630)) | Turn it off with `override_chat_template=False`, and check in the details of the first run, from the answer lengths, that the stop strings take effect |
| ⑤ | Overall score aggregation | Mean weighted by question count | `kormedmcqa:_average` is a simple mean ([`info_loggers.py` L381-L396](https://github.com/huggingface/lighteval/blob/7fa19dc6f53a713ba8bb6541e7ed66dad2e24fd7/src/lighteval/logging/info_loggers.py#L381-L396)) | Compare per-profession scores for now. How to compute the weighted mean is decided in the week-4 design |
| ⑥ | Answer index | `answer` 1–5 | `gold_index` starts at 0 | `answer - 1`. Forgetting it raises no error and only drops the score to around 20%, so a test has to catch it |

The regex gaps in ② do not only fail to extract an answer; some extract a different answer. We checked by feeding strings to the original `extract_choice`.

| Model output | Extracted answer | Why |
|---|---|---|
| `C가 정답` ("C is the answer") | Empty | Python `re` treats Hangul as word characters, so there is no `\b` between `C` and `가`. Pattern 1 does not match either, because nothing follows `정답` ("answer") |
| `C번` ("number C") | Empty | Same reason |
| `C is a correct answer` | `A` | Pattern 4 matches both `C` and the article `a`. With `IGNORECASE`, the lowercase `a` matches too, and since the last match is used, the answer becomes `A` |

When extraction fails, the result is empty and stays wrong; but when a different letter is extracted, an unrelated option becomes the answer. On a question whose answer is A, a wrong answer is scored as correct. That said, since the questions are in Korean, how often the model actually answers in English is an unverified guess. We will count it in real outputs before deciding (section 9, step 4).

For now we implement the original as is. If we fixed it, our scores would differ from harness, and we could not tell whether that was due to the intentional fix or to our own bug. Since generation is cut at `.`, real outputs are usually short, like ` C`, so the impact may be small. The examples above were also run on strings we wrote ourselves, not seen in real model outputs.

During validation we plan to run both the original and a fixed regex on the real outputs and count how many questions get different answers. Based on that number we decide whether to report it to harness, and we list it as a "known issue" in the PR description.

### This week's team decision: which of the data issues we found to report first

| Order | Issue | Where to report | Why |
|---|---|---|---|
| 1 | License mismatch (HF card CC BY-NC 2.0 vs paper MIT) | HF dataset Community tab | It concerns the terms of use, so it comes first. What we write in the lighteval docstring also depends on it |
| 2 | In pharm test, the 271 questions from 2024 have `subject` set to `pharmacy` instead of `pharm` | HF dataset Community tab | No effect on scores when loaded by config. But if the data is combined and filtered by `subject`, those 271 questions drop out. Same place as issue 1, so we post them together |
| 3 | Gaps in the regex | lm-evaluation-harness issue | First count whether it affects real scores (week-6 validation). If it does, propose a fix with that number of questions as evidence. The regexes live in harness's scoring code, not in the dataset, so this goes to harness |

- The lighteval implementation uses the original data as is and pins the dataset revision. This is so that, if the data is fixed later, scores do not change without anyone noticing.

## 9. Validation plan: which model, compared against which numbers

The goal is to run the same model with harness and lighteval and check that the per-profession accuracy and the answer extracted for each question are the same.

The reference for comparison is the harness result with the same model, questions and settings. Table 1 of the paper is listed alongside for reference only and is not used as a pass criterion, because the paper may have been measured with a version from before regex extraction was added (v3.0, 2026-06).

We start with a single model, [`Qwen/Qwen2.5-1.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct).
- The team has no GPU able to run EXAONE-3.0-7.8B, so we picked a small model that runs on CPU. The point is not the model's ability but whether the two tools score the same, so a small model is enough.
- This model also has scores in Table 1 of the paper (Direct 5-shot): doctor 33.33 / nurse 47.72 / pharm 35.48 / dentist 32.43, mean 37.92. Weighting the per-profession scores by test question count also gives 37.92 (the simple mean is 37.24). We list these numbers in the results table for reference.

Once a GPU is available, we run it once more with EXAONE-3.0-7.8B (paper: 55.73). Its tokenizer and end tokens differ from Qwen's, so we can also look at differences in stop-string and EOS handling.

The concern with CPU is time. The 5-shot prompt is about 2,000 characters per question, so running 3,009 questions with each of the two tools looks like it will take quite a while. We first run a small batch to measure the time per question and then plan the full run.

Fixed: model, tokenizer and dataset revision, both tool versions, CPU, float32, batch size 1, greedy, `max_gen_toks` 1024, stop strings, the order of the 5 few-shot examples, chat template off.

Steps:

1. Scoring test (no model): feed `C`, ` c`, `C.`, `(C)`, `정답： C` ("Answer: C"), `정답은 C입니다` ("The answer is C"), an empty output, and the gap cases from ② (`C가 정답`, `C번`, `C is a correct answer`), and check that the lighteval metric and harness `extract_choice` give the same results. In harness, the gap cases give empty, empty and `A` respectively, so lighteval must give the same. `answer - 1` is checked here as well.
2. Prompt comparison: take the 5-shot prompt of the first test question of each profession from both tools and compare them character by character (doctor test question 1 is 2,145 characters in harness).
3. Small run: 20 questions per profession, batch size 1. Match the generation, the extracted answer and correctness question by question.
4. Full run: the 3,009 test questions. Record per-profession accuracy, the weighted mean, the simple mean, the difference between the two tools (percentage points), and the number of per-question mismatches. Also count the questions where the original and the fixed regex give different answers. Also count the questions where the model answered with an English sentence, to see whether the "extracts a different answer" case from ② actually happens.

Scoring of the same generation must always be identical. If the generations themselves differ, rerun with batch size 1 to separate implementation or configuration problems from numerical differences.

### How to read the results

First, fix the guessing baselines. Distribution of test answers (counted by us, revision `79efd6f`):

| config | A | B | C | D | E | Best single-option guess |
| --- | --- | --- | --- | --- | --- | --- |
| doctor | 99 | 77 | 85 | 92 | 82 | A 22.76% |
| nurse | 163 | 165 | 174 | 187 | 189 | E 21.53% |
| pharm | 174 | 153 | 159 | 203 | 196 | D 22.94% |
| dentist | 152 | 141 | 170 | 179 | 169 | D 22.07% |
| total | 588 | 536 | 588 | **661** | 636 | D 21.97% |

If a per-profession score is below random (20%) or below that profession's guessing baseline, suspect a scoring (format) problem before concluding the model could not solve the questions.

Table 1 of the paper also has some odd scores. gemma-2-2b-it at 13.33 on doctor is below random, and Qwen2.5-7B-Instruct at 27.33 on nurse is lower than the 1.5B model of the same family (47.72). The answers may have been marked wrong because their format did not match the regexes (a guess).

So in the full run we count, per profession, the share of questions where none of the four regexes matched (the extraction failure rate). This number is used as evidence when we ask in the issue whether a log-likelihood variant is needed.

### Optional experiments (whether to do them is decided at the 10/18 session)

- Log-likelihood comparison: for the professions with a high extraction failure rate only, run the same model with the log-likelihood method and look at the score difference.
- Data contamination check: these past exams have been public on HF since 2024-03, and the original exam papers were published by KHPLEI even earlier, so models may have seen the questions and answers during training.
  - Scores by year: split test into 2022 / 2023 / 2024 (964 questions from 2024: doctor 150, nurse 291, pharm 271, dentist 252). On HF, the 2022–2023 questions were uploaded in 2024-03 and the 2024 questions in 2024-08.
  - Shuffled options: a model that solves from the content scores about the same, while a model that memorized the answer positions drops.
  - Question continuation: give only the first part of a question and see whether the model continues it almost exactly as the original.
  - These use settings that differ from the original, so they are not added to the default task and are run only as experiments.

Results of the optional experiments are only written in the PR description for reference. If a large difference shows up, the team decides at that point whether to share it with the maintainers or the dataset authors.
