"""Video-ready: knee-fixed bones + spine/ES muscles (6mm). Visualization only."""
import bpy, os, json, mathutils
OSIM="/data/opensim_models/ThoracolumbarFB/Fullbody_TLModels_v2.0_OS4x/MaleFullBodyModel_v2.0_OS4_modified_no_coupler.osim"
MX=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"tlfb_mesh_xforms.json")))
OUT="/tmp/knee_fixed_out"; os.makedirs(OUT,exist_ok=True)
RES_X,RES_Y=820,1150
RADIUS=0.006
SPINE=['il_','iliocost','longissi','ltpl','ltpt','long_col','mf_','multifidus',
       'deepmult','supmult','ql_','ps_','semi','splen']
def is_spine(n):
    n=n.lower(); return any(n.startswith(t) or ('_'+t) in n for t in SPINE)
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
    b.inputs["Base Color"].default_value=(0.95,0.95,0.93,1)
    if "Roughness" in b.inputs: b.inputs["Roughness"].default_value=0.5
    for en in ("Emission Color","Emission"):
        if en in b.inputs:
            try: b.inputs[en].default_value=(0.85,0.85,0.82,1)
            except: pass
    if "Emission Strength" in b.inputs: b.inputs["Emission Strength"].default_value=0.3
    return m

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
sc=bpy.context.scene; sc.muskemo.muscle_visualization_radius=RADIUS
imp=getattr(bpy.ops,'import'); imp.import_opensim_model(filepath=OSIM)
bpy.context.view_layer.update()
wm=white_mat()
for o in list(bpy.data.objects):
    t=o.get('MuSkeMo_type')
    if o.type=='MESH' and t=='GEOMETRY':
        if o.name in MX:
            o.parent=None; o.matrix_world=mat_from(MX[o.name]['R'],MX[o.name]['p'])
        o.hide_render=False; o.data.materials.clear(); o.data.materials.append(wm)
    elif o.type=='CURVE':
        o.hide_render = not is_spine(o.name)
    elif t in ('WRAP','LANDMARK','JOINT'):
        o.hide_render=True
for coll in bpy.data.collections:
    if any(k in coll.name.lower() for k in ['wrap','joint cent','landmark','frame']):
        coll.hide_render=True
bpy.context.view_layer.update()
mn=[1e9]*3; mx=[-1e9]*3
for o in bpy.data.objects:
    if o.type=='MESH' and not o.hide_render:
        for v in o.bound_box:
            wv=o.matrix_world@mathutils.Vector(v)
            for i in range(3): mn[i]=min(mn[i],wv[i]); mx[i]=max(mx[i],wv[i])
cx=(mn[0]+mx[0])/2; cy=(mn[1]+mx[1])/2; cz=(mn[2]+mx[2])/2; ortho=(mx[1]-mn[1])*1.10
sc.render.engine='BLENDER_EEVEE_NEXT'; sc.render.resolution_x=RES_X; sc.render.resolution_y=RES_Y
sc.render.image_settings.file_format='PNG'; sc.world.use_nodes=True
bg=sc.world.node_tree.nodes.get('Background')
if bg: bg.inputs[0].default_value=(0.10,0.11,0.13,1); bg.inputs[1].default_value=1.0
for loc,en in [((cx+2,cy+2,cz+3),6.0),((cx-2,cy+1,cz+3),4.5),((cx,cy-1,cz-3),3.0)]:
    bpy.ops.object.light_add(type='SUN',location=loc); bpy.context.object.data.energy=en
VIEWS={"side":(cx,cy,cz+5),"back":(cx-5,cy,cz),"oblique":(cx+3.5,cy+0.7,cz+3.5)}
bpy.ops.object.camera_add(location=(0,0,0)); cam=bpy.context.object; sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=ortho; cam.data.sensor_fit='VERTICAL'
cam.data.clip_start=0.01; cam.data.clip_end=60
for vn,loc in VIEWS.items():
    cam.location=mathutils.Vector(loc); cam.rotation_euler=look_at(loc,(cx,cy,cz))
    fp=os.path.join(OUT,f"TLFB_fixed_spine_{vn}.png"); sc.render.filepath=fp
    bpy.ops.render.render(write_still=True); print("[render]",vn)
print("FIXED_SPINE_DONE")
