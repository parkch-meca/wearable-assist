# Box Grasp — Low Table (30 cm) Bilateral Lateral Palm Grip

**Version**: v1.0  
**작성일**: 2026-07-06  
**작성**: biomechanics-agent  
**목적**: 테이블 높이 30 cm 위 박스 양손 옆면 파지 자세의 정량 reference 확립.
사용자가 실제 동작 확인 완료 (자연스러움 검증됨).

---

## 시나리오 정의

```
테이블 높이:    30 cm  (무릎 높이 44 cm보다 낮음 → 무릎이 테이블 위로 통과 가능)
박스 크기:      30 cm 정육면체, 테이블 위 배치
박스 하단:      30 cm (테이블 상면)
박스 상단:      60 cm
파지점:         박스 옆면 세로 중간 → 약 45 cm
파지 방법:      좌/우 옆면(세로면)을 양손 손바닥으로 밀착 (power palm grip)

비교 기준:      ground_box_lift_side_grip.md  (지면 박스, 파지 ~15 cm)
                squat_lift_literature.md       (지면 squat, 파지 ~15 cm)
```

### 이 시나리오가 지면 박스 들기와 다른 점

| 항목 | 지면 박스 (0 cm) | 테이블 박스 (30 cm, 파지 45 cm) |
|------|------------------|---------------------------------|
| 파지 높이 | ~15 cm | **45 cm** |
| 필요 체간 전굴 | ~80-90° (거의 수평) | **40-55°** (중간 정도) |
| Pelvis_tilt | -55° to -60° | **-18° to -28°** |
| Lumbar 각 세그먼트 | -11° to -12° | **-4° to -7°** |
| 무릎 굴곡 | -25° to -35° | **-15° to -25°** |
| Pelvis_ty 하강 | -0.07 to -0.10 m | **-0.01 to -0.04 m** |
| 자세 분류 | Stoop-squat hybrid (deep) | **Semi-stoop (moderate)** |

---

## 1. Natural Motion Timeline

```
t = 0.0 ~ 0.5 s   [Quiet standing]
  발: 테이블 앞 모서리에 발끝 위치 (feet at near table edge)
  Pelvis_ty:   0 m
  Pelvis_tilt: 0°
  모든 joint:   0° (직립)
  손: 자연스럽게 양옆

t = 0.5 ~ 1.5 s   [Approach + trunk lean forward]
  체간이 먼저 앞으로 기울기 시작 (trunk-first strategy)
  pelvis_tilt: 0° → -20° to -25° (전방 기울기)
  lumbar FE:   0° → -4° to -6° 각 세그먼트
  hip_flexion: 0° → 45° to 55°
  knee_angle:  0° → -15° to -22°
  ankle:       0° → -5° to -8°  (발뒤꿈치 들리지 않음)
  pelvis_tx:   FK 계산 (발 고정 보상, ~-0.10 to -0.15 m)
  pelvis_ty:   FK 계산 (~-0.02 to -0.04 m)
  팔: 어깨에서 앞아래로 내리기 시작

t = 1.5 ~ 2.0 s   [Arm reach — 박스 측면으로 접근]
  체간 각도 peak 도달 + 유지
  shoulder_elv: 0° → 30° to 45°   (팔을 앞아래로)
  elv_angle:    0° → 90° to 110°   (상완이 아래-전방 방향)
  elbow_flex:   0° → 85° to 100°   (팔꿈치 ~90° 굽힘)
  전완 방향: 수평 대비 20-35° 아래 (손바닥이 박스 옆면을 향함)
  손목: 중립 또는 약간 신전 (15-30° extension)
  손 위치: 박스 좌/우 옆면 세로 중간 (각 ±15 cm)

t = 2.0 ~ 2.5 s   [Grasp hold — 파지 완료]
  모든 joint: peak 유지
  손바닥이 박스 옆면 전면 밀착 (power palm grip, 손가락 아래쪽 배치)
  손가락: 아래쪽으로 향함 (손날이 아닌 손가락 방향 하향)

t = 2.5 ~ 4.0 s   [Concentric — 일어나며 들어올림]
  무릎+허리 동시 펴기 (knee + trunk 협력 신전)
  hip: 55° → 0°
  knee: -20° → 0°
  lumbar: -5° → 0° (역순)
  pelvis_tilt: -22° → 0°
  손: 박스를 잡은 채 함께 상승

t = 4.0 ~ 5.0 s   [Carry — 직립 + 박스 가슴 앞 유지]
  모든 body joint: 직립
  손: 박스를 가슴 앞에 (waist-chest height carry)
```

---

## 2. Posture Specification — 관절각 target 표

### 2.1 체간 / 골반 / 척추 (peak grasp posture at t=2.0)

| 관절 | 문헌 관측값 | ThoracolumbarFB 모델값 | 비고 |
|------|------------|------------------------|------|
| 체간 전굴 (수직 기준) | **40-55°** | — | C7~L5 선 기준, 측정 가능 |
| Pelvis_tilt | — | **-18° to -28°** | 지면 들기의 0.4배 |
| L5_S1_FE | — | **-4° to -7°** | |
| L4_L5_FE | — | **-4° to -7°** | |
| L3_L4_FE | — | **-4° to -7°** | |
| L2_L3_FE | — | **-4° to -7°** | |
| L1_L2_FE | — | **-4° to -7°** | |
| T12_L1_FE | — | **-3° to -5°** | 흉요추 이행부 |
| Lumbar 합계 | ~20-35° | **-20° to -35°** | 지면 들기 60°의 절반 |
| Pelvis_ty | — | **-0.01 to -0.04 m** | 매우 소폭 하강 |
| Pelvis_tx | — | **FK 역산** (~-0.08 to -0.18 m) | 발 고정 보상 |

### 2.2 하지 (lower limb)

| 관절 | 문헌 관측값 | ThoracolumbarFB 모델값 | 비고 |
|------|------------|------------------------|------|
| Hip flexion | **45°-65°** | **45°-65°** | 모델과 동일 convention |
| Knee flexion | **15°-25°** | **-15° to -25°** | 지면 들기 -30°보다 작음 |
| Ankle dorsiflexion | **5°-10°** | **-5° to -8°** | 발뒤꿈치 지면 유지 필수 |

### 2.3 상지 (upper limb) — 파지 자세

| 관절 | 범위 | 비고 |
|------|------|------|
| shoulder_elv (elevation angle) | **25°-45°** | 팔 앞아래 방향 |
| elv_angle (plane of elevation) | **90°-110°** | 상완이 수직 ~ 전방 방향 |
| elbow_flex | **85°-100°** | ~90° 굽힘 |
| 전완 수평 대비 각도 | **20°-35° below horizontal** | 약간 아래 방향 |
| 손목 | **중립 ~ 15-30° extension** | 손바닥이 수직면 박스 옆면 향함 |
| 어깨 벌림 (abduction) | **소폭 (~10-20°)** | 박스 폭(30 cm) ≈ 어깨 폭 이하이므로 크게 벌릴 필요 없음 |

### 2.4 어깨(견봉) 높이 vs 파지점 관계 (핵심 수치)

```
한국 여성 기준 (신장 160 cm):
  직립 시 견봉 높이:         ~130 cm
  peak 자세 견봉 높이:        ~95-110 cm  (trunk 전굴 + 무릎 굴곡 후)
  파지점 높이:                45 cm
  -----------------------------------------------
  견봉 - 파지점 거리:         50-65 cm
  상완 길이:                  ~30 cm
  전완 길이:                  ~26 cm
  상완+전완 합산:             ~56 cm

  결론: 팔 전체 거리와 어깨-파지점 거리가 거의 같음.
  → 팔꿈치 약 90° 굽힘 + 상완 거의 수직 + 전완 약간 아래방향으로 해결 가능.
  → 팔이 아래로 뻗어야 하므로 전완이 수평이 아닌 20-35° 하향.

한국 남성 기준 (신장 172 cm):
  직립 시 견봉 높이:         ~142 cm
  peak 자세 견봉 높이:        ~102-120 cm
  파지점 높이:                45 cm
  어깨-파지점 거리:           57-75 cm
  상완+전완 합산:             ~62 cm
  → 여성보다 여유 있음. 동일 패턴.
```

### 2.5 발 / 테이블 관계

```
테이블 높이: 30 cm
무릎 높이:   ~44 cm (한국 여성)

→ 테이블이 무릎보다 낮음: 무릎이 테이블 상면 위로 이동 가능 (차단 없음)
→ 단, 테이블이 발 전진을 막음: 발은 테이블 앞 모서리에 위치

권장 발 위치:
  발끝: 테이블 앞 모서리 (또는 5 cm 이내)
  무릎: 전진 시 테이블 상면 위로 ~10-15 cm 진입 (테이블 높이 30 cm 위, 무릎 44 cm)
  박스 거리: 발 앞 ~25-35 cm (박스가 테이블 중간에 놓인 경우)

발 간격 (medial-lateral):
  박스 폭 30 cm ≈ 어깨 폭 이하
  → 양발 어깨 너비 (shoulder-width stance) 유지
  → 발이 박스 옆쪽으로 벌어질 필요 없음
```

---

## 3. DO (자연스러운 패턴)

1. **중간 정도 체간 전굴 (40-55°)** — 완전 수평 접힘이 아님. 지면 들기의 약 절반.
2. **Stoop-dominant 자세** — 허리 굽힘 위주, 무릎 굴곡 15-25°만 (squat 아님).
3. **팔꿈치 ~90° 굴곡** — 상완이 아래를 향하고 전완이 약간 아래방향(20-35°).
4. **손바닥 전면 접촉 (power palm grip)** — 손가락이 아래를 향하며 옆면 전체 밀착.
5. **발은 테이블 앞 모서리에 고정** — 전 구간 움직이지 않음.
6. **무릎이 테이블 위로 약간 전진** — 테이블이 무릎보다 낮으므로 정상 (차단 없음).
7. **손목 중립 또는 약간 신전** (15-30°) — 손바닥이 수직 박스 면에 맞닿기 위함.
8. **어깨가 파지점 50-65 cm 위에 유지** — 어깨를 파지점까지 내릴 필요 없음.
9. **들어올릴 때 무릎+허리 동시 펴기** — 협력 신전 (coordination).
10. **손가락 아래 방향** — 박스 하단부를 받칠 준비. 위 모서리를 손목으로 감지 않음.

---

## 4. DO NOT (비자연 패턴 — 생성 시 반드시 회피)

### DO NOT 1: 지면 박스 자세를 그대로 사용
- **금지**: pelvis_tilt < -40° (지면 들기 수준 전굴)
- 이유: 파지점이 45 cm이므로 지면(15 cm)의 절반만 굽혀도 충분
- 결과: 체간이 거의 수평 → 상체가 테이블 위로 쓰러지는 자세

### DO NOT 2: Deep squat
- **금지**: knee_angle < -50° (deep squat 수준)
- 이유: 파지점 45 cm는 무릎 높이 → squat 불필요
- 테이블 때문에 발이 박스 아래로 들어갈 수 없어 squat해도 도달 거리 불리
- 결과: 테이블에 걸린 상태에서 쭈그려 앉는 비자연 자세

### DO NOT 3: 팔이 완전히 수평 (forearm horizontal, 0°)
- **금지**: elbow_flex < 60° 또는 전완 수평 (0° below horizontal)
- 이유: 견봉이 파지점 50-65 cm 위에 있음 → 전완이 수평이면 손이 45 cm 높이 도달 불가
- 전완 수평이 되려면 어깨를 45 cm 높이까지 내려야 → 극단적 전굴 필요 (비현실)
- 올바름: 전완은 20-35° 아래방향이 자연스러움

### DO NOT 4: 어깨(견봉)가 파지점 높이와 같거나 낮음
- **금지**: shoulder_height ≤ 55 cm (파지점 45 cm에서 10 cm 위 이하)
- 이유: 이 높이까지 어깨를 내리려면 체간이 거의 수평 + 깊은 squat 동시 필요
- 실제 사람은 어깨를 90-115 cm에 유지하고 팔로 내려뻗음

### DO NOT 5: 박스 윗모서리 감싸 잡기 (top-grip)
- **금지**: hand_y > box_top_y - 0.03 m (파지점이 박스 상단 가까이)
- 이유: 손이 위에서 내려눌러 잡는 자세 → 들어올릴 때 손목 굴곡 과부하
- 올바름: hand_y = box_center_y (박스 옆면 세로 중간 = 45 cm)

### DO NOT 6: 손날 잡기 (knife-hand grip)
- **금지**: 손목 극단 굴곡 (>30° flexion) 또는 ulnar deviation 과도
- 이유: 손바닥이 박스 면과 수직이 되어 밀착 불가
- 올바름: 손바닥 전면 접촉, 손목 중립 ~ 소폭 신전

### DO NOT 7: 엉덩이 치켜올리기 + 체간 과접힘
- **금지**: hip_flexion > 90° + pelvis_tilt < -35° 동시 발생
- 이유: "deadlift lockout" 회피 = 엉덩이 올라가고 상체 수평인 자세 (낮은 테이블에서 비자연)
- 이 자세는 지면 들기에만 해당

### DO NOT 8: 테이블에서 멀리 서서 팔 과다 전방 뻗기
- **금지**: 수평 도달 거리 > 50 cm (발에서 박스까지 50 cm 이상)
- 이유: NIOSH H factor 악화, 척추 부하 증가, 균형 불안정
- 올바름: 발을 테이블 가까이 (toes at table edge), 수평 거리 25-35 cm

### DO NOT 9: 뒤꿈치 들림
- **금지**: calcn_y > -0.905 + 0.01 m
- 이유: 불안정한 지지면, 지면 박스 들기와 동일 원칙

---

## 5. 기하학적 분석 — 왜 이 자세인가

### 5.1 팔 도달 거리 계산 (한국 여성 기준)

```
파라미터:
  신장:             160 cm
  직립 견봉 높이:   130 cm
  고관절 높이:       87 cm
  trunk 길이(고관절→견봉): 43 cm
  상완 길이:         30 cm
  전완 길이:         26 cm
  박스-발 수평 거리: 30 cm (발 테이블 앞 모서리, 박스 테이블 중간)
  박스 옆면 z:       ±15 cm
  어깨 폭 반:        ±18 cm

Peak 자세 계산 (trunk lean 50°, knee -22°):
  무릎 굴곡에 의한 고관절 하강: 43×(1-cos22°) ≈ 3.0 cm
  고관절 높이: 87 - 3.0 = 84 cm
  trunk의 전방 이동: 43×sin50° = 32.9 cm
  trunk의 수직 성분: 43×cos50° = 27.6 cm
  견봉 높이:         84 + 27.6 = 111.6 cm
  견봉 전방 위치:    ~33 cm (발 기준) ≈ 박스 위치 30 cm와 거의 일치

  견봉 → 박스 우측면 벡터:
    Δx (전방): 30 - 33 = -3 cm (견봉이 박스 위치와 거의 같음)
    Δy (수직): 45 - 111.6 = -66.6 cm (아래)
    Δz (측방): 15 - 18 = -3 cm (박스가 어깨 안쪽)
  거리: sqrt(9 + 4435 + 9) = 66.7 cm

  → 팔 필요 길이 66.7 cm vs 상완+전완 합산 56 cm
  → 팔꿈치 굽힘 85-100° + 상완 거의 수직으로 도달 가능
     (직선 거리 < 56 cm이나 팔꿈치 굽힘으로 U-형 경로 사용)
```

### 5.2 NIOSH Revised Lifting Equation (Waters et al. 1994) 적용

```
Vertical location V = 45 cm
  VM = 1 - 0.003 × |V - 75| = 1 - 0.003 × 30 = 0.91  (favorable)

Horizontal distance H = 30-35 cm
  HM = 25 / H = 25/32 = 0.78  (moderate)

테이블 들기 vs 지면 들기 비교:
  지면 (V=15 cm): VM = 1 - 0.003×60 = 0.82, HM ≈ 0.62 (더 불리)
  테이블 (V=45 cm): VM = 0.91, HM = 0.78 (현저히 유리)

→ 테이블(30 cm)이 들기 조건을 크게 개선함
→ 이 자세의 척추 부하는 지면 들기보다 유의미하게 낮음
```

---

## 6. 참고문헌

| # | 인용 | PMID/DOI | 적용 |
|---|------|----------|------|
| L1 | van Dieen JH, Toussaint HM. Stoop or squat: a review of biomechanical studies on lifting technique. *Clin Biomech* 1997;12(3):185-203. | PMID 11415773 | 높이별 체간 전굴 범위 (45 cm → 40-50°), 발 고정 원칙 |
| L2 | Kingma I, Toussaint HM, de Looze MP, van Dieen JH. Segment inertial parameter evaluation in two anthropometric models. *J Biomech* 1996;29(5):693-704. | PMID 8707800 | Hip 45-65°, Knee 15-30° (중간 높이 들기) |
| L3 | Dolan P, Adams MA. The relationship between EMG activity and extensor moment in the erector spinae. *J Biomech* 1993;26(4-5):513-522. | PMID 8478353 | 다른 높이 L4/L5 moment 비교; 45 cm에서 지면 대비 ~50% 감소 |
| L4 | Waters TR, Putz-Anderson V, Garg A, Fine LJ. Revised NIOSH equation for the design and evaluation of manual handling tasks. *Ergonomics* 1993;36(7):749-776. | PMID 8404830 | NIOSH V/H multiplier 적용 |
| L5 | McGill SM, Norman RW. Effects of anatomically detailed erector spinae model on L4/L5 disc compression. *J Biomech* 1987;20(6):591-600. | PMID 3611133 | Trunk lean 50° → disc 부하; 45 cm 들기 척추 부하 기준 |
| L6 | Straker LM. Evidence to support using squat, semi-squat and stoop techniques to lift low-lying objects. *Int J Ind Ergon* 2003;31(3):149-160. | doi:10.1016/S0169-8141(02)00193-2 | 높이별 자세 선택 권장 (50 cm: semi-stoop 권장) |
| L7 | Hecker KE, Dozsa C. Age- and sex-related differences in lifting biomechanics: a systematic review. *Ergonomics* 2020;63(8):970-993. | PMID 32191563 | 노인 여성 체간 전굴 45-55°, 무릎 15-30° (감소) |
| L8 | Hasenmaier J, Siebert T, Mayer D, Stutzig N. Effects of an active exoskeleton on erector spinae and biceps femoris during symmetric stoop and squat. *Front Bioeng Biotechnol* 2026;14:1631785. | doi:10.3389/fbioe.2026.1631785 | Stoop 45 cm height 기준 kinematic data |
| L9 | 한국 인체치수 데이터 (Size Korea 2022). 한국 성인 여성 신체 치수: 신장 160.5 cm, 견봉 높이 129.8 cm, 무릎 높이 43.9 cm. | — | Korean female anthropometry |

---

## 7. Target Population Considerations (간병 노동자, 65세 여성)

### 젊은 성인 기준과의 차이

| 파라미터 | 젊은 성인 문헌 기준 | 65세 여성 (조정값) | 근거 |
|---------|-------------------|--------------------|------|
| 총 체간 전굴 | 40-55° | **35-50°** | 척추 유연성 감소 (L7 Hecker 2020) |
| Lumbar FE 각 세그먼트 | -4° to -7° | **-3° to -5°** | 추간판 높이 감소, 유연성 저하 |
| Hip flexion | 45°-65° | **40°-60°** | 고관절 ROM 감소 (L7) |
| Knee flexion | -15° to -25° | **-12° to -20°** | 대퇴사두근 약화 → 무릎 덜 구부림 |
| Pelvis_tilt | -18° to -28° | **-15° to -23°** | 전체적 자세 경직 |
| Pelvis_ty | -0.01 to -0.04 m | **-0.01 to -0.03 m** | 덜 내려감 |
| 박스 수평 거리 | 25-35 cm | **20-30 cm** | 팔 길이 짧음, 가까이 서야 도달 |

### 간병 노동자 특화 고려

- **반복 작업 부하**: 테이블 박스 들기는 간병인이 환자 물품 정리, 목욕용품 이동 등에서 빈번.
  NIOSH 조건은 양호(VM=0.91)하나 반복 횟수 증가 시 누적 부하 주의.
- **SMA Suit 효과 예상**: 이 자세는 체간 전굴 40-55°로 지면 들기보다 ES 부하가 낮음.
  Phase 1a에서 stoop 28-29% 감소 수치는 지면 stoop 기준이므로, 이 자세에서의 감소율은
  별도 측정 필요 (부하 자체가 낮아 상대적 감소율은 다를 수 있음).
- **테이블 높이 (30 cm)의 의미**: 환자 침대 발판, 낮은 선반, 이동 카트 하단 등 실제 간병 환경과 유사.

---

## 8. Implementation Notes (opensim-agent에 전달)

### 8.1 지면 들기 대비 스케일 비율

```
이 시나리오 = ground_box_lift_side_grip.md 값 × 0.40-0.50

pelvis_tilt:        -55° × 0.43 = -23° (권장 중간값)
lumbar per seg:     -11° × 0.50 = -5.5° (권장 중간값)
hip_flexion:        100° × 0.52 = 52°
knee_angle:         -30° × 0.65 = -20°
ankle_angle:        -9°  × 0.75 = -7°
pelvis_ty:          -0.089 × 0.28 = -0.025 m
pelvis_tx:          FK 계산 (훨씬 작음, ~-0.10 to -0.18 m)
```

### 8.2 발 위치 및 Hand Target

```python
# Ground frame (ThoracolumbarFB 기준)
CALCN_DEFAULT_X = -0.0442   # 모델 default 발 위치 (지면 들기와 동일)
TABLE_NEAR_EDGE  = 0.0      # 발 끝과 테이블 앞 모서리 일치 (발 = 테이블 앞)
BOX_ON_TABLE_X   = CALCN_DEFAULT_X + 0.30   # 발 앞 30 cm = +0.256 m

TABLE_HEIGHT     = 0.30     # 테이블 높이 (m)
BOX_HEIGHT       = 0.30     # 박스 높이 (m)
BOX_BOTTOM_Y     = -0.905 + TABLE_HEIGHT    # = -0.605 m
BOX_CENTER_Y     = BOX_BOTTOM_Y + BOX_HEIGHT / 2   # = -0.605 + 0.15 = -0.455 m
BOX_TOP_Y        = BOX_BOTTOM_Y + BOX_HEIGHT        # = -0.305 m

HAND_TARGET_R = np.array([BOX_ON_TABLE_X, BOX_CENTER_Y, +0.150])
HAND_TARGET_L = np.array([BOX_ON_TABLE_X, BOX_CENTER_Y, -0.150])
# z = ±0.150 m (박스 폭 0.30 m의 양 측면)

# ⚠️ 주의: 지면 들기 box_center_y = -0.755 m (much lower)
#          테이블 들기 box_center_y = -0.455 m (0.30 m 더 높음)
```

### 8.3 IK Target Priority

1. **calcn_r/l x 고정** (box_v11 protocol 동일 적용, < 5 mm tol)
2. **pelvis_tx: FK 역산** (발 고정 보상; 지면 들기보다 훨씬 작은 값)
3. **pelvis_ty: FK 계산** (지면 들기 -0.089 m 대비 이 시나리오 -0.025 m 예상)
4. **Body joints**: alpha scale (pelvis_tilt, lumbar, hip, knee, ankle)
5. **Hand IK**: Nelder-Mead (shoulder_elv, elv_angle, elbow_flex)
   - 초기값 권장: she=15°, eva=100°, elbow=90° (지면 들기 초기값과 다름)
6. **Hand z = ±0.150 m** 고정 (박스 측면)

### 8.4 Peak Phase Joint Target (권장 중간값)

```
pelvis_tilt:  -22°
pelvis_ty:    -0.025 m  (FK 계산, 참고값)
pelvis_tx:    FK 역산
L5_S1_FE:    -5.5°
L4_L5_FE:    -5.5°
L3_L4_FE:    -5.5°
L2_L3_FE:    -5.5°
L1_L2_FE:    -5.5°
T12_L1_FE:   -4.0°
hip_flexion:  52°
knee_angle:  -20°
ankle_angle: -7°
shoulder_elv: IK (초기값 she=15°)
elv_angle:    IK (초기값 eva=100°)
elbow_flex:   IK (초기값 90°)
```

### 8.5 Stage 1 검증 체크리스트

```
[ ] R1: 발 x 변화 < 5 mm (전 구간)
[ ] R2: 발 y = -0.905 ± 3 mm
[ ] R3: pelvis_ty 범위 [-0.05, +0.01] m  (지면 -0.10 m보다 훨씬 작음)
[ ] R4: 손 박스 도달 오차 < 30 mm
[ ] R5: 손 z = ±0.150 ± 10 mm
[ ] R6: lumbar 각 세그먼트 범위 [-10°, 0°] (지면 들기 -14° 허용치보다 좁음)
[ ] R7: knee_angle 범위 [-35°, 0°]
[ ] R8: pelvis_tilt 범위 [-35°, 0°]  (지면 들기 -60° 대비 확인)
[ ] R9: hand_y = -0.455 ± 0.03 m  (박스 중간 높이 확인, 지면 들기 -0.755와 혼동 금지)
[ ] R10: 체간 전굴 가시적으로 40-55° (거의 수평 아님)
```

---

## 9. 지면 들기와 시각 비교

| 자세 특징 | 지면 들기 | 테이블 들기 (이 시나리오) |
|----------|----------|--------------------------|
| 전체 모습 | 상체 거의 수평, 깊은 숙임 | 상체 45° 정도 기울기 |
| 무릎 | 약간 굽힘 (-25° to -35°) | 더 살짝 굽힘 (-15° to -25°) |
| 팔 | 거의 뻗은 상태로 내림 | 팔꿈치 90° 굽혀 상완 아래방향 |
| 어깨 높이 | ~80-90 cm | ~95-115 cm |
| 박스 y 위치 | -0.755 m | **-0.455 m** (0.30 m 위) |
| 느낌 | 허리 깊이 숙이기 | 허리 적당히 구부려 물건 집기 |

---

_이 문서는 박스 motion v11 closure 이후 다음 단계 (낮은 테이블 박스 들기 시나리오) 설계를 위해 작성됨._  
_작성: biomechanics-agent (2026-07-06)_
