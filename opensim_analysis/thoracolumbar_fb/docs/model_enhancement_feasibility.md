# ThoracolumbarFB 보강 가능성 (2026-05-04)

**목적**: 박스 들기 가능하도록 ThoracolumbarFB 팔 구조 보강 검토  
**핵심 발견**: 문제는 arm length 단독이 아닌 posture spec + arm length 복합

---

## 0. 핵심 발견 (진단 요약)

```
[가장 중요한 발견]

현재 팔 길이(54.5 cm)로도 극단적 자세에서는 박스 도달 가능:
  - 성공 posture: pelvis_tilt=-75°, hip=110°, knee=-45°, lumbar=-60°
  - 박스까지 거리: 9.5 mm (< 50mm 허용 기준)
  - 단, 이 자세는 biomechanics-agent 스펙 초과 (squat 과도)

v8 시리즈 스펙(pelvis_tilt=-55°)으로는:
  - 141 mm 부족 → 팔을 14.1 cm (26%) 더 길게 해야 해결
  - 또는 발 앞에 15 cm 더 다가서도 104 mm 여전히 부족

결론: 두 가지 문제의 복합
  (1) 팔이 너무 짧음 (54.5 cm vs 인체 80 cm)
  (2) biomechanics-agent 스펙이 ThoracolumbarFB 팔 길이에 비해 박스가 너무 멀음
```

---

## 1. 어깨/팔 Architecture 수정 가능 항목

### 현재 팔 구조 (실측)

```
GH joint center: (0.0003, 0.5015, 0.1706) in ground (standing)
GH height above ground: ~1.407 m
  
세그먼트:
  GH → Elbow center: 29.1 cm  (인체 기준 ~33 cm → -3.9 cm)
  Elbow → distal ulna: 2.3 cm  (실제 전완 분리 없음)
  Distal ulna → hand_R: 24.4 cm  (hand_R body = 전완+손 복합)
  Total GH → hand_R: 54.5 cm  (인체 기준 ~80 cm → -25.5 cm)

shoulder_elv_r ROM: [0°, 154.7°] (팔을 아래로 내리는 방향만 가능)
```

### 수정 가능 항목 목록

| 항목 | 현재값 | 수정 방법 | 추가 reach | Phase 1a 영향 | 검증 난이도 |
|------|--------|---------|---------|------------|-----------|
| Humerus scale (uniform) | 29.1 cm | osim XML body mass/geometry | +2.9 cm (1.1×) | 없음 | 낮음 |
| Arm segment uniform scale | 54.5 cm | 모든 arm body mass + joint offset | +14.1 cm (1.26×) | 없음 | 중간 |
| shoulder_elv_r ROM 확대 | [0°, 154.7°] | osim XML coordinate range | +도달 방향 | 없음 | 낮음 |
| GH position (anterior) | x=0.0003 m | clavicle/scapula joint offset | +전방 도달 | 없음 | 중간 |
| elv_angle 활용도 개선 | [-90°, 155.2°] | 현재 ROM 이미 넓음 | 이미 최대 | 없음 | - |

### Phase 1a 결과 영향 평가

```
ThoracolumbarFB ES 분석 대상:
  L1~S1 erector spinae muscles (76 ES segments, Phase 1a의 핵심)
  이들의 origin/insertion: lumbar1~5, sacrum, pelvis, thoracic

팔 세그먼트 (humerus, ulna, radius, hand):
  - ES muscles와 해부학적 연결 없음
  - 어깨 근육 (deltoid, rotator cuff 등)은 ES와 무관
  
결론: 팔 architecture 변경 → ES 분석 직접 영향 없음
      Phase 1a regression test 예상 ΔES < 0.5 %p (거의 없음)
```

---

## 2. 구체적 보강 방안 A/B/C

### Option A: Humerus Scale 1.1× (최소 침습, 빠른 구현)

```
변경:
  humerus_R/L body mass: 비례 조정 (mass ∝ length^3 기준)
  shoulder_R/L joint의 child frame offset: 길이 1.1× 적용

예상 효과:
  상완 길이: 29.1 → 32.0 cm (+2.9 cm)
  총 reach: 54.5 → 57.4 cm
  v8 스펙에서 부족량: 141 → 126 mm (여전히 부족)
  
판정: PARTIAL — 개선되지만 v8 스펙 도달 불가
      PT=-75 극단 자세는 이미 성공 → Option A는 불필요
```

### Option B: 모든 팔 세그먼트 1.26× Scale (v8 스펙 해결)

```
목표: PT=-55 자세에서 박스 도달 (141 mm 부족 → 0)
필요 scale: 1.26× (현재 54.5 → 68.6 cm)

변경 대상:
  humerus_R/L:    mass/geometry 1.26×
  ulna_R/L:       mass/geometry 1.26×
  radius_R/L:     mass/geometry 1.26×
  hand_R/L:       mass/geometry 1.26×
  모든 joint offset (elbow, radioulnar, radius_hand): 1.26×

예상 효과:
  총 reach: 68.6 cm → v8 스펙(PT=-55) 박스 도달 가능
  인체 기준 대비: 68.6/80 = 85.8% (여전히 인체보다 작지만 작동)
  
주의사항:
  - 근육 경로 (어깨 근육의 via point) 별도 조정 필요
  - 26% scale 확대 → 모델 외관이 부자연스러울 수 있음
  - Methods에 "arm segment geometry was scaled" 명시 필수
  
Phase 1a 영향: ES 분석 무관, regression test PASS 예상
```

### Option C: 박스 거리 조정 (모델 수정 없이 해결)

```
핵심 발견:
  PT=-75, hip=110, knee=-45, lumbar=-60 → 현재 팔로 박스 도달 가능 (9.5 mm)
  
대안: biomechanics-agent 스펙 재검토
  - 박스 거리 30 cm → 20 cm 축소 (box_x = -0.0442 + 0.20 = +0.156 m)
  - pelvis_tilt 허용 범위: -75° (deep stoop으로 재분류)
  - 이 자세는 van Dieen 1997의 "deep stoop" 범위 (trunk angle 80-100°)에 해당
  
장점:
  - 모델 변경 불필요
  - 현재 검증된 모델 구조 유지
  - Phase 1a 완전 유지
  
단점:
  - pelvis_tilt -75° = biomechanics-agent 현재 스펙 (-55°~-60°) 초과
  - biomechanics-agent 재검토 및 동의 필요
  - knee -45° = 스펙 최대치 (-40°) 소폭 초과
```

---

## 3. 보강 후 Reach 예측

```
방안별 박스 도달 여부 (PT=-55 v8 스펙 기준):

Option A (1.1× humerus):  +4.2 cm reach → 여전히 -126 mm 부족  NO
Option B (1.26× all arm): +14.1 cm reach → ~0 mm 부족           YES (이론)
Option C (자세 조정):      모델 변경 없음  → PT=-75 자세로 YES   YES (검증됨)

방안별 박스 도달 여부 (PT=-75 extreme stoop 기준):
현재 모델:  9.5 mm → YES (이미 성공!)
```

---

## 4. 권장 보강 방안

### 권장 1: Option C + 자세 스펙 재설정 (즉시 실행 가능)

```
이유:
1. 현재 팔 길이로 이미 도달 가능 (PT=-75, hip=110, knee=-45)
2. 모델 수정 불필요 → Phase 1a 완전 유지
3. pelvis_tilt -75° = deep stoop = 실제 지면 들기 자연 자세 (van Dieen 1997)
   → "stoop은 trunk angle 80-100°" 문헌 지지

필요 조치:
  1. biomechanics-agent에 PT=-75, knee=-45 허용 여부 재검토 요청
  2. 새 박스 모션 v9: PT=-75, hip=110, knee=-45 기반 설계
  3. Stage 1 IK 실행 + 자가 검증

단점 (논문에 기술 필요):
  - 본 연구 모델의 팔 길이가 인체 기준 대비 31.9% 짧음
  - Deep stoop 자세(PT=-75°)는 일반 lifting 지침과 차이
  - Limitations: "arm reach limitation of ThoracolumbarFB v2.0"
```

### 권장 2: Option B (1.26× scale) 검토 (중기 옵션)

```
이유:
  - Option C로 해결되지 않는 경우
  - v8 스펙(PT=-55) 유지가 필수인 경우

절차:
  1. XML 편집: humerus/ulna/radius/hand body 및 joint offset 1.26×
  2. Phase 1a regression test 실행 (예상 ΔES < 0.5 %p)
  3. 새 모델 저장: MaleFullBodyModel_v2.0_OS4_modified_no_coupler_arm126.osim
  4. Methods에 "arm geometry scaled 1.26×" 명시
  
검토 일정: 필요 시 2-3시간 작업
```

---

## 5. 즉시 다음 단계 권장

CHEOL HOON님 결정 필요 항목:

**Option 선택**:
- A. 자세 스펙 재설정 (PT=-75, knee=-45) + v9 motion 설계 → 가장 빠름
- B. 팔 1.26× scale 후 v8 스펙 재시도 → 2-3시간 추가 작업
- C. 박스 거리 축소 (box_x = +0.156 m, 발 앞 20 cm) + PT=-55 유지 → biomechanics-agent 재검토 필요

**각 옵션의 전제조건**:
- A: biomechanics-agent deep stoop 재검토 승인
- B: Phase 1a regression test PASS 확인
- C: biomechanics-agent 스펙 재설계

---

_분석: opensim-agent (2026-05-04)_
