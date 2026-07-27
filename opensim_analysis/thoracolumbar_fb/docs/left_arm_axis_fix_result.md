# 왼팔 관절축 결함 수정 — 실행 결과 (2026-07-27)

조사([[left_arm_axis_fix_investigation]]) 후 사용자 승인으로 실제 수정 실행. **M1식 regression("안 바뀜 확인")이 아니라 결함 교정 — 값 변화 정상, ΔES 정직 측정.**

## [1] 축 미러 수정 (7축, 규칙 (−ax,−ay,az))

| 관절 | 수정 좌표축 |
|------|-----------|
| shoulder_L | shoulder_elv_l, shoulder_rot_l, elv_angle_l (3) |
| radius_hand_l | wrist_dev_l, wrist_flex_l (2) |
| **sterL_clavL_jnt** ★ | clav_prot_l, clav_elev_l (2) — 수정 중 발견한 동일 결함(M1 추가 관절) |

- 조사 때 5축 계획 → 실행 중 **쇄골 2축도 동일 비트-복사 결함** 발견(sterL_clavL_jnt 축이 sterR과 동일). 같은 규칙으로 함께 수정.
- **검증**: 좌우 대칭 MAX **0.00cm** (4자세, clav 구동 포함). 질량 77.969kg·COM·620근육·169좌표·mesh **전부 불변**. 중립 왼손 0.000cm(정지분석 무영향).
- 산출: `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap_armfix.osim` (gitignore, /data).

## [2] stoop/squat ES 재측정 (동일 파이프라인 def vs fix, F0 baseline)

M1 공통 → Δ = 순수 팔축 수정 효과. 박스는 skip(왼팔 coord 전부 0).

| 동작 | ES peak def→fix | Δ | ES mean Δ |
|------|-----------------|-----|-----------|
| stoop v5 | 31.9% → 31.6% | **−0.3%p** | ~0 |
| squat v1 | 27.4% → 26.3% | **−1.1%p** | ~0 |

- **max ΔES = −1.1%p (squat) < 5%p.** 왼팔 12.5cm 이동에도 척추 ES 변화 미미(팔무게의 L5/S1 moment 기여 작음).
- 슈트 효과 %는 OFF/ON 비율 → baseline이 ≤1.1%p만 이동하면 비율 거의 불변. **headline 32%/47% 실질 불변.**
- stoop/squat 모션은 clav_prot/elev를 구동하지 않음(컬럼 부재) → 쇄골 수정이 이 SO에 영향 없음(값 그대로 유효).

## [3] viz-mirror 대체

- 수정 후 왼팔을 **자기 coord로 독립 구동** → viz-mirror 없이 박스 파지 렌더 z-대칭 **0.29cm**(양팔 대칭, `armfix_no_vizmirror.png`).
- 걷기 비대칭 팔스윙 가능해짐(viz-mirror로 불가했던 것). 기존 박스 동영상은 viz-mirror로 이미 완성 → 재렌더 불필요(유효).

## headline 갱신 판단 (→ 사용자)

ΔES ≤1.1%p로 **갱신 불필요 권장**. 다만 이후 논문 수치는 수정 모델(armfix) 기준으로 통일 권장.

## 다음 (사용자 확인 후)

걷기(gait2354) 착수 — 좌우 독립 팔스윙 + GRF COP 정렬. **[2] 값 확인 후 착수(자동 X).**
