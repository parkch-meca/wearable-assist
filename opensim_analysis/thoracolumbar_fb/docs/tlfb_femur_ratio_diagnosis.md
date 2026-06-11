# TLFB 대퇴(femur) 비율 — 그림 위 눈금 실측 + 원인 확정

**일자:** 2026-06-11
**대상:** `MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim`
**계기:** 골반~무릎 femur가 짧아 보임. 이전 측정(femur 0.424 m, joint-center)은 "정상"이라 했으나 렌더에서 짧아 보이는 이유를 설명 못 함 → 그림 위 눈금으로 확정.

---

## 분기 판정: **A (절대 비율 정상) + 진짜 원인 = MuSkeMo knee collapse**

## [1]/[2] 구간 비율 실측 (OpenSim frame world 좌표, stature = skull top→foot bottom)

| 구간 | TLFB | Rajagopal | Lai | 표준 인체 | 판정 |
|------|------|-----------|-----|----------|------|
| **femur** (hip JC→knee JC) | **24.0 %** | 24.4 % | 24.5 % | 24–25 % | ✅ 정상 |
| tibia (knee→ankle) | 25.0 % | 23.8 % | 23.7 % | 23–25 % | ✅ |
| 다리 전체 (hip→floor) | **52.7 %** | 51.4 % | 51.5 % | 48–50 % | ✅ 오히려 더 긺 |
| 체간 (hip→shoulder) | **27.6 %** | 31.8 % | 31.8 % | ~30 % | 오히려 더 짧음 |

→ **TLFB femur 24.0%, 표준(24–25%)·Rajagopal(24.4%)과 동일. 다리 전체도 더 길고 체간은 오히려 더 짧다.**
→ 가설 "상세 흉요추로 체간이 길어 다리가 짧아 보인다"는 **숫자로 반증** (TLFB 체간 27.6% < 대조군 31.8%).

**그림 위 눈금 일치 확인:** OpenSim ground transform으로 직접 투영한 골격에서, hip JC·knee JC 수평선이 고관절·무릎에 정확히 위치하고 femur 24% bracket이 대퇴 분절과 일치. **"표준 femur 24.5% 위치" 기준선이 knee JC선과 거의 정확히 겹침** → femur 정상을 그림으로 증명.

## [3] 짧아 보인 진짜 원인 — MuSkeMo knee 관절 translation 미적용

MuSkeMo로 TLFB를 import하면 무릎이 접혀서 들어온다 (사실, 추측 아님):
- **뼈 길이 자체는 정상**: scene femur mesh 0.485 m + tibia 0.403 m ≈ 0.89 m (OpenSim 0.867과 일치).
- **그러나 tibia body 원점 = femur body 원점 (Y 차이 단 1 cm)**. 정상이면 femur 길이만큼 ~42 cm 아래여야 함.
- 결과: 정강이뼈가 대퇴뼈 위로 **겹쳐 접힘** → 다리가 절반 높이(scene foot −0.495 m, OpenSim −0.919 m)로 렌더.
- 대조군 Rajagopal/Lai의 walker_knee는 MuSkeMo가 정상 처리 → 다리 정상.

원인 추정: TLFB knee가 OpenSim CustomJoint translation(spline/coupler)을 쓰는데 MuSkeMo가 이를 적용 못 함(import 시 "transform function may not be supported" 경고 계열).

**영향 범위:** 이전 모든 MuSkeMo/Blender 렌더(비교 grid, 척추중심 렌더 포함)에서 TLFB 다리가 접혀 있었음. 척추 중심 영상은 다리가 초점이 아니라 큰 문제 없으나, **전신 비율을 보이는 샷에는 부적합**.

---

## 결론
1. **femur·다리 비율은 절대적으로 정상** (femur 24.0%, 다리 52.7%). 모델 좌표·뼈 mesh 모두 정상.
2. **"짧아 보임"은 착시가 아니라 MuSkeMo import 시 knee collapse라는 실제 렌더 버그.** 측정값과 시각의 충돌 = MuSkeMo가 다리를 접어 렌더했기 때문.
3. OpenSim 실제 pose 투영(이 figure 좌 3패널)에서는 눈금과 그림이 정확히 일치, femur 정상.

**산출물:** `docs/images/literature_review/tlfb_femur_ratio_ruler_grid.png`
(좌 3: OpenSim 실제 pose 골격 투영 + 눈금/비율, 우 1: MuSkeMo 접힘 렌더 = 원인)

### 사용자 결정 필요
동영상에서 전신 비율을 정확히 보이려면:
- (i) MuSkeMo knee collapse 해결 (TLFB knee joint를 MuSkeMo 호환 형태로 변환 — 모델 작업 필요), 또는
- (ii) 전신 샷 대신 척추 중심(상체·골반) 샷 위주로 영상 구성, 또는
- (iii) OpenSim GUI 렌더 파이프라인 사용 (knee 정상 표시)
