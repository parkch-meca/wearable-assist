# Claude Code Instructions for `wearable-assist`

## Project Context

SMA fabric muscle 기반 wearable suit가 들기 작업 중 척추기립근(erector spinae) 부하에 미치는 영향을 정량화.
주 모델: ThoracolumbarFB v2.0 (OpenSim 4.x, 620 근육 전신).

### 동작 용어 (terminology)

- **stoop lift** — 제자리 허리 굽힘 (무릎 거의 고정, 허리만 굽힘). v5 모션(`stoop_synthetic_v5.mot`)이 여기에 해당.
- **semi-squat lift** 또는 **stoop-squat hybrid** — 박스 들기처럼 무릎·고관절·허리가 함께 굽는 실제 들기 자세. `stoop_box20kg_v2.mot` (박스 v2)가 여기에 해당.
- `§1.6`의 "stoop lift 28–29 % 감소" 수치는 v5 제자리 stoop에만 적용; 박스 v2 수치는 별도 리포트.

## Directory Conventions

- `opensim_analysis/thoracolumbar_fb/` — 메인 분석 (현재 진행)
- `opensim_analysis/rajagopal_legacy/` — 이관 전 Rajagopal 기반 분석 (보존)
- 대용량 산출물 (`.mot`, `.sto`, `.mp4`, `.osim`, `.pkl`, `.npy`)은 `/data/` 하위 (repo 외부). `.gitignore` 참조.
- 결과 이미지(`.png`)는 원칙적으로 제외; 단 `opensim_analysis/*/docs/images/` 및 `docs/figures/` 하위는 포함 허용.

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

### 적용 규칙

- 자가 검증 `❌ 문제` → **다음 단계 진행 중단**, 원인 분석 후 사용자 에스컬레이션
- 자가 검증 `✅` 또는 `⚠️` → 사용자 + Claude 채팅 **2중 육안 검증** 필수
- 자가 검증이 ✅여도 중요 결정(SO 실행 / 본 MP4 렌더 / 논문 figure 확정)은 반드시 2중 육안 검증 통과 후에만 진행
- 자가 검증은 **조기 오류 탐지** 용도이며 사용자 승인을 대체하지 않음

## Current Focus (updated regularly)

- [완료] 박스 모션 v2 재생성 (semi-squat lift, hip+6° knee−10° ankle+4° pelvis_ty−0.10 m; 손이 박스 윗면 y ≈ −0.61 m 접촉)
- [진행중] 박스 SO v2 4조건 재실행 + 프리뷰 v4
- [대기] 박스 비교 MP4 v2 본 렌더 (2중 육안 검증 후)
- [대기] OpenSim Moco 분석 (eccentric / concentric 비대칭 패턴 반영)
- [대기] 성별 · 연령 그룹 확장

## Environment

- Python: `/home/sysop/miniconda3/envs/opensim/bin/python`
- OpenSim GUI: `~/opensim-build/opensim_gui_install/bin/opensim`
- 디스플레이: 렌더 시 `DISPLAY=:1` 지정
- GitHub auth: `gh` CLI (account `parkch-meca`, HTTPS + token via keyring)
- Git credential helper: `!/usr/bin/gh auth git-credential` (이미 설정됨)
