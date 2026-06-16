from PIL import Image, ImageDraw, ImageFont
import os, numpy as np
SRC="/tmp/cmp_render/squat_pose"
OUTDIR="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/literature_review"
OUT=os.path.join(OUTDIR,"squat_motion_verify_grid.png")
def F(s,b=False): return ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"%("Bold" if b else "Regular"),s)
def crop(p,pad=14):
    im=Image.open(p).convert("RGB"); a=np.asarray(im).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>26; ys,xs=np.where(m)
    return im.crop((max(0,xs.min()-pad),max(0,ys.min()-pad),min(im.width,xs.max()+pad),min(im.height,ys.max()+pad)))
PH=620
def sc(im): return im.resize((int(im.width*PH/im.height),PH))
side=sc(crop(os.path.join(SRC,"squat_side.png"))); front=sc(crop(os.path.join(SRC,"squat_front.png")))
PAD=20; TOP=120; RGT=470
W=side.width+front.width+3*PAD+RGT; H=TOP+PH+PAD+30
BG=(32,34,40); cv=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(cv)
d.text((PAD,16),"맨몸 squat 동작 검증 — squat_synthetic_v1 (가장 깊이, t=2.0s)", fill=(255,255,255),font=F(30,True))
d.text((PAD,58),"CHEOL HOON님 가이드라인: 발바닥 고정 · 상체 편 채(허리 안 숙임) · 무릎만 굽힘 · 양팔 앞으로 · 균형", fill=(200,205,215),font=F(16))
for ci,(im,lab) in enumerate([(side,"옆 (SIDE)"),(front,"앞 (FRONT)")]):
    x=PAD+ci*(side.width+PAD) if ci==0 else PAD+side.width+PAD
    cv.paste(im,(x,TOP)); d.rectangle([x,TOP,x+im.width,TOP+PH],outline=(110,112,120),width=2)
    d.text((x+8,TOP-26),lab,fill=(255,255,0),font=F(18,True))
# checklist
cx0=PAD+side.width+front.width+2*PAD+10; cy=TOP+10
d.text((cx0,cy-2),"동작 검증 체크리스트",fill=(255,255,255),font=F(20,True))
checks=[
 ("발바닥 전체 지면 고정 (들림 X)","발 평평 calcn–mtp Y차 ≈0, 접지 −0.907 m"),
 ("상체 편 채 (허리 안 숙임)","lumbar/L5_S1 = 0° (척추 중립). stoop과 결정적 차이"),
 ("무릎만 굽혀 내려감 (deep flexion)","knee 100° · hip 95° · 골반 하강 0.32 m"),
 ("양팔 앞으로 뻗음","shoulder elev 85°, 전방 (균형 counterweight)"),
 ("균형 (COM이 발 위)","COM x 0.21 ∈ [heel 0.14, toe 0.32] → 지지면 내"),
 ("진짜 squat (박스/stoop 아님)","곧은 등 + 깊은 무릎 = 쪼그려 앉기"),
]
yy=cy+34
for t,sub in checks:
    d.text((cx0,yy),"✓",fill=(120,230,150),font=F(20,True))
    d.text((cx0+28,yy),t,fill=(235,235,235),font=F(16,True))
    d.text((cx0+28,yy+22),sub,fill=(170,175,185),font=F(12))
    yy+=58
d.text((cx0,yy+4),"박스 하중 없음 (맨몸). .osim 불변, per-frame knee fix.",fill=(150,200,170),font=F(13))
cv.save(OUT); print("SAVED",OUT,cv.size)
