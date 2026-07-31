# Claude Code Instructions for `wearable-assist`

## Project Context

SMA fabric muscle 기반 wearable suit가 들기 작업 중 척추기립근(erector spinae) 부하에 미치는 영향을 정량화.
주 모델: ThoracolumbarFB v2.0 (OpenSim 4.x, 620 근육 전신).

### 동작 용어 (terminology)

- **stoop lift** — 제자리 허리 굽힘 (무릎 거의 고정, 허리만 굽힘). v5 모션(`stoop_synthetic_v5.mot`)이 여기에 해당.
- **semi-squat lift** 또는 **stoop-squat hybrid** — 박스 들기처럼 무릎·고관절·허리가 함께 굽는 실제 들기 자세. `stoop_box20kg_v2.mot` (박스 v2)가 여기에 해당.
- `§1.6`의 "stoop lift 28–29 % 감소" 수치는 v5 제자리 stoop에만 적용; 박스 v2 수치는 별도 리포트.
- **박스 motion v3-v7** — semi-squat lift 카테고리. 양 측면 잡기 + Coupler 제거 모델 사용.


## Directory Conventions

- `opensim_analysis/thoracolumbar_fb/` — 메인 분석 (현재 진행)
- `opensim_analysis/rajagopal_legacy/` — 이관 전 Rajagopal 기반 분석 (보존)
- 대용량 산출물 (`.mot`, `.sto`, `.mp4`, `.osim`, `.pkl`, `.npy`)은 `/data/` 하위 (repo 외부). `.gitignore` 참조.
- 결과 이미지(`.png`)는 원칙적으로 제외; 단 `opensim_analysis/*/docs/images/` 및 `docs/figures/` 하위는 포함 허용.

### 리포지토리 추적 기준 (2026-07-31 표준)

새 산출물을 만들 때 아래 기준을 적용한다. 상세는 `docs/five_motion_completion_record.md` §9.

| 추적 | 제외 |
|---|---|
| grid·합성본 PNG (`*_grid.png`, `*_verify_*`, `*_report`) | 개별 프레임 (`*_t[0-9]*`, `*_f[0-9]*`, `wt_front_*`, `fix[0-9]*`) |
| 논문 figure (`docs/images/paper_*/fig*.png`) | 시도별 진단 plot (`*_stage[0-9]_traj|joints|hand_box.png`) |
| 분석 plot (`*_angles.png`, `*_analysis_*.png`) | 렌더 중간 프레임 (`w2_*`, `fk_*`, `boxvid_*`) |
| 문서·스크립트·소형 설정 | 대용량 저작 파일 (`*.blend`), 백업 (`*.bak*`, `*.backup_*`) |

- **원칙**: 개별 프레임은 grid에 합성되어 추적되므로 중복이다. grid만 남긴다.
- **대용량 자산**은 리포지토리 밖 `/data/wearable-assist-assets/<종류>/` 에 두고 README로 용도·재생성 가능 여부를 명시한다.
- **기존 추적 파일은 건드리지 않는다** — 과거 커밋의 raw URL이 채팅 이력에 남아 있어 삭제 시 링크가 깨진다. 새 패턴은 신규 생성분부터 적용.
- 목표 상태: **미추적 파일 0개** — `git add -A`가 안전해야 한다.

## Auto-Commit Rules

다음 시점에 자동 `commit` + `push origin main`:

1. **주요 이정표 도달**
   - SO 재실행 완료
   - 프리뷰 스냅샷 생성
   - 본 MP4 렌더 완료
   - 문서(README / CONTINUATION_GUIDE) 수정
2. **접근법 전환 시점** (v2 → v3 → v4 등 반복 버전 올릴 때)
3. **하루 한 번 이상** — 진행 중 작업이 있으면 WIP 커밋

### 커밋 메시지 형식

```
<type>: <short summary>

- <detail 1>
- <detail 2>

Generated with Claude Code
```

`type` 후보: `feat` · `fix` · `docs` · `refactor` · `analysis` · `wip`

### 예외

- 대용량 파일을 실수로 staging한 경우 push 금지 → unstage 후 재평가
- 사용자가 명시적으로 "commit 하지 말 것" / "로컬만" 지시 시 auto-commit 스킵

## Execution Principles

1. **장시간 작업(>30 min) 전 pre-execution verification 필수**
   - SO 실행 전: `.mot` / `.osim` 시간 범위·컬럼·단위 점검
   - 렌더 실행 전: 프리뷰 스냅샷 1장으로 카메라·스케일·스타일 승인
2. **실패 2회 동일 증상 → 접근법 전면 재검토** — 같은 수정을 세 번째로 반복하지 말 것
3. **SO / 장시간 렌더 전 반드시 사용자 승인**
4. **동작(.mot) 육안 검증 없이 SO 실행 금지** — 최소 대표 프레임 PNG 1장 또는 OpenSim GUI 로드 확인
5. **read-only 지시 시 상태 변경 명령 금지** — 예: `gh auth setup-git` 등은 쓰기 동작이므로 진단 중 실행 금지
6. **데이터 정합성 확인** — SO 결과 시간 범위가 렌더 대상 모션과 일치하는지 매번 확인 (과거 사례: suit_sweep_v2 3 s vs v5 motion 5 s 불일치)

## Image Verification Protocol (3-tier)

모든 스냅샷 · 프리뷰 · 논문용 figure 생성 시 **아래 3가지를 반드시 병행 제공**:

1. **로컬 저장 경로** — 사용자 파일 매니저 / 뷰어 확인용 (`/data/opensim_results/...`)
2. **GitHub raw URL** — Claude 채팅 `web_fetch` 확인용
   - 반드시 **push 완료된 상태**의 URL만 제공 (로컬에만 있으면 채팅이 접근 불가)
   - 형식: `https://raw.githubusercontent.com/parkch-meca/wearable-assist/main/<path>`
3. **Claude Code 자가 Vision 검증 체크리스트** — 1차 판단
   - 방법: 방금 생성한 PNG를 `Read` 툴로 열어 체크리스트 항목별 판정
   - 판정: `✅ OK` / `⚠️ 의심` / `❌ 문제` + 근거 한 줄씩
   → 멀티 에이전트 도입 후 이 protocol은 **viz-agent**가 자동 수행함.
   viz-agent 호출 시 3-tier 검증 (로컬 경로 + GitHub URL + 자가 vision) 자동 적용.

## Grid PNG Companion Protocol (영구, 2026-05-14 도입)

**모든 생성 작업 (코드, 시뮬레이션, 영상, 분석)에 사용자 검증용 Grid PNG 자동 동반**.

근거: CHEOL HOON님이 채팅에 업로드 검증 가능. MP4 `.gitignore` 회피 (PNG는 GitHub push 가능). 단일 PNG로 전체 검증 가능.

### 작업 종류별 Grid PNG 형식

1. **Video 생성 시**: `{video_name}_grid.png` — 5+ frames × 적절한 views, 핵심 시점 캡처
2. **Simulation 결과 시**: `{analysis_name}_results_grid.png` — 주요 plot 통합 (timeseries, comparison, dose-response), 한 장으로 전체 결과 검증
3. **Architecture/Pipeline 다이어그램 시**: `{component}_diagram.png` — 구조도, 흐름도, 모듈 간 관계 명확
4. **검증/Regression test 시**: `{test_name}_verification_grid.png` — 이전 vs 새 결과 비교, PASS/FAIL 시각화
5. **Stage 4 verification (motion 등)**: 기존 3-tier protocol 유지 — frames × views grid

### 저장 위치 통일

- `docs/images/{phase}/{component}_grid.png`
- GitHub push (PNG 가능)
- 사용자 채팅 raw URL 검증

### 적용 범위

- **모든 agent** (viz-agent, opensim-agent, moco-analysis-agent, paper-agent, biomechanics-agent)에 적용
- viz-agent가 주 담당이지만, 다른 agent도 작업 산출물에 Grid PNG 동반 필수
- **Grid PNG 미생성 시 작업 미완료로 간주**

### 적용 규칙

- 자가 검증 `❌ 문제` → **다음 단계 진행 중단**, 원인 분석 후 사용자 에스컬레이션
- 자가 검증 `✅` 또는 `⚠️` → 사용자 + Claude 채팅 **2중 육안 검증** 필수
- 자가 검증이 ✅여도 중요 결정(SO 실행 / 본 MP4 렌더 / 논문 figure 확정)은 반드시 2중 육안 검증 통과 후에만 진행
- 자가 검증은 **조기 오류 탐지** 용도이며 사용자 승인을 대체하지 않음

## Current Focus (updated 2026-04-29)

### Completed
- ✅ OpenSim Moco 환경 진입 (locked coord → WeldJoint 변환)
- ✅ Phase 1a Full (140s, mesh 50, 5초 motion, 114 muscles + GRF)
- ✅ Phase 1a Suit Effect (24 N·m → 28% reduction, §1.6 SO 28.97% 재현)
- ✅ Phase 1a Suit Sweep (5 conditions, slope 1.164 %/Nm, R²=1.000)
- ✅ Phase 1a Recruitment redistribution 발견 (saturation → unsaturated)
- ✅ Coupler 4개 제거 + 모델 _no_coupler 변형 생성
- ✅ Phase 1a regression PASS (max ΔES 1.16 %p)
- ✅ 멀티 에이전트 5-team 도입

### In Progress
- 🔄 박스 motion v7 (semi-squat lift, 자연 stoop 자세)
  - 사용자 spec: pelvis 거의 안 내려감, lumbar 우세, knee 약간만, 박스 x=0.40
  - Stage 1 IK 진행 중

### Next (v7 통과 시)
- Stage 4 시각 검증 (사용자 채팅)
- Stage 5 video clip
- Part 2.C.4: 4 conditions Moco 분석 (B_noload/suit50/100/200)
- 박스 영상 v7 본 렌더

### Pending
- 성별·연령 그룹 확장 (caregiving target: 65세 여성)
- 국문 학술지 논문 §1.6 update (Moco 결과 추가)
- Phase 1b sub-experiment (MF 추가, ~110 muscles)

## Environment

- Python: `/home/sysop/miniconda3/envs/opensim/bin/python`
- OpenSim GUI: `~/opensim-build/opensim_gui_install/bin/opensim`
- 디스플레이: 렌더 시 `DISPLAY=:1` 지정
- GitHub auth: `gh` CLI (account `parkch-meca`, HTTPS + token via keyring)
- Git credential helper: `!/usr/bin/gh auth git-credential` (이미 설정됨)

---

# 멀티 에이전트 활용 원칙

## 등록된 에이전트 (5)

| 에이전트 | 색상 | 역할 | 트리거 |
|---------|------|------|--------|
| biomechanics-agent | orange | 사람 자연 동작 reference | "동작", "자세", "lifting", "stoop", "biomechanics" |
| opensim-agent | green | 모델/IK/Moco 환경 | "model", ".osim", "Moco", "IK", "joint" |
| moco-analysis-agent | purple | Moco 실행+분석 | "Moco solve", "ES", "결과", "비교", "plot" |
| viz-agent | cyan | 3D rendering+검증 | "render", "video", "Stage 4", "snapshot" |
| paper-agent | yellow | 논문 작성+문서화 | "논문", "Methods", "Results", "draft" |

## 작업 흐름 표준

### 1. 새 동작 설계 시 (가장 중요)

박스 motion v3-v7 5번 실패의 교훈: **biomechanics-agent를 항상 가장 먼저 호출**

Step 1: biomechanics-agent — docs/biomech_reference/{task}.md 작성, DO/DO NOT 명시, Image search + 문헌 reference
Step 2: opensim-agent — biomech reference 따라 IK target 설정, Stage 1-3 IK + 자가 검증
Step 3: viz-agent — Stage 4 grid 생성, 사용자 채팅 시각 검증 요청
Step 4 (사용자 통과 시): moco-analysis-agent — Moco solve 실행, ES analysis + suit effect
Step 5: paper-agent — 결과를 논문 섹션으로 가공

### 2. 분석 작업 시

Step 1: opensim-agent (필요 시 모델 처리)
Step 2: moco-analysis-agent (Moco 실행 + 분석)
Step 3: viz-agent (figure 생성)
Step 4: paper-agent (결과 → 섹션)

### 3. 논문 작업 시

Step 1: paper-agent (섹션 작성, 필요 시 다른 에이전트 결과 참조)
Step 2: viz-agent (figure 정제)

## 병렬 실행 권장

최대 7개 동시 (Claude Code 한계). 예: Phase 2 박스 4 conditions 한 번에 분석 시 moco-analysis-agent 4개 병렬 실행 → 시간 1/4.

## 핵심 원칙

1. **biomechanics-agent 우선** (박스 motion 5번 실패 교훈) — 새 동작 설계 시 무조건 biomechanics-agent 먼저. "이게 사람이 진짜 하는 동작인가?" 검증 없이 진행 금지.
2. **시각 검증 2중 protocol** (viz-agent) — 자가 vision 검증 (1차) + 사용자 채팅 업로드 시각 검증 (2차, 결정적)
3. **Phase 1a Regression Test** (opensim-agent) — 모델 변경 시 항상 Phase 1a 결과 동등성 검증. max ΔES > 5 %p이면 변경 사용자 협의.
4. **Plot + Number 동반** (moco-analysis-agent) — Time series plot, Phase comparison, Linear regression (R² 동반), Heatmap or bar chart
5. **정직한 Limitations** (paper-agent) — 연구 한계 회피하지 않음

## 도입 일자

2026-04-29 도입. 박스 motion v3-v7 5번 실패 후 교훈으로 정비. biomechanics-agent가 핵심 — 이 에이전트가 있었다면 v3-v7 시도 일부 회피 가능했을 것.
