"""
build_kit.py -- generates the ModKit_UE modular building set + prop set.

Run headless:
    blender -b --factory-startup --python build_kit.py

Everything is authored on a 4 m module with a 3 m wall height, origins at the
grid corner, so pieces snap together in Unreal at 400/200/100 uu grid steps.
"""
import os
import sys
import math
import bmesh
import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import modkit_lib as L
from modkit_lib import M, WALL_H, WALL_T, FLOOR_T

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RIB = 0.18          # width of the structural rib framing each wall
RECESS = 0.045      # how deep the panel bays sit
BAY_INSET = 0.18    # gap between rib frame and bay

MATS = {}
STATS = []


def _bays(bm, spans, z0, z1, thickness=WALL_T):
    """Carve recessed panel bays into both faces of a wall slab."""
    for (x0, x1) in spans:
        if x1 - x0 < 0.25:
            continue
        L.carve(bm, (x0, -0.01, z0), (x1, RECESS, z1))
        L.carve(bm, (x0, thickness - RECESS, z0), (x1, thickness + 0.01, z1))


def wall(name, width=M, height=WALL_H, opening=None, mat="M_Concrete"):
    """Straight wall slab with a rib frame, recessed bays and optional hole.

    `opening` = (x0, x1, z0, z1) cut clean through the slab.
    """
    bm = bmesh.new()
    L.add_box(bm, (0, 0, 0), (width, WALL_T, height))
    if opening:
        ox0, ox1, oz0, oz1 = opening
        L.carve(bm, (ox0, -0.01, oz0), (ox1, WALL_T + 0.01, oz1))
        spans = [(RIB, ox0 - RIB), (ox1 + RIB, width - RIB)]
    else:
        mid = width / 2.0
        spans = [(RIB, mid - RIB / 2), (mid + RIB / 2, width - RIB)]
    _bays(bm, spans, RIB, height - RIB)
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


def wall_arch(name, width=M, height=WALL_H, span=1.80, spring=1.45,
              mat="M_Concrete"):
    """Wall with a genuine semicircular arched opening."""
    bm = bmesh.new()
    L.add_box(bm, (0, 0, 0), (width, WALL_T, height))
    cx = width / 2.0
    r = span / 2.0
    x0, x1 = cx - r, cx + r
    L.carve(bm, (x0, -0.01, 0.0), (x1, WALL_T + 0.01, spring))
    L.carve_cylinder(bm, r, WALL_T + 0.02, segments=32,
                     center=(cx, WALL_T / 2.0, spring), axis='Y')
    _bays(bm, [(RIB, x0 - RIB), (x1 + RIB, width - RIB)], RIB, height - RIB)
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


def wall_corner(name, mat="M_Concrete"):
    """90-degree outer corner: one L-shaped watertight solid."""
    bm = bmesh.new()
    L.add_box(bm, (0, 0, 0), (M, WALL_T, WALL_H))
    L.weld(bm, (0, 0, 0), (WALL_T, M, WALL_H))
    _bays(bm, [(RIB + WALL_T, M - RIB)], RIB, WALL_H - RIB)
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


def slab(name, size=M, thick=FLOOR_T, top_at_zero=True, tiles=2,
         mat="M_Concrete"):
    """Floor / ceiling slab with a subtle recessed tile grid on the up-face."""
    z0, z1 = (-thick, 0.0) if top_at_zero else (0.0, thick)
    bm = bmesh.new()
    L.add_box(bm, (0, 0, z0), (size, size, z1))
    step = size / tiles
    groove = 0.05
    for i in range(tiles):
        for j in range(tiles):
            x0 = i * step + groove
            y0 = j * step + groove
            x1 = (i + 1) * step - groove
            y1 = (j + 1) * step - groove
            L.carve(bm, (x0, y0, z1 - 0.04), (x1, y1, z1 + 0.01))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


def pillar(name, size=0.40, height=WALL_H, mat="M_Steel"):
    """Square pillar with capital + base flare. Origin at base centre."""
    h = size / 2.0
    cap = size * 0.62
    bm = bmesh.new()
    L.add_box(bm, (-h, -h, 0), (h, h, height))
    L.weld(bm, (-cap, -cap, 0), (cap, cap, 0.12))
    L.weld(bm, (-cap, -cap, height - 0.12), (cap, cap, height))
    for z in (height * 0.34, height * 0.66):
        L.weld(bm, (-h - 0.03, -h - 0.03, z - 0.05),
               (h + 0.03, h + 0.03, z + 0.05))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


def stairs(name, run=M, rise=WALL_H, steps=12, width=1.6, mat="M_Concrete"):
    """Straight flight climbing exactly one storey over one module."""
    tread = run / steps
    riser = rise / steps
    w = width / 2.0
    bm = bmesh.new()
    L.add_box(bm, (-w, 0, 0), (w, tread, riser))
    for i in range(1, steps):
        L.weld(bm, (-w, i * tread, 0), (w, (i + 1) * tread, (i + 1) * riser))
    # stringers down each side for a finished silhouette
    for sx in (-w - 0.08, w):
        L.weld(bm, (sx, 0, 0), (sx + 0.08, run, 0.12))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


def railing(name, length=M, height=1.10, posts=5, mat="M_Steel"):
    """Handrail with vertical posts. Origin at the grid corner."""
    bm = bmesh.new()
    t = 0.05
    L.add_box(bm, (0, -t, height - 0.08), (length, t, height))
    L.weld(bm, (0, -t * 0.7, height * 0.48), (length, t * 0.7,
                                              height * 0.48 + 0.05))
    for i in range(posts):
        x = i * (length / (posts - 1))
        x = min(max(x, t), length - t)
        L.weld(bm, (x - t, -t, 0), (x + t, t, height))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


def doorframe(name, w=1.20, h=2.20, mat="M_PaintedMetal"):
    """Trim that dresses a doorway cut. Origin centred on the opening base."""
    d = WALL_T + 0.06
    j = 0.10
    bm = bmesh.new()
    L.add_box(bm, (-w / 2 - j, -d / 2, 0), (-w / 2, d / 2, h))
    L.weld(bm, (w / 2, -d / 2, 0), (w / 2 + j, d / 2, h))
    L.weld(bm, (-w / 2 - j, -d / 2, h), (w / 2 + j, d / 2, h + j))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


def parapet(name, length=M, height=0.90, mat="M_Concrete"):
    """Roof-edge parapet with a capstone lip."""
    bm = bmesh.new()
    L.add_box(bm, (0, 0, 0), (length, WALL_T, height))
    L.weld(bm, (0, -0.04, height - 0.10), (length, WALL_T + 0.04, height))
    _bays(bm, [(RIB, length - RIB)], 0.14, height - 0.20)
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))


# ================================================================== PROPS
def _put(bm, p0, p1):
    """Add a box, unioning it in if the mesh already has geometry."""
    if len(bm.verts) == 0:
        L.add_box(bm, p0, p1)
    else:
        L.weld(bm, p0, p1)


def crate(name, size=0.60, mat="M_Wood"):
    """Panelled crate with corner brackets. Origin at base centre."""
    h = size / 2.0
    frame = size * 0.14
    bm = bmesh.new()
    L.add_box(bm, (-h, -h, 0), (h, h, size))
    inner = h - frame
    d = 0.035
    # recess the four sides and the lid
    L.carve(bm, (-inner, -h - 0.01, frame), (inner, -h + d, size - frame))
    L.carve(bm, (-inner, h - d, frame), (inner, h + 0.01, size - frame))
    L.carve(bm, (-h - 0.01, -inner, frame), (-h + d, inner, size - frame))
    L.carve(bm, (h - d, -inner, frame), (h + 0.01, inner, size - frame))
    L.carve(bm, (-inner, -inner, size - d), (inner, inner, size + 0.01))
    # steel corner brackets
    b = frame * 0.9
    for sx in (-1, 1):
        for sy in (-1, 1):
            L.weld(bm, (sx * h - sx * b, sy * h - sy * b, 0),
                   (sx * h + sx * 0.02, sy * h + sy * 0.02, size + 0.02))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Props"))


def barrel(name, radius=0.30, height=0.92, mat="M_RustedIron"):
    """Ribbed barrel. Origin at base centre."""
    bm = bmesh.new()
    L.add_cylinder(bm, radius, height, segments=32,
                   center=(0, 0, height / 2.0))
    for z in (height * 0.22, height * 0.5, height * 0.78):
        L.add_cylinder(bm, radius * 1.045, 0.06, segments=32, center=(0, 0, z))
    L.add_cylinder(bm, radius * 0.55, 0.05, segments=24,
                   center=(0, 0, height - 0.01))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Props"))


def pallet(name, w=1.20, d=0.80, mat="M_Wood"):
    """Euro-style pallet. Origin at base centre."""
    bm = bmesh.new()
    board = 0.022
    blk_h = 0.078
    bx, by = w / 2.0, d / 2.0
    # bottom deckboards
    for y in (-by, -board * 1.5, by - 0.12):
        _put(bm, (-bx, y, 0), (bx, y + 0.12, board))
    # blocks
    for x in (-bx, -0.06, bx - 0.12):
        for y in (-by, -0.06, by - 0.12):
            _put(bm, (x, y, board), (x + 0.12, y + 0.12, board + blk_h))
    # top deckboards
    z = board + blk_h
    n = 5
    for i in range(n):
        y0 = -by + i * (d - 0.10) / (n - 1)
        L.weld(bm, (-bx, y0, z), (bx, y0 + 0.10, z + board))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Props"))


def pipe(name, length=2.0, radius=0.11, mat="M_Steel"):
    """Flanged pipe run, lying along X. Origin at base centre."""
    bm = bmesh.new()
    L.add_cylinder(bm, radius, length, segments=24,
                   center=(0, 0, radius), axis='X')
    for x in (-length / 2 + 0.04, 0.0, length / 2 - 0.04):
        L.add_cylinder(bm, radius * 1.35, 0.05, segments=24,
                       center=(x, 0, radius), axis='X')
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Props"))


def vent(name, w=0.90, h=0.60, mat="M_PaintedMetal"):
    """Wall vent with louvred slats. Origin at base centre, faces -Y."""
    d = 0.12
    bm = bmesh.new()
    L.add_box(bm, (-w / 2, 0, 0), (w / 2, d, h))
    inset = 0.07
    L.carve(bm, (-w / 2 + inset, -0.01, inset),
            (w / 2 - inset, 0.05, h - inset))
    slats = 6
    span = h - 2 * inset
    for i in range(slats):
        z = inset + (i + 0.5) * span / slats
        L.weld(bm, (-w / 2 + inset, 0.005, z - 0.018),
               (w / 2 - inset, 0.055, z + 0.018))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Props"))


def sign(name, w=1.10, h=0.55, mat="M_PaintedMetal"):
    """Bracketed wall sign. Origin at base centre, plate faces -Y."""
    bm = bmesh.new()
    L.add_box(bm, (-w / 2, 0.06, 0), (w / 2, 0.10, h))
    L.weld(bm, (-w / 2 + 0.05, 0.10, h * 0.5 - 0.02),
           (w / 2 - 0.05, 0.18, h * 0.5 + 0.02))
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.10)
        L.weld(bm, (x - 0.025, 0.10, h - 0.10), (x + 0.025, 0.20, h - 0.04))
    L.carve(bm, (-w / 2 + 0.05, 0.055, 0.05), (w / 2 - 0.05, 0.075, h - 0.05))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Props"))


def rubble(name, size=0.75, chunks=7, seed=3, mat="M_Concrete"):
    """Irregular debris pile built from jittered, unioned blocks."""
    import random
    rng = random.Random(seed)
    bm = bmesh.new()
    for i in range(chunks):
        # half-extents kept well under the scatter radius, otherwise every
        # chunk overlaps its neighbour and the union collapses into one slab
        sx = size * rng.uniform(0.09, 0.19)
        sy = size * rng.uniform(0.09, 0.19)
        sz = size * rng.uniform(0.07, 0.16)
        cx = rng.uniform(-size * 0.42, size * 0.42)
        cy = rng.uniform(-size * 0.42, size * 0.42)
        # tier the chunks so the pile gains height instead of spreading flat
        cz = sz + size * 0.13 * (i % 3) + rng.uniform(0.0, size * 0.05)
        _put(bm, (cx - sx, cy - sy, cz - sz), (cx + sx, cy + sy, cz + sz))
    # break up the axis-aligned silhouette so it reads as rock, not boxes
    L.jitter(bm, size * 0.10, seed=seed)
    # drop the pile so its lowest point sits on z = 0
    zmin = min(v.co.z for v in bm.verts)
    bmesh.ops.translate(bm, verts=list(bm.verts), vec=(0, 0, -zmin))
    return L.finish(bm, name, material=MATS[mat], bevel=0.02,
                    collection=L.get_collection("Props"))


def crate_stack(name, mat="M_Wood"):
    """Three crates pre-stacked -- a one-click set-dressing cluster."""
    bm = bmesh.new()
    _put(bm, (-0.60, -0.60, 0.00), (0.00, 0.00, 0.60))
    _put(bm, (0.02, -0.55, 0.00), (0.62, 0.05, 0.60))
    _put(bm, (-0.50, -0.50, 0.60), (0.10, 0.10, 1.20))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Props"))


# ================================================================== BUILD
def define_assets():
    """Every asset in the pack, in catalogue order."""
    return [
        # -- modular building kit -------------------------------------
        lambda: wall("SM_Wall_Straight_4m"),
        lambda: wall("SM_Wall_Half_2m", width=M / 2),
        lambda: wall("SM_Wall_Doorway_4m",
                     opening=(M / 2 - 0.60, M / 2 + 0.60, 0.0, 2.20)),
        lambda: wall("SM_Wall_Window_4m",
                     opening=(M / 2 - 0.90, M / 2 + 0.90, 1.00, 2.20)),
        lambda: wall_arch("SM_Wall_Arch_4m"),
        lambda: wall_corner("SM_Wall_Corner_4m"),
        lambda: slab("SM_Floor_4m", tiles=2),
        lambda: slab("SM_Ceiling_4m", tiles=1, top_at_zero=False),
        lambda: pillar("SM_Pillar_3m"),
        lambda: stairs("SM_Stairs_4m"),
        lambda: railing("SM_Railing_4m"),
        lambda: doorframe("SM_Doorframe"),
        lambda: parapet("SM_Parapet_4m"),
        # -- environment props ----------------------------------------
        lambda: crate("SM_Crate_Small", size=0.60),
        lambda: crate("SM_Crate_Large", size=1.00, mat="M_PaintedMetal"),
        lambda: crate_stack("SM_Crate_Stack"),
        lambda: barrel("SM_Barrel"),
        lambda: pallet("SM_Pallet"),
        lambda: pipe("SM_Pipe_2m"),
        lambda: vent("SM_Vent_Wall"),
        lambda: sign("SM_Sign_Wall"),
        lambda: rubble("SM_Rubble_Pile"),
    ]


def main():
    global MATS
    L.wipe_scene()
    MATS = L.build_materials()
    L.get_collection("Kit")
    L.get_collection("Props")

    nanite_dir = os.path.join(ROOT, "exports", "FBX_Nanite")
    lod_dir = os.path.join(ROOT, "exports", "FBX_LOD")
    glb_dir = os.path.join(ROOT, "exports", "GLTF")

    built = []
    for make in define_assets():
        try:
            obj = make()
        except Exception as exc:                       # noqa: BLE001
            print("FAILED %s: %s" % (make, exc))
            continue
        tris = L.tri_count(obj)
        built.append(obj)
        STATS.append((obj.name, tris, len(obj.data.vertices)))
        print("BUILT %-24s %6d tris" % (obj.name, tris))

        L.export_fbx([obj], os.path.join(nanite_dir, obj.name + ".fbx"))
        L.export_gltf([obj], os.path.join(glb_dir, obj.name + ".glb"))

        group, members = L.build_lod_group(obj)
        L.export_fbx([group] + members,
                     os.path.join(lod_dir, obj.name + "_LODs.fbx"))
        for ob in [group] + members:
            bpy.data.objects.remove(ob, do_unlink=True)

    return built


def layout_showcase(objs, spacing=6.0, per_row=6):
    """Spread every asset out on a grid so the .blend opens on a contact sheet."""
    for i, ob in enumerate(objs):
        ob.location = ((i % per_row) * spacing,
                       -(i // per_row) * spacing, 0.0)


def write_manifest(path):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("asset,triangles,vertices\n")
        for name, tris, verts in STATS:
            fh.write("%s,%d,%d\n" % (name, tris, verts))
    total = sum(t for _, t, _ in STATS)
    print("MANIFEST %d assets, %d tris total" % (len(STATS), total))


if __name__ == "__main__":
    objects = main()
    layout_showcase(objects)
    blend = os.path.join(ROOT, "source", "ModKit.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    write_manifest(os.path.join(ROOT, "docs", "asset_manifest.csv"))
    print("DONE saved %s" % blend)
