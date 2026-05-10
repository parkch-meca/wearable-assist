# Industry Evaluation Standards for Wearable Robot / Lifting Assessment (2026-04-29)

**작성**: biomechanics-agent  
**목적**: KIMM SMA fabric wearable suit 평가 framework에 산업 표준 통합  
**대상**: Caregiving workers (한국 요양보호사, 여성 55-65세), 박스 20 kg 지면 들기  
**현재 framework**: OpenSim Moco ES activation 28-29% 감소, L5/S1 moment 시뮬레이션

---

## 1. Wearable Robot 표준

### 1.1 ISO 13482:2014 — Physical Assistant Robot (핵심)

| 항목 | 내용 |
|------|------|
| 정식 명칭 | Safety Requirements for Personal Care Robots |
| 발행 | 2014 (초판), 2019 재검토 |
| 한국 채택 | KS B ISO 13482:2016 (정식 채택, KS번호 부여) |
| 유럽 | EN ISO 13482 (CE marking 근거) |
| 일본 | JIS B 8445 (동등 표준) |
| 미국 | 자발적(voluntary); OSHA 미강제 |

**Type B Physical Assistant Robot** = wearable exoskeleton/exosuit에 직접 적용 가능한 분류:
- 사용자와 물리적 접촉하여 신체 기능을 직접 보조/증강하는 로봇
- SMA fabric wearable suit = Type B 해당

**안전 메트릭 (Annex B)**:

| 메트릭 | 허용 한계 | 비고 |
|--------|---------|------|
| 인터페이스 힘 (정적) | ≤ 150 N | 준정적 접촉 |
| 인터페이스 힘 (동적) | ≤ 250 N (<0.5 s) | 충격성 힘 |
| 피부 접촉 온도 (단기) | ≤ 48°C | |
| 피부 접촉 온도 (장기) | ≤ 43°C | |
| 피부 압력 (지속) | ≤ 50 kPa | 통증 임계값 기준 |
| 비상정지 반응시간 | ≤ 250 ms | |
| ROM 보호 | 하드웨어 스톱 필수 | 과굴곡/신전 방지 |

**중요 한계**: ISO 13482는 **안전(Safety)** 표준 — 효과(Performance)는 명시하지 않음.  
Performance 평가는 ASTM F3474 또는 자체 프로토콜이 필요.

---

### 1.2 ISO/TR 23482-1:2020

| 항목 | 내용 |
|------|------|
| 정식 명칭 | Robotics — Application of ISO 13482 — Part 1: Safety-related test methods |
| 형태 | Technical Report (TR) = 가이던스, 비강제 |
| 발행 | 2020 |
| 내용 | ISO 13482 준수 확인을 위한 시험 방법론 제공 |

Physical Assistant Robot(Type B) 관련 시험 방법:
- 허리 인터페이스에서 힘/토크 측정 절차 (지정된 동작 수행 중)
- ROM 보호 하드웨어 스톱 검증 시험
- 비상정지 타이밍 시험
- 오작동 시 사용자 낙상 방지 안정성 시험

---

### 1.3 ISO 18646 시리즈

| 번호 | 제목 | 관련성 |
|------|------|--------|
| ISO 18646-1:2022 | 이동 로봇 로코모션 | **wearable 비해당** |
| ISO 18646-2:2019 | 내비게이션 | **wearable 비해당** |
| ISO 18646-3:2021 | 매니퓰레이션 로봇 팔 | **wearable 비해당** |
| ISO 18646-4:2023 | 모바일 매니퓰레이션 | **wearable 비해당** |

**결론**: ISO 18646은 자율 서비스 로봇용. 엑소슈트/웨어러블에는 **직접 적용 불가**.  
웨어러블 로봇의 정확한 표준 계통: **ISO 13482 → ISO/TR 23482-1**

---

### 1.4 ASTM F3474-21 — Exosuit Performance Test Methods

| 항목 | 내용 |
|------|------|
| 정식 명칭 | Standard Test Methods for Measuring the Performance of Wearable Assistive Devices |
| 발행 | 2021 (ASTM Committee F48) |
| 관할 | 미국 (ASTM International) |
| 한국 채택 | 미채택 (학계 참고용) |
| EU | EN ISO 13482 인증과 병행 참조 |

**F48 Committee 체계**:
- F3323:2019 — Terminology (용어 표준화)
- F3474:2021 — Performance test methods (현재 문서)
- F48.02 — Active devices
- F48.03 — Passive devices
- F48.04 — Soft wearable assistive devices **(SMA exosuit에 가장 근접, 개발 진행 중)**

**핵심 Performance Metrics**:

| 메트릭 | 측정 단위 | 프로토콜 |
|--------|---------|---------|
| 토크 보조 프로파일 | N·m | 부하 셀 @ 액추에이터 출력 |
| 대사 비용 감소 | % VO2 | 간접 열량계 (Douglas bag 또는 metabolic cart) |
| 근육 활성 감소 | %MVC (EMG) | SENIAM 전극 배치 |
| ROM 보존 | degrees | 관절각도계 또는 모션캡처 |
| 착/탈 시간 | minutes | 타이머 시험 |
| 사용자 편의성 | 0-10 VAS | 표준 설문 |
| 내구성 | hours | 연속 사용 시뮬레이션 |

**표준 시험 조건**:
- 보행: 1.2-1.5 m/s 평지
- 들기: NIOSH 일관 파라미터
- 계단: 표준 규격 계단

**산업 채택 현황 (미국)**:
- DARPA, DoD 조달 시 참조
- 근로자 보상 보험사 시험 프로토콜에서 점차 채택
- OSHA: 강제 아님, 자발적 준수

---

## 2. Lifting / Ergonomics 표준

### 2.1 NIOSH Revised Lifting Equation (RNLE) — 가장 중요

| 항목 | 내용 |
|------|------|
| 발행 | Waters et al. (1993, Ergonomics); Applications Manual (1994, DHHS Pub. 94-110) |
| 한국 채택 | KOSHA GUIDE H-9-2012 (적응 채택) |
| EU 동등 | EN 1005-2 (기계 안전 — 수동 취급) |
| 일본 동등 | JIS Z 8504 |
| OSHA 지위 | General Duty Clause 참조 (강제 아님) |

**공식**:
```
RWL = LC × HM × VM × DM × AM × FM × CM

LC  = 23 kg  (이상 조건 부하 상수)
HM  = 25/H  (수평 거리 보정, H = 손-신체 중심 수평 거리 cm)
VM  = 1 − (0.003|V−75|)  (수직 위치 보정, V = 손 높이 cm)
DM  = 0.82 + (4.5/D)  (이동 거리 보정, D = 수직 이동 거리 cm)
AM  = 1 − (0.0032 × A)  (비대칭 보정, A = 비대칭 각도 degrees)
FM  = 표 (분당 빈도 × 지속 시간)
CM  = 표 (양호/보통/불량 커플링)

LI (Lifting Index) = 실제 무게 / RWL
```

**LI 해석**:
- LI < 1.0: 허용 (저위험)
- 1.0 ≤ LI < 3.0: 주의 (일부 작업자 위험)
- LI ≥ 3.0: 고위험 (개선 필요)

**우리 박스 20 kg 시나리오 계산**:
```
박스 x=0.40 m, 박스 상면 높이 ≈ 15 cm, 허리 높이 ≈ 75 cm
H ≈ 40 cm, V ≈ 15 cm, D ≈ 60 cm, A = 0°, FM = 1.0, CM = Fair

HM = 25/40 = 0.625
VM = 1 − 0.003|15−75| = 1 − 0.18 = 0.820
DM = 0.82 + 4.5/60 = 0.895
AM = 1.0, FM = 1.0, CM = 0.95 (Fair)

RWL = 23 × 0.625 × 0.820 × 0.895 × 1.0 × 1.0 × 0.95 ≈ 10.0 kg
LI = 20 / 10.0 = 2.0  →  주의 구간
```

**65세 여성 조정**: 근력 약 30% 감소 → effective LI ≈ 2.6-2.9 → **고위험 범주 근접**

**통합 가치**: OpenSim Moco ES 감소 결과를 "LI 감소"로 변환하면 규제·산업 언어 사용 가능

**주요 한계**:
- 단일 대칭 들기만 적용 (비대칭/복합 작업 미지원)
- 연령/성별 population 보정 없음
- 정적 압축 추정 (척추 동역학 무시)
- L5/S1 압축 한계 기준: 3,400 N (NIOSH 1981)

---

### 2.2 EAWS (Ergonomic Assessment Worksheet System)

| 항목 | 내용 |
|------|------|
| 발행 | Schaub K, Caragnano G, Britzke B, Bruder R (2013). *Theoretical Issues in Ergonomics Science* 14(6):616-639 |
| 기원 | Volkswagen, Opel (ADAM OPEL AG) 자동차 산업 개발 |
| 채택 | VW, Mercedes-Benz, BMW, GM Europe, Fiat (~60% EU 자동차 OEM) |
| 소프트웨어 | eAWS (MTM-Institut, 상용) |
| 한국 | 공식 미채택, 학계/자발적 사용 |

**4 섹션 구조** (각 0-100점, 합계 0-400):
- **섹션 1**: 기본 자세 부하 (서기, 쪼그리기, 무릎 꿇기, 굽히기)
- **섹션 2**: 힘 작용 (밀기/당기기, 나르기, 파지력)
- **섹션 3**: 수동 물질 취급 (들기/내리기/나르기 — 무게×거리×빈도×커플링)
- **섹션 4**: 상지 부하 (반복 동작, 힘, 자세)

**리스크 구간**:
- 녹색 (0-25): 저위험
- 노랑 (25-50): 중위험, 모니터링
- 빨강 (50-100): 고위험, 인간공학적 개입 필수

**NIOSH 대비 차별점**:
- 하루 전체 누적 부하 평가 (NIOSH는 단일 동작)
- 다중 작업 지원
- 남성/여성 별도 기준값
- 연령 보정 계수: 40세 이상 점수 상승 (더 보수적)
- Section 3은 NIOSH 호환 + Snook & Ciriello 표 통합

---

### 2.3 REBA (Rapid Entire Body Assessment) — 요양/들기 작업에 가장 직접적

| 항목 | 내용 |
|------|------|
| 발행 | Hignett S, McAtamney L (2000). *Applied Ergonomics* 31(2):201-205 |
| 점수 범위 | 1-15 |
| 채택 | OSHA eTools, UK HSE, KOSHA 워크시트 포함 |

**REBA 해석**:
| 점수 | 위험 수준 | 조치 |
|------|---------|------|
| 1 | 무시 가능 | 필요 없음 |
| 2-3 | 저위험 | 조치 필요할 수 있음 |
| 4-7 | 중위험 | 조사 필요 |
| 8-10 | 고위험 | 즉시 조사 |
| 11-15 | 매우 고위험 | 즉시 개선 |

**카버리지**: 몸통, 목, 다리 + 팔, 손목 — 하체 포함으로 들기 작업 평가 적합

**요양보호사 박스 들기 REBA 추정**:
- 몸통 굽힘 >60°: 점수 +4
- 비틀림/측면 굽힘: +1
- 무릎 굽힘 <60°: 점수 +1
- 부하 >10 kg: +2
- 예상 기준선 REBA: **8-10 (고위험)**
- 목표: 엑소슈트로 7 이하 (중위험)로 감소

---

### 2.4 RULA (Rapid Upper Limb Assessment)

| 항목 | 내용 |
|------|------|
| 발행 | McAtamney L, Corlett EN (1993). *Applied Ergonomics* 24(2):91-99 |
| 점수 범위 | 1-7 |
| 한계 | 주로 상지 초점; 하요통 평가에 부적합 |

**들기 작업 적용 한계**: RULA는 상지 반복 작업에 특화 → 박스 들기 전체 평가에는 REBA가 우월

---

### 2.5 OWAS (Ovako Working Posture Analysis System)

| 항목 | 내용 |
|------|------|
| 발행 | Karhu O, Kansi P, Kuorinka I (1977). *Applied Ergonomics* 8(4):199-201 |
| 기원 | 핀란드 Ovako Steel (현 SSAB) |
| 방법 | 4자리 코드: 등, 팔, 다리, 부하 |
| 조치 | 1(정상)-4(즉시 수정) |
| 장점 | 빠른 관찰 코딩 |
| 단점 | 힘/시간 세부사항 부족, 조잡한 해상도 |

---

### 2.6 OCRA (Occupational Repetitive Actions)

들기 작업에 **비해당**: 상지 반복 동작(≥4회/분) 전용.  
EU 지침 2002/44/EC 기반. 요양보호사 반복 소물 취급 시 참조 가능.

---

### 2.7 KIM (Key Indicator Methods) — 독일 특화

| 방법 | 내용 |
|------|------|
| KIM-MHO | 들기/나르기/밀기/당기기 수동 취급 |
| KIM-ABP | 비틀린 자세, 측방 굽힘 |
| 기관 | BAuA (독일 연방 직업안전보건연구원) |
| 채택 | 독일 OHS 규정 (GDA) 공식 표준 |
| 한국 | 미채택 |

---

## 3. Performance Metrics 산업 표준

| 메트릭 | 단위 | 프로토콜 | 임계값/기준 | 표준 근거 |
|--------|------|---------|-----------|---------|
| 근육 활성 감소 | %MVC (EMG) | SENIAM 배치 표면 EMG | ≥10% = 임상적으로 의미 있음 | SENIAM, ASTM F3474 |
| Peak L5/S1 모멘트 감소 | N·m | 3D 모션캡처 + 힘판 | <220 N·m = 안전 경계 (McGill 2002) | NIOSH 1994, McGill 2002 |
| L5/S1 압축력 감소 | N | 근골격계 모델 (OpenSim) | <3,400 N NIOSH 조치 한계; <6,400 N 최대 | NIOSH 1981, Waters 1993 |
| 대사 비용 감소 | mL O2/kg/min | 간접 열량계 | >5% 감소 = 의미 있음 (절대 표준 없음) | ASTM F3474 |
| ROM 보존 | degrees | 관절각도계 또는 모션캡처 | 어느 관절에서도 <5° 제한 = 허용 | ASTM F3474, ISO 13482 |
| LI (Lifting Index) | unitless | NIOSH 방정식 | 목표: LI < 1.0 (현재 2.0 기준선에서) | NIOSH 1994 |
| REBA 점수 | 1-15 | 관찰 기반 비디오 분석 | ≥1 위험 범주 감소 (예: 고위험→중위험) | Hignett 2000 |
| 피크 토크 보조 | N·m | 액추에이터 출력 부하 셀 | 장치 특화 (우리 SMA: 24 N·m 설계) | ASTM F3474 |
| 사용자 편의성 | 0-10 VAS | 표준 설문 | ≥6/10 (산업 조달 임계값) | ASTM F3474 |
| 착/탈 시간 | minutes | 타이머 시험 | ≤5분 단독 (DARPA 기준); ≤3분 1인 보조 | ASTM F3474 |
| 내구성 | hours | 연속 사용 시뮬레이션 | ≥8시간 교대 (산업); ≥4시간 (의료) | ASTM F3474 |

**식별된 갭**:
- 연령별/성별별 performance 임계값 산업 표준 없음
- SMA fabric 소프트 엑소슈트 전용 표준 없음 → 가장 근접: ASTM F48.04 (개발 중)
- 시뮬레이션 기반(OpenSim) performance 주장에 대한 표준 없음 → 학계 출판만 가능

---

## 4. 우리 Framework 통합 가능성

| 표준 | 즉시 통합? | 추가 시간 | 추가 비용 | 추가 가치 | 통합 방법 |
|------|-----------|---------|---------|---------|---------|
| **NIOSH RWL/LI** | **YES** | 1-2일 | 없음 (계산) | 규제 언어 제공 | OpenSim 결과에서 LI 감소 계산 가능 |
| **REBA 점수** | **YES** | 2-3일 | 비디오만 | 직관적 소통 | 박스 motion 비디오에서 REBA 평가 |
| OWAS | YES | 1일 | 없음 | 제한적 | 박스 motion 비디오로 코딩 |
| KOSHA H-9-2012 | YES | 1-2일 | 없음 | 한국 규제 소통 | LI 계산 + 한국어 보고 |
| ASTM F3474 | PARTIAL | 3-6개월 | EMG/VO2 장비 | 미국 시장 진출 | EMG 파일럿 실험 필요 |
| EAWS | NO | 3-4주 | 소프트웨어 | EU 자동차 시장 | 전체 workday 모델링 필요 |
| KS B ISO 13482 | NO* | 6-12개월 | 인증 비용 | 한국 상업화 필수 | 하드웨어 안전 시험 |
| EN ISO 13482 | NO* | 6-12개월 | CE 인증 비용 | 유럽 시장 진출 | 하드웨어+소프트웨어 안전 시험 |

*인증 자체는 장기 과제; 설계 단계에서 준거 프레임으로는 즉시 활용 가능

---

## 5. 산업 채택 현황

### 5.1 지역별 비교

| 표준 | 한국 | 미국 | EU (유럽) | 일본 |
|------|------|------|---------|------|
| ISO 13482 (안전) | KS B ISO 13482:2016 (공식 채택) | 자발적 | EN ISO 13482, CE marking 근거 | JIS B 8445 동등 |
| ASTM F3474 (성능) | 미채택 (학계 참조) | DARPA/DoD 참조, 자발적 | EN ISO 13482와 병행 참조 | 미채택 |
| NIOSH 방정식 (들기) | KOSHA H-9-2012 (적응 채택) | OSHA 참조, 자발적 | EN 1005-2 (동등) | JIS Z 8504 동등 |
| EAWS (인간공학) | 학계/자발적 | Ford, GM 사용 | BMW, VW, Fiat (자동차) | Toyota 동등 |
| REBA | KOSHA 워크시트 포함 | OSHA eTools | UK HSE 가이던스 | 광범위 사용 |
| KIM 방법 | 미채택 | 미채택 | BAuA (독일) 공식 표준 | 미채택 |

### 5.2 KIMM 적용 시나리오

```
현재 단계 (시뮬레이션 phase):
  NIOSH LI 계산 → 박스 20 kg, H=40 cm → LI 2.0 (기준선)
  OpenSim Moco 24 N·m 보조 → ES 28% 감소
  LI 감소 = 직접 계산 불가 (LI는 무게/거리 기반, 근육활성 기반 아님)
  대안: L5/S1 압축력 감소를 NIOSH 3,400 N 한계 대비 제시

산업화 단계 (하드웨어 완성 후):
  KS B ISO 13482 인증 → 한국 시장 출시
  ASTM F3474 파일럿 → EMG 실험으로 시뮬레이션 검증
  KOSHA 기술지침 기여 → 요양보호사 지침 업데이트
```

---

## 6. 권장 표준 조합

### 즉시 채택 (Phase 2 박스 motion 결과에 통합 — 이번 논문)

**조합 A: 학계-산업 브릿지 최소 세트**

1. **NIOSH LI 보고**: 박스 20 kg, H=40 cm → LI 2.0 (기준선) 명시  
   → OpenSim L5/S1 압축력을 NIOSH 3,400 N 한계 대비 % 감소로 표현  
   → "wearable suit가 NIOSH 조치 한계 대비 하중을 X% 감소" 형태

2. **REBA 점수**: 박스 motion 비디오(Stage 5)에서 REBA 계산  
   → 착용 전 REBA 추정 8-10(고위험) → 착용 후 목표 ≤7(중위험)  
   → 직관적이고 현장 적용성 높은 지표

3. **L5/S1 < 3,400 N**: Moco 결과를 NIOSH 절대 한계 대비 제시  
   → 학계(N·m, %) + 산업(절대값 N) 언어 동시 사용

### 미래 채택 (1-2년 후, 하드웨어 완성 후)

4. **KS B ISO 13482 인증**: 하드웨어 안전 시험  
5. **ASTM F3474 EMG 파일럿**: 시뮬레이션 결과 실험적 검증  
6. **EAWS 직무 평가**: EU 시장 진출 또는 한국 대형 제조업체 대상 시

---

## 7. 학계 vs 산업 갭

| 차원 | 학계 (현재 framework) | 산업 (standards) | 브릿지 방법 |
|------|---------------------|-----------------|-----------|
| 결과 단위 | ES activation %, L5/S1 N·m | LI, REBA 점수, N (압축력) | 단위 변환 + 병기 |
| 효과 근거 | 통계적 유의성 (p-value, R²) | 규제 임계값 초과 여부 | 두 가지 모두 보고 |
| 대상 작업 | 단일 들기 동작 (5초) | 전체 작업 교대 누적 부하 | CLI 또는 EAWS 추정 |
| 인구 | 일반화 (모델 평균) | 성별/연령별 별도 기준 | 여성 65세 조정 데이터 포함 |
| 검증 방법 | 시뮬레이션 (OpenSim) | 실험 (EMG, VO2, force plate) | "시뮬레이션 → 실험 로드맵" 제시 |
| 인증 | 해당 없음 | KS B ISO 13482 / CE marking | "이 연구는 인증 사전 근거 제공" 명시 |

---

## 8. 인용

### 표준 문서
1. ISO 13482:2014. *Safety requirements for personal care robots*. Geneva: ISO.
2. ISO/TR 23482-1:2020. *Robotics — Application of ISO 13482 — Part 1: Safety-related test methods*. Geneva: ISO.
3. ASTM F3474-21. *Standard Test Methods for Measuring the Performance of Wearable Assistive Devices*. West Conshohocken: ASTM International.
4. ASTM F3323-19. *Standard Terminology for Exoskeletons and Exosuits*. ASTM International.
5. KOSHA GUIDE H-9-2012. *인력 운반 작업에 관한 기술지침*. 한국산업안전보건공단.
6. KS B ISO 13482:2016. *개인용 케어 로봇의 안전요건*. 국가기술표준원.

### 학술 논문
7. Waters TR, Putz-Anderson V, Garg A, Fine LJ (1993). Revised NIOSH equation for the design and evaluation of manual lifting tasks. *Ergonomics* 36(7):749-776.
8. Waters TR, Putz-Anderson V, Garg A (1994). *Applications Manual for the Revised NIOSH Lifting Equation*. DHHS (NIOSH) Publication No. 94-110. Cincinnati, OH.
9. Schaub K, Caragnano G, Britzke B, Bruder R (2013). The European Assembly Worksheet. *Theoretical Issues in Ergonomics Science* 14(6):616-639.
10. Hignett S, McAtamney L (2000). Rapid Entire Body Assessment (REBA). *Applied Ergonomics* 31(2):201-205.
11. McAtamney L, Corlett EN (1993). RULA: a survey method for the investigation of work-related upper limb disorders. *Applied Ergonomics* 24(2):91-99.
12. Karhu O, Kansi P, Kuorinka I (1977). Correcting working postures in industry. *Applied Ergonomics* 8(4):199-201.
13. McGill SM (2002). *Low Back Disorders: Evidence-Based Prevention and Rehabilitation*. Human Kinetics.

---

_작성: biomechanics-agent (2026-04-29)_  
_근거: ISO/ASTM/NIOSH/KOSHA 공식 표준 문서 + 학술 문헌 종합_  
_용도: Phase 2 박스 motion 결과 산업 표준 해석 + KIMM 상업화 인증 로드맵_
