Title: [BUG] Korean translation literals are incomplete, so `openai_mmlu_kor_*` and Korean extractive-match metrics fail

## Describe the bug
`TRANSLATION_LITERALS[Language.KOREAN]` only defines `confirmation_word`, `yes` and `no`. Anything that needs `question_word`, `answer`, `and_word` or `or_word` raises `AttributeError: Translation for 'answer' is needed for Language.KOREAN`.

- `openai_mmlu_kor_*`: the MCQ prompt function fails before any model call. From the code, the Korean configs of `global_mmlu` (same MCQ template), `mkqa` and `tydiqa` (QA template built on the MCQ one) should fail the same way.
- `MultilingualExtractiveMatchMetric(language=Language.KOREAN)` fails when building its regexes.

## To Reproduce
```python
from datasets import load_dataset
from lighteval.tasks.multilingual.tasks import openai_mmlu as om

name = "openai_mmlu_kor_mcf:high_school_mathematics"
cfg = {c.name: c for c in om.TASKS_TABLE}[name]
row = next(r for r in load_dataset("openai/MMMLU", "KO_KR", split="test") if r["Subject"] == "high_school_mathematics")
cfg.prompt_function(row, name)
# AttributeError: Translation for 'answer' is needed for Language.KOREAN
```

Script with the output before and after filling the literals: https://github.com/dw021213/hrm8k-lighteval-experiments/blob/c994677a3a41a8e5e841f0046e26b18214ad8275/e6_korean_literals.py

## Expected behavior
The Korean prompt is built (`질문: … 답변:`) and the metric runs. Filling the literals in memory with the values proposed in #1179, plus `and_word="그리고"`, makes both work.

#1179 adds most of these literals but not `and_word`, which `lazy_latex_regex` needs, and it has had no review since March. We are happy to help there or open a small PR, whichever you prefer.

## Version info
lighteval 0.13.1.dev0 at `c2af9e5`, Python 3.12, macOS, dataset `openai/MMMLU` (`KO_KR`).
