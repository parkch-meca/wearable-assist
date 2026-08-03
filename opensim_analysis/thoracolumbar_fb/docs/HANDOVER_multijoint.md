# 인계 문서 — 복합관절(허리+어깨+팔꿈치) 슈트 신규 연구

작성 2026-08-03 · 5동작 논문 완료 시점(커밋 e0545c3) 기준
직전 세션의 채팅 이미지 한도로 새 세션에 이월한다.

> **이 문서의 수치는 전부 `scripts/viz_knee_fix/paper_numbers.py`(단일 소스)에서
> 생성되었다.** 문서를 손으로 고치지 말고, 수치가 바뀌면
> `scripts/viz_knee_fix/gen_handover.py`를 다시 실행할 것.
> 경로는 작성 시점에 실제 존재를 확인한 것만 기재하였다.

---

## 1. 현재 지점

### 1.1 완료 상태

5동작 논문 완료 (커밋 `e0545c3`). ROM 부호 수정 + 좌팔 운동학 정정 + 전 동작 재실행까지 끝났다.

| 항목 | 값 |
|---|---|
| 기저 모델 | `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim` |
| 기저 모델 해시 (SHA-1 앞 12자리) | `e5bb8ab98934` |
| 해석 실행 모델 해시 (reserve 포함, 5동작 10회 전부 동일) | `ca12f321326e` |
| 좌표 수 | 169 |
| 근육 수 | 620 (ES 76) |
| 총 질량 | 77.969270 kg |
| reserve | tight (척추 `_FE`/`_LB`/`_AR`/`Abs_` optimal_force 5 N·m) |
| 척추 reserve 최대 (전 동작) | 1.79 N·m |

### 1.2 최종 수치

주 지표 (b) = **슈트 작동창 ES peak 평균** — 슈트 토크가 최대치의 90 % 이상인 구간에서
프레임별 최대 활성 ES 근육 값의 평균. 창은 ON 조건 토크로 정의하고 OFF에 동일 적용.

| 동작 | 하중 | OFF (%) | ON (%) | Δ (%p) | **Δ (%)** |
|---|---|---:|---:|---:|---:|
| 맨몸 스쿼트 | 0 kg | 60.37 | 37.88 | −22.49 | **−37.3** |
| 맨몸 스툽 | 0 kg | 64.62 | 43.42 | −21.20 | **−32.8** |
| 박스 들기 | 20 kg | 93.40 | 68.80 | −24.60 | **−26.3** |
| 맨몸 보행 | 0 kg | 22.41 | 27.20 | +4.79 | **+21.4** |
| 박스 운반 | 20 kg | 93.32 | 69.36 | −23.96 | **−25.7** |

보조 지표 — (a) 전주기 정점(짝지은 시점), (c) 창내 ES mean 평균:

| 동작 | (a) | **(b) 주 지표** | (c) |
|---|---:|---:|---:|
| 맨몸 스쿼트 | −35.1 % | **−37.3 %** | −39.0 % |
| 맨몸 스툽 | −33.2 % | **−32.8 %** | −31.0 % |
| 박스 들기 | −23.9 % | **−26.3 %** | −24.2 % |
| 맨몸 보행 | −2.8 % | **+21.4 %** | −12.0 % |
| 박스 운반 | −9.3 % | **−25.7 %** | −31.9 % |

### 1.3 핵심 서사

1. **하중 의존성** — 20 kg 두 동작(박스 들기 −26.3 %,
   박스 운반 −25.7 %)이
   0.6 %p 이내로 수렴하고,
   0 kg 두 동작(−37.3 %, −32.8 %)과 뚜렷이 갈린다.
   부하가 상대 효과를 가르는 주 변수다.
2. **보행은 감소가 아니라 재분배** — 주 지표가 +21.4 %로 **증가**하는 반면
   (c) ES mean은 −12.0 %로 감소한다. 근육군으로 분해하면
   장늑근(IL) −90.9 %, 최장근 요추부(LTpL) +28.5 %.
   총량은 −17.38 %p 감소하나 최대 활성 근육으로 집중된다.
   저부하 × 면외 운동(축회전 11.63°·측굴 10.87°) 조합에서만 발생하며,
   스툽(면외 0.00°)이나 운반(20 kg 시상면 부하 지배)에서는 나타나지 않는다.
3. **단조 경향은 지표 간 견고하지 않다** — 부하 순 단조성이 (a)·(b)에서는 성립하나
   (c)에서는 깨진다. 지표 정의는 부수적 선택이 아니라 결론을 좌우하는 설계 요소다.

### 1.4 알려진 한계 (신규 연구에도 이월)

- **포화** — 박스 들기·박스 운반 모두 슈트 OFF 정점이 상한
  (99.99 %, 100.00 %)에 도달한다. 두 동작의 효과는 **하한 추정**이다.
- **단일 체형** — 성인 남성 1개 체형. 고령 간병 인력 대상 정량값은 별도 확장 필요.
- **교차 피험자 GRF** — 보행·운반 지면반력은 다른 피험자 실측값을 체중 스케일로 보정.
  OFF/ON이 동일 GRF를 공유하므로 차이는 견고하다.
- **박스 들기 지면반력 부재** — 골반 reserve가 체중 지지력을 흡수. 절대값 비교 시 유의.
- **Static Optimization 기반** — 활성 동역학·길이–속도 의존성 미반영.

### 1.5 해소된 것

- **viz-mirror 의존 제거** — ROM 수정으로 좌팔이 독립 구동된다.
  렌더와 SO가 같은 운동학을 쓴다. 시각 보정 후처리는 더 이상 필요 없다.
- **좌팔 운동학 오류** — 스툽·박스 들기·박스 운반이 정정되었다 (논문 §2.2.1).

### 1.6 다음 목표

**복합관절(허리 + 어깨 + 팔꿈치) 슈트 신규 논문.**

> ⚠️ 5동작 논문과 **별개 논문**이다. 기존 초안
> (`docs/five_motion_paper_draft.md`)에 병합하지 말 것.

---

## 2. 복합관절 슈트 사양

출처: 사용자 제공 `복합관절_근력보조슈트_구성.pdf`.

> ⚠️ 이 PDF는 **파일시스템에 없다** (2026-08-03 `/data` 전체 검색 결과 미발견).
> 채팅 컨텍스트에만 업로드되어 있다. 새 세션에서 수치가 필요하면
> 사용자에게 재업로드를 요청하거나, 아래 요약을 근거로 진행하고
> 확정 전에 원본과 대조할 것.

### 2.1 구동기 배치

| 부위 | 힘 | 근육옷감 폭 | 목적·경로 |
|---|---|---|---|
| 허리 | 좌우 각 100 N (총 200 N) | 11 mm | 척추기립근 보조 |
| 어깨 | 좌우 각 100 N | 6 mm | 삼각근 보조. 등 뒤 부착 → 웨빙끈 → 삼각근 위 경유 → 상완 결착 |
| 팔꿈치 | 좌우 각 100 N | 6 mm | 이두근 보조 (수축 시 굽힘 보조) |

### 2.2 공통 사양

- SMA 와이어 직경 40 μm, 변태온도 48 ℃
- 근육 용량 10 kg 병렬, 구동부 길이 200 mm
- 길이 조절: BOA 다이얼 및 와이어 (부위별)

### 2.3 지지 구조

- 어깨 지지 밴드(가방끈 형태), 허리 지지 밴드(복대 형태), 허벅지 지지 밴드(안전하네스 형태)
- 냉각 팬 내장

### 2.4 제어

- **6채널** — 1·2ch 팔꿈치(좌/우), 3·4ch 어깨(좌/우), 5·6ch 허리(좌/우)
- 배터리 6S / 22.2 V / 1600 mAh, 제어보드 총 128.1 g (6채널)
- 상시 구동(Constant)이 On/Off 대비 약 **13배** 에너지 효율 (잠열 재투입 불필요)

### 2.5 기존 5동작 논문과의 관계

5동작 논문은 허리만 대상으로 **순수 토크 커플 24 N·m** (= 200 N × 0.12 m)을 썼다.
신규 연구는 같은 허리 사양을 PathActuator로 다시 표현하고 어깨·팔꿈치를 추가한다.

---

## 3. 확정된 모델링 방침

### 3.1 핵심 — PathActuator

슈트를 **PathActuator로 모델링한다** (근육과 동일 방식).
모멘트 암을 고정값으로 가정하지 않고 자세마다 OpenSim이 계산한다.
어깨·팔꿈치는 관절 각도에 따라 모멘트 암이 크게 변하므로 필수다.

| 부위 | 기점 | 경유점 | 종점 |
|---|---|---|---|
| 어깨 | thorax / scapula | 어깨 위 (`clavicle` 또는 `scapula` 좌표계에 고정 — 팔이 움직여도 끈이 그 위를 지나야 함) | `humerus` |
| 팔꿈치 | 상완 | 상완 앞쪽 | 전완 (`radius` / `ulna`) |
| 허리 | 기존 토크 커플 24 N·m 유지 | — | PathActuator 버전과 **교차 검증** |

허리를 두 방식으로 모두 돌리는 이유: 값이 유사하면 상호 검증이 되고,
다르면 어느 쪽이 실제에 가까운지 따져볼 근거가 된다.

### 3.2 부착점 처리

실측값이 없다. PDF 사진에서 해부학적 지표(견봉, 삼각근 조면 등)와 대조해 추정한다.

> ⭐ **부착점 민감도 분석 필수.** 결과가 부착점에 민감하면 그 자체가
> 설계 지침으로서 논문 기여가 된다. 실측값 부재라는 한계를 강점으로 전환한다.

### 3.3 검증 기준

- 모멘트 암 곡선이 자세에 따라 물리적으로 타당한가 (극단 자세에서 부호가 뒤집히지 않는지)
- 대표 자세에서 `100 N × 모멘트 암 = 보조 토크`가 손으로 검산되는가

---

## 4. 팔꿈치 근육 추가 (필수 선행 작업)

### 4.1 현황

`elbow_flexion` / `pro_sup`을 지나는 근육이 **좌우 모두 0개**다
(모멘트암 |r| > 2 mm 기준, `scripts/viz_knee_fix/diag_shoulder_muscles.py`로 실측).
reserve 액추에이터로만 구동되므로 **슈트 효과 측정이 불가능하다.**

### 4.2 추가 대상

biceps (long / short head), triceps, brachialis, brachioradialis.

참조: **Holzbaur 상지 모델**. 본 모델 어깨가 이미 Holzbaur YXY 파라미터화를 따르므로
정합성이 양호하다.

### 4.3 필요 작업

1. 근육 파라미터(최대등척력, 최적섬유장, 건슬랙길이, 부착점, 경유점)를 문헌에서 가져와
   본 모델 골격에 맞게 스케일
2. 검증: 팔꿈치 굽힘 최대 모멘트가 성인 남성 문헌 범위(약 60~80 N·m)에 들어오는지,
   각도별 모멘트 곡선의 형상·피크 위치가 문헌과 부합하는지

> ⚠️ 추가 후 **기존 5동작 결과에 영향이 없는지 확인**할 것 (팔 무게중심 변화 가능).
> 회귀 검증 방법은 §7.1의 조건 정합성 점검과 동일하게, 같은 `.mot`·같은 외력으로
> 재실행해 ES 지표를 대조한다.

---

## 5. 어깨 CoordinateActuator 사전 점검 (필수)

모델에 `shoulder_elv` / `shoulder_rot` / `elv_angle` 좌우 6개의 `CoordinateActuator`가
내장되어 있고, 기존 SO에서 실제로 힘을 낸다 (박스 들기 최대 **21.9 N·m**).

이는 척추 reserve에서 겪은 것과 **동일 구조**다. 전례:
보행 해석에서 표준 reserve가 ES를 3배 과소평가하고 슈트 효과의 부호까지 왜곡했으며,
tight 설정(optimal_force 5 N·m)으로 바꾸고서야 정확해졌다.

> ⚠️ 어깨를 측정 대상으로 삼기 **전에** tight 점검을 해야 한다.
> 하지 않으면 "어깨 슈트가 삼각근 부담을 줄였다"가 실제로는
> reserve 몫을 본 결과일 수 있다.

---

## 6. 평가 시나리오 골격

> ⚠️ **미결정 — 새 세션에서 사용자 확인 필요.**
> 대상 작업 현장이 **산업 현장**(조립·자재 운반)인가 **간병 노동**(환자 이동·부축)인가.
> 대표 동작이 달라진다.

### (a) 부위별 단독 부하 — 각 부위 효과 분리

| 주도 부위 | 동작 |
|---|---|
| 어깨 | 머리 위·어깨 높이 작업 (팔 들어 유지) |
| 팔꿈치 | 무게 들고 팔 굽히기 |
| 허리 | 기존 5동작 재사용 가능 |

### (b) 복합 부하 — 실제 작업 = 세 부위 동시

선반 위 물건 들어 내리기, 물건 들고 이동.

### (c) ⭐ 부위별 기여 분해 (다관절 논문의 핵심)

허리만 ON / 어깨만 ON / 팔꿈치만 ON / 전체 ON.

→ 세 부위 동시 효과가 각각의 합과 같은가, 상호작용이 있는가.
→ 허리 단독 논문에서는 던질 수 없던 질문이며, **복합관절 슈트의 존재 이유와 직결**된다.

---

## 7. 검증 체계 보강

5동작에서 시각 검증(생성자와 분리된 독립 검증자가 그림만으로 판정)은 작동했다.
그러나 아래 항목은 **아무도 보지 않아 사후에 발견**되었다.

| 놓친 것 | 결과 |
|---|---|
| reserve 설정 혼재 (5동작 중 3개가 다른 설정) | 결론 왜곡 |
| 기저 모델 이질성 (동작마다 다른 `.osim`, 문서엔 "공통"으로 기재) | 조건 통일 주장 무효 |
| 문헌 오독 (%MVC 절대 포인트를 상대 감소율로) | 7개 문서에 전파 |
| 박스 좌팔 오류 (외력 작용점과 손 위치 불일치) | 절대 ES 신뢰 불가 |
| 반올림 계산 방식 (인쇄값으로 파생값 재현 불가) | 7곳 불일치 |

시각 검증과 **성격이 다른 종류**의 점검이 필요하다.

### 7.1 조건 정합성 — 새 해석마다 자동 실행

모델 해시 · 좌표 수 · 근육 수 · reserve 설정 · 슈트 사양을 기존 해석과 대조하고,
다르면 의도된 변경인지 확인을 요구한다.

기존 자산: `scripts/viz_knee_fix/audit_conditions.py` (`.osim` / setup.xml /
ExternalLoads / `.sto` 헤더를 추측 없이 직접 읽는다).

### 7.2 수치 재현성 — 문서 작성 시 자동 실행

인쇄된 값으로 파생값이 재현되는지, 여러 문서 간 동일 값이 동일 표기인지 검사한다.
`paper_numbers` 단일 소스 표준을 신규 연구로 확장한다.

기존 자산: `scripts/viz_knee_fix/crosscheck_docs.py`
(md · docx · pdf · pptx 5개 문서를 대조. 2자리·1자리 표기 모두 검사하며,
1자리는 `−90.9 %` 안의 `90.9` 같은 오탐을 막기 위해 앞뒤 경계 조건이 필수).

### 7.3 운동학 정합성 — 외력이 있는 해석마다

- 외력 작용점과 실제 신체 부위 위치가 일치하는가
- 좌우 대칭 의도 동작에서 실제로 대칭인가 (보행처럼 교대가 정상인 동작은 제외)

> ⚠️ 다관절은 부착점·외력이 훨씬 많아 이 점검이 필수다.

기존 자산: `scripts/viz_knee_fix/fix_leftarm_mirror.py`
(좌표별 미러 부호를 축 정의에 기대지 않고 실측으로 확정한 뒤 대칭성을 검사).

---

## 8. 진행 순서

각 단계 결과를 확인하고 다음으로 넘어간다. 복잡도가 높아 중간에 방향이 흐트러지기 쉽다.

| # | 단계 | 상태 |
|---|---|---|
| 0 | 5동작 마무리 | ✅ 완료 (커밋 `e0545c3`) |
| 1 | 팔꿈치 근육 추가 + 검증 | 대기 |
| 2 | 어깨 CoordinateActuator tight 점검 | 대기 |
| 3 | 슈트 PathActuator 모델링 + 부착점 민감도 | 대기 |
| 4 | 평가 시나리오 확정 (**대상 현장 결정 필요**) | 대기 |
| 5 | 검증 체계 보강 | 대기 |
| 6 | 부위별·복합 해석 | 대기 |
| 7 | 신규 논문 | 대기 |

---

## 9. 이월된 확인 사항

### 9.1 투고 전 선행 논문 원문 확인 (사용자 몫)

| 논문 | 확인할 것 |
|---|---|
| Hasenmaier et al. 2026 (`doi:10.3389/fbioe.2026.1631785`) | MES 정규화 기준이 본 연구 ES peak와 대응하는지. 본 연구 스툽 baseline(68.93 %)과 실측 69.8 %MVC의 근접성이 핵심 근거이므로 결정적 |
| Hu et al. 2026 (`PMID 39967340`) | 모멘트 산출 정의 (활성도가 아닌 모멘트·압축력임은 이미 확인) |

### 9.2 기타

- 5동작 논문 **비차단 copy-edit 6건** — 학술지 서식 확정 후 일괄 처리
- **목표 학술지 미정** — 국문 초안 작성됨. 국제지 전환 시 번역 필요
- **박스 파지 폭 변동** — 좌우 손 간격이 파지 구간 중 0.341 → 0.286 m로 변한다.
  좌우 x·y는 모든 시점에서 일치하므로 시상면 모멘트·ES 정량에는 무관하며 논문 §2.2.1에 기록됨.
  향후 동작 생성에서 파지 폭을 제약으로 추가할 것.

---

## 10. 주요 산출물 경로

작성 시점에 실제 존재를 확인한 것만 기재한다.

### 10.1 논문

| 경로 | 크기 | 비고 |
|---|---|---|
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/five_motion_paper.pdf` | 1.7 MB | 최종본 (20쪽, A4) |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/five_motion_paper.docx` | 2.0 MB | 편집용 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/five_motion_paper_draft.md` | 50 KB | 초안 (국문) |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/five_motion_completion_record.md` | 30 KB | 완결 기록 §1–§11 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/shoulder_dof_diagnosis.md` | 14 KB | 좌측 어깨 진단 보고서 |

### 10.2 발표자료

| 경로 | 크기 | 비고 |
|---|---|---|
| `/data/opensim_results/SMA_suit_5motion_presentation.pptx` | 9.4 MB | 33슬라이드, 영상 5종 임베드. ⚠️ 리포지토리 밖 (.gitignore) |
| `/data/opensim_results/SMA_suit_5motion_presentation.pdf` | 6.9 MB | pdf 백업 |
| `/data/opensim_results/ppt_media` | 33개 항목 | 임베드 원본 (squat/stoop/box/gait/carry _ppt.mp4 + figure png) |

### 10.3 모델

| 경로 | 크기 | 비고 |
|---|---|---|
| `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix_rom.osim` | 4.5 MB | **최종 통일 모델**. 기저 해시 `e5bb8ab98934` |
| `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim` | 4.4 MB | ROM 수정 전 (이력 보존용) |
| `/data/romfix_unified/squat_off/model_res_tight.osim` | 4.6 MB | reserve 포함 실행 모델. 해시 `ca12f321326e` — 10회 실행 전부 동일 |

### 10.4 SO 결과 (5동작 × OFF/ON)

| 경로 | 크기 | 비고 |
|---|---|---|
| `/data/romfix_unified/squat_off` | 7개 항목 | 맨몸 스쿼트 OFF |
| `/data/romfix_unified/squat_on` | 7개 항목 | 맨몸 스쿼트 ON |
| `/data/romfix_unified/stoop_off` | 7개 항목 | 맨몸 스툽 OFF |
| `/data/romfix_unified/stoop_on` | 7개 항목 | 맨몸 스툽 ON |
| `/data/romfix_unified/box_off` | 7개 항목 | 박스 들기 OFF |
| `/data/romfix_unified/box_on` | 7개 항목 | 박스 들기 ON |
| `/data/romfix_unified/gait_off` | 6개 항목 | 맨몸 보행 OFF |
| `/data/romfix_unified/gait_on` | 6개 항목 | 맨몸 보행 ON |
| `/data/romfix_unified/carry_off` | 6개 항목 | 박스 운반 OFF |
| `/data/romfix_unified/carry_on` | 6개 항목 | 박스 운반 ON |
| `/data/romfix_unified/unified_numbers.json` | 2 KB | 지표 원본 (paper_numbers 입력) |
| `/data/romfix_unified/gait_redistribution.json` | 2 KB | 보행 재분배 분해 |
| `/data/romfix_unified/comparison.json` | 4 KB | 기존 확정본과의 대조 |
| `/data/romfix_unified/logs` | 10개 항목 | 실행 로그 10건 |

각 디렉터리 내: `so_StaticOptimization_activation.sto`, `so_StaticOptimization_force.sto`,
`setup.xml`, `model_res_tight.osim`, 외력 파일.

### 10.5 동작 파일 (.mot)

| 경로 | 크기 | 비고 |
|---|---|---|
| `/data/stoop_motion/squat_synthetic_v1.mot` | 229 KB | 맨몸 스쿼트 — 무변경 |
| `/data/stoop_results/stoop_v5/v5_30fps_armfix.mot` | 250 KB | 맨몸 스툽 — 좌팔 정정본 |
| `/data/stoop_motion/box_stoop_lift_m1_armfix.mot` | 433 KB | 박스 들기 — 좌팔 정정본 |
| `/data/gait_motion/gait_retarget_so.mot` | 116 KB | 맨몸 보행 — 무변경 |
| `/data/gait_motion/carry_walk_so_armfix.mot` | 142 KB | 박스 운반 — 좌팔 정정본 |

### 10.6 스크립트

수치 단일 소스와 재실행 파이프라인:

| 경로 | 크기 | 비고 |
|---|---|---|
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/paper_numbers.py` | 6 KB | ⭐ **수치 단일 소스**. 표기 규칙 강제, `.sto` 경로표(`STO`) 포함 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/rerun_romfix_all.py` | 6 KB | 5동작 OFF/ON 재실행 (`OMP_NUM_THREADS=1` 필수) |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/analyze_romfix.py` | 8 KB | 지표 (a)(b)(c) 산출 + 기존 대조 + 회귀 검증 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/make_rom_fixed_model.py` | 8 KB | ROM 부호 수정 모델 생성 + 검증 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/fix_leftarm_mirror.py` | 7 KB | 좌팔 미러 부호 실측 확정 + `.mot` 재생성 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/audit_conditions.py` | 13 KB | 해석 조건 전수 감사 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/crosscheck_docs.py` | 6 KB | 5개 문서 수치 일관성 자동 대조 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/analyze_gait_redistribution.py` | 8 KB | 보행 근육군 재분배 + Figure 7 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/make_paper_figures.py` | 10 KB | Figure 3–7 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/make_paper_figures12.py` | 8 KB | Figure 1–2 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/build_paper_docx.py` | 53 KB | 논문 docx 생성 (pdf는 `soffice --headless --convert-to pdf`) |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/build_presentation.py` | 67 KB | 발표자료 pptx 생성 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/gen_handover.py` | 22 KB | 이 문서 생성기 |

렌더 파이프라인: `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/viz_knee_fix/render_*.py`
(26개).
5동작 본 렌더는 `render_box_stoop_video.py`, `render_carry_walk_video.py`,
`render_public_video.py`, `render_public_video_squat.py`, `render_gait_side_color.py`.

### 10.7 대용량 자산 (리포지토리 밖)

| 경로 | 크기 | 비고 |
|---|---|---|
| `/data/wearable-assist-assets/blender` | 3개 항목 | Blender 저작 파일 2종(`muskemo_scene.blend`, `pose2sim_scene.blend`). 동봉 `README.md`에 용도·재생성 가능 여부 기재 |

### 10.8 검증 그리드 (GitHub raw 접근 가능)

| 경로 | 크기 | 비고 |
|---|---|---|
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/shoulder_diag/shoulder_diag_verification_grid.png` | 525 KB | 좌측 어깨 진단 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/shoulder_diag/romfix_rerun_verification_grid.png` | 409 KB | ROM+좌팔 수정 재실행 검증 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/paper_five_motion/paper_final_pages_01_10.png` | 1.3 MB | 논문 1–10쪽 미리보기 |
| `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/paper_five_motion/paper_final_pages_11_20.png` | 1.4 MB | 논문 11–20쪽 미리보기 |

raw URL 형식:
`https://raw.githubusercontent.com/parkch-meca/wearable-assist/main/<repo 상대경로>`

---

## 11. 새 세션 시작 시 먼저 할 것

1. 이 문서를 읽는다.
2. **사용자에게 확인** — §6의 대상 작업 현장(산업 vs 간병).
3. **사용자에게 요청** — §2의 `복합관절_근력보조슈트_구성.pdf` 재업로드
   (파일시스템에 없음).
4. §8의 1단계(팔꿈치 근육 추가)부터 착수. 단계를 건너뛰지 않는다.
