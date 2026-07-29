"""S14/S16용 키프레임 스트립 재생성.

기존 *_public_keyframes_grid.png은 노란 구간 라벨이 프레임 제목 위에 겹쳐 찍혀
양쪽 다 판독 불가 + 개발 노트 헤더 포함. 영상에서 프레임을 직접 뽑아
겹침 없는 라벨을 새로 얹는다.
"""
import subprocess, os
from PIL import Image, ImageDraw, ImageFont

MEDIA = '/data/opensim_results/ppt_media'
KF = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
CROP = (8, 88, 995, 720)          # 프레임 내 번인 제목·범례 제외, 2패널만

JOBS = {   # 2x2 배치 — 가로 7:1 스트립은 슬라이드 칸에서 너무 납작해짐
    'squat': [(0.55, '준비'), (1.90, '내려가는 중'), (3.25, '가장 깊이'),
              (5.10, '올라오는 중')],
    'stoop': [(0.70, '준비'), (2.45, '굽히는 중'), (4.10, '최대 굴곡'),
              (5.80, '펴는 중')],
}
HILITE = {'squat': 2, 'stoop': 2}   # 강조할 프레임 index
COLS = 2


def frame(key, t, out):
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', f'{MEDIA}/{key}_ppt.mp4',
                    '-ss', str(t), '-vframes', '1', out], check=True)


for key, marks in JOBS.items():
    crops = []
    for i, (t, _) in enumerate(marks):
        tmp = f'/tmp/_kf_{key}_{i}.png'
        frame(key, t, tmp)
        crops.append(Image.open(tmp).crop(CROP))
    W, H = crops[0].size
    PAD, LAB, GAP = 14, 52, 16
    rows = (len(crops) + COLS - 1) // COLS
    cell_h = H + LAB + GAP
    out = Image.new('RGB', (COLS * W + (COLS - 1) * GAP + 2 * PAD,
                            rows * cell_h - GAP + 2 * PAD), (24, 26, 30))
    d = ImageDraw.Draw(out)
    f_lab = ImageFont.truetype(KF, 38)
    for i, im in enumerate(crops):
        x = PAD + (i % COLS) * (W + GAP)
        y = PAD + (i // COLS) * cell_h
        out.paste(im, (x, y + LAB))
        col = (126, 217, 160) if i == HILITE[key] else (215, 219, 224)
        txt = marks[i][1]
        tw = d.textbbox((0, 0), txt, font=f_lab)[2]
        d.text((x + (W - tw) / 2, y + 4), txt, font=f_lab, fill=col)
        if i == HILITE[key]:
            d.rectangle([x - 3, y + LAB - 3, x + W + 2, y + LAB + H + 2],
                        outline=(126, 217, 160), width=3)
    p = f'{MEDIA}/kf_{key}.png'
    out.save(p)
    print(p, out.size, round(out.width / out.height, 2))

for f in os.listdir('/tmp'):
    if f.startswith('_kf_'):
        os.remove('/tmp/' + f)
