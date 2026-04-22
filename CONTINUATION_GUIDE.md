# CONTINUATION GUIDE

_Last updated: 2026-04-22_

새 채팅 세션에서 작업을 이어가려면 이 문서를 먼저 읽어 주세요.

---

## 1. 프로젝트 현재 상태

### 1.1 환경

- **OpenSim GUI 4.6** — Ubuntu 24.04에 설치 완료
  - 실행: `~/opensim-build/opensim_gui_install/bin/opensim`
  - 브라우저 뷰어: `http://127.0.0.1:8002/index.html?css=gui&modern=true`
- **Python OpenSim SDK** — conda 환경 `opensim`
  - Python: `/home/sysop/miniconda3/envs/opensim/bin/python`

### 1.2 모델

- **ThoracolumbarFB v2.0 (OS 4.x, 620 근육 전신)** — 정상 작동 확인
  - 수정 모델: `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim`
  - 지오메트리: `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/Geometry/`
  - 예비 액추에이터 포함 모델 (박스용): `/data/stoop_results/box_lift/model_with_reserves_box.osim`
  - 예비 액추에이터 포함 모델 (v5): `/data/stoop_results/stoop_v5/model_with_reserves_v5.osim`

### 1.3 동작 데이터

| 유형 | 파일 | 길이 | GRF |
|---|---|---|---|
| 제자리 stoop (느린 대칭, 발 고정) | `/data/stoop_motion/stoop_synthetic_v5.mot` | 5 s @ 120fps | ✅ `stoop_grf_v5.sto` / `stoop_grf_v5.xml` |
| 20 kg 박스 들기 | `/data/stoop_motion/stoop_box20kg.mot` | 3 s @ 120fps | (ExternalLoads로 직접 처리) |

### 1.4 Static Optimization 결과

| 조건 | 위치 | 동작 | 비고 |
|---|---|---|---|
| 무부하 0 N (v5) | `/data/stoop_results/stoop_v5/so_v5_StaticOptimization_activation.sto` | 5 s | v5 베이스라인 |
| 슈트 스윕 F{0,50,100,150,200} | `/data/stoop_results/suit_sweep_v2/F*/` | **3 s (구버전)** | 선형회귀용 |
| 슈트 F200 (v5) | `/data/stoop_results/suit_sweep_v5/F200/suit_v5_F200_StaticOptimization_activation.sto` | 5 s | 비교 영상용 |
| 박스 들기 0/100/200 N | `/data/stoop_results/box_lift/B_{noload,suit0,suit100,suit200}/` | 3 s | 박스 파지 t≥2.0s |

### 1.5 영상

| 콘텐츠 | 파일 |
|---|---|
| v5 단독 (OpenSim GUI 스타일) | `/data/opensim_results/video/stoop_v5_gui_quality_v2.mp4` |
| v5 슈트 비교 (0 N vs 200 N) | `/data/opensim_results/video/stoop_suit_comparison_v2.mp4` |
| 박스 들기 비교 (v1, 박스 표시 이슈 있음) | `/data/opensim_results/video/stoop_box_comparison.mp4` |

### 1.6 핵심 결과

- **SMA 슈트 도즈 반응 (3 s 모션 기준, suit_sweep_v2)**: ES mean peak 활성도 선형 감소
  - Δmean % vs 토크(N·m): **slope = 1.206 %/Nm**, intercept = 0.04 %, **R² = 1.0000**
  - 24 N·m (F=200 N)에서 **28.97 % 감소**
- **v5 5-s 모션 + 200 N 슈트**: ES mean peak 기준 약 **28–29 % 감소** (hold 구간 t=2.5–3.0s)
- **20 kg 박스 + 200 N 슈트**: 파지 직후 t≈2.0s에서 **21 % 감소** (11.7 % → 9.3 %); 박스 리프트오프 피크 t≈2.33s에서 10 % 감소 (18.4 % → 16.5 %)

---

## 2. 다음 단계

### 2.1 박스 들기 영상 수정 (진행 중)

- [x] 박스 크기 20×15×20 cm로 축소
- [x] 박스가 t=0부터 바닥(X=0.35, Y=-0.78)에 고정되어 보이도록 수정
- [x] 파지 후(t≥2 s) 박스가 손 중심 +0.08 m 앞쪽을 추적해 직립 시 몸통 관통 방지
- [x] 프리뷰 v2 생성: `/data/opensim_results/box_lift_preview_v2.png`
- [ ] **본 MP4 재렌더 승인 대기**: `python /data/stoop_motion/render_box_comparison.py video`
  - 스크립트: `/data/stoop_motion/render_box_comparison.py` (수정 완료)
  - 예상 소요: ~4 분 (91 프레임)
  - 출력: `/data/opensim_results/video/stoop_box_comparison.mp4` (덮어씀)

### 2.2 OpenSim Moco 분석 (예정)

- **목적**: eccentric(이완성)/concentric(단축성) 비대칭 패턴 반영
- **Static Optimization 한계**: 시점별 스냅샷 최적화 → 근육 activation dynamics·길이·속도 관계 미반영
- **예상 소요**: 하룻밤 (6–10 시간) 실행 필요
- **산출물**: 각 조건별 근육 activation 동역학 시계열 + 시간적분 비용 지표

### 2.3 성별·연령 그룹 확장 (예정)

- 현재는 MaleFullBody (성인 남성 1조건)만 수행
- 확장 시 모델 스케일링 + 인체 매개변수 세트 준비 필요

---

## 3. 주요 파일 경로

| 항목 | 경로 |
|---|---|
| 수정 모델 | `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified.osim` |
| stoop v5 동작 | `/data/stoop_motion/stoop_synthetic_v5.mot` |
| 박스 동작 | `/data/stoop_motion/stoop_box20kg.mot` |
| SO 결과 (무부하 v5) | `/data/stoop_results/stoop_v5/` |
| SO 결과 (슈트 v2 스윕, 3 s) | `/data/stoop_results/suit_sweep_v2/` |
| SO 결과 (슈트 v5 F200, 5 s) | `/data/stoop_results/suit_sweep_v5/F200/` |
| SO 결과 (박스) | `/data/stoop_results/box_lift/` |
| 영상 폴더 | `/data/opensim_results/video/` |
| 분석 플롯 | `/data/opensim_results/suit_effect_plot.png` |

### 주요 Python 스크립트 (`/data/stoop_motion/`)

| 스크립트 | 용도 |
|---|---|
| `gen_stoop_v5.py` | 제자리 stoop v5 동작 생성 (GRF 포함) |
| `gen_stoop_box_motion.py` | 20 kg 박스 들기 동작 생성 |
| `run_stoop_v5_so.py` | v5 베이스라인 ID + SO |
| `run_suit_so_v2.py` | 슈트 스윕 SO (3 s 모션, F0–F200) |
| `run_suit_so_v5.py` | 슈트 F200 SO (5 s v5 모션, GRF + 토크 커플 병합) |
| `run_box_so.py` | 박스 들기 4조건 SO (B_noload / B_suit0 / B_suit100 / B_suit200) |
| `render_v5_video.py` | v5 단독 렌더 |
| `render_suit_comparison_v2.py` | 슈트 비교 렌더 (preview / video 모드) |
| `render_box_comparison.py` | 박스 비교 렌더 (preview / video 모드) |
| `plot_suit_sweep.py` | 슈트 도즈 반응 플롯 + 선형 회귀 |

---

## 4. 실행 방법

```bash
# OpenSim GUI 실행
~/opensim-build/opensim_gui_install/bin/opensim &
# 브라우저에서 확인
firefox 'http://127.0.0.1:8002/index.html?css=gui&modern=true'

# Python 환경
conda activate opensim
# (또는 직접)  PY=/home/sysop/miniconda3/envs/opensim/bin/python

# SO 재실행 (슈트 v5 F200만)
$PY /data/stoop_motion/run_suit_so_v5.py 200

# 영상 렌더 — 항상 preview 먼저
DISPLAY=:1 $PY /data/stoop_motion/render_suit_comparison_v2.py preview
DISPLAY=:1 $PY /data/stoop_motion/render_suit_comparison_v2.py video

DISPLAY=:1 $PY /data/stoop_motion/render_box_comparison.py preview
DISPLAY=:1 $PY /data/stoop_motion/render_box_comparison.py video

# 슈트 도즈 반응 플롯
$PY /data/stoop_motion/plot_suit_sweep.py
```

---

## 5. 핵심 원칙 (반드시 준수)

1. **동작 스냅샷 육안 확인 필수** — 모든 SO/시뮬레이션 실행 전 `.mot` 파일을 OpenSim GUI에서 한 번 로드해 보고 오류가 없는지 확인.
2. **승인 전 SO/영상 렌더 실행 금지** — 장시간 작업이므로 매 단계 프리뷰(스냅샷 PNG) 확인 후 사용자 승인을 받고 진행.
3. **중요 결과는 반드시 영상으로 저장** — 숫자만 남기지 말고 `.mp4`로 남겨 리뷰 가능하게 둘 것.
4. **데이터 정합성 확인** — SO 결과의 시간 범위가 렌더링할 모션과 일치하는지 항상 확인 (예: suit_sweep_v2는 3 s, v5 motion은 5 s).

---

## 6. Git 상태

- `/data` 자체는 git repo가 아님
- `/data/wearable-assist/` 에 기존 repo 존재 (remote: `github.com/meca92/wearable-assist.git`, 첫 커밋 전 상태)
- 본 ThoracolumbarFB 작업물(stoop_motion/, stoop_results/, opensim_models/, opensim_results/)은 repo 외부에 위치
