# 걷기 동작 — 모션 소스·GRF·ES 지표 현황 조사 (착수 전, 2026-07-24)

박스 들기 완성 후 4번째 동작(걷기) 착수 전 사실 확인. **자동 진행 X — 경로는 사용자 결정.**

## [1] 걷기 모션 소스 후보

| 소스 | 보유 | TLFB 적용 필요작업 | 품질 | 비고 |
|------|------|--------------------|------|------|
| **gait2354 subject01_walk** (IK .mot + GRF .mot) | ✅ 로컬(OpenSim 배포) | 하체 **직접매핑** + 척추 분산 + **팔 합성 스윙** + GRF COP 정렬 | **高** | 실측 gait kinematics + 실측 GRF. 1.2s(~1주기) |
| gait1018 Moco walk (armless) | ✅ 로컬 | 하체 매핑 + 척추 + 팔 합성 (armless 소스) | 中 | 10 DOF 단순, arm 없음 |
| 합성(synthetic) 생성 | — | 양발 교대접지·체중이동·골반회전·이중지지 전부 합성 | 低~中 | **난이도 높음, 비권장**(stoop/squat과 차원 다름) |
| human2humanoid (`/data/retargeters`) | ✅ 있으나 SMPL→휴머노이드 로봇용 | OpenSim gait 부적합 | 부적합 | H2O/OmniH2O 로봇 텔레옵, 목적 다름 |

### 좌표 호환 (gait2354 → TLFB)
- **직접 매핑 ✅**: pelvis(6), hip_flexion/adduction/rotation r/l, knee_angle r/l, ankle_angle r/l (동일 이름·convention)
- **분산 필요**: gait2354 `lumbar_extension/bending/rotation`(허리 3 DOF 통짜) → TLFB 17분절 FE/LB/AR로 분산(stoop 방식 재사용)
- **TLFB에 없음**: subtalar_angle(무시 가능, 소영향), mtp(무시 가능)
- **팔 없음**: gait2354는 팔 좌표 없음 → **팔 스윙 합성 필요**

## [2] GRF

- **보유**: `subject01_walk1_grf.mot` — 실측 보행 GRF. 좌/우 발 교대(`ground_force_v/p` + `l_ground_force_v/p` + `ground_torque`). 수직 피크 **~770 N**(78 kg).
- **stoop GRF와 차이**: stoop은 양발 고정·일정 수직력. 보행은 **스탠스↔스윙 교대** → 각 발 GRF가 0(swing)↔피크(stance)로 순환, COP(px/pz)가 발 따라 이동.
- **사용 방안**: gait2354 하체를 **직접 매핑하면 발 접지 타이밍이 보존** → 기존 GRF 직접 사용 가능. 단 **COP(ground_force_px/pz)가 retarget된 TLFB 발밑에 오는지 좌표 정렬 확인 필요**(pelvis_tx/tz 앵커 + lab frame offset).

## [3] ES 지표 주의점 (중요)

- 보행 ES는 **낮고 순환적**(heel strike·contralateral loading 부근 피크 ~5~15% MVC). 직립이라 허리 부담 작음.
- **baseline 작음 → % 감소 불안정**(분모 작아 % 튐). 박스(37.5%)·stoop(88%)처럼 큰 baseline이 아님.
- **슈트는 들기용**(24 N·m 신전 보조). 직립 보행선 효과 미미하거나, 오히려 체간 자연 흔들림(trunk sway)을 저항할 수 있음.
- **권장**: 보행은 "슈트가 정상 보행을 **방해하지 않는가**"(가동성·편안함) 관점, 또는 ES **절대변화(%p)** + **gait phase별 피크**로 보고. **"부담 X% 감소" headline은 부적합**(baseline 작아 오해 소지).

## [4] ★ 새 관건 — viz-mirror가 걷기엔 안 맞음

- 박스 표준 **viz-mirror**(오른팔 mesh를 z반사해 왼팔로 렌더)는 **양팔이 같은 동작(대칭 파지)** 전제.
- **걷기는 팔이 좌우 반대로 스윙(비대칭)**: 오른다리 앞 → 왼팔 앞, 오른팔 뒤. viz-mirror는 좌=우 미러라 **양팔을 대칭으로 강제** → 걷기 arm swing 불가.
- 원인: 모델 왼팔(shoulder_L/wrist_l) 축이 오른팔 복사본(원본 결함)이라, 왼팔을 독립적으로 자연 구동 불가 → 박스에선 viz-mirror로 우회했으나 걷기엔 그 우회가 막힘.
- **선택지**:
  - (A) 모델 왼팔 관절축을 제대로 미러(구조 수정, regression) → 좌우 독립 팔 스윙 가능
  - (B) 팔 스윙을 최소/대칭으로(자연스러움 다소↓, viz-mirror 유지)
  - (C) 팔 스윙 없이 팔 중립 고정(걷기 팔 없음 = 부자연하나 하체·ES는 유효)

## [5] 후보 프레임
- `docs/images/phase2_box/gait_candidate_frame.png`: gait2354 t=1.0(우 stance/좌 swing)를 TLFB 하체 직접 매핑 + 발 접지 앵커. **다리 stride 정상 retarget 확인.** 팔은 [4] 문제로 부자연(viz-mirror가 비대칭 스윙 못 살림).

## 권장 경로 + 근거

**gait2354 subject01_walk retarget** (하체 직접 + 척추 분산 + GRF 기존 사용). 실측 kinematics+GRF로 품질 高, 합성보다 현실적·저위험.
**단 두 선결**: (i) 팔 스윙 — [4] 선택지 결정(A 구조수정 vs B/C 단순화), (ii) GRF COP를 TLFB 발밑에 정렬.

**ES는 % headline 대신 %p+phase 또는 "보행 비방해" 관점** 권장.

---
_조사만 완료. 경로(소스 A/B/C·ES 관점) 사용자 결정 후 착수._
