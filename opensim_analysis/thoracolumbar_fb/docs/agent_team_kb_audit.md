# Plan v2 — Day 1 KB Audit (Squat Lift 관점)

**작성일**: 2026-05-26
**작성**: 메인 Claude Code (orchestrator)
**목표**: 기존 7개 문서가 Squat lift 범용 model 시작에 어디까지 cover하는지, gap이 무엇인지 정리
**결정 사항**: Variant C 후보 시드 + Day 2-3 literature-agent gap 보강 spec

---

## 1. 7개 문서 핵심 내용 + Squat 적용성 + Gap

| # | 문서 | 작성일 | 핵심 내용 | Squat 적용성 | Gap |
|---|------|------|---------|------------|-----|
| 1 | `literature_synthesis.md` | 2026-05-10 | Yan 2024 / Hu 2026 / John 2022 / Pinheiro 2023 + NIOSH·REBA + Phase 1a 검증 + Novelty | **부분** — Yan 2024가 squat+stoop 비교했으나 squat 디테일 부족. Pinheiro multi-task는 walk/stair/STS (squat 아님) | Squat 특화 paper 추가 조사, Yan 2024 squat 결과 정밀 추출 |
| 2 | `alternative_fullbody_models.md` | 2026-04-29 | TLFB / LFB / Rajagopal / Holzbaur 비교, **arm reach 기준** | **낮음** — 비교 기준이 박스 reach. Squat은 hip/knee ROM이 핵심 | 각 model의 hip/knee ROM, Squat deep flexion 가능성 비교 부재 |
| 3 | `alternative_models_local.md` | 2026-05-04 | 시스템 내 .osim 7개 목록 + Rajagopal hip [-30°,120°], knee [0°,140°] | **부분** — ROM 일부 있음 | TLFB hip/knee ROM 실측 없음 (Squat 적합성 판정 불가) |
| 4 | `hybrid_model_pros_cons.md` | 2026-04-29 | H1/H2/H3 옵션 + arm reach 보강 + 박스 시나리오 조정 | **낮음** — arm reach 박스 lifting 중심. Squat과 무관 | Squat용 hybrid 필요성 자체 미평가 |
| 5 | `closest_reference_papers.md` | 2026-04-29 | 14 papers Tier 1-3 + Pipeline 모방 | **부분** — Squat 단독 paper 명시 없음 (de Looze, Grabke는 lift 일반 포함) | Squat lift 특화 paper Tier 추가 |
| 6 | `model_enhancement_feasibility.md` | 2026-05-04 | Humerus scale Option A/B/C, **arm reach 박스** | **낮음** — arm reach 중심 | Squat용 enhancement 필요성 미평가 |
| 7 | `model_modification_feasibility.md` | 2026-04-28 | Coupler 4개 제거 + Phase 1a regression 절차 (완료) | **참고** — 이미 적용된 변경 사항 | (완료, gap 없음) |

---

## 2. Squat Lift 관점 — 식별된 Gap 5가지

### Gap 1: Squat lift 특화 biomechanics reference 부재
- `docs/biomech_reference/` 디렉토리 확인 필요 (Day 2 작업)
- 박스 v11에는 `box_lift_natural.md`가 있을 것으로 추정 — Squat은 추정상 없음
- Day 2-3 biomechanics-agent 호출 필요 (Phase 1 외 작업으로 분리)

### Gap 2: Squat EMG/Kinematics 문헌 추출 부족
- Yan 2024가 squat + stoop 비교 했지만 본 docs에는 stoop 결과만 추출됨
- Hu 2026는 lifting 일반 (squat/stoop 구분 불명확)
- **literature-agent 우선 작업**: Yan 2024 squat 결과 정밀 추출 + Squat lift EMG 추가 paper 검색

### Gap 3: Model의 Hip/Knee ROM 실측 부재
- Squat = hip-knee-ankle dominant → hip flexion 100-130°, knee flexion 110-130° 필요
- 기존 docs는 박스 reach 중심 → hip/knee ROM 미평가
- **literature-agent + opensim-agent 협업**: TLFB v2.0 + forearm_v1의 hip/knee ROM 실측

### Gap 4: Variant C (literature 1순위) 후보 미확정
- 기존 박스 기준: Holzbaur 결합 H3 (현실적이지 않음)
- Squat 기준: **미확정** — literature-agent가 결정해야
- 후보 시드 (Day 1 잠정): §3 참조

### Gap 5: Validation 정량 기준의 Squat 적용
- Phase 1a ΔES < 5 %p (기존) — Squat 적용 가능
- Hu 2026 14.9-28.6% ES 감소 — Squat 단독 결과 명시 안 됨
- NIOSH/REBA — Squat 시나리오 LI/REBA 계산 부재
- **literature-agent**: Squat 시나리오 NIOSH LI, REBA 추정 + Hu 2026 squat 결과 추출

---

## 3. Variant C 후보 시드 (Day 2 확정 대기)

### 시드 A: Yan 2024 사용 모델 채택
- Yan 2024가 squat+stoop+exosuit 평가에 사용한 model (Gait2392 추정) 확인 필요
- 장점: 직접 reference 모방
- 단점: ES 분절 해상도 낮음 → 우리 76 ES novelty 손실

### 시드 B: TLFB + Hip/Knee ROM 확장 (자체 보강)
- TLFB v2.0 + forearm_v1 그대로 + hip/knee coordinate range 확장
- 장점: ES 76 분절 유지, baseline과 minimal divergence
- 단점: "literature 1순위"라기보다 자체 변형

### 시드 C: Eskandari 2025 + TLFB
- Eskandari 2025 "Comprehensive spine model + exoskeleton + box lifting" (Applied Ergonomics, PMID: 39489061)
- 장점: lifting task + ES 분석 + exo, 최신 paper
- 단점: 모델 자체 공개 여부 미확인, OpenSim 호환 미확인

### 시드 D: Beaucage-Gauvreau 2019 LFB
- 이미 alternative_models_local에서 평가됨 (L5_S1 only [-11.2°, 3.6°], 박스 부적합)
- Squat에도 lumbar ROM 부족 가능 → **시드 후보에서 제외**

**Day 2-3 literature-agent 최종 추천 → Variant C 확정**

---

## 4. Day 2-3 Literature-agent Spec (Gap 보강)

### 작업 1: Squat lift EMG/Kinematics 문헌 5+ 추출
- 검색: "squat lift erector spinae EMG", "squat lifting biomechanics older worker", "deep squat knee ROM"
- Yan 2024 squat 결과 정밀 (peak ES timing, magnitude, exosuit reduction)
- 산출: `docs/biomech_reference/squat_lift_literature.md` (5+ paper, 정량 spec)

### 작업 2: Squat 시나리오 spec 결정
- 박스 weight (10 kg / 15 kg / 20 kg 중 선택)
- 박스 위치 (지면 / 30 cm pallet)
- Foot stance (양발 동시 / staggered)
- Lift duration (3 s / 5 s)
- 산출: `docs/biomech_reference/squat_scenario_spec.md`

### 작업 3: Variant C 최종 후보 1개 확정
- 시드 A/B/C 평가 → 가장 학술 reference 강한 1개 추천
- Phase 1a regression 가능성 평가
- 산출: `docs/variant_c_recommendation.md`

### 작업 4: Hu 2026 squat 결과 추출 (validation criteria 보강)
- Hu 2026 paper의 lifting style 확인 (squat vs stoop)
- Squat ES 감소 정량 (% reduction)
- 산출: validation_protocol_v2.md §3 추가 데이터

### 작업 5: TLFB hip/knee ROM 실측 (opensim-agent 협업)
- `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_forearm_v1.osim` 의 hip/knee coordinate range
- Squat deep flexion (hip 130°, knee 130°) 가능 여부
- 산출: validation_protocol_v2.md §2 추가 데이터

---

## 5. Day 1 종료 시 사용자 검토 항목

1. ☐ 본 audit 결과 동의?
2. ☐ Gap 5가지 우선순위 동의? (특히 Gap 4 Variant C 후보)
3. ☐ Variant C 시드 A/B/C 중 우선 검토 순위?
4. ☐ Day 2-3 literature-agent 작업 spec 5개 동의?
5. ☐ 신규 agent 2개 (.md) 검토 후 승인?

---

## 6. Next (Day 2-3 plan)

- Day 2 오전: literature-agent 호출 → 작업 1, 2 (squat literature + scenario spec)
- Day 2 오후: literature-agent 작업 3, 4 (Variant C + Hu 2026 squat)
- Day 3 오전: opensim-agent 호출 → 작업 5 (TLFB ROM 실측) + literature-agent 협업
- Day 3 오후: Day 2-3 결과 통합 → Day 4 validation_protocol_v2.md draft

⚠️ **Day 1 종료 시 사용자 검토 후 Day 2 진행**
