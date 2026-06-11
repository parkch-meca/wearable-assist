# TLFB 머리 비율 실측 + 척추(ES) 중심 시각화 (1회 측정·렌더)

**일자:** 2026-06-11
**대상:** `MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim`
**목적:** (1) 미검증 항목 "머리 커보임" 사실 확인, (2) 동영상용 척추 중심 깨끗한 렌더 테스트. 추측·patch 루프 없음.

---

## [1] 머리/전신 비율 실측 — **TLFB 정상 (1/7.7)**

측정법: skull+jaw `.vtp` mesh를 OpenSim frame transform으로 world 좌표 변환 → bounding box.
stature = skull top → foot bottom (calcaneus/foot mesh 최저점).

| 모델 | head height | stature | stature/head | head 비율 | 판정 |
|------|------|------|------|------|------|
| **TLFB** | **0.230 m** | **1.769 m** | **7.69** | **1/7.7** | ✅ 정상 |
| Rajagopal | 0.193 m | 1.669 m | 8.63 | 1/8.6 | 정상(머리 작음) |
| Lai 2023 | 0.193 m | 1.671 m | 8.64 | 1/8.6 | 정상(머리 작음) |
| 표준 인체 | ~0.23 m | ~1.75 m | 7.5–8.0 | 1/7.5–1/8 | 기준 |

**결론:** TLFB head/body = **1/7.7, 표준 범위(1/7.5–1/8) 내**. Rajagopal/Lai(1/8.6)보다 오히려 교과서 표준에 더 가까움.
- TLFB head 높이 절대값 0.230 m, head 폭 ~0.195 m — 1.77 m 신장 대비 정상.
- **"머리 커보임"은 skull mesh 과대(scale 오류)가 아님 = 시각화 착시.** (이전 620-근육 풍선이 체간을 부풀려 상대적으로 두상이 강조됐던 것.)
- mesh scale/교체 불필요.

## [2] 척추(ES) 중심 정리 렌더 — **동영상 사용 가능 수준**

설정 변경(모델 교체 없음):
- `muscle_visualization_radius`: 0.015 m → **0.006 m (6 mm)**
- 표시 근육: 척추/ES 군 **270개만** (iliocostalis 28, longissimus 58, multifidus 110, QL 36, psoas 22, semispinalis 4, splenius 12). 나머지 사지·표층 체간근 **350개 hide**.
- wrapping sphere/cylinder/ellipsoid + joint center + landmark **전부 hide**.
- 카메라: back·side·oblique-post·front (ES 가시성 우선).

**결과:** 풍선 해소. 골격 정상 비례 노출(머리·다리 정상). side/back에서 erector spinae + multifidus column이 해부학적으로 선명하게 식별됨.

→ **자가 vision 판정:** ✅ "보여줄 수 있는" 수준. 단, 동영상 본 렌더는 **사용자 승인 후** 진행.

**산출물:** `docs/images/literature_review/tlfb_head_ratio_spine_grid.png`

### 사용자 결정 필요
- 이 척추중심 시각화(6 mm, ES 270개)로 동영상 진행할지
- 또는 표시 근육군 범위 조정(예: psoas/splenius 제외, ES proper만) 여부
