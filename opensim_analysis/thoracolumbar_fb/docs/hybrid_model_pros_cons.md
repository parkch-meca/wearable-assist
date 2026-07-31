# Hybrid 모델 학술 평가 (2026-04-29)

**작성**: biomechanics-agent
**목적**: Step 3 — ThoracolumbarFB 척추 + 보완된 팔 geometry를 결합하는 hybrid 접근의 학술 타당성 평가
**배경**: 박스 motion 9번 연속 실패의 근본 원인 = arm reach 31.9% 부족 (54.5 cm vs 인체 ~80 cm)

---

## 1. 학술적 정당성 평가

### 1.1 Hybrid 모델 정의

본 문맥에서 "Hybrid"는 세 가지 가능성:

- **옵션 H1**: ThoracolumbarFB 그대로 + humerus segment scale-up (가장 단순)
- **옵션 H2**: ThoracolumbarFB 척추 + 재구성된 forearm/hand geometry (중간 복잡도)
- **옵션 H3**: ThoracolumbarFB 척추 + Holzbaur UE model 팔 결합 (최고 복잡도)

---

### 1.2 옵션 H1: Humerus Scale-up (권장)

**변경 내용**: `humerus_R/L` segment mass center만 조정, forearm/hand geometry 수정

```
현재:
  GH→elbow: 29.1 cm (humerus_R mass_center = 0 -0.1197 0)
  elbow→hand_R: ~2.3 + 24.4 = 26.7 cm
  Total: 54.5 cm

목표:
  GH→elbow: 33 cm (+3.9 cm, scale factor 1.134)
  elbow→hand_R: 27 cm (forearm body 재정의)  
  Total: ~60 cm (인체 대비 약 -25%, 개선)
```

**전달 의미**: 이 조정만으로는 54.5 → ~60 cm. 여전히 ~120 mm 부족.

**더 적극적 조정** (ulna+radius+hand 재구성):
```
humerus: 29.1 → 33 cm (+3.9 cm)
forearm body (ulna+radius 통합 재정의): 2.3+24.4 → 28 cm (재배치)
Total: 33 + 28 = ~61 cm → 여전히 ~19 cm 부족
```

**한계**: OpenSim 모델에서 elbow→hand 구간의 geometry 재구성은 joint offset 변경 + mass center 재계산 필요. 팔 근육(deltoid, triceps 등)의 origin/insertion 경로도 재검증 필요.

---

### 1.3 사전 사례 (박스 lifting 목적 모델 결합)

#### 사례 1: Exoskeleton + 기존 모델 결합 (Favennec et al. 2026)

```
Favennec A et al. (2026). Effects of a soft back exoskeleton on lower lumbar spine loads
during manual materials handling: a musculoskeletal modelling study.
Computer Methods in Biomechanics and Biomedical Engineering. PMID: 39492646

방법: CORFOR exoskeleton을 validated musculoskeletal model에 추가
"15 participants lifted a box, with and without wearing a CORFOR"
→ 외부 장치를 기존 모델에 append — ES 분석 포함
→ 모델 자체 변경보다 외부 force element 추가
```

**관련성**: 기존 모델에 exoskeleton force를 추가하는 방식 = 본 프로젝트 SMA suit force와 동일 접근. Methods 작성 사례로 참고 가능.

#### 사례 2: EMG-driven subject-specific (Hu et al. 2026)

```
Hu F et al. (2026). Influence of varied assistance levels provided by a dual-joint active 
back-support exoskeleton on spinal musculoskeletal loading and kinematics during lifting.
Ergonomics. PMID: 39967340

방법: Subject-specific musculoskeletal model (8 subjects)
→ 개인 맞춤 모델 + EMG-driven approach
→ L5S1 compression + back muscles active moment 분석
```

**관련성**: ES force analysis 방법론 참고. 하지만 arm geometry 변경 사례 아님.

#### 사례 3: ThoracolumbarFB 자체 변형 사례 (본 프로젝트)

```
기존 변형 작업 (이미 완료):
- MaleFullBodyModel_v2.0_OS4_modified.osim: CoordinateCouplerConstraint 4개 제거
- MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler.osim: WeldJoint 변환
- Phase 1a regression test: max ΔES = 1.16 %p (PASS)

결론: 모델 구조 변경 전례 있음. Arm geometry 변경도 유사 검증 절차 적용 가능.
```

---

## 2. 각 옵션별 상세 평가

### 2.1 옵션 H1: Humerus Scale 단독

| 항목 | 평가 |
|------|------|
| 기술적 난이도 | 낮음 — XML mass_center 값 변경만 |
| 학술 정당성 | 중간 — 인체측정 근거 제시 필요 |
| Phase 1a 영향 | 매우 낮음 — ES와 팔 segment 무관 |
| Regression test | 간단 — ΔES < 1 %p 예상 |
| 재현성 | 높음 — 숫자 변경 1-2개, 재현 쉬움 |
| Reach 개선 | ~54.5 → ~60 cm (+5.5 cm) | 
| 박스 도달 여부 | 여전히 ~120 mm 부족 |
| Methods 작성 가능? | 가능 ("anthropometric scaling of arm segments") |
| **결론** | **부분 개선, 완전 해결 아님** |

### 2.2 옵션 H2: Forearm Geometry 재구성

| 항목 | 평가 |
|------|------|
| 기술적 난이도 | 중간 — ulna/radius body 위치 변경 + joint offset 수정 |
| 학술 정당성 | 중간 — 인체측정 + joint geometry 근거 모두 필요 |
| 어깨 근육 영향 | 팔꿈치 이하 변경 → deltoid/rotator cuff 영향 없음 |
| 전완 근육 경로 | ThoracolumbarFB에 전완 근육 있다면 재검증 필요 |
| Phase 1a 영향 | 낮음 (ES와 무관) |
| Reach 개선 | ~54.5 → ~70-75 cm (forearm 재구성 성공 시) |
| 박스 도달 여부 | 개선 가능성 있음 (natural stoop에서) |
| Methods 작성 가능? | 가능하나 complexity 증가 |
| **결론** | **잠재적 해결책, 중간 리스크** |

**ThoracolumbarFB forearm 현황 (실측)**:
```
GH center:    (0.0003, 0.5015, 0.1706) [ground frame, 직립]
Elbow center: (0.0064, 0.2111, 0.1583)  → GH→elbow = 29.1 cm
Distal ulna:  (0.0068, 0.1996, 0.1783)  → elbow→ulna_end = 2.3 cm (비정상)
hand_R:       (0.0248, -0.0424, 0.2033) → ulna→hand = 24.4 cm

문제: ulna body가 2.3 cm만 표현됨 (실제 전완 길이 ~27 cm의 8%)
     hand_R body가 전완 하부 + 손을 모두 포함하는 복합 body
```

### 2.3 옵션 H3: Holzbaur UE 결합

| 항목 | 평가 |
|------|------|
| 기술적 난이도 | 매우 높음 — 완전히 다른 joint architecture 결합 |
| 학술 정당성 | 높음 — Holzbaur 자체가 검증된 모델 |
| 척추-어깨 연결부 | clavicle/scapula joint location 재정의 필요 |
| 근육 경로 | Holzbaur의 50 muscle compartments 재배치 |
| Phase 1a 영향 | 낮음 (ES와 팔 무관) but 검증 복잡 |
| Reach 개선 | ~54.5 → ~75-80 cm (완전 해결) |
| 박스 도달 여부 | 해결 가능 |
| Methods 작성 가능? | 어려움 — 두 모델 결합의 validation 필요 |
| 개발 시간 | 수주~수개월 |
| **결론** | **완전 해결이지만 현실적이지 않음** |

---

## 3. 권장 vs 비권장

### 3.1 즉각 권장 (단기, v9 시도)

**방향 A: 박스 높이 조정 (가장 현실적)**

```
현재 박스: bottom y = -0.905 m (지면), center y = -0.755 m
조정 박스: bottom y = -0.605 m (30 cm 높이 팔레트 위), center y = -0.455 m
→ 현재 모델로 도달 가능한 높이 (low pallet level)
```

**학술 정당성**:
- 실제 요양 현장: 박스가 지면이 아닌 낮은 선반/팔레트에 위치하는 경우 다수
- ES 부하 분석 목적: 지면 박스와 팔레트 박스의 ES 차이 비교 → 오히려 연구 가치 있음
- 논문 Methods: "Box positioned at 30 cm height (pallet level) to accommodate model reach constraints while maintaining clinically relevant lifting scenario"

**방향 B: 발 위치 박스 쪽으로 이동 (자연스러운 전략)**

```
현재: calcn_r x = -0.044 m 고정 (발 앞 30 cm에 박스)
변경: calcn_r x = +0.10 ~ +0.15 m (발이 박스 바로 앞, 앞으로 이동 허용)
→ pelvis→box 거리 감소 → 도달 가능
```

**학술 정당성**:
- Geissinger et al. 2020: 실제 작업자의 대다수가 발을 박스 쪽으로 이동
- 발 이동은 자연스러운 인체 전략 — 발 고정 전제가 오히려 비현실적
- 노인 여성에서 더 빈번한 전략

**단점**: "발 고정 stoop"이라는 기존 Phase 1a와의 연속성 단절. 다른 시나리오.

---

### 3.2 중기 권장 (수주, v10+)

**Forearm Geometry 재구성 (옵션 H2)**:

```python
# XML 수정 예시 (MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim)
# 1. ulna_R body mass_center 수정: 0 -0.12 0 → 0 -0.13 0 (전완 길이 25 cm)
# 2. ulna_R→hand_R joint location 수정: 
#    현재: 0 -0.24 0 → 수정: 0 -0.28 0 (전완 길이 27-28 cm)
# 3. hand_R body mass_center: 0 -0.068 0 → 0 -0.065 0 (손 7 cm)
# 검증: GH→hand_R 측정
```

**Phase 1a Regression test 절차**:
1. 수정된 모델로 stoop_synthetic_v5.mot SO 재실행
2. ES peak 비교: 기준 대비 ΔES < 5 %p이면 PASS
3. 합격 시 박스 motion 재시도

**Methods 작성 가능**: "Arm segment geometry was corrected to match published anthropometric data (Winter 1990; De Leva 1996). The upper arm length was set to 33 cm and total forearm length to 27 cm based on 50th percentile male anthropometry. These modifications did not affect the erector spinae muscle representation, as confirmed by Phase 1a regression testing (ΔES < X %p)."

---

### 3.3 비권장

**옵션 H3 (Holzbaur 결합)**: 개발 기간 과다, 검증 복잡. 논문 마감 시한 고려 시 비현실적.

**박스 위치를 극단적 자세로 억지 도달**: v8/v8b/v8c에서 이미 시도. pelvis_tilt -75°, knee -45°는 biomechanics spec 위반. 논문에 이 자세를 "natural stoop"으로 기술 불가.

---

## 4. 학술 타당성 요약 테이블

| 방향 | 학술 정당성 | 재현성 | Methods 기술 가능 | 개발 시간 | 박스 도달 | 권장 |
|------|-----------|-------|----------------|---------|---------|------|
| A: 박스 높이 조정 (팔레트) | 높음 | 높음 | 쉬움 | 1일 | YES | **1순위** |
| B: 발 이동 허용 | 높음 | 높음 | 쉬움 | 1-2일 | YES | **2순위** |
| H1: Humerus scale | 중간 | 높음 | 가능 | 2-3일 | 부분 | 3순위 |
| H2: Forearm 재구성 | 중간-높음 | 중간 | 가능 | 1-2주 | 가능 | 4순위 |
| H3: Holzbaur 결합 | 높음 | 낮음 | 어려움 | 수주 | YES | 비권장 |
| 극단 자세 강제 | **없음** | - | 불가 | - | - | **금지** |

---

## 5. 다음 단계 제안 (사용자 결정용)

**CHEOL HOON님이 결정해야 할 사항**:

1. **박스 시나리오 정의**: 지면(y=-0.755) vs 팔레트/선반(y=-0.455 ~ -0.600)
   - 지면 고집 시: 발 이동 허용 or 모델 팔 재구성 필요
   - 팔레트 허용 시: 즉시 v9 진행 가능

2. **발 이동 허용 여부**: 자연스러운 인체 전략과 일치하지만 Phase 1a 제자리 stoop과 시나리오 차이

3. **개발 시간 vs 논문 마감**: H2 (forearm 재구성)은 가장 학술적으로 견고하나 시간 소요

**즉각 실행 가능한 테스트 (opensim-agent에 전달)**:

```python
# 박스 높이 변경 테스트 (1일 내)
BOX_BOTTOM_Y = -0.605   # 팔레트 위 박스 (ground = -0.905)
BOX_HEIGHT = 0.30
BOX_CENTER_Y = BOX_BOTTOM_Y + BOX_HEIGHT/2  # = -0.455 m
# → 현재 모델 low pallet reach: ≥ 3 mm 여유 (reach_analysis.md P3 자세 기준)

# 발 이동 테스트 (발 앞 10 cm 박스, 발이 5 cm 전진)
CALCN_NEW_X = -0.044 + 0.05  # 발이 5 cm 전진
BOX_X = CALCN_NEW_X + 0.10   # 발 앞 10 cm
# → pelvis→box 거리 감소 → 도달 가능성 계산 필요
```

---

## 6. 인용 문헌

1. **Holzbaur KRS, Murray WM, Delp SL (2005).**
   A model of the upper extremity for simulating musculoskeletal surgery and analyzing neuromuscular control.
   *Annals of Biomedical Engineering 33(6): 829-840.* PMID: 16078622

2. **de Zee M, Hansen L, Wong C, Rasmussen J, Simonsen EB (2007).**
   A generic detailed rigid-body lumbar spine model.
   *Journal of Biomechanics 40(6): 1219-1227.* PMID: 16901492

3. **Favennec A, Moissenet F, Frère J, Mornieux G (2026).**
   Effects of a soft back exoskeleton on lower lumbar spine loads during manual materials handling: a musculoskeletal modelling study.
   *Computer Methods in Biomechanics and Biomedical Engineering.* PMID: 39492646
   - Precedent for appending external device to validated MSK model

4. **Winter DA (1990).** Biomechanics and Motor Control of Human Movement. Wiley.
   - Standard anthropometric data (segment lengths, mass centers)

5. **De Leva P (1996).**
   Adjustments to Zatsiorsky-Seluyanov's segment inertia parameters.
   *Journal of Biomechanics 29(9): 1223-1230.*
   - Arm segment scaling data (forearm 0.146 × body height)

6. **Geissinger J, Alemi MM, Simon AM, Chang S, Asbeck A (2020).**
   Quantification of Postures for Low-Height Object Manipulation Conducted by Manual Material Handlers in a Retail Environment.
   *IISE Transactions on Occupational Ergonomics and Human Factors.* PMID: 32673178
   - Real workers move feet toward box; foot-fixed assumption is unrealistic

---

_작성: biomechanics-agent (2026-04-29)_
_참조: thoracolumbar_fb_reach_envelope.md (실측 data), real_human_box_lift_data.md (문헌), alternative_fullbody_models.md (모델 비교)_
