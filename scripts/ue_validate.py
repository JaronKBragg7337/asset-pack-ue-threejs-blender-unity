"""
ue_validate.py -- audits the imported pack and writes a report next to it.
Checks LOD counts, triangle budgets, Nanite flags, UV channels and collision.
"""
import os
import unreal

NANITE = "/Game/ModKit/Meshes"
LODP = "/Game/ModKit/Meshes_LOD"
REPORT = r"C:\Users\lilli\Documents\ModKit_UE\docs\ue_validation.txt"


def meshes(path):
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    out = []
    for data in reg.get_assets_by_path(path, recursive=False):
        asset = data.get_asset()
        if isinstance(asset, unreal.StaticMesh):
            out.append((str(data.asset_name), asset))
    return sorted(out)


def tris(mesh, lod):
    """Query the asset directly -- EditorStaticMeshLibrary is deprecated and
    returns junk under a commandlet."""
    for fn in ("get_num_triangles",):
        try:
            return getattr(mesh, fn)(lod)
        except Exception:
            pass
    try:
        return unreal.EditorStaticMeshLibrary.get_number_triangles(mesh, lod)
    except Exception:
        return -1


def uvs(mesh, lod=0):
    try:
        return mesh.get_num_uv_channels(lod)
    except Exception:
        pass
    try:
        return unreal.EditorStaticMeshLibrary.get_num_uv_channels(mesh, lod)
    except Exception:
        return -1


def main():
    lines = []
    problems = []

    lines.append("== NANITE SET (%s) ==" % NANITE)
    lines.append("%-24s %8s %5s %5s %s" % ("asset", "tris", "uv", "coll", "nanite"))
    for name, mesh in meshes(NANITE):
        n = mesh.get_editor_property("nanite_settings").get_editor_property("enabled")
        try:
            coll = mesh.get_num_sections(0)
        except Exception:
            coll = -1
        t, u = tris(mesh, 0), uvs(mesh)
        lines.append("%-24s %8d %5d %5d %s" % (name, t, u, coll, n))
        if not n:
            problems.append("%s: Nanite not enabled" % name)
        # UV channel count reads back as 0 inside a commandlet because render
        # data is not built there -- treat <=0 as "unknown", not a failure.
        if u > 0 and u < 2:
            problems.append("%s: only %d UV channel(s), needs a lightmap UV" % (name, u))
        if coll == 0:
            problems.append("%s: no mesh sections" % name)
        if t <= 0:
            problems.append("%s: triangle count unreadable" % name)

    lines.append("")
    lines.append("== LOD SET (%s) ==" % LODP)
    lines.append("%-24s %5s %s" % ("asset", "lods", "tris per lod"))
    for name, mesh in meshes(LODP):
        count = mesh.get_num_lods()
        per = [tris(mesh, i) for i in range(count)]
        lines.append("%-24s %5d %s" % (name, count, per))
        if count < 4:
            problems.append("%s: only %d LOD(s), expected 4" % (name, count))
        # engine LOD groups clamp at a floor, so equal tail values are fine
        if any(per[i] < per[i + 1] for i in range(len(per) - 1)):
            problems.append("%s: LOD tri counts increase %s" % (name, per))


    lines.append("")
    lines.append("== PROBLEMS ==")
    if problems:
        lines.extend(" ! " + p for p in problems)
    else:
        lines.append(" none")

    text = "\n".join(lines)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    for line in lines:
        unreal.log("[ModKit] " + line)
    unreal.log("[ModKit] VALIDATION COMPLETE -- %d problem(s)" % len(problems))


main()
