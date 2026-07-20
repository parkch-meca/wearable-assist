# 견갑골(scapula) 자유도 추가 — 방법·정량영향·권장경로 조사

**작성일**: 2026-07-21  
**목적**: 박스 옆면 손바닥 파지 시 체간 과굴곡(구조 한계)의 근본 원인인 "어깨가 파지점에 못 닿음"을 견갑 자유도로 해결 가능한지 조사. **실제 모델 수정 전 방법·정량영향·권장경로 보고** (사용자 결정 대기).

---

## 1. 현재 어깨 구조 (실측)

ThoracolumbarFB v2.0 (Male/Female, 원본 배포판 포함 **모든 변형**):

```
sternum → clavicle_R : WeldJoint "sterR_clavR_jnt"   (고정, 0 DOF)
clavicle_R → scapula_R: WeldJoint "clavR_scapR_jnt"  (고정, 0 DOF)
scapula_R → humerus_R : CustomJoint "shoulder_R"     (3 DOF: shoulder_elv, shoulder_rot, elv_angle)
```

- **scapula_R / clavicle_R body는 존재하나 흉곽에 용접(고정)** → protraction/retraction/elevation/depression 전부 불가.
- 이건 우리 팀 수정이 아니라 **ThoracolumbarFB 원설계** (Holzbaur 2005 arm26 단순화 철학).
- 자유로운 건 오직 glenohumeral 3 DOF뿐.

## 2. ES(척추기립근) 부착 확인 — 정량영향 판단의 핵심

- scapula/clavicle 부착 근육 **74개** = 전부 어깨근 (deltoid, rotator cuff, **trapezius**, **serratus**, pec).
- **ES(iliocostalis / longissimus / multifidus)는 scapula에 부착 0개** (실측 확인).
- ES = pelvis/sacrum/rib/spine 부착. → **견갑 DOF 추가가 ES 근육 line-of-action을 직접 바꾸지 않음.**
- 간접경로: trap_inf(T4–T12)·serratus 28개가 scapula↔흉추/늑골을 연결 → 흉추 부하 분담 소폭 변화 가능.
- 문헌(Cholewicki & McGill 1996, PMID 8900660): 견갑 안정근은 요추부하에 2차적. **ES 변화 추정 <5%p.**

**결론: 견갑 DOF 추가는 ES SO 결과에 영향 미미(<5%p 예상)하나 0은 아님 → Phase 1a regression 필수.**

## 3. 팔 부족량 실측 (근본 난이도)

자연 semi-stoop(biomech ref §8.4: pelvis −22°, hip 52°, knee −20°, lumbar −5.5°/seg)에서 팔이 박스 옆면(45cm)에 못 미치는 거리:

| 조건 (구조 변경 X, 기존 DOF만) | 어깨Y | 체간각 | 팔 부족 |
|---|---|---|---|
| 흉추 곧게 | 0.327 | 40.7° | **20.3 cm** |
| 흉추 −30°(생리 상한) | 0.283 | 44.5° | 16.1 cm |
| 흉추 −42°(생리 초과) | 0.268 | 45.8° | 14.7 cm |

- **부족량 15–20cm, 대부분 수직**. 어깨가 파지점보다 15–20cm 높음.
- 흉추 굴곡(기존 DOF)은 어깨를 ~6cm만 내림 → **혼자선 부족**.
- **생리적 견갑 protraction은 ~4–8cm** (Claeys 2015) → **견갑 DOF를 추가해도 15–20cm를 혼자 못 닫음.**

## 4. 경로별 비교

| 경로 | 내용 | 도달 기여 | 정량영향 | 난이도 | 판정 |
|---|---|---|---|---|---|
| **viz-전용 강체 이동** | 렌더서 팔사슬을 shift만큼 평행이동(protraction 모사) | 임의(수치상 100%) | **정확히 0** (.osim 불변) | 낮음 | ❌ **부적합** — 필요 shift 15–20cm에선 어깨↔상완 분리 착시(프로토타입서 확인). ≤~8cm에만 유효 |
| **M1: SC 2-DOF** | sterno-clav WeldJoint→CustomJoint(clav_prot/elev). Seth 2019 SC 파라미터 복사. scapula는 clavicle에 고정 유지 | ~8cm(주로 전방) | <5%p (regression 필요) | 낮음(~30분+regression) | △ 부분해결. 나머지는 자세로 |
| **M3: Seth ScapTho 4-DOF** | 흉곽 타원면 위 scapula 미끄러짐(protraction+depression+upward rot+winging). OpenSim 내장 ScapulothoracicJoint | 최대(수직 depression 포함) | <5%p 예상하나 trap/serratus 재계산, regression 범위 큼 | 높음(2–3일, ellipsoid 튜닝) | ○ 최고 충실도, 큰 작업 |
| **기존 DOF 최대활용** | 구조 변경 0. 전척추(흉추+요추) 분산 굴곡 + 중등도 semi-squat로 자연스러운 "깊은 들기" | 자세로 대부분 | 0(구조 불변) | 중간 | ○ 회귀위험 0, 단 자세는 깊음 |

## 5. 정량 목적 vs 시각 목적 분리 (핵심 통찰)

박스 들기의 두 목적:
1. **ES suit-effect 정량(SO)**: ES는 **척추** 근육 → **어깨/견갑과 무관**. 자연 척추 자세로 SO 돌리면 견갑 DOF 불필요. 박스 하중은 파지점(실제 박스 위치)에 외력으로 적용하면 됨.
2. **자연스러운 시각화(동영상/figure)**: 손이 박스에 닿아 보여야 함 → 여기서만 견갑/도달이 문제.

→ **정량 결과는 견갑 DOF 없이도 정확**. 시각화만을 위해 구조 수술을 할지가 판단 포인트.

## 6. 권장 (사용자 결정 대기)

**부족량(15–20cm)이 어떤 단일 수단(견갑 8cm, 흉추 6cm)보다 크다**는 게 핵심 사실. 따라서:

- **1순위 — 기존 DOF 최대활용(구조 변경 0)**: 전척추 분산 굴곡 + 중등도 semi-squat로 자연스러운 깊은 들기 자세 생성. 회귀위험 0, ES 정량 정확. 자세는 실제보다 다소 깊으나 "둥근 등 깊은 들기"로 자연스럽게 보이도록. → 시각검증 통과 시 즉시 SO 가능.
- **2순위 — M1(SC 2-DOF) 추가**: 1순위로도 ~8cm 부족 시, 최소 구조 변경으로 전방 8cm 확보. Phase 1a regression(max ΔES>5%p 협의) 통과 조건. ES 물리 불변이라 통과 가능성 높음.
- **3순위 — M3(Seth ScapTho)**: 논문급 견갑 kinematics가 꼭 필요할 때만. 큰 작업 + 광범위 regression.
- **비권장 — viz-전용 강체 이동**: 필요 shift가 커 어깨 분리 착시(실증됨).

**요약**: ES 정량엔 견갑 불필요(구조 안전). 자연 시각화를 위해선 먼저 기존 전척추 DOF를 제대로 써보고, 부족분만 M1로 보완하는 단계적 접근 권장. 처음부터 M3 대수술은 비용 대비 불리.

---

## 참고문헌
- Holzbaur KRS, Murray WM, Delp SL. A model of the upper extremity. *Ann Biomed Eng.* 2005;33(6):829-840. PMID 16078622.
- Seth A, Matias R, Veloso AP, Delp SL. A biomechanical model of the scapulothoracic joint. *PLoS One.* 2016;11(1):e0141028. PMID 26731718. (OpenSim ScapulothoracicJoint 표준)
- de Groot JH, Brand R. Shoulder rhythm regression model. *Clin Biomech.* 2001;16(9):735-743. PMID 11714546.
- Cholewicki J, McGill SM. Mechanical stability of the in vivo lumbar spine. *Clin Biomech.* 1996;11(1):1-15. PMID 8900660.
- Claeys K, et al. Scapulothoracic mobility & 3D shoulder kinematics. *Clin Biomech.* 2015;30(6):553-558.

_실제 모델 수정은 미실시. 사용자 경로 결정 후 진행._
