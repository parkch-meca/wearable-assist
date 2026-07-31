# Step 1.4 — 모델 수정 feasibility report

**Date**: 2026-04-28
**선행 진단**: [model_limit_diagnosis.md](model_limit_diagnosis.md)

## 수정 대상

`MaleFullBodyModel_v2.0_OS4_modified.osim` 의 4개 CoordinateCouplerConstraint:
- `coupler_shoulder_elv_r` (계수 −1.62)
- `coupler_shoulder_elv_l` (계수 +1.62)
- `coupler_elv_angle_r` (계수 −2.0)
- `coupler_elv_angle_l` (계수 −2.0)

모두 `pelvis_tilt`에 종속.

## 수정 방법

### 옵션 B (단순 제거)

**비용**: XML 편집 1회. 약 4분.
- 파일 사본 생성 → `MaleFullBodyModel_v2.0_OS4_modified_v2.osim` (또는 `..._free_arms.osim`)
- 4개 `<CoordinateCouplerConstraint>` 블록 제거
- 또는 `<isDisabled>true</isDisabled>` 플래그로 무력화 (역공학 안전)

**검증 항목**:
1. `model.initSystem()` 무에러 통과
2. `assemble()` 무에러 통과 (constraint 0개이므로 자동 통과)
3. 직립 자세, 보행 일부 자세에서 muscle path 유효성

### 옵션 C (coupler를 motion에 hardcode)

**비용**: 코드 수정. 약 1시간.
- `apply_state`에서 사용자가 명시적으로 coupler 관계 주입:
  ```python
  shoulder_elv_R = sh_elv_input + (-1.62) * pelvis_tilt_rad  # 단 motion design 시
  ```
- 모델 파일은 손대지 않음 → constraint 그대로 활성

**문제**: constraint가 활성이면 assemble이 여전히 sh_elv를 pelvis_tilt에 묶어버림. 즉 옵션 C는 옵션 B (constraint 제거)를 선행해야 의미 있음.

→ **사실상 옵션 B를 포함하는 옵션**.

## Phase 1a 회귀 검증 절차

Phase 1a는 stoop synthetic v5 motion + Moco Inverse 분석. 다음 항목이 coupler 제거 영향 받을 수 있음.

### 영향 가능성 분석

1. **Stoop motion 자체** (`stoop_synthetic_v5.mot`)
   - .mot 파일은 모든 coord 시간별 값 명시 → coupler 무관 (constraint는 dynamic 자동 enforcement용; 사전 정의 trajectory에는 영향 없음)
   - 단, 기존 .mot이 coupler 관계 만족하는 값을 갖는지 확인:
     - shoulder_elv_R(t) ≈ −1.62 × pelvis_tilt(t) ?
     - 만족 → 제거해도 결과 동일
     - 불만족 → 기존 .mot은 constraint 위반 상태로 사용되었던 것

2. **Moco Inverse 결과**
   - Moco는 .mot의 kinematics를 prescribed motion으로 받음
   - Coupler 제거 시 Moco 내부 dynamic equations 단순화됨
   - 하지만 prescribed motion이 동일하면 muscle activation 결과 동일해야 함

3. **ES activation 패턴 (논문 핵심 결과)**
   - Phase 1a Full result 87.7% / 82.8% / 53.3% (Hold/Con/Ecc)
   - Coupler 제거가 muscle path에 영향? — 어깨 근육에는 영향, ES (척추기립근)에는 무영향 추정
   - 안전을 위해 Phase 1a 재실행 → 수치 동등성 비교 필요

### 회귀 테스트 절차 (옵션 B 채택 시)

1. **모델 사본 생성**: `_modified_v2.osim` (couplers 제거)
2. **빠른 검증**:
   - initSystem 통과
   - 기존 stoop_synthetic_v5.mot 로드 → state 적용 → 위치 vs 원본 모델 비교 (어깨 위치 ±5 mm 이내 예상)
3. **Moco 재실행** (Phase 1a 무부하 stoop):
   - 같은 .mot, 같은 환경, 새 모델
   - 출력: ES activation time-series
4. **수치 비교**:
   - peak_hold, peak_con, peak_ecc 값
   - 차이 > 5%p → 원인 분석 후 협의
   - 차이 < 1%p → 회귀 통과, 모델 v2 채택

### 회귀 실패 시 대응

- 차이가 큰 경우: muscle path 변화 추적 (어깨 근육이 ES에 cross-coupling)
- 그래도 ES 영향 없으면: 단순 어깨 muscle activation 차이만 → 박스 motion 분석에서는 옵션 B 사용, Phase 1a 결과는 v1 모델 결과 유지

## 비용/이익 정리

| 항목 | 옵션 A (P3 자세) | 옵션 B (coupler 제거) | 옵션 D (v4 활용) |
|---|---|---|---|
| 모델 수정 | 없음 | XML 4 블록 삭제 | 없음 |
| Phase 1a 회귀 검증 | 불필요 | **필수** | 불필요 |
| 박스 motion 자유도 | 그라운드 박스만 (5 mm 여유) | 모든 박스 위치 | 기존 v4 결과 |
| 시각적 자연스러움 | Deep lumbar (deadlift-like) | 자유로운 자세 + 어깨 | v4 (이미 검토됨) |
| 향후 확장성 | Limited (자세 변경 시 coupler 재충돌) | High (어깨 자유) | 종료 |
| 시간 비용 | 1시간 (motion v6 설계) | 3-4시간 | 0시간 |

## 권고

**1순위: 옵션 B + 옵션 A 조합**
- Coupler 제거 (B) → 미래 확장성 확보
- 그러나 첫 box motion v6는 P3 자세 (A) 사용 → coupler 제거 후에도 P3 deep posture가 deadlift-like 자연스러움 제공
- Phase 1a 회귀 검증으로 모델 변경 검증

**2순위: 옵션 A 단독**
- Coupler 그대로 유지
- P3 자세로 박스 motion v6 즉시 진행
- Phase 1a 영향 없음
- 단, "양손 측면 잡기 + 어깨 forward elevation 강제" 시각적 어색함 잔존

**3순위: 옵션 D**
- v4 결과로 논문 작성, Phase 2 분석 마무리
- 모델 수정 필요 없음, 작업 종료

다음 사용자 결정에 따라 Step 2 또는 Step 3 직진.
