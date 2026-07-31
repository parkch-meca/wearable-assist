# Variant C Recommendation (Plan v2)

**작성일**: 2026-05-26
**작성**: literature-agent (Day 2 작업 3)
**목적**: Plan v2 §3.1 Variant C "literature 1순위" 최종 확정
**입력 docs**: `agent_team_kb_audit.md` §3 (시드 A/B/C), `squat_lift_literature.md` §3-5
**최종 결정**: 시드 C (Eskandari 2025) **불채택** → **대안 D (Akhavanfar 2024 Enhanced FATLS) 채택**

---

## 1. 사용자 우선순위 평가

### 우선순위 1: 시드 C (Eskandari 2025, PMID 39489061) OpenSim 호환 확인

**조사 결과: 호환 X (확정)**

- **Citation**: Eskandari AH, Ghezelbash F, Shirazi-Adl A, Arjmand N, Larivière C. *Appl Ergon* 2025;123:104407. doi:10.1016/j.apergo.2024.104407
- **소속**: Polytechnique Montréal (Shirazi-Adl 그룹)
- **사용 모델**: **EMG-assisted optimization 자체 model + Finite Element 통합** (SSRN 2023 SubjectSpecific Integrated FE-MS Trunk model, Ghezelbash et al.)
- **OpenSim 호환**: ❌ **No** — in-house 통합 FE+MS, OpenSim에 없음
- **공개 여부**: 모델 자체 미공개 (paper에서 commercial 또는 internal use 추정)
- **결론**: 시드 C는 **Plan v2 Variant C 후보에서 제외**

### 우선순위 2 (호환 X 시 fallback): 시드 B (TLFB + hip/knee ROM 확장)

평가 (`agent_team_kb_audit.md` §3 시드 B 평가 재확인):
- 장점: ES 76 분절 유지, baseline divergence 최소, 우리가 자체 검증 가능
- 단점: **"literature 1순위"라기보다 자체 변형**. 학술 reference 없음
- **fallback 추천도**: 중간 — 대안 D가 더 강하면 D 채택, D가 호환 X이면 B fallback

### 우선순위 3: 시드 A (Yan 2024 Gait2392 추정)

- Yan 2024 P1: "participant-specific musculoskeletal models in OpenSim" 명시 but **base model 미공개**
- 추가 조사: Yan + Anderson 그룹은 Bruno 2015 TLFB 사용 가능성 높음 (Anderson DE = TLFB 저자)
- 단점: ES 분절 해상도 차이 (Gait2392는 단일 ES, TLFB는 76 분절) → novelty 손실
- **A 추천도**: 낮음 (시드 C 또는 D가 더 강함)

---

## 2. 대안 D 평가 (literature-agent 추가 발굴)

### Akhavanfar M, Mir-Orefice A, Uchida TK, Graham RB (2024)

**Citation**: *An Enhanced Spine Model Validated for Simulating Dynamic Lifting Tasks in OpenSim*. *Ann Biomed Eng* 52(2):259–269. PMID 37741902. doi:10.1007/s10439-023-03368-x

**소속**: University of Ottawa (Graham RB) + University of Ottawa Mechanical Eng (Uchida TK)

**모델**:
- **Enhanced Fully Articulated Thoracolumbar Spine (FATLS)**
- **Base**: Bruno AG, Bouxsein ML, Anderson DE 2015 Thoracolumbar Spine (= 우리 TLFB v2.0 직계 조상)
- **Enhancement**:
  1. Passive structures (ligaments, intervertebral disc passive stiffness)
  2. Kinematic constraints for dynamic task
  3. Updated muscle parameters

**OpenSim 호환**: ✅ **OpenSim 3.3 + OpenSim 4.4 두 버전 제공**

**공개**: ✅ **SimTK group_id=2108** ([download URL](https://simtk.org/frs/?group_id=2108))
- `NewFATLSModelValidation.rar` (29 MB, OpenSim 3.3 + MATLAB scripts)
- `NewFATLSModelValidation-OpenSim4_4.rar` (23 MB, **OpenSim 4.4 + Python scripts**)
- `Geometry.rar` (4 MB)
- **License: MIT** (open source)
- Total 1,208 downloads, 8 followers, peer-reviewed 활용 사례 다수

**Validation**:
- **9 dynamic lifting/lowering tasks**
- Spinal force estimation r > 0.9 (강력)
- Bruno 2015 model의 static-only 한계 해결

---

## 3. 우리 baseline (TLFB v2.0 + forearm_v1) vs Akhavanfar Enhanced FATLS

| 항목 | TLFB v2.0 (우리 baseline) | Akhavanfar 2024 Enhanced FATLS |
|------|--------------------------|-------------------------------|
| Base | Bruno 2015 | Bruno 2015 (= 동일 직계) |
| Spine segments | T1–T12 + L1–L5 (fully articulated) | T1–T12 + L1–L5 (fully articulated) — **동일** |
| ES fascicles | 76 (우리 검증) | 동일 (Bruno 76개 유지) — 확인 필요 |
| Lower limbs | Rajagopal 기반 fully | Bruno full body — 차이 미세 |
| Forearm | forearm_v1 patch (우리 추가) | 미명시 — 미패치 가능성 |
| Passive structures | 기본 (ligament 없음) | **추가** (ligament, IVD passive stiffness) |
| Kinematic constraints | Coupler 4개 제거 (우리 변형) | **자체 dynamic constraint** 추가 |
| Validation | Phase 1a static SO (28% reduction) | **dynamic 9 tasks (r > 0.9)** |
| OpenSim 버전 | 4.x | **3.3 + 4.4** |
| 우리 변경 적용성 | n/a (baseline) | forearm_v1 + Coupler 제거를 Akhavanfar에 patch 적용 필요 |

**호환 평가**:
- ✅ Base 모델 동일 → Phase 1a regression 가능 (max ΔES < 5 %p 가능성 높음)
- ⚠️ Akhavanfar passive structure 추가로 static loading 약간 변동 가능 → regression 확인 필요
- ⚠️ forearm_v1 patch + Coupler 제거 우리 변경을 Akhavanfar에 재적용 필요 (1-2 일 작업)

---

## 4. 최종 추천: Variant C = Akhavanfar 2024 Enhanced FATLS

### 채택 사유
1. **OpenSim 4.4 호환** (우리 환경 직접 사용 가능)
2. **SimTK 공개 + MIT license** (학술 정당성 + 재현성)
3. **Bruno 2015 동일 base** → Phase 1a regression 가능
4. **Dynamic lifting 9 tasks validated** (squat lift 직접 적용 가능)
5. **Passive structures + kinematic constraints** → 우리 박스 motion 5개월 patch 패턴 (kinematic 한계) 해결 기대
6. **Plan v2 Squat lift target에 정확히 부합** (paper 자체가 dynamic lifting validation)

### 단점/위험
1. forearm_v1 + Coupler 제거 우리 변경을 Akhavanfar에 재적용 필요 (1-2 일 추가)
2. Day 3 Phase 1a regression 결과 max ΔES > 5 %p 시 채택 보류 → 시드 B fallback
3. 모델 검증된 lifting task가 우리 squat 시나리오와 정확히 일치하지 않을 가능성 (paper 9 tasks 상세 확인 Day 3)

### 위험 → fallback 시 채택
- 시드 B (TLFB + hip/knee ROM 확장) — 자체 변형, literature 약함
- 시드 A (Yan 2024 base) — Yan 2024 model 직접 공개 X, 추정 의존

---

## 5. parallel-explorer-agent에 전달 spec

```yaml
Variant A (baseline):
  model: MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim
  status: 검증 완료 (Phase 1a 28% ES reduction)
  비교 기준

Variant B (Hybrid H1):
  model: TLFB v2.0 + humerus scale-up (forearm_v1 강화)
  status: hybrid_model_pros_cons.md §H1
  novelty: arm reach 보강

Variant C (literature 1순위):
  model: Akhavanfar 2024 Enhanced FATLS (OpenSim 4.4)
  source: https://simtk.org/frs/?group_id=2108 → NewFATLSModelValidation-OpenSim4_4.rar
  license: MIT
  base: Bruno 2015 Thoracolumbar (= 우리 baseline 동일 조상)
  Enhancement: passive structures + kinematic constraints
  Validation: 9 dynamic lifting tasks (r > 0.9, Akhavanfar 2024)
  우리 적용 patch 필요: forearm_v1 + Coupler 제거 재적용
  Day 3 priority: SimTK download + Phase 1a regression test
```

---

## 6. 다음 단계 (Day 3)

1. **opensim-agent 호출** (병렬):
   1. TLFB v2.0 hip/knee ROM 실측 (현 baseline에서 deep squat 110° 가능 여부)
   2. Akhavanfar Enhanced FATLS OpenSim 4.4 다운로드 + 로드 + ROM 실측
   3. Akhavanfar에 forearm_v1 + Coupler 제거 patch 적용 시도
2. **literature-agent 추가** (필요 시): Akhavanfar paper 본문 추출 (validated 9 tasks 상세, ES fascicle 수)
3. **Day 3 검토 후 Day 4**: validation_protocol_v2.md draft에 Variant C 확정 반영

---

## 7. 만약 Akhavanfar 채택 불가 시 fallback

조건: Phase 1a regression max ΔES > 5 %p OR Akhavanfar 모델 로드 실패

→ **Variant C 시드 B (TLFB + hip/knee ROM 확장)** 채택, "literature 1순위" 표현은 "자체 변형 + Bruno 2015 base validation 인용"으로 약화

대안 후보 (시드 B 외):
- **MyoBack** (Zhu et al. 2025, bioRxiv): MyoSuite 환경, OpenSim 모델 변환 가능. exo 통합 검증된 추가 후보
- **Beaumont 2021 lumbar+lower limb** (Tandfonline doi:10.1080/10255842.2021.1886284): open-source validated lumbar model
- 둘 다 trunk-only or sub-model이므로 우리 full-body 요구에 미흡 → 시드 B fallback이 더 안전
