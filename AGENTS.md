# AGENTS.md

Instructions for AI coding agents (Codex, Claude Code, Cursor, Gemini) working
in this repo. Humans: see `README.md` and `CONTRIBUTING.md`.

## What this repo is

A procedurally generated CC0 asset pack. **Every mesh is produced by script.**
There are no hand-modelled files. If you cannot express an asset as Python that
runs in Blender headless, it does not belong here.

## Golden rules

1. **Never hard-code a dimension.** Every measurement comes from
   `scripts/kit_config.py`. If you need a new constant, add it there.
2. **Never commit a mesh you did not generate.** `exports/` and `source/` are
   build outputs. Change the generator, re-run it, commit the result.
3. **Every mesh must be a single watertight manifold.** Use `L.weld()` to union
   overlapping parts, not loose abutting boxes. This is what makes the bevel
   produce unbroken highlight edges.
4. **Run the build before you commit.** A change that doesn't regenerate
   cleanly is not done.

## Setup

Blender 5.x must be on PATH (or use the full path to `blender.exe`).
No pip installs are needed — everything uses Blender's bundled Python.

```bash
# fast, no Blender: validates config presets
python scripts/test_config.py

# full rebuild: writes exports/, source/ModKit.blend, docs/asset_manifest.csv
blender -b --factory-startup --python scripts/build_kit.py

# regenerate preview renders + contact sheet (slow, ~5 min)
blender -b source/ModKit.blend   --python scripts/render_previews.py
blender -b --factory-startup --python scripts/make_sheet.py
```


## Adding an asset — the whole procedure

1. Write a function in `scripts/build_kit.py` that returns
   `L.finish(bm, name, material=MATS[...], collection=L.get_collection(...))`.
2. Add one lambda to `define_assets()`.
3. Run the build. Confirm your asset appears in the `BUILT` output with a
   sane triangle count.
4. Regenerate previews if you want it in the contact sheet.

Minimal example:

```python
def roof_flat(name, width=M, depth=M, mat="M_Concrete"):
    """Flat roof panel with a drip lip. Origin at grid corner."""
    bm = bmesh.new()
    L.add_box(bm, (0, 0, 0), (width, depth, cfg.FLOOR_THICKNESS))
    L.weld(bm, (-0.04, -0.04, 0), (width + 0.04, depth + 0.04, 0.06))
    return L.finish(bm, name, material=MATS[mat],
                    collection=L.get_collection("Kit"))
```

## Naming

| Rule | Example |
|---|---|
| `SM_` prefix (static mesh) | `SM_Wall_Straight_4m` |
| PascalCase category first | `SM_Roof_Flat_4m` |
| Size suffix where it varies | `SM_Wall_Half_2m` |
| No spaces, no engine names in the asset | not `SM_UE_Wall` |

Kit pieces go in the `"Kit"` collection, props in `"Props"`.

## Pivots — get these right

* **Kit pieces** — origin at the **grid corner** (min X, min Y, min Z).
* **Floor/ceiling slabs** — origin at the corner of the **top surface**
  (geometry spans `z = -thickness .. 0`).
* **Props** — origin at **base centre** (centre X/Y, min Z).

Getting this wrong is the single most common way to make a piece that looks
fine in isolation and is useless in a level.


## Geometry helpers (`scripts/modkit_lib.py`, imported as `L`)

| Function | Purpose |
|---|---|
| `L.add_box(bm, p0, p1)` | Axis-aligned box. Use for the **first** part of a mesh. |
| `L.weld(bm, p0, p1)` | Boolean UNION a box in. Use for every subsequent part. |
| `L.carve(bm, p0, p1)` | Boolean DIFFERENCE a box out. |
| `L.add_cylinder(bm, r, depth, segments, center, axis)` | Cylinder. |
| `L.carve_cylinder(bm, r, depth, ...)` | Boolean a cylinder out (arches, holes). |
| `L.bool_bm(bm, cutter_bm, op)` | Boolean against an arbitrary bmesh. |
| `L.jitter(bm, amount, seed)` | Randomise vertices — turns blocky unions into rock. |
| `L.recess_faces(bm, faces, border, depth)` | Inset + push faces in (panels). |
| `L.finish(bm, name, ...)` | Weld, bevel, weighted-normal, unwrap, assign material. |

`L.finish()` is mandatory — it applies the shading treatment that makes the
pack coherent. Don't build objects any other way.

## Do not

* Add a dependency. Blender's bundled Python only. No pip.
* Add normal-map bakes or texture files. Shading is geometric by design.
* Edit files under `exports/`, `previews/` or `source/` by hand.
* Change `BEVEL_WIDTH` casually — it defines the pack's whole visual identity.
* Point two AI agents at Unreal's MCP server simultaneously (see below).

## Working alongside other agents

Blender-side work is **safe to parallelise** — each `blender -b` run is its own
process with no shared state. Multiple agents can add assets concurrently; the
only conflict surface is `define_assets()` in `build_kit.py`.

Unreal MCP is **not** safe to parallelise. The editor runs one MCP server on
one port (`127.0.0.1:8000`) and executes tool calls **serially on the game
thread**. Two agents issuing overlapping calls will interleave into one queue
and produce confusing partial state. One agent at a time, or use separate
editor instances on different ports (`-ModelContextProtocolPort=8123`).

Prefer the headless scripts (`ue_import.py`, `ue_lods.py`, `ue_validate.py`)
over MCP for anything reproducible — they run in their own process and don't
need an editor open at all.


## Definition of done

Before you consider a change complete:

- [ ] `python scripts/test_config.py` exits 0
- [ ] `blender -b --factory-startup --python scripts/build_kit.py` runs with no
      `FAILED` or `Traceback` lines
- [ ] Your asset appears in the `BUILT` list with a plausible triangle count
      (roughly 200–2,500 for this pack)
- [ ] `docs/asset_manifest.csv` regenerated
- [ ] Triangle counts for **existing** assets are unchanged, unless changing
      them was the point. A diff here means you altered shared geometry.

Verify that last one explicitly:

```bash
cp docs/asset_manifest.csv /tmp/before.csv
blender -b --factory-startup --python scripts/build_kit.py
diff /tmp/before.csv docs/asset_manifest.csv
```

## Roadmap — good next contributions

Done in v1.1: roofs, damaged/reinforced walls, interior pieces, prop states,
and the three.js viewer on GitHub Pages.

Ordered roughly by value:

1. **Roof corner + valley pieces** — the roof set covers flat, pitched, ridge
   and eave, but has no corner or valley, so L-shaped buildings can't be
   roofed cleanly. Highest-value gap right now.
2. **More wall variants** — boarded-up, pipework-clad, half-height with
   railing, windowed double-height.
3. **Example scenes** — one small demo level per engine showing how pieces fit
   together. A `build_demo_scene.py` that assembles a building from the kit
   inside Blender would serve all three engines at once.
4. **Vertex colours or a proper master material** in the .blend for better
   default shading (currently flat placeholder PBR).
5. **Stair variants** — spiral, half-landing, open-tread industrial.
6. **A `--preset` CLI flag** for `build_kit.py` so the chunky/fine/compact
   presets can be built without editing `kit_config.py`.

If you add a roof corner, match `SM_Roof_Pitched_4m`: same `ROOF_RISE`, same
standing-seam spacing, same overhang. Mismatched roof pitch is immediately
obvious in a level.

Keep the 4 m grid and the pivot conventions for anything modular. A roof that
doesn't line up with a 4 m wall is worse than no roof.
