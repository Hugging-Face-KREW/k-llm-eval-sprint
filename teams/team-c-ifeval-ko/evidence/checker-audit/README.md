# IFEval / IFEval-Ko 원본 검증 자료

**한국어** | [English](README.en.md)

**156건의 실험**에 사용한 입력·코드·재현 근거·채점 결과를 이 폴더에 모았다. [비교표](results.md)와 [results.json](results.json)에서 영어·Ko 판정과 집계를 확인할 수 있다. 별도 실험 패키지 없이 이 폴더에서 입력 생성부터 결과 검증·첨부 자료 생성까지 수행한다.

실험은 실제 데이터 조건 116건·메모리 override 2건·합성 입력 38건으로 구성되며, full 평가에서 검사한 instruction은 247개다. 보조 호환성·오류 입력 18건도 같은 실행에서 검사한다. Ko에서는 정상 반환 10건·예상 예외 8건이고, 영어에서는 정상 반환 16건·예상 예외 2건이다. 입력 18건 기준으로 strict·loose 각각 같은 건수이며, 정상 반환에는 F 판정도 포함한다. 보조 입력은 주 실험의 지표 분모에 넣지 않는다. 모델 생성·새 Lighteval-Ko 동등성·기존 Lighteval 영어/French 회귀는 미수행이다.

## 파일 안내

| 자료 | 파일과 확인할 내용 |
| --- | --- |
| 입력·사전 기대값 | [cases.json](cases.json): 156건의 원본 순서·kwargs·응답·검사 대상·해시 |
| 영어·Ko 원시 결과 | [original_results.json](original_results.json), [ko_results.json](ko_results.json): 동일 Ko 입력의 판정과 기준 입력 재현 기록 |
| 전체 실험 결과 | [results.md](results.md), [results.json](results.json): 영어·Ko 비교 열, 모든 개별 판정·문항 판정·재현 확인·집계 |
| 검증 범위·경계 | [coverage.json](coverage.json), [manifest.json](manifest.json) |
| 원본 문항 | [source_rows.json](source_rows.json), [source_rows.md](source_rows.md): 원본 32문항·55개 instruction의 전체 prompt·순서·kwargs |
| 기준 자료 | [baseline.json](baseline.json): 기대값 추적용 기준 입력·영어/Ko 저장 판정·환경. 현재 실험 결과를 다시 생성할 때 덮어쓰지 않음 |
| 보조 입력·양쪽 기대값 | [support_cases.json](support_cases.json), [support_original_results.json](support_original_results.json), [support_ko_results.json](support_ko_results.json) |
| 입력 생성·실행 | [build_cases.py](build_cases.py), [run_original.py](run_original.py), [run_ko.py](run_ko.py), [run_audit.py](run_audit.py), [audit_runtime.py](audit_runtime.py) |
| 비교·테스트·첨부 | [compare.py](compare.py), [test_audit.py](test_audit.py), [package_results.py](package_results.py) |
| 출처·복원·의존성 | [provenance.json](provenance.json), [fetch_sources.py](fetch_sources.py), [requirements.lock.txt](requirements.lock.txt), [nltk_resources.json](nltk_resources.json) |
| 검증·해시 | [validation.json](validation.json), [test_output.txt](test_output.txt), [SHA256SUMS](SHA256SUMS) |

`results.json`의 각 `cases[i]`에 입력과 양쪽 판정을 보관한다. `full`은 전체 instruction 평가, `isolated`와 `isolated_targets`는 지정한 index의 평가, `diagnostics`는 checker 진단 결과다. 기준 입력의 재현 근거는 해당 case의 `baseline_reproduction`에 포함한다. 비교표와 네 지표는 동일 Ko 입력 156건으로 집계하며, 재현 확인을 분모에 중복해서 더하지 않는다.

`original_*`는 원래 영어 문항의 출처 정보다. 실제 비교 입력은 `evaluated_input`에 기록하며, 양쪽 모두 `test_response_ko`를 사용한다. 원본 입력·응답의 해시와 캐시 키를 검사해 같은 key의 다른 응답이 덮어써지지 않도록 했다. 기록된 실행 파일·cache 경로는 각자의 환경에 맞게 지정한다.

## 확인할 대표 사례

| key | case ID | 동일 Ko 입력의 영어 / Ko strict·loose |
| --- | --- | --- |
| 3345 | `robber_full` | `keyword=robber` 조건에 강도 응답: 양쪽 실패·실패 |
| 3345 | `robber_keyword_override` | 명시적 `keyword=강도` override: 양쪽 통과·통과 |
| 3442 | `comma_boundary_compact` | 20단어 실패·실패 / 18단어 통과·통과 |
| 349 | `markdown_quote_valid_highlights_349` | 39단어 통과·통과 / 40단어 실패·실패 |

서로 다른 원래 응답의 재현 확인과 동일 Ko 입력의 판정 비교는 각 case에서 입력 출처를 구별해 기록한다. 알고리즘 차이는 동일 응답을 사용한 결과로 집계한다. `controlled_override`와 key가 null인 `synthetic`도 실제 데이터 조건과 구별한다.

## 고정 revision

| 대상 | revision |
| --- | --- |
| lm-evaluation-harness | `d6de81643928d653435c431bae19945d41d32520` |
| google/IFEval | `966cd89545d6b6acfd7638bc708b98261ca58e84` |
| Allganize IFEval-Ko 코드·데이터 | `54199e3801116897697babf341865741dcd06fc8` |
| 정적으로 참고한 Lighteval | `c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14` |

출처 URL과 원본 파일별 해시는 [provenance.json](provenance.json)에 보존했다. 고정 source의 실제 `InputExample`과 strict·loose 함수를 불러와 실행하며 checker·tokenizer·loose 변환은 수정하지 않는다.

## 재현

작업 디렉터리는 이 `checker-audit/`다. 입력·결과는 모두 이 폴더에 생성하고, 기준 자료 `baseline.json`은 읽기 전용으로 사용한다. 설치와 공개 source 복원에는 네트워크가 필요하다.

```bash
sha256sum --check SHA256SUMS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python fetch_sources.py
python -m pip install --no-deps --no-build-isolation -e sources/harness_full
python -c 'import nltk; assert nltk.download("punkt_tab", download_dir=".cache/nltk_data", quiet=True)'
python build_cases.py
python run_original.py
python run_ko.py
python compare.py
python test_audit.py
python package_results.py
sha256sum --check SHA256SUMS
```

이미 복원한 원본 디렉터리를 읽기 전용으로 재사용할 때는 builder·runner·비교기·packager에 같은 `--source-root /absolute/path/to/ifeval_checker_audit`를 전달한다. 그 경로에는 `sources/`와 `.cache/nltk_data/`가 있어야 한다. 이번 실행의 실제 경로·명령·버전·seed·모듈 해시는 원시 결과에 기록했다.

기본 import 모드는 `full-package`다. `--import-mode isolated-source`는 상위 harness 의존성을 불러오지 않고 원본 평가 모듈을 실행하는 대안이며 사용한 모드를 기록한다. 이번 결과는 양쪽 모두 full-package 실행이다. Python `random`과 `langdetect.DetectorFactory` seed는 0이다. source나 NLTK 자원의 해시가 다르면 검증을 중단한다.

`run_original.py`와 `run_ko.py`는 같은 `run_audit.py`를 사용한다. 기본 실행은 평가기당 비교 156건·기준 입력 재현 86건·보조 입력 18건을 처리하므로 실행 횟수는 260회다. 입력 레코드 수 174개와 구별하고, 재현 확인을 지표 분모에 더하지 않는다. `--suite normal|support`로 검사 범위를 선택할 수 있다.

기대값은 평가 실행 전에 선언하고 관측값으로 덮어쓰지 않는다. 기준 자료는 저장된 입력의 LF 해시와 기대값의 입력 해시를 대조한다. 실제 JSON 바이트 해시와 LF 해시를 구별해 checkout의 CRLF 변환을 검사한다. `build_cases.py`는 고정 데이터의 전체 prompt·instruction 순서·kwargs를 보존하고, 반복 ID는 `instruction_index`로 식별한다.

보조 입력의 `expected_original`·`expected_ko`는 각 고정 원본 코드와 seed 0에 근거해 사전 선언한다. 양쪽 full·isolated의 strict·loose Boolean·문항 판정 또는 예외 유형을 각각 검사한다. 원본 checker·NFC·예외 동작의 차이를 유지하며, 관측 결과로 기대값을 덮어쓰지 않는다. 검증 도구 테스트 25개에는 영어 보조 결과 전체를 예외로 바꾸는 변조, 개별 Boolean·예외 유형 변경, 결과 누락·순서 변경을 검출하는 검사가 포함된다.

## 첨부 범위

실험의 입력·원시 결과·비교표·코드·문서·출처 정보와 기대값 추적에 필요한 `baseline.json`을 포함한다. source·가상환경·cache·모델·개인 설정·`context.md`·이슈 초안은 제외한다. `package_results.py`가 검증 후 `attachments/ifeval-ko-regression.zip`과 `.sha256`을 만든다. 압축을 푼 최상위 디렉터리에서 `sha256sum --check SHA256SUMS`로 검사할 수 있다.

ZIP은 필요할 때 생성하는 실험 자료 묶음이다. 이슈 초안 작성과 원격 게시는 별도 범위이며, 이 폴더의 실험 재현에 해당 초안은 필요하지 않다.

## 확장 고정 응답 회귀 (2026-11-03)

실제 데이터 조건에서 `targets`로 지정한 instruction만 집계해 **21종·25개 입력 경로마다 strict·loose 모두 통과(TT)·모두 실패(FF)하는 응답**을 확보했다. 부수적으로 등장한 ID만으로 검증을 완료했다고 보지 않는다. 25개는 정상 kwargs에 따른 입력 경로 수이며 전체 코드 분기 수가 아니다.

13개 개수 조건의 N−1/N/N+1, 1203의 두 index가 만드는 네 Boolean 조합, strict 실패가 loose 통과로 바뀌는 사례를 검사했다. 기준 자료의 객체·입력·판정도 확인했다. `if v` 필터, NFC 적용 위치, 후보 8개의 순서·중복·빈 후보 제외, instruction별 OR·문항별 AND, strict 전체→loose 전체와 단계별 새 객체, 문항별 instruction 수가 다른 집계를 검증했다.

비교표의 `(EN,Ko)`와 경계 표의 `(strict,loose)`는 서로 다른 순서다. 원본의 번역·단위 불일치, 문자열 정규화 비대칭과 내부 예외 처리 결과를 그대로 유지했다. Ko 예상 예외 8건과 영어 예상 예외 2건은 각 평가기의 정상 채점 성공으로 세지 않는다.

새 Ko task에는 같은 입력·응답을 전달해 개별·문항 strict/loose 판정 일치율 100%, 네 지표의 분자·분모 일치와 절대 오차 ≤1e-12, 누락·미처리 예외·미해결 불일치 0을 요구한다. 모델 통합 선정안은 23문항·40개 instruction으로 유지한다. 새 task 검증, 기존 Lighteval 영어/French 회귀·객체 격리·optional dependency 로딩, 모델 통합·전체 split 평가는 미수행이다.
