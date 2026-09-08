"""Blender: Wooden post + iron leper bell (Broken Seal).

Act III leper beat — pairs narrative leper bell. Weathered oak post, iron
bracket, dull cast bell, hemp cord. Dirt-and-mail Occitania 1208 — NO glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_leper_bell_post.py
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

STEM = 'leper_bell_post'


def cylinder_bm(bm, cx, cy, z0, z1, r, segs=10):
    bot, top = [], []
    for i in range(segs):
        a = (i / segs) * math.tau
        bot.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z0)))
        top.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z1)))
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


def make_post(oak, oak_grey, limestone, mud):
    parts = []
    # Stone footing
    bm = bmesh.new()
    bc.box_bm(bm, -0.16, 0.16, -0.14, 0.14, 0.0, 0.18)
    bc.wear_stone(bm, amp=0.008, seed=1.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Bell_Footing', bm, limestone, False))

    # Post — slightly lean, weathered
    bm = bmesh.new()
    bc.box_bm(bm, -0.07, 0.07, -0.065, 0.065, 0.15, 2.15)
    for v in bm.verts:
        # taper slightly
        t = (v.co.z - 0.15) / 2.0
        v.co.x *= 1.0 - 0.12 * t
        v.co.y *= 1.0 - 0.12 * t
        v.co.x += 0.025 * t  # lean
        v.co.x += 0.006 * math.sin(v.co.z * 7)
    parts.append(bc.bm_to_object('Bell_Post', bm, oak_grey, False))

    # Cap board
    bm = bmesh.new()
    bc.box_bm(bm, -0.10, 0.12, -0.09, 0.09, 2.12, 2.22)
    parts.append(bc.bm_to_object('Bell_Cap', bm, oak, False))

    # Mud skirts
    for i, (mx, my) in enumerate(((-0.12, 0.08), (0.10, -0.09), (-0.08, -0.10))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=3, radius=0.07)
        for v in bm.verts:
            v.co.z *= 0.3
            v.co += Vector((mx, my, 0.02))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_mud{i}', bm, mud, True))

    return bc.join_named('Bell_Wood', parts)


def make_bracket_and_bell(iron, iron_dull, hemp):
    parts = []
    # Iron bracket arm sticking out +Y (road-facing side of post)
    # Vertical strap on post
    bm = bmesh.new()
    bc.box_bm(bm, -0.04, 0.08, 0.05, 0.08, 1.55, 1.95)
    parts.append(bc.bm_to_object('Bell_Strap', bm, iron, False))

    # Horizontal arm
    bm = bmesh.new()
    bc.box_bm(bm, -0.03, 0.05, 0.06, 0.42, 1.78, 1.88)
    parts.append(bc.bm_to_object('Bell_Arm', bm, iron, False))

    # Diagonal brace
    bm = bmesh.new()
    bc.box_bm(bm, -0.02, 0.04, 0.08, 0.32, 1.60, 1.68)
    for v in bm.verts:
        t = (v.co.y - 0.08) / 0.24
        v.co.z += 0.18 * t
    parts.append(bc.bm_to_object('Bell_Brace', bm, iron_dull, False))

    # Hook eye at arm tip
    bm = bmesh.new()
    cylinder_bm(bm, 0.01, 0.40, 1.70, 1.80, 0.025, segs=8)
    parts.append(bc.bm_to_object('Bell_Eye', bm, iron, True))

    # Bell body — classic flared profile (dull cast iron, no shine)
    bm = bmesh.new()
    segs = 12
    profile = [
        # (z_rel, r) from top of bell
        (0.00, 0.04),
        (0.04, 0.05),
        (0.10, 0.10),
        (0.18, 0.13),
        (0.28, 0.15),
        (0.35, 0.16),
        (0.38, 0.17),  # lip
    ]
    rings = []
    cx, cy, z_top = 0.01, 0.40, 1.55
    for z_rel, r in profile:
        ring = []
        for i in range(segs):
            a = (i / segs) * math.tau
            # slight oval wear
            rr = r * (1.0 + 0.04 * math.sin(a * 2))
            ring.append(bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a), z_top - z_rel)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for ri in range(len(rings) - 1):
        for i in range(segs):
            i2 = (i + 1) % segs
            bm.faces.new((rings[ri][i], rings[ri][i2], rings[ri + 1][i2], rings[ri + 1][i]))
    # top cap
    tc = bm.verts.new((cx, cy, z_top + 0.02))
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((tc, rings[0][i], rings[0][i2]))
    # open bottom — inner lip ring
    inner = []
    for i in range(segs):
        a = (i / segs) * math.tau
        inner.append(bm.verts.new((cx + 0.12 * math.cos(a), cy + 0.12 * math.sin(a), z_top - 0.36)))
    bm.verts.ensure_lookup_table()
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((rings[-1][i], rings[-1][i2], inner[i2], inner[i]))
    ic = bm.verts.new((cx, cy, z_top - 0.34))
    for i in range(segs):
        i2 = (i + 1) % segs
        bm.faces.new((ic, inner[i], inner[i2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Bell_Body', bm, iron_dull, True))

    # Crown loop on bell
    bm = bmesh.new()
    cylinder_bm(bm, cx, cy, z_top + 0.01, z_top + 0.10, 0.02, segs=6)
    parts.append(bc.bm_to_object('Bell_Crown', bm, iron, True))

    # Clapper stub inside (barely visible)
    bm = bmesh.new()
    cylinder_bm(bm, cx, cy, z_top - 0.28, z_top - 0.08, 0.018, segs=6)
    parts.append(bc.bm_to_object('Bell_Clapper', bm, iron, True))

    # Hemp suspension cord from eye to crown
    bm = bmesh.new()
    path = [
        Vector((cx, cy, 1.72)),
        Vector((cx, cy, 1.68)),
        Vector((cx, cy, z_top + 0.08)),
    ]
    r = 0.01
    rings = []
    for p in path:
        ring = []
        for s in range(5):
            a = (s / 5) * math.tau
            ring.append(bm.verts.new((p.x + r * math.cos(a), p.y + r * math.sin(a), p.z)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for k in range(len(rings) - 1):
        for s in range(5):
            s2 = (s + 1) % 5
            bm.faces.new((rings[k][s], rings[k][s2], rings[k + 1][s2], rings[k + 1][s]))
    parts.append(bc.bm_to_object('Bell_Cord', bm, hemp, True))

    # Pull cord hanging down for ringing
    bm = bmesh.new()
    path = []
    for k in range(8):
        t = k / 7
        path.append(Vector((
            cx + 0.08 + 0.02 * math.sin(t * 3),
            cy + 0.05,
            1.55 - t * 0.95,
        )))
    rings = []
    for p in path:
        ring = []
        for s in range(5):
            a = (s / 5) * math.tau
            ring.append(bm.verts.new((p.x + 0.008 * math.cos(a), p.y + 0.008 * math.sin(a), p.z)))
        rings.append(ring)
    bm.verts.ensure_lookup_table()
    for k in range(len(rings) - 1):
        for s in range(5):
            s2 = (s + 1) % 5
            bm.faces.new((rings[k][s], rings[k][s2], rings[k + 1][s2], rings[k + 1][s]))
    parts.append(bc.bm_to_object('Bell_Pull', bm, hemp, True))

    # Small wooden bead / handle at pull end
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=0.03)
    for v in bm.verts:
        v.co.z *= 1.3
        v.co += Vector((cx + 0.08, cy + 0.05, 0.58))
    oak = bc.mat('Bell_HandleOak', bc.PALETTE['oak'], 0.88, specular=0.15)
    parts.append(bc.bm_to_object('Bell_Handle', bm, oak, True))

    return bc.join_named('Bell_Iron', parts)


def build():
    bc.clear_scene()
    oak = bc.mat('Bell_Oak', bc.PALETTE['oak'], 0.88, specular=0.18)
    oak_grey = bc.mat('Bell_OakWeathered', (0.38, 0.32, 0.24), 0.92, specular=0.12)
    limestone = bc.mat('Bell_Limestone', bc.PALETTE['limestone'], 0.92, specular=0.12)
    mud = bc.mat('Bell_Mud', bc.PALETTE['mud'], 0.97, specular=0.05)
    # Dull iron — low metallic, no glow
    iron = bc.mat('Bell_Iron', (0.28, 0.26, 0.24), 0.55, metallic=0.45, specular=0.35)
    iron_dull = bc.mat('Bell_IronDull', (0.24, 0.22, 0.20), 0.70, metallic=0.30, specular=0.25)
    hemp = bc.mat('Bell_Hemp', (0.42, 0.36, 0.24), 0.92, specular=0.1)
    meshes = [
        make_post(oak, oak_grey, limestone, mud),
        make_bracket_and_bell(iron, iron_dull, hemp),
    ]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0.05, 0.15, 1.2),
                       views=[
                           ('front', (0.05, -3.2, 1.3)),
                           ('threequarter', (2.4, -2.4, 1.7)),
                       ])
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'reads=oak_post_iron_leper_bell_hemp_pull',
        'pairs_with=narrative_leper_bell_act_iii',
        'footprint_m~=0.35x0.55',
        'collision=tight_to_mesh',
        'no_glow=1',
        'style=act3_leper_bell_post_occitan_1208',
        'off_lane=1',
        'road_clear_m=2.4',
        'road_crown_x=[-1.2,1.2]_no_colliders',
        'place_band=soft_shoulder_|x|_1.2-4',
        'hub_anchor_hint=Act_III_leper_approach_or_wayside_near_ferry_(0,-32)_spur',
        'place=off_road_leper_house_approach_wayside',
    ])


if __name__ == '__main__':
    main()
