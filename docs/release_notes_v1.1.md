**36 procedurally generated meshes** for Unreal Engine, Unity, three.js and Blender. Public domain (CC0) — commercial use, no attribution.

### ▶ [Try it in your browser](https://jaronkbragg7337.github.io/asset-pack-ue-threejs-blender-unity/)

Spin every piece, toggle wireframe, read triangle counts and real-world dimensions. No download.

![All 36 assets](https://raw.githubusercontent.com/JaronKBragg7337/asset-pack-ue-threejs-blender-unity/main/previews/_ContactSheet_web.png)

## New in v1.1

**Roofs (4)** — flat panel with kerb, pitched gable with standing seams, ridge cap, eave fascia + gutter.

**Wall variants (2)** — blast-damaged with a ragged breach and impact pocks; bolt-plated reinforced.

**Interior (4)** — I-beam, braced support column, door leaf sized to the doorway wall, recessed floor hatch.

**Prop states (4)** — open barrel (hollowed), dented barrel, broken crate, flat debris scatter.

**Interactive viewer** — three.js, on GitHub Pages, with an asset picker, text filter, wireframe toggle and deep links (`#SM_Barrel_Open`).

**`kit_config.py`** — every dimension in one file, with `chunky` / `fine` / `compact` presets and a `validate()` pass that refuses impossible combinations instead of emitting broken geometry.

**`AGENTS.md` + `CONTRIBUTING.md`** — conventions for AI agents and humans, so the pack can be extended in parallel.

The original 22 assets are unchanged — identical triangle counts, verified by manifest diff.

## Download

**`ModKit-v1.1.zip`** below — meshes, previews and docs, no clone needed.

| Folder | Use it for |
|---|---|
| `exports/FBX_Nanite/` | Unreal 5 (Nanite), Unity |
| `exports/FBX_LOD/` | Mobile, older engines, no-Nanite pipelines |
| `exports/GLTF/` | three.js, Godot, web |
| `source/ModKit.blend` | Editing the originals (Blender 5.1) |

## Verified, not claimed

`docs/ue_validation.txt` is a real audit of the imported pack: **36/36 Nanite-enabled**, **36/36 with 4-level LOD chains** and non-increasing triangle counts, **zero problems**.

Two viewer bugs were found by testing in an actual browser rather than assuming the code worked:

- Models spun about their **pivot** — and kit pivots sit at the grid corner (that's what makes them snap together), so pieces swung out of frame. Fixed with a bounding-box-centred pivot group.
- `renderer.setSize(w, h, false)` resized the drawing buffer but left the canvas CSS box at its 300×150 default, rendering everything off-centre.

## Still no textures

Shading is geometric: exact-boolean watertight solids, a 1.2 cm bevel with hardened normals, and a weighted-normal pass. **Import normals — don't recompute them**, or every bevel softens and the pack looks muddy.
