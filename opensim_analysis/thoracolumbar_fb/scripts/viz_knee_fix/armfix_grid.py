import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, matplotlib.image as mpimg, numpy as np
from matplotlib import font_manager as fm
for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc','/usr/share/fonts/truetype/noto/NotoSansCJKkr-Regular.otf']:
    try: fm.fontManager.addfont(p); plt.rcParams['font.family']='Noto Sans CJK KR'; break
    except: pass
plt.rcParams['axes.unicode_minus']=False
fig=plt.figure(figsize=(15,5.4)); gs=fig.add_gridspec(1,3,width_ratios=[1.05,1.05,1.2])
# --- panel 1: ES peak def vs fix ---
ax=fig.add_subplot(gs[0,0])
mots=['stoop','squat']; defp=[31.9,27.4]; fixp=[31.6,26.3]
x=np.arange(2); w=0.36
ax.bar(x-w/2,defp,w,label='결함(def)',color='#c0504d'); ax.bar(x+w/2,fixp,w,label='수정(fix)',color='#4472c4')
for i in range(2):
    ax.text(x[i]-w/2,defp[i]+0.4,f'{defp[i]:.1f}',ha='center',fontsize=10)
    ax.text(x[i]+w/2,fixp[i]+0.4,f'{fixp[i]:.1f}',ha='center',fontsize=10)
    ax.text(x[i],max(defp[i],fixp[i])+2.2,f'Δ{fixp[i]-defp[i]:+.1f}%p',ha='center',fontsize=11,color='#2a6a2a',weight='bold')
ax.set_xticks(x); ax.set_xticklabels(['stoop v5','squat v1']); ax.set_ylabel('ES peak activation (%)'); ax.set_ylim(0,38)
ax.set_title('[2] 왼팔 축수정 전후 ES peak (F0 baseline)\n동일 파이프라인, M1 공통 → Δ=순수 팔수정',fontsize=11); ax.legend(fontsize=9)
# --- panel 2: symmetry / invariants text ---
ax2=fig.add_subplot(gs[0,1]); ax2.axis('off')
txt=("[1] 축 미러 수정 (7축)\n"
     "  shoulder_L: elv, rot, elv_angle (3)\n"
     "  radius_hand_l: wrist_dev, wrist_flex (2)\n"
     "  sterL_clavL_jnt: clav_prot, clav_elev (2)★\n"
     "  규칙 (−ax,−ay,az)  [elbow_l 검증됨]\n\n"
     "  ✅ 좌우 대칭 MAX 0.00cm (4자세, clav포함)\n"
     "  ✅ 질량 77.969kg 동일 · COM 동일\n"
     "  ✅ 620근육 · 169좌표 · mesh 불변\n"
     "  ✅ 중립 왼손 0.000cm → 정지분석 무영향\n\n"
     "[영향 범위]\n"
     "  박스(23%): 왼팔=0 → ΔES=0 (skip)\n"
     "  stoop/squat: clav 미구동 → SO 유효\n"
     "  max ΔES = −1.1%p (squat) < 5%p\n"
     "  → headline 32%/47% 실질 불변")
ax2.text(0.02,0.98,txt,va='top',ha='left',fontsize=10.3,
         bbox=dict(boxstyle='round',fc='#f4f4f4',ec='#888'))
ax2.set_title('[1] 수정 범위 + 불변/영향',fontsize=11)
# --- panel 3: render ---
ax3=fig.add_subplot(gs[0,2]); ax3.axis('off')
ax3.imshow(mpimg.imread('opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/armfix_no_vizmirror.png'))
ax3.set_title('[3] viz-mirror 대체 (왼팔 독립구동)\n박스 파지 z-대칭 0.29cm · 양팔 대칭',fontsize=11)
fig.suptitle('왼팔 관절축 결함 수정 — [1]수정+검증 [2]stoop/squat ES 재측정 [3]viz-mirror 대체  (2026-07-27)',fontsize=12.5,weight='bold')
fig.tight_layout(rect=[0,0,1,0.94])
out='opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/armfix_results_grid.png'
fig.savefig(out,dpi=115); print('SAVED',out)
