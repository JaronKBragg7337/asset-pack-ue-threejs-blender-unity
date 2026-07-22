"""
render_previews.py -- three-quarter beauty renders of every asset plus a
contact sheet, so the pack can be reviewed without opening Blender.

    blender -b source/ModKit_UE.blend --python scripts/render_previews.py
"""
import os
import math
import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "previews")
RES = 640


def studio():
    """Neutral grey world + key/fill/rim so form reads without texture."""
    scene = bpy.context.scene
    # Blender renamed this enum between 4.x and 5.x -- take whichever exists.
    engines = scene.render.bl_rna.properties['engine'].enum_items.keys()
    for candidate in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
        if candidate in engines:
            scene.render.engine = candidate
            break
    scene.render.resolution_x = RES
    scene.render.resolution_y = RES
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'

    world = bpy.data.worlds.new("Studio")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.055, 0.058, 0.065, 1)
    bg.inputs[1].default_value = 1.0
    scene.world = world

    for name, loc, energy, size in (
            ("Key", (4.5, -5.5, 6.0), 900, 4.0),
            ("Fill", (-6.0, -3.0, 2.5), 260, 6.0),
            ("Rim", (-2.0, 6.0, 4.0), 480, 3.0)):
        lamp = bpy.data.lights.new(name, 'AREA')
        lamp.energy = energy
        lamp.size = size
        ob = bpy.data.objects.new(name, lamp)
        ob.location = loc
        _aim(ob, Vector((0, 0, 0.6)))
        bpy.context.scene.collection.objects.link(ob)


def _aim(obj, target):
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def make_camera():
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 55
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam


def frame(cam, obj):
    """Park the camera on a 3/4 view scaled to the object's bounding sphere."""
    bb = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    centre = sum(bb, Vector()) / 8.0
    radius = max((v - centre).length for v in bb)
    dist = radius * 2.9 + 0.6
    ang = math.radians(38)
    cam.location = centre + Vector((
        math.cos(ang) * dist * 0.78,
        -math.sin(ang) * dist * 1.35,
        dist * 0.62))
    _aim(cam, centre)


def ground():
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.001))
    plane = bpy.context.active_object
    mat = bpy.data.materials.new("M_Studio_Floor")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.10, 0.10, 0.11, 1)
    bsdf.inputs["Roughness"].default_value = 0.55
    plane.data.materials.append(mat)
    return plane


def main():
    assets = [o for o in bpy.data.objects
              if o.type == 'MESH' and o.name.startswith("SM_")]
    assets.sort(key=lambda o: o.name)
    home = {o: o.location.copy() for o in assets}
    for o in assets:
        o.location = (0, 0, 0)
        o.hide_render = True

    studio()
    floor = ground()
    cam = make_camera()
    os.makedirs(OUT, exist_ok=True)

    for obj in assets:
        obj.hide_render = False
        frame(cam, obj)
        bpy.context.scene.render.filepath = os.path.join(OUT, obj.name + ".png")
        bpy.ops.render.render(write_still=True)
        print("RENDER %s" % obj.name)
        obj.hide_render = True

    # contact sheet: everything laid back out on its showcase grid
    floor.hide_render = False
    for obj in assets:
        obj.hide_render = False
        obj.location = home[obj]
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    cam.data.lens = 40
    cam.location = (16.0, -30.0, 20.0)
    _aim(cam, Vector((14.0, -9.0, 0.0)))
    bpy.context.scene.render.filepath = os.path.join(OUT, "_ContactSheet.png")
    bpy.ops.render.render(write_still=True)
    print("RENDER _ContactSheet")


if __name__ == "__main__":
    main()
