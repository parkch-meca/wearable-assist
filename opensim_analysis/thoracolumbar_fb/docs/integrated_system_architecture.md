# Integrated System Architecture
**작성일**: 2026-05-14  
**목적**: 통합 wearable robot evaluation 시스템 architecture — CHEOL HOON님 검토 + Step 2 결정용  
**범위**: 4개 design docs (model_infrastructure_design + motion_generation_methods + suit_actuator_module_design + visualization_framework_design) 통합  
**상태**: DESIGN ONLY — 구현 X. CHEOL HOON님 승인 후 Step 2 착수.

---

## §1. Executive Summary

### 1.1 CHEOL HOON님 진짜 목적 (재확인)

> "제대로 된 근골격계 모델 + 의미 있는 동작 생성 + 근력보조 슈트 효과 비교 + 동영상"

- 단발 patch 아닌 **진짜 인프라**: 한 번 구축 → 다양한 작업 확장 (stoop → box → squat → walk → caregiving)
- **동영상이 메인 deliverable**: 1080p 슈트 비교 영상 (Suit OFF vs ON, ES color overlay)
- **MocoTrack 즉시 포함**: Hybrid patch 패턴 (박스 v3-v13) 재발 방지

### 1.2 핵심 결정 (CHEOL HOON님 지시 반영)

| 결정 | 내용 | 근거 |
|------|------|------|
| MocoTrack 즉시 | 박스/squat/walk에 MocoTrack 적용 | Hybrid patch 13번 교훈 |
| ES color schema | viz-agent 표준 (§6.2) | CHEOL HOON님 결정 |
| 슈트 비교 기준 | 24 N·m (200 N × 0.12 m) | 200 N·m 오류 재발 방지 |
| 한 번에 한 작업 | 보고서 검토 → Step 2 결정 | 병렬 X, 순서 준수 |

### 1.3 4 docs 핵심 통합 요약

| Doc | 핵심 결정 | 상세 |
|-----|---------|------|
| Model Infrastructure (§2) | Hunt-Crossley contact + ExternalForce 손 하중 + Reserve 분리 | pelvis reserve 폭증 구조적 해결 |
| Motion Generation (§3) | MocoTrack 즉시 + foot anchor + CMA-ES | 13번 학습 통합 |
| Suit Actuator Module (§4) | SuitConfig 단위 분리 + assert 검증 | 200 N·m 오류 재발 방지 |
| Visualization (§6) | 1080p + ES color 24 N·m 기준 + Stage 4 Grid | 동영상 deliverable 표준 |

### 1.4 검증된 Reference Path

| 논문 | 우리 적용 |
|------|---------|
| John 2022 (MocoTrack + exoskeleton) | MocoTrack 즉시 적용 근거 |
| Falisse 2019 (SmoothSphereHalfSpaceForce) | Hunt-Crossley contact 파라미터 |
| Hu 2026 (4-condition dose-response) | Phase 2.C.4 구조 동일, 결과 정량 일치 |
| Yan 2024 (OpenSim SO + exosuit + lifting) | 파이프라인 구조 동등, 검증 기준 |
| Dembia 2020 (OpenSim Moco) | ModOpAddResiduals/Reserves 분리 표준 |
| Hicks 2015 (Is my model good enough?) | Reserve 허용 기준 (< 5% BW, < 1% BW×ht) |

### 1.5 Step 2 작업 범위 (6-7주)

| Week | 주요 작업 | 산출물 |
|------|---------|--------|
| 1-2 | Base 인프라 4개 모듈 구현 | suit_torque_module.py, model_setup.py, moco_track_setup.py, contact_model.py |
| 3 | Phase 1a 재현 검증 | 24 N·m → 28% 재현 PASS, regression PASS |
| 4-5 | 박스 motion MocoTrack 재실행 | tasks/box_lift/, 5 conditions |
| 6 | 박스 첫 의미있는 동영상 | box_lift_suit_comparison.mp4 (1080p) |
| 7 | Squat 시나리오 확장 시작 | tasks/squat/ skeleton |

---

## §2. 모델 인프라

### 2.1 발 접촉 모델

**Phase 1a (stoop lift): ExternalLoads GRF STO 유지**

현행 `stoop_grf_v5.sto` (368 N/foot 상수) + MocoInverse 조합은 검증 완료. 변경 불필요.

**박스/Squat/Walk: SmoothSphereHalfSpaceForce (Hunt-Crossley)**

GRF 불일치가 reserve 폭증의 근본 원인 (pelvis_ty 3,570 N 사례). Contact Sphere를 쓰면 solver가 GRF를 자동 계산 — 외부 STO 파일 불필요, kinematics와 완전 일관.

구현 클래스: `SmoothSphereHalfSpaceForce` (OpenSim 4.x, Falisse 2019). 구 파라미터 (2D gait 예제 검증값):

| 구 이름 | body | radius (m) | stiffness (N/m²) | dissipation (s/m) |
|--------|------|-----------|-----------------|------------------|
| heel_r/l | calcn_r/l | 0.035 | 3,067,776 | 2.0 |
| front_r/l | calcn_r/l | 0.015 | 3,067,776 | 2.0 |

ThoracolumbarFB 적용 시: calcn_r body frame heel/ball 좌표 FK로 실측 후 sphere 배치. static/dynamic friction 0.8, viscous 0.5.

| 작업 | 발 접촉 방식 |
|------|-----------|
| stoop lift (Phase 1a) | ExternalLoads STO (현행 유지) |
| box/squat | SmoothSphereHalfSpaceForce + MocoTrack |
| walk | SmoothSphereHalfSpaceForce + MocoTrack |

### 2.2 ExternalForce 손 하중 (박스 무게)

Newton 균형 원칙: 75 kg 몸 + 20 kg 박스 = 930 N. 발 GRF = 368 N/foot × 2 + 손 하중 = 각 98.1 N (아래).

```
box_force_r: hand_r body, ground frame 기준, -y 98.1 N × alpha(t)
box_force_l: hand_l body, 동일
alpha(t): t < 1.5 → 0, t=1.5~2.0 선형 증가, t=2.0~4.0 → 1, t=4.0~4.5 감소
```

이 방식으로 pelvis_tilt reserve 221 N·m 근본 원인을 구조적으로 해소 (손 하중 moment arm 불일치).

### 2.3 Reserve 분리 표준

Dembia 2020 공식 패턴 (`exampleMocoInverse.py`):

```python
model_proc.append(osim.ModOpAddResiduals(300.0, 50.0, 1.0))  # pelvis 6 DOF 전용
model_proc.append(osim.ModOpAddReserves(1.0))                  # 나머지 관절 (약한 보조)
```

Hicks 2015 허용 기준: 번역 < 36.8 N (5% BW), 회전 < 12.9 N·m (1% BW×ht).

| 작업 | translational_F | rotational_M | 이유 |
|------|---------------|-------------|------|
| stoop lift | 50 N | 20 N·m | 정적 동작 |
| box/squat | 300 N | 50 N·m | semi-squat 수직 가속도 |
| walk | 250 N | 50 N·m | 공식 예제 기준 |

### 2.4 Forearm v1 모델 (검증 완료)

De Leva 1996 기준 hand 19.2 cm 보강 적용. Phase 1a regression PASS (max ΔES 1.23 %p < 5 %p 기준).  
박스 작업용 모델: `MaleFullBodyModel_v2.0_OS4_moco_stoop_no_coupler_forearm_v1.osim`

---

## §3. 동작 생성 방법 (MocoTrack 중심)

### 3.1 MocoTrack 즉시 적용 (CHEOL HOON님 결정)

John 2022가 MocoTrack + exoskeleton torque sweep의 검증된 선례. Yan 2024가 lifting에서 같은 구조(reference kinematics → musculoskeletal tracking) 검증 (cross-correlation 0.84-0.98).

MocoInverse는 MocoTrack의 특수 케이스 (완전 처방 kinematics). 차이점:
- MocoInverse: kinematcis 완전 고정, muscles만 최적화
- MocoTrack: kinematics를 tracking weight로 유연하게 — contact model 사용 시 필수

박스/squat에서 Contact Sphere (§2.1) 사용 시 MocoTrack 요건. **Hybrid patch 패턴 대신 검증된 MocoTrack 경로 채택.**

### 3.2 박스 motion 13번 학습 통합 (재사용 가능)

| 발견 | 재사용 방법 |
|------|-----------|
| Foot x-anchor + FK bisection | 모든 정적 들기 작업 (stoop/box/squat) 공통 |
| CMA-ES + Two-pass warm-start | pass 1: mesh=25, pass 2: mesh=50 (warm-start) |
| ExternalForce XML 박스 하중 | box/squat/walk+carry 공통 template |
| Stage 1-4 자가 검증 protocol | 모든 신규 작업 의무 |

Foot FK bisection:
```python
def compute_pelvis_tx_to_fix_foot(model, state, coord_set, target_calcn_x=-0.0442):
    lo, hi = -1.0, 0.5
    for _ in range(50):
        mid = (lo + hi) / 2
        coord_set.get('pelvis_tx').setValue(state, mid, False)
        model.realizePosition(state)
        cx = model.getBodySet().get('calcn_r').getPositionInGround(state).get(0)
        if cx < target_calcn_x: lo = mid
        else: hi = mid
    return (lo + hi) / 2
```

Walk + carry에는 적용 불가 (동적 발 접촉 → contact force 모델링 필요).

### 3.3 4 Methods 비교 (요약)

| Method | 검증 문헌 | 적용 시점 | 결정 |
|--------|---------|---------|------|
| Predictive (direct collocation) | Falisse 2019, D'Hondt 2024 | 장기 (계산 수십~수백 시간) | Step 3+ |
| **MocoTrack** | **John 2022, Yan 2024** | **즉시 (박스/squat)** | **채택** |
| RL (KINESIS, GR00T) | 부분 검증 | 1년+ | 장기 |
| Hybrid (박스 v3-v13) | 우리 4개월 학습 | 회피 | **채택 X** |

### 3.4 5개 작업 시나리오 (Pinheiro 2023 확장)

| Task | 상태 | 발 전략 | 방법 | Week |
|------|------|--------|------|------|
| Stoop (Phase 1a) | 검증 완료 | ExternalLoads | MocoInverse | 유지 |
| Box (재구축) | v13 → MocoTrack | Contact sphere | MocoTrack | 4-5 |
| Squat | 신규 계획 | Contact sphere | MocoTrack | 7+ |
| Walk + carry | Step 3+ | 동적 contact | MocoTrack + CMU mocap | Step 3 |
| Patient transfer | 장기 caregiving | 동적 + 비대칭 | MocoTrack 또는 Predictive | Step 3+ |

---

## §4. 슈트 Actuator 모듈

### 4.1 단위 변환 모듈 분리 (구조적 오류 방지)

Phase 2.C.4 v1-v3 오류: `('B_suit200', 200.0)` → 200 N·m 직접 적용 = 실슈트의 8.33배.  
재발 방지: 모든 스크립트가 아래 모듈만 import, 직접 값 입력 금지.

```python
# suit_torque_module.py (핵심 구조)
class SuitConfig:
    def __init__(self, force_N, moment_arm_m, name):
        self.force_N = force_N
        self.moment_arm_m = moment_arm_m
    @property
    def torque_Nm(self):
        return self.force_N * self.moment_arm_m

SMA_SUIT_SPEC = SuitConfig(200, 0.12, "SMA_L20")  # → 24.0 N·m
assert abs(SMA_SUIT_SPEC.torque_Nm - 24.0) < 1e-9  # 실행 시 자동 검증

STANDARD_SWEEP = make_suit_sweep([0, 50, 100, 150, 200])
# → [('suit0',0.0),('suit50',6.0),('suit100',12.0),('suit150',18.0),('suit200',24.0)]
```

변수명 규칙: `_N` suffix = Newton (힘), `_NM` suffix = Newton·meter (토크).

### 4.2 Phase 1a 호환성 (24 N·m 검증)

`SMA_SUIT_SPEC.torque_Nm == 24.0` — Phase 1a 28% ES 감소 재현 가능. 모듈 도입 후 Phase 1a B_suit200 재실행 → ES mean 차이 < 0.1 %p → PASS.

### 4.3 Implementation Option B (현재 표준, Phase 1a 검증)

thoracic1 +Tz / pelvis -Tz (action-reaction 쌍). ExternalForce XML 방식.  
John 2022, Quinlivan 2017과 구조 동등 (외력을 body에 직접 적용).

### 4.4 다양한 슈트 plug-in (미래)

새 슈트 추가 = `SuitConfig` 1줄 + `make_suit_sweep()` 재사용.  
SMA fabric (현재) / Passive elastic / Active motor (Hu 2026 형식) / Cable-driven (Quinlivan 2017) 모두 동일 모듈로 sweep 생성.

---

## §5. Base + Task 모듈 구조

```
infrastructure/
├── base/
│   ├── model_setup.py        # build_model_processor() — 작업 공통 파이프라인
│   ├── suit_torque_module.py # 단위 변환 (§4.1) — N → N·m 한 곳만
│   ├── moco_track_setup.py   # MocoTrack 공통 설정 (John 2022 기반)
│   └── contact_model.py      # Hunt-Crossley sphere (Falisse 2019)
│
└── tasks/
    ├── stoop_lift/   # Phase 1a — ExternalLoads 유지, 변경 불필요
    │   ├── motion.py     # stoop_synthetic_v5.mot
    │   ├── grf.py        # stoop_grf_v5.sto
    │   └── conditions.py # STANDARD_SWEEP import
    ├── box_lift/     # MocoTrack 재구축 (Week 4-5)
    │   ├── motion.py     # MocoTrack reference kinematics
    │   ├── grf.py        # Contact sphere (§2.1)
    │   ├── hand_force.py # 박스 손 하중 (§2.2)
    │   └── conditions.py # PHASE2_BOX_SWEEP import
    ├── squat/        # 신규 (Week 7+, Yan 2024 형식)
    └── walk/         # Step 3+ (Falisse 2019 패턴)
```

`build_model_processor()` 핵심 인터페이스:

```python
def build_model_processor(model_path, grf_xml, muscle_list,
                           residuals=(300.0, 50.0, 1.0),
                           reserves_optf=1.0,
                           fiber_width_scale=1.5) -> osim.ModelProcessor:
    """
    작업 전환: grf_xml + muscle_list 교체만으로 충분.
    Base 수정 불필요.
    """
```

**효과**: Task 추가 = motion.py + grf.py + conditions.py 3개 파일만 작성. Base 수정 없음.

---

## §6. 시각화 + 동영상 Framework

### 6.1 3-tier Video 스펙

| Tier | 해상도 | FPS | Codec | 용도 |
|------|------|-----|-------|------|
| Verification | 720p | 30 | h264 CRF 23 | 빠른 내부 검증 |
| **Standard (default)** | **1080p** | **30** | **h264 CRF 17** | **YouTube + 논문 보조자료** |
| Archive | 4K | 30 | h265 CRF 18 | 최종 장기 보존 |

1080p 선택 근거: YouTube HD 기준 720p에서 한 단계 여유. 30fps는 5초 들기 동작에 충분. h264 CRF 17 ≈ near-lossless, 파일 크기 15-30 MB.

### 6.2 ES Color Schema (viz-agent 표준, CHEOL HOON님 결정)

| 활성도 | Hex | 이름 |
|--------|-----|------|
| 100% | #8B0000 | 진빨강 (최대/포화) |
| 75% | #CC2200 | 빨강 (고부하) |
| 50% | #FF6600 | 주황 (중부하) |
| 25% | #FFB300 | 호박색 (저중부하) |
| 10% | #FFD700 | 금노랑 (저부하) |
| 0% | #909090 | 중간회색 (비활성) |

**슈트 비교: 반드시 24 N·m 기준 사용.** 200 N·m 조건 (99 %p drop)은 misleading → 비교 영상 제외.

### 6.3 Stage 4 Grid PNG — 영구 Protocol

모든 신규 동작 작업 전 의무. Moco 분석 시작 전 Tier 2 (사용자 채팅 확인) 필수.

- 5 frames × 3 views (sagittal / anterior / 3-quarter)
- 16-item checklist (posture P1-P5, feet F1-F3, arms A1-A3, box B1-B5, general G1-G2)
- 생성 즉시 GitHub push → raw URL 사용자 채팅 제공
- Tier 1: Claude Code 자가 vision 검증, Tier 2: 사용자 최종 확인 (구속력 있는 게이트)

고정 카메라:
- sagittal: position (0, 0.4, 4.0)
- anterior: position (-4.0, 0.4, 0.0)
- 3-quarter: position (-2.2, 0.8, 3.0)

### 6.4 슈트 비교 Layout (Option A, default)

```
[SUIT OFF | B_noload]  |  [SUIT ON | B_suit24 (24 N·m)]
  3D body + ES lines   |    3D body + ES lines
  (빨강-주황)          |    (호박색)
─────────────────────────────────────────────
  IL_R10_r time series  |  ES mean bar + 핵심 수치
  delta -28%  R²=1.000  |  slope 1.164 %/N·m
```

하단 panel: `IL_R10_r: 87.7% → 63.0% (Delta -24.7 %p, -28%)` 번인 자막.

---

## §7. 검증 시나리오 (3 단계)

### 7.1 인프라 검증 1 — Phase 1a 재현 (Week 3, 최우선)

새 `build_model_processor()` 위에서 Phase 1a 조건 재실행.

Pass 기준:
- ES peak activation (B_noload): 기존 ±5 %p
- Suit effect (24 N·m): 23~33% 범위 (28% ±5 %p)
- Slope 방향성 유지 (음수), R² > 0.95
- pelvis reserve: Hicks 2015 기준 충족

Reserve 구조 변경 (ModOpAddReserves(10) → Residuals(50,20)+Reserves(1)) 으로 baseline ES 소폭 변화 가능. 28% → 25-31% 범위이면 해석적 동등.

### 7.2 박스 motion MocoTrack 재실행 (Week 4-5)

tasks/box_lift/ 구축. Contact sphere + ExternalForce 손 하중 + Suit 24 N·m.

Pass 기준:
- pelvis_ty reserve peak < 37 N (Hicks 5% BW)
- pelvis_tilt reserve peak < 13 N·m (Hicks 1% BW×ht)
- inf_pr < 1e-3 (수렴)
- ES 감소 범위: Hu 2026 14.9-28.6% 범위 내

### 7.3 Squat 자연 확장 (Week 7+)

tasks/squat/ 신규 추가. base/ 수정 없이 가능한지 확인.

Pass 기준 (설계):
- base/model_setup.py 수정 없이 squat 실행
- Reserve Hicks 기준 충족
- ES 패턴 생리학적 타당성 (Yan 2024: squat은 quad 주도, ES 상대적 감소)

---

## §8. Step 2 작업 계획 (6-7주)

| Week | 작업 | 산출물 | 담당 |
|------|------|--------|------|
| **1** | suit_torque_module.py 구현 + 단위 테스트 | assert PASS, import 검증 | opensim-agent |
| **2** | model_setup.py + moco_track_setup.py + contact_model.py | base/ 4개 모듈 | opensim-agent |
| **3** | Phase 1a 재현 검증 (smoke test) | ΔES < 5 %p PASS, 28% 재현 | moco-analysis-agent |
| **4** | tasks/box_lift/ 구축 + biomechanics-agent 동작 spec | box reference doc | biomechanics-agent 우선 |
| **5** | 박스 MocoTrack 실행 + 5 conditions Moco | ES analysis, reserve PASS | moco-analysis-agent |
| **6** | 박스 첫 동영상 (1080p, 24 N·m 비교) | box_lift_suit_comparison.mp4 | viz-agent |
| **7** | Squat task skeleton (biomechanics-agent → opensim-agent) | tasks/squat/ skeleton | 양 에이전트 |

각 Week: Stage 4 Grid PNG 사용자 채팅 검증 후 다음 단계 진행.

---

## §9. 위험 평가 + Fallback

### 9.1 MocoTrack 첫 적용 학습 곡선

- 위험 수준: 중
- 내용: John 2022 기반이나 우리 ThoracolumbarFB 환경에서 첫 적용
- Fallback: Contact sphere 없이 MocoInverse + kinematics-consistent GRF 재계산 (§2.1 단기 경로)
- 판단 기준: Week 4 MocoTrack 시도 후 수렴 실패 2회 → Fallback 전환, 사용자 협의

### 9.2 Contact Model 파라미터 튜닝

- 위험 수준: 중
- 내용: ThoracolumbarFB calcn body 스케일이 2D gait 예제와 다름 → sphere 위치 조정 필요
- Fallback: 2D gait 검증 파라미터 (heel 0.035 m, ball 0.015 m) 그대로 시작, FK로 위치 확인 후 미세 조정
- 판단 기준: pelvis_ty reserve가 300 N 초과 시 sphere 위치 재조정

### 9.3 박스 motion 13번 패턴 재발 방지

- 구조적 방지: MocoTrack 채택 (Hybrid 대신)
- 프로세스 방지: biomechanics-agent 우선 (새 동작 설계 시 무조건 먼저)
- 단위 방지: suit_torque_module.py (N → N·m 한 곳만)
- 시각 방지: Stage 4 Grid PNG 의무 (사용자 확인 없이 Moco 실행 금지)

### 9.4 새 발견 시 Protocol

1. 추정 X — 명확한 진단 먼저
2. Fallback 옵션 사용자 제시 (2-3개)
3. 사용자 결정 후 진행 (자동 다음 시도 절대 X)
4. 같은 증상 2회 실패 → 접근법 전면 재검토

---

## §10. CHEOL HOON님 검토 항목

### 10.1 Architecture 동의?

7가지 핵심 설계:
1. **Contact model**: Hunt-Crossley SmoothSphereHalfSpaceForce (박스/squat/walk)
2. **ExternalForce**: 손 하중 Newton 균형 (pelvis reserve 근본 해결)
3. **Reserve 분리**: ModOpAddResiduals(300,50) + ModOpAddReserves(1.0) 분리
4. **Suit module**: SuitConfig 단위 분리 + assert 자동 검증
5. **Base + Task**: build_model_processor() 공통 + task 3파일만 추가
6. **MocoTrack**: 박스/squat 즉시 적용 (Hybrid 대신)
7. **Visualization**: 1080p + ES color 24 N·m 기준 + Stage 4 의무

모두 검증된 문헌 기반 (John 2022 + Falisse 2019 + Dembia 2020 + Phase 1a 검증).

**동의하십니까?**

### 10.2 Step 2 6-7주 일정 합리?

- Week 1-2: base 인프라 4개 모듈
- Week 3: Phase 1a 재현 (regression gate)
- Week 4-5: 박스 MocoTrack
- Week 6: 박스 동영상 deliverable
- Week 7: Squat 시작

**일정 합리하다고 생각하십니까? 또는 조정이 필요한 week가 있습니까?**

### 10.3 다음 작업 시나리오 우선순위

제안 순서:
1. Squat (Week 7+, Yan 2024 형식, box 인프라 재사용)
2. Walk + carry (Step 3, Pinheiro 2023, CMU mocap 활용)
3. Patient transfer (caregiving 핵심, 장기, 실험 데이터 필요)

**이 우선순위에 동의하십니까? 또는 변경이 필요합니까?**

### 10.4 추가 우려/요청

예시:
- 논문 deadline 제약으로 특정 task 우선순위 변경 필요?
- Hardware 개발 타임라인과 연동 필요?
- Phase 1a 국문 학술지 투고 전 추가 분석 필요?
- 65세 여성 scaling 시점 (Step 2 내 또는 Step 3)?

**추가로 우려되시거나 요청하실 사항이 있으시면 말씀해 주세요.**

---

## §11. 인용

1. **John CT et al. (2022).** Feasibility of using MocoTrack to analyze wearable lower-limb exoskeleton assistance during walking. *Comput Methods Biomech Biomed Eng* 25(13):1482-1493. DOI: 10.1080/10255842.2022.2040546. — MocoTrack + exoskeleton torque sweep 근거
2. **Falisse A et al. (2019).** Rapid predictive simulations with complex musculoskeletal models. *J R Soc Interface* 16(157):20190402. PMID: 31431183. — SmoothSphereHalfSpaceForce 원천, contact 파라미터
3. **Hu F et al. (2026).** Active dual-joint back-support exoskeleton, 4 assist levels. *Ergonomics* 69(3):453-465. PMID: 39967340. — Phase 2.C.4 구조 동일, 14.9-28.6% ES 감소 정량 일치
4. **Yan C et al. (2024).** OpenSim SO + soft exosuit + lifting. *J Biomechanics* 176:112322. PMID: 39305855. — 파이프라인 구조 동등, cross-correlation 0.84-0.98 검증 기준
5. **Dembia CL et al. (2020).** OpenSim Moco: musculoskeletal optimal control. *PLoS Comput Biol* 16(12):e1008493. PMID: 33338028. — ModOpAddResiduals/Reserves 분리 표준
6. **Hicks JL et al. (2015).** Is my model good enough? *J Biomech Eng* 137(2):020905. — Reserve 허용 기준 (5% BW, 1% BW×ht)
7. **D'Hondt J et al. (2024).** Predictive simulation of box lifting. *J Biomech* 167:111925. PMID: 38490110. — 박스 들기 trunk 47-55°, knee 20-35° (우리 동작 설계 기준)
8. **Pinheiro C et al. (2023).** Multi-task evaluation framework for lower-limb exoskeleton. *J NeuroEng Rehabil* 20:55. — Task module 구조, Walk/Carry 확장 방법론
9. **De Leva P (1996).** Adjustments to Zatsiorsky-Seluyanov's segment inertia. *J Biomech* 29(9):1223. — Forearm_v1 modification 근거 (손 19.2 cm)
10. **Beaucage-Gauvreau E et al. (2019).** Validation of ThoracolumbarFB v2.0. *Comput Methods Biomech Biomed Eng* 22(7):744-755. DOI: 10.1080/10255842.2018.1558757. — 우리 주 모델 검증 논문
11. **Quinlivan BT et al. (2017).** Assistance magnitude versus metabolic cost reductions for soft exosuit. *Sci Robot* 2(2):eaah4416. — Dose-response 구조, PathActuator 미래 참조
12. **Anderson FC & Pandy MG (2001).** Dynamic optimization of human walking. *J Biomech Eng* 123:381. — Reserve < 5-10% net joint moment 기준
13. **OpenSim 4.5.2 bundle examples (2023).** exampleMocoInverse.py, example2DWalking.py. — ModOpAddResiduals/Reserves 분리 패턴, contact sphere 파라미터 실측

---

_작성: paper-agent (2026-05-14)_  
_기반: 4 design docs (model_infrastructure_design + motion_generation_methods + suit_actuator_module_design + visualization_framework_design) + literature_synthesis.md_  
_다음 단계: CHEOL HOON님 §10 검토 항목 (4개) 명시적 승인 → Step 2 Week 1 착수_  
_자동 진행 X — 사용자 검토 필수_
