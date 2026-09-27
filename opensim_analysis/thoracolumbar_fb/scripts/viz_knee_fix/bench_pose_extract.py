"""[벤치 ■1] 실험 영상에서 시상면 운동학 추출 — MediaPipe PoseLandmarker.

영상 `demo-waist-comparison.webm` (회사 소유) 3패널: NO SUIT / PASSIVE / ACTIVE.
PASSIVE 는 상용 수동형이라 이번 해석에서 제외 (사용자 지시), NO SUIT · ACTIVE 만 쓴다.

■ 측정 규약 (시상면, 피험자는 화면 왼쪽을 본다)
  몸통 경사   어깨–엉덩이 선과 **수평**이 이루는 각. 0° = 수평, +90° = 직립
  고관절 굴곡 몸통선과 대퇴선 사이 각의 여각 (0° = 곧게 편 상태)
  무릎 굴곡   대퇴선과 하퇴선 (0° = 완전 신전)
  손 높이     손목 y (발목 높이를 0, 어깨 높이를 1 로 정규화)
⚠️ 요추 굴곡은 표면 랜드마크로 직접 못 잰다 — 몸통 경사와 고관절 굴곡의 차이로
   **추정**하며, 그 자체를 측정값으로 쓰지 않는다 (§보고 참조).
"""
import os
import sys
import json
import numpy as np

sys.path.insert(0, '/data/suit_bench/pylibs')
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

VID = '/data/suit_bench/demo-waist-comparison.webm'
MODEL = '/data/suit_bench/pose_landmarker_heavy.task'
OUT = '/data/suit_bench'
PANELS = {'nosuit': (0.0, 1 / 3), 'active': (2 / 3, 1.0)}
L = {'nose': 0, 'l_ear': 7, 'r_ear': 8, 'l_sh': 11, 'r_sh': 12, 'l_el': 13,
     'r_el': 14, 'l_wr': 15, 'r_wr': 16, 'l_hip': 23, 'r_hip': 24,
     'l_kn': 25, 'r_kn': 26, 'l_an': 27, 'r_an': 28, 'l_ft': 31, 'r_ft': 32}


def ang_horiz(p, q):
    """p→q 선이 수평과 이루는 각 (도). 화면 y 는 아래로 증가하므로 뒤집는다."""
    d = np.array([q[0] - p[0], -(q[1] - p[1])])
    return float(np.degrees(np.arctan2(d[1], d[0])))


def between(a, b, c):
    """∠abc (도)."""
    u = np.array([a[0] - b[0], -(a[1] - b[1])])
    v = np.array([c[0] - b[0], -(c[1] - b[1])])
    cs = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-9)
    return float(np.degrees(np.arccos(np.clip(cs, -1, 1))))


def main():
    opts = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=MODEL),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1, min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5, min_tracking_confidence=0.5)

    cap = cv2.VideoCapture(VID)
    fps = cap.get(cv2.CAP_PROP_FPS)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f'영상 {W}x{H} · {fps:.2f} fps · {n} 프레임', flush=True)

    res = {k: [] for k in PANELS}
    frames = []
    fi = 0
    landmarkers = {k: vision.PoseLandmarker.create_from_options(opts) for k in PANELS}
    while True:
        ok, img = cap.read()
        if not ok:
            break
        t_ms = int(1000 * fi / fps)
        frames.append(fi / fps)
        for key, (x0, x1) in PANELS.items():
            sub = img[:, int(x0 * W):int(x1 * W)]
            rgb = cv2.cvtColor(sub, cv2.COLOR_BGR2RGB)
            mpimg = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            out = landmarkers[key].detect_for_video(mpimg, t_ms)
            if not out.pose_landmarks:
                res[key].append(None)
                continue
            lm = out.pose_landmarks[0]
            h, w = sub.shape[:2]
            P = {nm: (lm[i].x * w, lm[i].y * h, lm[i].visibility)
                 for nm, i in L.items()}
            res[key].append(P)
        fi += 1
    cap.release()

    # 좌우 평균 (시상면이므로 가려진 쪽 대신 보이는 쪽 가중)
    def mid(P, a, b):
        pa, pb = P[a], P[b]
        wa, wb = max(pa[2], 1e-3), max(pb[2], 1e-3)
        return ((pa[0] * wa + pb[0] * wb) / (wa + wb),
                (pa[1] * wa + pb[1] * wb) / (wa + wb))

    R = {}
    for key in PANELS:
        rows = []
        for t, P in zip(frames, res[key]):
            if P is None:
                rows.append(None)
                continue
            sh, hip = mid(P, 'l_sh', 'r_sh'), mid(P, 'l_hip', 'r_hip')
            kn, an = mid(P, 'l_kn', 'r_kn'), mid(P, 'l_an', 'r_an')
            wr = mid(P, 'l_wr', 'r_wr')
            trunk = ang_horiz(hip, sh)
            thigh = ang_horiz(kn, hip)
            hipflex = 180.0 - between(sh, hip, kn)
            knee = 180.0 - between(hip, kn, an)
            scale = abs(sh[1] - an[1]) + 1e-9
            rows.append(dict(t=t, trunk=trunk, thigh=thigh, hip_flex=hipflex,
                             knee=knee,
                             hand_norm=float((an[1] - wr[1]) / scale),
                             sh=sh, hip=hip, kn=kn, an=an, wr=wr))
        R[key] = rows

    json.dump(dict(fps=fps, res=R), open(f'{OUT}/pose_raw.json', 'w'),
              ensure_ascii=False, indent=1, default=float)

    print(f"\n{'t(s)':>6s} | {'NO SUIT 몸통°':>12s} {'고관절°':>8s} {'무릎°':>7s} "
          f"{'손높이':>7s} | {'ACTIVE 몸통°':>12s} {'고관절°':>8s} {'무릎°':>7s} {'손높이':>7s}")
    for i, t in enumerate(frames):
        if i % 4:
            continue
        a, b = R['nosuit'][i], R['active'][i]
        f = lambda r, k: (f"{r[k]:8.1f}" if r else '       —')
        print(f'{t:6.2f} | {f(a,"trunk")}{"":4s}{f(a,"hip_flex")}{f(a,"knee")}'
              f'{f(a,"hand_norm")} | {f(b,"trunk")}{"":4s}{f(b,"hip_flex")}'
              f'{f(b,"knee")}{f(b,"hand_norm")}')
    print(f'\nSAVED {OUT}/pose_raw.json')


if __name__ == '__main__':
    main()
