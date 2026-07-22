"""
test_config.py -- sanity checks for kit_config. Pure Python, no Blender needed.

    python scripts/test_config.py
"""
import importlib
import sys

import kit_config as cfg

failures = []

print("default:", cfg.validate() or "OK")
if cfg.validate():
    failures.append("default config is invalid")

for preset in sorted(cfg.PRESETS):
    importlib.reload(cfg)
    changed = cfg.apply_preset(preset)
    problems = cfg.validate()
    print("%-9s -> %d overrides, validate: %s"
          % (preset, len(changed), problems or "OK"))
    if problems:
        failures.append("preset %r produces invalid geometry: %s"
                        % (preset, problems))

# validation must actually catch a bad combination
importlib.reload(cfg)
cfg.WALL_HEIGHT = 2.0          # shorter than the 2.2 m door
caught = cfg.validate()
print("\nbroken config (wall 2.0 m, door 2.2 m) ->", len(caught), "problem(s)")
for problem in caught:
    print("   ", problem)
if not caught:
    failures.append("validate() failed to catch a door taller than the wall")

# unknown presets must raise, not silently no-op
importlib.reload(cfg)
try:
    cfg.apply_preset("does_not_exist")
    failures.append("unknown preset did not raise")
except KeyError as exc:
    print("\nunknown preset raises:", exc)

print("\n%s" % ("FAILED: " + "; ".join(failures) if failures else "ALL PASS"))
sys.exit(1 if failures else 0)
