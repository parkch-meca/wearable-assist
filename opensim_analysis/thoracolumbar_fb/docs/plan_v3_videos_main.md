# Plan v3 — 동영상 중심 (Variant A 단독)

**작성일**: 2026-05-28
**상태**: 사용자 승인 대기
**선행 결정**: Plan v2 + 사용자 방향 재정립 (2026-05-27)
**핵심 전환**: 동영상 = 메인 deliverable, 정량 결과 = 백업, paper = 후순위

---

## §0. 목표 재정립 (확정)

### 0.1 진짜 deliverable
1. **메인**: 동영상 순차 (Squat → Stoop → 박스 → 걷기 → 들고 나르기)
2. **백업**: Squat Moco 정량 (ES %, dose-response) — KIMM 산업체/정부 보고용
3. **후순위**: paper draft (정량 데이터 확보 후 작성)

### 0.2 "Phase 1a Stoop 미완료" 정의 (사용자 확정)
- numeric은 완료 (ES 28%, Hu 2026 일치)
- **미완료 = 자연스러운 동영상 부재** (손 분리 2회 발생)
- "보여줄 영상이 없는 상태"

### 0.3 핵심 검증 도전
**손 분리 발생 여부** — 시각화 paradigm 유지 가능 여부 결정
- 정적 snapshot에서 분리 → 즉시 Blender paradigm 전환
- 정적 OK + 동영상에서 분리 → 동영상 도구 자체 문제 → Blender
- 둘 다 OK → 동영상 path 진행

---

## §1. 결정 사항 (사용자 확정 2026-05-27/28)

| # | 결정 | 내용 |
|---|------|------|
| 1 | Phase 1a Stoop 미완료 | 시각화/동영상 (손 분리), numeric은 완료 |
| 2 | Variant | A 단독 (B/C 폐기, Akhavanfar = future work for deep stoop) |
| 3 | Paper | 후순위 (정량은 산출, draft만 보류) |
| 4 | 박스 영상 | 기존 v11b motion 렌더만 (새 motion 시도 X, closure 존중) |
| 5 | Blender | 선제 학습 (Squat 동영상과 병렬) |
| 6 | Snapshot protocol | 정적 Stage 4 grid 먼저 → PASS 시 동영상 |

---

## §2. 사전 진단 (Day 0 — Plan v3 시작 전, 즉시 가능)

### 2.1 박스 v11b 기존 자료로 정적↔동영상 손 분리 위치 진단

**확인된 자료**:
- 정적: `/data/wearable-assist/.../docs/images/phase2_box/box_motion_v11_stage4_grid.png` ✅
- 정적: `/data/wearable-assist/.../docs/images/phase2_box/box_motion_v11b_stage4_grid.png` ✅
- 동영상: `/data/opensim_results/video/box_v11b_main.mp4` ✅
- 동영상: `/data/opensim_results/video/box_v11b_suit_comparison.mp4` ✅

**Day 0 작업 (1-2시간, viz-agent 호출)**:
1. 두 PNG + 두 MP4를 viz-agent가 자가 검증 (손 분리 여부, mesh 연결)
2. 결과 분류:
   - (a) PNG OK + MP4 OK → 박스에서는 손 분리 없음 → Squat에서도 도구 자체는 문제 없을 가능성
   - (b) PNG OK + MP4 손 분리 → **동영상 도구 자체 문제 확정** → Blender 즉시 시작
   - (c) PNG 손 분리 + MP4 손 분리 → 모델 자체 또는 OpenSim 렌더 자체 문제 → Blender 즉시 시작
   - (d) PNG 손 분리 + MP4 OK → 비정상 (drilling needed)
3. 사용자 시각 검증 (PNG + MP4 직접 확인)

**Day 0 결과로 Plan v3 path 분기**:
- (a) → Plan v3 §3 그대로 진행 (정적 → 동영상 path)
- (b)(c) → Plan v3 우회: Blender path로 즉시 전환, Squat 정적 검증 후 Blender 동영상
- (d) → 추가 진단 후 사용자 협의

⚠️ **Day 0 작업 1-2시간 = Plan v3 전체 path 결정** — 가장 효율적 진입점

---

## §3. Phase 2 (Week 1-2, 동영상 중심)

### Week 1: Squat 정량 + 정적 검증
| Day | 작업 | 산출 | 검증 |
|---|---|---|---|
| 1 | Squat ROM/baseline 재확인 + Squat motion 생성 (biomechanics-agent + opensim-agent) | `squat_motion_v1.mot` | Stage 1 IK self-check |
| 2-3 | Squat Moco 4 conditions (0/8/16/24 N·m, moco-analysis-agent) | `solution.sto` × 4 | Solve_Succeeded, ES extraction |
| 4 | Squat Stage 4 grid (viz-agent, 정적 1장, **손 분리 검증 ⭐**) + Blender 사전 학습 시작 (literature-agent 병렬) | `squat_v1_stage4_grid.png`, `docs/blender_paradigm_learning.md` | viz-agent 자가 검증 (Visual criteria 5개) |
| 5 | **⭐ 사용자 정적 시각 검증** | — | PASS → Week 2 동영상 / FAIL → Blender 전환 |

### Week 2: Squat 동영상 + Stoop 재검토 시작
| Day | 작업 | 산출 | 검증 |
|---|---|---|---|
| 6-8 | Squat 동영상 (Suit ON vs OFF, viz-agent) | `squat_suit_comparison.mp4`, `squat_grid.png` (5+ frames) | viz-agent 자가 검증 |
| 9 | **⭐ 사용자 동영상 시각 검증** | — | PASS → Day 10 / FAIL → Blender 전환 |
| 10 | Stoop 동영상 재검토 시작 (Phase 1a 미완료 부분 = 손 분리) | `stoop_v6_motion.mot` 또는 기존 재렌더 | Stage 4 grid PASS |

### Patch trigger 활성 (validation_protocol_v2 §4)
- Squat motion 3번 재설계 → STOP
- Squat 동영상 렌더 3번 fail → STOP  
- Blender 학습 14일 초과 → STOP

---

## §4. Phase 3 (Week 3-4, Stoop + 박스 영상 마무리)

| Week | 작업 | 산출 |
|---|---|---|
| 3 | Stoop 동영상 진짜 완료 (Suit ON vs OFF, Phase 1a 시각 결과) | `stoop_phase1a_suit_comparison.mp4` |
| 4 | 박스 v11b 영상 렌더만 (기존 motion, closure 존중) | `box_v11b_final.mp4` (기존 자료 정리/재렌더) |

⚠️ Phase 3 = Stoop 진짜 완료 + 박스 closure 정리. **새 박스 motion 시도 절대 X**.

---

## §5. Phase 4 (1-2개월, 걷기 — 별도 plan)

- **별도 plan v4 작성 필요** (Hunt-Crossley contact, GRF, 발 trajectory 새 paradigm)
- Phase 2-3 완료 후 사용자 결정
- 본 plan v3 범위 외

---

## §6. Validation (validation_protocol_v2.md 보강)

### 6.1 Visual criteria 우선 (사용자 강조)
기존 5개 + 추가:
- ☐ 모든 body 부위 visible
- ☐ Mesh 연결 자연 (**손 분리 X — 최우선**)
- ☐ 자세 자연
- ☐ 근육 path 합리
- ☐ 일반인 이해 가능
- ☐ **(추가)** 동영상에서 frame-to-frame 부드러움 (jitter 없음)
- ☐ **(추가)** Suit ON vs OFF 시각 구분 가능

### 6.2 Numeric criteria (백업)
- Phase 1a regression ΔES < 5 %p

> ⛔ **정정 (2026-07-30)**: 이 절의 Hasenmaier 2026 "10–17 %" / "10–27 %"는 **%MVC 절대 포인트**이지 상대 감소율이 아니다. stoop 상대 감소율은 69.8→42.4 %MVC = **−39.3 %**, squat은 원문이 수준 간 유의차를 보고하지 않아 **대조 불가**. 상세는 `hu2026_squat_validation_input.md` R1 정정 박스 및 `five_motion_paper_draft.md` §4 참조.
- Squat ES reduction 10-28% (Hasenmaier 2026 + Hu 2026 범위)
- Solve_Succeeded < 300s
- 기타 validation_protocol_v2 §3.1 유지

### 6.3 Blender 전환 trigger (신규)
- 정적 손 분리 발견 → **즉시 Blender 전환** (동영상 시도 X)
- 동영상 손 분리 발견 → **즉시 Blender 전환**
- 박스 v11 정적 OK + 동영상 손 분리 (Day 0 결과 b) → **즉시 Blender** (Squat 동영상 시도 X)

---

## §7. Backup Path 활성화 — Blender + OpenSim 분리

### 7.1 사전 학습 (Day 4부터 병렬, literature-agent + general-purpose)
산출: `docs/blender_paradigm_learning.md`
- Blender + OpenSim 통합 사례 (논문/튜토리얼)
- OpenSim motion (.mot) → Blender 애니메이션 변환
- 근육 시각화 (OpenSim 근육 line → Blender)
- 작업 시간 추정 (Squat 동영상 1개 Blender로 만드는 데 N일?)
- 우리 모델 (TLFB+forearm_v1) Blender 호환성

### 7.2 전환 결정
- Day 5 사용자 정적 검증 FAIL → 즉시 Blender 전환
- Day 9 사용자 동영상 검증 FAIL → 즉시 Blender 전환
- Day 0 박스 진단 결과 (b) or (c) → Plan v3 시작과 동시 Blender 전환

### 7.3 Blender path Phase 2 (전환 시)
- Week 1: Blender 환경 + OpenSim motion 변환 학습
- Week 2: Squat Blender 동영상 1차 시도
- Week 3-4: Stoop + 박스 영상 Blender 변환
- Phase 4 (걷기)도 Blender 전제

---

## §8. 일정 요약

| Phase | 기간 | 주요 산출 | End 검증 |
|---|---|---|---|
| **Day 0** | 1-2시간 | 박스 v11b 정적↔동영상 손 분리 진단 | ⭐ 사용자 (Plan v3 path 결정) |
| **Phase 2 Week 1** | 5일 | Squat ROM + Moco + 정적 grid + Blender 학습 시작 | ⭐ 사용자 정적 시각 |
| **Phase 2 Week 2** | 5일 | Squat 동영상 + Stoop 재검토 시작 | ⭐ 사용자 동영상 시각 |
| **Phase 3** | 2주 | Stoop 동영상 완료 + 박스 v11b 렌더 | ⭐ 사용자 |
| **Phase 4** | 1-2개월 | 걷기 (별도 plan v4) | — |

**총 4-6주** (Phase 4 제외) — Plan v2와 동일하나 deliverable 동영상 중심

---

## §9. Open Issue (Day 0 시작 전 답)

1. **Day 0 viz-agent 호출 동의?** (1-2시간, 박스 v11b 진단)
2. **Squat motion 새로 설계 vs 기존 자료 활용?** — biomechanics-agent에 Squat 새 reference 부탁 필요
3. **Blender 학습 시점**: Day 4부터 (정적 검증 후) vs Day 1부터 (선제, 더 안전)
4. **Stoop 재검토 범위**: Phase 1a stoop_synthetic_v5 motion 그대로 재렌더 vs motion v6 새로 (손 자세 보정)?
5. **paper 후순위 = Squat Moco 결과 산출만 → paper draft는 언제?** (Phase 3 후? Phase 4 후?)

---

## §10. Plan v2 → v3 변경 점 요약

| 항목 | Plan v2 | Plan v3 |
|---|---|---|
| Deliverable | paper § (Squat lift) | **동영상 (Squat → Stoop → 박스 → 걷기 → 나르기)** |
| Variant | A + B + C 병렬 | **A 단독** (B/C future) |
| Phase 2 핵심 | Variant 비교 | **동영상 시각 검증** |
| Validation | Numeric 중심 | **Visual 우선 + Numeric 백업** |
| Backup | 보류 | **Blender 선제 학습 + 즉시 전환 가능** |
| 기간 | 4-6주 | 4-6주 (동일) |
| Stoop | "완료" 가정 | **미완료 인정, 재검토** |

---

## §11. 승인 후 첫 행동 (Day 0)

사용자 승인 즉시:
1. viz-agent 호출 → 박스 v11b 정적 PNG 2장 + 동영상 MP4 2개 자가 검증
2. 결과를 사용자에게 보고 (raw URL + 자가 검증 체크리스트)
3. 사용자 시각 검증 → Plan v3 path 분기 결정

⚠️ **Plan v3 승인 후 Day 0 시작**. Day 0 결과에 따라 (a) 정적→동영상 path 또는 (b)(c) Blender path 분기.

⚠️ **자동 진행 X — Plan v3 검토 후 승인 → Day 0 → 사용자 진단 결과 검토 → Phase 2 Week 1 시작**
