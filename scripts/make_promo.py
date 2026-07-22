"""Build public promo stills and a 16:9 gallery-tour video from ModKit.blend.

Run from the repository root:
  blender -b source/ModKit.blend --python scripts/make_promo.py -- --stills
  blender -b source/ModKit.blend --python scripts/make_promo.py -- --video
  blender -b source/ModKit.blend --python scripts/make_promo.py -- --preview

Outputs land in promo/.  The gallery contains every source mesh exactly once;
the separate hero and roof displays use linked duplicates of the same meshes.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "promo")


def cli():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--stills", action="store_true")
    p.add_argument("--video", action="store_true")
    p.add_argument("--preview", action="store_true")
    ns = p.parse_args(args)
    if not (ns.stills or ns.video or ns.preview):
        ns.stills = ns.video = True
    return ns


def hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)) + (1,)


def material(name, colour, metallic=0.0, roughness=0.45,
             emission=None, emission_strength=0.0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = hex_rgb(colour)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        socket = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        socket.default_value = hex_rgb(emission)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    return mat


def tune_source_materials():
    palette = {
        "M_Concrete": ("#A8ADB3", 0.0, 0.72),
        "M_PaintedMetal": ("#175D73", 0.72, 0.27),
        "M_RustedIron": ("#9A442B", 0.58, 0.56),
        "M_Steel": ("#596573", 0.88, 0.22),
        "M_Wood": ("#9B653C", 0.0, 0.58),
    }
    for name, (colour, metal, rough) in palette.items():
        mat = bpy.data.materials.get(name)
        if not mat:
            continue
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = hex_rgb(colour)
        bsdf.inputs["Metallic"].default_value = metal
        bsdf.inputs["Roughness"].default_value = rough


def cube(name, location, scale, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (scale[0] / 2, scale[1] / 2, scale[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if mat:
        obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("Edge bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    return obj


def text_obj(body, location, rotation, size, mat, align="CENTER"):
    curve = bpy.data.curves.new("PromoText", "FONT")
    curve.body = body
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.006
    curve.bevel_depth = 0.002
    obj = bpy.data.objects.new(body, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)
    return obj


def area_light(name, location, energy, colour, size, target=None):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = colour
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    if target:
        look_at(obj, target)
    return obj


def point_light(name, location, energy, colour, radius=1.0):
    data = bpy.data.lights.new(name, "POINT")
    data.energy = energy
    data.color = colour
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, lens=45):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    data.sensor_width = 36
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


def duplicate(source, name, location, rotation=(0, 0, 0), scale=1.0):
    obj = source.copy()
    obj.data = source.data
    obj.name = name
    bpy.context.collection.objects.link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = (scale, scale, scale)
    return obj


def fit_scale(obj, footprint=3.1, max_height=2.7):
    dims = obj.dimensions
    horizontal = max(dims.x, dims.y, 0.001)
    return min(1.0, footprint / horizontal, max_height / max(dims.z, 0.001))


def pedestal(location, base_mat, glow_mat, side):
    x, y, z = location
    cube("Pedestal", (x, y, z + 0.10), (3.4, 3.0, 0.20), base_mat, 0.06)
    # An aisle-facing luminous edge makes silhouettes readable during motion.
    inner_x = x - side * 1.62
    cube("EdgeLight", (inner_x, y, z + 0.19), (0.035, 2.72, 0.035), glow_mat)


def configure_scene(scene):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.render.fps_base = 1
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 35
    scene.render.use_file_extension = True
    scene.world.color = (0.005, 0.008, 0.015)
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.004, 0.007, 0.015, 1)
    bg.inputs["Strength"].default_value = 0.12
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    scene.view_settings.exposure = 0.35

    # Keep output deterministic across Blender compositor API revisions.


def build_scene():
    scene = bpy.context.scene
    sources = {o.name: o for o in list(bpy.data.objects) if o.type == "MESH" and o.name.startswith("SM_")}
    if len(sources) != 38:
        raise RuntimeError("expected 38 source meshes, found %d" % len(sources))
    for obj in sources.values():
        obj.hide_render = True
        obj.hide_viewport = True

    tune_source_materials()
    floor_mat = material("Promo_Floor", "#080D14", 0.70, 0.24)
    wall_mat = material("Promo_Wall", "#101A26", 0.35, 0.42)
    base_mat = material("Promo_Pedestal", "#182535", 0.72, 0.22)
    cyan = material("Promo_Cyan", "#05252F", 0.30, 0.22, "#42D8FF", 8.0)
    orange = material("Promo_Orange", "#35150A", 0.25, 0.28, "#FF7A32", 7.0)
    white = material("Promo_Text", "#EAF6FF", 0.05, 0.30, "#BCEEFF", 2.4)

    cube("GalleryFloor", (0, 0, -0.16), (19, 96, 0.30), floor_mat)
    cube("LeftWall", (-9.5, 0, 3.2), (0.25, 96, 6.6), wall_mat)
    cube("RightWall", (9.5, 0, 3.2), (0.25, 96, 6.6), wall_mat)

    # Repeating ceiling ribs establish speed and depth during the camera move.
    for y in range(-44, 49, 8):
        cube("CeilingRib", (0, y, 6.1), (19, 0.12, 0.14), wall_mat)
        cube("CyanRail", (-8.9, y, 4.7), (0.05, 6.4, 0.05), cyan)
        cube("OrangeRail", (8.9, y, 4.7), (0.05, 6.4, 0.05), orange)
        area_light("Overhead", (0, y, 5.8), 720, (0.55, 0.78, 1.0), 5.0, (0, y, 0))

    names = sorted(sources)
    spacing = 4.45
    start = -40.0
    for i, asset_name in enumerate(names):
        side = -1 if i % 2 == 0 else 1
        row = i // 2
        x = side * 5.65
        y = start + row * spacing
        pedestal((x, y, 0), base_mat, cyan if side < 0 else orange, side)
        src = sources[asset_name]
        z = 0.23
        dup = duplicate(src, "Gallery_%s" % asset_name, (x, y, z),
                        (0, 0, -side * math.radians(20)))
        dup.scale = (fit_scale(dup),) * 3
        # Most pivots sit at the floor; compensate objects whose source bounds dip.
        bpy.context.view_layer.update()
        min_z = min((dup.matrix_world @ Vector(c)).z for c in dup.bound_box)
        dup.location.z += 0.27 - min_z
        # Asset names stay in the manifest and viewer; the promo remains clean
        # and readable even when X crops or scales the media.

    # A separate assembled vignette beyond the gallery supplies the hero render.
    hero_y = 54.0
    cube("HeroPad", (0, hero_y, 0.02), (16, 14, 0.28), base_mat, 0.12)
    for x, y in [(-4, hero_y - 3), (0, hero_y - 3), (4, hero_y - 3),
                 (-4, hero_y + 1), (0, hero_y + 1), (4, hero_y + 1)]:
        duplicate(sources["SM_Floor_4m"], "HeroFloor", (x, y, 0.18))
    wall_specs = [
        ("SM_Wall_Damaged_4m", (-6, hero_y + 4.7, 0.35), math.pi),
        ("SM_Wall_Window_4m", (-2, hero_y + 4.7, 0.35), math.pi),
        ("SM_Wall_Doorway_4m", (2, hero_y + 4.7, 0.35), math.pi),
        ("SM_Wall_Reinforced_4m", (6, hero_y + 4.7, 0.35), math.pi),
        ("SM_Wall_Arch_4m", (-6, hero_y + 0.7, 0.35), math.radians(-90)),
        ("SM_Wall_Straight_4m", (6, hero_y + 0.7, 0.35), math.radians(90)),
    ]
    for name, loc, rz in wall_specs:
        duplicate(sources[name], "Hero_%s" % name, loc, (0, 0, rz))
    duplicate(sources["SM_Stairs_4m"], "HeroStairs", (-1.8, hero_y - 2.2, 0.32),
              (0, 0, math.radians(8)), 0.82)
    duplicate(sources["SM_Railing_4m"], "HeroRailing", (3.8, hero_y + 0.8, 0.35),
              (0, 0, math.radians(90)), 0.88)
    duplicate(sources["SM_Support_Column_3m"], "HeroColumn", (4.9, hero_y + 2.0, 0.35))
    duplicate(sources["SM_Beam_4m"], "HeroBeam", (1.0, hero_y + 3.9, 3.3))
    for name, loc, rz in [
        ("SM_Crate_Stack", (-5.3, hero_y - 5.0, 0.3), 0.25),
        ("SM_Barrel", (4.8, hero_y - 4.3, 0.3), -0.2),
        ("SM_Barrel_Dented", (5.5, hero_y - 4.0, 0.3), 0.4),
        ("SM_Pallet", (-3.2, hero_y - 5.2, 0.3), -0.3),
        ("SM_Rubble_Pile", (5.6, hero_y + 1.3, 0.3), 0.2),
    ]:
        duplicate(sources[name], "HeroProp_%s" % name, loc, (0, 0, rz))
    area_light("HeroKey", (-5, hero_y - 7, 8), 2200, (0.42, 0.75, 1.0), 7.0,
               (0, hero_y, 1.5))
    area_light("HeroRim", (7, hero_y + 4, 6), 1300, (1.0, 0.28, 0.08), 5.0,
               (0, hero_y, 1.5))
    point_light("HeroFill", (0, hero_y - 2, 2.2), 480, (0.18, 0.55, 1.0), 2.0)

    # Roof feature island: every roof part, with the new junctions centered.
    roof_y = -54.0
    cube("RoofPad", (0, roof_y, 0.02), (18, 11, 0.28), base_mat, 0.12)
    cube("RoofBackdrop", (0, roof_y + 5.4, 2.7), (18, 0.22, 5.4), wall_mat)
    cube("RoofBackdropCyan", (-4.7, roof_y + 5.25, 3.8), (6.8, 0.04, 0.05), cyan)
    cube("RoofBackdropOrange", (4.7, roof_y + 5.25, 3.8), (6.8, 0.04, 0.05), orange)
    roof_names = sorted(n for n in names if "Roof" in n)
    for i, name in enumerate(roof_names):
        row, col = divmod(i, 3)
        x = (col - 1) * 5.0
        y = roof_y - 1.8 + row * 4.0
        pedestal((x, y, 0.18), base_mat, cyan if col < 2 else orange, -1 if col < 2 else 1)
        obj = duplicate(sources[name], "RoofFeature_%s" % name, (x, y, 0.48),
                        (0, 0, math.radians(-15)))
        obj.scale = (min(0.72, fit_scale(obj, 3.4, 2.2)),) * 3
    area_light("RoofKey", (-5, roof_y - 5, 7), 1350, (0.42, 0.78, 1.0), 6.0,
               (0, roof_y, 0.8))
    area_light("RoofRim", (6, roof_y + 4, 5), 1100, (1.0, 0.30, 0.08), 5.0,
               (0, roof_y, 0.8))

    configure_scene(scene)
    return scene


def render_still(scene, filename, location, target, lens=45, preview=False):
    cam = camera("StillCamera", location, target, lens)
    scene.camera = cam
    scene.render.resolution_x = 960 if preview else 1920
    scene.render.resolution_y = 540 if preview else 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = os.path.join(OUT, filename)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print("PROMO STILL", scene.render.filepath)


def render_video(scene, preview=False):
    cam = camera("TourCamera", (0, -45.5, 2.15), (0, -38, 1.25), 33)
    target_data = bpy.data.objects.new("TourTarget", None)
    bpy.context.collection.objects.link(target_data)
    target_data.location = (0, -38, 1.15)
    constraint = cam.constraints.new(type="TRACK_TO")
    constraint.target = target_data
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    scene.camera = cam

    end_frame = 240 if preview else 450
    scene.frame_start = 1
    scene.frame_end = end_frame
    cam.location = (0, -45.5, 2.15)
    cam.keyframe_insert("location", frame=1)
    target_data.location = (0, -38, 1.15)
    target_data.keyframe_insert("location", frame=1)
    cam.location = (0, -41.5, 2.05)
    cam.keyframe_insert("location", frame=36 if not preview else 18)
    target_data.location = (0, -34, 1.15)
    target_data.keyframe_insert("location", frame=36 if not preview else 18)
    cam.location = (0, 42.0, 2.25)
    cam.keyframe_insert("location", frame=end_frame - (45 if not preview else 20))
    target_data.location = (0, 48, 1.35)
    target_data.keyframe_insert("location", frame=end_frame - (45 if not preview else 20))
    cam.location = (0, 45.0, 2.6)
    cam.keyframe_insert("location", frame=end_frame)
    target_data.location = (0, 53, 1.6)
    target_data.keyframe_insert("location", frame=end_frame)
    # Blender 5's layered Action API no longer exposes legacy fcurves here.
    # Default Bezier easing gives the entrance and final reveal a gentle settle.

    scene.render.resolution_x = 854 if preview else 1280
    scene.render.resolution_y = 480 if preview else 720
    scene.render.resolution_percentage = 100
    # This Blender distribution omits its internal FFmpeg output module, so
    # render a lossless sequence and encode it with the system FFmpeg afterward.
    frames = os.path.join(OUT, "video_frames_preview" if preview else "video_frames")
    os.makedirs(frames, exist_ok=True)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = os.path.join(frames, "frame_")
    bpy.ops.render.render(animation=True)
    print("PROMO FRAMES", frames)


def main():
    ns = cli()
    os.makedirs(OUT, exist_ok=True)
    scene = build_scene()
    if ns.preview:
        render_still(scene, "preview_hero.png", (12, 49, 7.4), (0, 55, 1.4), 50, True)
        render_still(scene, "preview_collection.png", (0, -47, 2.7), (0, -27, 1.0), 34, True)
        render_still(scene, "preview_roofs.png", (0, -77, 14), (0, -52.8, 0.7), 55, True)
    if ns.stills:
        render_still(scene, "modkit_hero.png", (12, 49, 7.4), (0, 55, 1.4), 50)
        render_still(scene, "modkit_collection.png", (0, -47, 2.7), (0, -27, 1.0), 34)
        render_still(scene, "modkit_roofs.png", (0, -77, 14), (0, -52.8, 0.7), 55)
    if ns.video:
        render_video(scene, False)


main()
