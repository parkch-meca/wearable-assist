"""[벤치 ■1] 포즈 추정 검증 오버레이 + 벤치 기하 판독용 격자.

프레임 위에 랜드마크·세그먼트·각도를 얹고, 픽셀 격자를 그려 벤치 치수를 읽는다.
스케일 기준: 어깨–발목 픽셀 거리 ↔ 모델의 같은 거리.
"""
import os
import sys
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VID_FRAMES = '/data/suit_bench/frames'
POSE = '/data/suit_bench/pose_raw.json'
OUT = '/data/suit_bench/overlay'
os.makedirs(OUT, exist_ok=True)
KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
PANEL_X = {'nosuit': 0, 'active': 1280}
PW = 640


def draw(panel, t, out_png, grid=True):
    d0 = json.load(open(POSE))
    R = d0['res'][panel]
    i = int(round(t * d0['fps']))
    r = R[min(i, len(R) - 1)]
    fi = int(round(t * 4)) + 1          # frames/ 는 4 fps 로 추출
    src = f'{VID_FRAMES}/f_{fi:03d}.png'
    im = Image.open(src).convert('RGB')
    im = im.crop((PANEL_X[panel], 0, PANEL_X[panel] + PW, im.height))
    dr = ImageDraw.Draw(im)
    if grid:
        for x in range(0, PW, 50):
            dr.line([(x, 0), (x, im.height)], fill=(70, 70, 70), width=1)
            dr.text((x + 2, 2), str(x), font=ImageFont.truetype(KF, 11),
                    fill=(150, 150, 150))
        for y in range(0, im.height, 50):
            dr.line([(0, y), (PW, y)], fill=(70, 70, 70), width=1)
            dr.text((2, y + 2), str(y), font=ImageFont.truetype(KF, 11),
                    fill=(150, 150, 150))
    if r:
        pts = {k: tuple(r[k]) for k in ('sh', 'hip', 'kn', 'an', 'wr')}
        for a, b, c in (('sh', 'hip', '#ff3b30'), ('hip', 'kn', '#34c759'),
                        ('kn', 'an', '#0a84ff'), ('sh', 'wr', '#ffd60a')):
            dr.line([pts[a], pts[b]], fill=c, width=5)
        for k, p in pts.items():
            dr.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill='#ffffff',
                       outline='#000000', width=2)
            dr.text((p[0] + 10, p[1] - 8), k, font=ImageFont.truetype(KF, 16),
                    fill='#ffffff')
        tilt = 180.0 - (r['trunk'] if r['trunk'] > 0 else r['trunk'] + 360)
        cap = (f"t={t:.2f}s  몸통 경사 {tilt:+.1f}°  고관절 {r['hip_flex']:.1f}°  "
               f"무릎 {r['knee']:.1f}°  대퇴 {r['thigh']:.1f}°")
        dr.rectangle([0, im.height - 34, PW, im.height], fill=(15, 15, 15))
        dr.text((8, im.height - 28), cap, font=ImageFont.truetype(KF, 17),
                fill=(255, 255, 255))
    im.save(out_png)
    return out_png, r


if __name__ == '__main__':
    for panel, t in (('nosuit', 3.0), ('active', 3.0), ('active', 5.8),
                     ('active', 0.0)):
        p, r = draw(panel, t, f'{OUT}/{panel}_{t:.1f}.png')
        print('SAVED', p)
