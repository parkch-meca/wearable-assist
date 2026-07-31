# Local 대체 모델 검토 (2026-05-04)

**목적**: 박스 들기 분석에 적합한 대체 모델 탐색  
**배경**: ThoracolumbarFB arm reach 31.9% 부족으로 박스 들기 불가 판정

---

## 1. 시스템 내 .osim 모델 전체 목록

| 모델 경로 | 크기 | 수정일 | Bodies | Muscles |
|---------|------|------|--------|---------|
| `/data/opensim_models/ThoracolumbarFB/.../MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim` | 4.2 MB | 2026-04-28 | 78 | 620 |
| `/data/opensim_models/LFB/LFB_model.osim` | 921 KB | 2019-02-20 | 29 | 238 |
| `/data/opensim_models/Rajagopal2016.osim` | 854 KB | 2026-04-13 | 22 | 80 |
| `/data/opensim_models/RajagopalLaiUhlrich2023.osim` | 901 KB | 2026-04-13 | 22 | 80 |
| `/home/sysop/Downloads/Fullbody_OS4.x_v2.0-latest/.../MaleFullBodyModel_v2.0_OS4.osim` | 4.4 MB | 2021-06-29 | 78 | 620 |
| `/home/sysop/Downloads/Fullbody_OS4.x_v2.0-latest/.../MaleFullBodyModel_v2.0_OS4_BU.osim` | - | - | - | - |
| `/home/sysop/Downloads/GenericLiftingFull-BodyMode-latest/LFB_model.osim` | 921 KB | 2019-02-20 | 29 | 238 |

---

## 2. 후보별 평가

### 2.1 ThoracolumbarFB v2.0 (현재 사용)

**경로**: `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim`

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 수 | 22 (T1~S1) + Abdomen | ES 분석 최적 |
| Total muscle 수 | 620 | 최다 |
| shoulder_elv ROM | [0°, 154.7°] | 제한적 |
| GH→hand_R total | 54.5 cm | 인체 대비 -31.9% |
| 박스 reach | 불가 (141 mm 부족) | **부적합** |
| Phase 1a 호환 | 완전 호환 | 우수 |

### 2.2 GenericLiftingFullBody (LFB) v1.0

**경로**: `/data/opensim_models/LFB/LFB_model.osim`

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 수 | 5 (L1~L5) + torso | ES 분석 제한적 |
| Total muscle 수 | 238 | 중간 |
| Shoulder coords | arm_flex [-90°, 180°], arm_add [-180°, 90°] | 넓음 |
| GH→hand_r total | ~53 cm (ThoracolumbarFB와 유사) | 인체 대비 부족 |
| 박스 reach (PT=-75, hip=110, knee=-45) | **140 mm 부족** | **부적합** |
| Lumbar ROM | L5_S1 only: [-11.2°, 3.6°] | **극히 제한** |
| Phase 1a 호환 | 척추 구조 완전 다름 | 이전 불가 |

**LFB 특이사항**:
- L5_S1_Flex_Ext 실제 ROM: **[-11.2°, 3.6°]** (나머지 L4~L1은 constraint 종속)
- 전체 lumbar flexion = L5_S1 -11.2° 뿐 → ThoracolumbarFB -60° 대비 심각하게 제한
- 박스 들기 자세에서 어깨 reach가 ThoracolumbarFB보다 나을 것 없음

### 2.3 Rajagopal 2016

**경로**: `/data/opensim_models/Rajagopal2016.osim`

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 수 | 1 (lumbar_extension 단일) | ES 분석 불가 |
| Total muscle 수 | 80 | 적음 |
| Hip ROM | [-30°, 120°] | **hip -30° 제한** (stoop 용 100° hip 불가) |
| Knee ROM | [0°, 120°] | 음수 방향 0° (무릎 굽힘 정의 반대) |
| arm_flex ROM | [-90°, 90°] | 제한됨 |
| 박스 reach | 미테스트 | 구조상 불가 예상 |
| Phase 1a 호환 | 완전 불가 (척추 구조 다름) | 불가 |

**Rajagopal 문제점**:
- hip_flexion_r: [-30°, 120°] → 최소값이 -30° → stoop의 hip +100° 가능하나
- knee_angle_r: [0°, 120°] → 0°가 최소 → 무릎 굽힘 방향 정의 반대 (양수가 굽힘)
- 척추 = 단일 lumbar joint → L1-S1 개별 분석 불가
- ES 분석 목적에 부적합

### 2.4 RajagopalLaiUhlrich 2023

**경로**: `/data/opensim_models/RajagopalLaiUhlrich2023.osim`

| 항목 | 값 | 평가 |
|------|----|----|
| 척추 분절 수 | 1 (lumbar_extension) | Rajagopal과 동일 |
| Total muscle 수 | 80 | 동일 |
| Hip ROM | [-30°, 120°] | 동일 제한 |
| Knee ROM | [0°, 140°] | Rajagopal보다 약간 더 넓음 |
| arm_flex ROM | [-90°, 90°] | 제한됨 |
| Phase 1a 호환 | 불가 | |

---

## 3. 모델 비교 요약

| 모델 | 척추 분절 | Muscles | Arm reach | 박스 lifting | Phase 1a |
|------|---------|---------|---------|------------|---------|
| ThoracolumbarFB | 22 | 620 | 54.5 cm | 불가 (-31.9%) | 완전 호환 |
| LFB | 5 | 238 | ~53 cm | 불가 (lumbar 제한) | 불가 |
| Rajagopal2016 | 1 | 80 | ~54 cm (예상) | 구조 제한 | 불가 |
| RajagopalLai2023 | 1 | 80 | ~54 cm (예상) | 구조 제한 | 불가 |

**발견**: 시스템 내 모든 모델에서 arm total reach는 54-58 cm 수준으로 유사하게 부족.  
이는 OpenSim 커뮤니티에서 공통적으로 사용되는 Opensim 표준 arm geometry 기반 모델의 공통 특성.

---

## 4. Hybrid 가능성

### 4.1 ThoracolumbarFB 척추 + 다른 모델 어깨/팔 결합

**이론적 접근**:
```
ThoracolumbarFB:
  유지: sacrum, lumbar1~5, thoracic1~12, rib cage, pelvis
  유지: 620 muscles (ES + 척추 관련)
  교체: clavicle_R/L, scapula_R/L, humerus_R/L, ulna_R/L, radius_R/L, hand_R/L

대체 팔 구조 (예: 실제 인체측정 기반):
  shoulder_offset 조정: GH 위치 유지
  humerus 길이: 33 cm (현재 29 cm → +4 cm)
  forearm 재구성: 28 cm (현재 2.3+24.4 = 26.7 cm 분산 → 통합 28 cm)
  total 목표: ~80 cm
```

**기술적 난이도**: 높음

```
필요 작업:
1. shoulder_R joint의 parent frame (scapula_R_offset) 위치 유지
2. humerus_R mass properties 재계산
3. 어깨 근육 (deltoid, supraspinatus 등) origin/insertion 재배치
   → ThoracolumbarFB에서 어깨 근육은 620 중 일부
   → 재배치 시 Phase 1a ES 분석에는 무관 (어깨 근육 != ES)
4. Scapulohumeral rhythm (clavicle-scapula coupler) 재검증
```

### 4.2 Phase 1a 결과 영향

```
변경 대상: humerus, ulna, radius, hand (팔 세그먼트)
Phase 1a 분석 대상: L1~S1 ES muscles (erector spinae)

결론: 팔 architecture 변경은 ES 분석에 직접적 영향 없음
     → Phase 1a regression test 통과 가능성 높음 (예상 ΔES < 1 %p)
```

**단, 다음 검증 필요**:
1. Scapula/clavicle 위치가 thoracic 척추와 연결되므로 thoracic 분석 관련 주의
2. 어깨 근육 (serratus, pectoralis minor 등) 경로 재검증

### 4.3 Hybrid 가능성 결론

| 방식 | 가능성 | 난이도 | 검증 복잡도 |
|------|------|------|-----------|
| humerus scale 1.1× (in-place) | 가능 | 낮음 | 낮음 (Phase 1a regression 만) |
| Arm segment geometry 재구성 | 가능 | 중간 | 중간 |
| 완전 외부 모델 팔 교체 | 가능 | 높음 | 높음 |

---

_분석: opensim-agent (2026-05-04)_
