# Pinned Ko Source Prompt Catalog

[한국어](source_rows.md) | **English**

`source_rows.json` preserves original prompts, instruction order and all 24 kwargs fields. Tables omit only null fields. English reading translations below are documentation only; actual scoring always uses the verbatim Korean prompts and original parameter strings. Translation/checker mismatches are preserved, including 5 versus 6 in key 127, at most 6 versus <6 in 1268, and characters versus words in 3538.

Pinned data: [train Parquet](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/data/train-00000-of-00001.parquet). Each ID links to checker code at the same revision.

## key 122

**English reading translation — not a scoring input:**

> Write a blog post about the history of the Internet and its impact on our lives. Address teenagers and enclose the entire response in double quotation marks.

**Original Korean prompt (verbatim):**

```text
인터넷의 역사와 그것이 우리의 삶에 미친 영향에 대한 블로그 포스트를 작성하세요. 블로그 포스트는 십대들을 대상으로 하며, 전체 응답을 큰따옴표로 감싸세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`startend:quotation`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1619) | `{}` |

## key 127

**English reading translation — not a scoring input:**

> Write a complete article using this text as a starting point: ‘You may need to meet with a helper to make a parenting plan. First, estimate how much time you can spend parenting each day and whether it is enough....’ Do not use the keywords `수면` (sleep), `요리` (cooking) or `먹이기` (feeding). Mention the keyword `일정` (schedule) at least 5 times.

**Original Korean prompt (verbatim):**

```text
아래의 텍스트를 출발점으로 삼아 완전한 기사를 작성하세요: "당신은 양육 계획을 세우기 위해 도우미와 만날 필요가 있을 수 있습니다. 첫 번째는 매일 양육을 위해 얼마나 많은 시간을 가질 수 있는지 추정하는 것이며, 그것이 충분한지 여부입니다...."
다음 키워드를 사용하지 마세요: 수면, 요리, 먹이기
'일정'이라는 키워드를 5회 이상 언급하세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`keywords:forbidden_words`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1155) | `{"forbidden_words": ["수면", "요리", "먹이기"]}` |
| 1 | [`keywords:frequency`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) | `{"frequency": 6, "keyword": "일정", "relation": "at least"}` |

## key 136

**English reading translation — not a scoring input:**

> A nucleus is a collection of protons and neutrons. Explain this in detail. Write exactly 9 very short bullet points and use fewer than 100 words. Follow this example format: `* 핵은 양성자와 중성자의 집합체입니다.` (‘A nucleus is a collection of protons and neutrons’), `* 양성자는 ....` (‘Protons are ....’).

**Original Korean prompt (verbatim):**

```text
핵은 양성자와 중성자의 집합체입니다. 이에 대해 자세히 설명하십시오. 정확히 9개의 매우 짧은 글머리 기호를 작성하십시오. 사용하는 단어 수를 제한하십시오(100단어 미만). 예를 들면:
* 핵은 양성자와 중성자의 집합체입니다.
* 양성자는 ....

위의 예시 형식을 따르십시오.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:number_bullet_lists`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L334) | `{"num_bullets": 9}` |
| 1 | [`length_constraints:number_words`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L907) | `{"num_words": 100, "relation": "less than"}` |

## key 240

**English reading translation — not a scoring input:**

> What is a lattice? Rewrite the answer so children can understand it, entirely in Russian. No other language is allowed.

**Original Korean prompt (verbatim):**

```text
격자는 무엇인가요? 어린이들이 이해할 수 있도록 답변을 다시 작성하고, 전적으로 러시아어로 작성되도록 하세요. 다른 언어는 허용되지 않습니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`language:response_language`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L164) | `{"language": "ru"}` |

## key 349

**English reading translation — not a scoring input:**

> I want to start a vegetable and flower garden in my small backyard. Can you advise me on watering the plants? Include at least 3 italicized text sections, such as `*이탤릭 텍스트 1*`, `*이탤릭 텍스트 2*`, etc. Keep the entire answer under 40 words.

**Original Korean prompt (verbatim):**

```text
나는 작은 뒷마당에 채소와 꽃을 위한 정원을 시작하고 싶어. 내 식물에 물 주는 방법에 대한 조언을 줄 수 있니? 최소한 3개의 이탤릭 텍스트 섹션이 필요해: *이탤릭 텍스트 1*, *이탤릭 텍스트 2* 등.

답변을 짧게 해줘 -- 전체 답변은 40단어 미만이어야 해.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:number_highlighted_sections`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L469) | `{"num_highlights": 3}` |
| 1 | [`length_constraints:number_words`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L907) | `{"num_words": 40, "relation": "less than"}` |

## key 1082

**English reading translation — not a scoring input:**

> Write exactly 2 paragraphs about a man who wakes up one day and realizes he is inside a video game. Separate the paragraphs with the Markdown delimiter `***`.

**Original Korean prompt (verbatim):**

```text
어느 날 한 남자가 깨어나 자신이 비디오 게임 안에 있다는 것을 깨닫는 이야기를 정확히 2단락으로 작성하세요. 단락은 마크다운 구분자 ***로 구분하세요.***
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`length_constraints:number_paragraphs`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L593) | `{"num_paragraphs": 2}` |

## key 1107

**English reading translation — not a scoring input:**

> Write two jokes about rockets. Do not include commas. Separate the jokes with six asterisks: `******`.

**Original Korean prompt (verbatim):**

```text
로켓에 대한 두 가지 농담을 작성하세요. 응답에 쉼표를 포함하지 마세요. 두 농담은 6개의 별표 기호로 구분하세요: ******.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`punctuation:no_comma`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1530) | `{}` |
| 1 | [`combination:two_responses`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1243) | `{}` |

## key 1127

**English reading translation — not a scoring input:**

> Write a poem about missing class, with 4 sections labeled `섹션 X` (‘Section X’). End with this exact phrase: `제가 놓친 수업에 대한 돈을 돌려받을 수 있을까요?` (‘Can I get my money back for the class I missed?’).

**Original Korean prompt (verbatim):**

```text
수업이 그리운 것에 대한 시를 써주세요. 시는 "섹션 X"으로 표시된 4개의 섹션이 있어야 합니다. 시를 다음의 정확한 문구로 마무리하세요: "제가 놓친 수업에 대한 돈을 돌려받을 수 있을까요?"
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:multiple_sections`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L543) | `{"num_sections": 4, "section_spliter": "섹션"}` |
| 1 | [`startend:end_checker`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1335) | `{"end_phrase": "제가 놓친 수업에 대한 돈을 돌려받을 수 있을까요?"}` |

## key 1203

**English reading translation — not a scoring input:**

> What happened when China's Tang dynasty came to power? Use the word `전쟁` (war) at least 8 times and `평화` (peace) at least 10 times.

**Original Korean prompt (verbatim):**

```text
중국의 당나라가 권력을 잡았을 때 무슨 일이 일어났습니까? 전쟁이라는 단어를 최소한 8번 사용하고, 평화라는 단어를 최소한 10번 사용해야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`keywords:frequency`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) | `{"frequency": 8, "keyword": "전쟁", "relation": "at least"}` |
| 1 | [`keywords:frequency`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) | `{"frequency": 10, "keyword": "peace", "relation": "at least"}` |

## key 1233

**English reading translation — not a scoring input:**

> How many meters above ground was the world's tallest skyscraper in 2000? Include only the main points. End with the exact phrase `도와드릴 수 있는 다른 것이 있나요?` (‘Is there anything else I can help you with?’). Mention `마천루` (skyscraper) at least 8 times.

**Original Korean prompt (verbatim):**

```text
2000년 세계에서 가장 높은 마천루는 지면에서 몇 미터 높이였나요? 답변에는 주요 사항만 포함해 주세요. 답변을 "도와드릴 수 있는 다른 것이 있나요?"라는 정확한 문구로 마무리해 주세요. "마천루"라는 단어를 최소 8번 언급해 주세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`startend:end_checker`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1335) | `{"end_phrase": "도와드릴 수 있는 다른 것이 있나요?"}` |
| 1 | [`keywords:frequency`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) | `{"frequency": 8, "keyword": "마천루", "relation": "at least"}` |

## key 1237

**English reading translation — not a scoring input:**

> Write an entertaining post for teenagers about Buena Onda, a restaurant serving Argentinian food. Highlight at least three sections using Markdown such as `*강조된 섹션*`. Mention `아르헨티나` (Argentina).

**Original Korean prompt (verbatim):**

```text
10대들을 위한 재미있는 포스트를 작성하세요. 아르헨티나 음식을 제공하는 Buena Onda라는 레스토랑에 대해 이야기하세요. 응답의 최소 세 섹션을 *강조된 섹션*과 같은 마크다운 형식으로 강조하세요. 포스트에 "아르헨티나"라는 단어를 언급하세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:number_highlighted_sections`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L469) | `{"num_highlights": 3}` |
| 1 | [`keywords:existence`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L778) | `{"keywords": ["아르헨티나"]}` |

## key 1242

**English reading translation — not a scoring input:**

> Can you suggest a nickname for `스타포드`? Use JSON, do not use the word `별명` (nickname), and add nothing outside the JSON block.

**Original Korean prompt (verbatim):**

```text
스타포드를 위한 별명을 지어 줄 수 있나요? JSON 형식을 사용하고 응답에 "별명"이라는 단어를 사용하지 마세요. JSON 블록 외부에 아무것도 추가하지 마세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:json_format`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L935) | `{}` |
| 1 | [`keywords:forbidden_words`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1155) | `{"forbidden_words": ["별명"]}` |

## key 1262

**English reading translation — not a scoring input:**

> Explain in detail: ‘Increased axle loads increased road damage.’ Include a title enclosed in double angle brackets, such as `<<제목>>`, and write fewer than 5 sentences.

**Original Korean prompt (verbatim):**

```text
다음 텍스트에 대해 자세히 설명해 주시겠습니까: 축 하중 증가가 도로 손상을 증가시켰습니다? 귀하의 응답은 <<제목>>이라는 이중 각괄호로 감싸진 제목을 포함해야 합니다. 5문장 미만으로 작성하십시오.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:title`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360) | `{}` |
| 1 | [`length_constraints:number_sentences`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L237) | `{"num_sentences": 5, "relation": "less than"}` |

## key 1268

**English reading translation — not a scoring input:**

> Give an example diary entry about stress management and explain how you came up with it. The entire response must contain at most 6 sentences.

**Original Korean prompt (verbatim):**

```text
스트레스 관리에 대한 일기 항목의 예를 줄 수 있나요? 예를 어떻게 생각해냈는지 말해 주세요. 당신의 전체 응답은 6문장 이하로 구성되어야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`length_constraints:number_sentences`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L237) | `{"num_sentences": 6, "relation": "less than"}` |

## key 1480

**English reading translation — not a scoring input:**

> Write a blog post about the most interesting things you have seen on public transport. First repeat the preceding sentence without changing a single word, then answer. Put no word or character before the repeated sentence.

**Original Korean prompt (verbatim):**

```text
대중교통에서 본 것 중 가장 흥미로운 것들에 대한 블로그 포스트를 작성하세요. 첫째, 위의 문장을 단어 하나하나 바꾸지 않고 반복한 다음, 답변을 주세요. 어떤 단어나 문자도 반복 문장 앞에 말하지 마세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`combination:repeat_prompt`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1298) | `{"prompt_to_repeat": "대중교통에서 본 것 중 가장 흥미로운 것들에 대한 블로그 포스트를 작성하세요."}` |

## key 1800

**English reading translation — not a scoring input:**

> Explain to a group of elementary-school students why we have seasons. Add a postscript beginning with `P.S.` at the end.

**Original Korean prompt (verbatim):**

```text
초등학생 그룹에게 우리가 계절이 있는 이유를 설명하세요. 응답의 끝에 P.S.로 시작하는 후기를 추가해야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_content:postscript`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L653) | `{"postscript_marker": "P.S."}` |

## key 1928

**English reading translation — not a scoring input:**

> Expand this sentence into a formal story: ‘My dog is brown and my cat is black.’ Include a title enclosed in double angle brackets, as in `<<제목>>`, and no commas. The word `피부` (skin) must appear fewer than 3 times.

**Original Korean prompt (verbatim):**

```text
다음 문장을 공식적인 이야기로 자세히 설명하십시오: "내 개는 갈색이고 내 고양이는 검은색입니다." 귀하의 답변에는 제목이 포함되어야 하며 제목은 이중 꺾쇠 괄호로 묶여야 합니다 즉 <<제목>> 그리고 귀하의 응답에는 쉼표가 포함되어서는 안 됩니다. 귀하의 응답에서 "피부"라는 단어는 3회 미만으로 나타나야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:title`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360) | `{}` |
| 1 | [`punctuation:no_comma`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1530) | `{}` |
| 2 | [`keywords:frequency`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) | `{"frequency": 3, "keyword": "피부", "relation": "less than"}` |

## key 1954

**English reading translation — not a scoring input:**

> What are poppy seeds used for? Write exactly 7 paragraphs, with the last paragraph beginning with `요약` (summary). Separate paragraphs with two newline characters.

**Original Korean prompt (verbatim):**

```text
양귀비 씨앗의 용도는 무엇인가요? 당신의 대답은 정확히 7개의 단락으로 구성되어야 하며, 마지막 단락은 "요약"이라는 단어로 시작해야 합니다. 각 단락은 두 개의 줄 바꿈으로 구분되어야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`length_constraints:nth_paragraph_first_word`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1014) | `{"first_word": "요약", "nth_paragraph": 7, "num_paragraphs": 7}` |

## key 2035

**English reading translation — not a scoring input:**

> Write a joke in at least 5 sentences. Use Markdown to italicize at least 2 sections, as in `*이탤릭체*`, and enclose the answer in double quotation marks.

**Original Korean prompt (verbatim):**

```text
최소 5문장으로 농담을 작성하세요. 답변에서 최소 2개 섹션을 *이탤릭체*로 표시하기 위해 Markdown을 사용하세요. 답변을 큰따옴표로 감싸세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:number_highlighted_sections`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L469) | `{"num_highlights": 2}` |
| 1 | [`startend:quotation`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1619) | `{}` |
| 2 | [`length_constraints:number_sentences`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L237) | `{"num_sentences": 5, "relation": "at least"}` |

## key 2142

**English reading translation — not a scoring input:**

> Write a proposal for a new college course on the history of the world as told by a dog. The proposal must contain the word `포식자` (predator) at least twice.

**Original Korean prompt (verbatim):**

```text
새로운 대학 과정 개가 들려주는 세계의 역사에 대한 제안서를 작성하십시오. 제안서에는 반드시 '포식자'라는 단어가 두 번 이상 등장해야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`keywords:frequency`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) | `{"frequency": 2, "keyword": "predatory", "relation": "at least"}` |

## key 3073

**English reading translation — not a scoring input:**

> How are you feeling today? Write exactly 4 paragraphs separated by two newline characters each. Begin the first paragraph with `회사` (company).

**Original Korean prompt (verbatim):**

```text
오늘 기분이 어떠신가요? 정확히 4개의 단락을 각각 두 개의 줄 바꿈으로 구분하여 작성해 주실 수 있나요? 첫 번째 단락은 "회사"라는 단어로 시작해 주세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`length_constraints:nth_paragraph_first_word`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1014) | `{"first_word": "회사", "nth_paragraph": 1, "num_paragraphs": 4}` |

## key 3311

**English reading translation — not a scoring input:**

> What is SRE? Use only Korean, provide a title in double angle brackets such as `<<SRE>>`, and use the keywords `지표` (indicator), `목표` (goal) and `관리` (management).

**Original Korean prompt (verbatim):**

```text
SRE란 무엇인가? 응답에는 오직 한국어만 사용하고, <<SRE>>와 같은 이중 꺾쇠 괄호로 제목을 제공하라. '지표', '목표' 및 '관리'라는 키워드를 사용하라.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`language:response_language`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L164) | `{"language": "ko"}` |
| 1 | [`detectable_format:title`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360) | `{}` |
| 2 | [`keywords:existence`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L778) | `{"keywords": ["지표", "목표", "관리"]}` |

## key 3345

**English reading translation — not a scoring input:**

> Write a strange poem I can send to my friend Steve in Australia about why the United States has no kangaroo invasion. Use `강도` (robber) at least twice. Include exactly 2 Markdown bullets using this exact format: `* 포인트 1`, `* 포인트 2`. Do not include `죽이다` (kill), `도살` (slaughter), `점령` (occupation) or `침략` (invasion).

**Original Korean prompt (verbatim):**

```text
나는 호주에 있는 내 친구 스티브에게 보낼 수 있는 이상한 시를 원해. 그 시는 왜 미국에 캥거루 침략이 없는지에 대한 내용이어야 해. '강도'라는 단어는 최소 2번 등장해야 하고, 시는 아래의 정확한 형식을 사용하여 마크다운 형식으로 정확히 2개의 글머리를 포함해야 해:
* 포인트 1
* 포인트 2
'죽이다', '도살', '점령', '침략'이라는 키워드는 응답에 포함하지 마.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`keywords:frequency`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) | `{"frequency": 2, "keyword": "robber", "relation": "at least"}` |
| 1 | [`detectable_format:number_bullet_lists`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L334) | `{"num_bullets": 2}` |
| 2 | [`keywords:forbidden_words`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1155) | `{"forbidden_words": ["죽이다", "도살", "점령", "침략"]}` |

## key 3442

**English reading translation — not a scoring input:**

> What is the answer to the riddle about something you can catch but cannot throw, and something you can throw but cannot catch? Use fewer than 20 words in the entire answer and enclose the title in double angle brackets, as in `<<제목>>`.

**Original Korean prompt (verbatim):**

```text
잡을 수 있지만 던질 수 없는 것과 던질 수 있지만 잡을 수 없는 것에 대한 수수께끼의 답은 무엇인가요? 전체 답변은 20단어 미만이어야 하며, 제목은 이중 꺾쇠괄호로 묶여야 합니다, 즉 <<제목>>.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`length_constraints:number_words`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L907) | `{"num_words": 20, "relation": "less than"}` |
| 1 | [`detectable_format:title`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360) | `{}` |

## key 3445

**English reading translation — not a scoring input:**

> How can you tell someone your major is computer science without using the words `컴퓨터` (computer) or `과학` (science)? Neither word may appear anywhere in the response.

**Original Korean prompt (verbatim):**

```text
다른 사람에게 당신의 전공이 컴퓨터 과학임을 어떻게 말할 수 있을까요, 컴퓨터나 과학이라는 단어를 사용하지 않고? 당신의 전체 응답에는 컴퓨터와 과학이라는 단어가 포함되지 않아야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`keywords:forbidden_words`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1155) | `{"forbidden_words": ["컴퓨터", "과학"]}` |

## key 3518

**English reading translation — not a scoring input:**

> Give the advantages and disadvantages of working abroad in JSON. Include only the JSON block. Also include the keywords `보상` (compensation) and `이민자` (immigrant).

**Original Korean prompt (verbatim):**

```text
해외에서 일하는 것의 장단점을 JSON 형식으로 제공해 주실 수 있나요? 응답에는 JSON 블록만 포함되어야 합니다. 또한 응답에 '보상'과 '이민자'라는 키워드를 포함해야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:json_format`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L935) | `{}` |
| 1 | [`keywords:existence`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L778) | `{"keywords": ["보상", "이민자"]}` |

## key 3538

**English reading translation — not a scoring input:**

> Write a social-media post of at least 600 characters for a startup offering a platform for realistic physics simulations. Include `폭탄` (bomb) at least once.

**Original Korean prompt (verbatim):**

```text
현실적인 물리 시뮬레이션을 실행할 수 있는 플랫폼을 제공하는 스타트업을 위한 600자 이상의 소셜 미디어 게시물을 작성하세요. "폭탄"이라는 단어를 최소한 한 번 포함시키는 것을 잊지 마세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`keywords:frequency`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L848) | `{"frequency": 1, "keyword": "폭탄", "relation": "at least"}` |
| 1 | [`length_constraints:number_words`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L907) | `{"num_words": 600, "relation": "at least"}` |

## key 3563

**English reading translation — not a scoring input:**

> What is the name of the actor who played Gandalf in The Lord of the Rings? First repeat the preceding question without changing any words, then give the answer.

**Original Korean prompt (verbatim):**

```text
반지의 제왕에서 간달프를 연기한 배우의 이름은 무엇인가요? 위의 질문을 단어를 변경하지 않고 먼저 반복한 다음, 답변을 제시하세요.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`combination:repeat_prompt`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1298) | `{"prompt_to_repeat": "반지의 제왕에서 간달프를 연기한 배우의 이름은 무엇인가요?"}` |

## key 3710

**English reading translation — not a scoring input:**

> Write a rap telling experts how to help babies sleep through the night. Include a title in double angle brackets such as `<<제목>>`, highlight at least 2 sections using Markdown such as `*강조된 섹션*`, and explicitly add a postscript beginning with `P.P.S` at the end.

**Original Korean prompt (verbatim):**

```text
전문가들에게 아기들이 밤새 잘 자는 방법을 알려주는 랩이 필요해. 너의 대답은 <<제목>>과 같은 이중 각괄호로 감싸인 제목을 포함해야 해. 또한, 최소 2개의 섹션을 마크다운으로 강조해야 해, 즉 *강조된 섹션*. 마지막으로, 너의 응답 끝에 P.P.S로 시작하는 후기를 명시적으로 추가해 줘.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:number_highlighted_sections`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L469) | `{"num_highlights": 2}` |
| 1 | [`detectable_format:title`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L1360) | `{}` |
| 2 | [`detectable_content:postscript`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L653) | `{"postscript_marker": "P.P.S"}` |

## key 3739

**English reading translation — not a scoring input:**

> What is the name of the green-eyed monster that makes people jealous? Use at most 3 sentences, specifically only 1 or 2 sentences.

**Original Korean prompt (verbatim):**

```text
사람들에게 질투를 일으키는 초록 눈의 괴물의 이름은 무엇인가요? 당신의 대답은 3문장 이하(단 1문장 또는 2문장)여야 합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`length_constraints:number_sentences`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L237) | `{"num_sentences": 3, "relation": "less than"}` |

## key 3743

**English reading translation — not a scoring input:**

> Write a joke about `조에` and bubbles, with at least 3 placeholders enclosed in square brackets, such as `[date]`.

**Original Korean prompt (verbatim):**

```text
저는 [date]와 같은 대괄호로 표시된 최소 3개의 자리 표시자가 포함된 조에와 거품에 관한 농담이 필요합니다.
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_content:number_placeholders`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L287) | `{"num_placeholders": 3}` |

## key 3750

**English reading translation — not a scoring input:**

> Was the moon landing propaganda created by the government? Include one of these exact phrases: `제 답변은 예입니다.` (‘My answer is yes’), `제 답변은 아니요입니다.` (‘My answer is no’), or `제 답변은 아마도입니다.` (‘My answer is maybe’).

**Original Korean prompt (verbatim):**

```text
달 착륙은 정부가 만들어낸 선전인가? 당신의 대답은 다음의 정확한 문구 중 하나를 포함해야 합니다: "제 답변은 예입니다." 또는 "제 답변은 아니요입니다." 또는 "제 답변은 아마도입니다."
```

| Index | instruction_id | kwargs (null omitted) |
| ---: | --- | --- |
| 0 | [`detectable_format:constrained_response`](https://huggingface.co/datasets/allganize/IFEval-Ko/blob/54199e3801116897697babf341865741dcd06fc8/ifeval_ko/instructions.py#L373) | `{}` |
