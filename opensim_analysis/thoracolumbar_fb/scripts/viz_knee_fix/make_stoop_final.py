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
fig=plt.figure(figsize=(16,9.4)); gs=fig.add_gridspec(2,3,height_ratios=[1,1],width_ratios=[1,1,1.5],wspace=0.05,hspace=0.14)
fig.suptitle("박스 옆손바닥 파지 완성 ✅ — 자연 stoop + 팔꿈치 몸옆(akimbo 해소) + M1 견갑 · 독립검증 통과",
             fontsize=14,fontweight='bold',y=0.995,color='#0a6')
ax=fig.add_subplot(gs[0,0]); ax.imshow(crop("/tmp/cmp_render/interf/stoop1_front.png")); ax.axis('off'); ax.set_title("이전 앞 — 팔꿈치 akimbo(닭날개) ❌",fontsize=9.5,fontweight='bold',color='#a00')
ax=fig.add_subplot(gs[0,1]); ax.imshow(crop("/tmp/cmp_render/interf/stoop5_front.png")); ax.axis('off'); ax.set_title("완성 앞 — 팔꿈치 몸옆·아래 ✅",fontsize=9.5,fontweight='bold',color='#0a6')
ax=fig.add_subplot(gs[1,0]); ax.imshow(crop("/tmp/cmp_render/interf/stoop5_side.png")); ax.axis('off'); ax.set_title("완성 옆 — 다리곧게+허리굽힘 자연 stoop ✅",fontsize=9.5,fontweight='bold',color='#0a6')
ax=fig.add_subplot(gs[1,1]); ax.imshow(crop("/tmp/cmp_render/interf/stoop5_front.png")); ax.axis('off'); ax.set_title("완성 앞 — 양손 대칭 옆면 파지",fontsize=9.5,fontweight='bold')
ax=fig.add_subplot(gs[:,2]); ax.axis('off')
ax.text(0,1.0,"[완성된 자세]",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.945,f"• 자연 stoop: 무릎 {C['knee']:.0f}°(곧게) + hip hinge {C['hip']:.0f}°\n"
               f"  + 골반틸트 {C['pelvis_tilt']:.0f}° + 요추 {C['lumbar_tot']:.0f}°, 등 {D['back_angle']:.0f}°\n"
               f"• 팔꿈치: 어깨 아래 20cm 내려옴(akimbo 해소)\n"
               f"  박스 폭 파지 위해 전완 약간 벌어짐(자연)\n"
               f"• M1 견갑 protraction 도달 보조\n"
               f"• 손바닥 옆면 오차 {D['palm_err_cm']:.1f}cm 밀착, 발끝 박스앞 정렬",fontsize=9.3,va='top')
ax.text(0,0.70,"[독립검증 통과 — 2단계]",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.645,"1차(자세): 자연 stoop SOLVED 6/6 (무릎곧게·hip hinge·\n"
               "         손밀착·간섭0·대칭·발접지)\n"
               "2차(팔꿈치): akimbo 해소 SOLVED (팔꿈치 몸옆 아래,\n"
               "         박스 옆면 자연 파지)",fontsize=9.3,va='top',color='#225')
ax.text(0,0.50,"[정량 안전 — M1 regression]",fontsize=12.5,fontweight='bold',color='#0a6',va='top')
ax.text(0,0.445,"견갑 protraction 추가 stoop SO regression:\n"
               "MAX ΔES 0.029%p → stoop/squat headline 불변.",fontsize=9.3,va='top')
ax.text(0,0.35,"[여정 요약]",fontsize=12.5,fontweight='bold',color='#225',va='top')
ax.text(0,0.295,"6회 실패(웅크림·등세움) → 사용자 정정 '무릎높이=stoop'\n"
               "→ 무릎세움+허리굽힘 → 팔꿈치 몸옆 → 완성.\n"
               "biomechanics 우선(실제 동작) 원칙이 돌파구.",fontsize=9.3,va='top')
ax.text(0,0.17,"[다음]",fontsize=12,fontweight='bold',color='#7a0000',va='top')
ax.text(0,0.115,"사용자 확인 후 SO(박스 20kg + suit 조건별 ES 부하).\n자동 SO 미실행.",fontsize=9.3,va='top',color='#333')
OUT="/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/box_table30_FINAL_grid.png"
fig.savefig(OUT,dpi=110,bbox_inches='tight',facecolor='white'); print("SAVED",OUT)
