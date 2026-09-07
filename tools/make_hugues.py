"""Blender: Captain Hugues (Broken Seal) — northern captain GLB + previews.

Mail/surcoat, dull iron, campaign commander — not chrome plate.
Dirt-and-mail Occitania 1208–10. No fantasy glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_hugues.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import character_common as cc

TARGET_HEIGHT = 1.78
MAX_WIDTH = 0.58
P = 'Hugues'


def make_hauberk(mail):
    profile = [
        (0.72, 0.198, 0.152, 0.010),
        (0.88, 0.188, 0.144, 0.012),
        (1.02, 0.178, 0.136, 0.014),
        (1.16, 0.192, 0.146, 0.012),
        (1.28, 0.205, 0.152, 0.008),
        (1.36, 0.160, 0.122, 0.005),
        (1.42, 0.072, 0.066, 0.000),
    ]
    skirt = [
        (0.58, 0.205, 0.158, 0.016),
        (0.44, 0.195, 0.150, 0.018),
        (0.32, 0.178, 0.140, 0.014),
    ]
    return cc.make_lathe_body(f'{P}_Hauberk', mail, profile, segs=22, fold_amp=0.008,
                              fold_freq=10, skirt=skirt, hem_scale=1.02, subdiv=2)


def make_surcoat(wool):
    """Campaign surcoat over mail — dusty northern wool, no chrome heraldry glow."""
    bm = bmesh.new()
    segs = 20
    profile = [(0.78, 0.210, 0.160), (0.95, 0.200, 0.152), (1.12, 0.205, 0.158),
               (1.26, 0.215, 0.162), (1.34, 0.168, 0.128)]
    rings = []
    for z, rx, ry in profile:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            side = abs(math.cos(a))
            rscale = 1.0 + 0.045 * (1 - side)
            wave = 1.0 + 0.012 * math.sin(a * 4 + z * 3)
            row.append(bm.verts.new((rx * rscale * wave * math.cos(a),
                                     ry * wave * math.sin(a), z)))
        rings.append(row)
    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    prev = rings[0]
    for z, rx, ry in ((0.62, 0.215, 0.165), (0.48, 0.205, 0.158), (0.38, 0.190, 0.148)):
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            row.append(bm.verts.new((rx * math.cos(a), ry * math.sin(a), z)))
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((prev[j], prev[j2], row[j2], row[j]))
        prev = row
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    parts = [cc.bm_to_object(f'{P}_SurcoatBase', bm, wool)]
    # Dull cloth bar (northern mark) — not glowing heraldry
    for scale, loc in [
        ((0.10, 0.012, 0.028), (0, 0.172, 1.12)),
        ((0.028, 0.012, 0.10), (0, 0.172, 1.12)),
    ]:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= scale[0]
            v.co.y *= scale[1]
            v.co.z *= scale[2]
            v.co += Vector(loc)
        parts.append(cc.bm_to_object('_mark', bm, wool))
    return cc.join_named(f'{P}_Surcoat', parts)


def make_coif(mail):
    """Mail coif — commander, face open, dull iron rings."""
    bm = bmesh.new()
    segs_u, segs_v = 24, 14
    grid = []
    theta0, theta1 = math.radians(48), math.radians(312)
    for i in range(segs_v + 1):
        v = i / segs_v
        z = 1.70 - v * 0.36
        rx = 0.114 + 0.025 * (0.5 - abs(v - 0.4)) + (0.048 * max(0, v - 0.65) / 0.35)
        ry = 0.120 + 0.02 * math.sin(v * math.pi) + (0.032 * max(0, v - 0.65) / 0.35)
        row = []
        for j in range(segs_u + 1):
            t = j / segs_u
            ang = theta0 + (theta1 - theta0) * t
            rmod = 1.0 + 0.03 * math.sin(ang * 12 + v * 8)
            x = rx * rmod * math.cos(ang)
            y = -0.01 + ry * rmod * math.sin(ang) * 0.95
            z_adj = z + (0.02 if v < 0.1 else 0)
            row.append(bm.verts.new((x, y, z_adj)))
        grid.append(row)
    for i in range(segs_v):
        for j in range(segs_u):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    for edge_j in (0, segs_u):
        for i in range(segs_v):
            a, b = grid[i][edge_j], grid[i + 1][edge_j]
            ai = bm.verts.new((a.co.x * 0.75, a.co.y * 0.5, a.co.z))
            bi = bm.verts.new((b.co.x * 0.75, b.co.y * 0.5, b.co.z))
            if edge_j == 0:
                bm.faces.new((a, b, bi, ai))
            else:
                bm.faces.new((a, ai, bi, b))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    return cc.bm_to_object(f'{P}_Coif', bm, mail)


def make_sword(leather, iron, wood):
    """Belt sword — campaign commander, dull iron, not parade chrome."""
    parts = []
    # scabbard
    bm = bmesh.new()
    path = [Vector((0.20, 0.08, 0.95)), Vector((0.22, 0.10, 0.70)),
            Vector((0.24, 0.11, 0.45)), Vector((0.25, 0.12, 0.28))]
    cc.tube(bm, path, [0.018, 0.017, 0.016, 0.012], segs=10)
    parts.append(cc.bm_to_object('_scab', bm, leather))
    # hilt / grip above belt
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.19, 0.075, 0.96)), Vector((0.18, 0.07, 1.08))],
            [0.014, 0.012], segs=8)
    parts.append(cc.bm_to_object('_grip', bm, wood))
    # crossguard
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.055
        v.co.y *= 0.012
        v.co.z *= 0.010
        v.co += Vector((0.185, 0.072, 0.96))
    parts.append(cc.bm_to_object('_guard', bm, iron))
    # pommel
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.022,
                              matrix=Matrix.Translation((0.18, 0.07, 1.10)))
    parts.append(cc.bm_to_object('_pommel', bm, iron))
    return cc.join_named(f'{P}_Sword', parts)


def make_kit(leather, iron):
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.040)
    for v in bm.verts:
        v.co.x *= 0.72
        v.co.z *= 1.25
        v.co += Vector((-0.16, 0.15, 0.90))
    parts.append(cc.bm_to_object('_pouch', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.08, 0.14, 0.92)), Vector((-0.08, 0.15, 0.80))],
            [0.012, 0.010], segs=8)
    parts.append(cc.bm_to_object('_knife_scab', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.08, 0.145, 0.93)), Vector((-0.08, 0.145, 0.97))],
            [0.007, 0.003], segs=6)
    parts.append(cc.bm_to_object('_knife', bm, iron))
    return cc.join_named(f'{P}_Kit', parts)


def build():
    cc.clear_scene()
    skin = cc.mat(f'{P}_Skin', (0.70, 0.52, 0.40), 0.55, specular=0.38)
    mail = cc.mat(f'{P}_Mail', (0.40, 0.40, 0.38), 0.50, metallic=0.52, specular=0.42)
    iron = cc.mat(f'{P}_Iron', (0.26, 0.25, 0.23), 0.58, metallic=0.68, specular=0.38)
    wool = cc.mat(f'{P}_Surcoat', (0.28, 0.30, 0.34), 0.90, specular=0.14)  # slate-north
    leather = cc.mat(f'{P}_Leather', (0.20, 0.13, 0.08), 0.84, specular=0.22)
    hair_m = cc.mat(f'{P}_Hair', (0.16, 0.12, 0.08), 0.76)
    brow_m = cc.mat(f'{P}_Brow', (0.12, 0.08, 0.05), 0.80)
    wood = cc.mat(f'{P}_Oak', (0.36, 0.24, 0.13), 0.78, specular=0.28)
    hose = cc.mat(f'{P}_Hose', (0.26, 0.24, 0.22), 0.86)
    boots = cc.mat(f'{P}_Boots', (0.11, 0.08, 0.06), 0.92)

    meshes = [
        make_hauberk(mail),
        make_coif(mail),
        make_surcoat(wool),
        cc.make_head(P, skin, hair_m, brow_m, hair_style='coif_ready'),
        cc.make_belt(P, leather, rx=0.178, ry=0.135),
        make_sword(leather, iron, wood),
        make_kit(leather, iron),
        cc.make_limbs(P, mail, skin, hose, boots, build='broad', bare_forearms=False),
    ]
    return cc.finish_character(
        'hugues', meshes, f'{P}_Armature', TARGET_HEIGHT, MAX_WIDTH,
        look_note='Northern captain: mail hauberk+coif, slate surcoat with dull cloth mark, belt sword, campaign kit — dull iron not chrome',
    )


if __name__ == '__main__':
    build()
