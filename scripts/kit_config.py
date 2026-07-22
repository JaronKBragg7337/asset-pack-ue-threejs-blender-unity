"""
kit_config.py -- every tunable in the pack, in one place.

This is the ONLY file you should need to edit to re-roll the whole kit at a
different scale, wall height, or level of edge detail. Nothing else in the
codebase should contain a hard-coded dimension.

Units are metres. 1 m = 1 Blender unit = 100 Unreal units = 1 Unity unit.

Usage:
    import kit_config as cfg
    cfg.MODULE          # 4.0

    # or start from a preset
    cfg.apply_preset("chunky")
"""

# --------------------------------------------------------------- grid
MODULE = 4.0            # width of one modular bay
WALL_HEIGHT = 3.0       # floor to ceiling
WALL_THICKNESS = 0.20
FLOOR_THICKNESS = 0.20

# --------------------------------------------------------------- openings
DOOR_WIDTH = 1.20
DOOR_HEIGHT = 2.20
WINDOW_WIDTH = 1.80
WINDOW_HEIGHT = 1.20
WINDOW_SILL = 1.00      # height of the window base off the floor
ARCH_SPAN = 1.80        # width of the arched opening
ARCH_SPRING = 1.45      # height where the arch's semicircle begins


# --------------------------------------------------------------- detailing
# The single biggest lever on how the pack reads. Bevel width controls how
# wide the lit edge highlight is; too small and edges look razor-sharp and
# CG, too large and everything looks soft and inflated.
BEVEL_WIDTH = 0.012     # 1.2 cm
BEVEL_SEGMENTS = 2
BEVEL_ANGLE_LIMIT = 30.0    # degrees; edges sharper than this get bevelled
WEIGHTED_NORMAL_WEIGHT = 60

RIB_WIDTH = 0.18        # structural rib framing each wall panel
RECESS_DEPTH = 0.045    # how deep the recessed panel bays sit
BAY_INSET = 0.18        # gap between the rib frame and the bay
GROOVE = 0.05           # floor/ceiling tile groove width
TILE_DEPTH = 0.04       # how deep the tile grooves cut

# --------------------------------------------------------------- roofs
ROOF_THICKNESS = 0.18
ROOF_RISE = 1.30        # height gain from eave to ridge across half a module
ROOF_OVERHANG = 0.22    # how far the roof projects past the wall below
ROOF_TRIM_DEPTH = 0.14  # eave / fascia board depth
ROOF_SEAM_HALF_WIDTH = 0.035  # half-width of standing-seam roof ribs
ROOF_SEAM_LIFT = 0.05         # height of standing seams above the roof skin
ROOF_SEAM_COUNT = 5           # ribs distributed evenly across a roof span

# --------------------------------------------------------------- UVs
UV_ANGLE_LIMIT = 66.0   # smart-project seam angle, degrees
UV_ISLAND_MARGIN = 0.004

# --------------------------------------------------------------- LODs
# Used only by the Blender-side LOD export. Unreal builds its own chains via
# engine LOD groups (see scripts/ue_lods.py) because its reducer is better.
LOD_RATIOS = (1.0, 0.55, 0.28, 0.12)
LOD_SCREEN_SIZES = (1.0, 0.45, 0.18, 0.06)

# --------------------------------------------------------------- rendering
PREVIEW_RESOLUTION = 640
CONTACT_SHEET_COLUMNS = 6


# --------------------------------------------------------------- presets
# Each preset is a partial override of the values above. Anything not listed
# keeps its default.
PRESETS = {
    "default": {},

    # Larger bays and heavier trim -- reads well for industrial/sci-fi.
    "chunky": {
        "MODULE": 4.0,
        "WALL_HEIGHT": 3.5,
        "WALL_THICKNESS": 0.30,
        "BEVEL_WIDTH": 0.020,
        "BEVEL_SEGMENTS": 3,
        "RIB_WIDTH": 0.26,
        "RECESS_DEPTH": 0.070,
    },

    # Tighter detail for close-up hero pieces or high-end renders.
    "fine": {
        "BEVEL_WIDTH": 0.006,
        "BEVEL_SEGMENTS": 3,
        "RIB_WIDTH": 0.12,
        "RECESS_DEPTH": 0.030,
    },

    # Small-scale interiors -- 2 m bays, lower ceilings.
    "compact": {
        "MODULE": 2.0,
        "WALL_HEIGHT": 2.4,
        "DOOR_HEIGHT": 2.00,
        "WINDOW_WIDTH": 1.00,
        "RIB_WIDTH": 0.12,
    },
}


def apply_preset(name):
    """Overwrite this module's constants with a named preset.

    Call before importing modkit_lib, or call reload_dependents() after.
    Raises KeyError on an unknown preset so typos fail loudly rather than
    silently building the default kit.
    """
    if name not in PRESETS:
        raise KeyError("unknown preset %r -- available: %s"
                       % (name, ", ".join(sorted(PRESETS))))
    module = globals()
    for key, value in PRESETS[name].items():
        if key not in module:
            raise KeyError("preset %r sets unknown constant %r" % (name, key))
        module[key] = value
    return {k: module[k] for k in PRESETS[name]}


def describe():
    """Human-readable dump of the active configuration."""
    keys = ("MODULE", "WALL_HEIGHT", "WALL_THICKNESS", "FLOOR_THICKNESS",
            "DOOR_WIDTH", "DOOR_HEIGHT", "WINDOW_WIDTH", "WINDOW_HEIGHT",
            "BEVEL_WIDTH", "BEVEL_SEGMENTS", "RIB_WIDTH", "RECESS_DEPTH")
    width = max(len(k) for k in keys)
    return "\n".join("%-*s %s" % (width, k, globals()[k]) for k in keys)


def validate():
    """Catch parameter combinations that would produce broken geometry."""
    problems = []
    if DOOR_HEIGHT >= WALL_HEIGHT:
        problems.append("DOOR_HEIGHT (%.2f) must be below WALL_HEIGHT (%.2f)"
                        % (DOOR_HEIGHT, WALL_HEIGHT))
    if WINDOW_SILL + WINDOW_HEIGHT >= WALL_HEIGHT:
        problems.append("window top (%.2f) exceeds WALL_HEIGHT (%.2f)"
                        % (WINDOW_SILL + WINDOW_HEIGHT, WALL_HEIGHT))
    if ARCH_SPRING + ARCH_SPAN / 2.0 >= WALL_HEIGHT:
        problems.append("arch apex (%.2f) exceeds WALL_HEIGHT (%.2f)"
                        % (ARCH_SPRING + ARCH_SPAN / 2.0, WALL_HEIGHT))
    if DOOR_WIDTH + 2 * RIB_WIDTH >= MODULE:
        problems.append("door + ribs (%.2f) wider than MODULE (%.2f)"
                        % (DOOR_WIDTH + 2 * RIB_WIDTH, MODULE))
    if BEVEL_WIDTH * 2 >= min(RIB_WIDTH, WALL_THICKNESS):
        problems.append("BEVEL_WIDTH (%.3f) too large for RIB_WIDTH/thickness"
                        % BEVEL_WIDTH)
    if ROOF_SEAM_HALF_WIDTH * 2 >= MODULE / (ROOF_SEAM_COUNT + 1):
        problems.append("roof seams are too wide for their spacing")
    if ROOF_SEAM_LIFT >= ROOF_THICKNESS:
        problems.append("ROOF_SEAM_LIFT must be below ROOF_THICKNESS")
    return problems
