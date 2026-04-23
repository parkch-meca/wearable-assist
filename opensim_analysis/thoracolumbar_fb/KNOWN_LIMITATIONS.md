# Known Limitations — `stoop_box_comparison_v2.mp4`

본 영상은 **발표용 임시 영상**입니다. 아래 제약사항을 Moco 파이프라인 전환 후 근본 해결할 예정입니다.

## 1. 박스 파지 순간 ~15 cm 수직 pop

**증상**: t = 2.0 s에서 박스가 바닥(렌더 grid y=−0.905)에서 손 위치로 순간이동.

**원인**: `stoop_box20kg_v2.mot`의 t=2.0 s 손 중심 y = −0.606 m. 박스 윗면(grid 위 15 cm)은 y = −0.755. 손이 박스 윗면보다 15 cm 위에 있음 → 파지 로직 전환 시 pop 발생.

**완화**: v1 → v3에서 pop 27 → 27 cm, v4에서 1.9 cm, v5(최종)에서 렌더 grid 기준 재정의로 15 cm. 완전 제거는 모션 재생성 필요.

## 2. 발-바닥 15 cm 매몰 (peak 굽힘 구간)

**증상**: t ≈ 1.9–2.5 s 구간에서 발(calcn_r.y = −1.057 m)이 렌더 grid(y=−0.905)보다 15 cm 아래.

**원인**: `stoop_box20kg_v2.mot` 생성 시 `pelvis_ty = −0.32 m`를 하드코딩 offset으로 적용. 모션에 ground contact constraint 없음 → pelvis 드롭 시 발이 그대로 따라 내려감.

**완화**: 카메라 +35° azimuth (front-right 3/4) + 바닥 opacity 0.75 상향으로 clipping 가시성 감소.

## 3. Reserve actuator로 인한 ES activation 과소추정 (⚠ 중요)

### Finding

SO 설정에서 비-pelvis 회전 reserve `optimalForce = 100 Nm`. 이로 인해 reserve가 cost 대비 매우 저렴해져 척추 신전 모멘트의 상당 부분이 reserve로 흡수됨:

| 조건 @ t=2.33 | Reserve 척추 FE 합 | ES peak | ES mean |
|---|---:|---:|---:|
| R100 (현재) B_suit0 | **413 Nm** | 66.7 % | 18.6 % |
| R50 B_suit0 | 209 Nm | 86.8 % | 25.3 % |
| R10 B_suit0 | 22 Nm | **100.0 %** (saturation) | 38.7 % |
| R1 B_suit0 | 0.4 Nm | 100.0 % (11 muscle saturated) | 43.8 % |

→ R100은 baseline ES를 과소추정. **문헌 EMG(40–70 % MVC)와 매칭되는 R50이 더 현실적** (ES peak 87 %). 단 계산은 R100보다 ~90× 느림.

### 상대 효과의 Robustness

| 조건 | Suit Δ% @ R100 | @ R50 | 상대 차이 |
|---|---:|---:|---|
| 박스 + semi-squat | 10.34 % | 10.60 % | **0.27 %p** — robust ✅ |
| Suit-only stoop (§1.6) | 28.12 % | 21.25 % | **6.87 %p** — sensitive ⚠ |

→ 박스 영상의 **상대 감소율**은 reserve에 robust하나, **§1.6 headline 28.97 % 수치는 R50에서 ≈ 21 %로 재추정**. 방향성(선형 감소, R²=1)은 불변.

### 결론

- 본 영상은 R100 결과 기준으로 렌더 (baseline ES는 과소추정)
- Display metric을 `ES mean (76근육 평균)` → `ES peak (최대)`로 변경. `IL_R11_r` 등 실제로 일하는 근육의 활성도(80 % 급)가 문헌과 매칭되게.
- Moco 파이프라인에서 reserve를 체계적으로 다룸 (penalty weight, activation dynamics).

## 4. 해결 계획 (Moco 단계)

- Ground contact를 constraint로 직접 처리 → 발 매몰 소멸
- Motion이 최적 제어 결과 → box–hand 정합 자동
- Reserve penalty를 비용 함수에 명시적으로 포함 → 민감도 튜닝 체계화
- 다른 동작(reach, overhead, stairs)에 동일 파이프라인 확장

현재 파일은 Moco 완료 후 `stoop_box_comparison_v3.mp4`로 대체 예정.

## 참조

- Reserve 민감도 상세: [docs/reserve_sensitivity.md](docs/reserve_sensitivity.md)
- Suit sweep R100 vs R50 비교: [docs/suit_sweep_reserve_comparison.md](docs/suit_sweep_reserve_comparison.md)
- Moco 환경 점검: [docs/moco_env_check.md](docs/moco_env_check.md)
