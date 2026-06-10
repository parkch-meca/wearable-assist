# TLFB 비례 왜곡 + 근육 풍선 원인 진단 (사실 확인)

**일자:** 2026-06-11
**대상 모델:** `MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim` (forearm_v1 제거 버전)
**목적:** 비례 왜곡(다리 짧음/상체 과대) + 근육 풍선이 (a) TLFB 모델 결함인지 (b) MuSkeMo 시각화 도구/설정 문제인지 **사실로 분리**. 추측·patch 없음, 진단만.

---

## 분기 판정: **C (MuSkeMo 시각화 설정 문제)** — TLFB 모델 결함 아님

세 가지 독립 사실이 모두 모델 결함을 배제하고 시각화 원인을 가리킴.

---

## [1] 뼈 길이 실측 (OpenSim API, default pose, joint-center 거리)

| 분절 | TLFB | Rajagopal | De Leva 1996 (175 cm) | 판정 |
|------|------|-----------|----------------------|------|
| femur (hip→knee) | **0.424 m** | 0.408 m | ~0.42 m | ✅ 정상 (오히려 약간 김) |
| tibia (knee→ankle) | **0.443 m** | 0.396 m | ~0.43 m | ✅ 정상 |
| humerus (shoulder→elbow) | 0.291 m | — | ~0.33 m | 약간 짧음(어깨 JC 정의 차이) |
| joint-center Y span | 1.480 m | 1.380 m | — | 정상 |

→ **모델 좌표상 다리는 짧지 않다. femur·tibia 모두 표준 이상.** "다리 짧음"은 좌표 결함이 아님.
→ 측면(side) 렌더에서도 다리뼈가 정상 길이로 완전히 보임. front view에서 짧아 보인 것은 전면 체간 근육 덩어리가 다리를 가린 **착시**.

## [2] Geometry mesh inventory

| 모델 | 참조 mesh(unique) | 존재 | 누락 |
|------|------|------|------|
| **TLFB no_coupler** | 130 | **130** | **0** |
| Rajagopal2016 | 81 | 81* | 0* |
| Lai 2023 | 81 | 81* | 0* |

\* 전역 `/data/opensim_models/Geometry`는 비어 있으나, 메시는 `opensim-gui/opensim-models/Geometry` 및 TLFB Geometry 폴더에 전부 존재(대조군 렌더에 사용).

→ **TLFB 뼈 mesh 누락 0개. 풍선은 뼈 누락 때문이 아니다.**

## [3] MuSkeMo 근육 굵기 알고리즘

- 기본 import는 `SimpleMuscleNode` (geometry node) + bevel 사용.
- 굵기 = `Curve Circle`의 **단일 씬 전역 상수** `muskemo.muscle_visualization_radius`, **기본값 0.015 m (지름 30 mm)**.
- **F_max와 무관.** F_max는 속성으로 저장만 되고, 옵션 `VolumetricMuscleViz`(사용자가 따로 켜야 함)에서만 부피 계산에 사용 (`CompareVolMuscVizVolumes.py`).
- 즉 **620개 근육 전부가 동일한 15 mm 반경 튜브**로 그려짐.

→ **근육 굵기는 비정상 force 때문이 아니라 고정 튜브 반경 설정 때문.** 조정 가능한 단일 파라미터.

## [4] 대조군 비교 렌더 (동일 파이프라인·카메라·radius 0.015, wrap/joint/landmark 숨김)

| 모델 | 근육 수 | 외형 |
|------|--------|------|
| **TLFB** | **620** | 척추·늑골 위 튜브 밀집 → 체간 붉은 덩어리(풍선). 다리는 측면에서 정상. |
| Rajagopal | 81 | 뼈 명확, 정상 인체 비례, 풍선 없음 |
| Lai 2023 | 80 | 동일하게 정상 |

→ 같은 도구·같은 설정인데 **TLFB만 풍선** = 근육 수(620 vs 80, 약 7.7배)와 고정 튜브 반경의 조합.
→ Rajagopal/Lai에도 동일 튜브 아티팩트가 있으나 근육이 적어 **약하게** 나타남.

---

## 결론 (사실 기반)

1. **비례 왜곡 = 착시, 모델 결함 아님.** 다리뼈 좌표 정상(femur 0.424 / tibia 0.443). front view에서 체간 근육 덩어리가 다리를 가려 "다리 짧음/상체 과대"로 보임.
2. **근육 풍선 = MuSkeMo 시각화 설정.** 620개 근육 × 고정 15 mm 튜브 반경(F_max 무관). 단일 파라미터로 조정 가능.
3. **mesh 누락 없음**, wrapping sphere는 별도 collection(`Wrapping geometry`) + `Joint centers`·`Landmarks` 구로 렌더에서 숨기면 사라짐(본 grid에서 처리).

### 사용자 결정 필요 (자동 진행 안 함)
- 동영상 진행 전, 다음 중 택일을 위한 판단 필요:
  - (i) `muscle_visualization_radius` 축소(예: 0.005–0.008 m)로 풍선 완화
  - (ii) 근육 일부만 표시(예: 척추기립근군만) 하여 체간 가독성 확보
  - (iii) VolumetricMuscleViz(F_max 기반 부피)로 전환 — 해부학적이나 더 무거움
  - (iv) 현 상태 유지 + 측면/후면 위주 카메라로 다리 비례 보이게

*(Akhavanfar SimTK 모델 도착 시 대조군 grid에 추가 예정)*

**산출물:** `docs/images/literature_review/muskemo_proportion_diagnosis_grid.png` (3 모델 × 4 view)
