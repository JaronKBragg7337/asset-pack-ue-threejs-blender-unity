"""Assemble and export the ModKit Industrial Outpost example scene.

The scene is built entirely from linked instances of the 38 generated pack
meshes. No hand-modelled geometry is introduced. Run from the repository root:

  blender -b source/ModKit.blend --python scripts/build_demo_scene.py

Outputs:
  examples/industrial_outpost/ModKit_Industrial_Outpost.blend
  examples/industrial_outpost/ModKit_Industrial_Outpost.glb
  examples/industrial_outpost/ModKit_Industrial_Outpost.fbx
  examples/industrial_outpost/preview.png
  examples/industrial_outpost/layout.json
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "examples", "industrial_outpost")
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

import kit_config as cfg  # noqa: E402
import modkit_lib as L  # noqa: E402


M = cfg.MODULE
H = cfg.WALL_HEIGHT
DEG = math.pi / 180.0
PLACED = []
INSTANCE_COUNTS = {}


def rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1,)


def tune_materials():
    """Give the example a legible no-texture palette using existing materials."""
    palette = {
        "M_Concrete": ("#9EA7AF", 0.0, 0.72),
        "M_PaintedMetal": ("#17667B", 0.66, 0.30),
        "M_RustedIron": ("#8C422C", 0.55, 0.58),
        "M_Steel": ("#465463", 0.82, 0.25),
        "M_Wood": ("#95613A", 0.0, 0.60),
    }
    for name, (colour, metal, rough) in palette.items():
        mat = bpy.data.materials.get(name)
        if not mat:
            continue
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = rgb(colour)
        bsdf.inputs["Metallic"].default_value = metal
        bsdf.inputs["Roughness"].default_value = rough


def collection(name):
    coll = bpy.data.collections.get(name)
    if not coll:
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
    return coll


def move_to(obj, coll):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    coll.objects.link(obj)


def place(sources, asset, location, rotation=(0.0, 0.0, 0.0),
          scale=1.0, zone="Architecture", label=None):
    if asset not in sources:
        raise KeyError("missing source asset %s" % asset)
    obj = sources[asset].copy()
    obj.data = sources[asset].data
    number = INSTANCE_COUNTS.get(asset, 0) + 1
    INSTANCE_COUNTS[asset] = number
    obj.name = label or "%s_%02d" % (asset, number)
    bpy.context.collection.objects.link(obj)
    move_to(obj, collection("Demo_%s" % zone))
    obj.hide_render = False
    obj.hide_viewport = False
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = (scale, scale, scale)
    obj["modkit_asset"] = asset
    PLACED.append(obj)
    return obj


def wall_x(sources, asset, x, y, facing="north", z=0.0):
    if facing == "north":
        return place(sources, asset, (x, y, z))
    return place(sources, asset, (x + M, y, z), (0, 0, math.pi))


def wall_y(sources, asset, x, y, facing="east", z=0.0):
    if facing == "east":
        return place(sources, asset, (x, y, z), (0, 0, 90 * DEG))
    return place(sources, asset, (x, y + M, z), (0, 0, -90 * DEG))


def assemble(sources):
    """Build a two-level, L-shaped outpost plus a working yard."""
    # Ground/foundation: every placement stays on the pack's four-metre grid.
    for gx in range(-1, 5):
        for gy in range(-1, 4):
            place(sources, "SM_Floor_4m", (gx * M, gy * M, 0), zone="Foundation")

    # Main 12 x 8 m shell. The open front corner makes the interior readable.
    wall_x(sources, "SM_Wall_Doorway_4m", 0, 0, "north")
    wall_x(sources, "SM_Wall_Window_4m", M, 0, "north")
    wall_x(sources, "SM_Wall_Damaged_4m", 2 * M, 0, "north")
    wall_x(sources, "SM_Wall_Straight_4m", 0, 2 * M, "south")
    wall_x(sources, "SM_Wall_Reinforced_4m", M, 2 * M, "south")
    wall_x(sources, "SM_Wall_Arch_4m", 2 * M, 2 * M, "south")
    wall_y(sources, "SM_Wall_Corner_4m", 0, 0, "east")
    wall_y(sources, "SM_Wall_Half_2m", 0, M, "east")
    wall_y(sources, "SM_Wall_Window_4m", 3 * M, 0, "west")
    wall_y(sources, "SM_Wall_Straight_4m", 3 * M, M, "west")

    # Upper L-shaped roof: flat service bay plus all junction vocabulary.
    place(sources, "SM_Roof_Pitched_4m", (0, 0, H), zone="Roof")
    place(sources, "SM_Roof_Valley_4m", (M, 0, H), zone="Roof")
    place(sources, "SM_Roof_Pitched_4m", (2 * M, 0, H), zone="Roof")
    place(sources, "SM_Roof_Corner_4m", (0, M, H), zone="Roof")
    place(sources, "SM_Roof_Flat_4m", (M, M, H), zone="Roof")
    place(sources, "SM_Ceiling_4m", (2 * M, M, H), zone="Roof")
    place(sources, "SM_Roof_Ridge_4m",
          (0, 0.5 * M - 0.26, H + cfg.ROOF_RISE + cfg.ROOF_THICKNESS),
          zone="Roof")
    place(sources, "SM_Roof_Trim_4m", (2 * M, -cfg.ROOF_OVERHANG, H), zone="Roof")
    place(sources, "SM_Parapet_4m", (M, 2 * M, H + cfg.FLOOR_THICKNESS),
          zone="Roof")
    place(sources, "SM_Railing_4m", (2 * M, 2 * M, H + cfg.FLOOR_THICKNESS),
          zone="Roof")

    # Interior circulation and structure.
    place(sources, "SM_Stairs_4m", (M + 0.25 * M, 0.60 * M, 0.20), zone="Interior")
    place(sources, "SM_Pillar_3m", (0.18 * M, 1.78 * M, 0.20), zone="Interior")
    place(sources, "SM_Support_Column_3m", (2.72 * M, 1.74 * M, 0.20),
          zone="Interior")
    place(sources, "SM_Beam_4m", (M, 1.88 * M, H - 0.34), zone="Interior")
    place(sources, "SM_Doorframe", (0.50 * M - cfg.DOOR_WIDTH / 2,
                                     -cfg.WALL_THICKNESS, 0.20), zone="Interior")
    place(sources, "SM_Door_Panel", (0.50 * M, -0.08 * M, 0.20),
          (0, 0, -28 * DEG), zone="Interior")
    place(sources, "SM_Floor_Hatch", (2.12 * M, 1.15 * M, 0.23), zone="Interior")

    # Wall-mounted details. Slight offsets use the configured wall thickness.
    place(sources, "SM_Sign_Wall", (1.55 * M, -cfg.WALL_THICKNESS, 0.55 * H),
          zone="Details")
    place(sources, "SM_Vent_Wall", (2.55 * M, -cfg.WALL_THICKNESS, 0.58 * H),
          zone="Details")
    place(sources, "SM_Pipe_2m", (3 * M + cfg.WALL_THICKNESS, 1.45 * M, 0.55 * H),
          (0, 90 * DEG, 90 * DEG), zone="Details")

    # Yard storytelling: loading zone, salvage, and three barrel states.
    place(sources, "SM_Pallet", (-0.35 * M, -0.58 * M, 0.22),
          (0, 0, -12 * DEG), zone="Props")
    place(sources, "SM_Crate_Large", (-0.32 * M, -0.55 * M, 0.35),
          (0, 0, 8 * DEG), zone="Props")
    place(sources, "SM_Crate_Small", (-0.08 * M, -0.62 * M, 0.35),
          (0, 0, -18 * DEG), zone="Props")
    place(sources, "SM_Crate_Stack", (3.58 * M, -0.58 * M, 0.25),
          (0, 0, 20 * DEG), zone="Props")
    place(sources, "SM_Crate_Broken", (3.30 * M, -0.78 * M, 0.25),
          (0, 0, -30 * DEG), zone="Props")
    place(sources, "SM_Barrel", (2.82 * M, -0.66 * M, 0.25), zone="Props")
    place(sources, "SM_Barrel_Open", (3.04 * M, -0.70 * M, 0.25),
          (0, 0, 12 * DEG), zone="Props")
    place(sources, "SM_Barrel_Dented", (3.22 * M, -0.48 * M, 0.25),
          (0, 0, -15 * DEG), zone="Props")
    place(sources, "SM_Rubble_Pile", (3.66 * M, 2.45 * M, 0.25),
          (0, 0, 18 * DEG), zone="Props")
    place(sources, "SM_Debris_Scatter", (3.32 * M, 2.72 * M, 0.24),
          (0, 0, -24 * DEG), zone="Props")


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_camera_and_lights():
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("IndustrialOutpostWorld")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.008, 0.014, 0.025, 1)
    bg.inputs["Strength"].default_value = 0.22

    camera_data = bpy.data.cameras.new("OutpostCamera")
    camera_data.lens = 48
    camera = bpy.data.objects.new("OutpostCamera", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (5.4 * M, -5.2 * M, 4.2 * M)
    look_at(camera, (1.35 * M, 0.75 * M, 0.65 * H))
    scene.camera = camera

    def area(name, location, energy, colour, size, target):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = colour
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)

    area("OutpostKey", (-1.8 * M, -2.2 * M, 4.2 * M), 1800,
         (0.35, 0.70, 1.0), 7.0, (1.2 * M, 0.8 * M, H))
    area("OutpostRim", (4.5 * M, 3.0 * M, 3.0 * M), 1500,
         (1.0, 0.28, 0.08), 6.0, (1.8 * M, 0.9 * M, H))
    sun_data = bpy.data.lights.new("OutpostSun", "SUN")
    sun_data.energy = 1.2
    sun_data.color = (0.78, 0.88, 1.0)
    sun = bpy.data.objects.new("OutpostSun", sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (35 * DEG, -25 * DEG, -35 * DEG)


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return lo, hi


def write_layout(path):
    bpy.context.view_layer.update()
    lo, hi = bounds(PLACED)
    payload = {
        "name": "ModKit Industrial Outpost",
        "generator": "scripts/build_demo_scene.py",
        "units": "metres",
        "grid_module": M,
        "instance_count": len(PLACED),
        "unique_assets": sorted(INSTANCE_COUNTS),
        "bounds_metres": {
            "min": [round(v, 4) for v in lo],
            "max": [round(v, 4) for v in hi],
        },
        "instances": [{
            "name": obj.name,
            "asset": obj["modkit_asset"],
            "location": [round(v, 4) for v in obj.location],
            "rotation_degrees": [round(v / DEG, 3) for v in obj.rotation_euler],
            "scale": [round(v, 4) for v in obj.scale],
        } for obj in PLACED],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    return payload


def render_preview(path):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = path
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.30
    bpy.ops.render.render(write_still=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    sources = {obj.name: obj for obj in bpy.data.objects
               if obj.type == "MESH" and obj.name.startswith("SM_")}
    if len(sources) != 38:
        raise RuntimeError("expected 38 source meshes, found %d" % len(sources))
    tune_materials()
    assemble(sources)

    missing = sorted(set(sources) - set(INSTANCE_COUNTS))
    if missing:
        raise RuntimeError("demo does not exercise every asset: %s" % ", ".join(missing))

    # The editable .blend should contain the assembled scene, not the original
    # contact-sheet layout. Linked mesh data remains shared between instances.
    for src in sources.values():
        bpy.data.objects.remove(src, do_unlink=True)

    add_camera_and_lights()
    bpy.context.view_layer.update()

    layout_path = os.path.join(OUT, "layout.json")
    layout = write_layout(layout_path)

    glb_path = os.path.join(OUT, "ModKit_Industrial_Outpost.glb")
    fbx_path = os.path.join(OUT, "ModKit_Industrial_Outpost.fbx")
    L.export_gltf(PLACED, glb_path)
    L.export_fbx(PLACED, fbx_path)

    blend_path = os.path.join(OUT, "ModKit_Industrial_Outpost.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    render_preview(os.path.join(OUT, "preview.png"))

    print("DEMO %d instances, %d unique assets" %
          (layout["instance_count"], len(layout["unique_assets"])))
    print("DEMO bounds", layout["bounds_metres"])
    print("DEMO saved", OUT)


main()
