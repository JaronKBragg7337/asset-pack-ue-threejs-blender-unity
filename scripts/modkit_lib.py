"""
modkit_lib -- shared geometry helpers for the ModKit_UE asset pack.
Blender 5.1.x  |  Units: 1 Blender unit = 1 metre = 100 Unreal units.

Conventions
-----------
* +X = right, +Y = forward(depth), +Z = up.
* Modular pieces have their origin at the GRID CORNER (min X, min Y, min Z)
  so they snap cleanly on Unreal's power-of-two grid.
* Props have their origin at the BASE CENTRE (centre X/Y, min Z) so they
  drop onto floors without sinking.
"""
import math
import bmesh
import bpy
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- constants
# Every dimension lives in kit_config.py -- do not hard-code sizes here.
# These are short aliases kept for readability inside the geometry code.
import kit_config as cfg

M = cfg.MODULE            # module size            (400 uu)
WALL_H = cfg.WALL_HEIGHT  # wall height            (300 uu)
WALL_T = cfg.WALL_THICKNESS
FLOOR_T = cfg.FLOOR_THICKNESS
DOOR_W = cfg.DOOR_WIDTH
DOOR_H = cfg.DOOR_HEIGHT
WIN_W = cfg.WINDOW_WIDTH
WIN_H = cfg.WINDOW_HEIGHT
WIN_SILL = cfg.WINDOW_SILL

BEVEL_W = cfg.BEVEL_WIDTH
BEVEL_SEGS = cfg.BEVEL_SEGMENTS
SMOOTH_ANGLE = math.radians(40.0)


# ---------------------------------------------------------------- scene mgmt
def wipe_scene():
    """Factory-clean scene: drop every object and orphaned datablock."""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.objects,
                 bpy.data.collections, bpy.data.images):
        for block in list(coll):
            if block.users == 0:
                coll.remove(block)


def get_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def link_to(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def activate(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj


# ---------------------------------------------------------------- primitives
def add_box(bm, p0, p1):
    """Axis-aligned box from corner p0 to corner p1. Returns its 6 faces."""
    (x0, y0, z0), (x1, y1, z1) = p0, p1
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    co = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
          (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    v = [bm.verts.new(c) for c in co]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (2, 3, 7, 6), (1, 2, 6, 5), (3, 0, 4, 7)]
    faces = [bm.faces.new([v[i] for i in q]) for q in quads]
    bm.normal_update()
    return faces


def add_cylinder(bm, radius, depth, segments=24, center=(0, 0, 0), axis='Z'):
    res = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=segments,
        radius1=radius, radius2=radius, depth=depth)
    verts = res['verts']
    if axis == 'X':
        bmesh.ops.rotate(bm, verts=verts,
                         matrix=Matrix.Rotation(math.radians(90), 3, 'Y'))
    elif axis == 'Y':
        bmesh.ops.rotate(bm, verts=verts,
                         matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
    bmesh.ops.translate(bm, verts=verts, vec=Vector(center))
    return verts


def carve(bm, p0, p1):
    """Boolean-subtract an axis-aligned box from the current bmesh."""
    cutter = bmesh.new()
    add_box(cutter, p0, p1)
    tmp = bpy.data.meshes.new("_cut")
    cutter.to_mesh(tmp)
    cutter.free()
    src = bpy.data.meshes.new("_src")
    bm.to_mesh(src)

    ob_a = bpy.data.objects.new("_a", src)
    ob_b = bpy.data.objects.new("_b", tmp)
    bpy.context.collection.objects.link(ob_a)
    bpy.context.collection.objects.link(ob_b)

    mod = ob_a.modifiers.new("bool", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = ob_b
    mod.solver = 'EXACT'
    activate(ob_a)
    bpy.ops.object.modifier_apply(modifier="bool")

    bm.clear()
    bm.from_mesh(ob_a.data)
    bpy.data.objects.remove(ob_a, do_unlink=True)
    bpy.data.objects.remove(ob_b, do_unlink=True)
    bpy.data.meshes.remove(src, do_unlink=True)
    bpy.data.meshes.remove(tmp, do_unlink=True)
    bm.normal_update()


def recess_faces(bm, faces, border=0.06, depth=0.02):
    """Inset a border around each face then push the centre in -- panel look."""
    faces = [f for f in faces if f.is_valid]
    if not faces:
        return []
    res = bmesh.ops.inset_individual(bm, faces=faces, thickness=border,
                                     depth=0.0, use_even_offset=True)
    bm.normal_update()
    for f in faces:
        if not f.is_valid:
            continue
        n = f.normal.copy()
        bmesh.ops.translate(bm, verts=list(f.verts), vec=-n * depth)
    bm.normal_update()
    return res.get('faces', [])


def faces_facing(bm, axis, sign, min_area=0.0):
    """Collect faces whose normal points along +/- a world axis."""
    idx = {'X': 0, 'Y': 1, 'Z': 2}[axis]
    out = []
    for f in bm.faces:
        if f.calc_area() < min_area:
            continue
        n = f.normal
        if abs(n[idx]) > 0.95 and (n[idx] > 0) == (sign > 0):
            out.append(f)
    return out


# ---------------------------------------------------------------- finishing
def finish(bm, name, origin=(0, 0, 0), bevel=BEVEL_W, segs=BEVEL_SEGS,
           material=None, uv=True, collection=None):
    """bmesh -> object, welded, bevelled, weighted-normal, UV-unwrapped."""
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
    bm.normal_update()

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(obj)
    activate(obj)

    # Origin: shift geometry so the requested point lands on (0,0,0).
    if any(origin):
        mat = Matrix.Translation(-Vector(origin))
        me.transform(mat)

    bev = obj.modifiers.new("Bevel", 'BEVEL')
    bev.width = bevel
    bev.segments = segs
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(cfg.BEVEL_ANGLE_LIMIT)
    bev.harden_normals = True
    bev.miter_outer = 'MITER_ARC'
    bev.loop_slide = True

    wn = obj.modifiers.new("WeightedNormal", 'WEIGHTED_NORMAL')
    wn.keep_sharp = True
    wn.weight = cfg.WEIGHTED_NORMAL_WEIGHT
    return _post(obj, material, uv, collection)


def _post(obj, material, uv, collection):
    """Smooth-shade, apply the stack, unwrap, assign material, file away."""
    activate(obj)
    # Full smooth shading is intentional: the bevel + weighted-normal combo
    # is what creates the hard edges, and it does so without normal-map bakes.
    bpy.ops.object.shade_smooth()
    for mod in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        except RuntimeError as exc:
            print("  ! modifier %s on %s: %s" % (mod.name, obj.name, exc))

    if uv:
        smart_unwrap(obj)
    if material:
        obj.data.materials.append(material)
    if collection:
        link_to(obj, collection)

    obj.data.name = obj.name
    return obj


def smart_unwrap(obj, angle=None, margin=None):
    angle = cfg.UV_ANGLE_LIMIT if angle is None else angle
    margin = cfg.UV_ISLAND_MARGIN if margin is None else margin
    activate(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    try:
        bpy.ops.uv.smart_project(angle_limit=math.radians(angle),
                                 island_margin=margin,
                                 correct_aspect=True, scale_to_bounds=False)
    except (RuntimeError, TypeError) as exc:
        print("  ! unwrap %s: %s" % (obj.name, exc))
    bpy.ops.object.mode_set(mode='OBJECT')


# ---------------------------------------------------------------- materials
PALETTE = {
    "M_Concrete":      ((0.216, 0.212, 0.203, 1), 0.88, 0.0),
    "M_PaintedMetal":  ((0.106, 0.180, 0.212, 1), 0.42, 1.0),
    "M_Steel":         ((0.310, 0.325, 0.341, 1), 0.32, 1.0),
    "M_Wood":          ((0.278, 0.176, 0.098, 1), 0.72, 0.0),
    "M_RustedIron":    ((0.192, 0.094, 0.055, 1), 0.85, 1.0),
    "M_Plastic":       ((0.545, 0.176, 0.106, 1), 0.38, 0.0),
    "M_Glass":         ((0.620, 0.702, 0.729, 1), 0.06, 0.0),
    "M_Rubber":        ((0.043, 0.043, 0.047, 1), 0.94, 0.0),
}


def build_materials():
    mats = {}
    for name, (base, rough, metal) in PALETTE.items():
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = base
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metal
            if name == "M_Glass":
                bsdf.inputs["Alpha"].default_value = 0.25
                mat.blend_method = 'BLEND'
        mats[name] = mat
    return mats


def tri_count(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ---------------------------------------------------------------- LOD chain
LOD_RATIOS = cfg.LOD_RATIOS


def build_lod_group(obj, ratios=LOD_RATIOS, collection=None):
    """Unreal-style LOD group: an Empty named LOD_<mesh> parenting LOD0..LODn.

    Unreal's FBX importer reads this null as an LOD group when
    'Import Mesh LODs' is enabled, so the whole chain lands in one asset.
    """
    group = bpy.data.objects.new("LOD_" + obj.name, None)
    group.empty_display_size = 0.25
    bpy.context.collection.objects.link(group)

    members = []
    for i, ratio in enumerate(ratios):
        lod = obj.copy()
        lod.data = obj.data.copy()
        lod.name = "%s_LOD%d" % (obj.name, i)
        lod.data.name = lod.name
        bpy.context.collection.objects.link(lod)
        if ratio < 1.0:
            dec = lod.modifiers.new("Decimate", 'DECIMATE')
            dec.decimate_type = 'COLLAPSE'
            dec.ratio = ratio
            dec.use_collapse_triangulate = True
            activate(lod)
            bpy.ops.object.modifier_apply(modifier="Decimate")
        lod.parent = group
        members.append(lod)

    if collection:
        link_to(group, collection)
        for m in members:
            link_to(m, collection)
    return group, members


# ---------------------------------------------------------------- export
FBX_KW = dict(
    use_selection=True,
    global_scale=1.0,
    apply_scale_options='FBX_SCALE_NONE',
    apply_unit_scale=True,
    axis_forward='-Z',
    axis_up='Y',
    object_types={'MESH', 'EMPTY'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    use_triangles=True,
    use_tspace=True,
    bake_space_transform=False,
    use_custom_props=False,
    path_mode='COPY',
    embed_textures=False,
    add_leaf_bones=False,
    bake_anim=False,
)


def export_fbx(objects, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.fbx(filepath=filepath, **FBX_KW)
    return filepath


def export_gltf(objects, filepath):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(filepath=filepath, export_format='GLB',
                              use_selection=True, export_apply=True,
                              export_yup=True)
    return filepath


# ------------------------------------------------------- generalised boolean
def bool_box(bm, p0, p1, op='DIFFERENCE'):
    """Boolean an axis-aligned box against the bmesh. op: DIFFERENCE|UNION.

    Keeping every piece a single watertight manifold (rather than abutting
    loose boxes) is what lets the bevel modifier produce clean, unbroken
    highlight edges -- and it keeps the triangle budget honest.
    """
    cutter = bmesh.new()
    add_box(cutter, p0, p1)
    tmp = bpy.data.meshes.new("_cut")
    cutter.to_mesh(tmp)
    cutter.free()
    src = bpy.data.meshes.new("_src")
    bm.to_mesh(src)

    ob_a = bpy.data.objects.new("_a", src)
    ob_b = bpy.data.objects.new("_b", tmp)
    bpy.context.collection.objects.link(ob_a)
    bpy.context.collection.objects.link(ob_b)

    mod = ob_a.modifiers.new("bool", 'BOOLEAN')
    mod.operation = op
    mod.object = ob_b
    mod.solver = 'EXACT'
    activate(ob_a)
    bpy.ops.object.modifier_apply(modifier="bool")

    bm.clear()
    bm.from_mesh(ob_a.data)
    bpy.data.objects.remove(ob_a, do_unlink=True)
    bpy.data.objects.remove(ob_b, do_unlink=True)
    bpy.data.meshes.remove(src, do_unlink=True)
    bpy.data.meshes.remove(tmp, do_unlink=True)
    bm.normal_update()


def carve(bm, p0, p1):
    bool_box(bm, p0, p1, 'DIFFERENCE')


def weld(bm, p0, p1):
    bool_box(bm, p0, p1, 'UNION')


# ------------------------------------------------- boolean against any bmesh
def bool_bm(bm, cutter, op='DIFFERENCE'):
    """Boolean an arbitrary bmesh cutter against bm. Consumes `cutter`."""
    tmp = bpy.data.meshes.new("_cut")
    cutter.to_mesh(tmp)
    cutter.free()
    src = bpy.data.meshes.new("_src")
    bm.to_mesh(src)

    ob_a = bpy.data.objects.new("_a", src)
    ob_b = bpy.data.objects.new("_b", tmp)
    bpy.context.collection.objects.link(ob_a)
    bpy.context.collection.objects.link(ob_b)

    mod = ob_a.modifiers.new("bool", 'BOOLEAN')
    mod.operation = op
    mod.object = ob_b
    mod.solver = 'EXACT'
    activate(ob_a)
    bpy.ops.object.modifier_apply(modifier="bool")

    bm.clear()
    bm.from_mesh(ob_a.data)
    bpy.data.objects.remove(ob_a, do_unlink=True)
    bpy.data.objects.remove(ob_b, do_unlink=True)
    bpy.data.meshes.remove(src, do_unlink=True)
    bpy.data.meshes.remove(tmp, do_unlink=True)
    bm.normal_update()


def carve_cylinder(bm, radius, depth, segments=24, center=(0, 0, 0), axis='Z'):
    cutter = bmesh.new()
    add_cylinder(cutter, radius, depth, segments, center, axis)
    bool_bm(bm, cutter, 'DIFFERENCE')


def jitter(bm, amount, seed=0):
    """Randomly nudge every vertex -- turns blocky unions into natural rock."""
    import random
    rng = random.Random(seed)
    for v in bm.verts:
        v.co.x += rng.uniform(-amount, amount)
        v.co.y += rng.uniform(-amount, amount)
        v.co.z += rng.uniform(-amount, amount)
    bm.normal_update()
