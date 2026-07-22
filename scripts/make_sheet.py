"""
make_sheet.py -- composite the individual asset renders into one contact
sheet. Uses Blender's bundled numpy so there is no extra dependency.

    blender -b --factory-startup --python scripts/make_sheet.py
"""
import os
import glob
import numpy as np
import bpy

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PREV = os.path.join(ROOT, "previews")
COLS = 6


def load(path):
    img = bpy.data.images.load(path)
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    bpy.data.images.remove(img)
    return buf.reshape(h, w, 4)      # bottom-up, matching Blender's origin


def main():
    files = sorted(f for f in glob.glob(os.path.join(PREV, "SM_*.png")))
    if not files:
        print("SHEET no source renders found")
        return
    tiles = [load(f) for f in files]
    th, tw = tiles[0].shape[:2]
    rows = (len(tiles) + COLS - 1) // COLS

    sheet = np.zeros((rows * th, COLS * tw, 4), dtype=np.float32)
    sheet[..., 3] = 1.0
    for i, tile in enumerate(tiles):
        r, c = divmod(i, COLS)
        r = rows - 1 - r                      # fill top-down visually
        sheet[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = tile

    out = bpy.data.images.new("ContactSheet", COLS * tw, rows * th, alpha=True)
    out.pixels.foreach_set(sheet.ravel())
    out.filepath_raw = os.path.join(PREV, "_ContactSheet.png")
    out.file_format = 'PNG'
    out.save()
    print("SHEET %d tiles -> %dx%d" % (len(tiles), COLS * tw, rows * th))


if __name__ == "__main__":
    main()
