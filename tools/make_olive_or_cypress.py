"""Blender: Mediterranean cypress (Broken Seal) — period tree, not fantasy pine.

Cupressus sempervirens — tall narrow column, Occitan wayside / cloister garden.
Dirt-and-mail 1208 — muted sage foliage, rough bark, no glow, no Kenney pine kit.
Rebuild:
  /usr/bin/blender -b -P tools/make_olive_or_cypress.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
import bpy
from mathutils import Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import building_shell_common as bc

STEM = 'olive_or_cypress'
# Tall narrow cypress ~5.5–6.5 m; tight trunk footprint for off-lane plant


def cylinder_shell(bm, cx, cy, z0, z1, r0, r1, segs=10):
    bot, top = [], []
    for i in range(segs):
        a = (i / segs) * math.tau
        bot.append(bm.verts.new((cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0)))
        top.append(bm.verts.new((cx + r1 * math.cos(a), cy + r1 * math.sin(a), z1)))
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((bot[i], bot[i2], top[i2], top[i]))
    bc_v = bm.verts.new((cx, cy, z0))
    tc = bm.verts.new((cx, cy, z1))
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((bc_v, bot[i2], bot[i]))
        bm.faces.new((tc, top[i], top[i2]))


def make_trunk(bark):
    parts = []
    # Root flare
    bm = bmesh.new()
    cylinder_shell(bm, 0, 0, 0.0, 0.25, 0.18, 0.12, segs=10)
    for v in bm.verts:
        v.co.x += 0.015 * math.sin(v.co.y * 12 + v.co.z * 5)
        v.co.y += 0.012 * math.cos(v.co.x * 10)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Cypress_Root', bm, bark, True))

    # Main trunk — slight lean
    bm = bmesh.new()
    segs, n_rings = 10, 8
    rings = []
    for ri in range(n_rings + 1):
        t = ri / n_rings
        z = 0.2 + t * 5.4
        r = 0.11 * (1.0 - 0.55 * t) + 0.04
        lean = 0.04 * t
        ring = []
        for i in range(segs):
            a = (i / segs) * math.tau
            # bark roughness
            rr = r * (1.0 + 0.06 * math.sin(a * 3 + z * 2))
            ring.append(bm.verts.new((rr * math.cos(a) + lean, rr * math.sin(a), z)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for ri in range(n_rings):
        for i in range(segs):
            i2 = (i + 1) % segs
            bm.faces.new((rings[ri][i], rings[ri][i2], rings[ri + 1][i2], rings[ri + 1][i]))
    # tip cap
    tip = bm.verts.new((0.04, 0.0, 5.75))
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((tip, rings[-1][i], rings[-1][i2]))
    # bottom cap
    botc = bm.verts.new((0.0, 0.0, 0.2))
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((botc, rings[0][i2], rings[0][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Cypress_Trunk', bm, bark, True))
    return bc.join_named('Cypress_Wood', parts)


def make_foliage(foliage, foliage_dark):
    """Stacked tapered ellipsoids — Mediterranean cypress silhouette, not pine boughs."""
    parts = []
    layers = [
        # (z_center, rx, ry, rz, mat_dark)
        (1.4, 0.55, 0.52, 0.55, False),
        (2.1, 0.58, 0.55, 0.60, True),
        (2.85, 0.52, 0.50, 0.58, False),
        (3.55, 0.45, 0.43, 0.55, True),
        (4.2, 0.38, 0.36, 0.50, False),
        (4.75, 0.28, 0.27, 0.42, True),
        (5.2, 0.18, 0.17, 0.35, False),
        (5.5, 0.10, 0.10, 0.28, True),
    ]
    for i, (cz, rx, ry, rz, dark) in enumerate(layers):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=1.0)
        lean = 0.03 * (cz / 5.5)
        for v in bm.verts:
            v.co.x = v.co.x * rx + lean
            v.co.y *= ry
            v.co.z = v.co.z * rz + cz
            # irregular silhouette
            n = math.sin(v.co.x * 9 + i) * math.cos(v.co.y * 8 + cz)
            v.co.x += 0.02 * n
            v.co.y += 0.018 * math.sin(v.co.z * 6 + i)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mat = foliage_dark if dark else foliage
        parts.append(bc.bm_to_object(f'_fol{i}', bm, mat, True))

    # Sparse low skirt / dead lower needles (muted)
    for i, (ox, oy, oz, s) in enumerate((
        (-0.25, 0.15, 0.9, 0.22), (0.2, -0.18, 0.85, 0.18), (0.05, 0.22, 1.05, 0.15),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=s)
        for v in bm.verts:
            v.co.z *= 0.7
            v.co += Vector((ox, oy, oz))
        parts.append(bc.bm_to_object(f'_skirt{i}', bm, foliage_dark, True))

    return bc.join_named('Cypress_Foliage', parts)


def make_ground(mud, dirt):
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=0.35)
    for v in bm.verts:
        v.co.z *= 0.18
        v.co.x *= 1.2
        v.co += Vector((0, 0, 0.02))
        if v.co.z < 0:
            v.co.z = 0.002
    parts.append(bc.bm_to_object('Cypress_Earth', bm, dirt, True))
    for i, (mx, my) in enumerate(((-0.25, 0.2), (0.22, -0.18), (-0.1, -0.25))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=3, radius=0.1)
        for v in bm.verts:
            v.co.z *= 0.25
            v.co += Vector((mx, my, 0.015))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_mud{i}', bm, mud, True))
    return bc.join_named('Cypress_Ground', parts)


def build():
    bc.clear_scene()
    # Muted sage / dusty green — winter Occitan, not neon fantasy foliage
    foliage = bc.mat('Cypress_Foliage', (0.28, 0.34, 0.24), 0.92, specular=0.08)
    foliage_dark = bc.mat('Cypress_FoliageDark', (0.22, 0.26, 0.18), 0.94, specular=0.06)
    bark = bc.mat('Cypress_Bark', (0.32, 0.26, 0.18), 0.95, specular=0.08)
    mud = bc.mat('Cypress_Mud', bc.PALETTE['mud'], 0.97, specular=0.05)
    dirt = bc.mat('Cypress_Dirt', (0.36, 0.30, 0.20), 0.96, specular=0.05)
    meshes = [
        make_ground(mud, dirt),
        make_trunk(bark),
        make_foliage(foliage, foliage_dark),
    ]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, 0, 2.8),
                       views=[
                           ('front', (0.0, -8.5, 3.2)),
                           ('threequarter', (5.5, -6.5, 4.0)),
                       ])
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'species=cupressus_sempervirens_mediterranean_cypress',
        'not_fantasy_pine=1',
        'footprint_trunk_m~=0.4',
        'canopy_width_m~=1.2',
        'collision=tight_to_trunk_foliage_visual_ok',
        'style=occitan_1208_dirt_and_mail_no_glow',
        'off_lane=1',
        'road_clear_m=2.4',
        'road_crown_x=[-1.2,1.2]_no_colliders',
        'place_band=soft_shoulder_|x|_1.2-4_preferred',
        'hub_anchor_hint=Fontfroide_(-6,+38)_mile_(0,+22)_shoulders_wayside',
        'place=off_road_wayside_cloister_garden_edge',
    ])


if __name__ == '__main__':
    main()
