# 박스 20kg stoop 들기 — 완성 요약 (2026-07-24)

낮은 테이블(30cm) 위 박스(30cm, 20kg)를 양손 옆면 손바닥으로 stoop 들기 하는 전체 파이프라인
(**파지 → 모션 → OFF/ON SO → 일반인 동영상**) 완성. 사용자 최종 확인 완료.

## 1. 결과 — 슈트 효과 (ES = 척추기립근 IL+LTpL+LTpT 76근육)

**최대하중 순간(t=2.8s, 최대 stoop+박스): ES peak 37.5% → 28.8% = −23%** (EMG정렬 peak 지표).
지표 무관 robust: ES mean도 −26%. 구간별 liftoff −21% / carryup −26% / carry_hold −25% / lower −22%.

### 3개 동작 슈트 효과 비교 (부하-자세 패턴)

| 동작 | 슈트 감소 | 비고 |
|------|-----------|------|
| squat (맨몸) | **47%** (hold) / 37% (부하정점) | 무릎 우세, ES 낮음→% 큼 |
| stoop (맨몸) | **32%** (hold, IL_R10 88→63%) | 허리 우세 |
| **박스 20kg stoop (이번)** | **23%** (최대하중) / 28% (하중평균) | 부하 커서 % 작음 |
| 박스 semi-squat (v2, 참고) | 11% | squat 성분→% 작음 |

**패턴 정합**: (a) 동일 stoop서 무부하 32% → 20kg 23% (부하↑ → 고정 24N·m 비중↓ → %↓).
(b) box-stoop 23% > box-squat 11% (stoop 자세가 ES 부담 커 슈트 효과 큼).

## 2. 산출물

- **동영상**: `/data/opensim_results/box_stoop_suit_video.mp4` (1600×1000, 7.53초, 30fps).
  백업 `docs/images/literature_review/box_stoop_suit_video.mp4` (.mp4 gitignore, 로컬 백업).
- **키프레임 grid**: `docs/images/literature_review/box_public_keyframes_grid.png`,
  `docs/images/phase2_box/box_stoop_video_keyframes.png`.
- **SO 결과 plot**: `docs/images/phase2_box/box_stoop_so_results.png`.
- **모션**: `/data/stoop_motion/box_stoop_lift_m1.mot` (7.5초, 226프레임).
- **모델**: `MaleFullBodyModel_v2.0_OS4_modified_no_coupler_M1scap.osim` (M1 견갑 protraction, 로컬).

## 3. 확립된 방법 (다음 동작에 재사용할 표준)

### 3.1 파지/자세
- **낮은 물체 = stoop**(무릎 세우고 허리 굽혀 hip hinge). 무릎 극단 굽힘 crouch 아님.
- **박스 옆면 손바닥 파지 시 손목은 중립**(전완-손 일직선), **손바닥 방향은 pro_sup(전완 회전)가 담당**.
  팔 IK에 wrist-neutral 페널티(`wrist_flex²+dev²` 최소화) 표준화 → 자연 파지 + 전환 회전 없음.
- 팔꿈치는 몸 옆·아래(akimbo 금지); 박스 폭 파지엔 전완이 약간 벌어지는 게 자연.

### 3.2 모델 — M1 견갑 protraction
- 원본 ThoracolumbarFB는 sterno-clav/clav-scap이 **WeldJoint(고정)** → 견갑 못 움직여 팔이 낮은 물체 못 닿음.
- **M1**: sterR/L_clavR/L_jnt WeldJoint→2-DOF CustomJoint(clav_prot/elev, Seth 2019). `build_m1_scapula.py`.
- **regression 통과**: stoop SO ES max ΔES 0.029%p (ES는 견갑 부착 0 → 정량 안전). Phase 1a 불변.

### 3.3 렌더 viz 표준 (★ 경로별 점검 필수)
- **viz-mirror 범위 = 어깨 girdle 전체**(clavicle + scapula + humerus + ulna + radius + hand).
  모델 왼팔 축이 오른팔 복사본(원본 결함)이라, 오른쪽을 z=0 반사해 왼쪽으로 렌더. 팔뼈만 미러하면 견갑 비대칭 남음.
- **손목 viz 해제**(pro_sup/wrist 잠금 해제)로 .mot palm 방향 적용.
- **렌더 경로별로 viz 수정이 따로 적용됨**: Blender(MuSkeMo, knee-fix 필요) vs PyVista(OpenSim 직접, knee-fix 자동).
  새 렌더 경로 만들 때 viz-mirror / 손목해제 / knee-fix 3가지 적용 여부 반드시 점검.
- 전부 렌더 전용, `.osim` 불변 → SO/ES 정량 영향 0.

### 3.4 검증
- **생성/검증 분리**: 독립 Agent가 수치 없이 그림만 판정(자가검증 편향 제거).
- **전환/연속 아티팩트는 촘촘 시퀀스(0.1초 간격)로 검증** — 듬성한 키프레임으론 손목 회전·박스 상승 등 놓침.
- **개별 프레임보다 시퀀스/비교 grid가 신뢰도 높음**(검증자 개별프레임 오독 다수).

## 4. 여정 요약
박스 파지 6회 실패(웅크림·등세움 집착) → 사용자 "무릎높이=stoop" 정정으로 SOLVED → 팔꿈치 자연화
→ M1 견갑 protraction(regression 통과) → 모션 → OFF/ON SO(−23%) → 일반인 동영상
→ viz-mirror(견갑 포함) + 손목 중립화 회귀 수정까지 완성.

**교훈: biomechanics 우선(실제 동작 해본 사용자 지적)이 6회 실패를 끝냄.**

## 5. 다음 (별도 지시 후)
- 걷기 동작 (별도 지시 대기, 자동 착수 X)
- 여성/65세 간병인 조정, 국문 논문 §1.6 update
