"""
ue_lods.py -- builds LOD chains on the /Game/ModKit/Meshes_LOD set.

Why LOD groups rather than explicit reduction:
  * Blender's 'LOD_' FBX null is not honoured by the UE FBX importer, so the
    LOD export lands as four unrelated static meshes.
  * StaticMeshEditorSubsystem is unavailable inside a commandlet (returns None)
    and the deprecated EditorStaticMeshLibrary.set_lods returns -1 there.
  * Assigning a built-in LOD group makes the engine generate and persist the
    chain immediately, with switch distances tuned per asset class.

  UnrealEditor-Cmd.exe <project>.uproject -run=pythonscript -script="ue_lods.py"
"""
import unreal

SRC = "/Game/ModKit/Meshes"
DEST = "/Game/ModKit/Meshes_LOD"
LOGF = r"C:\Users\lilli\Documents\ModKit_UE\docs\lod_build.txt"

ARCH_GROUP = "LevelArchitecture"
PROP_GROUP = "SmallProp"
LARGE_GROUP = "LargeProp"

KIT = ("Wall", "Floor", "Ceiling", "Stairs", "Pillar", "Parapet",
       "Doorframe", "Railing")
LARGE = ("Crate_Large", "Crate_Stack", "Rubble", "Pallet")

_log = []


def P(msg):
    _log.append(str(msg))
    unreal.log("[ModKit] %s" % msg)
    with open(LOGF, "w", encoding="utf-8") as fh:
        fh.write("\n".join(_log) + "\n")


def group_for(name):
    if any(k in name for k in LARGE):
        return LARGE_GROUP
    if any(k in name for k in KIT):
        return ARCH_GROUP
    return PROP_GROUP


def base_names():
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    out = set()
    for data in reg.get_assets_by_path(SRC, recursive=False):
        name = str(data.asset_name)
        if name.startswith("SM_"):
            out.add(name)
    return sorted(out)


def purge_helpers():
    """Remove the SM_*_LODn assets left behind by the FBX LOD import."""
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    removed = 0
    for data in reg.get_assets_by_path(DEST, recursive=False):
        name = str(data.asset_name)
        if "_LOD" in name:
            if unreal.EditorAssetLibrary.delete_asset("%s/%s" % (DEST, name)):
                removed += 1
    P("helpers removed: %d" % removed)


def build_chain(name):
    src_path = "%s/%s" % (SRC, name)
    dst_path = "%s/%s" % (DEST, name)

    if unreal.EditorAssetLibrary.does_asset_exist(dst_path):
        unreal.EditorAssetLibrary.delete_asset(dst_path)
    if not unreal.EditorAssetLibrary.duplicate_asset(src_path, dst_path):
        P("%s: duplicate FAILED" % name)
        return 0

    mesh = unreal.EditorAssetLibrary.load_asset(dst_path)
    # a hand-authored LOD chain replaces Nanite -- they are alternatives
    nan = mesh.get_editor_property("nanite_settings")
    nan.set_editor_property("enabled", False)
    mesh.set_editor_property("nanite_settings", nan)

    group = group_for(name)
    mesh.set_editor_property("lod_group", group)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, False)

    count = mesh.get_num_lods()
    P("%-24s %-18s %d LODs  %s"
      % (name, group, count,
         [mesh.get_num_triangles(i) for i in range(count)]))
    return count


def main():
    names = base_names()
    P("building LOD chains for %d mesh(es)" % len(names))
    purge_helpers()
    ok = sum(1 for n in names if build_chain(n) >= 3)
    unreal.EditorAssetLibrary.save_directory("/Game/ModKit", False, True)
    P("COMPLETE: %d/%d meshes have a multi-LOD chain" % (ok, len(names)))


main()
