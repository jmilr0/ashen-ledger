"""Bake Idle + Walk clips onto Ashen Ledger party companion GLBs.

Applies usable armature auto-weights (body) + sensible bone-parented props,
then exports looping Idle (breath/shift) and Walk (foot-plant) actions named
exactly for Engineering AnimationMixer: `Idle`, `Walk`.

Characters: clerk, sergeant, convers, guide, surgeon.

Rebuild (Blender 4.3.2 background):

  # Clerk first (Engineering early wire)
  /usr/bin/blender -b -P tools/bake_party_walk.py -- clerk

  # Remaining four
  /usr/bin/blender -b -P tools/bake_party_walk.py -- sergeant convers guide surgeon

  # Or all five
  /usr/bin/blender -b -P tools/bake_party_walk.py -- all

Equivalent per-character via existing makers (also bake clips after this change):
  /usr/bin/blender -b -P tools/make_clerk.py
  /usr/bin/blender -b -P tools/make_sergeant.py
  /usr/bin/blender -b -P tools/make_convers.py
  /usr/bin/blender -b -P tools/make_guide.py
  /usr/bin/blender -b -P tools/make_surgeon.py

Clip metadata (default):
  Idle — 48 frames @ 24 fps ≈ 2.000 s
  Walk — 28 frames @ 24 fps ≈ 1.167 s
"""
from __future__ import annotations

import os
import sys
import traceback

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import character_common as cc

PARTY = ('clerk', 'sergeant', 'convers', 'guide', 'surgeon')


def _parse_args(argv):
    # Blender passes script args after `--`
    if '--' in argv:
        argv = argv[argv.index('--') + 1:]
    else:
        argv = []
    argv = [a.strip().lower() for a in argv if a.strip()]
    if not argv or argv == ['all']:
        return list(PARTY)
    out = []
    for a in argv:
        if a == 'all':
            out.extend(PARTY)
        elif a in PARTY:
            out.append(a)
        else:
            raise SystemExit(f'Unknown character {a!r}; choose from {PARTY} or all')
    # preserve order, unique
    seen = set()
    ordered = []
    for a in out:
        if a not in seen:
            seen.add(a)
            ordered.append(a)
    return ordered


def _report_glb(slug):
    path = os.path.join(cc.OUT_DIR, f'{slug}.glb')
    size = os.path.getsize(path) if os.path.isfile(path) else 0
    print(f'GLB {path} bytes={size}')
    return path, size


def bake_clerk():
    import make_clerk as mc
    meshes, arm = mc.build_clerk()
    cc.apply_party_clips(arm, meshes)
    glb_path = os.path.join(cc.OUT_DIR, 'clerk.glb')
    # Use clerk's export to keep selection rules identical
    mc.export_glb(glb_path, export_animations=True)
    print('Exported', glb_path)
    if os.environ.get('ASHEN_SKIP_PREVIEWS', '').strip() not in ('1', 'true', 'yes'):
        mc.render_previews()
        mc.cleanup_preview_helpers()
        mc.export_glb(glb_path, export_animations=True)
        print('Re-exported clean', glb_path)
    else:
        print('Skipping previews (ASHEN_SKIP_PREVIEWS)')
    mesh_objs = [o for o in list(__import__('bpy').context.scene.objects) if o.type == 'MESH']
    b = mc.world_bounds(mesh_objs)
    tris = mc.count_tris(mesh_objs)
    meta = os.path.join(mc.PREV_DIR, 'clerk_scale.txt')
    with open(meta, 'w') as f:
        f.write(
            f"height_m={b['size'][2]:.4f}\n"
            f"width_x_m={b['size'][0]:.4f}\n"
            f"depth_y_m={b['size'][1]:.4f}\n"
            f"tris={tris}\n"
            f"capsule_diameter_m=0.60\n"
            f"formation_spacing_m=0.90 (context only)\n"
            f"target_height_m={mc.TARGET_HEIGHT}\n"
            f"clips=Idle({cc.IDLE_FRAMES}f@{cc.IDLE_FPS}fps),Walk({cc.WALK_FRAMES}f@{cc.WALK_FPS}fps)\n"
        )
    print('Wrote', meta)
    return glb_path


def bake_via_maker(module_name):
    mod = __import__(module_name)
    # finish_character now bakes Idle+Walk when bake_clips=True (default)
    return mod.build()


def bake_one(slug):
    print('=' * 60)
    print('Baking party clips for', slug)
    print('=' * 60)
    if slug == 'clerk':
        path = bake_clerk()
    else:
        path = bake_via_maker(f'make_{slug}')
    return _report_glb(slug)


def main():
    # Previews are slow in batch; set ASHEN_SKIP_PREVIEWS=0 to force.
    os.environ.setdefault('ASHEN_SKIP_PREVIEWS', '1')
    targets = _parse_args(sys.argv)
    print('Party bake targets:', targets)
    print(f'Idle {cc.IDLE_FRAMES}f @ {cc.IDLE_FPS}fps ({cc.IDLE_FRAMES/cc.IDLE_FPS:.3f}s)')
    print(f'Walk {cc.WALK_FRAMES}f @ {cc.WALK_FPS}fps ({cc.WALK_FRAMES/cc.WALK_FPS:.3f}s)')
    results = []
    for slug in targets:
        try:
            path, size = bake_one(slug)
            results.append((slug, path, size, 'ok'))
        except Exception as exc:
            traceback.print_exc()
            results.append((slug, None, 0, f'FAIL: {exc}'))
    print('\n=== bake_party_walk summary ===')
    for slug, path, size, status in results:
        print(f'  {slug}: {status} {path or ""} ({size} bytes)')
    failed = [r for r in results if r[3] != 'ok']
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
