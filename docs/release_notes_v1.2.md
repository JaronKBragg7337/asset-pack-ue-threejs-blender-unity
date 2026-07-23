**38 procedurally generated meshes** for Unreal Engine, Unity, three.js and Blender. Public domain (CC0) — commercial use, no attribution.

### ▶ [Try every asset in your browser](https://jaronkbragg7337.github.io/asset-pack-ue-threejs-blender-unity/)

![All 38 assets](https://raw.githubusercontent.com/JaronKBragg7337/asset-pack-ue-threejs-blender-unity/main/previews/_ContactSheet_web.png)

## New in v1.2

**Roof corner and valley junctions** close the largest remaining gap in the modular roof set. L- and T-shaped buildings can now use a square hip corner and a cross-gable valley piece that match the existing roof pitch, thickness and overhang.

Both new meshes are procedurally generated, watertight manifolds with grid-corner pivots and complete FBX, LOD FBX, GLB, Blender and preview outputs. All 36 existing asset triangle counts remain unchanged.

## Industrial Outpost example scene

The release now includes a separate **70-instance Industrial Outpost** demo
built entirely from all 38 ModKit assets. Explore it in the
[live viewer](https://jaronkbragg7337.github.io/asset-pack-ue-threejs-blender-unity/docs/#example)
or download `ModKit-v1.2-Industrial-Outpost.zip` for Blender, GLB, FBX and the
complete transform manifest.

### July 23 geometry corrections

- centred and base-aligned the Industrial Outpost doorframe and door leaf with
  the doorway wall cut
- rebuilt `SM_Barrel_Dented` as one continuous, deformed ribbed shell instead
  of boolean-separated barrel slices
- corrected `SM_Pallet` with three perpendicular lower runners and nine support
  blocks beneath its five upper deckboards

## Download

**`ModKit-v1.2.zip`** below contains the complete pack — no clone or build step required.

| Folder | Use it for |
|---|---|
| `exports/FBX_Nanite/` | Unreal 5 (Nanite), Unity |
| `exports/FBX_LOD/` | Mobile, older engines, no-Nanite pipelines |
| `exports/GLTF/` | three.js, Godot, web |
| `source/ModKit.blend` | Editing the originals (Blender 5.1) |
| `scripts/` | Procedurally rebuilding or extending the entire pack |

## Verified

- all 38 assets load in the public three.js viewer
- all 38 meshes imported into Unreal Engine 5.8 with Nanite enabled
- all 38 LOD assets have four non-increasing LOD levels
- zero Unreal validation problems
- zero non-manifold edges on the new roof junctions

## Still no textures

Shading remains geometric: watertight solids, a 1.2 cm bevel with hardened normals, and a weighted-normal pass. **Import normals — don't recompute them**, or every bevel softens and the pack looks muddy.
