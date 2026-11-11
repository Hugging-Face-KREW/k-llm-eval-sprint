"""English presentation of the same saved selection-coverage counts."""

TEXT_EN = {
    "# 문항 선정 범위 집계": "# Prompt Selection Coverage",
    "입력 조건을 집계한 결과이며 모델 실행·코드 분기 실행률·고정 응답 회귀 결과가 아니다. 선정안은 팀 검토 전 제안이다.": "This counts input conditions, not model execution, measured code-branch coverage or stored-response regression. The selection is a proposal pending team review.",
    "| 목록 | 문항 | 지시 | ID 포함 | 입력 경로 포함 | 반복 ID 문항 | 복수 지시 문항 |": "| Selection | Prompts | Instructions | IDs | Input paths | Repeated-ID prompts | Multiple-instruction prompts |",
    "## 유형별 대응": "## Instruction-type mapping",
    "| instruction ID | 전체 발생 | 선정 문항 발생 | 선정 key | Ko 관련 변경 근거 |": "| Instruction ID | Full occurrences | Selected occurrences | Selected keys | Ko change evidence |",
    "Ko 수정 클래스 표시는 고정 제작자 문서의 열거 기준이며, ‘—’가 영어와의 완전한 동등성을 뜻하지 않는다.": "Modified-class labels follow the pinned authors' documentation. A dash does not establish complete equivalence with English.",
    "## 지시 유형별 입력 경로": "## Input paths by instruction type",
    "| instruction ID | 입력 경로 | 전체 발생 | 선정 문항 발생 |": "| Instruction ID | Input path | Full occurrences | Selected occurrences |",
    "`default`는 관찰된 정상 kwargs에서 값에 따른 명시적 경로 선택이 없는 유형이다. 응답별 성공·실패를 하나로 합쳐 검증했다는 뜻이 아니다.": "`default` means no explicit value-dependent path selection under observed normal kwargs. It does not combine or validate all response pass/fail behavior.",
    "입력 경로 집계는 check_following의 kwargs 유래 속성과 상수의 동등 비교를 AST로 확인하고 실제 데이터에 등장하는 값을 센다. 나머지 파라미터의 수치·문구·언어 값은 같은 연산의 인자이며 모든 값을 개별 경로로 세지 않는다.": "Path counting checks AST equality comparisons between kwargs-derived attributes and constants in check_following, then counts values present in the data. Other numbers, phrases and language values are arguments to the same operations, not separate paths per value.",
    "데이터에 없는 누락·오류·난수 fallback, 추신의 기타 표지, 응답에 따른 분기, NFC/NFD·정규식·문장/단어 경계는 고정 응답 회귀 대상이다. 이 출력은 해당 검사를 실행하지 않는다.": "Missing/invalid inputs, random fallbacks, other postscript markers, response-dependent branches, NFC/NFD, regexes and sentence/word boundaries belong to stored-response regression. This output does not execute those checks.",
}
CELLS_EN = {
    "선정안": "Proposal", "제작자 열거 수정 클래스": "Author-listed modified class",
    "Ko 단어 utility": "Ko word utility", "Ko 문장 utility": "Ko sentence utility",
    "Ko 고정 선택 문구": "Ko fixed response phrases",
}


def render_english(lines, report):
    import re
    out = []
    for line in lines:
        if line in TEXT_EN:
            out.append(TEXT_EN[line])
            continue
        if line.startswith("고정 revision: "):
            out.append(f"Pinned revision: `{report['revision']}`. Data: {report['full_rows']} prompts, {report['full_instructions']} instructions, {report['full_ids']} types.")
            continue
        for korean, english in CELLS_EN.items():
            line = line.replace(korean, english)
        if re.search(r"[가-힣]", line):
            raise ValueError("Missing coverage translation: " + line)
        out.append(line)
    return [out[0], "", "[한국어](coverage.md) | **English**", ""] + out[2:]
