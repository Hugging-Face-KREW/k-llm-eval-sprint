# Design Document: Porting KorMedMCQA to Lighteval

[한국어](design.md) | **English**

> Team: STPs (STP즈, Team D) · Analysis report: [analysis.en.md](analysis.en.md)
>
> Reference versions: dataset revision `79efd6f91edfc8036330d7a4daa88b9f2deb9a82`, lm-evaluation-harness `97a5e2c` (task version 3.0), lighteval `c2af9e5f` (team fork `Hugging-Face-KREW/lighteval`), paper arXiv 2403.01469v3
>
> Implementation: fork branch `kangmin/kormedmcqa-task` at `88089039` (`src/lighteval/tasks/tasks/kormedmcqa.py`, `tests/unit/tasks/test_kormedmcqa.py`). PR to `team-d/kormedmcqa` planned.
>
> The comments at the top of code blocks and the `file :line` references point to source locations at the commit above.
>
> **Updated 11/8**: reflects what was decided at the week-4 session (11/1) and the implementation results of 11/7. The overall score (5-1 ②, 5-3), `choices` and the metric name (section 3, 5-2), the unit tests (6-1) and the task split (section 7) changed.

## 1. Task names, file location

### 1-1. Task names

`kormedmcqa:{doctor,nurse,pharm,dentist}` (one task per profession, four in total)

The names use the `<benchmark>:<subset>` format, for three reasons.

- It follows lighteval's existing convention. `mmlu:anatomy` and `arabic_mmlu:<subset>` use the same format.
- When the part before `:` is the same, lighteval groups the tasks automatically and produces `kormedmcqa:_average`.
- A single profession can be run on its own (`kormedmcqa:doctor|5`). Only the separator differs from harness's `kormedmcqa_doctor`.

Below is the same pattern in existing code. It loops over the subset list, creates `name:subset` tasks, and passes the same subset value as `hf_subset`. kormedmcqa builds its four configs the same way (section 5 ③).

```py
# src/lighteval/tasks/multilingual/tasks/arabic.py:109-111
ARABIC_MMLU_TASKS = [
    CustomArabicMMLUTask(name=f"arabic_mmlu:{subset}", hf_subset=subset) for subset in ARABIC_MMLU_SUBSETS
]
```

### 1-2. File location

We propose `src/lighteval/tasks/tasks/kormedmcqa.py`. One file holds `extract_choice`, the prompt function, the metric and the four tasks.

Why `tasks/tasks/`:

- `tasks/tasks/` is always loaded. `multilingual/tasks/` is only loaded when `load_multilingual=True` (`registry.py` default `False`).
- On the other hand, the existing Korean-related tasks (`global_mmlu`, `paws_x` etc.) live in `multilingual/tasks/`, so the maintainers may prefer that location.
- Since it is a single file, moving it to `multilingual/tasks/` only means moving the file; the code does not change. If the maintainers want a different location, we move it during PR review.

### 1-3. Scope

Only KorMedMCQA is implemented. Ko-MuSR, from the team assignment list, is optional and was left out of this sprint's scope.

## 2. Data scope

### 2-1. What the original (harness) does

| Item | Original setting | Source |
| --- | --- | --- |
| Dataset | `sean0042/KorMedMCQA` | `_template_yaml` :1 |
| subset | `doctor` / `nurse` / `pharm` / `dentist` (one per task) | `doctor.yaml` :2, `dentist.yaml` :2, `nurse.yaml` :2, `pharm.yaml` :2 |
| Evaluation split | `test` | `_template_yaml` :2 |
| Few-shot split | `fewshot` | `_template_yaml` :3 |
| Few-shot sampling | `first_n` (in order from the start) | `_template_yaml` :5 |
| Mean | Per-profession scores averaged with weights by question count | `_kormedmcqa.yaml` :10 |

```yaml
# _template_yaml:1~5
dataset_path : sean0042/KorMedMCQA
test_split : test
fewshot_split : fewshot
fewshot_config:
  sampler: first_n
```

The shot count is given at run time with `--num_fewshot 5` (`_cli/run.py` :123). If it is not given, the run is 0-shot (`evaluator.py` :327-342).

### 2-2. Values to set in Lighteval

| Field | Value | Original counterpart | Lighteval default | Source |
| --- | --- | --- | --- | --- |
| `hf_repo` | `sean0042/KorMedMCQA` | `dataset_path` | (required field) | `lighteval_task.py` :115 |
| `hf_subset` | One of the four professions | `dataset_name` | (required field) | `lighteval_task.py` :116 |
| `hf_revision` | `79efd6f91edfc8036330d7a4daa88b9f2deb9a82` (all 40 characters) | (the original does not pin it) | `None` (latest) | `lighteval_task.py` :128 |
| `evaluation_splits` | `["test"]` | `test_split` | `["validation"]` | `lighteval_task.py` :133 |
| `few_shots_split` | `"fewshot"` | `fewshot_split` | `None` | `lighteval_task.py` :134 |
| `few_shots_select` | `"sequential"` | `sampler: first_n` | `None` → `balanced` | `prompt_manager.py` :203-205 |
| Shot count | Not written in the config; given in the run string `kormedmcqa:doctor\|5` | (given at run time) | Config default 0, overridden by the run string | `lighteval_task.py` :148, `registry.py` :203-204, 229 |

### 2-3. What happens if they are not set

| Field not set | Lighteval behavior | Result |
| --- | --- | --- |
| `evaluation_splits` | Scores `validation` | This dataset's splits are `train`/`dev`/`test`/`fewshot`, so there is no `validation`. It may raise an error or score the wrong split (**guess**, needs to be confirmed by running it) |
| `few_shots_split` | From the candidate list (`hf_avail_splits`, default `train`/`validation`/`test`), drops the evaluation split, then looks for names containing `train`, `dev`, `valid`, `default`, in that order, and uses the first one (`lighteval_task.py` :234-236, :256-279) | `train` is in the candidates, so the examples are drawn from `train`. `fewshot` is not in the candidate list, so it is never chosen. The examples differ from the original, so the prompt differs |
| `few_shots_select` | `balanced` (samples so the answer distribution is even) | Each profession has exactly one answer of each letter A–E, so 5-shot picks the same 5 examples, but in a different order |

When `few_shots_split` is set, `hf_avail_splits` is not used.

```py
# src/lighteval/tasks/prompt_manager.py:203-205
few_shots_select = task.fewshot_selection
if few_shots_select is None:
    few_shots_select = "balanced"
```

We judged that `sequential` behaves the same as the original `first_n`. Since `variance_seed` is passed as 0 (`lighteval_task.py` :397-399), the loop below does not run, and the first 5 items of the `fewshot` split become the examples in their original order.

```py
# src/lighteval/tasks/prompt_manager.py:261-266
def _init_fewshot_sampling_sequential(self, num_fewshot: int, variance_seed: int):
    # No balancing of the few-shot examples, we take the first items of the set
    # We rotate by num_fewshot * seed (seed >= 0) to be able to have different series of sequential few-shots
    fewshotpool = self.task.fewshot_docs()
    for _ in range(num_fewshot * variance_seed):
        fewshotpool.append(fewshotpool.pop(0))
```

### 2-4. The four tasks

| Task name | `hf_subset` | test questions | few-shot questions |
| --- | --- | --- | --- |
| `kormedmcqa:doctor` | `doctor` | 435 | 5 |
| `kormedmcqa:nurse` | `nurse` | 878 | 5 |
| `kormedmcqa:pharm` | `pharm` | 885 | 5 |
| `kormedmcqa:dentist` | `dentist` | 811 | 5 |
| Total |  | 3,009 |  |

The 20 `fewshot` questions are not included in the total.

## 3. Prompt function: mapping the original fields to `Doc(query, choices, gold_index)`

harness prompt format ([`_template_yaml` L9](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L9)):

```txt
{question.strip()}
A. {A}
B. {B}
C. {C}
D. {D}
E. {E}
정답：
```

| Original field | Where in Doc | Conversion rule |
| --- | --- | --- |
| `question` | First line of `query` | `.strip()` applied (not applied to the options; the original does the same) |
| `A`–`E` | The `A. ...` to `E. ...` lines of `query` | Joined with newlines |
| (fixed text) | Last line of `query` | `정답：` ("Answer:"; **full-width colon `：`**, never a regular `:`) |
| `answer` (1–5) | `gold_index` | **`answer - 1`** (Lighteval counts from 0. Forgetting it raises no error; the score just drops to around 20%) |
| (letters A–E) | `choices` | `["A", "B", "C", "D", "E"]` (no leading space). Adding a space would not affect the prompt or the scoring (3-1 ①), but there is no reason to, so we left it out |
| `cot`, `subject`, `year`, `period`, `q_number` | Not used |  |

```py
# kormedmcqa.py (implementation)
LETTERS = ["A", "B", "C", "D", "E"]


def kormedmcqa_prompt(line, task_name: str = None):
    query = f"{line['question'].strip()}\n" + "".join(f"{letter}. {line[letter]}\n" for letter in LETTERS) + "정답："
    return Doc(
        task_name=task_name,
        query=query,
        choices=list(LETTERS),
        gold_index=line["answer"] - 1,
    )
```

- `task_name` is taken as an argument of the prompt function and passed to Doc (same structure as `med.py`). lighteval calls `self.formatter(item, self.name)` for each row of data ([`lighteval_task.py` L309](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/lighteval_task.py#L309)). Both `test` and `fewshot` become Docs through this function ([L345-348](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/lighteval_task.py#L345-L348)).

### 3-1. Prompt limitations and how they were resolved

This covers the prompt items of analysis report section 8 ③ and the points to check that came up during design. We checked them in two ways.

- We read the actual code of both tools.
- We compared the run records of the 435 doctor test questions. The prompts in the harness records and the prompts assembled from the `doc` in the lighteval records using the assembly rule below were **identical character for character for all 435 questions.** doctor test question 1 is 2,145 characters in both.

| # | Limitation (source) | harness code | Lighteval code | Result |
| --- | --- | --- | --- | --- |
| ① | Whether `choices` include a leading space | — | The few-shot answer is appended after stripping spaces with `get_golds()[0].strip()` ([`prompt_manager.py` L159](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L159)) | **Resolved.** The prompt is the same with or without the space. In scoring, `strip_strings=True` also removes the space from the gold |
| ② | Must match character for character, including the separators between examples (analysis 8 ③, 6-2) | The few-shot-only `doc_to_text` appends `정답： {answer}\n\n` ("Answer: {answer}") at the end of each example itself, with `doc_to_target: ""` ([`_template_yaml` L4-7](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/tasks/kormedmcqa/_template_yaml#L4-L7)). Since the target is empty, no extra separator is added and pieces are joined with `"".join` ([`task.py` L1078-1088, L1040](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/api/task.py#L1078-L1088)) | Example = `query + " " + answer`, pieces joined with `"\n\n".join` ([`prompt_manager.py` L157-165](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L157-L165)) | **Same string.** Built differently, but both give `…정답： E\n\n…정답： A\n\n…\n\n{question}\n정답：` |
| ③ | Few-shot order `first_n` vs `balanced` (analysis 8 ③) | `first_n` = the first n items of the `fewshot` split, in order ([`samplers.py` L95-104](https://github.com/EleutherAI/lm-evaluation-harness/blob/97a5e2c710e2b56b9dd48f367bb6fe87bbb2c176/lm_eval/api/samplers.py#L95-L104)) | `sequential` = the pool in order, first n items ([`prompt_manager.py` L261-267](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L261-L267), L231 `[:num_fewshot]`) | **Resolved.** With `few_shots_select="sequential"`, the same 5 questions are appended in the same order |
| ④ | Full-width colon `：` | U+FF1A (L6, L9) | Our function also uses U+FF1A | **Match** |

lighteval's assembly code is below. harness has separate templates for evaluation and for few-shot; lighteval uses only one `prompt_function`.

```py
# src/lighteval/tasks/prompt_manager.py:156-165  (_prepare_plain_text)
for fewshot_sample in doc.fewshot_samples:
    query = self._extract_query(fewshot_sample.query, fewshot_sample.instruction)
    parts.append(query + " " + fewshot_sample.get_golds()[0].strip())

query = self._extract_query(doc.query, doc.instruction)
parts.append(query)

return "\n\n".join(parts)
```

**Conditions for getting the same prompt** (breaking any of them changes the prompt):

- Do not put an `instruction` in `Doc`. If set, it is prepended ([L153-154](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L153-L154)).
- Do not give a `system_prompt` in the model config. If set, it is prepended ([L150-151](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L150-L151)).
- Turn the chat template off (`override_chat_template=False`). If on, the plain-text assembly above is not used ([L54-57](https://github.com/Hugging-Face-KREW/lighteval/blob/c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14/src/lighteval/tasks/prompt_manager.py#L54-L57)).

## 4. Scoring: metric, generation length, stop sequences, answer extraction rules

For KorMedMCQA, the model generates an answer, a regex extracts the chosen option, and that is compared with the correct answer. To reproduce the existing lm-evaluation-harness evaluation, we apply the settings below.

### 4-1. Generation settings

| Item | Setting | Source |
| --- | --- | --- |
| Maximum generation length | `generation_size=1024` | harness `max_gen_toks: 1024` |
| Sampling | Greedy decoding. The task has no field for this; it follows the model default (temperature 0) | harness `do_sample: false`, `temperature: 0.0` |
| Stop sequences | `["Q:", "</s>", "<\|im_end\|>", ".", "\n\n"]` | Existing KorMedMCQA evaluation settings |
| Chat template | `override_chat_template=False` | Same as harness `apply_chat_template=False`: no chat template applied |

### 4-2. Answer extraction

Regular expressions extract the multiple-choice answer A–E from the generated text.

| Order | Regex | Example |
| --- | --- | --- |
| 1 | `정답[:\s]*([ABCDE])` | 정답: c ("Answer: c") |
| 2 | `정답은\s*([ABCDE])\s*입니다` | 정답은 c 입니다 ("The answer is c") |
| 3 | `\b([ABCDE])\.` | c. |
| 4 | `\b([ABCDE])\b` | c |

- `IGNORECASE` is applied and the regexes are tried in order.<br>**IGNORECASE: the setting that makes matching case-insensitive**
- The last match of the first regex that matches is taken as the answer.
- The extracted answer is uppercased (`.upper()` is applied).
- If extraction fails, an empty string (`""`) is returned and the question is scored as wrong.
- Implemented to match `extract_choice` in harness's `utils.py`.

### 4-3. Answer conversion and evaluation metric

The dataset's correct answer 1–5 is converted to the `gold_index` of section 3, and compared as a letter A–E with the model's predicted answer.

- **Metric:** Lighteval's `ExactMatches`. The name in the results table is `em` (the same name as the built-in `Metrics.exact_match`)
- **Prediction normalization:** `extract_choice` passed as `normalize_pred`
- **Gold answer:** kept as A–E via `Doc`'s `gold_index`
- **Scoring rule:** 1 point if correct, 0 if wrong or if extraction fails

Reference implementation: the GSM8K `ExactMatches` setup in `src/lighteval/tasks/tasks/tiny_benchmarks.py`

### 4-4. Score aggregation

Accuracy is computed for each of the four subsets: Doctor, Nurse, Pharm and Dentist. The overall score uses lighteval's default `kormedmcqa:_average` (simple mean), and the weighted mean is computed separately and written in the PR description (5-3).

Accuracy = {(number of correct questions) / (total number of evaluated questions)} \* 100 (%)

## 5. Differences from the original, and why

> The goal is to give the same score as harness for the same input. With Qwen2.5-1.5B-Instruct, 435 doctor questions, 5-shot, the experimental custom task matched harness in per-question outputs and scoring, for the doctor task (accuracy 0.3310 for both; time: 25–30 minutes on CPU).
>
> On 11/7 we ran the same conditions again with `kormedmcqa:doctor|5` as implemented in the fork. Accuracy was 0.3310 (144/435), and the prompt tokens, generated text and per-question scores were identical to harness for all 435 questions. The remaining scope is in section 8.

### 5-1. Summary

| # | Item | Original (harness) | Lighteval | Approach | Why |
| --- | --- | --- | --- | --- | --- |
| ① | Answer extraction | `ExtractChoiceFilter` + `take_first` filter | No filter step. The default `exact_match` compares the whole output | Put the original `extract_choice` into `ExactMatches`'s `normalize_pred` | To score the same way as the original |
| ② | Overall score | **Mean weighted** by question count (`weight_by_size: true`) | `kormedmcqa:_average` is a **simple mean** | **Keep the simple mean.** The weighted mean is computed separately from the per-profession scores and question counts and written in the PR description (5-3) | Do not change a lighteval-wide convention. Proposed this way in issue #1481. GPT-4o: weighted 85.61, simple 85.53 |
| ③ | Grouping professions | group yaml | Tasks whose names share the part before `:` are grouped as a superset | Create four `kormedmcqa:<profession>` tasks | `kormedmcqa\|5` runs all four professions together |
| ④ | Few-shot selection | `sampler: first_n` | Default `balanced` | `few_shots_select="sequential"` | With the default, the example order changes and so does the prompt |
| ⑤ | Few-shot count | CLI `--num_fewshot 5` | Run string `kormedmcqa:doctor\|5` | Always write `\|5` when running | Without `\|`, it is overridden to 0-shot |
| ⑥ | Few-shot split | `fewshot_split: fewshot` | If not set, `train` is chosen first | `few_shots_split="fewshot"` | To use the same split for examples as the original |
| ⑦ | Evaluation split | `test_split: test` | Default is `validation` | `evaluation_splits=["test"]` | The default differs from the original |
| ⑧ | Answer representation | `answer` 1–5 converted to a letter | `gold_index` 0–4 | `answer - 1` | The indexing differs |
| ⑨ | Metric normalization | `ignore_case`, `ignore_punctuation`, removing spaces and newlines | These options are not used | Only `strip_strings=True` | The extraction result is a single uppercase letter, so this does not affect the score |
| ⑩ | Generation settings | `until`, `max_gen_toks`, `temperature: 0.0` | `stop_sequence`, `generation_size`, model default | Values carried over as is; temperature not set | Only the names differ; the default is greedy |
| ⑪ | Chat template | Not used by default | Turned on automatically if the tokenizer has one | `override_chat_template=False` at run time | When on, the stop strings are ignored |
| ⑫ | Gaps in the regex | Present |  | **Not fixed; implemented as in the original** | If we fixed them, we could not tell an intended fix from our own bug |

### 5-2. Answer extraction: from a filter to the metric

harness processes the generation with filters and then computes `exact_match`.

```yaml
# lm_eval/tasks/kormedmcqa/_template_yaml
filter_list:
  - name: "extract_answer"
    filter:
      - function: !function utils.ExtractChoiceFilter
      - function: "take_first"
```

lighteval has no filter step, so extraction happens in the metric. `CHOICE_PATTERNS` and `extract_choice` are carried over as is; only where they are called changes.

```py
# kormedmcqa.py (implementation)
kormedmcqa_metric = SampleLevelMetric(
    metric_name="em",
    sample_level_fn=ExactMatches(strip_strings=True, normalize_pred=extract_choice),
    category=SamplingMethod.GENERATIVE,
    corpus_level_fn=np.mean,
    higher_is_better=True,
)
```

- `extract_choice` returns a single letter A–E via `.upper()`, so harness's options for ignoring case, punctuation and spaces are not needed.
- If extraction fails, the result is an empty string and the answer is wrong, the same as in harness.
- The metric name is `em`. The built-in `Metrics.exact_match`, which uses the same `ExactMatches`, is `em`, and other built-in metrics that attach a normalization function (`rouge_t5` etc.) do not change their names either. The extraction rules are written in the docstring and the PR description.

### 5-3. Overall score: keep the simple mean, compute the weighted mean afterwards (decided)

**Decision (week-4 session)**: the task code keeps lighteval's default `kormedmcqa:_average` (simple mean). The weighted mean for comparison with harness is computed with option 1 below and written together in the results table of the PR description. We proposed the same in issue #1481.

harness weights by question count.

```yaml
# lm_eval/tasks/kormedmcqa/_kormedmcqa.yaml:7~11
aggregate_metric_list:
  - metric: exact_match
    aggregation: mean
    weight_by_size: true
    filter_list: extract_answer
```

lighteval's `_average` is a simple mean for every benchmark.

```py
# src/lighteval/logging/info_loggers.py:382-384, 391-396
if "|" in k:
    task, fewshot = k.split("|")
    grouped_tasks[f"{task.split(':')[0]}:_average|{fewshot}"].append(k)
...
if len(list_of_subtasks) > 1:
    metrics = list(self.metric_aggregated[list_of_subtasks[0]].keys())
    self.metric_aggregated[average_task] = {
        metric: sum(self.metric_aggregated[k][metric] for k in list_of_subtasks) / len(list_of_subtasks)
        for metric in metrics
    }
```

| Option | Method | Same calculation as harness at 5-shot? | Notes |
| --- | --- | --- | --- |
| 1 (**chosen**) | Compute afterwards: weight the per-profession scores by question count ourselves | **Yes** | No change to the task code. The result goes in the PR description |
| 2 | Combined task: add a task that concatenates the four professions | **No** | Same only at 0-shot. Requires intercepting `download_dataset_worker` |
| 3 | Add a weighted mean to lighteval's aggregation code | Depends on the implementation | Changes the `_average` convention, so it needs the maintainers' input |

**Why option 2 differs at 5-shot**: if the `fewshot` split is also concatenated across the four professions, the pool becomes 20 items with doctor's 5 at the front. `sequential` only uses the first 5, so nurse, pharm and dentist questions also get doctor's examples. harness uses each profession's own examples.

```py
# src/lighteval/tasks/prompt_manager.py:230-231
# get rid of the doc that's the one we're evaluating, if it's in the fewshot
return [x for x in samples if x != formatted_doc][:num_fewshot]
```

An example calculation for option 1:

```py
rows = []
for task, scores in results.items():
    # Keep only per-profession tasks such as "kormedmcqa:doctor|5" (skip all, _average)
    name = task.split("|")[0]
    if not name.startswith(f"{prefix}:") or "_average" in name:
        continue
    details = sorted(run.glob(f"details/**/details_{task}_*.parquet"))[-1]
    rows.append((name, scores[metric], len(pd.read_parquet(details))))

total_n = sum(n for _, _, n in rows)
weighted = sum(score * n for _, score, n in rows) / total_n
```

**Precedent**: `mmlu` reports `mmlu:_average` as a simple mean even though the subjects have different question counts. Meanwhile, `bbq`, `lsat_qa` and `bold` keep a task combining everything next to the subtasks. However, these three read the dataset's `all` config directly. They are not a precedent for concatenating four configs in code, as KorMedMCQA would need.

```py
# src/lighteval/tasks/tasks/bbq.py:53, 55-56, 71
name="bbq",
hf_repo="lighteval/bbq_helm",
hf_subset="all",
...
name="bbq:Age",
```

### 5-4. Few-shot count

Even if `LightevalTaskConfig.num_fewshots=5` is set, the run string overrides it. Running `kormedmcqa:doctor` without `|` gives 0-shot. It cannot be fixed in the task, so `|5` must be stated in the run examples and the docstring.

```py
# src/lighteval/tasks/registry.py:204-207, 229
    task_name, few_shot = tuple(task.split("|"))
else:
    task_name = task
    few_shot = 0
...
config.num_fewshots = few_shot
```

For few-shot selection and split, see 2-3; for string assembly, see 3-1.

### 5-5. Generation settings and chat template

`do_sample` and `temperature` are not task fields. When the default temperature is 0, lighteval sets `do_sample=False`.

```py
# src/lighteval/models/transformers/transformers_model.py:817-818
if num_samples == 1 and generation_config["temperature"] == 0:
    generation_config["do_sample"] = False
```

When the chat template is on, the stop strings are reduced to the single EOS token. That is why we pass `override_chat_template=False`. This is a model argument, so it goes in the run command rather than the task file.

```py
# src/lighteval/models/transformers/transformers_model.py:694-700
if self.use_chat_template:
    stop_tokens = [self.tokenizer.eos_token]
else:
    # NOTE: we are assuming all items in a batch behave similarly (same
    # stop_tokens and max_tokens genrated) which is not necessarily
    # the case! Because of that we only use batch size of 1
    stop_tokens = [self.tokenizer.eos_token] + batch[0].stop_sequences
```

### 5-6. Actual impact of the regex gaps

Tallying the Qwen2.5-1.5B-Instruct outputs on the 435 doctor questions at 5-shot, no case of the gaps appeared. Because of the stop strings `.` and `\n\n`, outputs almost always end after a single letter. So we keep ⑫ as is for reproducibility, and under these conditions it can be considered to have no effect on the score.

| What was checked | Result on 435 questions |
| --- | --- |
| Answered with a single letter only | 430 |
| Extraction failed (empty) | 0 |
| Lowercase article issue (`a` caught as A) | 0 |
| Answer with a particle attached (`C가` "C + subject particle", `C번` "number C") | 0 |
| Multiple answers (`A, D, E` etc.) | 5 |
| Questions where the original and fixed regex (6-4) disagree | 0 |

- The 5 multiple answers are scored by their last letter. These are cases where the model gave several answers, so fixing the regex would not make them correct.
- This result is limited to one model, doctor, and 5-shot. Larger models that answer with explanations, and 0-shot, need to be looked at separately. On 100 questions at 0-shot, outputs like `C\n해설: ...` ("C\nExplanation: ...") appeared.
- The fix is provisional, so these numbers are not yet enough to decide whether to report it.

### 5-7. Points to watch when validating

These are not implementation differences, but places where results differ when comparing with harness.

| Item | harness | Lighteval | Note |
| --- | --- | --- | --- |
| Running a subset of questions | `--limit N`: the first N | `--max-samples N`: N after shuffling with seed 42 | On 100 doctor questions, only 26 overlapped. Compare on all questions |
| Reasoning tags | No handling in the KorMedMCQA config | `remove_reasoning_tags` defaults to `True` | Check this when comparing models that output `<think>` tags |

```py
# src/lighteval/tasks/lighteval_task.py:387-390  (get_docs)
n_samples = min(max_samples, len(eval_docs)) if max_samples else len(eval_docs)
rnd = random.Random()
rnd.seed(42)
rnd.shuffle(eval_docs)
```

## 6. Test plan

### 6-1. Unit tests

**Implemented (11/7)**: 33 tests in `tests/unit/tasks/test_kormedmcqa.py`, all passing (41 including `test_registry.py`). The dataset is CC BY-NC, so the tests use fake rows instead of the original text.

| Target | What is checked |
| --- | --- |
| Prompt | Snapshot of the full string, full-width colon, `answer` 1–5 → gold A–E |
| `extract_choice` | Each of the four regexes, the last match of the same regex, an earlier regex taking priority, a full-width colon (`정답：C`, "Answer:C") not matching pattern 1, and the gaps we deliberately kept |
| metric | The extraction → scoring path, feeding in a `ModelResponse` |
| Config | Four tasks, and that each profession's config values match the harness settings |

Below is the original plan.

`extract_choice`:

```py
@pytest.mark.parametrize("output, expected", [
    ("정답: B", "B"),
    ("정답 : B", "B"),
    ("정답은 C입니다", "C"),
    ("정답은 C 입니다.", "C"),
    ("A와 B 중 B", "B"),
    ("(C)", "C"),
    ("", ""),
    ("C가 정답", ""),
    ("C is a correct answer", "A"),   # known gap
])
def test_extract_choice(output, expected):
    assert extract_choice(output) == expected
```

Prompt function:

- With `answer = 1` and `answer = 5`, gold is A and E

Metric:

- pred `C`, gold `C` gives 1
- An empty pred with gold `C` gives 0

### 6-2. Character-level prompt comparison between harness and lighteval

- Compare all four subsets.
- doctor matched for all 435 questions, and test question 1 is 2,145 characters in both (3-1).

### 6-3. Full item-by-item comparison

Compare all 3,009 questions, including nurse, pharm and dentist, with harness question by question. doctor's 435 questions have been confirmed to match (section 5).

### 6-4. Counting the impact of the regex gaps

Count the questions where the answers extracted by the original and the fixed regexes differ. The fix is a provisional version that is case-sensitive so it does not catch lowercase articles. The results are in 5-6.

```py
FIXED = [re.compile(p) for p in [
    r"정답[:：\s]*([ABCDE])",
    r"정답은\s*([ABCDE])\s*입니다",
    r"(?<![A-Za-z])([ABCDE])\.",
    r"(?<![A-Za-z])([ABCDE])(?![A-Za-z])",
]]
diff = [r for r in rows if ext(ORIG, out(r)) != ext(FIXED, out(r))]
```

### 6-5. Validation with an EXAONE model

Running additionally with EXAONE (a Korean-specialized model made by LG) lets us check two more things.

1. Tokenizer end handling: EXAONE's tokenizer and end tokens differ from Qwen's. Differences in stop strings or EOS handling that did not show up with Qwen may appear.
2. Comparison with the paper's score: the paper reports 55.73.

If we cannot test on an NVIDIA GPU, we state that in the PR's validation scope.

## 7. Task split

At the week-4 session we split the schedule in two: task code and doctor reproduction by 11/8, and the full comparison and upstream PR by 11/15.

| Task | Details | Deliverable | Owner | Due | Status |
| --- | --- | --- | --- | --- | --- |
| Data splits, few-shot | The data settings of the four task definitions (`hf_subset`, `hf_revision`, `evaluation_splits`, `few_shots_split`, `few_shots_select`) | `TASKS_TABLE` in `kormedmcqa.py` (comprehension over the profession list) | 정민채 | 11/8 | Done |
| Prompt | Prompt function and unit tests | `kormedmcqa_prompt` | 김강민 | 11/8 | Done |
| Scoring | `extract_choice`, metric, generation settings, unit tests | `extract_choice`, `SampleLevelMetric`, `test_kormedmcqa.py` | 나하윤, 김강민 | 11/8 | Done |
| doctor reproduction | Full `kormedmcqa:doctor\|5` run, item-by-item comparison with harness | 0.3310 reproduced | 김강민 | 11/8 | Done |
| Fork PR | PR to `team-d/kormedmcqa`, with `tasks inspect` output attached | Fork PR | 김강민 | 11/8 | In progress |
| Character-level prompt comparison | Compare the nurse, pharm and dentist prompts with harness character by character | Comparison script | 김대성 | 11/15 | |
| Full run, comparison | Compare all 3,009 questions, including nurse, pharm and dentist, with harness; count the regex impact; compute the weighted mean | Results table | 김강민 | 11/15 | |
| Upstream PR | `huggingface/lighteval` PR (`Closes #1481`) | PR | 김강민 | 11/15 | |

## 8. Not yet confirmed

- The actual behavior when `evaluation_splits` is not set and there is no `validation` split
- Whether the nurse, pharm and dentist subsets match harness
- A full 0-shot run, and the scoring path for outputs with an explanation after the answer and for multiple answers
