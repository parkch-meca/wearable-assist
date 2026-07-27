import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt, numpy as np, opensim as osim
from matplotlib import font_manager as fm
for p in ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
    try: fm.fontManager.addfont(p); plt.rcParams['font.family']='Noto Sans CJK JP'; break
    except: pass
plt.rcParams['axes.unicode_minus']=False
t=osim.TimeSeriesTable('/data/gait_motion/gait_retarget_v2.mot'); T=np.array(list(t.getIndependentColumn()))
def c(n): return np.array([t.getDependentColumn(n)[i] for i in range(t.getNumRows())])
def jumps(x): d=np.abs(np.diff(x)); return d.max()  # max frame-to-frame deg change
fig,ax=plt.subplots(2,2,figsize=(14,8))
# arm swing
ax[0,0].plot(T,c('elv_angle_r'),'b-o',ms=3,label='elv_angle_R (팔 스윙)')
ax[0,0].plot(T,c('elv_angle_l'),'r-o',ms=3,label='elv_angle_L')
ax[0,0].axhline(0,color='k',lw=0.5); ax[0,0].set_title(f'팔 스윙 elv_angle (contralateral)  최대 프레임간변화 R={jumps(c("elv_angle_r")):.1f}° L={jumps(c("elv_angle_l")):.1f}°')
ax[0,0].set_ylabel('deg'); ax[0,0].legend(fontsize=9); ax[0,0].grid(alpha=0.3)
# elbow/wrist (should be flat -> no artifact)
for nm,col in [('elbow_flexion_r','b'),('elbow_flexion_l','r'),('wrist_flex_r','c'),('wrist_dev_r','m'),('pro_sup_r','g'),('shoulder_elv_r','orange')]:
    ax[0,1].plot(T,c(nm),col,label=nm,lw=1.5)
ax[0,1].set_title('팔꿈치(25° 고정)·손목·shoulder_elv(0) — 평탄해야(회전 아티팩트 없음)'); ax[0,1].set_ylabel('deg'); ax[0,1].legend(fontsize=8); ax[0,1].grid(alpha=0.3)
# legs
ax[1,0].plot(T,c('hip_flexion_r'),'b-',label='hip_flex_R'); ax[1,0].plot(T,c('hip_flexion_l'),'r-',label='hip_flex_L')
ax[1,0].plot(T,c('knee_angle_r'),'b--',label='knee_R'); ax[1,0].plot(T,c('knee_angle_l'),'r--',label='knee_L')
ax[1,0].set_title('다리 (hip/knee, 직접 매핑)'); ax[1,0].set_ylabel('deg'); ax[1,0].legend(fontsize=8); ax[1,0].grid(alpha=0.3); ax[1,0].set_xlabel('t (s)')
# arm vs leg contralateral: overlay elv_angle_r vs hip_flexion_r (should be anti-phase)
ax[1,1].plot(T,c('elv_angle_r')/ (np.abs(c('elv_angle_r')).max()),'b-',label='팔R (정규화)')
ax[1,1].plot(T,c('hip_flexion_r')/(np.abs(c('hip_flexion_r')).max()),'g-',label='다리R hip (정규화)')
ax[1,1].set_title('우팔 vs 우다리 — 반대위상(contralateral) 확인'); ax[1,1].legend(fontsize=9); ax[1,1].grid(alpha=0.3); ax[1,1].set_xlabel('t (s)'); ax[1,1].axhline(0,color='k',lw=0.5)
fig.suptitle('[3] 걷기 retarget v2 — 각도 시계열 (아티팩트/급점프 점검)',fontsize=13,weight='bold')
fig.tight_layout(rect=[0,0,1,0.96])
fig.savefig('/data/wearable-assist/opensim_analysis/thoracolumbar_fb/docs/images/phase2_box/gait_v2_angles.png',dpi=115)
# report jump metrics
print('=== 프레임간 최대 변화(급점프 점검) ===')
for nm in ['elv_angle_r','elv_angle_l','hip_flexion_r','knee_angle_r','ankle_angle_r','L5_S1_FE','wrist_flex_r']:
    print(f'  {nm:16s}: max Δframe = {jumps(c(nm)):.2f}°')
print('SAVED gait_v2_angles.png')
