"""Pilot v2: SAME structure (knee fix bones + ES path-point curves), only colormap changed:
per-muscle activation, inferno colormap, VMAX=OFF peak, gamma lift + emission glow."""
import bpy, os, json, mathutils

FRAME="/tmp/cmp_render/frames/frame_2.500.json"
OSIM="/tmp/cmp_render/tlfb/TLFB.osim"
OUT="/tmp/cmp_render/pilot_v3"; os.makedirs(OUT,exist_ok=True)
RAD=0.006
D=json.load(open(FRAME))
VMAX=max(v['off'] for v in D['muscles'].values())   # OFF peak = 0.311
AMIN=0.03                                            # below this = inactive (dim)
GAMMA=0.85
VDIFF=max(0.05, max(v['off']-v['on'] for v in D['muscles'].values()))  # ~0.09
DGAMMA=0.75
print("[scale] VMAX(OFFpeak)=",round(VMAX,3),"AMIN=",AMIN,"VDIFF=",round(VDIFF,3))

# inferno anchors (t, r,g,b)
INF=[(0.00,0.001,0.000,0.014),(0.13,0.122,0.047,0.281),(0.25,0.282,0.062,0.408),
     (0.38,0.451,0.122,0.412),(0.50,0.612,0.182,0.353),(0.63,0.767,0.275,0.250),
     (0.75,0.894,0.412,0.145),(0.88,0.969,0.620,0.130),(1.00,0.988,0.998,0.645)]
def inferno(x):
    x=max(0.0,min(1.0,x))
    for i in range(len(INF)-1):
        t0,r0,g0,b0=INF[i]; t1,r1,g1,b1=INF[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0
            return (r0+(r1-r0)*f, g0+(g1-g0)*f, b0+(b1-b0)*f)
    return INF[-1][1:]
def actcolor(a):
    n=max(0.0,min(1.0,(a-AMIN)/(VMAX-AMIN)))**GAMMA
    return inferno(n), n
# 'hot' map for the difference panel (black->red->orange->yellow->white)
HOT=[(0.00,0.02,0.0,0.0),(0.30,0.62,0.04,0.0),(0.55,0.95,0.32,0.02),
     (0.80,1.0,0.78,0.12),(1.00,1.0,1.0,0.92)]
def hot(x):
    x=max(0.0,min(1.0,x))
    for i in range(len(HOT)-1):
        t0,r0,g0,b0=HOT[i]; t1,r1,g1,b1=HOT[i+1]
        if x<=t1:
            f=(x-t0)/(t1-t0) if t1>t0 else 0
            return (r0+(r1-r0)*f,g0+(g1-g0)*f,b0+(b1-b0)*f)
    return HOT[-1][1:]
def diffcolor(d):
    n=max(0.0,min(1.0,d/VDIFF))**DGAMMA
    return hot(n), n

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
    try: m.show_transparent_back=False
    except Exception: pass
    return m

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM)
bpy.context.view_layer.update()
wm=white_mat()
for o in list(bpy.data.objects):
    t=o.get('MuSkeMo_type')
    if o.type=='MESH' and t=='GEOMETRY':
        if o.name in D['mesh']:
            o.parent=None; o.matrix_world=mat_from(D['mesh'][o.name]['R'],D['mesh'][o.name]['p'])
        o.data.materials.clear(); o.data.materials.append(wm); o.hide_render=False
    elif o.type=='CURVE' or t in ('WRAP','LANDMARK','JOINT'):
        bpy.data.objects.remove(o, do_unlink=True)
for coll in bpy.data.collections:
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame','muscle']):
        coll.hide_render=True

mcoll=bpy.data.collections.new("ES_muscles"); bpy.context.scene.collection.children.link(mcoll)
muscle_objs={}
for nm,md in D['muscles'].items():
    pts=md['pts']
    if len(pts)<2: continue
    cu=bpy.data.curves.new(nm,'CURVE'); cu.dimensions='3D'
    sp=cu.splines.new('POLY'); sp.points.add(len(pts)-1)
    for i,(x,y,z) in enumerate(pts): sp.points[i].co=(x,y,z,1)
    cu.bevel_depth=RAD; cu.use_fill_caps=True
    ob=bpy.data.objects.new(nm,cu); mcoll.objects.link(ob)
    mat=bpy.data.materials.new("m_"+nm); mat.use_nodes=True
    ob.data.materials.append(mat); muscle_objs[nm]=(ob,mat)

def recolor(cond):
    for nm,(ob,mat) in muscle_objs.items():
        if cond=='diff':
            d=max(0.0, D['muscles'][nm]['off']-D['muscles'][nm]['on'])
            col,n=diffcolor(d)
        else:
            col,n=actcolor(D['muscles'][nm][cond])
        b=mat.node_tree.nodes.get("Principled BSDF")
        b.inputs["Base Color"].default_value=(col[0],col[1],col[2],1)
        for en in ("Emission Color","Emission"):
            if en in b.inputs:
                try: b.inputs[en].default_value=(col[0],col[1],col[2],1)
                except: pass
        if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.25+2.8*n

mn=[1e9]*3; mx=[-1e9]*3
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE') and not o.hide_render:
        for v in o.bound_box:
            wv=o.matrix_world@mathutils.Vector(v)
            for i in range(3): mn[i]=min(mn[i],wv[i]); mx[i]=max(mx[i],wv[i])
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2
xext=mx[0]-mn[0]; yext=mx[1]-mn[1]; zext=mx[2]-mn[2]
RESX,RESY=760,1050
# side view sees X(horiz)&Y(vert); back view sees Z(horiz)&Y(vert). cover both with margin.
ortho=max(yext, xext*RESY/RESX, zext*RESY/RESX)*1.12
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=760; sc.render.resolution_y=1050
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value=(0.11,0.12,0.14,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),4.0),((cx-2,cy+1,cz+3),3.0),((cx,cy-1,cz-3),2.0)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'
cam.data.clip_start=0.01; cam.data.clip_end=60
VIEWS={"side":(cx,cy,cz+5),"back":(cx-5,cy,cz)}
for cond in ['off','on','diff']:
    recolor(cond)
    for vn,loc in VIEWS.items():
        cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
        fp=os.path.join(OUT,f"pilot_{cond}_{vn}.png"); sc.render.filepath=fp
        bpy.ops.render.render(write_still=True); print("[render]",cond,vn)
print("PILOT_V3_DONE")
