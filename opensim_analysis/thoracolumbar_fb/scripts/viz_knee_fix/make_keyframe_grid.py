"""Keyframe grid: 5 phases x (DIFF side panel) from rendered frames, for chat verification."""
from PIL import Image, ImageDraw, ImageFont
import os, json
RENDER="/tmp/cmp_render/vout"
meta=json.load(open(os.path.join(RENDER,"meta.json")))
N=len(meta)
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)
# pick frames nearest motion times
targets=[(0.0,"직립"),(1.25,"하강"),(2.75,"Hold peak"),(3.75,"상승"),(5.0,"직립 복귀")]
def nearest(t): return min(range(N), key=lambda i:abs(meta[i]['t']-t))
idxs=[(nearest(t),lab) for t,lab in targets]
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"stoop_video_keyframes_grid.png")
sample=Image.open(os.path.join(RENDER,f"f{idxs[0][0]:04d}_diff_side.png")); pw,ph=sample.size
sc=0.62; PW,PH=int(pw*sc),int(ph*sc); PAD=10; TOP=92
W=5*PW+6*PAD; H=TOP+2*PH+3*PAD+70
cv=Image.new("RGB",(W,H),(20,22,26)); d=ImageDraw.Draw(cv)
d.text((PAD,8),"Stoop 들기 본 동영상 키프레임 — 슈트 효과(DIFF) 시간 변화", fill=(255,255,255), font=F(22,True))
d.text((PAD,42),"상=DIFF side (슈트가 줄인 ES 활성도, hot 0→0.09)  ·  하=DIFF back  ·  하강할수록 효과(빛) 커짐", fill=(255,180,90), font=F(14))
for ci,(idx,lab) in enumerate(idxs):
    x=PAD+ci*(PW+PAD); m=meta[idx]
    for ri,view in enumerate(['side','back']):
        y=TOP+ri*(PH+PAD)
        fp=os.path.join(RENDER,f"f{idx:04d}_diff_{view}.png")
        im=Image.open(fp).convert("RGB").resize((PW,PH)); cv.paste(im,(x,y))
        d.rectangle([x,y,x+PW,y+PH],outline=(220,120,30),width=2)
    d.text((x+6,TOP-24),f"{lab}  t={m['t']:.1f}s",fill=(255,255,0),font=F(14,True))
    d.text((x+6,TOP+2*PH+PAD+6),f"ES peak −{m['peak_red']:.0f}%",fill=(255,170,80),font=F(14,True))
cv.save(OUT); print("SAVED",OUT,cv.size)
