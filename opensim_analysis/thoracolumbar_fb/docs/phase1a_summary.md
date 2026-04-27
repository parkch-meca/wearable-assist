# Phase 1a Summary — One-page Overview

**Date**: 2026-04-28 · **Result**: ✅ PASS · **Wall time**: 140 s

> **TL;DR**: MocoInverse + GRF로 stoop lifting의 erector spinae(ES) activation dynamics를 정량화. SO로는 얻을 수 없는 5-phase 구조와 eccentric/concentric 비대칭 패턴을 검출. 슈트 효과 분석에 phase-targeted 설계 가능성 시사.

## 1. 무엇을 했나

114개 Phase 1a 근육 (IL 24 + LTpT 42 + LTpL 10 + QL 36 + RA 2)을 가진 ThoracolumbarFB 모델에 5 초 stoop motion(`stoop_synthetic_v5.mot`)을 prescribed kinematics로 주고, MocoInverse로 muscle activation 시계열을 최적화. GRF는 ExternalLoads로 통합 (양발 vy ≈ 367.9 N).

- Solver: OpenSim Moco 4.5.2 + CasADi/IPOPT
- Mesh: 50 intervals (Hermite-Simpson)
- Reserve actuators: optF = 10 Nm (spine FE), 10 N (translations) — SO R10에 대응
- 결과: **Optimal Solution Found in 140 seconds**

## 2. 핵심 발견 3가지

### (1) 5-phase activation 구조

stoop 동작이 5 단계로 나뉘며, 각 단계의 ES 부하가 명확히 구분됨:

| Phase | 시간 | IL_R10_r mean | 의미 |
|---|---|---:|---|
| Quiet | 0.0–1.0 s | 8 % | 직립 baseline |
| Eccentric | 1.0–2.0 s | **53 %** | 굽히는 동안 ES 신장 수축 |
| Hold | 2.0–2.5 s | **88 %** | 최대 굽힘 유지 |
| Concentric | 2.5–4.0 s | **83 %** | 펴는 동안 ES 단축 수축 |
| Recovery | 4.0–5.0 s | 28 % | 직립 복귀 |

→ Hold + Concentric이 부하의 **75–80 %를 담당**. SO는 이 시간 구조를 모름.

### (2) Eccentric/Concentric 비대칭 (논문 핵심 후보)

같은 정도의 spine flexion이 발생하는 두 phase에서 ES 활성도가 크게 다름:

| 근육 | Eccentric | Concentric | **Δ (con−ecc)** |
|---|---:|---:|---:|
| IL_R10_r | 53 % | 83 % | **+29 %p** |
| IL_R10_l | 53 % | 81 % | +28 |
| LTpL_L5_r | 33 % | 46 % | +13 |
| LTpL_L5_l | 33 % | 47 % | +14 |
| IL_R11_r | 10 % | 22 % | +12 |

→ Concentric이 Eccentric보다 **평균 50 % 더 높은 activation**. 이는 SMA suit assist를 phase-targeted로 설계하면 효과 차별화 가능함을 시사.

### (3) SO 대비 새로 얻은 정보

| | SO (R10) | MocoInverse |
|---|---|---|
| 시점별 activation | ✅ 시점 snapshot | ✅ 연속 시계열 |
| Activation dynamics (시간 결합) | ❌ | ✅ |
| Phase별 부담 분포 | ❌ | ✅ |
| Eccentric/concentric 구분 | ❌ | ✅ |
| Spine FE reserve at peak | 22 Nm | 19.4 Nm (일치) |
| Wall time | 21 min/조건 | 140 s 전체 |

## 3. 다음 단계 권고

| 우선순위 | 후보 | 기대 효과 |
|---|---|---|
| **1** | **슈트 효과 분석 (옵션 c)** — 24 Nm thor/pel 토크 추가하고 ES Δ 측정 | §1.6 28.97 % 결과를 Moco 기준으로 재산출 → 논문 헤드라인 즉시 업데이트 |
| 2 | Phase 1b — MF/EO/IO 추가 후 부담 분담 정량화 | 개별 sub-experiment로 논문 별도 섹션 |
| 3 | Phase 2 — 박스 들기 MocoInverse + 손 외력 | KNOWN_LIMITATIONS의 박스 영상 근본 해결 |
| 4 | 성별/연령 확장 (65세 여성 모델) | 일반화 제외. 모델 스케일링 작업 별도 큼 |

## 4. 산출물 위치

- 보고서: [`results/phase1a_full/full_report.md`](../../results/phase1a_full/full_report.md)
- 폴리시드 figure: [`docs/images/phase1a_full/figure_5phase_activation.png`](images/phase1a_full/figure_5phase_activation.png), [`figure_summary_polished.png`](images/phase1a_full/figure_summary_polished.png)
- Solution: `results/phase1a_full/solution.sto` (gitignored)
- 스크립트: [`scripts/run_moco_phase1a_full.py`](../scripts/run_moco_phase1a_full.py), [`scripts/analyze_phase1a_full.py`](../scripts/analyze_phase1a_full.py)
- 기술 노트: [`docs/phase1a_technical.md`](phase1a_technical.md)
- 논문 draft: [`docs/phase1a_paper_draft.md`](phase1a_paper_draft.md)
