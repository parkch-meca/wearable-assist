import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.image as mpimg, numpy as np, json
kf="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
fm.fontManager.addfont(kf); plt.rcParams['font.family']=fm.FontProperties(fname=kf).get_name(); plt.rcParams['axes.unicode_minus']=False
def crop(p,pad=6):
    im=mpimg.imread(p); a=(im[:,:,:3]*255).astype(int); bg=a[2,2]
    m=np.abs(a-bg).sum(2)>16; ys,xs=np.where(m)
    return im[max(0,ys.min()-pad):ys.max()+pad,max(0,xs.min()-pad):xs.max()+pad]
D=json.load(open('/tmp/cmp_render/m1_frame.json'))['diag']; C=D['contrib']
fig=plt.figure(figsize=(16,9.4)); gs=fig.add_gridspec(1,3,width_ratios=[1,1,1.55],wspace=0.06)
fig.suptitle("박스 옆손바닥 파지 SOLVED ✅ — 자연 stoop(무릎 세움+허리 굽힘) + M1 견갑 · 독립검증 6/6 통과",
             fontsize=14.5,fontweight='bold',y=0.995,color='#0a6')
for i,(p,t) in enumerate([("/tmp/cmp_render/interf/stoop1_front.png","앞 — 양손 박스 옆면 대칭 파지"),
                          ("/tmp/cmp_render/interf/stoop1_side.png","옆 — 다리 곧게+허리 굽혀(hip hinge) 자연 stoop")]):
    ax=fig.add_subplot(gs[0,i]); ax.imshow(crop(p)); ax.axis('off'); ax.set_title(t,fontsize=10.5,fontweight='bold')
ax=fig.add_subplot(gs[0,2]); ax.axis('off')
ax.text(0,1.0,"[핵심 정정] 무릎 높이 박스 = stoop",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.94,"사용자 지적: 무릎 세우고 허리 굽혀 집는 게 자연.\n"
               "이전 실패=배분 거꾸로(무릎 극단 굽힘+등 세움=웅크림).",fontsize=9.6,va='top')
ax.text(0,0.83,"[관절 배분 — 반전]",fontsize=12.5,fontweight='bold',color='#225',va='top')
ax.text(0,0.77,f"무릎:      -81° (웅크림) → {C['knee']:.0f}° (곧게 세움)\n"
               f"고관절:    hip hinge {C['hip']:.0f}° + 골반틸트 {C['pelvis_tilt']:.0f}°\n"
               f"허리(요추): {C['lumbar_tot']:.0f}° 굴곡 (자연 stoop)\n"
               f"등 lean:   {D['back_angle']:.0f}° (허리 굽힘=stoop이라 정상)\n"
               f"발목:      {C['ankle']:.0f}°  · 발끝 박스 앞 정렬(유지)",fontsize=9.6,va='top')
ax.text(0,0.585,"[M1 견갑 protraction]",fontsize=12.5,fontweight='bold',color='#225',va='top')
ax.text(0,0.525,f"clav_prot 48°로 어깨 전방이동(도달 보조).\n"
               f"regression 통과: MAX ΔES 0.029%p (정량 안전).",fontsize=9.6,va='top')
ax.text(0,0.44,"[독립검증 SOLVED 6/6] ✅",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.38,"① 다리 곧게(자연 stoop, 웅크림X) ② hip hinge 허리굽힘\n"
               "③ 실루엣=사람이 낮은박스 집는 자세 ④ 손바닥 옆면 밀착\n"
               f"⑤ 다리-테이블 간섭 없음(정강이 {D['shin_gap_cm']:.0f}cm 여유)\n"
               "⑥ 좌우 대칭·발 접지·머리 자연",fontsize=9.6,va='top',color='#225')
ax.text(0,0.20,"[검증 수치]",fontsize=12,fontweight='bold',color='#225',va='top')
ax.text(0,0.145,f"palm 옆면 오차 {D['palm_err_cm']:.1f}cm(밀착), 손끝 {D['tip_err_cm']:.1f}cm.\n"
               "생성/검증 분리 유지(독립 Agent가 그림만 판정).",fontsize=9.6,va='top')
ax.text(0,0.04,"다음: 사용자 확인 후 SO(suit 효과). 자동 SO 미실행.",fontsize=10,fontweight='bold',color='#7a0000',va='top')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_table30_stoop_SOLVED_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
