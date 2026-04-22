# ThoracolumbarFB Analysis — SMA Suit & Erector Spinae Load

SMA fabric muscle 기반 wearable suit가 stoop lift 동작 중 척추기립근(ES) 활성도에 미치는 영향을 정량화합니다.

## 모델 & 동작

- **모델**: ThoracolumbarFB v2.0 (OpenSim 4.x, 620 근육 전신)
- **동작**:
  - `stoop_synthetic_v5.mot` — 제자리 stoop (5 s, GRF 포함)
  - `stoop_box20kg.mot` — 20 kg 박스 들기 (3 s)
- **슈트 모델**: thoracic–pelvis 토크 커플, 모멘트 암 0.12 m (F=200 N → T=24 N·m peak)

## 디렉토리 구조

```
thoracolumbar_fb/
├── README.md                 ← 이 파일 (요약)
├── scripts/                  ← Python 스크립트 10개 (motion gen, SO, rendering)
└── docs/
    ├── CONTINUATION_GUIDE.md ← 전체 진행 가이드 (세부 현황·파일 경로)
    └── images/
        ├── box_lift_preview_v3.png
        └── suit_effect_plot.png
```

### scripts/

| 스크립트 | 용도 |
|---|---|
| `gen_stoop_v5.py` | stoop v5 동작 생성 (GRF 포함) |
| `gen_stoop_box_motion.py` | 20 kg 박스 들기 동작 생성 |
| `run_stoop_v5_so.py` | v5 베이스라인 ID + SO |
| `run_suit_so_v2.py` | 슈트 스윕 SO (F0–F200, 3 s) |
| `run_suit_so_v5.py` | 슈트 F200 SO (5 s v5, GRF + 토크 커플 병합) |
| `run_box_so.py` | 박스 들기 4조건 SO |
| `render_v5_video.py` | v5 단독 렌더 |
| `render_suit_comparison_v2.py` | 슈트 비교 렌더 |
| `render_box_comparison.py` | 박스 비교 렌더 |
| `plot_suit_sweep.py` | 슈트 도즈 반응 플롯 |

> **경로 주의**: 스크립트 상단의 모델·동작·결과 경로는 절대경로(`/data/...`)로 하드코딩됨. 상대경로 리팩토링은 별도 이슈로 후순위.

## 대용량 산출물 위치 (repo 외부 / `.gitignore`에 의해 제외)

| 자원 | 경로 |
|---|---|
| 모델 (.osim) | `/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/` |
| 동작 (.mot) | `/data/stoop_motion/` |
| GRF (.sto/.xml) | `/data/stoop_motion/stoop_grf_v5.{sto,xml}` |
| SO 결과 (.sto) | `/data/stoop_results/{stoop_v5, suit_sweep_v2, suit_sweep_v5, box_lift}/` |
| 영상 (.mp4) | `/data/opensim_results/video/` |

## 실행 (요약)

```bash
conda activate opensim
PY=/home/sysop/miniconda3/envs/opensim/bin/python

# SO 예시 (슈트 F200, v5 모션)
$PY scripts/run_suit_so_v5.py 200

# 렌더 (preview 먼저)
DISPLAY=:1 $PY scripts/render_suit_comparison_v2.py preview
DISPLAY=:1 $PY scripts/render_suit_comparison_v2.py video
```

상세 실행 순서·전제·트러블슈팅은 [`docs/CONTINUATION_GUIDE.md`](docs/CONTINUATION_GUIDE.md) 참조.

## 핵심 결과 (CONTINUATION_GUIDE §1.6)

- **슈트 도즈 반응** (3 s 모션, suit_sweep_v2): ES mean peak 선형 감소
  - slope = **1.206 %/N·m**, intercept = 0.04 %, **R² = 1.0000**
  - 24 N·m (F=200 N) → **28.97 % 감소**
- **v5 5 s 모션 + 200 N 슈트**: ES mean peak 약 **28–29 % 감소** (t=2.5–3.0 s)
- **20 kg 박스 + 200 N 슈트**: 파지 직후 t≈2.0 s에서 **−21 %** (11.7 → 9.3 %); 리프트오프 피크 t≈2.33 s에서 **−10 %** (18.4 → 16.5 %)

## 현재 진행 상태

- [x] v5 stoop 단독 렌더
- [x] v5 슈트 비교 렌더 (`stoop_suit_comparison_v2.mp4`)
- [x] 박스 들기 v1 렌더
- [ ] **박스 들기 v4** — hip/knee flexion 증가 모션 재생성 중 (손이 바닥까지 내려오도록)
- [ ] OpenSim Moco 분석 (eccentric/concentric 비대칭)
- [ ] 성별·연령 그룹 확장

다음 단계 세부는 [`docs/CONTINUATION_GUIDE.md §2`](docs/CONTINUATION_GUIDE.md) 참조.
