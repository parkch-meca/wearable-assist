# CONTINUATION GUIDE — Moco 전환 단계

_Last updated: 2026-04-23 (end of session)_  
_Next session: 2026-04-24_  
_Project: wearable-assist / opensim_analysis / thoracolumbar_fb_

---

## 0. 이 문서의 용도

내일(2026-04-24) 새 Claude 채팅 세션을 시작할 때, 이 문서를 **맨 처음에 업로드**해서 전체 맥락을 복원.

이 문서 + userMemories (13-18번 신규) + /data/wearable-assist/opensim_analysis/thoracolumbar_fb/ 의 최신 커밋(b9b8aec 이후)이 모든 맥락입니다.

---

## 1. 어제(2026-04-23) 세션 요약

### 1.1 원래 목표
- 20kg 박스 들기 비교 영상 완성 (stoop_box_comparison.mp4)

### 1.2 실제 진행 경과

**박스 영상 trouble-shooting → Reserve 민감도 발견 → Moco 전환 결정**의 연쇄:

1. v4 preview에서 "t=0 박스 13cm 부양" 발견
2. 조사 중 "발 15cm 땅속 매몰" 추가 발견 (motion에 ground contact constraint 없음)
3. **"20kg인데 ES 22%는 너무 낮다"** 사용자 지적으로 수치 검증 착수
4. Reserve actuator 413Nm이 척추 근육 대신 일하고 있음 발견 (근본 원인)
5. Reserve 민감도 스윕 실시 (R100→R50→R10→R5→R1)
6. **결론: 절대값은 민감, 상대값(suit 효과)은 robust** → 논문 메시지 유지 가능
7. 박스 영상은 임시본(v2)으로 마무리, Moco로 근본 해결 결정

### 1.3 최종 산출물 (Commit b9b8aec)

GitHub: https://github.com/parkch-meca/wearable-assist/commit/b9b8aec

| 파일 | 내용 |
|---|---|
| `docs/reserve_sensitivity.md` | R100/50/10/5/1 스윕 상세 |
| `docs/suit_sweep_reserve_comparison.md` | §1.6 slope R100 vs R50 비교 |
| `docs/moco_env_check.md` | Moco 환경 점검 체크리스트 |
| `KNOWN_LIMITATIONS.md` | 박스 영상 3가지 제약 + Moco 해결 계획 |
| `scripts/run_reserve_sweep*.py` | 재현 스크립트 |
| `scripts/render_box_comparison.py` (M) | ES peak metric으로 display 변경 |
| `docs/images/box_lift_preview_v6.png` | 최종 프리뷰 |
| `/data/opensim_results/video/stoop_box_comparison_v2.mp4` | 임시본 영상 (1.27MB, 3.03s) |

### 1.4 핵심 수치 (기억할 것)

```
Reserve 민감도 (B_suit0 @ t=2.33s, 20kg 박스):

Reserve 설정    ES peak    ES mean    Reserve 사용    SO 수렴
R100 (현재)     66.7%      18.6%      413 Nm         ✅
R50             86.8%      25.3%      209 Nm         ✅
R10             100% sat   38.7%      22 Nm          ✅ (2 근육 saturation)
R5              100% sat   41.6%      6.8 Nm         ✅ (4 근육 saturation)
R1              100% sat   43.8%      0.4 Nm         ✅ (4 근육 saturation)

Suit 상대 감소율 (B_suit0 → B_suit200, R100 vs R50):
R100: Δ peak = −10.34%, Δ mean = −10.42%
R50:  Δ peak = −10.60%, Δ mean = −10.95%
차이: 0.27%p (robust)

Suit sweep slope (§1.6):
R100 재측정:   1.120 %/Nm (기존 1.206 값과 가까움)
R50:           0.889 %/Nm (약간 낮음)
R² = 1.0000 양쪽 모두 유지
```

---

## 2. 내일 시작점

### 2.1 목표 (우선순위 순)

**목표 1**: OpenSim Moco 파이프라인 확립
- Step 1: `prepare_model_for_moco.py` 작성 (locked coord → WeldJoint)
- Step 2: Moco smoke test (예제 1개 실행, 익숙해지기)
- Step 3: MocoTrack으로 제자리 stoop v5 실행 (첫 Moco 시뮬레이션)
- Step 4: 결과 검증 (기존 SO 결과와 비교)

**목표 2**: 안정화 후 20kg 박스 들기 MocoTrack 실행
- Ground contact constraint 반영
- Box interaction constraint 반영
- 기대: 박스-손-발 정합이 자동 해결됨

**목표 3**: 논문 수치 업데이트
- Moco 결과로 §1.6 재계산
- Fig 7/8 재생성
- Absolute baseline 값 업데이트 (ES peak 기준)

### 2.2 결정된 설계 원칙 (변경 금지)

1. **Moco 타입**: MocoTrack 먼저 + MocoInverse 병행 검증 (MocoStudy는 과욕)
2. **초기 동작**: 제자리 stoop v5 → 20kg 박스 순차 (팔 들기/계단은 확장 단계)
3. **Reserve**: 포함 with high penalty로 시작, 단계적 감소 (목표 <10%)
4. **Locked coord**: 보수적 weld (stoop 무관 coord만)
5. **지표**: ES peak 우선, ES mean 보조 (metric 정의 확정)

### 2.3 환경 전제

- Dell Precision 7960, Xeon w7-3465X (28코어), 128GB RAM
- OpenSim 4.5.2 (conda env `opensim`, Python 3.11)
- Moco 모듈 별도 설치 불필요 (확인됨)
- CasADi 내장 OK
- 작업 경로: `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/`

---

## 3. Claude Code용 첫 프롬프트 (내일 시작 시)

```
목표: Moco 전환 Step 1-2. 
(Step 1) prepare_model_for_moco.py 작성 및 실행.
(Step 2) Moco smoke test (간단 예제 1개).

=== Step 1: Model preprocessing ===

목적: ThoracolumbarFB의 locked coordinate를 WeldJoint로 변환.
CasADiSolver는 locked coord를 처리 못하므로 필수.

[1.1] Locked coord 전체 목록 추출
   - MaleFullBodyModel_v2.0_OS4_modified.osim 로드
   - locked=True인 모든 coord를 출력
   - 각 coord가 속한 joint와 default value 기록
   - 출력 파일: docs/locked_coords_inventory.md

[1.2] Weld 대상 분류 (보수적 원칙)
   - Stoop/lift 관련 coord는 유지:
     * 모든 lumbar FE (L1-L5, T10-T12 flexion-extension)
     * hip flexion, knee flexion, ankle dorsiflexion
     * shoulder/elbow (박스 들기용)
   - Weld 가능 후보:
     * Vertebra axial rotation (비 sagittal plane)
     * Vertebra lateral bending (비 sagittal plane)  
     * Finger/toe joints
     * 기타 stoop 무관 coord
   - 각 결정에 근거 명시 (테이블로)
   - 사용자 승인 대기

[1.3] prepare_model_for_moco.py 작성
   - 입력: MaleFullBodyModel_v2.0_OS4_modified.osim
   - 작업: [1.2] 승인된 coord를 WeldJoint로 변환
   - 출력: MaleFullBodyModel_v2.0_OS4_moco.osim (신규)
   - 검증: 원본 default pose의 body positions와 변환 모델의 default 
     pose body positions 비교 (오차 <1mm 기대)

[1.4] 모델 검증
   - 변환 모델을 opensim.Model()로 로드
   - initSystem() 성공 확인
   - opensim.MocoStudy() + problem.setModelAsCopy() 성공 확인
   - 근육 수 = 620 (변화 없어야 함)
   - Free coord 수 = 원본 free coord 수와 같아야 함

=== Step 2: Moco smoke test ===

목적: Moco solver가 실제로 수렴하는지 확인. 
ThoracolumbarFB가 아닌 가벼운 예제로.

[2.1] OpenSim 내장 예제 중 가벼운 것 선택
   find / -path "*/Moco/example*" -name "*.py" 2>/dev/null | head -20
   
   후보 (빠른 것부터):
   - exampleMocoInverse (가장 단순)
   - exampleSitToStand
   
   실행하여 수렴 확인. 시간 기록.

[2.2] 예제 실행 결과 정리
   - 실행 시간
   - solver iterations
   - objective value 수렴 여부
   - 산출 파일 (motion, controls)

이 두 예제가 돌면 Moco 기본 환경 OK 확정.

=== 보고 ===

각 step 완료 후 보고:
- 산출 파일 경로
- 핵심 수치
- 장애물/경고 사항
- 다음 step 진행 가능 여부

Git commit + push 각 step 완료 시:
Step 1: "moco: Prepare ThoracolumbarFB model for Moco (weld locked coords)"
Step 2: "moco: Smoke test examples passed, environment confirmed"

=== 원칙 ===

- Step 1.2 승인 대기 필수 (weld 범위 결정은 사용자가)
- Step 1.4 검증에서 오차 있으면 중단, 원인 조사
- Step 2에서 수렴 실패하면 Moco 설치/환경 문제 가능성, 즉시 보고
- 대원칙: "시간 걸려도 제대로 된 모델" — 빠른 우회보다 정확성
```

---

## 4. 다음 세션 Claude 채팅에게 전달할 맥락

새 세션 시작 시 **첫 메시지**로 이 문서 업로드 + 다음 설명:

> "어제 작업 이어가자. 이 가이드 문서 먼저 읽어줘. 
> 목표는 OpenSim Moco 파이프라인 확립. 
> 프롬프트는 §3에 준비됨. 
> 검토하고 Claude Code에 전달할 최종 버전 만들어줘."

## 5. 만약 내가 다른 것 먼저 하고 싶다면

선택지:

**A. Moco 집중** (권장) → §3 프롬프트 그대로 진행
**B. 논문 초안 수정 먼저** → Moco 전에 R50 재계산으로 §1.6 업데이트 (1-2일)
  - 단점: Moco 결과 나오면 또 수정 가능성
**C. 박스 영상 재시도** → 비권장 (이미 확정된 임시본)
**D. 다른 프로젝트** (KINESIS, GR00T 등) → Moco 보류

A가 가장 일관적.

---

## 6. 장애물 및 리스크

### 이미 파악된 것
- Locked coordinate (~40-60개) → Step 1에서 해결
- Motion이 박스 들기 최적화가 아님 → MocoTrack으로 근본 해결

### 아직 모르는 것
- Moco가 620 근육 모델 수렴할지 (시간 걸릴 가능성 — 예제는 단순 모델)
- GRF/external load (박스) constraint 설정 방법
- MocoTrack의 kinematic reference weight 튜닝

### 마음의 준비
- Moco 첫 실행은 하루 이상 걸릴 수 있음 (밤샘 실행)
- 수렴 실패 시 문제 분해해야 함 (모델 복잡도 줄이기부터)
- Step 1(1시간) + Step 2(30분) + 예제 익히기(반나절) + 제자리 stoop(1-2일) = 첫 주 목표

---

## 7. 참고 링크 및 파일

### Git
- Repo: https://github.com/parkch-meca/wearable-assist
- 최신 commit: b9b8aec (2026-04-23 09:02 UTC)
- 파일 시스템: `/data/wearable-assist/opensim_analysis/thoracolumbar_fb/`

### 어제 생성된 핵심 문서
- `docs/reserve_sensitivity.md` — reserve 민감도 분석
- `docs/suit_sweep_reserve_comparison.md` — slope 재확인  
- `docs/moco_env_check.md` — Moco 환경 점검
- `KNOWN_LIMITATIONS.md` — 박스 영상 제약

### 문헌 참고 (어제 사전 조사)
- Frontiers 2026 (active exoskeleton, 15kg lift, ES 10-27% MVC): https://www.frontiersin.org/articles/10.3389/fbioe.2026.1631785
- PLAD (Sadler et al., 2006, 5/15/25kg, ES EMG 감소 14.4-27.6%): https://pubmed.ncbi.nlm.nih.gov/16494978/
- 이외 어제 web_search 결과 기록됨

---

## 8. Claude 채팅에게 개인적으로 (내일의 나에게)

- 사용자는 "대원칙: 범용 확장 가능한 파이프라인"을 중시
- "완벽"보다 "정직한 수치" 우선
- 이미지 검증 프로토콜 엄수 (userMemories #18)
- Claude Code에 task router 역할 강요 금지 (userMemories #2)
- 사용자가 직접 코드 실행하지 않음 — 내가 Claude Code에게 프롬프트 만들어 전달하는 구조
