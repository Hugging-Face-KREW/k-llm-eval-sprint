# IFEval / IFEval-Ko 86건 원본 검증 자료

분석보고서 9.3.1절의 기존 영어·Ko evaluator 비교 실험을 검토하기 위한 부속 자료다. 당시 저장한 입력, 스크립트, 결과 JSON을 변경 없이 복사했다.

실험 범위는 **저장 응답 86건을 영어·Ko evaluator 각각으로 채점한 것**이다. 실제 데이터 조건 46건, 메모리 override 2건, 합성 fixture 38건으로 구성되며 실제 데이터의 고유 key는 11개다. 모델 생성 86회나 새 Lighteval-Ko의 동등성 검증을 뜻하지 않는다.

## 파일 안내

| 자료 | 파일과 확인할 내용 |
| --- | --- |
| 입력·응답 | [cases.json](cases.json): case ID, key, scope, 원본 prompt·instruction·kwargs, 저장 응답, 명시적 override |
| 영어 원시 결과 | [original_results.json](original_results.json): 86건과 당시 실행 환경 |
| Ko 원시 결과 | [ko_results.json](ko_results.json): 같은 case ID 순서의 86건과 당시 실행 환경 |
| 전체 비교 | [results.json](results.json): 입력·양쪽 원시 결과·차이·환경·source revision을 함께 보관 |
| 영어·Ko 실행 | [run_original.py](run_original.py), [run_ko.py](run_ko.py), [audit_runtime.py](audit_runtime.py): 원본 evaluator import와 실제 반환값·호출 trace 수집 |
| 비교·입력 구성 | [compare.py](compare.py), [build_cases.py](build_cases.py) |
| source 복원 | [fetch_sources.py](fetch_sources.py), [provenance.json](provenance.json): 고정 revision과 SHA-256으로 공개 source·데이터 복원 |
| 실행 의존성 | [requirements.lock.txt](requirements.lock.txt), [nltk_resources.json](nltk_resources.json) |
| 첨부 파일 해시 | [SHA256SUMS](SHA256SUMS) |

`results.json`의 `cases[i].case`, `cases[i].original`, `cases[i].ko`는 각각 입력과 양쪽 원시 결과 행에 대응한다. `full`은 문항의 전체 instruction, `isolated`는 대상 instruction만 채점한 결과이며 `diagnostics`는 checker 단독 관찰이다. 세 경로를 구분해서 읽는다.

`environments` 및 각 원시 결과의 `environment`에 있는 executable·cache 경로는 당시 로컬 실행 기록이다. 재실행할 때 그 절대 경로를 그대로 사용할 필요는 없다.

## 확인할 대표 사례

| key | case ID | 대상 조건의 영어 / Ko strict·loose |
| --- | --- | --- |
| 3345 | `robber_full` | 영어 robber 응답 통과·통과 / Ko 강도 응답 실패·실패 |
| 3345 | `robber_keyword_override` | 영어 통과·통과 / Ko keyword를 메모리에서 바꾼 대조군 통과·통과 |
| 3442 | `comma_boundary_compact` | 20단어 실패·실패 / 18단어 통과·통과 |
| 349 | `markdown_quote_valid_highlights_349` | 39단어 통과·통과 / 40단어 실패·실패 |

3345는 언어별로 다른 응답을 사용했다. `controlled_override`와 key가 null인 `synthetic`은 원본 데이터 조건의 실행과 구분하며, 판정 차이를 모두 버그로 해석하지 않는다.

## 고정 revision

| 대상 | revision |
| --- | --- |
| lm-evaluation-harness | `d6de81643928d653435c431bae19945d41d32520` |
| google/IFEval | `966cd89545d6b6acfd7638bc708b98261ca58e84` |
| Allganize IFEval-Ko 코드·데이터 | `54199e3801116897697babf341865741dcd06fc8` |
| 정적으로 참고한 Lighteval | `c2af9e5f2fde494539f84c8ea9d09f18ac9e9c14` |

출처 URL과 원본 파일별 해시는 [provenance.json](provenance.json)에 보존했다. 내려받는 원본 코드의 저작권·라이선스 고지를 유지하며 원본 checker를 수정하지 않는다.

## 재현

재실행은 **이 폴더의 별도 작업용 복사본**에서 수행한다. runner와 비교 스크립트는 같은 이름의 결과 파일을 덮어쓰므로, 첨부된 과거 결과와 새 결과를 구분해 보관한다. 아래 명령의 작업 디렉터리는 복사한 `checker-audit/`다. 설치·공개 source 복원에는 네트워크가 필요하다.

먼저 복사한 첨부 파일의 무결성을 확인한다.

```bash
sha256sum --check SHA256SUMS
```

원본 실행 환경은 WSL·Python 3.12.3이다. 새 가상환경과 source를 구성한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python fetch_sources.py
python -m pip install --no-deps --no-build-isolation -e sources/harness_full
python -c 'import nltk; assert nltk.download("punkt_tab", download_dir=".cache/nltk_data", quiet=True)'
```

보관된 입력을 그대로 사용해 양쪽 evaluator와 비교 스크립트를 실행한다.

```bash
python run_original.py
python run_ko.py
python compare.py
```

입력 구성 과정을 확인하려면 source 복원 후 `python build_cases.py`를 실행할 수 있다. 이 명령은 `cases.json`도 덮어쓴다. `compare.py`는 입력·source·NLTK 자원 hash와 결과의 대응을 검증하고 `results.json`, `results.md`, `dataset_checks.json`을 생성한다. 이 재현 절차는 원본 프로젝트의 명령을 현재 폴더 구조에 맞춰 정리한 것이며, 이번 첨부 과정에서 새 환경 설치나 전체 재실행을 수행한 것은 아니다.

## 첨부 범위

이 폴더에는 기존 86건의 자료만 포함한다. 콘솔 로그 전체, 후속 부등호 42건·Known Issue 23건·metric 재사용 11건·별도 언어 대조군 23건의 원본 자료는 포함하지 않았다. 가상환경, 캐시, 다운로드한 source 전체, 모델 가중치도 첨부하지 않는다. source와 NLTK 자원은 고정 revision·hash를 확인하며 별도로 복원한다.
