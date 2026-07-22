22 procedurally generated meshes for Unreal Engine, Unity, three.js and Blender. **Public domain (CC0)** — commercial use, no attribution required.

![All 22 assets](https://raw.githubusercontent.com/JaronKBragg7337/asset-pack-ue-threejs-blender-unity/main/previews/_ContactSheet_web.png)

## Download

Grab **`ModKit-v1.0.zip`** below (16 MB) — meshes, previews and docs, no git clone needed.

## Contents

**Modular building kit (13)** — walls (straight, half, doorway, window, arch, corner), floor and ceiling slabs, pillar, stairs, railing, doorframe, parapet.

**Environment props (9)** — small and large crates, crate stack, barrel, pallet, pipe run, wall vent, wall sign, rubble pile.

~20,700 triangles for the whole set. Authored on a 4 m module with 3 m wall height, grid-corner pivots, 1 unit = 1 m.

## Formats

| Folder | Use it for |
|---|---|
| `exports/FBX_Nanite/` | Unreal 5 (Nanite), Unity |
| `exports/FBX_LOD/` | Mobile, older engines, anything without Nanite |
| `exports/GLTF/` | three.js, Godot, web viewers |
| `source/ModKit.blend` | Editing the originals (Blender 5.1) |

## No textures needed

Shading comes from geometry, not maps: exact-boolean watertight solids, a 1.2 cm bevel with hardened normals, and a weighted-normal pass. That's why the pieces read as solid under moving light with zero texture memory.

**Import normals — don't recompute them.** Letting your engine recalculate will soften every bevel and the pack will look muddy.

## Verified, not claimed

`docs/ue_validation.txt` is a real audit of the imported pack: all 22 meshes Nanite-enabled in the Nanite set, all 22 with 4-level LOD chains and non-increasing triangle counts, zero problems reported.

## MCP / AI agent support

UE 5.8's official `ModelContextProtocol` plugin and Blender's official Anthropic connector are both documented in the README, including the game-thread deadlock gotcha when probing Unreal's MCP server. `scripts/check_unreal_mcp.py` verifies the server is live.

## Known quirks

- Unreal ignores Blender's `LOD_` FBX null — `scripts/ue_lods.py` uses engine LOD groups instead.
- `StaticMeshEditorSubsystem` is `None` inside a commandlet; `EditorStaticMeshLibrary.set_lods` returns `-1` there.
- The UV column in the audit reads `0` — a commandlet artifact, not missing UVs.

Everything is procedural. Change four constants in `scripts/modkit_lib.py`, re-run one command, get the whole pack at different proportions.
