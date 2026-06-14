"""Full stoop video render. per-frame knee fix + ES path-point curves + activation/diff color.
Fixed camera (global bbox). Renders OFF/ON/DIFF x side/back per frame. Visualization only.
Usage: blender -b --python render_video.py -- <frames_dir> <out_dir>"""
import bpy, os, json, glob, sys, mathutils

argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
FRAMES_DIR=argv[0] if argv else "/tmp/cmp_render/test_frames"
OUT=argv[1] if len(argv)>1 else "/tmp/cmp_render/test_out"
os.makedirs(OUT,exist_ok=True)
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"
RAD=0.006
PANEL_X,PANEL_Y=460,620

files=sorted(glob.glob(os.path.join(FRAMES_DIR,"frame_*.json")), key=lambda p:float(os.path.basename(p)[6:-5]))
frames=[json.load(open(f)) for f in files]
print("[frames]",len(frames))

# global color scales (fixed across video) from ALL frames
alloff=[v['off'] for fr in frames for v in fr['muscles'].values()]
allon =[v['on'] for fr in frames for v in fr['muscles'].values()]
alldiff=[max(0.0,v['off']-v['on']) for fr in frames for v in fr['muscles'].values()]
VMAX=max(alloff); AMIN=0.03; GAMMA=0.85
VDIFF=max(0.05, max(alldiff)); DGAMMA=0.75
print("[scale] VMAX",round(VMAX,3),"VDIFF",round(VDIFF,3))

INF=[(0.00,0.001,0.000,0.014),(0.13,0.122,0.047,0.281),(0.25,0.282,0.062,0.408),
     (0.38,0.451,0.122,0.412),(0.50,0.612,0.182,0.353),(0.63,0.767,0.275,0.250),
     (0.75,0.894,0.412,0.145),(0.88,0.969,0.620,0.130),(1.00,0.988,0.998,0.645)]
HOT=[(0.00,0.02,0.0,0.0),(0.30,0.62,0.04,0.0),(0.55,0.95,0.32,0.02),(0.80,1.0,0.78,0.12),(1.00,1.0,1.0,0.92)]
def lut(A,x):
    x=max(0.,min(1.,x))
    for i in range(len(A)-1):
        t0,r0,g0,b0=A[i]; t1,r1,g1,b1=A[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0
            return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return A[-1][1:]
def colof(cond,m):
    if cond=='diff':
        n=max(0.,min(1.,max(0.,m['off']-m['on'])/VDIFF))**DGAMMA; return lut(HOT,n),n
    a=m[cond]; n=max(0.,min(1.,(a-AMIN)/(VMAX-AMIN)))**GAMMA; return lut(INF,n),n
def mat_from(R,p):
    return mathutils.Matrix(((R[0],R[1],R[2],p[0]),(R[3],R[4],R[5],p[1]),(R[6],R[7],R[8],p[2]),(0,0,0,1)))
def look_at(cl,t):
    cl=mathutils.Vector(cl); t=mathutils.Vector(t); f=(t-cl).normalized(); up=mathutils.Vector((0,1,0))
    r=f.cross(up); r=r if r.length>1e-6 else mathutils.Vector((1,0,0)); r.normalize(); u=r.cross(f).normalized()
    return mathutils.Matrix(((r.x,u.x,-f.x),(r.y,u.y,-f.y),(r.z,u.z,-f.z))).to_euler()
def white_mat():
    m=bpy.data.materials.get("BoneWhite")
    if m: return m
    m=bpy.data.materials.new("BoneWhite"); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(0.88,0.88,0.86,1)
    if "Roughness" in b.inputs: b.inputs["Roughness"].default_value=0.6
    if "Alpha" in b.inputs: b.inputs["Alpha"].default_value=0.30
    m.blend_method='BLEND'
    return m

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM)
bpy.context.view_layer.update()
wm=white_mat()
bone_objs={}
for o in list(bpy.data.objects):
    t=o.get('MuSkeMo_type')
    if o.type=='MESH' and t=='GEOMETRY':
        o.data.materials.clear(); o.data.materials.append(wm); o.hide_render=False
        bone_objs[o.name]=o
        if o.parent: o.parent=None
    elif o.type=='CURVE' or t in ('WRAP','LANDMARK','JOINT'):
        bpy.data.objects.remove(o, do_unlink=True)
for coll in bpy.data.collections:
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame','muscle']):
        coll.hide_render=True

# persistent materials per muscle
musc_names=list(frames[0]['muscles'].keys())
musc_mats={}
for nm in musc_names:
    mm=bpy.data.materials.new("m_"+nm); mm.use_nodes=True; musc_mats[nm]=mm
mcoll=bpy.data.collections.new("ES"); bpy.context.scene.collection.children.link(mcoll)

# global bbox over all frames (bones via per-frame transforms approximated by mesh local extents + muscle pts)
mn=[1e9]*3; mx=[-1e9]*3
for fr in frames:
    for nm,mp in fr['muscles'].items():
        for x,y,z in mp['pts']:
            mn[0]=min(mn[0],x);mn[1]=min(mn[1],y);mn[2]=min(mn[2],z)
            mx[0]=max(mx[0],x);mx[1]=max(mx[1],y);mx[2]=max(mx[2],z)
    for nm,mxf in fr['mesh'].items():
        p=mxf['p']
        for i in range(3): mn[i]=min(mn[i],p[i]); mx[i]=max(mx[i],p[i])
# pad for mesh extents
for i in range(3): mn[i]-=0.25; mx[i]+=0.25
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2
xext=mx[0]-mn[0]; yext=mx[1]-mn[1]; zext=mx[2]-mn[2]
ortho=max(yext, xext*PANEL_Y/PANEL_X, zext*PANEL_Y/PANEL_X)*1.05
print("[bbox]",[round(v,2) for v in mn],[round(v,2) for v in mx],"ortho",round(ortho,2))

sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=PANEL_X; sc.render.resolution_y=PANEL_Y
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value=(0.11,0.12,0.14,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),4.0),((cx-2,cy+1,cz+3),3.0),((cx,cy-1,cz-3),2.0)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'
cam.data.clip_start=0.01; cam.data.clip_end=60
CAMS={"side":(cx,cy,cz+6),"back":(cx-6,cy,cz)}

cur_curves=[]
def build_muscles(fr):
    global cur_curves
    for ob in cur_curves: bpy.data.objects.remove(ob, do_unlink=True)
    cur_curves=[]
    for nm,mp in fr['muscles'].items():
        pts=mp['pts']
        if len(pts)<2: continue
        cu=bpy.data.curves.new(nm,'CURVE'); cu.dimensions='3D'
        sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
        for i,(x,y,z) in enumerate(pts): sp.points[i].co=(x,y,z,1)
        cu.bevel_depth=RAD; cu.use_fill_caps=True
        ob=bpy.data.objects.new(nm,cu); mcoll.objects.link(ob)
        ob.data.materials.append(musc_mats[nm]); cur_curves.append(ob)

def recolor(fr,cond):
    for nm,mp in fr['muscles'].items():
        mm=musc_mats.get(nm)
        if mm is None: continue
        col,n=colof(cond,mp)
        b=mm.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value=(col[0],col[1],col[2],1)
        for en in ("Emission Color","Emission"):
            if en in b.inputs:
                try: b.inputs[en].default_value=(col[0],col[1],col[2],1)
                except: pass
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.25+2.8*n

meta=[]
for fi,fr in enumerate(frames):
    for nm,mxf in fr['mesh'].items():
        if nm in bone_objs: bone_objs[nm].matrix_world=mat_from(mxf['R'],mxf['p'])
    build_muscles(fr)
    # peak ES reduction %
    pairs=[(v['off'],v['on']) for v in fr['muscles'].values()]
    pk=max(pairs,key=lambda ab:ab[0]); red=100*(pk[0]-pk[1])/pk[0] if pk[0]>1e-6 else 0
    meta.append({'t':fr['t'],'peak_off':pk[0],'peak_on':pk[1],'peak_red':red})
    for cond in ['off','on','diff']:
        recolor(fr,cond)
        for vn,loc in CAMS.items():
            cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
            sc.render.filepath=os.path.join(OUT,f"f{fi:04d}_{cond}_{vn}.png")
            bpy.ops.render.render(write_still=True)
    if fi%10==0: print("[frame]",fi,"t=",round(fr['t'],2))
json.dump(meta, open(os.path.join(OUT,"meta.json"),"w"))
print("VIDEO_RENDER_DONE", len(frames),"frames")
