from PIL import Image, ImageDraw, ImageFont
import os, json
COMP="/tmp/cmp_render/squat_vcomp"
RENDER="/tmp/cmp_render/squatbw_vout"
meta=json.load(open(os.path.join(RENDER,"meta.json"))); N=len(meta)
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"squat_public_keyframes_grid.png")
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)
targets=[(0.0,"준비"),(1.25,"내려가는 중"),(2.75,"가장 깊이"),(3.75,"올라오는 중"),(5.0,"복귀")]
def near(t): return min(range(N),key=lambda i:abs(meta[i]['t']-t))
idxs=[(near(t),lab) for t,lab in targets]
PW=520
frames=[Image.open(os.path.join(COMP,f"v{idx:04d}.png")).convert("RGB") for idx,_ in idxs]
ph=int(frames[0].height*PW/frames[0].width)
sca=[im.resize((PW,ph)) for im in frames]
PAD=10; TOP=58
W=5*PW+6*PAD; H=TOP+ph+PAD+10
cv=Image.new("RGB",(W,H),(24,26,30)); d=ImageDraw.Draw(cv)
d.text((PAD,10),"일반인용 squat(쪼그려 앉기) 키프레임 — 슈트 없음 | 슈트 착용 (좌우) + 허리 근육 확대 인셋",fill=(255,255,255),font=F(24,True))
d.text((PAD,38),"허리 굽힐수록 '슈트 없음' 허리 인셋이 빨개짐(힘듦). '슈트 착용'은 초록 유지(편함).",fill=(255,185,95),font=F(15))
for ci,((idx,lab),im) in enumerate(zip(idxs,sca)):
    x=PAD+ci*(PW+PAD); cv.paste(im,(x,TOP))
    d.rectangle([x,TOP,x+PW,TOP+ph],outline=(80,82,90))
    d.text((x+6,TOP+2),f"{lab}  ↓{meta[idx]['peak_red']:.0f}%",fill=(255,255,0),font=F(16,True))
cv.save(OUT); print("SAVED",OUT,cv.size)
