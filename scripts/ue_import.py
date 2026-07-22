"""
ue_import.py -- imports the ModKit pack into an Unreal project and sets up a
parameterised master material with one instance per palette entry.

Run headless from the project folder:
  UnrealEditor-Cmd.exe <project>.uproject -run=pythonscript -script="ue_import.py"
"""
import os
import glob
import unreal

PACK = r"C:\Users\lilli\Documents\ModKit_UE"
NANITE_SRC = os.path.join(PACK, "exports", "FBX_Nanite")
LOD_SRC = os.path.join(PACK, "exports", "FBX_LOD")

DEST_NANITE = "/Game/ModKit/Meshes"
DEST_LOD = "/Game/ModKit/Meshes_LOD"
DEST_MAT = "/Game/ModKit/Materials"

PALETTE = {
    "MI_Concrete":     ((0.216, 0.212, 0.203), 0.88, 0.0),
    "MI_PaintedMetal": ((0.106, 0.180, 0.212), 0.42, 1.0),
    "MI_Steel":        ((0.310, 0.325, 0.341), 0.32, 1.0),
    "MI_Wood":         ((0.278, 0.176, 0.098), 0.72, 0.0),
    "MI_RustedIron":   ((0.192, 0.094, 0.055), 0.85, 1.0),
    "MI_Plastic":      ((0.545, 0.176, 0.106), 0.38, 0.0),
    "MI_Rubber":       ((0.043, 0.043, 0.047), 0.94, 0.0),
}


def log(msg):
    unreal.log("[ModKit] %s" % msg)


def make_task(filename, destination, import_lods):
    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", True)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_materials", True)
    opts.set_editor_property("import_as_skeletal", False)
    opts.set_editor_property("mesh_type_to_import",
                             unreal.FBXImportType.FBXIT_STATIC_MESH)

    smd = opts.static_mesh_import_data
    smd.set_editor_property("import_translation", unreal.Vector(0, 0, 0))
    smd.set_editor_property("import_rotation", unreal.Rotator(0, 0, 0))
    smd.set_editor_property("import_uniform_scale", 1.0)
    smd.set_editor_property("combine_meshes", not import_lods)
    smd.set_editor_property("generate_lightmap_u_vs", True)
    smd.set_editor_property("auto_generate_collision", True)
    smd.set_editor_property("normal_import_method",
                            unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS)
    if import_lods:
        opts.set_editor_property("import_animations", False)
        try:
            smd.set_editor_property("import_mesh_lods", True)
        except Exception:               # older UE spelling
            smd.set_editor_property("import_mesh_lo_ds", True)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", filename)
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("options", opts)
    return task


def import_folder(src, dest, import_lods):
    files = sorted(glob.glob(os.path.join(src, "*.fbx")))
    if not files:
        log("no FBX found in %s" % src)
        return []
    tasks = [make_task(f, dest, import_lods) for f in files]
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    imported = []
    for task in tasks:
        imported.extend(task.get_editor_property("imported_object_paths") or [])
    log("imported %d file(s) into %s" % (len(files), dest))
    return imported


def enable_nanite(package_path):
    """Nanite on every static mesh under a content path."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_path(package_path, recursive=True)
    count = 0
    for data in assets:
        asset = data.get_asset()
        if not isinstance(asset, unreal.StaticMesh):
            continue
        settings = asset.get_editor_property("nanite_settings")
        settings.set_editor_property("enabled", True)
        asset.set_editor_property("nanite_settings", settings)
        unreal.EditorAssetLibrary.save_loaded_asset(asset, False)
        count += 1
    log("Nanite enabled on %d mesh(es)" % count)
    return count


def build_master_material():
    """A tiny parameterised PBR master: BaseColor / Roughness / Metallic."""
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    path = DEST_MAT + "/M_ModKit_Master"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)

    mat = tools.create_asset("M_ModKit_Master", DEST_MAT,
                             unreal.Material, unreal.MaterialFactoryNew())
    lib = unreal.MaterialEditingLibrary

    colour = lib.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, -420, -120)
    colour.set_editor_property("parameter_name", "BaseColor")
    colour.set_editor_property("default_value",
                               unreal.LinearColor(0.5, 0.5, 0.5, 1.0))

    rough = lib.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -420, 60)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.6)

    metal = lib.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -420, 180)
    metal.set_editor_property("parameter_name", "Metallic")
    metal.set_editor_property("default_value", 0.0)

    lib.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    lib.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat, False)
    log("created M_ModKit_Master")
    return mat


def build_instances(master):
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    lib = unreal.MaterialEditingLibrary
    made = 0
    for name, (rgb, rough, metal) in PALETTE.items():
        path = "%s/%s" % (DEST_MAT, name)
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            continue
        inst = tools.create_asset(name, DEST_MAT, unreal.MaterialInstanceConstant,
                                  unreal.MaterialInstanceConstantFactoryNew())
        lib.set_material_instance_parent(inst, master)
        lib.set_material_instance_vector_parameter_value(
            inst, "BaseColor", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        lib.set_material_instance_scalar_parameter_value(inst, "Roughness", rough)
        lib.set_material_instance_scalar_parameter_value(inst, "Metallic", metal)
        unreal.EditorAssetLibrary.save_loaded_asset(inst, False)
        made += 1
    log("created %d material instance(s)" % made)


def main():
    log("pack source: %s" % PACK)
    import_folder(NANITE_SRC, DEST_NANITE, import_lods=False)
    import_folder(LOD_SRC, DEST_LOD, import_lods=True)
    enable_nanite(DEST_NANITE)
    build_instances(build_master_material())
    unreal.EditorAssetLibrary.save_directory("/Game/ModKit", False, True)
    log("IMPORT COMPLETE")


main()
