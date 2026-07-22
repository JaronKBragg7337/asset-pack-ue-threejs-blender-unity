# Industrial Outpost example scene

A 70-instance, pack-only diorama assembled from all 38 ModKit assets. It is
intended as both a starting point and a readable example of the four-metre
grid, corner pivots, roof junctions, wall attachments and prop placement.

## Open or import it

| File | Best for |
|---|---|
| `ModKit_Industrial_Outpost.blend` | Editing the complete scene in Blender 5.1+ |
| `ModKit_Industrial_Outpost.glb` | three.js, Godot and browser workflows |
| `ModKit_Industrial_Outpost.fbx` | Unreal, Unity and other FBX workflows |
| `layout.json` | Reconstructing or inspecting every transform in code |
| `preview.png` | Quick visual reference |

The scene uses metres and the same source materials as the pack. Normals and
tangents are exported; import them rather than recalculating them.

## Rebuild it

From the repository root:

```bash
blender -b source/ModKit.blend --python scripts/build_demo_scene.py
```

The generator fails if the source pack does not contain exactly 38 meshes or
if the scene stops exercising any asset, so it cannot silently drift behind
the pack.

Like the rest of ModKit, the example scene is CC0.
