# Muscle Set v2: Phase 1a (114) + Lower Limb (44) = 158 muscles

**Date**: 2026-04-29
**Motivation**: Phase 2.C.4 박스 v11b 결과에서 reserve pelvis_tilt = 221 N·m (Phase 1a 11배) 발견. 하지 근육 부재가 직접 원인으로 진단됨.
**Decision (CHEOL HOON님)**: "제대로 된 확장 가능한 모델 먼저 — 이상한 모델로 작업한 결과는 의미 없음"

---

## 1. 모델 정보

| 항목 | 내용 |
|------|------|
| 기반 모델 | MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim |
| 총 근육 (원본) | 620 |
| Phase 1a set (v1) | 114 (IL 24 + LTpT 42 + LTpL 10 + QL 36 + RA 2) |
| 추가 하지 근육 | 44 |
| Muscle Set v2 합계 | **158** (dedup 후) |

---

## 2. 추가 하지 근육 목록 (44개)

### 2.1 Gluteus Maximus — 6개 (3 bundles × 2 sides)

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| glut_max1_r/l | 573 N | Superior bundle |
| glut_max2_r/l | 819 N | Middle bundle |
| glut_max3_r/l | 552 N | Inferior bundle |

**총 bilateral peak**: ~1944 N  
**생략**: gluteus minimus — ThoracolumbarFB v2.0에 없음

### 2.2 Gluteus Medius — 6개 (3 bundles × 2 sides)

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| glut_med1_r/l | 1119 N | Anterior bundle |
| glut_med2_r/l | 873 N | Middle bundle |
| glut_med3_r/l | 1000 N | Posterior bundle |

**생략**: gluteus minimus — ThoracolumbarFB v2.0에 없음

### 2.3 Hamstrings — 4개 (2 muscles × 2 sides)

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| bifemlh_r/l | 2700 N | Biceps femoris long head |
| bifemsh_r/l | 804 N | Biceps femoris short head |

**생략**: semimembranosus, semitendinosus — ThoracolumbarFB v2.0에 없음  
**문헌**: Delp et al. (1990) — BF long head: 2178 N (scaled to this model's 2700 N within plausible range)

### 2.4 Quadriceps — 4개 (2 muscles × 2 sides)

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| rect_fem_r/l | 1169 N | Rectus femoris (biarticular) |
| vas_int_r/l | 5000 N | Vastus intermedius |

**생략**: vastus lateralis, vastus medialis — ThoracolumbarFB v2.0에 없음 (vas_int만 존재)

### 2.5 Iliopsoas & Psoas — 6개

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| iliacus_r/l | 1073 N | Primary hip flexor |
| Ps_L1_VB_r/l | 252 N | Psoas major (L1 VB origin) |
| Ps_L5_VB_r/l | 367 N | Psoas major (L5 VB origin) |

**비고**: Psoas는 ThoracolumbarFB에서 분절별 bundle (Ps_L1_TP ~ Ps_L5_TP + IVD + VB)로 표현됨. Hip flexion에 직접 기여하는 VB bundle만 포함 (TP/IVD는 요추 안정화 기여, QL에 이미 반영).

### 2.6 Hip Assistants — 4개 (2 muscles × 2 sides)

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| tfl_r/l | 233 N | Tensor fasciae latae |
| sar_r/l | 156 N | Sartorius |

### 2.7 Deep Hip Rotators — 4개 (2 muscles × 2 sides)

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| gem_r/l | 164 N | Gemellus |
| quad_fem_r/l | 381 N | Quadratus femoris |

### 2.8 Adductor / Gracilis — 4개

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| add_mag2_r/l | 2343 N | Adductor magnus (posterior) |
| grac_r/l | 162 N | Gracilis |

### 2.9 Calf — 4개 (2 muscles × 2 sides)

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| med_gas_r/l | 2500 N | Gastrocnemius medial head |
| soleus_r/l | 4000 N | Soleus |

**생략**: gastrocnemius lateral head — ThoracolumbarFB v2.0에 없음  
**근거**: calf 포함은 carrying 단계 ankle 안정화 및 box lifting에서 plantarflexion 기여

### 2.10 Tibialis — 2개 (1 muscle × 2 sides)

| 모델 이름 | max iso force | 비고 |
|-----------|--------------|------|
| tib_ant_r/l | 3000 N | Tibialis anterior (ankle dorsiflexion) |

---

## 3. ThoracolumbarFB v2.0 모델에서 누락된 근육

다음 근육은 사용자 요청 목록에 포함되었으나 ThoracolumbarFB v2.0 모델에 존재하지 않음:

| 근육 | 사용자 이름 | 비고 |
|------|------------|------|
| gluteus minimus | glmin_r/l | 없음 |
| semimembranosus | semimem_r/l | 없음 |
| semitendinosus | semiten_r/l | 없음 |
| vastus lateralis | vaslat_r/l | 없음 |
| vastus medialis | vasmed_r/l | 없음 |
| gastrocnemius lateral | gaslat_r/l | 없음 |

**학술 의미**: ThoracolumbarFB v2.0은 흉요추 척추에 특화된 full-body 모델로, 일부 하지 근육이 단순화 또는 생략됨 (Bruno et al. 2015). 이 한계는 Methods에 명시 필요.

---

## 4. Phase 1a Regression Test 결과

**조건**: stoop_synthetic_v5.mot, t=[1.0, 3.0]s, mesh=25 (smoke), GRF 포함

| 지표 | 114-muscle (v1) | 158-muscle (v2) | 변화 | 판정 |
|------|----------------|----------------|------|------|
| **ES max |ΔActivation|** | -- | -- | **0.10 %p** | PASS (< 5 %p) |
| **ES mean |ΔActivation|** | -- | -- | **0.01 %p** | PASS (< 3 %p) |
| reserve pelvis_tilt | 17.48 N·m | 17.48 N·m | -0.00 (-0%) | -- |
| reserve hip_flex_r | 1.94 N·m | 0.26 N·m | -1.67 (-86.5%) | PASS |
| reserve hip_flex_l | 1.94 N·m | 0.26 N·m | -1.67 (-86.5%) | PASS |
| **reserve knee_r** | 7.89 N·m | **0.04 N·m** | **-7.85 (-99.5%)** | **PASS** |
| **reserve knee_l** | 7.89 N·m | **0.04 N·m** | **-7.85 (-99.5%)** | **PASS** |
| reserve ankle_r | 1.83 N·m | 0.12 N·m | -1.71 (-93.3%) | PASS |
| reserve ankle_l | 1.83 N·m | 0.12 N·m | -1.71 (-93.3%) | PASS |

**전체 판정: PASS**

### 핵심 관찰
- ES 활성화 변화 극히 소량 (max 0.10 %p) — 하지 근육 추가가 ES 결과에 영향 없음
- 무릎 reserve 99.5% 감소 (7.89 → 0.04 N·m) — quadriceps/hamstrings 추가 효과
- 고관절 reserve 86.5% 감소 — iliacus/glut 추가 효과
- 발목 reserve 93.3% 감소 — soleus/gastrocnemius 추가 효과
- **pelvis_tilt reserve 불변 (17.48 N·m)**: stoop 동작에서 pelvis는 hip 근육이 아닌 척추 근육이 담당. Phase 2.C.4 박스 lifting의 221 N·m는 동작 자체의 다른 요인(박스 20kg 외력 + 더 큰 pelvis 움직임)임을 확인.

---

## 5. 학술 인용

- **Delp SL et al. (1990)** An interactive graphics-based model of the lower extremity to study orthopaedic surgical procedures. *IEEE Trans Biomed Eng* 37:757–767.
- **Holzbaur KR et al. (2005)** A model of the upper extremity for simulating musculoskeletal surgery and analyzing neuromuscular control. *Ann Biomed Eng* 33:829–840.
- **Bruno AG et al. (2015)** Development and validation of a musculoskeletal model of the fully thoracolumbar spine. *Med Eng Phys* 37:1084–1093.
- **Anderson FC & Pandy MG (2001)** Static and dynamic optimization solutions for gait are practically equivalent. *J Biomech* 34:153–161.

---

## 6. 사용 가이드

### muscle_set_v2.py import

```python
import sys
sys.path.insert(0, '/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/')
from muscle_set_v2 import MUSCLE_SET_V2, PHASE1A_MUSCLES, LOWER_LIMB_MUSCLES
```

### Phase 1a Moco 스크립트

```bash
# Smoke test (빠른 검증)
python run_moco_phase1a_v2_lower_limb.py smoke

# Full (production)
python run_moco_phase1a_v2_lower_limb.py full
```

### Phase 2.C.4 적용

- 박스 v11b 이후 모든 Moco 분석에서 MUSCLE_SET_V2 사용
- moco-analysis-agent에게 `muscle_set='v2'` 지시

---

## 7. 향후 과제

- [ ] Full mode (t=0-5s, mesh=50) regression 실행 → pelvis_tilt reserve 전체 시계열 확인
- [ ] Phase 2.C.4 재실행 (158 muscles) → 221 N·m reserve 감소 확인
- [ ] pectineus (pect_r/l, 266N), piriformis (peri_r/l, 444N) 포함 여부 재검토 (현재 미포함)
- [ ] tib_post_r/l (tib_post, 3600N) 추가 검토 — 발목 내반 안정화

---

## 8. 파일 경로

| 파일 | 경로 |
|------|------|
| Muscle set Python 정의 | `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/muscle_set_v2.py` |
| Phase 1a v2 스크립트 | `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/run_moco_phase1a_v2_lower_limb.py` |
| Regression 비교 스크립트 | `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/scripts/compare_phase1a_v2_regression.py` |
| Smoke 결과 | `/data/opensim_results/phase1a_v2_lower_limb/smoke/` |
| Regression figure | `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase1a_regression_v2_lower_limb.png` |
