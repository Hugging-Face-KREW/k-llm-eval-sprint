# Item-by-item comparison of KorMedMCQA with the original (lm-evaluation-harness)
 
[한국어](README.md) | **English**
 
This is the record of checking, on all 3,009 `test` questions, that the `kormedmcqa:{doctor,nurse,pharm,dentist}` tasks merged into the Lighteval fork (fork PR #3)
give the same results as the [lm-evaluation-harness `kormedmcqa` task](https://github.com/EleutherAI/lm-evaluation-harness/tree/main/lm_eval/tasks/kormedmcqa) (version 3.0). The upstream issue is [huggingface/lighteval#1481](https://github.com/huggingface/lighteval/issues/1481).
For the design, see the [design document](../design.en.md).
 
## Code and validation material
 
| Artifact | Location and role |
| --- | --- |
| Task code | `src/lighteval/tasks/tasks/kormedmcqa.py` on the Lighteval fork branch `team-d/kormedmcqa` (`1f1c1d24`, task commit `88089039`) |
| Unit tests | `tests/unit/tasks/test_kormedmcqa.py` on the same branch, 33 tests |
| Comparison script | [compare_with_harness.py](compare_with_harness.py): matches the per-item records of the two tools by row number and compares five things |
| Run results | [results/doctor.json](results/doctor.json), [results/dentist.json](results/dentist.json): `--report` output of the script, without the question text |
 
## Comparison method
 
We run the same subset with each tool separately and compare the parquet from Lighteval `--save-details` with the jsonl from harness `--log_samples`.
 
- **Matching questions**: by Lighteval `doc.id` and harness `doc_id` (the dataset row number). Lighteval shuffles the questions with seed 42 before running them, so matching by line order would compare different questions.
- **What is compared**: prompt text (decoded `input_tokens` vs harness `arguments`), prompt token IDs (the harness prompt re-tokenized), generated text, the letter extracted with `extract_choice` (vs harness `filtered_resps`), and the per-question score.
- If anything differs, the script prints the first question that differs and exits with code 1.
## Run settings
 
| Item | Value |
| --- | --- |
| Model | `Qwen/Qwen2.5-1.5B-Instruct` |
| Settings | 5-shot, float32, batch size 1, chat template off (`override_chat_template=False`), CPU |
| Data | All of `sean0042/KorMedMCQA` `test`. Lighteval is pinned to revision `79efd6f9`; harness uses the latest |
| Scope | `--max-samples` and `--limit` pick different questions, so neither is used |
 
## Results
 
| Task | Questions | Same prompt | Same generation | Same score | Accuracy (harness / Lighteval) | Standard error |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `kormedmcqa:doctor` | 435 | 435 | 435 | 435 | 0.3310 / 0.3310 (144) | 0.0226 |
| `kormedmcqa:nurse` | 878 | 878 | 878 | 878 | 0.5114 / 0.5114 (449) | 0.0169 |
| `kormedmcqa:pharm` | 885 | 885 | 885 | 885 | 0.3955 / 0.3955 (350) | 0.0164 |
| `kormedmcqa:dentist` | 811 | 811 | 811 | 811 | 0.3551 / 0.3551 (288) | 0.0168 |
| **Total** | **3,009** | **3,009** | **3,009** | **3,009** | | |
 
| Overall score | Value |
| --- | ---: |
| `kormedmcqa:_average` (Lighteval, simple mean of the four subsets) | 0.3983 |
| harness group `kormedmcqa` / paper (mean weighted by question count) | 0.4091 (1,231/3,009) |
 
The two values differ by 1.1 percentage points because nurse, the subset with the highest score, also has the most questions. This goes into the Differences section of the upstream PR.
 
Number of distinct A–E letters in the generated output:
 
| Task | One letter | None | Two or more |
| --- | ---: | ---: | ---: |
| doctor | 430 | 0 | 5 |
| nurse | 859 | 0 | 19 |
| pharm | 850 | 0 | 35 |
| dentist | 803 | 0 | 8 |
 
Since no output has zero letters, the two gaps in the harness regex that we deliberately kept (a full-width colon after `정답` ("answer"), and Hangul right after the letter) did not change the score of any question.
 
### Scope of the check
 
- **doctor, nurse, dentist**: all five items were compared (435/435, 878/878, 811/811). The results are in `results/`.
- **pharm**: before this script existed, a team member compared prompt token IDs, generation and score on their own PC with a separate script (885/885, `results/pharm.json`). Prompt text and extracted letters were not compared separately. pharm was run on Windows, so four local edits outside the task were made to Lighteval (the `list_models` argument, `:` and `|` in the cache and details file names, and `xxhash` encoding). None of them touch prompts, generation or scoring.
## Reproduction
 
```bash
SUBSET=dentist
 
# Lighteval (an environment with the fork's team-d/kormedmcqa branch installed)
lighteval accelerate \
  "model_name=Qwen/Qwen2.5-1.5B-Instruct,override_chat_template=False,device=cpu,batch_size=1,dtype=float32" \
  "kormedmcqa:${SUBSET}|5" --save-details --output-dir results/lighteval
 
# lm-evaluation-harness (a separate environment)
lm_eval --model hf \
  --model_args pretrained=Qwen/Qwen2.5-1.5B-Instruct,dtype=float32 \
  --tasks kormedmcqa_${SUBSET} --num_fewshot 5 \
  --batch_size 1 --device cpu --log_samples --output_path results/harness
 
# Comparison (python from the Lighteval environment)
python teams/team-d-kormedmcqa/validation/compare_with_harness.py \
  --lighteval-details results/lighteval/details/Qwen/Qwen2.5-1.5B-Instruct/*/details_kormedmcqa:${SUBSET}\|5_*.parquet \
  --harness-samples results/harness/Qwen__Qwen2.5-1.5B-Instruct/samples_kormedmcqa_${SUBSET}_*.jsonl \
  --tokenizer Qwen/Qwen2.5-1.5B-Instruct \
  --report ${SUBSET}.json
```
 
On an Apple M5 CPU, dentist took 662 seconds with Lighteval and 1,205 seconds with harness.
 
## Owners
 
| subset | Run and comparison |
| --- | --- |
| doctor | @kangmin04 |
| nurse | @minmin-129 |
| pharm | @naha0106-tech |
| dentist | @kangmin04 (Qwen run), @eotjd613 (pipeline check with SmolLM2-135M-Instruct, 811/811 match) |
 
