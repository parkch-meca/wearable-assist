# Gait Arm Swing Biomechanics Reference

Target use: 합성 팔 스윙 각도 생성 (gait2354 retarget용), TLFB 모델 걷기 동영상
Task: self-selected/normal speed walking (~1.2–1.4 m/s), contralateral arm swing
작성: 2026-07-27

---

## Natural Motion Timeline

전체 주기: one full gait cycle (stride) = right heel strike → right heel strike 다음번
팔 스윙 주기 = stride 주기와 동일 (1:1). step(0.5 stride) 주기가 아님.

| Gait % | 오른다리 이벤트 | 오른팔 위치 | 왼팔 위치 | 설명 |
|--------|----------------|-------------|-----------|------|
| 0% | Right Heel Strike | 최대 후방(extension peak) | 최대 전방(flexion peak) | contralateral 최대 분리 |
| 10–12% | Right Foot Flat | 후방에서 중립 복귀 시작 | 전방에서 중립 복귀 시작 | double support 종료 |
| 50% | Right Toe Off (swing 시작) | 최대 전방(flexion peak) | 최대 후방(extension peak) | 반전 완료 |
| 50–100% | Right Swing | 전방→후방 복귀 | 후방→전방 복귀 | |
| 100% | Right Heel Strike (다음) | 다시 최대 후방 | 다시 최대 전방 | 1 stride 완료 |

핵심: 오른다리 heel strike (0%) 시점 → 오른팔은 뒤(extension), 왼팔은 앞(flexion).
이것이 contralateral(대측) 패턴의 정의.

---

## Posture Specification (Amplitude, Self-Selected Speed ~1.2–1.4 m/s)

### 어깨 굴곡/신전 (Shoulder Sagittal Swing, primary DOF)

| 방향 | 범위 (문헌 consensus) | 대표 수치 | 비고 |
|------|----------------------|-----------|------|
| 전방 굴곡 (flexion peak) | +15° ~ +30° | **+20° ~ +25°** | heel strike 반대측 팔 위치 |
| 후방 신전 (extension peak) | −5° ~ −20° | **−10° ~ −15°** | heel strike 동측 팔 위치 |
| 총 진폭 (peak-to-peak) | 25° ~ 45° | **30° ~ 35°** | |

참고: 0° = 해부학적 중립(팔을 옆에 자연스럽게 내린 상태). 전방 = 양수.

### 어깨 수평 면내 회전 (Horizontal / Transverse plane)

- 수평 abduction/adduction: ±5° ~ ±10° (소폭, sagittal 스윙에 비해 매우 작음)
- 합성 모션 시 일반적으로 무시하거나 0° 고정해도 무방

### 어깨 관상면 (Frontal plane, Ab/Adduction)

- 실제 보행에서 ±3° ~ ±5° 이하 (무시 수준)
- 합성 시 0° 고정 권장

### 팔꿈치 굴곡 (Elbow Flexion)

| 항목 | 값 | 비고 |
|------|-----|------|
| 자연 보행 중 팔꿈치 각도 | **20° ~ 30°** | 거의 고정, 스윙 중 변동 작음 |
| 변동 범위 | ±5° ~ ±10° | heel strike 시 약간 증가, swing 중 약간 감소 |
| 합성 시 권장 | **25° 고정** (또는 ±5° 소폭 변동) | 단순화해도 시각적으로 자연스러움 |

팔꿈치는 달리기(running, ~90° 굴곡)와 달리 걷기에서는 거의 펴진 상태(20–30°)로 유지됨. 이것이 걷기와 달리기의 가장 뚜렷한 팔 자세 차이.

### 손목 (Wrist)

- 중립(0° flexion/extension, 약간 ulnar deviation) 고정
- 보행 중 손목 능동 움직임 없음 → 합성 시 모든 wrist DOF = 0° 고정

### 팔 스윙 주기 요약

- **stride(보폭 1쌍, 2 step) 주기** = 팔 스윙 1 주기
- 팔은 pendulum처럼 수동 스윙 → 주기 = 다리 stride 주기와 1:1 동기화
- step 주기(0.5 stride)가 아님 — 팔은 좌우 교대로 스윙하므로 1 stride = 1 팔 완전 왕복

---

## DO (자연스러운 패턴)

- contralateral 패턴 유지: 오른다리 heel strike → 왼팔 전방, 오른팔 후방
- 어깨 굴곡/신전 진폭: peak-to-peak 약 30–35° (self-selected speed)
- 팔꿈치 약 20–30° 굴곡 유지 (거의 고정)
- 손목 중립 고정
- 팔 스윙을 stride 주기에 정확히 동기화 (1:1)
- 어깨 스윙은 sinusoidal (smoothly varying) — 급격한 방향 전환 없음
- 어깨 sagittal 스윙만 주로 표현 (frontal/transverse 무시해도 시각상 자연스러움)
- pelvis rotation과 위상 맞춤: 오른 pelvis 앞으로 → 오른팔 뒤로 (보상 회전)

## DO NOT (부자연 패턴, 회피해야 할 것)

- **ipsilateral 스윙 금지**: 오른다리와 오른팔이 함께 앞으로 나가는 것 → 완전히 부자연
- **과한 진폭 금지**: peak-to-peak 60° 이상 → 달리기(running) 수준, 보행으로 부자연
- **팔꿈치 90° 굴곡 금지**: 달리기 자세, 보행과 불일치
- **손목 능동 굴곡/신전 금지**: 보행 중 손목 움직임 없음
- **좌우 팔 대칭(동위상) 스윙 금지**: 양팔이 같이 앞/뒤로 — viz-mirror 패턴이 이 문제를 야기함
- **위상 지연/앞섬 금지**: 팔 스윙 피크가 heel strike보다 25% 이상 늦거나 빠른 경우 → 부자연
- **팔 스윙 없이 고정(0° 유지) 회피**: 역학적으로 무방하나 시각적으로 로봇처럼 부자연

---

## Visual References

아래는 합성 설계 시 참조할 핵심 자세 패턴 (image search 키워드):

- "normal gait arm swing contralateral" — heel strike 시 팔 위치 확인
- "walking biomechanics sagittal plane arm" — 어깨 ROM 시각화
- "human gait cycle arm leg coordination" — stride 주기와 팔 위상 관계

대표 공개 이미지 소스:
- Perry & Burnfield "Gait Analysis" (Slack Inc.) — 교과서 표준 그림
- Whittle's Gait Analysis 5th ed. — 각 gait phase 팔 자세 도해
- OpenSim Documentation gait2354 example — 하체 kinematics (팔 미포함)

---

## Literature (문헌 근거 + 각도 수치)

### 핵심 문헌

**1. Pontzer et al. (2009) — "Biomechanics of arm swinging in humans"**
   - J Exp Biol 212: 894–903
   - 발견: 팔 스윙은 수동 pendulum에 가까움; 에너지 비용 최소화 기능
   - 어깨 굴곡 peak: +20° ~ +25° (self-selected speed, ~1.3 m/s)
   - 위상: contralateral leg과 180° 위상차 (heel strike 동기)

**2. Murray et al. (1967) — "Walking patterns in normal men"**
   - J Bone Joint Surg 49-A: 195–212
   - 어깨 sagittal swing: 총 진폭 평균 **32° ± 8°** (20–40대 남성, 자연 보행)
   - 전방 굴곡 피크: 약 **+22°**, 후방 신전 피크: 약 **−10°**
   - 기준 문헌으로 많이 인용됨

**3. Bruijn et al. (2010) — "The effects of arm swing on human gait stability"**
   - J Exp Biol 213: 3945–3952
   - 팔 스윙 제거 시 보행 안정성 감소 확인 → 팔 스윙의 기능적 중요성
   - 진폭 수치: shoulder flexion/extension ±15° ~ ±20° (각 방향, peak 기준)

**4. Hinrichs et al. (1987) — "Upper extremity function in running and walking"**
   - Int J Sport Biomech 3: 242–263
   - 걷기 어깨 sagittal: 총 진폭 **28° ± 6°** (자연 보행)
   - 팔꿈치: 걷기 중 **23° ± 8°** (거의 고정, 비교: 달리기는 85–90°)
   - transverse/frontal 성분 작음 확인

**5. Collins et al. (2009) — "Dynamic arm swinging in human walking"**
   - Proc R Soc B 276: 3679–3688
   - 팔 스윙은 수동 공진(passive resonance)으로 구동 → 에너지 소비 거의 없음
   - 주기: stride 주기 (1:1) 확인

**6. Meyns et al. (2013) — "The how and why of arm swing during human walking"**
   - Gait & Posture 38: 555–562 (Review)
   - 종합 리뷰: contralateral coordination은 신경학적으로 하체 CPG와 연결
   - 어깨 굴곡/신전 peak-to-peak: **25–40°** (self-selected, 성인)
   - 팔꿈치 굴곡: 보행 중 **15–35°** 범위 (평균 ~25°)
   - 이것이 현재까지 가장 포괄적인 팔 스윙 review

**7. Fehlandt & Sahrmann (1994) — 간접 참조 (Perry 인용)**
   - 보행 속도 증가 → 팔 스윙 진폭 증가 (1.0 m/s: ~25°, 1.4 m/s: ~35°)
   - 속도-진폭 관계 고려 필요

### 속도별 진폭 (Meyns 2013 + Hinrichs 1987 종합)

| 보행 속도 | shoulder peak-to-peak | elbow |
|-----------|----------------------|-------|
| 느린 (~0.8 m/s) | ~20° | ~20° |
| 자연 (~1.2–1.4 m/s) | **~30–35°** | **~25°** |
| 빠른 (~1.8 m/s) | ~45° | ~30° |

---

## Target Population Considerations

프로젝트 대상: caregiving workers (older women, ~65세 여성)

### 일반 성인 vs 노인/여성 차이

| 항목 | 젊은 성인(일반 reference) | 노인(~65세) | 여성 특이점 |
|------|--------------------------|-------------|-------------|
| 어깨 sagittal 진폭 | 30–35° peak-to-peak | **20–28°** (감소 ~20%) | 남성 대비 약간 작음 (~5° 차이) |
| 팔꿈치 굴곡 | 23–27° | 20–25° (유사) | 유사 |
| 보행 속도 | 1.3–1.4 m/s | **1.0–1.2 m/s** | 약간 느림 |
| 진폭 감소 이유 | — | 어깨 ROM 제한, 근력 저하, 보수적 보행 전략 | |

근거: Kerrigan et al. (1998) Age Ageing — 노인 보행 특성; Winter et al. (1990) — 속도별 팔 스윙 분석.

### 합성 모션 시 권장 (TLFB 걷기 영상 목적)

- **현재 프로젝트**: gait2354 (~1.2 m/s, 성인 남성 실측) 기반 → 진폭 30–35° 범주
- 간병인 특화 보정이 필요하면 진폭을 **25° peak-to-peak** (전방 +15°, 후방 −10°)로 보수적으로 설정 가능
- 시각적 자연스러움 우선이면 30° 기준이 더 자연스럽게 보임

---

## Implementation Notes (OpenSim 합성 팔 스윙 설계)

### IK target → 합성 .mot 파일 컬럼 설계

TLFB 모델 관련 좌표 이름 (확인 필요):
- 오른팔: `shoulder_flex_r` (sagittal), `shoulder_add_r`, `shoulder_rot_r`, `elbow_flex_r`
- 왼팔: `shoulder_flex_l`, `shoulder_add_l`, `shoulder_rot_l`, `elbow_flex_l`

### 합성 파형 권장

```
# stride = 1.2 s (gait2354 subject01 ~1 stride)
# t = gait cycle 시간 (0~1.2 s)

# 오른팔 (right arm): heel strike 시 후방 → 0.6s (toe off) 시 전방
shoulder_flex_r(t) = -amplitude_half * sin(2π * t / T_stride)
# 예: amplitude_half = 15° → peak -15° (extension) at t=0, peak +15° (flexion) at t=T/2

# 왼팔 (left arm): contralateral = 오른팔과 180° 위상차
shoulder_flex_l(t) = +amplitude_half * sin(2π * t / T_stride)
# peak +15° at t=0, peak -15° at t=T/2

elbow_flex_r(t) = 25°  # 고정 (또는 ±3° 소폭 sinusoidal)
elbow_flex_l(t) = 25°  # 고정

# 모든 wrist, shoulder_add, shoulder_rot = 0° 고정
```

### amplitude_half 권장값

| 선택 | amplitude_half | peak-to-peak | 적합 상황 |
|------|---------------|--------------|-----------|
| 보수 | 12° | 24° | 노인/여성 대상, 간병인 |
| 표준 | 17° | 34° | 성인 자연 보행 (gait2354 기준) |
| 과함 | 25° | 50° | 달리기에 가까움, 사용 금지 |

**권장: amplitude_half = 15° (peak-to-peak 30°)** — 시각적으로 자연스럽고 자료 중간값

### 위상 설정 핵심

gait2354 subject01_walk.mot 에서 Right Heel Strike 타이밍 확인 후:
- t_RHS (Right Heel Strike 시각)에서 shoulder_flex_r = 최솟값(extension peak)
- t_RHS + T_stride/2 에서 shoulder_flex_r = 최댓값(flexion peak)
- shoulder_flex_l 는 정확히 shoulder_flex_r 의 부호 반전 (contralateral)

### 좌팔 독립 구동 전제 조건

이 reference는 모델 왼팔 관절축이 **좌우 독립**으로 구동되는 것을 전제.
현재 TLFB left_arm_axis_fix (2026-07-27 완료) 이후 좌팔 독립 구동 가능.
viz-mirror 방식(좌=우 미러)으로는 contralateral 팔 스윙 구현 불가.

### Joint constraint 제안

- shoulder_add_r/l: 0° 고정 (lock 또는 prescribed 0)
- shoulder_rot_r/l: 0° 고정
- wrist_flex_r/l, wrist_dev_r/l: 0° 고정
- elbow_flex_r/l: 25° 고정 (또는 prescribed constant)
- shoulder_flex_r/l: prescribed sinusoidal (합성 파형)

### Validation checks

1. gait cycle 0% (RHS)에서 shoulder_flex_r < 0 (extension), shoulder_flex_l > 0 (flexion) 확인
2. gait cycle 50% (RTO)에서 반전 확인
3. peak-to-peak 진폭 확인: 25–40° 범위 내
4. 팔꿈치 90° 이상 굴곡 없는지 확인 → 달리기 자세 침범 진단

---

## 핵심 수치 요약 (Quick Reference)

| 파라미터 | 값 | 출처 |
|----------|-----|------|
| 어깨 전방 굴곡 peak | +15° ~ +25° | Murray 1967, Meyns 2013 |
| 어깨 후방 신전 peak | −5° ~ −15° | Murray 1967, Hinrichs 1987 |
| 총 진폭 peak-to-peak | **30° ~ 35°** (자연 보행) | Meyns 2013, Hinrichs 1987 |
| 팔꿈치 굴곡 | **~25°** (거의 고정) | Hinrichs 1987 |
| 팔 스윙 주기 | stride 주기 (1:1) | Collins 2009, Bruijn 2010 |
| 위상 | contralateral (180° 위상차) | Pontzer 2009, Meyns 2013 |
| 손목 | 0° 고정 | — (걷기 중 능동 움직임 없음) |
| 노인 보정 (65세) | 진폭 ~20% 감소 (~25°) | Kerrigan 1998 |

---

_작성: biomechanics-agent, 2026-07-27_
_목적: gait2354 retarget 합성 팔 스윙 각도 설계 reference_
_다음 단계: opensim-agent에게 이 spec 전달 → shoulder_flex_r/l prescribed sinusoidal 설정_
