# 문항 선정 근거 재현

**한국어** | [English](README.en.md)

고정 IFEval-Ko 데이터와 checker를 대조해 문항 선정안의 ID·입력 경로 포함 범위를 집계한다. 모델 생성과 checker 실행은 하지 않는다.

## 자료

- [selection.json](selection.json): 검증 문항 23개 key와 유지할 진단 문항 목록. 선정안은 팀 검토 전 제안이다.
- [audit_coverage.py](audit_coverage.py): 데이터·원본 코드의 SHA-256 확인, registry·checker AST 분석, 선정안 집계.
- [coverage.json](coverage.json): 원본 URL·revision·hash, 스크립트·선정 파일 hash, 환경, 지시 index별 대응과 집계.
- [coverage.md](coverage.md): 같은 결과의 유형별·입력 경로별 표.

## 분모와 집계 범위

고정 revision `54199e3801116897697babf341865741dcd06fc8`의 `train` split은 342문항·481개 지시·21종 ID다. 같은 문항의 반복 ID도 지시 index별로 센다.

`check_following`에서 kwargs로 설정한 속성의 값에 따라 다른 연산·정규식으로 갈라지는 조건을 조사했다. 정상 데이터에 실제 등장하는 분기 값은 `relation`을 쓰는 3종의 각 2개, 추신의 `P.P.S`·`P.S.` 2개다. 나머지 17종은 관찰된 정상 입력에서 해당 값 분기가 없어 ID당 `default` 1개로 센다. 합계는 25개 `(instruction ID, 입력 경로)` 쌍이다. 스크립트는 AST에서 상수와 비교하는 조건을 확인하고, 검토하지 않은 분기 필드·클래스·값이 나오면 중단한다.

이는 코드 분기 실행률이 아니다. 응답에 따른 성공·실패, 누락·잘못된 kwargs·난수 fallback, 추신의 기타 표지, 모든 숫자·문구·언어 값의 조합을 25개로 포함했다는 뜻도 아니다. 이 항목은 [설계 문서 6.2절](../../design.md#fixed-response-regression)의 고정 응답 회귀 범위에서 확인한다. 원본 평가기로 수행한 [156건의 실험 결과](../checker-audit/results.md)를 확인할 수 있다. 새 task 동등성·모델 통합 평가는 아직 실행하지 않았다.

## 재현

운영 저장소 루트에서 실행한다. 집계 환경은 [coverage.json](coverage.json)의 `runtime`에 기록한다.

```bash
python -m pip install "pyarrow==26.0.0"
python teams/team-c-ifeval-ko/evidence/sample-coverage/audit_coverage.py
```

기존 [provenance.json](../checker-audit/provenance.json)의 Ko 원본 URL·hash를 재사용하여 고정 데이터·checker·registry·제작자 문서를 내려받는다. checker 코드는 import하거나 실행하지 않고 AST로 읽는다. 데이터는 임시 폴더에서 읽고 종료 시 정리한다. 결과는 이 폴더의 `coverage.json`·`coverage.md`·`coverage.en.md`에 저장한다.

기존 자료를 덮어쓰지 않고 재현 결과를 확인하려면 별도 출력 폴더를 지정한다.

```bash
python teams/team-c-ifeval-ko/evidence/sample-coverage/audit_coverage.py --output-dir /tmp/ifeval-ko-coverage
```

이미 같은 원본을 보관하고 있으면 `--source-dir <원본폴더>`로 네트워크 다운로드를 생략할 수 있다. 폴더에는 `data/train-00000-of-00001.parquet`, `ifeval_ko/instructions.py`, `ifeval_ko/instructions_registry.py`, `README_Ko.md`가 있어야 한다. 이 경우에도 원본 hash를 검사한다.

## 확인한 결과

| 목록 | 문항·지시 | ID 포함 | 입력 경로 포함 | 반복 ID·복수 지시 |
| --- | --- | --- | --- | --- |
| 선정안 | 23·40 | 21/21 | 25/25 | 1문항·13문항 |

선정안은 키워드 빈도·문장 수·단어 수의 `less than`·`at least`, 추신의 `P.P.S`·`P.S.`를 모두 포함한다. 입력 포함 조건이 충족된 사실과 실제 응답을 검사해 같은 판정이 나오는지는 별개의 확인 항목이다.
