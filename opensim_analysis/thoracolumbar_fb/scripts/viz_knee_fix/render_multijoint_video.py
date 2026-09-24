"""[1] 본 MP4 렌더 — 승인된 프리뷰 2종의 전 프레임 동영상.

(가) waist  스툽 · 조건 A(L1→허벅지) vs 조건 B(T8→천골→허벅지) 좌우 분할
     ⭐ 프레임 구성 수정 — 프리뷰의 t=2.20/2.75/3.40 은 자세가 거의 같아 중복이었다.
        동영상은 t=0 직립부터 전 구간을 담아 **상단 앵커 높이 차(L1 vs T8)** 가
        직립 구간에서 먼저 보이게 한다. 100 N 포화 표기는 유지.
(나) carry  운반 20 kg · 조건 B + 팔꿈치 (어깨 제외) — 프리뷰 구성 그대로

■ 공통
  · 패널 구성·색·카메라·캡션은 make_multijoint_preview 의 함수를 그대로 호출한다 (복제 없음)
  · 슈트 경로색 = 청록 계열 (근육 inferno 와 분리), 굵기·색이 장력에 비례
  · 인코딩 H.264 / yuv420p / **Constrained Baseline** (profile:v baseline) + faststart
  · 포스터 프레임(대표 정지컷) 별도 PNG 추출
  ⚠️ 기존 파일 덮어쓰기 금지 — 출력은 `*_v1.mp4` 새 이름

■ 사용법
  render_multijoint_video.py waist|carry [--shard i/N] [--frames-only] [--encode-only]
  (shard 로 프레임을 나눠 병렬 렌더한 뒤 --encode-only 로 합친다)
"""
import os
import re
import sys
import json
import shutil
import subprocess
os.environ.setdefault('DISPLAY', ':1')
from pathlib import Path
import numpy as np
import opensim as osim
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_multijoint_preview as MP
import suit_model as sm
import suit_moment_arm_fix as F
import suit_span_conditions as SC
import suit_multijoint_conditions as MC

VID = Path('/data/opensim_results/multijoint_videos')
VID.mkdir(parents=True, exist_ok=True)
DOC = Path('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/suit_multijoint')
DOC.mkdir(parents=True, exist_ok=True)
FR = Path('/data/opensim_results/multijoint_videos/frames')

# (가) 스툽 A vs B
STOOP_MOT = '/data/stoop_results/stoop_v5/v5_30fps_armfix.mot'
A_STO = '/data/suit_16Nm/path16/so_StaticOptimization_activation.sto'
B_STO = '/data/suit_span/path_T8_sacfem/so_StaticOptimization_activation.sto'
OFF_STO = '/data/romfix_unified/stoop_off/so_StaticOptimization_activation.sto'
STOOP_WIN = (2.091667, 3.408333)
STOOP_LOOPS = 2
STOOP_POSTER = 0.25          # 직립 — 앵커 높이 차가 가장 잘 보이는 시점
# 갱신된 4프레임 그리드 — 직립 포함, 자세가 서로 다른 시점만
STOOP_GRID_FRAMES = [0.20, 1.40, 2.75, 4.40]

# (나) 운반 다부위
CARRY_STO = '/data/suit_carry/all/so_StaticOptimization_activation.sto'
CARRY_LOOPS = 5
CARRY_POSTER = 0.85


def sharded(n, spec):
    if not spec:
        return list(range(n))
    i, N = (int(x) for x in spec.split('/'))
    return [k for k in range(n) if k % N == i]


def encode(frames_dir, pattern, fps, out_mp4):
    """H.264 / yuv420p / Constrained Baseline."""
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps),
           '-i', str(frames_dir / pattern),
           '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2',
           '-c:v', 'libx264', '-profile:v', 'baseline', '-level', '3.1',
           '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'medium',
           '-movflags', '+faststart', str(out_mp4)]
    subprocess.run(cmd, check=True)
    p = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                        '-show_entries', 'stream=profile,pix_fmt,width,height,nb_frames,codec_name',
                        '-of', 'default=nw=1', str(out_mp4)],
                       capture_output=True, text=True)
    return p.stdout.strip()


def poster(frames_dir, pattern, idx, out_png):
    src = frames_dir / (pattern % idx)
    shutil.copy(str(src), str(out_png))
    return out_png


# ────────────────────────── (가) 스툽 A vs B ──────────────────────────
def stoop_setup():
    model = osim.Model(F.MODEL)
    state = model.initSystem()
    meshes = MP.collect_meshes(model)
    tbl, cols, Tm = MP.load_mot(STOOP_MOT)
    mt = MP.mtypes_of(model, cols)
    CONDS = [
        ('A', '조건 A · L1→허벅지 (현 하드웨어)',
         MP.waist_path_pts(F.MODEL, 'L1', 'femur'), MP.load_act(A_STO)),
        ('B', '조건 B · T8→천골→허벅지 (설계 제안)',
         MP.waist_path_pts(F.MODEL, 'T8', 'sacrum_femur'), MP.load_act(B_STO)),
    ]
    # 기준장 = 그 조건의 SO 를 만들 때와 동일하게 모션 첫 프레임
    row0 = tbl.getRowAtIndex(0)
    cs0 = model.getCoordinateSet()
    for ci, nm in enumerate(cols):
        if cs0.contains(nm):
            v = row0[ci]
            cs0.get(nm).setValue(state, np.radians(v) if mt[nm] == 1 else v, False)
    model.realizePosition(state)
    L0 = {}
    for key, _, P, _ in CONDS:
        L0[key] = {sd: sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000
                   for sd, G in ((sd, MP.path_ground(model, state, P[sd])) for sd in P)}
    return model, state, meshes, tbl, cols, Tm, mt, CONDS, L0, MP.load_act(OFF_STO)


def stoop_frame(env, fi, out_png, tmp_pfx):
    model, state, meshes, tbl, cols, Tm, mt, CONDS, L0, (To, lo, Do) = env
    tq = float(Tm[fi])
    aoff = MP.acts_at(To, Do, lo, tq)
    es_off = 100 * max(v for kk, v in aoff.items()
                       if kk.startswith(('IL_', 'LTpL', 'LTpT')))
    panels, vals = [], []
    for key, title, P, (Tt, ll, Dd) in CONDS:
        acts = MP.acts_at(Tt, Dd, ll, tq)
        row = tbl.getRowAtIndex(fi)
        cs = model.getCoordinateSet()
        for ci, nm in enumerate(cols):
            if cs.contains(nm):
                v = row[ci]
                cs.get(nm).setValue(state, np.radians(v) if mt[nm] == 1 else v, False)
        model.realizePosition(state)
        pts_t = [MP.tens_for(model, state, P[sd], L0[key][sd]) for sd in ('R', 'L')]
        es = 100 * max(v for kk, v in acts.items()
                       if kk.startswith(('IL_', 'LTpL', 'LTpT')))
        vals.append((es, float(np.mean([t for _, t in pts_t]))))
        png = MP.TMP / f'{tmp_pfx}_{key}.png'
        panels.append(MP.render_panel(model, state, meshes, tbl, cols, mt, fi,
                                      acts, pts_t, title, png, cam_dz=3.0))
    a, b = Image.open(panels[0]), Image.open(panels[1])
    comb = Image.new('RGB', (a.width + b.width, a.height + MP.CAPH), (12, 12, 12))
    comb.paste(a, (0, 0))
    comb.paste(b, (a.width, 0))
    inwin = STOOP_WIN[0] <= tq <= STOOP_WIN[1]
    sat = min(vals[0][1], vals[1][1]) >= 99.9
    cap = [(f't = {tq:.2f} s' + ('   [슈트 작동창]' if inwin else ''),
            (235, 235, 235), 20),
           (f'ES peak   OFF {es_off:5.1f} %  →  A {vals[0][0]:5.1f} %    |    '
            f'B {vals[1][0]:5.1f} %', (255, 190, 120), 18),
           (f'슈트 장력   A {vals[0][1]:5.1f} N    |    B {vals[1][1]:5.1f} N'
            + ('   (양쪽 상한 포화)' if sat else ''), (150, 200, 255), 18)]
    comb.paste(MP.caption_strip(a.width + b.width, cap), (0, a.height))
    comb.save(out_png)
    return vals


def stoop_grid(env):
    """갱신된 4프레임 검증 그리드 — 직립 포함."""
    Tm = env[5]
    ims = []
    for k, tq in enumerate(STOOP_GRID_FRAMES):
        fi = int(np.argmin(np.abs(Tm - tq)))
        p = MP.TMP / f'grid_w_{k}.png'
        stoop_frame(env, fi, p, f'gw{k}')
        ims.append(Image.open(p))
    cw, ch = ims[0].width, ims[0].height
    canvas = Image.new('RGB', (cw, ch * len(ims)), (12, 12, 12))
    for i, im in enumerate(ims):
        canvas.paste(im, (0, i * ch))
    out = DOC / 'preview_waist_AvsB_v1.png'
    canvas.save(out)
    return out


# ────────────────────────── (나) 운반 다부위 ──────────────────────────
def carry_setup():
    model = osim.Model(MC.MODEL)
    state = model.initSystem()
    meshes = MP.collect_meshes(model)
    tbl, cols, Tm = MP.load_mot(MC.MOT)
    mt = MP.mtypes_of(model, cols)
    PW_ = {sd: MC.waist_points(sd) for sd in ('R', 'L')}
    PE_ = {sd: MC.elbow_points(sd, extended=True) for sd in ('R', 'L')}
    L0w = {sd: MC.neutral_length(PW_[sd]) for sd in PW_}
    # 팔꿈치 기준장 = 작업 자세 피팅 (해석 첫 프레임) — 조건 생성과 동일 규칙
    row0 = tbl.getRowAtIndex(0)
    cs0 = model.getCoordinateSet()
    for ci, nm in enumerate(cols):
        if cs0.contains(nm):
            v = row0[ci]
            cs0.get(nm).setValue(state, np.radians(v) if mt[nm] == 1 else v, False)
    model.realizePosition(state)
    L0e = {sd: sum(np.linalg.norm(G[i + 1] - G[i]) for i in range(len(G) - 1)) * 1000
           for sd, G in ((sd, MP.path_ground(model, state, PE_[sd])) for sd in PE_)}
    act = MP.load_act(CARRY_STO)
    return model, state, meshes, tbl, cols, Tm, mt, PW_, PE_, L0w, L0e, act


def carry_frame(env, fi, out_png, tmp_pfx):
    (model, state, meshes, tbl, cols, Tm, mt, PW_, PE_, L0w, L0e,
     (Tt, ll, Dd)) = env
    tq = float(Tm[fi])
    row = tbl.getRowAtIndex(fi)
    cs = model.getCoordinateSet()
    for ci, nm in enumerate(cols):
        if cs.contains(nm):
            v = row[ci]
            cs.get(nm).setValue(state, np.radians(v) if mt[nm] == 1 else v, False)
    model.realizePosition(state)
    pts_t = [MP.tens_for(model, state, PW_[sd], L0w[sd]) for sd in ('R', 'L')]
    pts_e = [MP.tens_for(model, state, PE_[sd], L0e[sd]) for sd in ('R', 'L')]
    acts = MP.acts_at(Tt, Dd, ll, tq)
    es = 100 * max(v for kk, v in acts.items()
                   if kk.startswith(('IL_', 'LTpL', 'LTpT')))
    eb = 100 * np.mean([v for kk, v in acts.items()
                        if kk.startswith(('BIClong', 'BICshort', 'BRA_', 'BRD_'))])
    png = MP.TMP / f'{tmp_pfx}.png'
    MP.render_panel(model, state, meshes, tbl, cols, mt, fi, acts, pts_t + pts_e,
                    '운반 20 kg · 조건 B + 팔꿈치 (어깨 제외)', png,
                    cam_dz=3.1, keep_arm=True, box=True)
    im = Image.open(png)
    comb = Image.new('RGB', (im.width, im.height + MP.CAPH), (12, 12, 12))
    comb.paste(im, (0, 0))
    cap = [(f't = {tq:.2f} s', (235, 235, 235), 20),
           (f'ES peak {es:5.1f} %   |   팔꿈치 굴근 평균 {eb:5.2f} %',
            (255, 190, 120), 18),
           (f'허리 장력 {np.mean([t for _, t in pts_t]):5.1f} N   |   '
            f'팔꿈치 장력 {np.mean([t for _, t in pts_e]):5.1f} N',
            (150, 200, 255), 18)]
    comb.paste(MP.caption_strip(im.width, cap), (0, im.height))
    comb.save(out_png)
    return es, eb


JOBS = {
    'waist': dict(setup=stoop_setup, frame=stoop_frame, loops=STOOP_LOOPS,
                  poster_t=STOOP_POSTER, mp4='stoop_waist_AvsB_v1.mp4',
                  poster='poster_stoop_waist_AvsB_v1.png'),
    'carry': dict(setup=carry_setup, frame=carry_frame, loops=CARRY_LOOPS,
                  poster_t=CARRY_POSTER, mp4='carry_multijoint_v1.mp4',
                  poster='poster_carry_multijoint_v1.png'),
}


def main():
    which = sys.argv[1]
    cfg = JOBS[which]
    shard = next((a.split('=')[-1] if '=' in a else sys.argv[sys.argv.index(a) + 1]
                  for a in sys.argv if a.startswith('--shard')), None)
    encode_only = '--encode-only' in sys.argv
    frames_only = '--frames-only' in sys.argv
    grid_only = '--grid-only' in sys.argv
    fdir = FR / which
    fdir.mkdir(parents=True, exist_ok=True)

    if not encode_only:
        env = cfg['setup']()
        Tm = env[5]
        if grid_only:
            print('SAVED', stoop_grid(env))
            return
        idxs = sharded(len(Tm), shard)
        for k in idxs:
            out = fdir / f'frame_{k:04d}.png'
            cfg['frame'](env, k, out, f'v_{which}_{k}')
            if k % 20 == 0:
                print(f'  [{which}] frame {k}/{len(Tm)}', flush=True)
        if frames_only:
            print(f'[{which}] 프레임 {len(idxs)}장 완료 (shard {shard})')
            return

    # 루프 복제 → 연속 번호
    tbl, cols, Tm = MP.load_mot(STOOP_MOT if which == 'waist' else MC.MOT)
    n = len(Tm)
    dt = float(np.median(np.diff(Tm)))
    fps = int(round(1.0 / dt))
    seq = FR / f'{which}_seq'
    if seq.exists():
        shutil.rmtree(seq)
    seq.mkdir(parents=True)
    vi = 0
    for _ in range(cfg['loops']):
        for k in range(n):
            os.link(fdir / f'frame_{k:04d}.png', seq / f'v_{vi:05d}.png')
            vi += 1
    out_mp4 = VID / cfg['mp4']
    if out_mp4.exists():
        print(f'⛔ 이미 있음 — 덮어쓰지 않는다: {out_mp4}')
        return
    info = encode(seq, 'v_%05d.png', fps, out_mp4)
    pidx = int(np.argmin(np.abs(Tm - cfg['poster_t'])))
    pp = poster(fdir, 'frame_%04d.png', pidx, DOC / cfg['poster'])
    print(f'VIDEO {out_mp4}  ({out_mp4.stat().st_size/1e6:.1f} MB) '
          f'{vi} 프레임 @ {fps} fps')
    print(info)
    print(f'POSTER {pp}  (t={Tm[pidx]:.2f} s)')


if __name__ == '__main__':
    main()
