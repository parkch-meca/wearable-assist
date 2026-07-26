# 왼팔 관절축 결함 수정 — 방법·regression·viz-mirror 대체 조사 (수정 전, 2026-07-27)

걷기(gait2354) 착수를 위해 왼팔 관절축 결함을 근본 수정(선택지 A) 결정. **M1처럼 실제 수정 전 조사만 — 사용자 확인 후 착수.**

## [1] 결함 정확한 범위 (실측)

좌/우 팔 관절축 벡터 대조 결과:

| 관절 | 좌표축 | 상태 |
|------|--------|------|
| **shoulder_L** | shoulder_elv_l, shoulder_rot_l, elv_angle_l (3축) | ❌ 오른쪽과 **비트-동일**(미러 아님) |
| **radius_hand_l** (손목) | wrist_dev_l, wrist_flex_l (2축) | ❌ 오른쪽과 **비트-동일**(미러 아님) |
| elbow_l | elbow_flexion_l | ✅ 정상 미러됨 |
| radioulnar_l | pro_sup_l | ✅ 정상 미러됨 |

**결함은 오직 5개 회전축 벡터** (shoulder_L 3 + wrist_l 2).
- **offset frame은 이미 올바르게 미러**됨 (scapula_L_offset transl z, orient 부호 반전 확인).
- **근육 부착점도 미러**됨 (DELT1_l 등 z좌표 반전 확인).
- body mesh도 정상(_l 메시).
→ **mesh/근육/frame/질량 전부 정상, 축 벡터만 수정 대상.** (M1의 구조 추가보다 훨씬 좁음)

## [2] 수정 방법 + 범위

- **올바른 미러 규칙 = (−ax, −ay, az)** (x,y 부호 반전, z 유지 = 시상면 반사의 축벡터 pseudovector 변환).
  정상 미러 관절(elbow_l, radioulnar_l)의 좌표축이 정확히 이 규칙 → 검증됨.
- **★검증 완료**: shoulder_L(3축)+wrist_l(2축)에 이 규칙 적용 후, stoop 자세(shoulder_elv_l=73°)에서
  수정된 왼손 위치가 **오른손의 z-미러와 정확히 일치(오차 0.0cm)**. 완벽 대칭.
- 수정 = `.osim`의 `<TransformAxis><axis>` 5개(+일관성 위해 dependent rotation3 축) 재정의. XML 축 벡터만.
- **mesh/근육/mass/frame 변경 없음.** 매우 좁은 수정.

## [3] ★ regression 범위 (핵심)

### 영향 메커니즘
- ES 근육은 척추 부착 → 팔 축과 **직접 무관**.
- **간접**: 축 수정 시 왼팔 coord가 **0이 아니면** 왼팔이 올바른 미러 위치로 **이동** → 팔 무게중심 이동 → 척추 하중(moment) 변화 → ES 소폭 변할 수 있음.

### 분석별 영향 (왼팔 coord 실측)
| 분석 | 왼팔 coord | 영향 | 재검증 |
|------|-----------|------|--------|
| **박스** (headline 23%) | shoulder_elv_l 등 **전부 0(정지)** | **없음** (ΔES=0) | 불필요 |
| **Phase 1a stoop v5** (32%) | shoulder_elv_l 73°, elv_angle_l 90° | **있음** (hand_L 12.5cm 이동) | **필요** |
| **squat v1** (47%) | shoulder_elv_l 85°, elv_angle_l 90° | **있음** | **필요** |

### max ΔES 계획
- stoop + squat SO를 수정 모델로 재실행, ES(IL/LTpL/LTpT) 대비. 박스는 skip(왼팔 0).
- 크기 추정: 왼팔(전완+손 ~2-4kg)이 6-12cm 이동 → L5/S1 moment ~2-4 N·m 변화 → ES **~1-3%p 예상**(측정 필요).
- 임계 5%p: 초과 시 협의.
- **주의(중요)**: 기존 stoop/squat 결과는 **결함(비대칭 왼팔)**로 계산됨. 수정은 이를 **더 정확**하게 만들지만 숫자가 바뀜.
  즉 "regression 통과"가 아니라 "**결함 교정으로 값이 개선**"일 수 있음 → headline 갱신 여부 판단 필요.

## [4] viz-mirror 대체 가능성

- **수정 후 왼팔이 자기 coord로 올바르게 구동/렌더** → **viz-mirror 불필요**해짐(근본 해결).
- **걷기**: 왼팔 coord 직접 지정(비대칭 스윙) → 작동. (viz-mirror로는 불가했던 것)
- **박스(대칭)**: 왼팔=미러 coord 지정하면 viz-mirror 없이 렌더 가능. 단 **기존 박스 동영상은 viz-mirror로 이미 완성** → 재렌더 불필요(그대로 유효). 원하면 일관성 위해 재렌더 가능(선택).
- 즉 축 수정은 viz-mirror를 **대체**하며, 기존 박스 산출물엔 영향 없음.

## 권장 + 순서

**수정 진행 권장** — 근거: (a) 결함이 축 5개로 매우 좁음, (b) 미러 규칙 검증 완료(0.0cm 대칭),
(c) mesh/근육/mass 불변으로 저위험, (d) 걷기+모든 비대칭 동작의 기반, viz-mirror 근본 대체.

**순서**:
1. 축 5개 미러 수정 → 좌우 대칭 검증(hand_L = 오른손 z-미러).
2. **regression: stoop + squat SO 재실행, max ΔES 측정**(박스 skip). <5%p면 진행, >5%p면 협의(결함교정 vs headline 갱신).
3. 걷기 착수(gait2354 retarget + 좌우 독립 팔 스윙).

⚠️ 실제 수정 미실시. 사용자 확인 후 착수.
